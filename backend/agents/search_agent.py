"""
search_agent.py — The Research Search Agent
============================================
WHY THIS AGENT EXISTS:
After the Planner breaks the question into sub-tasks, we need to actually
FIND information. This agent takes those sub-tasks and performs web searches
using the Tavily API.

WHY TAVILY (not Google or Bing):
Regular search APIs return just links and titles. Tavily is built specifically
for AI agents — it returns:
  - Clean text content (not raw HTML)
  - Relevance scores
  - Content snippets ready for LLM consumption
This saves us from having to scrape websites and clean HTML ourselves.

The agent has the Tavily search tool attached, so it can:
1. Read each sub-task from the Planner
2. Craft optimal search queries
3. Execute searches and collect results
4. Return a structured list of sources with content
"""

from crewai import Agent, Task
from backend.config import get_llm, TAVILY_API_KEY

# WHY we import TavilySearchResults from langchain:
# CrewAI integrates seamlessly with LangChain tools. Tavily's LangChain
# integration is well-tested and returns structured results that CrewAI
# can pass between agents automatically.
try:
    from langchain_community.tools.tavily_search import TavilySearchResults
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False


def _get_search_tools():
    """
    Returns the list of tools available to the Search Agent.

    WHY conditional tool loading:
    If the user hasn't installed langchain-community or doesn't have a
    Tavily API key, we still want the agent to work — it'll just use the
    LLM's training knowledge instead of live web results.
    """
    tools = []
    if TAVILY_AVAILABLE and TAVILY_API_KEY:
        tavily_tool = TavilySearchResults(
            max_results=5,  # WHY 5: Balance between coverage and speed/cost
            # Each result includes title, URL, and content snippet
        )
        tools.append(tavily_tool)
    return tools


def create_search_agent():
    """
    Creates and returns the Search Agent.

    WHY these parameters:
    - tools: Tavily search tool gives this agent the ability to search the web
    - max_iter: Limit iterations to prevent runaway searches (cost control)
    """
    return Agent(
        role="Research Search Specialist",
        goal=(
            "Execute web searches for each research sub-task provided by the "
            "Planner. Find the most relevant, credible, and recent sources for "
            "each sub-task. Prioritize academic papers, reputable news outlets, "
            "and official reports."
        ),
        backstory=(
            "You are a skilled research librarian and information specialist. "
            "You know how to craft precise search queries that surface the most "
            "relevant and authoritative sources. You can quickly evaluate source "
            "credibility and relevance."
        ),
        verbose=True,
        allow_delegation=False,
        llm=get_llm(),
        tools=_get_search_tools(),
        max_iter=15,  # WHY 15: Enough for 3-5 sub-tasks × 2-3 searches each
    )


def create_search_task(agent, planner_output):
    """
    Creates the search task based on the Planner's output.

    WHY we pass planner_output as context:
    The Search Agent needs to know what sub-tasks to search for. By including
    the Planner's output directly in the task description, the Search Agent
    can parse the sub-tasks and craft appropriate queries.
    """
    return Task(
        description=(
            f"Based on the research plan below, conduct web searches to find "
            f"relevant, high-quality sources for each sub-task.\n\n"
            f"Research Plan:\n{planner_output}\n\n"
            f"For each sub-task:\n"
            f"1. Use the search tool to find relevant articles and sources\n"
            f"2. Collect at least 2-3 sources per sub-task\n"
            f"3. Include the source title, URL, and a content summary\n\n"
            f"Focus on finding diverse, credible sources. Prefer recent "
            f"publications (last 2-3 years) when available."
        ),
        expected_output=(
            "A structured list of sources organized by sub-task:\n\n"
            "## Sub-task 1: [title]\n"
            "- Source 1: [title] | [url] | [key content summary]\n"
            "- Source 2: [title] | [url] | [key content summary]\n\n"
            "## Sub-task 2: [title]\n"
            "- Source 1: ...\n"
            "(continue for all sub-tasks)"
        ),
        agent=agent,
    )
