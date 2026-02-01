"""
AI-Powered Mock Interview Platform
Streamlit application for conducting and evaluating mock interviews.
"""
import streamlit as st
import time
from datetime import datetime
from config import (
    OPENAI_API_KEY,
    MIN_QUESTIONS,
    MAX_QUESTIONS,
    QUESTION_TIME_LIMIT_SECONDS,
)
from resume_analyzer import analyze_resume, extract_text_from_pdf
from jd_parser import parse_job_description
from interviewer import (
    Question,
    generate_question,
    evaluate_answer,
    get_next_difficulty,
    should_terminate_early,
    AnswerEvaluation,
)
from report_generator import generate_report

# Page config
st.set_page_config(
    page_title="AI Mock Interview Platform",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for professional look
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
    
    /* Main App Background */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #312e81 100%);
        font-family: 'DM Sans', sans-serif;
    }
    
    /* Typography */
    h1, h2, h3, h4, h5, h6, p, div, span {
        font-family: 'DM Sans', sans-serif !important;
        color: #e2e8f0;
    }
    
    h1 {
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    
    .main-header {
        background: linear-gradient(90deg, #818cf8 0%, #c084fc 50%, #e879f9 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        text-shadow: 0 0 30px rgba(168, 85, 247, 0.2);
    }
    
    .sub-header {
        color: #94a3b8 !important;
        font-size: 1.1rem;
        margin-bottom: 2.5rem;
        line-height: 1.6;
    }
    
    /* Cards & Containers (Glassmorphism) */
    .card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid rgba(148, 163, 184, 0.1);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    
    .question-box {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(168, 85, 247, 0.05) 100%);
        backdrop-filter: blur(10px);
        border-left: 5px solid #818cf8;
        padding: 2rem;
        border-radius: 0 16px 16px 0;
        margin: 1.5rem 0;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    
    /* Input Fields */
    .stTextArea textarea {
        background-color: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(99, 102, 241, 0.2) !important;
        color: #f1f5f9 !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        font-size: 1rem !important;
        transition: all 0.2s ease;
    }
    
    .stTextArea textarea:focus {
        border-color: #818cf8 !important;
        box-shadow: 0 0 0 2px rgba(129, 140, 248, 0.2) !important;
        background-color: rgba(15, 23, 42, 0.8) !important;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 12px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        border: none;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-size: 0.9rem;
        width: 100%;
    }
    
    /* Primary Button (Submit/Start) */
    button[kind="primary"] {
        background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 100%);
        color: white;
        box-shadow: 0 4px 6px -1px rgba(99, 102, 241, 0.3);
    }
    
    button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(99, 102, 241, 0.4);
        background: linear-gradient(90deg, #4f46e5 0%, #7c3aed 100%);
    }

    /* Secondary Button (Standard Streamlit buttons) */
    .stButton > button[kind="secondary"] {
        background: rgba(30, 41, 59, 0.8);
        border: 1px solid rgba(148, 163, 184, 0.2);
        color: #e2e8f0;
    }
    
    .stButton > button[kind="secondary"]:hover {
        background: rgba(51, 65, 85, 0.9);
        border-color: rgba(148, 163, 184, 0.4);
        color: white;
    }
    
    /* Specific styling for Finish button (4th column) */
    div[data-testid="column"]:nth-of-type(4) .stButton > button {
        background: rgba(220, 38, 38, 0.1) !important;
        border: 1px solid rgba(220, 38, 38, 0.2) !important;
        color: #f87171 !important;
    }
    
    div[data-testid="column"]:nth-of-type(4) .stButton > button:hover {
        background: rgba(220, 38, 38, 0.2) !important;
        color: #fca5a5 !important;
        border-color: rgba(220, 38, 38, 0.4) !important;
        box-shadow: 0 4px 12px rgba(220, 38, 38, 0.1) !important;
    }

    /* Progress Bar */
    .stProgress > div > div > div > div {
        background-image: linear-gradient(90deg, #34d399 0%, #2dd4bf 50%, #38bdf8 100%);
        border-radius: 999px;
    }
    
    /* Sidebar */
    div[data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.95);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Badges & Scores */
    .score-badge {
        display: inline-block;
        padding: 0.35rem 1rem;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.9rem;
        letter-spacing: 0.025em;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .score-strong { background: rgba(34, 197, 94, 0.2); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.3); }
    .score-average { background: rgba(234, 179, 8, 0.2); color: #facc15; border: 1px solid rgba(234, 179, 8, 0.3); }
    .score-weak { background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
    
    .timer {
        font-size: 2.5rem;
        font-weight: 800;
        text-align: center;
        padding: 1.5rem;
        text-shadow: 0 0 20px rgba(0,0,0,0.3);
        font-variant-numeric: tabular-nums;
    }
    
    .result-score {
        font-size: 5rem;
        font-weight: 800;
        text-align: center;
        margin: 2rem 0;
        text-shadow: 0 0 40px rgba(0,0,0,0.3);
    }
    
    .result-strong { color: #4ade80; }
    .result-average { color: #facc15; }
    .result-weak { color: #f87171; }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: rgba(30, 41, 59, 0.4);
        border-radius: 8px;
        color: #e2e8f0 !important;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    defaults = {
        "stage": "upload",  # upload, interviewing, results
        "resume_data": None,
        "jd_data": None,
        "resume_text": "",
        "jd_text": "",
        "questions": [],
        "evaluations": [],
        "current_question": None,
        "current_difficulty": "medium",
        "question_start_time": None,
        "interview_complete": False,
        "early_terminated": False,
        "report": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def render_upload_stage():
    """Render resume and JD upload stage."""
    st.markdown('<p class="main-header">AI-Powered Mock Interview Platform</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Upload your resume and job description to start a realistic, adaptive mock interview.</p>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📄 Your Resume")
        resume_input = st.radio("Resume input method", ["Paste text", "Upload PDF"], horizontal=True)
        resume_text = ""
        if resume_input == "Paste text":
            resume_text = st.text_area(
                "Paste your resume content",
                height=200,
                placeholder="Paste your resume here. Include skills, experience, projects, and education.",
            )
        else:
            resume_file = st.file_uploader("Upload resume PDF", type=["pdf"])
            if resume_file:
                try:
                    resume_text = extract_text_from_pdf(resume_file)
                    st.success(f"Extracted {len(resume_text)} characters from PDF.")
                except Exception as e:
                    st.error(f"Failed to parse PDF: {e}")

    with col2:
        st.markdown("#### 📋 Job Description")
        jd_text = st.text_area(
            "Paste the job description",
            height=200,
            placeholder="Paste the full job description you're interviewing for. Include role, requirements, and responsibilities.",
        )

    st.session_state["resume_text"] = resume_text
    st.session_state["jd_text"] = jd_text

    if st.button("Start Interview", use_container_width=True):
        if not resume_text.strip():
            st.warning("Please provide your resume (paste text or upload PDF).")
            return
        if not jd_text.strip():
            st.warning("Please provide the job description.")
            return

        with st.spinner("Analyzing your resume and job description..."):
            resume_data = analyze_resume(resume_text, OPENAI_API_KEY)
            jd_data = parse_job_description(jd_text, OPENAI_API_KEY)
            st.session_state["resume_data"] = resume_data
            st.session_state["jd_data"] = jd_data
            st.session_state["stage"] = "interviewing"
            # Generate first question
            q = generate_question(resume_data, jd_data, [], "medium", OPENAI_API_KEY)
            st.session_state["current_question"] = q
            st.session_state["question_start_time"] = time.time()
            st.rerun()


def render_interview_stage():
    """Render the live interview stage."""
    resume_data = st.session_state["resume_data"]
    jd_data = st.session_state["jd_data"]
    questions = st.session_state["questions"]
    evaluations = st.session_state["evaluations"]
    current_q = st.session_state["current_question"]
    difficulty = st.session_state["current_difficulty"]

    st.markdown('<p class="main-header">Mock Interview in Progress</p>', unsafe_allow_html=True)
    progress = len(questions) + (1 if current_q else 0)
    st.progress(min(1.0, progress / MAX_QUESTIONS), text=f"Question {progress} of up to {MAX_QUESTIONS}")

    # Sidebar: Interview info
    with st.sidebar:
        st.markdown("### Interview Status")
        st.write(f"**Role:** {jd_data.get('role', 'N/A')}")
        st.write(f"**Questions asked:** {len(questions)}")
        if evaluations:
            avg = sum(e.overall_score for e in evaluations) / len(evaluations)
            st.write(f"**Current avg score:** {avg:.1f}")
        st.write(f"**Current difficulty:** {difficulty}")

    if current_q:
        # Display question
        st.markdown(
            f'<div class="question-box">'
            f'<strong>Question {len(questions) + 1}</strong> '
            f'(Difficulty: {current_q.difficulty} | Category: {current_q.category})<br><br>'
            f'{current_q.text}'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Timer
        elapsed = int(time.time() - st.session_state["question_start_time"])
        remaining = max(0, QUESTION_TIME_LIMIT_SECONDS - elapsed)
        mins, secs = divmod(remaining, 60)
        timer_color = "#4ade80" if remaining > 60 else "#f87171" if remaining > 30 else "#ef4444"
        st.markdown(
            f'<div class="timer" style="color: {timer_color}">⏱️ {mins:02d}:{secs:02d} remaining</div>',
            unsafe_allow_html=True,
        )

        answer = st.text_area(
            "Your answer",
            height=150,
            placeholder="Type your answer here. Be concise but thorough. The timer is running!",
            key="answer_input",
        )

        col1, col2, _, col3 = st.columns([1, 1, 2, 1])
        with col1:
            if st.button("Submit Answer", type="primary"):
                if not answer.strip():
                    st.warning("Please provide an answer before submitting.")
                else:
                    time_taken = time.time() - st.session_state["question_start_time"]
                    evaluation = evaluate_answer(current_q, answer, time_taken, OPENAI_API_KEY)
                    evaluations.append(evaluation)
                    questions.append(current_q)

                    # Check early termination
                    scores = [e.overall_score for e in evaluations]
                    if should_terminate_early(len(questions), scores):
                        st.session_state["early_terminated"] = True
                        st.session_state["interview_complete"] = True
                        st.session_state["current_question"] = None
                        st.session_state["stage"] = "results"
                        report = generate_report(questions, evaluations, True)
                        st.session_state["report"] = report
                        st.rerun()

                    # Adapt difficulty
                    next_diff = get_next_difficulty(difficulty, evaluation, scores)
                    st.session_state["current_difficulty"] = next_diff

                    # Generate next question or finish
                    if len(questions) >= MAX_QUESTIONS:
                        st.session_state["interview_complete"] = True
                        st.session_state["current_question"] = None
                        st.session_state["stage"] = "results"
                        report = generate_report(questions, evaluations, False)
                        st.session_state["report"] = report
                        st.rerun()
                    else:
                        next_q = generate_question(
                            resume_data, jd_data, questions, next_diff, OPENAI_API_KEY
                        )
                        st.session_state["current_question"] = next_q
                        st.session_state["question_start_time"] = time.time()
                        st.rerun()

        with col2:
            if st.button("Skip Question"):
                # Record skipped question with 0 score
                skipped_eval = AnswerEvaluation(
                    accuracy=0,
                    clarity=0,
                    depth=0,
                    relevance=0,
                    time_efficiency=0,
                    overall_score=0,
                    feedback="Question skipped by candidate.",
                    skill_area=current_q.skill_area,
                )
                evaluations.append(skipped_eval)
                questions.append(current_q)
                
                # Check termination (too many skips might trigger early termination)
                scores = [e.overall_score for e in evaluations]
                if should_terminate_early(len(questions), scores):
                    st.session_state["early_terminated"] = True
                    st.session_state["interview_complete"] = True
                    st.session_state["current_question"] = None
                    st.session_state["stage"] = "results"
                    report = generate_report(questions, evaluations, True)
                    st.session_state["report"] = report
                    st.rerun()

                # Generate next question
                if len(questions) >= MAX_QUESTIONS:
                    st.session_state["interview_complete"] = True
                    st.session_state["current_question"] = None
                    st.session_state["stage"] = "results"
                    report = generate_report(questions, evaluations, False)
                    st.session_state["report"] = report
                    st.rerun()
                else:
                    # Keep same difficulty if skipped? Or decrease?
                    # Let's decrease difficulty if they skip
                    next_diff = get_next_difficulty(difficulty, skipped_eval, scores)
                    st.session_state["current_difficulty"] = next_diff
                    
                    next_q = generate_question(
                        resume_data, jd_data, questions, next_diff, OPENAI_API_KEY
                    )
                    st.session_state["current_question"] = next_q
                    st.session_state["question_start_time"] = time.time()
                    st.rerun()

        with col3:
            if st.button("Finish Interview"):
                if len(questions) < 2:
                    st.warning("Complete at least 2 questions for a meaningful report.")
                else:
                    st.session_state["interview_complete"] = True
                    st.session_state["current_question"] = None
                    st.session_state["stage"] = "results"
                    report = generate_report(questions, evaluations, False)
                    st.session_state["report"] = report
                    st.rerun()

        # Show last evaluation if any
        if evaluations:
            last = evaluations[-1]
            score_class = "score-strong" if last.overall_score >= 70 else "score-average" if last.overall_score >= 50 else "score-weak"
            st.markdown(
                f'<div class="card">Last answer score: '
                f'<span class="score-badge {score_class}">{last.overall_score}/100</span>'
                f'<br><small>Feedback: {last.feedback}</small></div>',
                unsafe_allow_html=True,
            )
    else:
        st.info("Loading next question...")


def render_results_stage():
    """Render the final results and report."""
    report = st.session_state["report"]
    early = st.session_state.get("early_terminated", False)

    st.markdown('<p class="main-header">Interview Results</p>', unsafe_allow_html=True)
    if early:
        st.warning("The interview was concluded early based on performance thresholds. Focus on the feedback below to improve.")

    # Overall score
    rs = report.readiness_score
    score_class = "result-strong" if rs >= 70 else "result-average" if rs >= 50 else "result-weak"
    st.markdown(
        f'<div class="result-score {score_class}">{rs}/100</div>'
        f'<p style="text-align: center; color: #94a3b8; font-size: 1.2rem;">Interview Readiness Score</p>'
        f'<p style="text-align: center; color: #6366f1; font-weight: 600;">Hiring Readiness: {report.hiring_indicator}</p>',
        unsafe_allow_html=True,
    )

    # Breakdown
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Performance by Skill Area")
        for skill, score in report.performance_by_skill.items():
            pct = score
            st.write(f"**{skill}**")
            st.progress(score / 100)
            st.caption(f"{score}/100")

    with col2:
        st.markdown("#### Strengths")
        for s in report.strengths:
            st.success(f"✓ {s}")
        st.markdown("#### Areas to Improve")
        for w in report.weaknesses:
            st.error(f"✗ {w}")

    st.markdown("#### Actionable Feedback")
    for i, fb in enumerate(report.actionable_feedback, 1):
        st.markdown(f"{i}. {fb}")

    st.markdown("#### Question-by-Question Breakdown")
    for i, qr in enumerate(report.question_results, 1):
        q_preview = qr['question'][:80] + "..." if len(qr['question']) > 80 else qr['question']
        with st.expander(f"Q{i}: {q_preview} (Score: {qr['score']}/100)"):
            st.write(f"**Difficulty:** {qr['difficulty']} | **Category:** {qr['category']}")
            st.write(f"**Feedback:** {qr['feedback']}")

    if st.button("Start New Interview", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


def main():
    init_session_state()

    if st.session_state["stage"] == "upload":
        render_upload_stage()
    elif st.session_state["stage"] == "interviewing":
        render_interview_stage()
    else:
        render_results_stage()


if __name__ == "__main__":
    main()
