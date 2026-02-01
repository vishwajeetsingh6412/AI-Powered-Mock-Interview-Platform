"""AI Interviewer - generates questions, adapts difficulty, evaluates responses."""
import json
import re
from typing import Optional, List
from dataclasses import dataclass, field
from jd_parser import extract_dynamic_context
from config import (
    DIFFICULTY_LEVELS,
    EARLY_TERMINATION_THRESHOLD,
    MIN_QUESTIONS_BEFORE_TERMINATION,
    CONSECUTIVE_LOW_SCORES,
    SCORING_WEIGHTS,
    QUESTION_TIME_LIMIT_SECONDS,
)


@dataclass
class Question:
    """Represents an interview question."""
    text: str
    difficulty: str  # easy, medium, hard
    category: str    # technical, conceptual, behavioral, scenario
    skill_area: str = ""


@dataclass
class AnswerEvaluation:
    """Evaluation of a candidate's answer."""
    accuracy: float
    clarity: float
    depth: float
    relevance: float
    time_efficiency: float
    overall_score: float
    feedback: str
    skill_area: str = ""


def generate_question(
    resume_data: dict,
    jd_data: dict,
    previous_questions: list,
    current_difficulty: str,
    api_key: Optional[str] = None,
) -> Question:
    """Generate next interview question based on context and difficulty."""
    q_context = f"""
Resume skills: {', '.join(resume_data.get('skills', [])[:15])}
Role: {jd_data.get('role', 'Software Engineer')}
Required skills: {', '.join(jd_data.get('required_skills', [])[:10])}
Previous questions asked: {[q.text[:50] for q in previous_questions[-3:]]}
"""
    categories = ["technical", "conceptual", "behavioral", "scenario"]
    # Vary categories
    cat_idx = len(previous_questions) % 4
    category = categories[cat_idx]

    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            return _generate_question_ai(client, resume_data, jd_data, previous_questions, current_difficulty, category)
        except Exception:
            pass

    return _generate_question_fallback(resume_data, jd_data, previous_questions, current_difficulty, category)


def _generate_question_ai(client, resume_data: dict, jd_data: dict, prev: list, diff: str, category: str) -> Question:
    """Generate question using OpenAI - MUST be aligned with job description."""
    jd_excerpt = jd_data.get("raw_excerpt", "")[:1200]
    responsibilities = jd_data.get("key_responsibilities", [])
    role = jd_data.get("role", "Software Engineer")
    req_skills = jd_data.get("required_skills", [])
    prev_qs = [q.text[:80] for q in prev[-2:]] if prev else []
    prompt = f"""You are an expert technical interviewer. Generate ONE interview question that is DIRECTLY relevant to the job description below.

JOB DESCRIPTION (use this to tailor your question):
Role: {role}
Required skills: {req_skills}
Responsibilities: {responsibilities}

JD excerpt:
{jd_excerpt}

The question MUST test knowledge or experience related to this specific role and its requirements.
Generate a {diff} difficulty, {category} question.
Previous questions (do NOT repeat similar): {prev_qs}

Return JSON only: {{"question": "...", "skill_area": "...", "category": "..."}}"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
    )
    content = response.choices[0].message.content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```\w*\n?", "", content).replace("```", "").strip()
    data = json.loads(content)
    return Question(
        text=data.get("question", "Explain your approach to problem-solving."),
        difficulty=diff,
        category=data.get("category", category),
        skill_area=data.get("skill_area", "general"),
    )


def _build_dynamic_questions(ctx: dict, category: str, diff: str, q_index: int) -> List[str]:
    """
    Dynamically build questions from JD context using templates.
    Works for ANY role - no fixed question bank.
    """
    s, s2 = ctx.get("skill", "the role"), ctx.get("skill2", "related technologies")
    v, verb = ctx.get("verb", "work with"), ctx.get("verbs", ["work with"])
    d, phrase = ctx.get("domain", "production"), ctx.get("phrase", "key tasks")
    role = ctx.get("role", "this role")

    # Template structure: (technical, conceptual, behavioral, scenario) x (easy, medium, hard)
    templates = {
        "technical": {
            "easy": [
                f"What is your experience with {s}? How have you used it in projects?",
                f"Explain the key concepts of {s} relevant to {role}.",
                f"How would you get started with {s} for a new project?",
                f"What are the main features of {s} that matter for {d} systems?",
                f"Describe a simple use case where you applied {s}.",
            ],
            "medium": [
                f"How would you {v} {s} in a {d} environment?",
                f"Describe your approach to optimizing {s} for scale.",
                f"What challenges have you faced with {s} and how did you solve them?",
                f"How do you integrate {s} with {s2} in practice?",
                f"Walk through how you would design a solution using {s} for {phrase}.",
                f"What are the trade-offs when choosing {s} over alternatives?",
            ],
            "hard": [
                f"Design a {d} system using {s}. What architecture would you choose and why?",
                f"How would you handle failure scenarios when {v} {s} at scale?",
                f"Discuss the limitations of {s} and how you would work around them.",
                f"Your {s}-based system is degrading under load. How do you diagnose and fix it?",
                f"Compare {s} and {s2} for {phrase}. When would you use each?",
            ],
        },
        "conceptual": {
            "easy": [
                f"Why is {s} important for {role}?",
                f"What does good {phrase} look like in your experience?",
                f"How do you stay updated with {s} and {s2}?",
            ],
            "medium": [
                f"Explain the relationship between {s} and {d} systems.",
                f"What principles guide your approach to {phrase}?",
                f"How would you explain {s} to a non-technical stakeholder?",
            ],
            "hard": [
                f"Discuss trade-offs in {phrase} when scaling with {s}.",
                f"How would you approach technical debt in a {s}-based codebase?",
                f"What would you change about how {s} is typically used in the industry?",
            ],
        },
        "behavioral": {
            "easy": [
                f"Tell me about a project where you used {s}. What was your contribution?",
                f"How do you handle disagreements about {phrase}?",
                f"Describe a time you learned {s} quickly.",
            ],
            "medium": [
                f"Describe a challenging situation with {phrase}. How did you resolve it?",
                f"Tell me about a time you had to {v} under pressure.",
                f"How do you prioritize when working on {s} and {s2} simultaneously?",
            ],
            "hard": [
                f"Describe a failure with {s} and what you learned.",
                f"Tell me about a technical decision you made with incomplete information regarding {phrase}.",
                f"How have you mentored others on {s}?",
            ],
        },
        "scenario": {
            "easy": [
                f"A teammate asks for help with {s}. How do you approach it?",
                f"You need to onboard someone to {phrase}. What's your plan?",
                f"A bug appears in a {s} component. Walk through your debugging steps.",
            ],
            "medium": [
                f"Your {s} deployment fails at 2 AM. What do you do?",
                f"A stakeholder wants to change scope for {phrase}. How do you respond?",
                f"The {d} system is slow. How do you investigate and fix it?",
                f"You discover a critical issue with {s} in production. What's your process?",
            ],
            "hard": [
                f"Design a rollout strategy for migrating from {s} to {s2} with zero downtime.",
                f"You have to choose between speed and quality for {phrase}. How do you decide?",
                f"A security vulnerability is found in your {s} stack. How do you handle it?",
            ],
        },
    }
    cat_templates = templates.get(category, templates["technical"])
    diff_templates = cat_templates.get(diff, cat_templates.get("medium", cat_templates["easy"]))
    return diff_templates if isinstance(diff_templates, list) else [diff_templates]


def _generate_question_fallback(resume_data: dict, jd_data: dict, previous_questions: list, diff: str, category: str) -> Question:
    """Dynamic question generation - builds questions from JD context in real time."""
    jd_text = jd_data.get("raw_excerpt", "") or ""
    ctx = extract_dynamic_context(jd_text, jd_data)

    # Ensure we have skills (from JD or resume)
    if not ctx.get("skills"):
        ctx["skills"] = resume_data.get("skills", []) or ["technical skills"]
        ctx["skill"] = ctx["skills"][0] if ctx["skills"] else "the role"
        ctx["skill2"] = ctx["skills"][1] if len(ctx["skills"]) > 1 else ctx["skill"]

    # Build dynamic questions from templates + JD context
    q_list = _build_dynamic_questions(ctx, category, diff, len(previous_questions))

    # Avoid repeating: exclude questions similar to recent ones
    prev_texts = [q.text.lower()[:40] for q in previous_questions[-3:]]
    candidates = [q for q in q_list if not any(pt in q.lower()[:50] for pt in prev_texts)]
    if not candidates:
        candidates = q_list

    # Pick deterministically but vary by question index
    idx = (hash(str(ctx.get("role", "")) + str(len(previous_questions)) + category) % len(candidates) + len(candidates)) % len(candidates)
    question_text = candidates[idx]

    skill_area = ctx.get("skill", "general")
    return Question(text=question_text, difficulty=diff, category=category, skill_area=skill_area)


def evaluate_answer(
    question: Question,
    answer: str,
    time_taken_seconds: float,
    api_key: Optional[str] = None,
) -> AnswerEvaluation:
    """Evaluate candidate's answer on accuracy, clarity, depth, relevance, time efficiency."""
    max_time = QUESTION_TIME_LIMIT_SECONDS

    # Time efficiency: full score if within limit, penalty for overtime
    if time_taken_seconds <= max_time:
        time_score = 100 - (time_taken_seconds / max_time) * 20  # Slight penalty for slow answers
        time_score = max(50, min(100, time_score))
    else:
        overtime_ratio = (time_taken_seconds - max_time) / max_time
        time_score = max(0, 50 - overtime_ratio * 50)  # Penalize overtime

    if api_key and answer.strip():
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            eval_result = _evaluate_with_ai(client, question, answer, time_score)
            if eval_result:
                return eval_result
        except Exception:
            pass

    # Fallback: heuristic scoring
    word_count = len(answer.split())
    depth_score = min(100, 30 + word_count * 2) if word_count > 10 else 40
    clarity_score = min(100, 40 + word_count) if 20 < word_count < 200 else 60
    accuracy_score = 65  # Default without AI
    relevance_score = 70

    overall = (
        accuracy_score * SCORING_WEIGHTS["accuracy"]
        + clarity_score * SCORING_WEIGHTS["clarity"]
        + depth_score * SCORING_WEIGHTS["depth"]
        + relevance_score * SCORING_WEIGHTS["relevance"]
        + time_score * SCORING_WEIGHTS["time_efficiency"]
    )

    return AnswerEvaluation(
        accuracy=accuracy_score,
        clarity=clarity_score,
        depth=depth_score,
        relevance=relevance_score,
        time_efficiency=time_score,
        overall_score=round(overall, 1),
        feedback="Consider providing more specific examples and structure your answers with clear points.",
        skill_area=question.skill_area,
    )


def _evaluate_with_ai(client, question: Question, answer: str, time_score: float) -> Optional[AnswerEvaluation]:
    """Use AI to evaluate answer."""
    prompt = f"""Evaluate this interview response. Return JSON only.

Question (difficulty: {question.difficulty}): {question.text}
Answer: {answer}

Score each 0-100:
- accuracy: correctness and factual accuracy
- clarity: organization and articulation
- depth: detail and thoroughness
- relevance: how well it addresses the question

Also provide "feedback": one sentence of actionable feedback.

Format: {{"accuracy": n, "clarity": n, "depth": n, "relevance": n, "feedback": "..."}}"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    content = response.choices[0].message.content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```\w*\n?", "", content).replace("```", "").strip()
    data = json.loads(content)
    acc = float(data.get("accuracy", 70))
    clar = float(data.get("clarity", 70))
    depth = float(data.get("depth", 70))
    rel = float(data.get("relevance", 70))
    time_sc = time_score
    overall = (
        acc * SCORING_WEIGHTS["accuracy"]
        + clar * SCORING_WEIGHTS["clarity"]
        + depth * SCORING_WEIGHTS["depth"]
        + rel * SCORING_WEIGHTS["relevance"]
        + time_sc * SCORING_WEIGHTS["time_efficiency"]
    )
    return AnswerEvaluation(
        accuracy=acc,
        clarity=clar,
        depth=depth,
        relevance=rel,
        time_efficiency=time_sc,
        overall_score=round(overall, 1),
        feedback=data.get("feedback", "Good response."),
        skill_area=question.skill_area,
    )


def get_next_difficulty(
    current_difficulty: str,
    evaluation: AnswerEvaluation,
    recent_scores: list,
) -> str:
    """Adapt difficulty based on response quality."""
    score = evaluation.overall_score
    idx = DIFFICULTY_LEVELS.index(current_difficulty)

    if score >= 80 and idx < 2:
        return DIFFICULTY_LEVELS[idx + 1]  # Increase difficulty
    if score < 50 and idx > 0:
        return DIFFICULTY_LEVELS[idx - 1]  # Decrease difficulty
    return current_difficulty


def should_terminate_early(
    question_count: int,
    scores: list,
    threshold: float = EARLY_TERMINATION_THRESHOLD,
) -> bool:
    """Determine if interview should end early due to poor performance."""
    if question_count < MIN_QUESTIONS_BEFORE_TERMINATION:
        return False
    avg = sum(scores) / len(scores) if scores else 0
    if avg < threshold:
        return True
    # Consecutive low scores
    if len(scores) >= CONSECUTIVE_LOW_SCORES:
        recent = scores[-CONSECUTIVE_LOW_SCORES:]
        if all(s < 40 for s in recent):
            return True
    return False
