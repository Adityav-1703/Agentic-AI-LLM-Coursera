"""Tool registry for CareerPilot agents."""

from app.tools.calculator import calculate_study_hours
from app.tools.interview import generate_interview_questions
from app.tools.progress import generate_final_report, track_progress
from app.tools.research import research_topics
from app.tools.skill_analysis import analyze_skill_gaps
from app.tools.study_plan import generate_study_plan

ALL_TOOLS = [
    calculate_study_hours,
    analyze_skill_gaps,
    research_topics,
    generate_study_plan,
    generate_interview_questions,
    track_progress,
    generate_final_report,
]

TOOL_BY_NAME = {t.name: t for t in ALL_TOOLS}
