"""
AutoGen conceptual demo — NOT used by the production CareerPilot LangGraph app.

AutoGen centers on multi-agent conversations (AssistantAgent / UserProxyAgent)
with optional group chat managers. Control flow emerges from dialogue patterns
and speaker selection rather than a declarative graph.
"""

from __future__ import annotations


def conceptual_autogen_layout() -> dict:
    return {
        "framework": "AutoGen",
        "units": ["AssistantAgent", "UserProxyAgent", "GroupChat", "GroupChatManager"],
        "example_pattern": (
            "UserProxy initiates; specialist assistants reply; a manager selects the next speaker."
        ),
        "contrast_with_langgraph": [
            "AutoGen is conversation-centric; LangGraph is state-machine-centric.",
            "Human-in-the-loop often appears as UserProxy requesting input.",
            "LangGraph interrupts + checkpointers give durable workflow pause/resume APIs.",
        ],
        "pseudo_code": """
# Illustrative only — requires `autogen` / `autogen-agentchat` extras.
analyst = AssistantAgent("career_analyst", system_message="Produce skill maps.")
researcher = AssistantAgent("researcher", system_message="Use tools for sources.")
user = UserProxyAgent("user", human_input_mode="ALWAYS")

group = GroupChat(agents=[user, analyst, researcher], messages=[], max_round=8)
manager = GroupChatManager(groupchat=group)
user.initiate_chat(manager, message=user_goal)
""",
    }


if __name__ == "__main__":
    import json

    print(json.dumps(conceptual_autogen_layout(), indent=2))
