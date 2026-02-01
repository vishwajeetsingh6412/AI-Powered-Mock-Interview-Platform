"""Generate final interview report with readiness score and feedback."""
from typing import List
from dataclasses import dataclass
from interviewer import AnswerEvaluation, Question


@dataclass
class InterviewResult:
    """Full interview result for reporting."""
    readiness_score: float
    hiring_indicator: str  # Strong Yes, Yes, Maybe, No
    performance_by_skill: dict
    strengths: List[str]
    weaknesses: List[str]
    actionable_feedback: List[str]
    question_results: List[dict]


def compute_readiness_score(evaluations: List[AnswerEvaluation], early_terminated: bool) -> float:
    """Compute overall interview readiness score 0-100."""
    if not evaluations:
        return 0.0
    scores = [e.overall_score for e in evaluations]
    avg = sum(scores) / len(scores)
    # Penalty for early termination
    if early_terminated:
        avg *= 0.9
    return round(min(100, max(0, avg)), 1)


def get_hiring_indicator(readiness_score: float) -> str:
    """Get hiring recommendation based on readiness score."""
    if readiness_score >= 80:
        return "Strong Yes"
    if readiness_score >= 65:
        return "Yes"
    if readiness_score >= 50:
        return "Maybe"
    return "No"


def generate_report(
    questions: List[Question],
    evaluations: List[AnswerEvaluation],
    early_terminated: bool,
    api_key: str = None,
) -> InterviewResult:
    """Generate comprehensive interview report."""
    readiness = compute_readiness_score(evaluations, early_terminated)
    hiring = get_hiring_indicator(readiness)

    # Performance by skill area
    skill_scores = {}
    for ev in evaluations:
        area = ev.skill_area or "general"
        if area not in skill_scores:
            skill_scores[area] = []
        skill_scores[area].append(ev.overall_score)
    performance_by_skill = {
        k: round(sum(v) / len(v), 1) for k, v in skill_scores.items()
    }

    # Strengths: areas where score >= 75
    strengths = [
        k for k, v in performance_by_skill.items()
        if v >= 75
    ]
    if not strengths:
        strengths = ["Willingness to engage", "Response structure"]

    # Weaknesses: areas where score < 60
    weaknesses = [
        k for k, v in performance_by_skill.items()
        if v < 60
    ]
    if not weaknesses and readiness < 70:
        weaknesses = ["Depth of technical knowledge", "Time management"]

    # Actionable feedback from evaluations
    actionable = list(set(ev.feedback for ev in evaluations if ev.feedback))[:5]
    if not actionable:
        actionable = [
            "Practice structuring answers with clear examples.",
            "Focus on time management during responses.",
            "Brush up on fundamentals for the role.",
        ]

    # Question-level results
    question_results = []
    for q, e in zip(questions, evaluations):
        question_results.append({
            "question": q.text,
            "difficulty": q.difficulty,
            "category": q.category,
            "score": e.overall_score,
            "feedback": e.feedback,
        })

    return InterviewResult(
        readiness_score=readiness,
        hiring_indicator=hiring,
        performance_by_skill=performance_by_skill,
        strengths=strengths,
        weaknesses=weaknesses,
        actionable_feedback=actionable,
        question_results=question_results,
    )
