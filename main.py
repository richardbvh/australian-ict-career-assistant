# main.py
# Gradio app that routes queries to:
# - RAG (retrieve snippets from OSCA via rag_pipeline.retrieve)
# - Salary tool (Adzuna API) via tools.get_salary
# Router: Google Gemini (prompt-driven) with keyword guardrails; falls back safely if key is missing.

from typing import List, Dict, Tuple, Optional
import re
import os
import yaml
import gradio as gr
from dotenv import load_dotenv

load_dotenv()

from rag_pipeline import retrieve
from tools import get_salary
from prompts import render_tool_block  # template for the tool block

# --------------------- Load config ---------------------
try:
    with open("config.yml", "r") as f:
        CFG = yaml.safe_load(f) or {}
except Exception:
    CFG = {}

TOP_K = CFG.get("rag", {}).get("top_k", 4)
DEFAULT_LOC = CFG.get("tools", {}).get("salary", {}).get("default_location", "Australia")
COUNTRY = CFG.get("tools", {}).get("salary", {}).get("country", "au")

# LLM (Gemini) config
LLM_CFG = CFG.get("llm", {}) or {}
LLM_MODEL = LLM_CFG.get("model", "gemini-2.5-flash")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# --------------------- Gemini router ---------------------
def gemini_route(query: str) -> str:
    """
    Classify into: RAG / TOOL / BOTH using Google Gemini.
    Returns 'rag' on any error or when API key is missing.
    """
    try:
        if not GOOGLE_API_KEY:
            return "rag"
        from google import genai
        client = genai.Client(api_key=GOOGLE_API_KEY)
        prompt = (
            "Classify the user query into exactly one of these labels: RAG, TOOL, BOTH.\n"
            "- RAG: asks about role definitions, tasks, responsibilities, skills\n"
            "- TOOL: asks about salary/pay/wage/compensation\n"
            "- BOTH: asks for both role info and salary\n"
            "Return only ONE WORD: RAG or TOOL or BOTH.\n\n"
            f"Query: {query}\nAnswer:"
        )
        resp = client.models.generate_content(model=LLM_MODEL, contents=prompt)
        label = (resp.text or "").strip().upper()
        return {"RAG": "rag", "TOOL": "tool", "BOTH": "both"}.get(label, "rag")
    except Exception:
        return "rag"

# --------------------- Intent guardrails ---------------------
def _asks_salary(q: str) -> bool:
    ql = (q or "").lower()
    return bool(re.search(r"\b(salary|pay|wage|compensation)\b", ql))

def _asks_role_info(q: str) -> bool:
    ql = (q or "").lower()
    return any(k in ql for k in ["what", "task", "duty", "responsibilit", "skill", "role", "do"])

# --------------------- Router ---------------------
def choose_route(q: str) -> str:
    """
    Return 'rag', 'tool', or 'both'.
    Guardrails first; for ambiguous cases, always try Gemini; fallback to 'rag'.
    """
    q = q or ""
    has_salary = _asks_salary(q)
    has_role = _asks_role_info(q)

    # Obvious cases (fast and deterministic)
    if has_salary and has_role:
        return "both"
    if has_salary and not has_role:
        return "tool"
    if not has_salary and has_role:
        return "rag"

    # Ambiguous -> let Gemini decide; fallback to 'rag' internally
    return gemini_route(q)

# --------------------- RAG rendering ---------------------
def synthesize_from_ctx(ctxs: List[Dict]) -> str:
    """Render retrieved pages as concise bullets (deterministic, grounded)."""
    if not ctxs:
        return "**[OSCA]**\nNo relevant passages were found in the OSCA document."
    bullets = []
    for c in ctxs:
        snippet = (c.get("text") or "").strip().replace("\n", " ")
        if len(snippet) > 280:
            snippet = snippet[:280] + "..."
        page = c.get("meta", {}).get("page", "?")
        bullets.append(f"- (Page {page}) {snippet}")
    return "**[OSCA]**\n" + "\n".join(bullets)

# --------------------- Salary parsing ---------------------
KNOWN_ROLES = [
    "web developer", "software engineer", "cyber security analyst", "cyber security architect", "cyber security engineer", "penetration tester",
    "cyber security operations coordinator", "database administrator", "systems administrator", "ict network and systems engineer", "network administrator", "network architect",
    "ict quality assurance engineer", "ict support engineer", "ict test analyst", "telecommunications engineer", "cloud engineer", "devops engineer",
    "cloud architect", "ict business analyst", "solution architect", "systems analyst", "digital game developer",
]
KNOWN_LOCS = [
    "australia", "sydney", "melbourne", "brisbane", "perth",
    "adelaide", "canberra", "hobart", "gold coast",
]

def _best_role_match(text_lower: str) -> Optional[str]:
    for r in KNOWN_ROLES:
        if r in text_lower:
            return r
    return None

def parse_role_location(q: str, default_loc: str = "Australia") -> Tuple[str, str]:
    """
    Extract (role, LocationTitleCase) from a free-form salary question.
    """
    ql = (q or "").lower()
    loc = next((loc for loc in KNOWN_LOCS if loc in ql), default_loc.lower())
    role = _best_role_match(ql)
    if role is None:
        t = ql
        t = re.sub(r"\b(salary|pay|wage|compensation)\b", " ", t)
        t = t.replace(f"in {loc}", " ")
        t = re.sub(r"\b(what|does|do|task[s]?|dut(?:y|ies)|responsibilit\w*|skill[s]?|and|the|of|a|an|role)\b", " ", t)
        t = re.sub(r"[?.,]", " ", t)
        role = " ".join(t.split()) or "software engineer"  # safe fallback
    return role, loc.title()

# --------------------- Pipeline ---------------------
def answer(user_query: str) -> str:
    """
    1) Route
    2) RAG retrieve (if needed)
    3) Salary tool (if needed) + fallback to Australia when city has no data
    4) Combine to Markdown
    """
    route = choose_route(user_query)
    blocks: List[str] = [f"**Route:** `{route.upper()}`"]  # optional: helps demo/debug

    # RAG
    if route in ("rag", "both"):
        try:
            ctxs = retrieve(user_query, top_k=TOP_K)
            blocks.append(synthesize_from_ctx(ctxs))
        except Exception:
            blocks.append("**[OSCA]**\nIndex not found. Please run `python rag_pipeline.py` to build the index.")

    # Tool
    if route in ("tool", "both"):
        role, loc = parse_role_location(user_query, default_loc=DEFAULT_LOC)
        tool_res = get_salary(role, location=loc, use_adzuna=True, country=COUNTRY)

        used_fallback = False
        if not tool_res or tool_res.get("average_salary_AUD") is None:
            if loc.lower() != "australia":
                tool_res = get_salary(role, location="Australia", use_adzuna=True, country=COUNTRY)
                used_fallback = True

        if tool_res and tool_res.get("average_salary_AUD") is not None:
            blocks.append(
                render_tool_block(
                    role=tool_res["role"],
                    location=tool_res["location"],
                    median=tool_res["average_salary_AUD"],
                    n_samples=tool_res.get("n_samples", 0),
                    source=tool_res.get("source", "Adzuna API"),
                    used_fallback=used_fallback,
                )
            )
        else:
            blocks.append("**Tool – Salary Lookup (Adzuna)**\nNo salary data available for this query.")

    return "\n\n".join(blocks)

# --------------------- UI ---------------------
demo = gr.Interface(
    fn=answer,
    inputs=gr.Textbox(
        label=(
            "Ask about roles (tasks/skills) or salary.\n"
            "Examples:\n"
            "- What does a Web Developer do?\n"
            "- software engineer salary in Australia\n"
            "- What tasks does a Web Developer do and salary in Sydney?"
        ),
        placeholder="Type your question here…",
    ),
    outputs=gr.Markdown(),
    title=CFG.get("app", {}).get("title", "KIT719 Project 2 — RAG + Adzuna Tool"),
)

if __name__ == "__main__":
    # If the default port (7860) is busy, run: python main.py --server.port 7861
    demo.launch()
