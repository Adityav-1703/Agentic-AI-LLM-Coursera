"""
CrewAI conceptual demo — NOT used by the production CareerPilot LangGraph app.

CrewAI organizes work as Agents + Tasks + Crew. Collaboration is role-driven
task delegation rather than an explicit state graph with conditional edges.
"""

from __future__ import annotations

# This demo is intentionally dependency-light so the main project installs cleanly.
# Install extras only if you want to execute this file:
#   pip install crewai


def conceptual_crew_layout() -> dict:
    return {
        "framework": "CrewAI",
        "units": ["Agent", "Task", "Crew", "Process"],
        "example_agents": [
            {"role": "Career Analyst", "goal": "Build a skill map"},
            {"role": "Researcher", "goal": "Find learning resources"},
            {"role": "Study Planner", "goal": "Produce a schedule"},
        ],
        "collaboration_model": (
            "Sequential or hierarchical process where a manager/crew assigns tasks. "
            "Shared context is mostly conversational memory + task outputs, "
            "not a typed LangGraph state machine."
        ),
        "contrast_with_langgraph": [
            "CrewAI emphasizes roles and delegated tasks.",
            "LangGraph emphasizes explicit nodes, edges, checkpoints, and interrupts.",
            "Conditional routing in LangGraph is first-class; CrewAI uses process/manager patterns.",
        ],
        "pseudo_code": """
from crewai import Agent, Task, Crew, Process

analyst = Agent(role="Career Analyst", goal="Map skills", tools=[analyze_skill_gaps])
researcher = Agent(role="Researcher", goal="Find sources", tools=[research_topics])
planner = Agent(role="Study Planner", goal="Schedule prep", tools=[generate_study_plan])

t1 = Task(description="Analyze role", agent=analyst)
t2 = Task(description="Research gaps", agent=researcher, context=[t1])
t3 = Task(description="Draft plan", agent=planner, context=[t1, t2])

crew = Crew(agents=[analyst, researcher, planner], tasks=[t1, t2, t3], process=Process.sequential)
result = crew.kickoff(inputs={"goal": user_goal})
""",
    }


if __name__ == "__main__":
    import json

    print(json.dumps(conceptual_crew_layout(), indent=2))
