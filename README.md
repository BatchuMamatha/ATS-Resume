# ATS Resume Analyzer (Streamlit + Gemini)

A Streamlit app that compares a resume PDF against a job description and provides ATS-focused feedback, recruiter-style critique, and an ATS-oriented DOCX draft.

## What the app does

From `resume.py`, the app currently supports:

- Resume summary
- Match percentage estimate
- Missing keyword detection
- Skill improvement suggestions
- Recruiter-style critique (shortlisting gaps, STAR/XYZ issues, ATS risks)
- ATS resume draft generation (preview + downloadable `.docx`)
- Custom Q&A over resume + JD
- Local fallback analysis when Gemini is unavailable

## Tech stack

- Python
- Streamlit
- Google Generative AI (`gemini-1.5-flash`)
- PyMuPDF (`fitz`) for PDF text extraction
- `python-docx` for DOCX generation

## Repository files

- `/home/runner/work/ATS-Resume/ATS-Resume/resume.py` – main Streamlit application and analysis logic
- `/home/runner/work/ATS-Resume/ATS-Resume/requirements.txt` – Python dependencies
- `/home/runner/work/ATS-Resume/ATS-Resume/.env` – sample API key variable
- `/home/runner/work/ATS-Resume/ATS-Resume/README.md` – project documentation

## Setup

1. Clone and enter the project directory.
2. (Recommended) Create and activate a virtual environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Configure API key:

- Current code reads `API_KEY` directly from `resume.py`.
- `.env` contains `API_KEY="YOUR_API_KEY"`, but `resume.py` does not currently load from `.env`.

5. Run the app:

```bash
streamlit run resume.py
```

## Usage

1. Paste a job description.
2. Upload a text-based PDF resume.
3. Use analysis buttons to review ATS fit, missing keywords, and recruiter feedback.
4. Generate ATS resume draft and download DOCX.

## Notes

- ATS score is an estimate, not a guarantee.
- If Gemini fails or is not configured, the app uses local fallback logic.
- DOCX export requires `python-docx` (already listed in `requirements.txt`).
