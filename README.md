# 📄 AI-Powered Resume ATS Tracker | Google Gemini Pro

## 🚀 Project Overview
This AI-powered Resume ATS (Applicant Tracking System) helps job seekers optimize their resumes by analyzing job descriptions and providing:

✅ **Resume Match Percentage** – Get an exact match score with the job description 📊  
✅ **Missing Keywords** – Identify important terms missing from your resume 🔑  
✅ **Skill Improvement Suggestions** – Enhance your resume based on AI recommendations 📈  
✅ **Resume Summary** – Get a concise AI-generated summary of your resume 📄  
✅ **Custom AI Queries** – Ask specific questions about your resume and job description 💬  

## 🛠 Tech Stack
- **Google Gemini Pro 1.5** – Advanced AI-driven insights
- **Streamlit** – Interactive UI
- **PyMuPDF (Fitz)** – Extracting text from PDF resumes
- **Python & FastAPI** – Backend processing

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

### 5️⃣ Run the Streamlit App
```bash
streamlit run app.py  
```

### 6️⃣ Open in Your Browser
Once the server starts, open the provided URL in your browser to access the AI-powered Resume ATS.

---
## 👩‍💻 Contributors
Developed by: **Mamatha Batchu**

## 📜 License
This project is open-source and available under the MIT License.

🚀 **Optimize your resume today & land your dream job!**
