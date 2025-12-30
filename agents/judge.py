"""
Judge - The Synthesizer (Supervisor)

Coordinates Sage and Oracle, rates their responses, and provides balanced judgment.
Uses parallel delegation to gather multiple perspectives simultaneously.
"""
from bedsheet import Supervisor
from bedsheet.llm import AnthropicClient
from bedsheet.memory import InMemory
from .sage import sage
from .oracle import oracle


# Create the Judge supervisor agent instance
judge = Supervisor(
    name="Judge",
    instruction="""You are Judge, a wise coordinator seeking counsel from expert advisors.

When you receive a question, consult both Sage and Oracle simultaneously for their perspectives.
After receiving their insights, ask each to rate the other's response (1-10 with brief reason).

Before giving your final answer, reflect on what you learned from each advisor and their cross-ratings.
Then provide your balanced judgment to the User.""",
    model_client=AnthropicClient(),
    memory=InMemory(),
    collaborators=[sage, oracle],
    collaboration_mode="supervisor",
    max_iterations=10,
)
