"""
planner_agent.py — The Research Planner Agent
=============================================
WHY THIS AGENT EXISTS:
When a user asks a broad question like "AI ethics", you can't just Google
that and get a great research report. The question is too vague and wide.

This agent is a "research methodology expert" — it takes the broad question
and decomposes it into 3-5 focused, searchable sub-tasks. For example:
  "AI ethics" → [
    "Historical development of AI ethics frameworks",
    "Current AI bias and fairness challenges",
    "Regulatory approaches to AI ethics globally",
    "Impact of AI ethics on industry practices"
  ]

This decomposition is crucial because:
1. The Search Agent gets focused queries → better search results
2. The final report has clear structure → each sub-task becomes a section
3. We can parallelize searches in the future

The agent uses NO tools — it relies purely on the LLM's reasoning ability
to break down the research question intelligently.
"""

from crewai import Agent, Task
from backend.config import get_llm


def create_planner_agent():
    """
    Creates and returns the Planner Agent.

    WHY these specific parameters:
    - role: Tells the LLM to think like a research planner
    - goal: Explicitly says to break into sub-tasks (not answer the question)
    - backstory: Gives the LLM "experience" context to reason better
    - verbose: True so we can stream status updates to the frontend
    - allow_delegation: False because this agent works alone
    """
    return Agent(
        role="Senior Research Planner",
        goal=(
            "Break down the user's research question into 3-5 focused, "
            "searchable sub-tasks that together would provide comprehensive "
            "coverage of the topic. Each sub-task should be specific enough "
            "to yield targeted search results."
        ),
        backstory=(
            "You are an expert research methodologist with 20 years of experience "
            "in academic research. You excel at taking broad, complex topics and "
            "decomposing them into well-structured research plans. You understand "
            "that good research starts with good questions — specific, focused, "
            "and collectively exhaustive."
        ),
        verbose=True,
        allow_delegation=False,
        llm=get_llm(),
    )


def create_planner_task(agent, research_query):
    """
    Creates the planning task for the given research query.

    WHY the expected_output format:
    We ask for a numbered list because:
    1. It's easy for the next agent (Search) to parse
    2. It provides clear structure for the final report sections
    3. The descriptions help the Search Agent craft better queries
    """
    return Task(
        description=(
            f"Analyze the following research question and break it down into "
            f"3-5 focused sub-tasks that a research team should investigate:\n\n"
            f"Research Question: {research_query}\n\n"
            f"For each sub-task, provide:\n"
            f"1. A clear, specific title\n"
            f"2. A brief description of what to investigate\n"
            f"3. Suggested search queries to find relevant information\n\n"
            f"Make sure the sub-tasks collectively cover the topic comprehensively "
            f"without significant overlap."
        ),
        expected_output=(
            "A numbered list of 3-5 research sub-tasks, each with:\n"
            "- Title: [specific sub-task title]\n"
            "- Description: [what to investigate]\n"
            "- Search Queries: [2-3 suggested search queries]\n"
        ),
        agent=agent,
    )
