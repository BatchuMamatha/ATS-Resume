📄 AI-Powered Resume ATS Tracker | Google Gemini Pro

🚀 Project Overview

This AI-powered Resume ATS (Applicant Tracking System) helps job seekers optimize their resumes by analyzing job descriptions and providing:

✅ Resume Match Percentage – Get an exact match score with the job description 📊✅ Missing Keywords – Identify important terms missing from your resume 🔑✅ Skill Improvement Suggestions – Enhance your resume based on AI recommendations 📈✅ Resume Summary – Get a concise AI-generated summary of your resume 📄✅ Custom AI Queries – Ask specific questions about your resume and job description 💬

🛠 Tech Stack

Google Gemini Pro 1.5 for advanced AI-driven insights

Streamlit for an interactive UI

PyMuPDF (Fitz) for extracting text from PDF resumes

Python & FastAPI for backend processing

💻 How to Run Locally?

1️⃣ Clone the Repository

 git clone https://github.com/yourusername/resume-ats-gemini.git  
 cd resume-ats-gemini  

2️⃣ Create a Virtual Environment using Conda (Recommended)

If you are using Conda to manage virtual environments, follow these steps:

 # Create a new environment named 'resume-ats'
 conda create --name resume-ats python=3.10  

 # Activate the environment  
 conda activate resume-ats  

Alternatively, if you prefer to use venv, run:

 python -m venv venv  
 source venv/bin/activate  # On macOS/Linux  
 venv\Scripts\activate     # On Windows  

3️⃣ Install Dependencies

 pip install -r requirements.txt  

4️⃣ Create a .env File & Add API Key

 touch .env  
 echo "API_KEY=your_google_api_key" > .env  

5️⃣ Run the Streamlit App

 streamlit run app.py  

6️⃣ Open in Your Browser

Once the server starts, open the provided URL in your browser to access the AI-powered Resume ATS.

👩‍💻 Contributors

Developed by: Mamatha Batchu

🚀 Optimize your resume today & land your dream job!

📜 License

This project is open-source and available under the MIT License.

