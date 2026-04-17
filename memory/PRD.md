# GCSE Question Bank Platform - PRD

## Original Problem Statement
Build a database for Genius Education (GE) tuition center to extract GCSE Maths questions from PDF files. Extract questions with their diagrams, crop images cleanly (no bleeding text), and store in a database format for reuse. Custom GE ID system for parent-child question tracking. Support marks, difficulty levels, topics, and marking schemes.

## What's Been Implemented

### Phase 1 (Initial MVP)
- Paper CRUD, PDF upload, AI extraction pipeline, question approval workflow, stats, Swiss brutalist UI

### Phase 2 (Current)
- **CRITICAL FIX**: Fixed `image_contents` → `file_contents` in GPT-5.2 vision calls
- GE ID system: Papers (GE-2017-P1), Questions (GE-2017-P1-Q01), Parts (GE-2017-P1-Q01A)
- Mark scheme PDF upload + AI extraction + auto-linking
- 30 GCSE topics across 4 categories
- Difficulty tagging (Bronze/Silver/Gold)
- LaTeX rendering with KaTeX
- Collapsible left pane with paper selection → question list flow
- Real extraction tested: 23 questions + 10 diagrams from a 20-page PDF

## Verified Extraction Results
- 23 questions extracted from Edexcel 2017 Paper 1
- Diagrams cropped cleanly (square with labels, graphs, geometric shapes)
- Questions correctly tagged: Q1-Q22 with difficulty (bronze → gold)
- Parts identified: Q1(a-d), Q8(a-b), Q11(a-c), Q12(a-b), etc.
- Topics auto-suggested: scatter graphs, quadratics, trigonometry, vectors, etc.
- LaTeX rendering confirmed working for mathematical expressions

## Prioritized Backlog
### P0 (Next)
- Bulk question approval workflow
- Test mark scheme upload and linking

### P1 (Important)  
- Export questions to PDF/docx formats
- Assignment builder (pick by topic + difficulty)
- Question search by text

### P2 (Nice to Have)
- User authentication
- Student-facing delivery
