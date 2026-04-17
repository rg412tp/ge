from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException, Response
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import base64
import io
import fitz  # PyMuPDF
from PIL import Image
import requests
import asyncio
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'gcse_question_bank')]

# Object Storage
STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"
EMERGENT_KEY = os.environ.get("EMERGENT_LLM_KEY")
APP_NAME = "gcse-question-bank"
storage_key = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create the main app
app = FastAPI(title="GCSE Question Bank API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ============ Object Storage Functions ============
def init_storage():
    """Initialize object storage - call once at startup"""
    global storage_key
    if storage_key:
        return storage_key
    try:
        resp = requests.post(f"{STORAGE_URL}/init", json={"emergent_key": EMERGENT_KEY}, timeout=30)
        resp.raise_for_status()
        storage_key = resp.json()["storage_key"]
        logger.info("Object storage initialized successfully")
        return storage_key
    except Exception as e:
        logger.error(f"Failed to initialize storage: {e}")
        return None

def put_object(path: str, data: bytes, content_type: str) -> dict:
    """Upload file to object storage"""
    key = init_storage()
    if not key:
        raise Exception("Storage not initialized")
    resp = requests.put(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key, "Content-Type": content_type},
        data=data, timeout=120
    )
    resp.raise_for_status()
    return resp.json()

def get_object(path: str) -> tuple:
    """Download file from object storage"""
    key = init_storage()
    if not key:
        raise Exception("Storage not initialized")
    resp = requests.get(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key}, timeout=60
    )
    resp.raise_for_status()
    return resp.content, resp.headers.get("Content-Type", "application/octet-stream")

# ============ Pydantic Models ============
class PaperCreate(BaseModel):
    board: str = "AQA"  # AQA, Edexcel, OCR
    qualification: str = "GCSE"
    subject: str = "Mathematics"
    paper_number: str = "1"
    tier: str = "Higher"  # Foundation, Higher
    session: str = "June"
    exam_year: int = 2024

class Paper(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    board: str
    qualification: str
    subject: str
    paper_number: str
    tier: str
    session: str
    exam_year: int
    status: str = "processing"  # processing, extracted, reviewed
    pdf_path: Optional[str] = None
    total_questions: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class QuestionPart(BaseModel):
    part_label: str  # a, b, c, etc.
    text: str
    latex: Optional[str] = None
    marks: Optional[int] = None
    images: List[str] = []  # List of image asset IDs
    confidence: float = 0.0

class Question(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    paper_id: str
    question_number: int
    text: str
    latex: Optional[str] = None
    parts: List[QuestionPart] = []
    marks: Optional[int] = None
    images: List[str] = []  # List of image asset IDs
    has_diagram: bool = False
    has_table: bool = False
    status: str = "draft"  # draft, needs_review, approved
    confidence: float = 0.0
    review_reason_codes: List[str] = []
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ImageAsset(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    paper_id: str
    question_id: Optional[str] = None
    storage_path: str
    original_filename: str
    content_type: str
    width: int
    height: int
    page_number: int
    crop_coords: Optional[Dict[str, int]] = None  # x, y, width, height
    description: Optional[str] = None
    is_deleted: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ExtractionJob(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    paper_id: str
    status: str = "pending"  # pending, processing, completed, failed
    total_pages: int = 0
    processed_pages: int = 0
    questions_found: int = 0
    images_extracted: int = 0
    error_message: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# ============ AI Extraction Functions ============
async def extract_questions_from_page(page_image_base64: str, page_number: int, paper_id: str) -> Dict[str, Any]:
    """Use GPT-5.2 to extract questions from a page image"""
    try:
        chat = LlmChat(
            api_key=EMERGENT_KEY,
            session_id=f"extraction-{paper_id}-page-{page_number}",
            system_message="""You are an expert at extracting GCSE Maths exam questions from images.
            
Your task is to:
1. Identify all questions on the page
2. Extract question numbers and their parts (a, b, c, etc.)
3. Extract the full text of each question/part
4. Identify any diagrams, graphs, or tables and describe their location
5. Estimate marks if visible

Return a JSON object with this structure:
{
  "questions": [
    {
      "question_number": 1,
      "text": "Full question text here",
      "parts": [
        {
          "part_label": "a",
          "text": "Part (a) text here",
          "marks": 2
        }
      ],
      "marks": 5,
      "has_diagram": true,
      "has_table": false,
      "diagram_description": "A coordinate grid showing...",
      "diagram_location": "below question text, centered"
    }
  ],
  "page_has_content": true,
  "confidence": 0.95
}

If this is a blank page or cover page with no questions, return:
{"questions": [], "page_has_content": false, "confidence": 1.0}

Be precise and extract ALL text exactly as written. For mathematical expressions, include them in plain text."""
        ).with_model("openai", "gpt-5.2")
        
        image_content = ImageContent(image_base64=page_image_base64)
        user_message = UserMessage(
            text=f"Extract all GCSE Maths questions from page {page_number} of this exam paper. Return the result as valid JSON.",
            image_contents=[image_content]
        )
        
        response = await chat.send_message(user_message)
        
        # Parse JSON from response
        import json
        # Try to extract JSON from response
        response_text = response.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        result = json.loads(response_text.strip())
        return result
        
    except Exception as e:
        logger.error(f"Error extracting questions from page {page_number}: {e}")
        return {"questions": [], "page_has_content": False, "confidence": 0.0, "error": str(e)}

async def extract_diagram_from_page(page_image_base64: str, page_number: int, paper_id: str, question_number: int) -> Dict[str, Any]:
    """Use GPT-5.2 to identify and describe diagram boundaries for cropping"""
    try:
        chat = LlmChat(
            api_key=EMERGENT_KEY,
            session_id=f"diagram-{paper_id}-page-{page_number}-q{question_number}",
            system_message="""You are an expert at identifying diagram boundaries in exam papers.

Your task is to identify the bounding box of any diagrams, graphs, figures, or tables on this page.
The coordinates should be in percentages of the page dimensions (0-100).

Return a JSON object with this structure:
{
  "diagrams": [
    {
      "question_number": 1,
      "type": "graph",
      "description": "Coordinate grid with plotted points",
      "bounding_box": {
        "x_percent": 10,
        "y_percent": 30,
        "width_percent": 80,
        "height_percent": 40
      }
    }
  ],
  "has_diagrams": true
}

If there are no diagrams, return: {"diagrams": [], "has_diagrams": false}

Be precise with boundaries - ensure no text bleeds into the diagram crop."""
        ).with_model("openai", "gpt-5.2")
        
        image_content = ImageContent(image_base64=page_image_base64)
        user_message = UserMessage(
            text=f"Identify the bounding boxes of all diagrams, graphs, figures, or tables on this page. Focus on question {question_number} if specified. Return valid JSON.",
            image_contents=[image_content]
        )
        
        response = await chat.send_message(user_message)
        
        import json
        response_text = response.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        result = json.loads(response_text.strip())
        return result
        
    except Exception as e:
        logger.error(f"Error extracting diagram info from page {page_number}: {e}")
        return {"diagrams": [], "has_diagrams": False, "error": str(e)}

# ============ PDF Processing Functions ============
def convert_page_to_base64(pdf_document, page_number: int, dpi: int = 150) -> str:
    """Convert a PDF page to base64 encoded PNG image"""
    page = pdf_document[page_number]
    mat = fitz.Matrix(dpi/72, dpi/72)
    pix = page.get_pixmap(matrix=mat)
    img_data = pix.tobytes("png")
    return base64.b64encode(img_data).decode('utf-8')

def crop_image_from_page(pdf_document, page_number: int, bbox: Dict[str, float], dpi: int = 200) -> bytes:
    """Crop a specific region from a PDF page"""
    page = pdf_document[page_number]
    mat = fitz.Matrix(dpi/72, dpi/72)
    pix = page.get_pixmap(matrix=mat)
    
    # Convert to PIL Image for cropping
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    
    # Calculate pixel coordinates from percentages
    x = int(bbox['x_percent'] / 100 * img.width)
    y = int(bbox['y_percent'] / 100 * img.height)
    w = int(bbox['width_percent'] / 100 * img.width)
    h = int(bbox['height_percent'] / 100 * img.height)
    
    # Add small padding
    padding = 10
    x = max(0, x - padding)
    y = max(0, y - padding)
    w = min(img.width - x, w + 2*padding)
    h = min(img.height - y, h + 2*padding)
    
    # Crop
    cropped = img.crop((x, y, x + w, y + h))
    
    # Save to bytes
    img_byte_arr = io.BytesIO()
    cropped.save(img_byte_arr, format='PNG', optimize=True)
    return img_byte_arr.getvalue()

# ============ API Endpoints ============
@api_router.get("/")
async def root():
    return {"message": "GCSE Question Bank API", "version": "1.0.0"}

@api_router.get("/health")
async def health():
    return {"status": "healthy", "storage_initialized": storage_key is not None}

# Paper endpoints
@api_router.post("/papers", response_model=Paper)
async def create_paper(paper_data: PaperCreate):
    paper = Paper(**paper_data.model_dump())
    doc = paper.model_dump()
    await db.papers.insert_one(doc)
    return paper

@api_router.get("/papers", response_model=List[Paper])
async def list_papers():
    papers = await db.papers.find({}, {"_id": 0}).to_list(100)
    return papers

@api_router.get("/papers/{paper_id}", response_model=Paper)
async def get_paper(paper_id: str):
    paper = await db.papers.find_one({"id": paper_id}, {"_id": 0})
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper

# PDF Upload and Extraction
@api_router.post("/papers/{paper_id}/upload")
async def upload_pdf(paper_id: str, file: UploadFile = File(...)):
    """Upload a PDF and start extraction"""
    # Verify paper exists
    paper = await db.papers.find_one({"id": paper_id}, {"_id": 0})
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    
    # Read PDF content
    pdf_content = await file.read()
    
    # Upload to object storage
    storage_path = f"{APP_NAME}/pdfs/{paper_id}/{uuid.uuid4()}.pdf"
    try:
        put_object(storage_path, pdf_content, "application/pdf")
    except Exception as e:
        logger.error(f"Failed to upload PDF to storage: {e}")
        raise HTTPException(status_code=500, detail="Failed to store PDF")
    
    # Update paper with PDF path
    await db.papers.update_one(
        {"id": paper_id},
        {"$set": {"pdf_path": storage_path, "status": "processing"}}
    )
    
    # Create extraction job
    job = ExtractionJob(paper_id=paper_id)
    await db.extraction_jobs.insert_one(job.model_dump())
    
    # Start extraction in background
    asyncio.create_task(process_pdf_extraction(paper_id, pdf_content, job.id))
    
    return {"message": "PDF uploaded successfully", "job_id": job.id, "paper_id": paper_id}

async def process_pdf_extraction(paper_id: str, pdf_content: bytes, job_id: str):
    """Background task to extract questions from PDF"""
    try:
        # Update job status
        await db.extraction_jobs.update_one(
            {"id": job_id},
            {"$set": {"status": "processing", "started_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        # Open PDF
        pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
        total_pages = len(pdf_document)
        
        await db.extraction_jobs.update_one(
            {"id": job_id},
            {"$set": {"total_pages": total_pages}}
        )
        
        all_questions = []
        images_extracted = 0
        
        # Process each page
        for page_num in range(total_pages):
            try:
                # Convert page to image
                page_base64 = convert_page_to_base64(pdf_document, page_num)
                
                # Extract questions using AI
                extraction_result = await extract_questions_from_page(page_base64, page_num + 1, paper_id)
                
                if extraction_result.get("questions"):
                    for q_data in extraction_result["questions"]:
                        # Check for diagrams
                        if q_data.get("has_diagram") or q_data.get("has_table"):
                            diagram_result = await extract_diagram_from_page(
                                page_base64, page_num, paper_id, q_data["question_number"]
                            )
                            
                            # Crop and save diagrams
                            image_ids = []
                            if diagram_result.get("diagrams"):
                                for diag in diagram_result["diagrams"]:
                                    try:
                                        cropped_img = crop_image_from_page(
                                            pdf_document, page_num, diag["bounding_box"]
                                        )
                                        
                                        # Upload cropped image
                                        img_id = str(uuid.uuid4())
                                        img_path = f"{APP_NAME}/images/{paper_id}/{img_id}.png"
                                        put_object(img_path, cropped_img, "image/png")
                                        
                                        # Save image asset record
                                        img_asset = ImageAsset(
                                            id=img_id,
                                            paper_id=paper_id,
                                            storage_path=img_path,
                                            original_filename=f"diagram_{q_data['question_number']}_{page_num+1}.png",
                                            content_type="image/png",
                                            width=int(diag["bounding_box"]["width_percent"]),
                                            height=int(diag["bounding_box"]["height_percent"]),
                                            page_number=page_num + 1,
                                            crop_coords={
                                                "x": int(diag["bounding_box"]["x_percent"]),
                                                "y": int(diag["bounding_box"]["y_percent"]),
                                                "width": int(diag["bounding_box"]["width_percent"]),
                                                "height": int(diag["bounding_box"]["height_percent"])
                                            },
                                            description=diag.get("description", "")
                                        )
                                        await db.image_assets.insert_one(img_asset.model_dump())
                                        image_ids.append(img_id)
                                        images_extracted += 1
                                    except Exception as e:
                                        logger.error(f"Error cropping diagram: {e}")
                            
                            q_data["images"] = image_ids
                        
                        # Create question record
                        parts = []
                        for part_data in q_data.get("parts", []):
                            parts.append(QuestionPart(
                                part_label=part_data.get("part_label", ""),
                                text=part_data.get("text", ""),
                                marks=part_data.get("marks"),
                                confidence=extraction_result.get("confidence", 0.8)
                            ))
                        
                        question = Question(
                            paper_id=paper_id,
                            question_number=q_data["question_number"],
                            text=q_data.get("text", ""),
                            parts=parts,
                            marks=q_data.get("marks"),
                            images=q_data.get("images", []),
                            has_diagram=q_data.get("has_diagram", False),
                            has_table=q_data.get("has_table", False),
                            confidence=extraction_result.get("confidence", 0.8),
                            status="needs_review" if extraction_result.get("confidence", 0) < 0.9 else "draft"
                        )
                        
                        await db.questions.insert_one(question.model_dump())
                        all_questions.append(question)
                
                # Update progress
                await db.extraction_jobs.update_one(
                    {"id": job_id},
                    {"$set": {
                        "processed_pages": page_num + 1,
                        "questions_found": len(all_questions),
                        "images_extracted": images_extracted
                    }}
                )
                
            except Exception as e:
                logger.error(f"Error processing page {page_num}: {e}")
        
        pdf_document.close()
        
        # Update job as completed
        await db.extraction_jobs.update_one(
            {"id": job_id},
            {"$set": {
                "status": "completed",
                "completed_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Update paper status
        await db.papers.update_one(
            {"id": paper_id},
            {"$set": {
                "status": "extracted",
                "total_questions": len(all_questions)
            }}
        )
        
        logger.info(f"Extraction completed for paper {paper_id}: {len(all_questions)} questions, {images_extracted} images")
        
    except Exception as e:
        logger.error(f"Extraction failed for paper {paper_id}: {e}")
        await db.extraction_jobs.update_one(
            {"id": job_id},
            {"$set": {
                "status": "failed",
                "error_message": str(e),
                "completed_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        await db.papers.update_one(
            {"id": paper_id},
            {"$set": {"status": "failed"}}
        )

# Extraction job status
@api_router.get("/extraction-jobs/{job_id}")
async def get_extraction_job(job_id: str):
    job = await db.extraction_jobs.find_one({"id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@api_router.get("/papers/{paper_id}/extraction-status")
async def get_paper_extraction_status(paper_id: str):
    job = await db.extraction_jobs.find_one(
        {"paper_id": paper_id},
        {"_id": 0},
        sort=[("created_at", -1)]
    )
    if not job:
        raise HTTPException(status_code=404, detail="No extraction job found for this paper")
    return job

# Question endpoints
@api_router.get("/questions", response_model=List[Question])
async def list_questions(paper_id: Optional[str] = None, status: Optional[str] = None):
    query = {}
    if paper_id:
        query["paper_id"] = paper_id
    if status:
        query["status"] = status
    questions = await db.questions.find(query, {"_id": 0}).to_list(500)
    return questions

@api_router.get("/questions/{question_id}", response_model=Question)
async def get_question(question_id: str):
    question = await db.questions.find_one({"id": question_id}, {"_id": 0})
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question

@api_router.patch("/questions/{question_id}")
async def update_question(question_id: str, updates: Dict[str, Any]):
    """Update a question (for review/approval workflow)"""
    # Filter allowed update fields
    allowed_fields = ["text", "latex", "marks", "status", "parts", "review_reason_codes"]
    filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}
    
    if not filtered_updates:
        raise HTTPException(status_code=400, detail="No valid update fields provided")
    
    result = await db.questions.update_one(
        {"id": question_id},
        {"$set": filtered_updates}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Question not found")
    
    return {"message": "Question updated", "updated_fields": list(filtered_updates.keys())}

@api_router.post("/questions/{question_id}/approve")
async def approve_question(question_id: str):
    """Approve a question"""
    result = await db.questions.update_one(
        {"id": question_id},
        {"$set": {"status": "approved"}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Question not found")
    return {"message": "Question approved"}

@api_router.post("/questions/{question_id}/reject")
async def reject_question(question_id: str, reason: Optional[str] = None):
    """Reject a question and mark for re-review"""
    updates = {"status": "needs_review"}
    if reason:
        updates["review_reason_codes"] = [reason]
    
    result = await db.questions.update_one(
        {"id": question_id},
        {"$set": updates}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Question not found")
    return {"message": "Question rejected"}

# Image endpoints
@api_router.get("/images/{image_id}")
async def get_image(image_id: str):
    """Get image metadata"""
    image = await db.image_assets.find_one({"id": image_id, "is_deleted": False}, {"_id": 0})
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return image

@api_router.get("/images/{image_id}/download")
async def download_image(image_id: str):
    """Download the actual image file"""
    image = await db.image_assets.find_one({"id": image_id, "is_deleted": False}, {"_id": 0})
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    try:
        data, content_type = get_object(image["storage_path"])
        return Response(content=data, media_type=content_type)
    except Exception as e:
        logger.error(f"Error downloading image: {e}")
        raise HTTPException(status_code=500, detail="Failed to download image")

@api_router.get("/papers/{paper_id}/images")
async def list_paper_images(paper_id: str):
    """List all images for a paper"""
    images = await db.image_assets.find(
        {"paper_id": paper_id, "is_deleted": False},
        {"_id": 0}
    ).to_list(100)
    return images

# Stats endpoint
@api_router.get("/stats")
async def get_stats():
    """Get overall statistics"""
    total_papers = await db.papers.count_documents({})
    total_questions = await db.questions.count_documents({})
    approved_questions = await db.questions.count_documents({"status": "approved"})
    pending_review = await db.questions.count_documents({"status": "needs_review"})
    total_images = await db.image_assets.count_documents({"is_deleted": False})
    
    return {
        "total_papers": total_papers,
        "total_questions": total_questions,
        "approved_questions": approved_questions,
        "pending_review": pending_review,
        "total_images": total_images
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    try:
        init_storage()
    except Exception as e:
        logger.error(f"Storage init failed: {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
