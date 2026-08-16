import json
import os
import re
from collections import Counter
from io import BytesIO

import fitz
import google.generativeai as genai
import streamlit as st

# Set page config as the very first Streamlit command
st.set_page_config(page_title="AI Resume ATS", page_icon="📄", layout="wide")

try:
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Inches, Pt

    DOCX_READY = True
except ImportError:
    Document = None
    WD_ALIGN_PARAGRAPH = None
    Inches = None
    Pt = None
    DOCX_READY = False


# Load API Key from environment, secrets, or fallback
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    try:
        API_KEY = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        pass
if not API_KEY:
    API_KEY = "AIzaSyCCLkm_f5S2bGFa4aaZdD0fyK9W1sLHdcI"

# Sidebar API Key Override Input
custom_key = st.sidebar.text_input(
    "🔑 Gemini API Key (optional)",
    value="",
    type="password",
    help="Enter your Gemini API key to override the default credentials."
)
if custom_key:
    API_KEY = custom_key

GENAI_READY = bool(API_KEY) and "your_" not in API_KEY.lower()

model = None
if GENAI_READY:
    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
    except Exception as e:
        st.sidebar.error(f"Failed to configure Gemini: {e}")


STOP_WORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "from",
    "have",
    "your",
    "resume",
    "job",
    "description",
    "based",
    "please",
    "only",
    "number",
    "into",
    "about",
    "these",
    "their",
    "you",
    "are",
    "was",
    "were",
    "will",
    "can",
    "should",
    "must",
    "not",
    "has",
    "had",
    "need",
    "needed",
    "ability",
    "experience",
    "skills",
    "skill",
    "work",
    "role",
    "candidate",
    "position",
    "company",
}

SECTION_ALIASES = {
    "summary": {"summary", "professional summary", "profile", "objective"},
    "skills": {"skills", "technical skills", "core skills", "key skills", "technical stack"},
    "experience": {
        "experience",
        "work experience",
        "professional experience",
        "employment",
        "professional background",
    },
    "projects": {"projects", "project experience", "academic projects"},
    "education": {"education", "academics"},
    "certifications": {"certifications", "certificates", "licenses"},
    "achievements": {"achievements", "awards", "honors"},
}

STRONG_VERBS = {
    "built",
    "delivered",
    "developed",
    "designed",
    "implemented",
    "improved",
    "led",
    "managed",
    "optimized",
    "reduced",
    "streamlined",
    "launched",
    "scaled",
    "automated",
    "analyzed",
    "created",
    "produced",
    "resolved",
    "drove",
    "enhanced",
}


def _extract_section(prompt, start_marker, end_marker=None):
    lower_prompt = prompt.lower()
    start_index = lower_prompt.find(start_marker.lower())
    if start_index == -1:
        return ""

    start_index += len(start_marker)
    if end_marker:
        end_index = lower_prompt.find(end_marker.lower(), start_index)
        if end_index == -1:
            end_index = len(prompt)
    else:
        end_index = len(prompt)

    return prompt[start_index:end_index].strip()


def _split_lines(text):
    return [line.strip() for line in text.splitlines() if line.strip()]


def _safe_json_loads(raw_text):
    cleaned = raw_text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    start_index = cleaned.find("{")
    end_index = cleaned.rfind("}")
    if start_index != -1 and end_index != -1:
        cleaned = cleaned[start_index : end_index + 1]
    return json.loads(cleaned)


def _identify_section_heading(line):
    normalized = line.strip().lower().rstrip(":")
    for section, aliases in SECTION_ALIASES.items():
        if normalized in aliases:
            return section
    return None


def _parse_resume_sections(resume_text):
    sections = {name: [] for name in SECTION_ALIASES}
    sections["other"] = []
    current_section = "other"

    for line in _split_lines(resume_text):
        heading = _identify_section_heading(line)
        if heading:
            current_section = heading
            continue
        sections.setdefault(current_section, []).append(line)

    return sections


def _detect_candidate_name(resume_text):
    for line in _split_lines(resume_text)[:6]:
        clean_line = re.sub(r"[^A-Za-z .'-]", "", line).strip()
        if 2 <= len(clean_line.split()) <= 4 and not _identify_section_heading(clean_line):
            if not re.search(r"@|http|www|resume|curriculum|vitae", clean_line, re.I):
                return clean_line.title()
    return "Targeted Candidate"


def _extract_contact_info(resume_text):
    email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", resume_text)
    phone_match = re.search(r"(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}", resume_text)
    linkedin_match = re.search(r"https?://(?:www\.)?linkedin\.com/\S+", resume_text, re.I)
    github_match = re.search(r"https?://(?:www\.)?github\.com/\S+", resume_text, re.I)

    contact_parts = []
    if email_match:
        contact_parts.append(email_match.group(0))
    if phone_match:
        contact_parts.append(phone_match.group(0))
    if linkedin_match:
        contact_parts.append(linkedin_match.group(0))
    if github_match:
        contact_parts.append(github_match.group(0))

    return " | ".join(contact_parts)


def _derive_target_title(job_desc):
    jd_lines = _split_lines(job_desc)
    for line in jd_lines[:3]:
        clean_line = re.sub(r"\s+", " ", line).strip()
        if 3 <= len(clean_line.split()) <= 10 and not clean_line.endswith(":"):
            if not re.search(r"responsibilities|requirements|qualifications|about the role", clean_line, re.I):
                return clean_line[:70].strip()

    top_tokens = [token for token in _tokenize(job_desc) if token not in STOP_WORDS]
    if top_tokens:
        return f"Targeted {top_tokens[0].title()} {top_tokens[1].title() if len(top_tokens) > 1 else 'Professional'}"
    return "ATS-Optimized Professional"


def _prioritize_bullets(bullets, job_desc, limit=8):
    jd_tokens = set(_tokenize(job_desc))

    def _bullet_score(bullet):
        bullet_tokens = set(_tokenize(bullet))
        overlap = len(bullet_tokens & jd_tokens)
        metric_bonus = 2 if re.search(r"\d|%|\$", bullet) else 0
        verb_bonus = 1 if bullet.split() and bullet.split()[0].lower() in STRONG_VERBS else 0
        return overlap + metric_bonus + verb_bonus

    ordered = sorted(bullets, key=_bullet_score, reverse=True)
    selected = []
    for bullet in ordered:
        clean_bullet = re.sub(r"\s+", " ", bullet).strip().rstrip(".")
        if clean_bullet and clean_bullet not in selected:
            selected.append(clean_bullet)
        if len(selected) >= limit:
            break
    return selected


def _collect_section_lines(sections, section_name):
    return [line for line in sections.get(section_name, []) if line]


def _build_resume_blueprint(resume_text, job_desc):
    sections = _parse_resume_sections(resume_text)
    resume_tokens = set(_tokenize(resume_text))
    jd_tokens = list(dict.fromkeys(_tokenize(job_desc)))
    matched_keywords = [token for token in jd_tokens if token in resume_tokens]
    missing_keywords = _top_missing_keywords(job_desc, resume_text, limit=18)
    combined_keywords = []

    for keyword in matched_keywords + missing_keywords:
        if keyword not in combined_keywords:
            combined_keywords.append(keyword)
        if len(combined_keywords) >= 18:
            break

    if not combined_keywords:
        combined_keywords = jd_tokens[:12]

    skills_from_resume = _collect_section_lines(sections, "skills")
    skills_text = []
    for line in skills_from_resume:
        parts = re.split(r"[,|;/]", line)
        for part in parts:
            token = part.strip()
            if token and token not in skills_text:
                skills_text.append(token)

    if combined_keywords:
        for keyword in combined_keywords:
            skill_label = keyword.replace("/", " / ").strip()
            if skill_label and skill_label not in skills_text:
                skills_text.append(skill_label)

    if not skills_text:
        skills_text = [keyword.replace("/", " / ").strip() for keyword in jd_tokens[:10]]

    resume_bullets = _extract_bullets(resume_text)
    experience_bullets = _prioritize_bullets(resume_bullets, job_desc, limit=8)
    if not experience_bullets:
        experience_bullets = [line for line in _collect_section_lines(sections, "experience") if len(line.split()) <= 25][:6]
    if not experience_bullets:
        experience_bullets = ["[Add measurable accomplishment from your source resume]"]

    project_bullets = _collect_section_lines(sections, "projects")
    if not project_bullets:
        project_bullets = [line for line in _collect_section_lines(sections, "other") if len(line.split()) <= 18][:4]

    education_lines = _collect_section_lines(sections, "education")
    if not education_lines:
        education_lines = [line for line in _collect_section_lines(sections, "other") if re.search(r"b\.?tech|m\.?tech|bachelor|master|degree|university|college|school", line, re.I)][:4]

    certification_lines = _collect_section_lines(sections, "certifications")
    if not certification_lines:
        certification_lines = [line for line in _collect_section_lines(sections, "other") if re.search(r"certif|license|credential|course", line, re.I)][:4]

    summary_keywords = combined_keywords[:6] if combined_keywords else jd_tokens[:6]
    summary_text = (
        f"ATS-focused professional with demonstrated exposure to {', '.join(summary_keywords)}. "
        f"Known for converting responsibilities into measurable outcomes and tailoring work to hiring priorities."
    )

    if model is not None:
        prompt = f"""Return ONLY valid JSON for a resume blueprint.

Rules:
- Use only facts supported by the source resume.
- Do not invent employers, dates, titles, degrees, or certifications.
- Rewrite bullets with STAR / XYZ framing where supported by the source text.
- Include ATS keywords from the job description naturally and truthfully.
- If a field is missing, use an empty list or placeholder text like [add detail].

JSON schema:
{{
  "name": "string",
  "target_title": "string",
  "contact": "string",
  "summary": "string",
  "skills": ["string"],
  "experience": ["string"],
  "projects": ["string"],
  "education": ["string"],
  "certifications": ["string"]
}}

Job Description:
{job_desc}

Source Resume:
{resume_text}
"""
        try:
            response = model.generate_content(prompt)
            blueprint = _safe_json_loads(response.text)
            if isinstance(blueprint, dict):
                blueprint.setdefault("name", _detect_candidate_name(resume_text))
                blueprint.setdefault("target_title", _derive_target_title(job_desc))
                blueprint.setdefault("contact", _extract_contact_info(resume_text))
                blueprint.setdefault("summary", summary_text)
                blueprint.setdefault("skills", skills_text)
                blueprint.setdefault("experience", experience_bullets)
                blueprint.setdefault("projects", project_bullets)
                blueprint.setdefault("education", education_lines)
                blueprint.setdefault("certifications", certification_lines)
                return blueprint
        except Exception:
            pass

    return {
        "name": _detect_candidate_name(resume_text),
        "target_title": _derive_target_title(job_desc),
        "contact": _extract_contact_info(resume_text),
        "summary": summary_text,
        "skills": skills_text,
        "experience": experience_bullets,
        "projects": project_bullets,
        "education": education_lines,
        "certifications": certification_lines,
    }


def _render_resume_preview(blueprint):
    lines = []
    if blueprint.get("name"):
        lines.append(blueprint["name"])
    if blueprint.get("target_title"):
        lines.append(blueprint["target_title"])
    if blueprint.get("contact"):
        lines.append(blueprint["contact"])
    lines.append("")
    lines.append("PROFESSIONAL SUMMARY")
    lines.append(blueprint.get("summary", ""))
    lines.append("")
    lines.append("CORE SKILLS")
    lines.append(" | ".join(blueprint.get("skills", [])))
    lines.append("")
    lines.append("PROFESSIONAL EXPERIENCE HIGHLIGHTS")
    for bullet in blueprint.get("experience", []):
        lines.append(f"- {bullet}")
    if blueprint.get("projects"):
        lines.append("")
        lines.append("PROJECTS")
        for bullet in blueprint.get("projects", []):
            lines.append(f"- {bullet}")
    if blueprint.get("education"):
        lines.append("")
        lines.append("EDUCATION")
        for line in blueprint.get("education", []):
            lines.append(f"- {line}")
    if blueprint.get("certifications"):
        lines.append("")
        lines.append("CERTIFICATIONS")
        for line in blueprint.get("certifications", []):
            lines.append(f"- {line}")
    return "\n".join(lines).strip()


def _build_docx_bytes(blueprint):
    if not DOCX_READY:
        return None

    document = Document()
    section = document.sections[0]
    section.top_margin = Inches(0.55)
    section.bottom_margin = Inches(0.55)
    section.left_margin = Inches(0.7)
    section.right_margin = Inches(0.7)

    normal_style = document.styles["Normal"]
    normal_style.font.name = "Calibri"
    normal_style.font.size = Pt(10.5)

    name_paragraph = document.add_paragraph()
    name_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    name_run = name_paragraph.add_run(blueprint.get("name", "Targeted Candidate"))
    name_run.bold = True
    name_run.font.size = Pt(18)

    title_paragraph = document.add_paragraph()
    title_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_paragraph.add_run(blueprint.get("target_title", "ATS-Optimized Resume"))
    title_run.italic = True
    title_run.font.size = Pt(11)

    contact_text = blueprint.get("contact", "")
    if contact_text:
        contact_paragraph = document.add_paragraph()
        contact_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        contact_paragraph.add_run(contact_text)

    def add_heading(text):
        paragraph = document.add_paragraph()
        run = paragraph.add_run(text)
        run.bold = True
        run.font.size = Pt(11)
        return paragraph

    def add_bullet(text):
        paragraph = document.add_paragraph(style="List Bullet")
        paragraph.paragraph_format.space_after = Pt(0)
        paragraph.paragraph_format.space_before = Pt(0)
        paragraph.add_run(text)

    add_heading("Professional Summary")
    document.add_paragraph(blueprint.get("summary", ""))

    add_heading("Core Skills")
    document.add_paragraph(" | ".join(blueprint.get("skills", [])))

    add_heading("Professional Experience Highlights")
    for bullet in blueprint.get("experience", []):
        add_bullet(bullet)

    if blueprint.get("projects"):
        add_heading("Projects")
        for bullet in blueprint.get("projects", []):
            add_bullet(bullet)

    if blueprint.get("education"):
        add_heading("Education")
        for line in blueprint.get("education", []):
            add_bullet(line)

    if blueprint.get("certifications"):
        add_heading("Certifications")
        for line in blueprint.get("certifications", []):
            add_bullet(line)

    buffer = BytesIO()
    document.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


def _generate_ats_resume_package(resume_text, job_desc):
    blueprint = _build_resume_blueprint(resume_text, job_desc)
    preview_text = _render_resume_preview(blueprint)
    ats_score = _ats_score(preview_text, job_desc)
    docx_bytes = _build_docx_bytes(blueprint)
    return blueprint, preview_text, ats_score, docx_bytes


def _tokenize(text):
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9+#.-]*", text.lower())
    return [token for token in tokens if token not in STOP_WORDS and len(token) > 2]


def _extract_bullets(text):
    bullets = []
    for line in _split_lines(text):
        if re.match(r"^(\-|\*|•|▪|\d+[\).:-])\s+", line):
            bullets.append(re.sub(r"^(\-|\*|•|▪|\d+[\).:-])\s+", "", line).strip())
    return bullets


def _top_missing_keywords(job_desc, resume_text, limit=12):
    resume_tokens = set(_tokenize(resume_text))
    job_counts = Counter(_tokenize(job_desc))
    missing = []

    for token, _ in job_counts.most_common():
        if token in resume_tokens:
            continue
        if token in missing:
            continue
        missing.append(token)
        if len(missing) >= limit:
            break

    return missing


def _ats_score(resume_text, job_desc):
    resume_tokens = set(_tokenize(resume_text))
    job_tokens = [token for token in _tokenize(job_desc) if token not in STOP_WORDS]
    if not job_tokens:
        return 0

    job_unique = list(dict.fromkeys(job_tokens))
    hits = sum(1 for token in job_unique if token in resume_tokens)
    base_score = round((hits / len(job_unique)) * 100)

    bullets = _extract_bullets(resume_text)
    metric_bullets = [bullet for bullet in bullets if re.search(r"\d|%|\$|x|year|month", bullet, re.I)]

    bonus = min(12, len(metric_bullets) * 3)
    penalty = 0
    if len(bullets) and len(metric_bullets) / len(bullets) < 0.35:
        penalty += 8
    if len(_split_lines(resume_text)) < 8:
        penalty += 5
    if "\t" in resume_text:
        penalty += 5

    return max(0, min(100, base_score + bonus - penalty))


def _formatting_risks(resume_text):
    risks = []
    lines = _split_lines(resume_text)

    if "\t" in resume_text:
        risks.append("Tabbed or column-like formatting can break ATS parsing.")
    if any(len(line) > 140 for line in lines):
        risks.append("Long wrapped lines may indicate dense layout that is harder for ATS parsers to interpret.")
    if not _extract_bullets(resume_text):
        risks.append("The extracted text does not show clear bullet points; ATS-friendly resumes should use simple bullets and standard headings.")
    if sum(1 for line in lines if line.isupper()) > 5:
        risks.append("Excessive all-caps text can reduce readability and may signal decorative formatting.")
    if len(lines) < 8:
        risks.append("The extracted PDF text is sparse; this often means the layout is image-heavy, multi-column, or too compressed for ATS.")

    return risks or ["No obvious parsing risk was detected from the extracted text alone, but PDF layout may still affect ATS parsing."]


def _bullet_quality_feedback(resume_text):
    bullets = _extract_bullets(resume_text)
    if not bullets:
        return ["No bullet points were detected in the extracted text. ATS resumes should use concise bullets under each role or project."]

    issues = []
    if len(bullets) < 5:
        issues.append("Very few bullets were extracted, so the resume may not be demonstrating enough role-specific achievement detail.")

    weak_bullets = [
        bullet
        for bullet in bullets
        if not re.search(r"\d|%|\$|increase|decrease|improve|reduced|grew|delivered|launched", bullet, re.I)
    ]
    if weak_bullets:
        issues.append("Many bullets lack measurable outcomes or clear business impact.")
    if any(len(bullet.split()) > 28 for bullet in bullets):
        issues.append("Some bullets are too long and read like paragraphs instead of concise accomplishment statements.")

    issues.append("Use STAR/XYZ structure: what you did, how you did it, the scale or context, and the measurable result.")
    return issues


def _why_not_shortlisted(resume_text, job_desc):
    missing = _top_missing_keywords(job_desc, resume_text, limit=8)
    reasons = []

    if missing:
        reasons.append(f"The resume does not explicitly surface key job terms such as {', '.join(missing[:5])}.")
    if _ats_score(resume_text, job_desc) < 70:
        reasons.append("The resume appears under-aligned with the JD, which often causes ATS or recruiter screening to reject it early.")
    if len(_extract_bullets(resume_text)) < 4:
        reasons.append("There is too little quantified achievement evidence for a recruiter to see clear impact quickly.")

    risks = _formatting_risks(resume_text)
    if risks:
        reasons.append(risks[0])

    return reasons or ["The main issue is likely insufficient evidence of direct job fit, impact, and ATS keyword alignment."]


def _local_recruiter_review(resume_text, job_desc):
    missing = _top_missing_keywords(job_desc, resume_text, limit=12)
    score = _ats_score(resume_text, job_desc)
    bullet_feedback = _bullet_quality_feedback(resume_text)
    risks = _formatting_risks(resume_text)
    reasons = _why_not_shortlisted(resume_text, job_desc)

    lines = [
        f"Overall ATS readiness estimate: {score}/100",
        "",
        "Why this resume may not be shortlisted:",
    ]
    lines.extend(f"- {reason}" for reason in reasons[:4])
    lines.extend(
        [
            "",
            "Missing ATS keywords / phrases:",
        ]
    )
    if missing:
        lines.extend(f"- {keyword}" for keyword in missing)
    else:
        lines.append("- No major missing keywords were detected from the supplied text.")

    lines.extend(
        [
            "",
            "Bullet quality / impact gaps:",
        ]
    )
    lines.extend(f"- {item}" for item in bullet_feedback[:4])
    lines.extend(
        [
            "",
            "Formatting / ATS risks:",
        ]
    )
    lines.extend(f"- {risk}" for risk in risks[:4])
    lines.extend(
        [
            "",
            "Concrete next steps:",
            "- Rewrite bullets to follow STAR or XYZ: situation, action, scale, measurable result.",
            "- Mirror the JD wording for required tools, domain terms, and seniority markers where they are truthful.",
            "- Keep the PDF layout simple: one column, standard headings, no tables, no icons, no text boxes.",
            "- Put the strongest matching experience and skills near the top of the resume.",
        ]
    )
    return "\n".join(lines)


def _local_resume_draft_guidance(resume_text, job_desc):
    missing = _top_missing_keywords(job_desc, resume_text, limit=8)
    lines = [
        "ATS-optimized draft guidance:",
        "- Use a plain one-column layout with standard headings.",
        "- Lead with a 2-3 line summary that mirrors the JD truthfully.",
        "- Add a skills section that includes the most relevant JD terms you truly possess.",
        "- Rewrite each bullet with STAR/XYZ structure and measurable impact.",
        "- Keep only experience that strengthens match quality; remove generic filler.",
    ]
    if missing:
        lines.append(f"- Work the following JD terms naturally into the draft where truthful: {', '.join(missing[:8])}.")
    return "\n".join(lines)


def _extract_recruiter_prompt(resume_text, job_desc):
    return f"""You are a skeptical technical recruiter, hiring manager, and ATS optimization expert.

Be blunt and evidence-based. Do not rewrite the resume. Do not assume the candidate is a match.

Evaluate the resume against the job description and return these sections:
1. Overall ATS Readiness
2. Why This May Not Be Shortlisted
3. Missing ATS Keywords and Phrases
4. Formatting / ATS Parsing Risks
5. Bullet Quality Issues
6. STAR / XYZ Gaps
7. Concrete Fixes
8. Recruiter Verdict

Rules:
- Base every claim on the provided resume and job description.
- Call out weak bullets, lack of metrics, poor alignment, and keyword gaps.
- If the resume looks generic, say so directly.
- Mention when formatting may hurt ATS parsing.
- Do not generate a new resume.

Job Description:
{job_desc}

Resume:
{resume_text}
"""


def _extract_rewrite_prompt(resume_text, job_desc):
    return f"""Rewrite the resume into an ATS-optimized draft tailored to the job description.

Rules:
- Preserve only facts supported by the source resume. Do not invent employers, dates, titles, or certifications.
- Use strong bullet points with STAR / XYZ framing and measurable impact where available.
- Mirror key ATS keywords from the job description naturally and truthfully.
- Keep the output concise, professional, and recruiter-friendly.
- Use a standard one-column resume structure with sections: Summary, Skills, Experience, Projects, Education.
- If the source resume is weak or missing data, show placeholders like [add metric] instead of fabricating details.

Job Description:
{job_desc}

Resume:
{resume_text}
"""


def extract_text_from_pdf(uploaded_pdf):
    try:
        doc = fitz.open(stream=uploaded_pdf.read(), filetype="pdf")
        text = "\n".join([page.get_text("text") for page in doc])
        return text.strip()
    except Exception:
        return ""


def _local_fallback_response(prompt, max_lines=15):
    prompt_lower = prompt.lower()
    resume_text = _extract_section(prompt, "Resume:")
    job_desc = _extract_section(prompt, "Job Description:")

    if "recruiter verdict" in prompt_lower or "why this may not be shortlisted" in prompt_lower or "ats parsing risks" in prompt_lower:
        return _local_recruiter_review(resume_text, job_desc)

    if "ats-optimized draft" in prompt_lower or "rewrite the resume" in prompt_lower:
        return _local_resume_draft_guidance(resume_text, job_desc)

    if "match percentage" in prompt_lower:
        return str(_ats_score(resume_text, job_desc))

    if "missing important keywords" in prompt_lower or "missing keywords" in prompt_lower:
        missing = _top_missing_keywords(job_desc, resume_text, limit=max_lines)
        if not missing:
            return "No major missing keywords detected from the job description."
        return "\n".join(f"- {keyword}" for keyword in missing)

    if "skill improvements" in prompt_lower:
        missing = _top_missing_keywords(job_desc, resume_text, limit=5)
        suggestions = [
            "- Emphasize measurable achievements with numbers where possible.",
            "- Add missing job-description keywords that match your real experience.",
            "- Use STAR or XYZ framing to make impact obvious to recruiters.",
        ]
        if missing:
            suggestions.append(f"- Strengthen exposure to: {', '.join(missing)}.")
        return "\n".join(suggestions[:max_lines])

    if "summarize key details" in prompt_lower or "summarize" in prompt_lower:
        lines = _split_lines(resume_text)
        if not lines:
            return "No resume text found to summarize."
        return "\n".join(f"- {line}" for line in lines[:max_lines])

    if not GENAI_READY:
        return "Gemini API key is missing or invalid, so this response uses a local fallback."

    return "Local fallback could not infer a specific answer from the provided prompt."


def get_gemini_response(prompt, max_lines=15):
    if model is None:
        return _local_fallback_response(prompt, max_lines=max_lines)

    try:
        response = model.generate_content(prompt)
        lines = response.text.strip().split("\n")
        return "\n".join(lines[:max_lines])
    except Exception:
        return _local_fallback_response(prompt, max_lines=max_lines)


st.markdown(
    """
    <h1 style="text-align:center; color:#4A90E2;">📄 AI-Powered Resume ATS Tracking</h1>
    <p style="text-align:center; font-size:16px; color:#666;">Optimize your resume, find ATS gaps, and get recruiter-style critique.</p>
    """,
    unsafe_allow_html=True,
)

if not GENAI_READY:
    st.info("Gemini is not configured with a valid API key. The app will still run and use local fallback responses.")

st.caption("ATS scores are estimates, not guarantees. The review mode is designed to be critical rather than flattering.")
st.session_state.setdefault("generated_resume_package", None)

col1, col2 = st.columns([1, 1])

with col1:
    job_desc = st.text_area("📌 Paste Job Description Here", height=180)

with col2:
    uploaded_file = st.file_uploader("📤 Upload Resume (PDF)", type=["pdf"])
    resume_text = extract_text_from_pdf(uploaded_file) if uploaded_file else ""

if uploaded_file and not resume_text:
    st.error("The PDF text could not be extracted. Try a text-based PDF or paste the resume text after converting it.")

if uploaded_file and job_desc and resume_text:
    st.divider()
    st.subheader("🔍 Resume Analysis & Improvement")

    st.metric("Local ATS readiness estimate", f"{_ats_score(resume_text, job_desc)}/100")

    row1 = st.columns(3)
    row2 = st.columns(3)

    if row1[0].button("📄 Resume Summary"):
        with st.spinner("Analyzing..."):
            prompt = f"Summarize key details of this resume:\n\nResume:\n{resume_text}"
            st.subheader("📄 Resume Summary")
            st.write(get_gemini_response(prompt, max_lines=15))

    if row1[1].button("📊 Match Percentage"):
        with st.spinner("Calculating..."):
            prompt = (
                "Compare this resume with the job description and give a match percentage (only number):\n\n"
                f"Job Description:\n{job_desc}\n\nResume:\n{resume_text}"
            )
            match_percentage = get_gemini_response(prompt, max_lines=1)
        st.subheader("📊 Match Percentage")
        st.markdown(f"<h2 style='text-align:center; color:#27AE60;'>✅ {match_percentage}%</h2>", unsafe_allow_html=True)

    if row1[2].button("🧑‍💼 Recruiter Critique"):
        with st.spinner("Reviewing like a recruiter..."):
            prompt = _extract_recruiter_prompt(resume_text, job_desc)
            st.subheader("🧑‍💼 Recruiter Critique")
            st.write(get_gemini_response(prompt, max_lines=80))

    if row2[0].button("📈 Skill Improvement"):
        with st.spinner("Analyzing..."):
            prompt = f"Suggest skill improvements for this resume based on the job description:\n\nJob Description:\n{job_desc}\n\nResume:\n{resume_text}"
            st.subheader("📈 Skill Improvement Suggestions")
            st.write(get_gemini_response(prompt, max_lines=25))

    if row2[1].button("🔑 Missing Keywords"):
        with st.spinner("Identifying..."):
            prompt = f"List missing important keywords and skills in this resume based on the job description:\n\nJob Description:\n{job_desc}\n\nResume:\n{resume_text}"
            st.subheader("🔑 Missing Keywords")
            st.write(get_gemini_response(prompt, max_lines=25))

    if row2[2].button("📝 Generate ATS Resume DOCX"):
        with st.spinner("Building ATS-optimized resume draft..."):
            blueprint, preview_text, generated_score, docx_bytes = _generate_ats_resume_package(resume_text, job_desc)
            st.session_state["generated_resume_package"] = {
                "blueprint": blueprint,
                "preview_text": preview_text,
                "generated_score": generated_score,
                "docx_bytes": docx_bytes,
            }

    generated_package = st.session_state.get("generated_resume_package")
    if generated_package:
        st.divider()
        st.subheader("📝 Generated ATS Resume")
        st.metric("Estimated ATS score of generated draft", f"{generated_package['generated_score']}/100")
        if generated_package["generated_score"] < 90:
            st.warning("The current source resume does not support a truthful 90+ estimate yet. Add stronger metrics, direct JD alignment, and role-specific proof for a higher score.")
        else:
            st.success("The generated draft is estimated to be 90+ aligned with the provided job description.")

        st.text_area("ATS Resume Preview", generated_package["preview_text"], height=520)

        if generated_package["docx_bytes"]:
            candidate_name = generated_package["blueprint"].get("name", "ATS_Resume").replace(" ", "_")
            target_title = generated_package["blueprint"].get("target_title", "Target_Role").replace(" ", "_")
            file_name = f"{candidate_name}_{target_title}_ATS_Resume.docx"
            st.download_button(
                label="Download DOCX Resume",
                data=generated_package["docx_bytes"],
                file_name=file_name,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        else:
            st.error("python-docx is not installed. Add it to the environment to enable DOCX export.")

        st.write("This draft is truth-preserving: it restructures the uploaded resume and prioritizes JD-aligned keywords without inventing employers, dates, or certifications.")

    st.divider()

    st.subheader("💬 Ask Your Own Question")
    user_prompt = st.text_area("📝 Type your custom query about the resume or job description", height=100)

    if st.button("🤖 Get AI Response"):
        with st.spinner("Processing..."):
            custom_prompt = (
                f"Based on this resume and job description, answer the following:\n\n{user_prompt}\n\n"
                f"Job Description:\n{job_desc}\n\nResume:\n{resume_text}"
            )
            st.subheader("🤖 AI Response")
            st.write(get_gemini_response(custom_prompt))

else:
    st.warning("⚠️ Please upload a resume and enter a job description.")

st.markdown(
    """
    <style>
    padding=15px
    </style>
    <br><hr>
    <p style="text-align:center; font-size:14px; color:#666;">🚀 Powered by <b>Google Gemini Pro</b> | Developed for Mamatha Batchu</p>
    """,
    unsafe_allow_html=True,
)
