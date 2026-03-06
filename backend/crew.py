"""
crew.py — CrewAI Orchestration Layer
======================================
WHY THIS FILE EXISTS:
This is the "conductor" of our multi-agent orchestra. While each agent
module defines WHO an agent is and WHAT it does, this module defines
HOW they work TOGETHER.

CrewAI's `Crew` class handles:
1. Sequential task execution (Agent 1 → Agent 2 → Agent 3 → Agent 4)
2. Passing output from one agent as input to the next
3. Error handling and retries
4. Verbose logging for debugging

FLOW:
  User Query
     ↓
  Planner Agent → breaks query into sub-tasks
     ↓
  Search Agent → finds sources for each sub-task
     ↓
  Analyzer Agent → extracts insights from sources
     ↓
  Writer Agent → produces final Markdown report
     ↓
  Saved to Supabase + returned to frontend

WHY SEQUENTIAL (not parallel):
Each agent DEPENDS on the previous agent's output:
- Search needs Planner's sub-tasks to know what to search for
- Analyzer needs Search's sources to have something to analyze
- Writer needs Analyzer's insights to write the report
Parallel execution wouldn't make sense for this pipeline.
"""

import json
import asyncio
import re
from crewai import Crew, Process

from backend.agents.planner_agent import create_planner_agent, create_planner_task
from backend.agents.search_agent import create_search_agent, create_search_task
from backend.agents.analyzer_agent import create_analyzer_agent, create_analyzer_task
from backend.agents.writer_agent import create_writer_agent, create_writer_task
from backend.config import get_llm


async def run_research(query, progress_callback=None):
    """
    Execute the full research pipeline for a given query.

    This is the MAIN ENTRY POINT for the entire agent system.

    Args:
        query: The user's research question (e.g., "AI ethics")
        progress_callback: Optional async function called with status updates.
                          Signature: async callback(agent_name, status, data)
                          Used by the API server to send SSE events to the frontend.

    Returns:
        dict with keys:
            - sub_tasks: Planner output (text)
            - sources: Search output (text)
            - analysis: Analyzer output (text)
            - report: Writer output (Markdown text)

    WHY async:
    Even though CrewAI itself is synchronous, we wrap it in async because:
    1. FastAPI is async — we need to not block the event loop
    2. The progress_callback needs to be async for SSE streaming
    3. We use asyncio.to_thread() to run the sync crew in a thread pool
    """

    async def notify(agent_name, status, data=None):
        """Helper to safely call the progress callback."""
        if progress_callback:
            await progress_callback(agent_name, status, data)

    results = {}

    try:
        # ═══════════════════════════════════════════
        # STEP 1: PLANNER AGENT
        # ═══════════════════════════════════════════
        # WHY first: Everything else depends on having a good research plan.
        # The Planner decomposes the broad query into focused sub-tasks.
        await notify("planner", "active", "Breaking down your research question...")

        planner_agent = create_planner_agent()
        planner_task = create_planner_task(planner_agent, query)

        # WHY Crew even for a single agent:
        # CrewAI's Crew handles the execution lifecycle — retries, logging,
        # output formatting. It's more robust than calling the agent directly.
        planner_crew = Crew(
            agents=[planner_agent],
            tasks=[planner_task],
            process=Process.sequential,
            verbose=True,
            manager_llm=get_llm(),
        )

        # WHY asyncio.to_thread:
        # CrewAI's kickoff() is blocking (synchronous). Running it in a thread
        # pool prevents it from blocking FastAPI's event loop, which would
        # freeze all other requests.
        planner_result = await asyncio.to_thread(planner_crew.kickoff)
        results["sub_tasks"] = str(planner_result)

        await notify("planner", "done", results["sub_tasks"])

        # ═══════════════════════════════════════════
        # STEP 2: SEARCH AGENT
        # ═══════════════════════════════════════════
        # WHY second: Now that we have sub-tasks, we can search for each one.
        # The Search Agent uses Tavily to find relevant web sources.
        await notify("search", "active", "Searching for relevant sources...")

        search_agent = create_search_agent()
        search_task = create_search_task(search_agent, results["sub_tasks"])

        search_crew = Crew(
            agents=[search_agent],
            tasks=[search_task],
            process=Process.sequential,
            verbose=True,
            manager_llm=get_llm(),
        )

        search_result = await asyncio.to_thread(search_crew.kickoff)
        results["sources"] = str(search_result)

        await notify("search", "done", results["sources"])

        # ═══════════════════════════════════════════
        # STEP 3: ANALYZER AGENT
        # ═══════════════════════════════════════════
        # WHY third: With sources collected, the Analyzer extracts insights.
        # It finds patterns, contradictions, and key data points.
        await notify("analyzer", "active", "Analyzing sources and extracting insights...")

        analyzer_agent = create_analyzer_agent()
        analyzer_task = create_analyzer_task(analyzer_agent, results["sources"])

        analyzer_crew = Crew(
            agents=[analyzer_agent],
            tasks=[analyzer_task],
            process=Process.sequential,
            verbose=True,
            manager_llm=get_llm(),
        )

        analyzer_result = await asyncio.to_thread(analyzer_crew.kickoff)
        results["analysis"] = str(analyzer_result)

        # Attempt to parse Visualization Data as JSON
        results["chart_data"] = None
        try:
            # 1. Look for JSON block under '## Visualization Data'
            json_match = re.search(r'```json\s+(.*?)\s+```', results["analysis"], re.DOTALL)
            if json_match:
                parsed_json = json.loads(json_match.group(1))
                if isinstance(parsed_json, list) and len(parsed_json) > 0:
                    results["chart_data"] = parsed_json
        except Exception as e:
            print(f"⚠️ Failed to parse chart data from analysis: {e}")

        await notify("analyzer", "done", results["analysis"])

        # ═══════════════════════════════════════════
        # STEP 4: WRITER AGENT
        # ═══════════════════════════════════════════
        # WHY last: The Writer needs ALL previous data to compose the report.
        # It transforms raw analysis into a polished Markdown document.
        await notify("writer", "active", "Writing your research report...")

        writer_agent = create_writer_agent()
        writer_task = create_writer_task(writer_agent, query, results["analysis"])

        writer_crew = Crew(
            agents=[writer_agent],
            tasks=[writer_task],
            process=Process.sequential,
            verbose=True,
            manager_llm=get_llm(),
        )

        writer_result = await asyncio.to_thread(writer_crew.kickoff)
        results["report"] = str(writer_result)

        await notify("writer", "done", results["report"])

        return results

    except Exception as e:
        await notify("error", "failed", str(e))
        raise


# ─── Direct execution for testing ──────────────────────────
if __name__ == "__main__":
    """
    WHY a __main__ block:
    Allows testing the pipeline directly with:
        python -m backend.crew
    Useful for debugging without starting the full API server.
    """
    import asyncio

    async def test():
        async def print_progress(agent, status, data=None):
            print(f"\n{'='*60}")
            print(f"[{agent.upper()}] Status: {status}")
            if data:
                print(f"Data preview: {str(data)[:200]}...")
            print(f"{'='*60}\n")

        result = await run_research(
            "What are the ethical implications of artificial intelligence?",
            progress_callback=print_progress,
        )
        print("\n\n" + "="*80)
        print("FINAL REPORT:")
        print("="*80)
        print(result["report"])

    asyncio.run(test())
