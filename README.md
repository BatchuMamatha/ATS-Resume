# 📄 AI-Powered Resume ATS Tracker | Google Gemini Pro

## 🚀 Project Overview
This AI-powered Resume ATS (Applicant Tracking System) helps job seekers optimize their resumes by analyzing job descriptions and providing:

✅ **Resume Match Percentage** – Get an exact match score with the job description 📊  
✅ **Missing Keywords** – Identify important terms missing from your resume 🔑  
✅ **Skill Improvement Suggestions** – Enhance your resume based on AI recommendations 📈  
✅ **Resume Summary** – Get a concise AI-generated summary of your resume 📄  
✅ **Recruiter-Style Critique** – See why a resume may not be shortlisted, including ATS, formatting, and impact gaps 🧑‍💼  
✅ **ATS Resume Draft Guidance** – Generate a truth-preserving, ATS-friendly rewrite draft with STAR/XYZ guidance ✍️  
✅ **DOCX Resume Export** – Download a clean, one-column ATS resume draft as a Word document 📄  
✅ **Custom AI Queries** – Ask specific questions about your resume and job description 💬  

## 🛠 Tech Stack
- **Google Gemini Pro 1.5** – Advanced AI-driven insights
- **Streamlit** – Interactive UI
- **PyMuPDF (Fitz)** – Extracting text from PDF resumes
- **Python** – Local analysis and fallback processing
- **python-docx** – Building downloadable DOCX resumes

## 💻 How to Run Locally?

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/BatchuMamatha/ATS-Resume.git
```

### 2️⃣ Create a Virtual Environment (Recommended: Conda)
#### Using Conda:
```bash
# Create a new environment named 'venv'
conda create --name venv python=3.10  

# Activate the environment  
conda activate venv  
```
#### Alternatively, using venv:
```bash
python -m venv venv  
source venv/bin/activate  # On macOS/Linux  
venv\Scripts\activate     # On Windows  
```

### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt  
```

### 4️⃣ Create a `.env` File & Add API Key
```bash
touch .env  
echo "API_KEY=your_google_api_key" > .env  
```

If the API key is missing or invalid, the app still runs and uses local ATS heuristics plus recruiter-style critique.

Upload a resume PDF and paste a job description, then use the DOCX generator to build a new ATS-friendly draft that is grounded in the source resume and tailored to the JD.

### 5️⃣ Run the Streamlit App
```bash
streamlit run resume.py  
```

### 6️⃣ Open in Your Browser
Once the server starts, open the provided URL in your browser to access the AI-powered Resume ATS.

The app is intentionally critique-first: it explains why a resume is weak, which ATS keywords are missing, where bullet points lack impact, and what to fix before generating a rewrite.

---
## 👩‍💻 Contributors
Developed by: **Mamatha Batchu**

## 📜 License
This project is open-source and available under the MIT License.

🚀 **Optimize your resume today & land your dream job!**
