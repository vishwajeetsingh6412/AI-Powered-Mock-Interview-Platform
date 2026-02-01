"""Job Description parser - extracts requirements and role alignment."""
import json
import re
from typing import Optional, List


def extract_dynamic_context(jd_text: str, jd_data: Optional[dict] = None) -> dict:
    """
    Extract dynamic terms from JD for question generation.
    Works with ANY job description - no fixed role list.
    """
    jd_data = jd_data or {}
    text = (jd_text or "").lower()
    skills = jd_data.get("required_skills", [])
    responsibilities = jd_data.get("key_responsibilities", [])
    role = jd_data.get("role", "Software Engineer")

    # Extract action verbs from responsibilities and full text
    action_verbs = ["build", "design", "develop", "implement", "optimize", "deploy", "manage",
                    "create", "improve", "scale", "integrate", "analyze", "maintain", "debug",
                    "evaluate", "monitor", "automate", "refactor", "test", "migrate"]
    found_verbs = [v for v in action_verbs if v in text]

    # Extract domain/context terms
    domain_terms = ["real-time", "scalable", "distributed", "high-traffic", "production",
                    "microservices", "cloud", "performance", "security", "reliable",
                    "large-scale", "data-driven", "user-facing", "mission-critical"]
    found_domains = [d for d in domain_terms if d in text]

    # Extract key phrases (responsibilities as question fodder)
    key_phrases = []
    for r in responsibilities[:5]:
        if isinstance(r, str) and len(r) > 10:
            # Take first meaningful part (before "and" or comma)
            phrase = re.split(r"\s+and\s+|\s*,\s*", r)[0].strip()[:80]
            if phrase:
                key_phrases.append(phrase)

    # Extract additional tech terms from raw text (beyond predefined list)
    tech_patterns = [
        r"\b(python|java|javascript|react|node\.?js|aws|docker|kubernetes|sql|nosql|mongodb|postgres|redis|kafka|spark|tensorflow|pytorch|ml|api|rest|graphql)\b",
        r"\b([a-z]+\.js|[a-z]+\.py)\b",
        r"\b(ci/cd|agile|scrum|tdd|bdd)\b",
    ]
    extra_techs = set()
    for pat in tech_patterns:
        for m in re.finditer(pat, text, re.I):
            t = m.group(1).lower()
            if len(t) > 2 and t not in {"the", "and", "for", "with"}:
                extra_techs.add(t.title())
    all_skills = list(dict.fromkeys(skills + list(extra_techs)))

    return {
        "role": role,
        "skills": all_skills[:10] or ["technical skills"],
        "skill": all_skills[0] if all_skills else "the role",
        "skill2": all_skills[1] if len(all_skills) > 1 else all_skills[0] if all_skills else "core technologies",
        "verbs": found_verbs[:5] or ["work with"],
        "verb": found_verbs[0] if found_verbs else "work with",
        "domains": found_domains[:3] or ["production"],
        "domain": found_domains[0] if found_domains else "production",
        "key_phrases": key_phrases[:5] or ["key responsibilities"],
        "phrase": key_phrases[0] if key_phrases else "your main responsibilities",
    }


def parse_job_description(jd_text: str, api_key: Optional[str] = None) -> dict:
    """
    Parse job description to extract role, required skills, experience level, etc.
    """
    if not jd_text or not jd_text.strip():
        return {
            "role": "Software Engineer",
            "required_skills": [],
            "nice_to_have": [],
            "experience_level": "mid",
            "key_responsibilities": [],
            "raw_excerpt": "",
        }

    # Rule-based extraction
    role = _extract_role_rulebased(jd_text)
    required_skills = _extract_required_skills_rulebased(jd_text)
    experience_level = _extract_experience_level_rulebased(jd_text)
    responsibilities = _extract_responsibilities_rulebased(jd_text)

    # AI enhancement if available
    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            enhanced = _enhance_jd_with_ai(client, jd_text, role, required_skills, experience_level)
            if enhanced:
                return enhanced
        except Exception:
            pass

    return {
        "role": role,
        "required_skills": required_skills,
        "nice_to_have": [],
        "experience_level": experience_level,
        "key_responsibilities": responsibilities,
        "raw_excerpt": jd_text[:1500].strip(),  # For question generation context
    }


def _extract_role_rulebased(text: str) -> str:
    """Extract job role/title."""
    roles = [
        "Software Engineer", "Backend Developer", "Frontend Developer", "Full Stack Developer",
        "Data Scientist", "ML Engineer", "DevOps Engineer", "Data Engineer",
        "Product Manager", "Technical Lead", "Solutions Architect",
    ]
    text_lower = text.lower()
    for r in roles:
        if r.lower() in text_lower:
            return r
    # Try to find from first line
    first_line = text.split("\n")[0].strip()
    if first_line and len(first_line) < 80:
        return first_line
    return "Software Engineer"


def _extract_required_skills_rulebased(text: str) -> list:
    """Extract required skills from JD."""
    skills = [
        "Python", "Java", "JavaScript", "TypeScript", "C++", "Go", "Rust", "SQL",
        "React", "Vue", "Angular", "Node.js", "Django", "Flask", "FastAPI", "Spring Boot",
        "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform", "CI/CD",
        "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "NLP", "Data Science",
        "Data Structures", "Algorithms", "System Design",
        "REST API", "GraphQL", "Microservices", "ETL", "Spark", "Kafka",
    ]
    text_lower = text.lower()
    found = []
    for s in skills:
        if s.lower() in text_lower:
            found.append(s)
    return found if found else ["Problem Solving", "Communication"]


def _extract_experience_level_rulebased(text: str) -> str:
    """Extract experience level."""
    text_lower = text.lower()
    if "senior" in text_lower or "lead" in text_lower or "5+" in text or "8+" in text:
        return "senior"
    if "junior" in text_lower or "entry" in text_lower or "0-2" in text or "1-2" in text:
        return "junior"
    return "mid"


def _extract_responsibilities_rulebased(text: str) -> list:
    """Extract key responsibilities."""
    resp_section = re.search(r"(?:responsibilities?|what you'll do|key responsibilities?)[:\s]*([\s\S]*?)(?=\n\n(?:requirements?|qualifications?|skills?|$))", text, re.I)
    if resp_section:
        content = resp_section.group(1)
        items = re.findall(r"[-•]\s*(.+?)(?=\n[-•]|\n\n|$)", content, re.S)
        return [i.strip()[:150] for i in items[:5]]
    return []


def _enhance_jd_with_ai(client, jd_text: str, role: str, skills: list, level: str) -> Optional[dict]:
    """Use AI to enhance JD parsing."""
    try:
        prompt = f"""Parse this job description and return JSON:
- "role": job title
- "required_skills": list of required technical skills
- "nice_to_have": list of preferred skills
- "experience_level": "junior" | "mid" | "senior"
- "key_responsibilities": list of key responsibilities

JD:
{jd_text[:3000]}

Return ONLY valid JSON."""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = re.sub(r"^```\w*\n?", "", content).replace("```", "").strip()
        data = json.loads(content)
        data["raw_excerpt"] = jd_text[:1500].strip()
        return data
    except Exception:
        return None
