# GCSE Question Bank Platform - PRD

## Original Problem Statement
Build a question bank database for Genius Education (GE) tuition center. Extract GCSE Maths questions from PDFs with clean image crops. Custom GE ID system with parent-child hierarchy. Editable fields. Mark scheme linking. Future: AI answer recommendation, Hostinger deployment.

## GE ID Format
- Paper: `GE{2-digit exam year}{Board: EX/AQ/OC}{Paper#}` → `GE17EX1`
- Question: `GE{year}{board}{paper}{2-digit import year}{3-digit seq}` → `GE17EX126001`
- Sub-part: Append letter → `GE17EX126001A`, `GE17EX126001B`
- Import year auto-set to current year (2026→26, 2027→27)

## What's Implemented
- PDF upload + GPT-5.2 vision extraction (23 questions from 20 pages)
- Two-pass AI diagram cropping (bounding box + refinement)
- GE ID system with parent-child chain
- LaTeX rendering (KaTeX) - handles \text{}, \frac{}, mixed content
- Mark scheme upload + extraction + auto-linking
- Difficulty tagging (Bronze/Silver/Gold)
- 30 GCSE topics across 4 categories
- Editable fields: text, marks, parts, images (replace/add/remove)
- Re-extract button for improved re-processing
- Shared images across question parts

## Next
- Test mark scheme upload end-to-end
- Hostinger database sync/offline copy
- AI answer recommendation module (Google/Anthropic keys)
