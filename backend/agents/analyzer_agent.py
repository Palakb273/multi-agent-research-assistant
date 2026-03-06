"""
analyzer_agent.py — The Research Analyzer Agent
================================================
WHY THIS AGENT EXISTS:
Raw search results are just data — they need ANALYSIS to become knowledge.
This agent reads through all the sources found by the Search Agent and:
1. Identifies key themes and patterns across sources
2. Extracts the most important facts and statistics
3. Notes contradictions or debates between sources
4. Ranks findings by importance and relevance

WHY SEPARATE FROM THE WRITER:
Analysis and writing are fundamentally different cognitive tasks:
- Analysis = critical thinking: "What does this data MEAN?"
- Writing = communication: "How do I EXPLAIN this clearly?"

By separating them, each agent can focus on what it does best.
The Analyzer produces raw insights; the Writer crafts them into prose.

OPTIONAL CHROMA INTEGRATION:
If ChromaDB is available, this agent can store article embeddings.
This enables semantic search across all sources — finding connections
that keyword search would miss. For example, two articles might both
discuss "algorithmic fairness" even though one calls it "AI bias"
and the other calls it "machine learning discrimination."
"""

from crewai import Agent, Task
from backend.config import get_llm


def create_analyzer_agent():
    """
    Creates and returns the Analyzer Agent.

    WHY no tools:
    The Analyzer works purely with the text data provided by the Search Agent.
    It doesn't need to search or access external resources — its job is
    to THINK deeply about the information already collected.
    """
    return Agent(
        role="Senior Research Analyst",
        goal=(
            "Analyze the collected research sources to extract key insights, "
            "identify patterns and themes, note contradictions, and create a "
            "comprehensive analysis that synthesizes information across all sources."
        ),
        backstory=(
            "You are a PhD-level research analyst with expertise in synthesizing "
            "information from multiple sources. You excel at identifying patterns, "
            "drawing connections between disparate pieces of information, and "
            "separating well-supported claims from speculation. Your analyses "
            "are thorough, balanced, and insightful."
        ),
        verbose=True,
        allow_delegation=False,
        llm=get_llm(),
    )


def create_analyzer_task(agent, search_output):
    """
    Creates the analysis task based on the Search Agent's output.

    WHY this specific structure:
    The expected output mirrors a professional research analysis:
    - Key Findings: the most important discoveries
    - Themes: patterns that span multiple sources
    - Contradictions: where sources disagree (important for credibility)
    - Data Points: specific statistics and facts (makes the report concrete)
    """
    return Task(
        description=(
            f"Analyze the following research sources and extract meaningful insights:\n\n"
            f"Sources:\n{search_output}\n\n"
            f"Your analysis should:\n"
            f"1. Identify the 3-5 most important findings across all sources\n"
            f"2. Find common themes and patterns\n"
            f"3. Note any contradictions or debates between sources\n"
            f"4. Extract specific data points, statistics, or metrics\n"
            f"5. Assess the overall quality and credibility of the information\n"
            f"6. Identify any gaps in the research that need further investigation\n\n"
            f"Crucially, you must extract a specific set of numeric data points that can be visualized as a chart. "
            f"Provide this data in a strict JSON format under a section heading `## Visualization Data`.\n\n"
            f"Be thorough but concise. Focus on insights that would be most "
            f"valuable for a comprehensive research report."
        ),
        expected_output=(
            "A structured analysis with the following sections:\n\n"
            "## Key Findings\n"
            "- Finding 1: [description with supporting evidence]\n"
            "- Finding 2: ...\n\n"
            "## Common Themes\n"
            "- Theme 1: [description of pattern across sources]\n\n"
            "## Contradictions & Debates\n"
            "- [areas where sources disagree]\n\n"
            "## Key Data Points\n"
            "- [specific statistics, quotes, or facts]\n\n"
            "## Research Gaps\n"
            "- [areas needing further investigation]\n\n"
            "## Source Quality Assessment\n"
            "- [brief assessment of overall source credibility]\n\n"
            "## Visualization Data\n"
            "```json\n"
            "[\n"
            "  {\"label\": \"Category/Year/Item\", \"value\": 45},\n"
            "  {\"label\": \"Other Category\", \"value\": 30}\n"
            "]\n"
            "```"
        ),
        agent=agent,
    )
