import streamlit as st
import google.generativeai as genai
import fitz  # PyMuPDF for extracting text from resumes
from dotenv import load_dotenv
import os

# Load API Key
load_dotenv()
genai.configure(api_key=os.getenv("API_KEY"))

# Initialize Gemini Model
model = genai.GenerativeModel("gemini-1.5-flash")

# Extract text from PDF resume
def extract_text_from_pdf(uploaded_pdf):
    doc = fitz.open(stream=uploaded_pdf.read(), filetype="pdf")
    text = "\n".join([page.get_text("text") for page in doc])
    return text.strip()

# Get concise AI response
def get_gemini_response(prompt, max_lines=15):
    response = model.generate_content(prompt)
    lines = response.text.strip().split("\n")
    return "\n".join(lines[:max_lines])

# Set page config for better UI
st.set_page_config(page_title="AI Resume ATS", page_icon="📄", layout="wide")

# Header with styling
st.markdown(
    """
    <h1 style="text-align:center; color:#4A90E2;">📄 AI-Powered Resume ATS Tracking</h1>
    <p style="text-align:center; font-size:16px; color:#666;">Optimize your resume and improve job match with AI.</p>
    """,
    unsafe_allow_html=True,
)

# Layout using columns for responsiveness
col1, col2 = st.columns([1, 1])

with col1:
    job_desc = st.text_area("📌 Paste Job Description Here", height=90)

with col2:
    uploaded_file = st.file_uploader("📤 Upload Resume (PDF)", type=["pdf"])
    resume_text = extract_text_from_pdf(uploaded_file) if uploaded_file else None

if uploaded_file and job_desc:
    st.divider()
    st.subheader("🔍 Resume Analysis & Improvement")
    
    # Responsive button layout
    btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)

    # Resume Summary
    if btn_col1.button("📄 Resume Summary"):
        with st.spinner("Analyzing..."):
            prompt = f"Summarize key details of this resume:\n\n{resume_text}"
            st.subheader("📄 Resume Summary")
            st.write(get_gemini_response(prompt))

    # Percentage Match
    if btn_col2.button("📊 Match Percentage"):
        with st.spinner("Calculating..."):
            prompt = f"Compare this resume with the job description and give a match percentage (only number):\n\nJob Description:\n{job_desc}\n\nResume:\n{resume_text}"
            match_percentage = get_gemini_response(prompt, max_lines=1)
        st.subheader("📊 Match Percentage")
        st.markdown(f"<h2 style='text-align:center; color:#27AE60;'>✅ {match_percentage}%</h2>", unsafe_allow_html=True)

    # Skill Improvement Suggestions
    if btn_col3.button("📈 Skill Improvement"):
        with st.spinner("Analyzing..."):
            prompt = f"Suggest skill improvements for this resume based on the job description:\n\n{job_desc}\n\nResume:\n{resume_text}"
            st.subheader("📈 Skill Improvement Suggestions")
            st.write(get_gemini_response(prompt))

    # Missing Keywords
    if btn_col4.button("🔑 Missing Keywords"):
        with st.spinner("Identifying..."):
            prompt = f"List missing important keywords and skills in this resume based on the job description:\n\n{job_desc}\n\nResume:\n{resume_text}"
            st.subheader("🔑 Missing Keywords")
            st.write(get_gemini_response(prompt))

    # Divider
    st.divider()

    # Custom User Prompt
    st.subheader("💬 Ask Your Own Question")
    user_prompt = st.text_area("📝 Type your custom query about the resume or job description", height=100)

    if st.button("🤖 Get AI Response"):
        with st.spinner("Processing..."):
            custom_prompt = f"Based on this resume and job description, answer the following:\n\n{user_prompt}\n\nJob Description:\n{job_desc}\n\nResume:\n{resume_text}"
            st.subheader("🤖 AI Response")
            st.write(get_gemini_response(custom_prompt))

else:
    st.warning("⚠️ Please upload a resume and enter a job description.")

# Footer Styling
st.markdown(
    """
    <style>padding=15px</style>
    <br><hr>
    <p style="text-align:center; font-size:14px; color:#666;">🚀 Powered by <b>Google Gemini Pro</b> | Developed for Mamatha Batchu</p>
    """,
    unsafe_allow_html=True,
)
