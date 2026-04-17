import { useState, useEffect, useCallback } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, useNavigate } from "react-router-dom";
import axios from "axios";
import { Toaster } from "@/components/ui/sonner";
import { toast } from "sonner";
import { 
  FilePdf, 
  Upload, 
  CheckCircle, 
  XCircle, 
  Clock, 
  CaretRight,
  Image as ImageIcon,
  Table,
  ChartLine,
  Stack,
  MagnifyingGlass,
  Funnel,
  ArrowClockwise,
  Eye,
  Check,
  X
} from "@phosphor-icons/react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// ============ Components ============

const StatusTag = ({ status }) => {
  const statusClasses = {
    draft: "status-draft",
    processing: "status-processing",
    "needs_review": "status-needs-review",
    approved: "status-approved",
    extracted: "status-extracted",
    completed: "status-approved",
    failed: "status-needs-review",
    pending: "status-processing"
  };
  
  return (
    <span data-testid={`status-tag-${status}`} className={`status-tag ${statusClasses[status] || "status-draft"}`}>
      {status?.replace("_", " ")}
    </span>
  );
};

const ProgressBar = ({ value, max }) => {
  const percent = max > 0 ? (value / max) * 100 : 0;
  return (
    <div className="progress-bar w-full" data-testid="progress-bar">
      <div className="progress-bar-fill" style={{ width: `${percent}%` }} />
    </div>
  );
};

// ============ PDF Upload Zone ============
const PDFUploadZone = ({ paperId, onUploadComplete }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [file, setFile] = useState(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.type === "application/pdf") {
      setFile(droppedFile);
    } else {
      toast.error("Please drop a PDF file");
    }
  };

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
    }
  };

  const handleUpload = async () => {
    if (!file || !paperId) return;
    
    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post(`${API}/papers/${paperId}/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      toast.success("PDF uploaded! Extraction started.");
      onUploadComplete(response.data.job_id);
      setFile(null);
    } catch (error) {
      toast.error("Upload failed: " + (error.response?.data?.detail || error.message));
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="p-6 border-b border-black">
      <div
        data-testid="pdf-upload-zone"
        className={`dropzone ${isDragging ? "active" : ""}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => document.getElementById("pdf-input").click()}
      >
        <input
          id="pdf-input"
          data-testid="pdf-file-input"
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={handleFileSelect}
        />
        {file ? (
          <div className="flex flex-col items-center gap-4">
            <FilePdf size={48} weight="duotone" />
            <p className="font-mono text-sm">{file.name}</p>
            <p className="text-xs text-slate-500">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-4">
            <Upload size={48} weight="duotone" />
            <p className="font-mono text-sm">Drop PDF here or click to select</p>
            <p className="text-xs text-slate-500">GCSE Maths Question Papers</p>
          </div>
        )}
      </div>
      
      {file && (
        <button
          data-testid="upload-pdf-btn"
          onClick={handleUpload}
          disabled={uploading || !paperId}
          className="btn-primary w-full mt-4 disabled:opacity-50"
        >
          {uploading ? "Uploading..." : "Start Extraction"}
        </button>
      )}
    </div>
  );
};

// ============ Paper Form ============
const PaperForm = ({ onPaperCreated }) => {
  const [formData, setFormData] = useState({
    board: "AQA",
    qualification: "GCSE",
    subject: "Mathematics",
    paper_number: "1",
    tier: "Higher",
    session: "June",
    exam_year: 2024
  });
  const [creating, setCreating] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setCreating(true);
    try {
      const response = await axios.post(`${API}/papers`, formData);
      toast.success("Paper created!");
      onPaperCreated(response.data);
    } catch (error) {
      toast.error("Failed to create paper");
    } finally {
      setCreating(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="p-6 border-b border-black">
      <h3 className="font-sans text-lg font-semibold mb-4">New Paper</h3>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="text-xs tracking-widest uppercase font-bold block mb-1">Board</label>
          <select
            data-testid="paper-board-select"
            value={formData.board}
            onChange={(e) => setFormData({...formData, board: e.target.value})}
            className="w-full border border-black p-2 bg-white"
          >
            <option value="AQA">AQA</option>
            <option value="Edexcel">Edexcel</option>
            <option value="OCR">OCR</option>
          </select>
        </div>
        <div>
          <label className="text-xs tracking-widest uppercase font-bold block mb-1">Year</label>
          <input
            data-testid="paper-year-input"
            type="number"
            value={formData.exam_year}
            onChange={(e) => setFormData({...formData, exam_year: parseInt(e.target.value)})}
            className="w-full border border-black p-2"
          />
        </div>
        <div>
          <label className="text-xs tracking-widest uppercase font-bold block mb-1">Paper</label>
          <select
            data-testid="paper-number-select"
            value={formData.paper_number}
            onChange={(e) => setFormData({...formData, paper_number: e.target.value})}
            className="w-full border border-black p-2 bg-white"
          >
            <option value="1">Paper 1</option>
            <option value="2">Paper 2</option>
            <option value="3">Paper 3</option>
          </select>
        </div>
        <div>
          <label className="text-xs tracking-widest uppercase font-bold block mb-1">Tier</label>
          <select
            data-testid="paper-tier-select"
            value={formData.tier}
            onChange={(e) => setFormData({...formData, tier: e.target.value})}
            className="w-full border border-black p-2 bg-white"
          >
            <option value="Higher">Higher</option>
            <option value="Foundation">Foundation</option>
          </select>
        </div>
        <div>
          <label className="text-xs tracking-widest uppercase font-bold block mb-1">Session</label>
          <select
            data-testid="paper-session-select"
            value={formData.session}
            onChange={(e) => setFormData({...formData, session: e.target.value})}
            className="w-full border border-black p-2 bg-white"
          >
            <option value="June">June</option>
            <option value="November">November</option>
          </select>
        </div>
      </div>
      <button 
        data-testid="create-paper-btn"
        type="submit" 
        disabled={creating}
        className="btn-primary w-full mt-4"
      >
        {creating ? "Creating..." : "Create Paper"}
      </button>
    </form>
  );
};

// ============ Extraction Status ============
const ExtractionStatus = ({ jobId, onComplete }) => {
  const [job, setJob] = useState(null);

  useEffect(() => {
    if (!jobId) return;
    
    const pollStatus = async () => {
      try {
        const response = await axios.get(`${API}/extraction-jobs/${jobId}`);
        setJob(response.data);
        
        if (response.data.status === "completed") {
          onComplete();
        } else if (response.data.status === "failed") {
          toast.error("Extraction failed: " + (response.data.error_message || "Unknown error"));
        }
      } catch (error) {
        console.error("Failed to poll status:", error);
      }
    };

    pollStatus();
    const interval = setInterval(pollStatus, 2000);
    
    return () => clearInterval(interval);
  }, [jobId, onComplete]);

  if (!job) return null;

  return (
    <div data-testid="extraction-status" className="p-6 border-b border-black bg-slate-50">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs tracking-widest uppercase font-bold">Extraction</span>
        <StatusTag status={job.status} />
      </div>
      <ProgressBar value={job.processed_pages} max={job.total_pages} />
      <div className="flex justify-between mt-2 text-xs text-slate-600">
        <span>Pages: {job.processed_pages}/{job.total_pages}</span>
        <span>Questions: {job.questions_found}</span>
        <span>Images: {job.images_extracted}</span>
      </div>
    </div>
  );
};

// ============ Question List ============
const QuestionList = ({ questions, selectedId, onSelect }) => {
  const [filter, setFilter] = useState("all");
  
  const filteredQuestions = questions.filter(q => {
    if (filter === "all") return true;
    return q.status === filter;
  });

  return (
    <div className="h-full flex flex-col">
      {/* Filter bar */}
      <div className="p-4 border-b border-black flex items-center gap-2">
        <Funnel size={16} weight="bold" />
        <select
          data-testid="question-filter-select"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="border border-black px-2 py-1 text-xs bg-white"
        >
          <option value="all">All ({questions.length})</option>
          <option value="draft">Draft</option>
          <option value="needs_review">Needs Review</option>
          <option value="approved">Approved</option>
        </select>
      </div>
      
      {/* Question rows */}
      <div className="flex-1 overflow-auto">
        {filteredQuestions.length === 0 ? (
          <div className="p-8 text-center text-slate-500">
            <Stack size={48} className="mx-auto mb-4" />
            <p className="text-sm">No questions found</p>
          </div>
        ) : (
          filteredQuestions.map((question) => (
            <div
              key={question.id}
              data-testid={`question-row-${question.question_number}`}
              onClick={() => onSelect(question)}
              className={`p-4 border-b border-black cursor-pointer transition-colors ${
                selectedId === question.id ? "bg-slate-100" : "hover:bg-slate-50"
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <span className="font-sans font-bold text-lg">Q{question.question_number}</span>
                  <div className="flex gap-1">
                    {question.has_diagram && (
                      <span title="Has diagram" className="p-1 border border-slate-400">
                        <ChartLine size={14} />
                      </span>
                    )}
                    {question.has_table && (
                      <span title="Has table" className="p-1 border border-slate-400">
                        <Table size={14} />
                      </span>
                    )}
                    {question.images?.length > 0 && (
                      <span title={`${question.images.length} image(s)`} className="p-1 border border-slate-400">
                        <ImageIcon size={14} />
                      </span>
                    )}
                  </div>
                </div>
                <StatusTag status={question.status} />
              </div>
              <p className="text-xs text-slate-600 mt-2 line-clamp-2">{question.text}</p>
              {question.parts?.length > 0 && (
                <div className="mt-2 text-xs text-slate-500">
                  Parts: {question.parts.map(p => p.part_label).join(", ")}
                </div>
              )}
              <div className="flex items-center justify-between mt-2">
                <span className="text-xs text-slate-500">
                  {question.marks ? `${question.marks} marks` : ""}
                </span>
                <span className="text-xs text-slate-500">
                  Confidence: {(question.confidence * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

// ============ Question Detail ============
const QuestionDetail = ({ question, onUpdate, onClose }) => {
  const [images, setImages] = useState([]);
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    if (question?.images?.length > 0) {
      // Fetch image data
      Promise.all(
        question.images.map(async (imgId) => {
          try {
            const response = await axios.get(`${API}/images/${imgId}`);
            return response.data;
          } catch {
            return null;
          }
        })
      ).then((imgs) => setImages(imgs.filter(Boolean)));
    } else {
      setImages([]);
    }
  }, [question]);

  const handleApprove = async () => {
    setUpdating(true);
    try {
      await axios.post(`${API}/questions/${question.id}/approve`);
      toast.success("Question approved!");
      onUpdate();
    } catch (error) {
      toast.error("Failed to approve question");
    } finally {
      setUpdating(false);
    }
  };

  const handleReject = async () => {
    setUpdating(true);
    try {
      await axios.post(`${API}/questions/${question.id}/reject`);
      toast.success("Question marked for review");
      onUpdate();
    } catch (error) {
      toast.error("Failed to reject question");
    } finally {
      setUpdating(false);
    }
  };

  if (!question) {
    return (
      <div className="h-full flex items-center justify-center text-slate-500">
        <div className="text-center">
          <Eye size={48} className="mx-auto mb-4" />
          <p className="text-sm">Select a question to view details</p>
        </div>
      </div>
    );
  }

  return (
    <div data-testid="question-detail" className="h-full flex flex-col overflow-auto">
      {/* Header */}
      <div className="p-6 border-b border-black flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h2 className="font-sans text-2xl font-bold">Question {question.question_number}</h2>
          <StatusTag status={question.status} />
        </div>
        <div className="flex gap-2">
          <button
            data-testid="approve-question-btn"
            onClick={handleApprove}
            disabled={updating || question.status === "approved"}
            className="btn-primary flex items-center gap-2 disabled:opacity-50"
          >
            <Check size={16} weight="bold" />
            Approve
          </button>
          <button
            data-testid="reject-question-btn"
            onClick={handleReject}
            disabled={updating}
            className="btn-secondary flex items-center gap-2"
          >
            <X size={16} weight="bold" />
            Reject
          </button>
        </div>
      </div>
      
      {/* Content */}
      <div className="flex-1 p-6 overflow-auto">
        {/* Question text */}
        <div className="mb-6">
          <label className="text-xs tracking-widest uppercase font-bold block mb-2">Question Text</label>
          <div className="border border-black p-4 bg-slate-50">
            <p className="whitespace-pre-wrap">{question.text}</p>
          </div>
        </div>
        
        {/* Parts */}
        {question.parts?.length > 0 && (
          <div className="mb-6">
            <label className="text-xs tracking-widest uppercase font-bold block mb-2">Parts</label>
            <div className="border border-black">
              {question.parts.map((part, idx) => (
                <div key={idx} className="p-4 border-b border-black last:border-b-0">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="font-bold">({part.part_label})</span>
                    {part.marks && (
                      <span className="text-xs text-slate-500">[{part.marks} marks]</span>
                    )}
                  </div>
                  <p className="whitespace-pre-wrap text-sm">{part.text}</p>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* Images/Diagrams */}
        {images.length > 0 && (
          <div className="mb-6">
            <label className="text-xs tracking-widest uppercase font-bold block mb-2">
              Diagrams & Figures ({images.length})
            </label>
            <div className="grid grid-cols-2 gap-4">
              {images.map((img) => (
                <div
                  key={img.id}
                  data-testid={`diagram-${img.id}`}
                  data-label={`Fig ${img.page_number}.${images.indexOf(img) + 1}`}
                  className="diagram-container"
                >
                  <img
                    src={`${API}/images/${img.id}/download`}
                    alt={img.description || "Diagram"}
                    className="w-full h-auto"
                  />
                  {img.description && (
                    <p className="text-xs text-slate-500 mt-2">{img.description}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* Metadata */}
        <div className="grid grid-cols-2 gap-4">
          <div className="border border-black p-4">
            <label className="text-xs tracking-widest uppercase font-bold block mb-1">Marks</label>
            <p className="text-lg font-bold">{question.marks || "—"}</p>
          </div>
          <div className="border border-black p-4">
            <label className="text-xs tracking-widest uppercase font-bold block mb-1">Confidence</label>
            <p className="text-lg font-bold">{(question.confidence * 100).toFixed(0)}%</p>
          </div>
        </div>
      </div>
    </div>
  );
};

// ============ Papers List ============
const PapersList = ({ papers, selectedId, onSelect }) => {
  return (
    <div className="border-b border-black">
      <div className="p-4 border-b border-black">
        <label className="text-xs tracking-widest uppercase font-bold">Papers</label>
      </div>
      <div className="max-h-48 overflow-auto">
        {papers.length === 0 ? (
          <div className="p-4 text-center text-slate-500 text-sm">
            No papers yet. Create one above.
          </div>
        ) : (
          papers.map((paper) => (
            <div
              key={paper.id}
              data-testid={`paper-row-${paper.id}`}
              onClick={() => onSelect(paper)}
              className={`p-3 border-b border-slate-200 cursor-pointer flex items-center justify-between ${
                selectedId === paper.id ? "bg-slate-100" : "hover:bg-slate-50"
              }`}
            >
              <div>
                <span className="font-semibold">{paper.board}</span>
                <span className="text-slate-500 ml-2">
                  {paper.session} {paper.exam_year} - Paper {paper.paper_number}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <StatusTag status={paper.status} />
                <CaretRight size={16} />
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

// ============ Stats Card ============
const StatsCard = ({ stats }) => {
  if (!stats) return null;
  
  return (
    <div className="p-4 border-b border-black bg-slate-50">
      <div className="grid grid-cols-4 gap-4 text-center">
        <div>
          <p className="text-2xl font-bold">{stats.total_papers}</p>
          <p className="text-xs text-slate-500">Papers</p>
        </div>
        <div>
          <p className="text-2xl font-bold">{stats.total_questions}</p>
          <p className="text-xs text-slate-500">Questions</p>
        </div>
        <div>
          <p className="text-2xl font-bold text-green-600">{stats.approved_questions}</p>
          <p className="text-xs text-slate-500">Approved</p>
        </div>
        <div>
          <p className="text-2xl font-bold text-amber-600">{stats.pending_review}</p>
          <p className="text-xs text-slate-500">Review</p>
        </div>
      </div>
    </div>
  );
};

// ============ Main Dashboard ============
const Dashboard = () => {
  const [papers, setPapers] = useState([]);
  const [selectedPaper, setSelectedPaper] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [selectedQuestion, setSelectedQuestion] = useState(null);
  const [extractionJobId, setExtractionJobId] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const [papersRes, statsRes] = await Promise.all([
        axios.get(`${API}/papers`),
        axios.get(`${API}/stats`)
      ]);
      setPapers(papersRes.data);
      setStats(statsRes.data);
    } catch (error) {
      console.error("Failed to fetch data:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchQuestions = useCallback(async (paperId) => {
    try {
      const response = await axios.get(`${API}/questions?paper_id=${paperId}`);
      setQuestions(response.data);
    } catch (error) {
      console.error("Failed to fetch questions:", error);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    if (selectedPaper) {
      fetchQuestions(selectedPaper.id);
    }
  }, [selectedPaper, fetchQuestions]);

  const handlePaperCreated = (paper) => {
    setPapers([...papers, paper]);
    setSelectedPaper(paper);
  };

  const handlePaperSelect = (paper) => {
    setSelectedPaper(paper);
    setSelectedQuestion(null);
    setQuestions([]);
  };

  const handleUploadComplete = (jobId) => {
    setExtractionJobId(jobId);
  };

  const handleExtractionComplete = () => {
    setExtractionJobId(null);
    if (selectedPaper) {
      fetchQuestions(selectedPaper.id);
    }
    fetchData();
  };

  const handleQuestionUpdate = () => {
    if (selectedPaper) {
      fetchQuestions(selectedPaper.id);
    }
    fetchData();
  };

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="text-center">
          <ArrowClockwise size={48} className="animate-spin mx-auto mb-4" />
          <p className="text-sm">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen" data-testid="dashboard">
      {/* Header */}
      <header className="border-b border-black">
        <div className="p-6 flex items-center justify-between">
          <div>
            <h1 className="font-sans text-3xl font-bold tracking-tight">GCSE Question Bank</h1>
            <p className="text-sm text-slate-600 mt-1">Extract and manage exam questions</p>
          </div>
          <div className="flex items-center gap-4">
            <button
              data-testid="refresh-btn"
              onClick={fetchData}
              className="p-2 border border-black hover:bg-black hover:text-white transition-colors"
            >
              <ArrowClockwise size={20} />
            </button>
          </div>
        </div>
        <StatsCard stats={stats} />
      </header>

      {/* Main content - dual pane */}
      <div className="dual-pane" style={{ height: "calc(100vh - 180px)" }}>
        {/* Left pane - Upload & Papers */}
        <div className="border-r border-black flex flex-col overflow-hidden">
          <PaperForm onPaperCreated={handlePaperCreated} />
          <PapersList 
            papers={papers} 
            selectedId={selectedPaper?.id} 
            onSelect={handlePaperSelect} 
          />
          
          {selectedPaper && (
            <>
              <PDFUploadZone 
                paperId={selectedPaper.id} 
                onUploadComplete={handleUploadComplete}
              />
              {extractionJobId && (
                <ExtractionStatus 
                  jobId={extractionJobId} 
                  onComplete={handleExtractionComplete}
                />
              )}
            </>
          )}
          
          {/* Question list */}
          <div className="flex-1 overflow-hidden">
            {selectedPaper && (
              <QuestionList
                questions={questions}
                selectedId={selectedQuestion?.id}
                onSelect={setSelectedQuestion}
              />
            )}
          </div>
        </div>

        {/* Right pane - Question Detail */}
        <div className="overflow-hidden">
          <QuestionDetail
            question={selectedQuestion}
            onUpdate={handleQuestionUpdate}
            onClose={() => setSelectedQuestion(null)}
          />
        </div>
      </div>
    </div>
  );
};

// ============ App Router ============
function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Dashboard />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="bottom-right" />
    </div>
  );
}

export default App;
