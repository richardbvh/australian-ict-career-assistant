# prompts.py
# Centralized prompts/templates for the project.
# Keep all routing/system/tool descriptions here.

SYSTEM_PROMPT = """You are a helpful career assistant.
- For role questions (tasks/skills/duties), ground your answer in the OSCA document excerpts.
- For salary questions, use the Salary Tool output. Do not invent numbers.
- Be concise and factual.
"""

ROUTER_PROMPT = """Classify the query into exactly one label: RAG, TOOL, or BOTH.
- RAG: asks about tasks/skills/definitions of a role
- TOOL: asks about salary/pay/wage/compensation
- BOTH: asks for both role info and salary
Return only one word: RAG or TOOL or BOTH.
Query: {query}
"""

# RAG answer template (used if you later add an LLM to write a paragraph)
RAG_ANSWER_TEMPLATE = """Write a short answer using ONLY the snippets below.
Cite each claim with [Page N]. Do not invent facts.

Snippets:
{snippets}

User question:
{query}

Answer:
"""

# Tool answer template (we already use a hand-written renderer in main.py,
# but we keep a template here to satisfy the requirement and for consistency).
TOOL_ANSWER_TEMPLATE = """**Tool – Salary Lookup (Adzuna)**
- Role: **{role}**
- Location: **{location}**
- Estimated median salary: **A$ {median:,.0f}/year**
- Samples used: **{n_samples}**
- Source: {source}{extras}
"""

FALLBACK_CITY_TO_COUNTRY_NOTE = "\n_(No city-level salary found; using Australia-wide data.)_"

def render_tool_block(role: str, location: str, median: float, n_samples: int,
                      source: str, used_fallback: bool) -> str:
    """Return a formatted Markdown block for the salary tool."""
    extras = FALLBACK_CITY_TO_COUNTRY_NOTE if used_fallback else ""
    return TOOL_ANSWER_TEMPLATE.format(
        role=role.title(),
        location=location,
        median=median,
        n_samples=n_samples,
        source=source,
        extras=extras
    )
