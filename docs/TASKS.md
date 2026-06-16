# TASKS.md — PolicyPulse AI Build Plan

## Purpose

This file breaks PolicyPulse AI into small implementation tasks that can be safely executed by Antigravity, Codex, Cursor, or another AI coding tool.

The goal is to avoid one huge prompt and instead build the project step by step.

---

## Build Rule

For every task:

1. Read `AGENTS.md`.
2. Read `docs/PRD.md`.
3. Read `docs/ARCHITECTURE.md`.
4. Propose a short plan before coding.
5. Make only the required changes.
6. Do not rewrite unrelated files.
7. Run or explain the test command.
8. Summarize changed files and remaining risks.

---

# Phase 0 — Project Brain

## Task 0.1 — Confirm Project Structure

Status: Done

Goal:

Create initial folders and files:

* `docs/`
* `sample_data/`
* `src/`
* `src/agents/`
* `src/parsers/`
* `src/rag/`
* `src/utils/`
* `tests/`
* `app.py`
* `AGENTS.md`
* `docs/PRD.md`
* `docs/ARCHITECTURE.md`
* `docs/TASKS.md`
* `docs/DEMO_PLAN.md`

Acceptance Criteria:

* All folders exist.
* `app.py` runs with Streamlit.
* Git repo is clean after commit.

---

# Phase 1 — Sample Data

## Task 1.1 — Create Sample Attendance Policy

Goal:

Create `sample_data/attendance_policy.txt`.

The policy should describe a university attendance rule requiring students to maintain 85% attendance to sit in final exams.

It should intentionally be incomplete by not clearly defining:

* medical exemptions
* appeal process
* disability accommodations
* working student flexibility
* transport issues
* attendance dispute process

Acceptance Criteria:

* File exists.
* Policy is realistic.
* Policy is short enough for a demo.
* Policy creates clear gaps for the AI agents to detect.

---

## Task 1.2 — Create Sample Student Comments

Goal:

Create `sample_data/student_comments.csv`.

The CSV should contain at least 20 student comments about the attendance policy.

Columns:

* `id`
* `comment`

Comments should include:

* support for attendance discipline
* opposition to strict 85% rule
* medical exemption concerns
* appeal process concerns
* working student concerns
* disability accommodation concerns
* transport issue concerns
* fairness concerns
* attendance dispute concerns

Acceptance Criteria:

* CSV is valid.
* At least 20 comments exist.
* Comments are varied.
* Comments support a strong demo.

---

# Phase 2 — Parsers

## Task 2.1 — Build File Parser

Goal:

Create `src/parsers/file_parser.py`.

Functions:

```python
extract_text_from_pdf(file) -> str
extract_text_from_txt(file) -> str
extract_text_from_docx(file) -> str
parse_policy_file(file) -> str
```

Requirements:

* Support PDF, TXT, and DOCX.
* Return clean text.
* Raise friendly errors for unsupported file types.
* Do not crash on empty files.

Acceptance Criteria:

* PDF text can be extracted.
* TXT text can be extracted.
* DOCX text can be extracted.
* Unsupported file type gives clear error.

---

## Task 2.2 — Build Comment Parser

Goal:

Create `src/parsers/comment_parser.py`.

Functions:

```python
parse_comments_csv(file) -> list[str]
parse_comments_txt(file) -> list[str]
parse_comments_text(raw_text: str) -> list[str]
parse_comments_file(file) -> list[str]
```

Requirements:

* CSV should support a `comment` column.
* TXT should treat each non-empty line as one comment.
* Pasted text should treat each non-empty line as one comment.
* Remove empty comments.
* Return a list of strings.

Acceptance Criteria:

* CSV comments parse correctly.
* TXT comments parse correctly.
* Pasted comments parse correctly.
* Empty comments are ignored.

---

# Phase 3 — Utilities

## Task 3.1 — Build LLM Client

Goal:

Create `src/utils/llm_client.py`.

Function:

```python
call_llm(system_prompt: str, user_prompt: str) -> str
```

Requirements:

* Load environment variables from `.env`.
* Use `OPENAI_API_KEY` as default.
* Use `gpt-4o-mini` or another available OpenAI model.
* Return raw text response.
* Raise clear error if API key is missing.
* Handle API failures gracefully.

Acceptance Criteria:

* Function works with a valid API key.
* Missing API key gives clear error.
* No API key is hard-coded.

---

## Task 3.2 — Build JSON Utility

Goal:

Create `src/utils/json_utils.py`.

Functions:

```python
strip_markdown_fences(text: str) -> str
parse_json_response(raw_text: str) -> dict
```

Requirements:

* Remove ```json fences if present.
* Parse JSON safely.
* Raise clear error if JSON parsing fails.
* Do not silently return wrong data.

Acceptance Criteria:

* Parses raw JSON.
* Parses fenced JSON.
* Gives clear error on invalid JSON.

---

# Phase 4 — RAG Knowledge Base

## Task 4.1 — Create Lightweight Policy Knowledge Base

Goal:

Create `src/rag/knowledge_base.py`.

Function:

```python
get_policy_principles() -> str
```

The function should return policy design principles, including:

* clear eligibility rules
* transparent penalties
* defined appeal process
* accessibility and disability consideration
* medical/emergency exception handling
* affected group identification
* clear deadlines
* dispute resolution process
* public communication clarity

Acceptance Criteria:

* Function returns a useful multi-line string.
* Gap Detection Agent can use it as context.
* No external database is required.

---

# Phase 5 — AI Agents

## Task 5.1 — Build Policy Extraction Agent

Goal:

Create `src/agents/policy_extraction_agent.py`.

Function:

```python
analyze_policy(policy_text: str) -> dict
```

Output keys:

```json
{
  "policy_title": "",
  "summary": "",
  "main_rules": [],
  "deadlines": [],
  "penalties": [],
  "affected_groups": [],
  "unclear_clauses": [],
  "missing_definitions": []
}
```

Acceptance Criteria:

* Accepts policy text.
* Calls LLM.
* Returns parsed dictionary.
* Handles empty input gracefully.

---

## Task 5.2 — Build Public Sentiment Agent

Goal:

Create `src/agents/sentiment_agent.py`.

Function:

```python
analyze_sentiment(comments: list[str]) -> dict
```

Output keys:

```json
{
  "support_percentage": 0,
  "opposition_percentage": 0,
  "neutral_percentage": 0,
  "overall_mood": "",
  "urgency_level": "",
  "sentiment_summary": ""
}
```

Acceptance Criteria:

* Accepts list of comments.
* Returns sentiment percentages.
* Percentages should roughly total 100.
* Gives useful summary.

---

## Task 5.3 — Build Concern Clustering Agent

Goal:

Create `src/agents/concern_clustering_agent.py`.

Function:

```python
cluster_concerns(comments: list[str]) -> dict
```

Output keys:

```json
{
  "top_concerns": [
    {
      "theme": "",
      "count": 0,
      "summary": "",
      "sample_comments": []
    }
  ],
  "affected_groups": [],
  "repeated_keywords": []
}
```

Acceptance Criteria:

* Groups similar comments.
* Returns top concern themes.
* Includes sample comments.
* Identifies affected groups.

---

## Task 5.4 — Build Gap Detection Agent

Goal:

Create `src/agents/gap_detection_agent.py`.

Function:

```python
detect_gaps(policy_analysis: dict, concern_analysis: dict, policy_principles: str) -> dict
```

Output keys:

```json
{
  "gaps": [
    {
      "public_concern": "",
      "covered_in_policy": true,
      "gap_description": "",
      "severity": "low",
      "suggested_fix": ""
    }
  ],
  "overall_gap_summary": ""
}
```

Acceptance Criteria:

* Compares policy analysis with public concerns.
* Uses policy principles as lightweight RAG context.
* Identifies missing protections or unclear areas.
* Returns gap severity.

---

## Task 5.5 — Build Recommendation Agent

Goal:

Create `src/agents/recommendation_agent.py`.

Function:

```python
generate_recommendations(
    policy_analysis: dict,
    sentiment_analysis: dict,
    concern_analysis: dict,
    gap_analysis: dict
) -> dict
```

Output keys:

```json
{
  "recommended_changes": [],
  "revised_policy_wording": [],
  "meeting_questions": [],
  "executive_memo": "",
  "final_summary": ""
}
```

Acceptance Criteria:

* Produces actionable recommendations.
* Produces revised policy wording.
* Produces public meeting questions.
* Produces copy-ready executive memo.

---

# Phase 6 — Pipeline

## Task 6.1 — Build Full Analysis Pipeline

Goal:

Create `src/agents/pipeline.py`.

Function:

```python
run_policy_analysis(policy_text: str, comments: list[str]) -> dict
```

Pipeline order:

1. `analyze_policy`
2. `analyze_sentiment`
3. `cluster_concerns`
4. `get_policy_principles`
5. `detect_gaps`
6. `generate_recommendations`

Final output:

```json
{
  "policy_analysis": {},
  "sentiment_analysis": {},
  "concern_analysis": {},
  "gap_analysis": {},
  "recommendations": {}
}
```

Acceptance Criteria:

* Pipeline runs end-to-end.
* Each agent output is included.
* Errors are clear.
* Function can be called from `app.py`.

---

# Phase 7 — Streamlit UI

## Task 7.1 — Build Main Input UI

Goal:

Update `app.py`.

UI should include:

* title
* caption
* project explanation
* policy upload
* policy paste text area
* comments upload
* comments paste text area
* sample data button
* analyze button

Acceptance Criteria:

* User can provide policy input.
* User can provide comments input.
* User can load sample data.
* App validates missing inputs.

---

## Task 7.2 — Connect UI to Pipeline

Goal:

Update `app.py` to run `run_policy_analysis`.

Requirements:

* Use Streamlit spinners.
* Store result in session state.
* Show friendly API errors.
* Do not crash on failure.

Acceptance Criteria:

* Clicking analyze runs the full pipeline.
* Result is stored.
* Errors show in UI.

---

## Task 7.3 — Build Results Dashboard

Goal:

Display final result in tabs.

Tabs:

1. Overview
2. Public Concerns
3. Policy Gaps
4. Recommendations
5. Executive Memo

Acceptance Criteria:

* Overview shows summary and metrics.
* Public Concerns shows clusters.
* Policy Gaps shows table.
* Recommendations shows bullet list.
* Executive Memo shows copy-ready memo.

---

# Phase 8 — Polish

## Task 8.1 — Improve UI Styling

Goal:

Make the demo look professional.

Add:

* clean layout
* icons/emojis where useful
* metrics cards
* clear section headings
* tables
* short explanatory captions

Acceptance Criteria:

* App looks presentable for judges.
* Output is easy to scan.
* Demo flow is smooth.

---

## Task 8.2 — Add Downloadable Report

Optional.

Goal:

Allow user to download final report as `.txt` or `.md`.

Acceptance Criteria:

* Download button works.
* Report includes summary, concerns, gaps, recommendations, and memo.

---

# Phase 9 — Testing

## Task 9.1 — Manual Test

Goal:

Run:

```bash
streamlit run app.py
```

Test:

1. App loads.
2. Sample data loads.
3. Analyze button works.
4. All tabs show output.
5. Missing API key shows friendly error.
6. No secrets are committed.

Acceptance Criteria:

* Demo works from start to finish.

---

## Task 9.2 — Basic Unit Tests

Optional if time remains.

Goal:

Create `tests/test_basic_pipeline.py`.

Test:

* comment parsing
* TXT parsing
* JSON utility
* knowledge base returns text

Acceptance Criteria:

* `pytest` runs without failing.

---

# Hackathon Priority Order

If time is limited, complete only:

1. Sample data
2. Parsers
3. LLM client
4. Five agents
5. Pipeline
6. Streamlit input UI
7. Results dashboard
8. Demo polish

Do not spend time on optional features until the core demo works.

---

# Final Done Definition

The project is considered done when:

* `streamlit run app.py` works.
* Sample data can be loaded.
* Analysis pipeline runs.
* The dashboard shows policy summary, sentiment, concerns, gaps, recommendations, and executive memo.
* The demo can be completed in under 5 minutes.
