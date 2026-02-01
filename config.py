"""Configuration for the Mock Interview Platform."""
import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Interview Settings
MIN_QUESTIONS = 5
MAX_QUESTIONS = 15
QUESTION_TIME_LIMIT_SECONDS = 180  # 3 minutes per question
EARLY_TERMINATION_THRESHOLD = 35  # Below this average score, terminate early
MIN_QUESTIONS_BEFORE_TERMINATION = 3  # Must ask at least 3 questions before early termination
CONSECUTIVE_LOW_SCORES = 2  # Number of consecutive low scores (< 40) for early termination

# Difficulty levels
DIFFICULTY_LEVELS = ["easy", "medium", "hard"]
DIFFICULTY_SCORES = {"easy": 1, "medium": 2, "hard": 3}

# Scoring weights
SCORING_WEIGHTS = {
    "accuracy": 0.30,
    "clarity": 0.20,
    "depth": 0.25,
    "relevance": 0.15,
    "time_efficiency": 0.10,
}
