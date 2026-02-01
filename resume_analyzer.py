"""Resume analysis module - extracts skills, experience, projects from candidate resume."""
import json
import re
from typing import Optional
from pypdf import PdfReader


def extract_text_from_pdf(file) -> str:
    """Extract text from PDF file."""
    try:
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text.strip()
    except Exception as e:
        raise ValueError(f"Failed to parse PDF: {str(e)}")


def analyze_resume(resume_text: str, api_key: Optional[str] = None) -> dict:
    """
    Analyze resume and extract structured information using AI or rule-based fallback.
    Returns: skills, experience, projects, education, role_relevance
    """
    if not resume_text or not resume_text.strip():
        return {
            "skills": [],
            "experience": [],
            "projects": [],
            "education": [],
            "summary": "",
            "role_relevance": "general",
        }

    # Rule-based extraction as fallback (works without API)
    skills = _extract_skills_rulebased(resume_text)
    experience = _extract_experience_rulebased(resume_text)
    projects = _extract_projects_rulebased(resume_text)
    education = _extract_education_rulebased(resume_text)

    # Try AI enhancement if API key available
    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            enhanced = _enhance_with_ai(client, resume_text, skills, experience, projects)
            if enhanced:
                return enhanced
        except Exception:
            pass  # Fall back to rule-based

    return {
        "skills": skills,
        "experience": experience,
        "projects": projects,
        "education": education,
        "summary": resume_text[:500] + "..." if len(resume_text) > 500 else resume_text,
        "role_relevance": "general",
    }


def _extract_skills_rulebased(text: str) -> list:
    """Extract skills using common tech skill patterns."""
    tech_skills = [
        "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust", "Kotlin", "Swift",
        "SQL", "NoSQL", "MongoDB", "PostgreSQL", "MySQL", "Redis",
        "React", "Angular", "Vue", "Node.js", "Django", "Flask", "FastAPI", "Spring Boot",
        "Machine Learning", "Deep Learning", "NLP", "Computer Vision", "TensorFlow", "PyTorch", "scikit-learn",
        "AWS", "Azure", "GCP", "Docker", "Kubernetes", "CI/CD", "Git", "Linux",
        "Data Structures", "Algorithms", "System Design", "REST API", "GraphQL", "Microservices",
        "Pandas", "NumPy", "Data Analysis", "ETL", "Data Engineering",
        "Agile", "Scrum", "JIRA", "GitHub", "GitLab",
    ]
    text_lower = text.lower()
    found = []
    for skill in tech_skills:
        if skill.lower() in text_lower:
            found.append(skill)
    # Also look for common section headers and extract from skills section
    skills_section = re.search(r"(?:skills?|technical skills?|technologies?)[:\s]+([\s\S]*?)(?=\n\n|experience|education|projects|$)", text, re.I)
    if skills_section:
        section_text = skills_section.group(1)
        for skill in tech_skills:
            if skill.lower() in section_text.lower() and skill not in found:
                found.append(skill)
    return list(dict.fromkeys(found)) if found else tech_skills[:5]  # Default to common skills


def _extract_experience_rulebased(text: str) -> list:
    """Extract experience entries."""
    experiences = []
    # Look for common job title patterns with optional date prefix
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if re.search(r"(?:Software Engineer|Developer|Data Scientist|ML Engineer|Backend|Frontend|Full Stack|Intern)[^,\n]*", line, re.I):
            period = lines[i - 1].strip() if i > 0 and re.search(r"\d{4}|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec", lines[i - 1]) else ""
            details = "\n".join(lines[i + 1 : i + 4]) if i + 1 < len(lines) else ""
            experiences.append({"period": period, "title": line.strip(), "details": details[:200]})
            if len(experiences) >= 5:
                break
    if not experiences:
        # Fallback: look for job title patterns
        titles = re.findall(r"(?:Software Engineer|Developer|Data Scientist|ML Engineer|Backend|Frontend|Full Stack)[^,\n]*", text, re.I)
        for t in titles[:3]:
            experiences.append({"period": "", "title": t.strip(), "details": ""})
    return experiences


def _extract_projects_rulebased(text: str) -> list:
    """Extract project information."""
    projects = []
    proj_section = re.search(r"(?:projects?|key projects?)[:\s]*([\s\S]*?)(?=\n\n(?:education|experience|skills|$))", text, re.I)
    if proj_section:
        content = proj_section.group(1)
        lines = [l.strip() for l in content.split("\n") if len(l.strip()) > 10]
        for line in lines[:5]:
            projects.append({"name": line[:80], "description": line})
    if not projects:
        bullet_match = re.findall(r"[-•]\s*(.+?)(?=\n[-•]|\n\n|$)", text, re.S)
        for b in bullet_match[:3]:
            if len(b) > 30 and any(kw in b.lower() for kw in ["built", "developed", "implemented", "designed", "created"]):
                projects.append({"name": b[:50] + "...", "description": b})
    return projects


def _extract_education_rulebased(text: str) -> list:
    """Extract education."""
    edu = []
    edu_section = re.search(r"(?:education|academic)[:\s]*([\s\S]*?)(?=\n\n(?:experience|skills|projects|$))", text, re.I)
    if edu_section:
        content = edu_section.group(1)
        for line in content.split("\n")[:3]:
            if line.strip() and len(line.strip()) > 5:
                edu.append(line.strip())
    return edu


def _enhance_with_ai(client, resume_text: str, skills: list, experience: list, projects: list) -> Optional[dict]:
    """Use OpenAI to enhance resume analysis."""
    try:
        prompt = f"""Analyze this tech resume and return a JSON object with:
- "skills": list of technical skills (programming languages, frameworks, tools)
- "experience": list of objects with "title", "company" (if found), "period", "highlights"
- "projects": list of objects with "name", "description", "tech_stack"
- "education": list of education entries
- "role_relevance": one of "backend", "frontend", "fullstack", "data_science", "ml_engineer", "devops", "general"

Resume:
{resume_text[:4000]}

Return ONLY valid JSON, no markdown."""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = re.sub(r"^```\w*\n?", "", content).replace("```", "").strip()
        data = json.loads(content)
        return {
            "skills": data.get("skills", skills),
            "experience": data.get("experience", experience),
            "projects": data.get("projects", projects),
            "education": data.get("education", []),
            "summary": resume_text[:500],
            "role_relevance": data.get("role_relevance", "general"),
        }
    except Exception:
        return None
