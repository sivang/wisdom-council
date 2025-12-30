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

Follow this 2-ROUND workflow for efficiency:

ROUND 1 - GATHER PERSPECTIVES (PARALLEL):
Delegate to BOTH Sage and Oracle simultaneously, asking each for their perspective on the question.
Wait for both responses.

ROUND 2 - CROSS-RATING (PARALLEL):
After receiving both perspectives, delegate to BOTH advisors simultaneously:
- Ask Sage: "Here is Oracle's response: [include Oracle's full response]. Please rate it 1-10 with a brief reason."
- Ask Oracle: "Here is Sage's response: [include Sage's full response]. Please rate it 1-10 with a brief reason."

FINAL SYNTHESIS:
After receiving both cross-ratings, provide your balanced judgment combining both perspectives and cross-ratings.""",
    model_client=AnthropicClient(),
    memory=InMemory(),
    collaborators=[sage, oracle],
    collaboration_mode="supervisor",
    max_iterations=10,
)
