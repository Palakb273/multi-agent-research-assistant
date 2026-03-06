"""
writer_agent.py — The Research Report Writer Agent
===================================================
WHY THIS AGENT EXISTS:
This is the final agent in the pipeline. It takes the structured analysis
from the Analyzer and transforms it into a polished, readable research
report in Markdown format.

WHY MARKDOWN OUTPUT:
- Universal: renders beautifully in browsers, GitHub, docs, etc.
- Structured: headers, bullet points, links are all native
- Exportable: easily converted to PDF, HTML, docx
- Copyable: users can paste it anywhere and it still looks good

The Writer doesn't add new information — it STRUCTURES and COMMUNICATES
the analysis in the most effective way possible. It's like having a
professional technical writer on your research team.
"""

from crewai import Agent, Task
from backend.config import get_llm


def create_writer_agent():
    """
    Creates and returns the Writer Agent.

    WHY these specific parameters:
    - The writer's backstory emphasizes communication skills (not research skills)
    - This helps the LLM focus on clarity, structure, and readability
    - No tools needed — the writer works with the Analyzer's output
    """
    return Agent(
        role="Research Report Writer",
        goal=(
            "Transform the research analysis into a polished, well-structured "
            "Markdown research report that is clear, comprehensive, and engaging. "
            "The report should be suitable for both technical and non-technical "
            "audiences."
        ),
        backstory=(
            "You are an award-winning research writer and science communicator. "
            "You specialize in making complex topics accessible without losing "
            "depth or accuracy. Your reports are known for their clear structure, "
            "engaging prose, and thorough citations. You follow best practices "
            "in technical writing and always include proper source attribution."
        ),
        verbose=True,
        allow_delegation=False,
        llm=get_llm(),
    )


def create_writer_task(agent, research_query, analysis_output):
    """
    Creates the writing task based on the analysis.

    WHY this report structure:
    Professional research reports follow a standard pattern:
    1. Title & metadata (context)
    2. Executive Summary (for busy readers who want the TL;DR)
    3. Introduction (why this topic matters)
    4. Detailed sections (the actual research findings)
    5. Key Takeaways (actionable conclusions)
    6. Sources (credibility and further reading)

    This structure is universally understood and maximizes readability.
    """
    return Task(
        description=(
            f"Write a comprehensive research report based on the following analysis:\n\n"
            f"Original Research Question: {research_query}\n\n"
            f"Analysis:\n{analysis_output}\n\n"
            f"Your report should follow this structure:\n"
            f"1. **Title**: A compelling, descriptive title\n"
            f"2. **Executive Summary**: A 2-3 paragraph overview of the key findings\n"
            f"3. **Introduction**: Context and importance of the research topic\n"
            f"4. **Detailed Findings**: Separate sections for each major finding/theme, "
            f"   with supporting evidence and analysis. Add inline citation numbers like [1], [2] next to claims.\n"
            f"5. **Key Takeaways**: Bullet points of the most important conclusions\n"
            f"6. **References**: A numbered list matching your inline citations, e.g. `[1] Source Title — Source URL`\n\n"
            f"Use proper Markdown formatting: headers (##), bullet points, bold text, "
            f"and blockquotes for important quotes. Make the report engaging and "
            f"accessible to a general audience while maintaining academic rigor. "
            f"Crucially, YOU MUST INCLUDE INLINE CITATION NUMBERS e.g. [1] THROUGHOUT THE TEXT."
        ),
        expected_output=(
            "A complete Markdown research report with:\n"
            "- A compelling title (# heading)\n"
            "- Executive Summary\n"
            "- Introduction with context\n"
            "- 3-5 detailed finding sections (## headings) WITH inline citations e.g. [1], [2]\n"
            "- Key Takeaways as bullet points\n"
            "- ## References section with numbered sources\n"
            "- Proper Markdown formatting throughout\n"
            "- Approximately 1500-2500 words"
        ),
        agent=agent,
    )
