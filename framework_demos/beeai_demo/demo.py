"""
BeeAI conceptual demo — NOT used by the production CareerPilot LangGraph app.

BeeAI (IBM) focuses on interoperable agents/frameworks and runtime composition.
Agents can be composed across stacks; emphasis is on standards and reusable
agent services rather than a single opinionated graph DSL.
"""

from __future__ import annotations


def conceptual_beeai_layout() -> dict:
    return {
        "framework": "BeeAI",
        "units": ["Agent", "Tool", "Workflow / Runtime composition"],
        "theme": (
            "Interoperability across agent frameworks and deployable agent services."
        ),
        "contrast_with_langgraph": [
            "BeeAI highlights cross-framework agent ecosystems (incl. IBM course stack).",
            "LangGraph (used in CareerPilot production path) provides fine-grained "
            "conditional edges, typed shared state, and interrupt-based HITL.",
            "CareerPilot keeps BeeAI as a conceptual mapping so the portfolio shows "
            "awareness of the full course toolkit without forcing four runtimes into one API.",
        ],
        "mapped_roles": {
            "orchestrator": "Supervisor / router agent",
            "career_analyst": "Domain specialist agent + skill tool",
            "researcher": "Tool-using research agent",
            "study_planner": "Planning agent",
            "interviewer": "Generation agent",
            "evaluator": "Critique / scoring agent",
            "report_agent": "Synthesis agent",
        },
    }


if __name__ == "__main__":
    import json

    print(json.dumps(conceptual_beeai_layout(), indent=2))
