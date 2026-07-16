# ATS Resume Analyzer

An AI-assisted Streamlit app that evaluates a resume against a job description, highlights ATS gaps, and generates a structured ATS-focused resume draft.

## Project

This project is designed to help candidates improve resume-to-job alignment by combining:
- ATS-style scoring heuristics
- Keyword and skill gap detection
- Recruiter-style critical feedback
- AI-powered and local fallback analysis paths
- Downloadable ATS-optimized DOCX resume output

## Features

- Upload and parse resume content from PDF files
- Analyze resume fit against a pasted job description
- Generate:
  - Resume summary
  - Match percentage estimate
  - Missing keyword insights
  - Skill improvement suggestions
  - Recruiter critique
- Build an ATS-focused resume draft with:
  - In-app preview
  - Downloadable `.docx` output
- Ask custom Q&A prompts using resume + JD context
- Fall back to local logic when Gemini output is unavailable

## Tech Stack

- **Language:** Python
- **UI Framework:** Streamlit
- **AI Model Integration:** Google Generative AI (`gemini-1.5-flash`)
- **PDF Processing:** PyMuPDF (`fitz`)
- **Document Export:** `python-docx`

## Getting Started

1. Clone the repository and move into the project directory.
2. (Recommended) Create and activate a Python virtual environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Start the app:

```bash
streamlit run resume.py
```

## Prerequisites

- Python 3.9+ (recommended)
- `pip` package manager
- Internet access for Gemini-backed responses
- A valid Gemini API key configured in the app runtime path used by `resume.py`

## Usage

1. Launch the app.
2. Paste the target job description.
3. Upload a text-readable PDF resume.
4. Use the action buttons to run analysis (summary, match, critique, keywords, skills).
5. Generate and review the ATS draft.
6. Download the generated DOCX file.
7. Optionally ask custom resume/JD questions in the Q&A section.

## Roadmap

- Move API key handling to environment-variable-first loading
- Improve scoring transparency and explainability
- Add support for multi-format resume uploads (DOCX/TXT)
- Add automated tests for parser and scoring helpers
- Introduce modular package structure beyond a single-file app
- Add deployment-ready configuration and CI checks

## Architecture

Current implementation is centered in `resume.py`:

- **UI Layer (Streamlit):**
  - Input collection for job description and PDF
  - Action buttons and output rendering
  - Resume draft preview and download flow
- **Extraction Layer:**
  - PDF text extraction via PyMuPDF
  - Resume section parsing and normalization helpers
- **Analysis Layer:**
  - ATS estimate, missing keyword detection, and recruiter-style review helpers
  - Prompt builders for AI-assisted workflows
- **Generation Layer:**
  - Resume blueprint creation
  - Preview text rendering
  - DOCX byte generation for download
- **Response Layer:**
  - Gemini model response handling
  - Local fallback responses when AI output is unavailable

## Contributing

Contributions are welcome.

1. Fork the repository.
2. Create a feature/fix branch in your fork.
3. Make focused, well-tested changes.
4. Open a pull request with a clear summary of what changed and why.

For documentation improvements, keep section structure consistent and ensure usage instructions stay aligned with actual app behavior.
