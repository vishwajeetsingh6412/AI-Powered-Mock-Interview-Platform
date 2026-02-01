# AI-Powered Mock Interview Platform

An intelligent mock interview platform that simulates real-world interview conditions with adaptive question difficulty, time constraints, and objective scoring.

## Features

- **Resume Analysis**: Extracts skills, experience, projects, and role relevance
- **Job Description Parsing**: Aligns questions with role requirements
- **Adaptive Questions**: Technical, conceptual, behavioral, and scenario-based at Easy/Medium/Hard levels
- **Dynamic Difficulty**: Increases for strong responses, decreases for weaker ones
- **Time Constraints**: 3 minutes per question with overtime penalties
- **Early Termination**: Ends interview if performance falls below threshold
- **Objective Scoring**: Accuracy, Clarity, Depth, Relevance, Time Efficiency
- **Comprehensive Report**: Readiness score, skill breakdown, strengths/weaknesses, actionable feedback

## Setup

1. **Clone and install dependencies**:
   ```bash
   cd mock_interview_platform
   pip install -r requirements.txt
   ```

2. **Optional: Add OpenAI API key for enhanced AI features**:
   - Copy `.env.example` to `.env`
   - Add your OpenAI API key from https://platform.openai.com/api-keys
   - With the API key: AI-powered question generation and answer evaluation
   - Without: Rule-based fallback (works fully offline)

## Run

```bash
streamlit run app.py
```

Then open http://localhost:8501 in your browser.

## Deploy on Streamlit Cloud

1. Push this project to a GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click "New app" and select your repo
4. Set `app.py` as the main file
5. Add `OPENAI_API_KEY` in Secrets (optional, for AI features)

## Usage

1. **Upload Resume**: Paste text or upload PDF
2. **Paste Job Description**: The role you're interviewing for
3. **Start Interview**: Answer questions within the time limit
4. **Review Results**: Get your readiness score and improvement tips

## Configuration

Edit `config.py` to adjust:
- `QUESTION_TIME_LIMIT_SECONDS`: Time per question (default: 180)
- `EARLY_TERMINATION_THRESHOLD`: Score below which interview may end early (default: 35)
- `MIN_QUESTIONS` / `MAX_QUESTIONS`: Interview length bounds
