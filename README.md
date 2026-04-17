# GE Question Bank - Genius Education

GCSE Maths question bank platform. Extract questions from PDF past papers using AI, build a structured database with diagrams, marks, topics, and mark schemes.

## Features
- PDF upload with AI extraction (Gemini Flash)
- Question parts with parent-child GE IDs (e.g., GE17EX126001A)
- Diagram cropping with AI refinement (no text bleeding)
- Mark scheme upload and auto-linking
- Difficulty tagging (Bronze/Silver/Gold)
- 30 GCSE topic categories
- Inline editing (text, marks, images)
- Cost tracking for API usage
- LaTeX rendering for mathematical expressions

## GE ID Format
`GE{exam_year}{board}{paper}{import_year}{seq}` → `GE17EX126001`
- Sub-parts: `GE17EX126001A`, `GE17EX126001B`

## Tech Stack
- **Frontend**: React 19 + Tailwind CSS + KaTeX
- **Backend**: FastAPI + Motor (async MongoDB)
- **Database**: MongoDB
- **AI**: Gemini 3 Flash (vision extraction)
- **Deployment**: Docker Compose

## Quick Start (Docker)

```bash
# 1. Clone
git clone https://github.com/rg412tp/ge.git
cd ge

# 2. Configure
cp .env.example .env
cp backend/.env.example backend/.env.production
# Edit both files with your credentials

# 3. Run
docker-compose up -d

# 4. Open
# http://localhost (frontend)
# http://localhost:8001/api/ (backend)
```

## VPS Deployment

```bash
# On your VPS:
curl -fsSL https://raw.githubusercontent.com/rg412tp/ge/main/scripts/deploy-vps.sh | bash
```

## Update After Changes

```bash
# Push changes to GitHub, then on VPS:
cd /opt/ge && bash scripts/update-vps.sh
```

## Environment Variables

### backend/.env.production
```
MONGO_URL=mongodb://admin:PASSWORD@mongo:27017
DB_NAME=ge_question_bank
GEMINI_API_KEY=your_gemini_key
CORS_ORIGINS=https://apps.geniuseducation.co.uk
```

### .env (root)
```
REACT_APP_BACKEND_URL=https://apps.geniuseducation.co.uk
MONGO_ROOT_USERNAME=admin
MONGO_ROOT_PASSWORD=your_password
```

## API Cost
- Gemini Flash: ~$0.008 per 20-page paper extraction
- ~40 API calls per paper (20 pages + 10 diagrams + 10 refinements)
- Monitor: GET `/api/api-usage`
