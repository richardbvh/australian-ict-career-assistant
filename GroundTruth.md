# Ground Truth & Evaluation (KIT719 Project 2)

**Run date:** 2025-10-18 (AEST/Hobart)
**Config:** `TOP_K = 3`, `COUNTRY = au`
**Doc set:** `OSCA_27_ICT.pdf` (Chroma; `all-MiniLM-L6-v2`)
**Router:** Keyword guardrails (+ Gemini fallback if configured)

## Baseline Questions (5–7)

### 1) RAG — What tasks does a Web Developer do?

**Expected citations (OSCA):**
[Page 17] “Web Developer — Plans, produces and maintains websites … using web programming languages, software applications, technologies and databases …”

**Manual answer (from citations only):**
Plans, produces and maintains websites using web programming languages, software/technologies and databases to meet user needs; collaborates with others.

**System check (this run):**
* Retrieved includes expected pages? **YES** (Pages 17, 22, 22)
* Grounded (shows Page N)? **YES** → [Page 17]
* Factually correct? **YES**

### 2) RAG — What is the OSCA skill level for Software Engineer?

**Expected citation (OSCA):**
[Page 14] contains “Skill level: 1”.

**Manual answer:** Skill level 1.

**System check (this run):**
* Retrieved includes page with “Skill level: 1”? **YES** (Pages 14, 1, 20)
* Grounded? **YES** → [Page 14]
* Correct? **YES**

### 3) RAG — List alternative titles for ICT Database Administrator.

**Expected citation (OSCA):**
[Page 8] “Alternative titles: DBA, ICT Database Manager …” (and “ICT Database Analyst” under specialisation)

**Manual answer:** DBA, ICT Database Manager (related: ICT Database Analyst as a specialisation).

**System check (this run):**
* Retrieved includes expected page? **YES** (Page 8, also 8; Page 18 = unrelated BA titles)
* Grounded? **YES** → [Page 8]
* Correct? **YES**

### 4) TOOL — software engineer salary in Australia

**Manual tool call (from run):**
* **Median:** A$ 130,000
* **Samples:** 13
* **Source/Notes:** Adzuna API (median, filtered); `pages_queried=2`; `results_per_page=50`; `category=it-jobs`; `max_days_old=90`; `client_filters="30k<=s<=300k, median"`

**System check:**
* Tool invoked? **YES**
* Matches manual? **YES**
* Grounded block? **YES**

### 5) TOOL — web developer salary in Sydney

**Manual tool call (from run):**
* **Median:** A$ 115,700
* **Samples:** 7
* **Source/Notes:** Adzuna API (median, filtered)

**System check:**
* Tool invoked? **YES**
* Matches manual? **YES**
* Grounded block? **YES**

### 6) BOTH — What does a Database Administrator do and salary in Australia?

**Expected RAG citations:**
* [Page 7] DBA role definition (“Plans, designs, configures, maintains and supports an organisation’s DBMS …”)
* [Page 8] Alternative titles + tasks context

**Manual tool result:**
* **Median:** A$ 140,000
* **Samples:** 9
* **Source:** Adzuna API (median, filtered)

**System check (this run):**
* Router = BOTH? **YES**
* RAG grounded with Page N? **YES** (Pages 8, 7, 1)
* Tool block with numbers? **YES**
* Correct overall? **YES**

### 7) BOTH — What tasks does a Web Developer do and salary in Sydney?

**Expected RAG citations:** [Page 17] (Web Developer tasks)

**Manual tool result:**
* **Median:** A$ 115,700
* **Samples:** 7
* **Source:** Adzuna API (median, filtered)

**System check (this run):**
* Router = BOTH? **YES**
* RAG grounded with Page N? **YES** (Pages 17, 1, 20)
* Tool block with numbers? **YES**
* Correct overall? **YES**

---

## Difficult Questions (2–3)

### D1) City-level sparse data

**Query:** “web developer salary in Hobart CBD and typical responsibilities”
**Observed:** RAG → Pages 17, 18, 1. Tool → No city data → Fallback Australia: A$ 105,000 (n=15).
**Why difficult:** Sparse postings at city granularity.
**Resolution:** Fallback to AU median with explanation.
**Improvements:** Add state-level fallback; relax filters / increase pages queried.

### D2) Overly broad RAG query

**Query:** “Tell me everything about ICT roles”
**Observed:** RAG pulls generic pages (19, 18, 9).
**Why difficult:** Scope too broad → noisy retrieval.
**Improvements:** Ask user to narrow; optionally raise `top_k`; add query rewrite for target role.

### D3) Role not in OSCA

**Query:** “What does a Prompt Engineer do and salary in Australia?”
**Observed:** RAG has no direct entry (hits 1/22/20 are generic nearby roles). Tool returns A$ 165,000 (n=5).
**Why difficult:** Document coverage gap.
**Improvements:** Keep a small auxiliary glossary; clearly label “role not in OSCA” in UI when applicable.

---

## Routing Decisions (sanity from run)

* “web developer salary in Hobart CBD and typical responsibilities” → **BOTH**
* “Tell me everything about ICT roles” → **RAG**
* “What does a Prompt Engineer do and salary in Australia?” → **BOTH**
* “What tasks does a Web Developer do?” → **RAG**
* “software engineer salary in Australia” → **TOOL**
* “What tasks does a Web Developer do and salary in Sydney?” → **BOTH**

---

## Summary

* **RAG coverage:** 3/3 baseline RAG questions retrieved expected pages and can be cited (Pages 17, 14, 8).
* **Tool correctness:** 3/3 baseline tool queries produced medians & samples with clear source (Adzuna).
* **BOTH routing:** 2/2 baseline BOTH handled correctly with grounded RAG + numeric tool output.
* **Difficult cases:** City-sparse salaries handled via fallback; broad/out-of-scope queries behave sensibly.
* **Next improvements:** sentence-level chunking + re-ranking; optional LLM writer to turn bullets into short paragraphs with [Page N] cites; add state-level salary fallback.