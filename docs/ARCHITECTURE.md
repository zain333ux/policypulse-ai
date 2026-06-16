# Architecture Document — PolicyPulse AI

## 1. Project Overview

PolicyPulse AI is a Streamlit-based hackathon MVP that analyzes a proposed policy document and public/student feedback comments using a multi-agent AI workflow.

The system reads user-provided inputs, runs them through five specialized AI agents, and displays a structured public consultation report.

## 2. High-Level Architecture

User Input
↓
File/Text Parsers
↓
Multi-Agent Analysis Pipeline
↓
Structured Result Object
↓
Streamlit Dashboard

## 3. Tech Stack

* Python
* Streamlit
* OpenAI API as default LLM provider
* Gemini API optional
* python-dotenv for environment variables
* pandas for CSV handling
* PyMuPDF for PDF text extraction
* python-docx for DOCX text extraction
* Plotly or Streamlit native charts for visualization
* Pydantic or normal dictionaries for structured outputs

## 4. Folder Structure

```text
policypulse-ai/
│
├── app.py
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
├── AGENTS.md
├── README.md
│
├── docs/
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   ├── TASKS.md
│   └── DEMO_PLAN.md
│
├── sample_data/
│   ├── attendance_policy.txt
│   └── student_comments.csv
│
├── src/
│   ├── __init__.py
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── policy_extraction_agent.py
│   │   ├── sentiment_agent.py
│   │   ├── concern_clustering_agent.py
│   │   ├── gap_detection_agent.py
│   │   └── recommendation_agent.py
│   │
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── file_parser.py
│   │   └── comment_parser.py
│   │
│   ├── rag/
│   │   ├── __init__.py
│   │   └── knowledge_base.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── llm_client.py
│       └── json_utils.py
│
└── tests/
    └── test_basic_pipeline.py
```

## 5. Data Flow

### Step 1: Policy Input

The user provides a policy through:

* PDF upload
* TXT upload
* pasted text
* sample policy button

The parser converts the input into plain text.

### Step 2: Comments Input

The user provides comments through:

* CSV upload
* TXT upload
* pasted text
* sample comments button

The parser converts comments into a clean list of strings.

### Step 3: Multi-Agent Pipeline

The app runs five agents in sequence:

1. Policy Extraction Agent
2. Public Sentiment Agent
3. Concern Clustering Agent
4. Gap Detection Agent
5. Recommendation Agent

### Step 4: Final Result Object

The pipeline returns one final dictionary containing all outputs.

### Step 5: Streamlit Dashboard

The final result is shown in tabs:

1. Overview
2. Public Concerns
3. Policy Gaps
4. Recommendations
5. Executive Memo

## 6. Agent Responsibilities

### 6.1 Policy Extraction Agent

Input:

* policy text

Output:

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

Purpose:

This agent extracts the most important parts of the uploaded policy.

---

### 6.2 Public Sentiment Agent

Input:

* list of comments

Output:

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

Purpose:

This agent estimates how people feel about the policy.

---

### 6.3 Concern Clustering Agent

Input:

* list of comments

Output:

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

Purpose:

This agent groups repeated comments into meaningful themes.

---

### 6.4 Gap Detection Agent

Input:

* policy extraction result
* concern clustering result
* RAG knowledge base principles

Output:

```json
{
  "gaps": [
    {
      "public_concern": "",
      "covered_in_policy": true,
      "gap_description": "",
      "severity": "low | medium | high",
      "suggested_fix": ""
    }
  ],
  "overall_gap_summary": ""
}
```

Purpose:

This agent compares what people are concerned about against what the policy actually says.

---

### 6.5 Recommendation Agent

Input:

* policy extraction result
* sentiment result
* concern clustering result
* gap detection result

Output:

```json
{
  "recommended_changes": [],
  "revised_policy_wording": [],
  "meeting_questions": [],
  "executive_memo": "",
  "final_summary": ""
}
```

Purpose:

This agent creates the final actionable recommendations and official memo.
### 6.6 Survey Generator Agent Optional

Input:

- policy text
- policy extraction result

Output:

```json
{
  "survey_title": "",
  "survey_description": "",
  "questions": [
    {
      "question": "",
      "type": "multiple_choice | checkbox | short_answer | paragraph | linear_scale",
      "options": [],
      "required": true,
      "purpose": ""
    }
  ],
  "sharing_message": "",
  "google_forms_setup_steps": []
}
## 7. LLM Client Design

The LLM client should live in:

```text
src/utils/llm_client.py
```

Responsibilities:

* Load API keys from `.env`
* Use OpenAI as default
* Optionally support Gemini later
* Provide one function for calling the model
* Handle missing API keys gracefully
* Return plain text response
* Do not hard-code secrets

Recommended function:

```python
def call_llm(system_prompt: str, user_prompt: str) -> str:
    pass
```

## 8. JSON Handling

LLM outputs should be parsed safely.

File:

```text
src/utils/json_utils.py
```

Responsibilities:

* strip markdown fences
* parse JSON
* return fallback dictionaries if needed
* show clear errors if parsing fails

Recommended function:

```python
def parse_json_response(raw_text: str) -> dict:
    pass
```

## 9. RAG / Knowledge Base Design

For the hackathon MVP, use a lightweight local RAG-style knowledge base instead of a vector database.

File:

```text
src/rag/knowledge_base.py
```

It should contain policy design principles such as:

* policies should define clear eligibility rules
* policies should include an appeal process
* policies should consider accessibility needs
* policies should explain deadlines clearly
* policies should include exception handling
* policies should identify affected groups
* policies should communicate penalties transparently

Recommended function:

```python
def get_policy_principles() -> str:
    pass
```

## 10. Streamlit UI Design

The main app file is:

```text
app.py
```

The UI should include:

### Header

* Title: PolicyPulse AI
* Caption: Turn public feedback into clear policy decisions.
* Short explanation

### Sidebar

* Demo scenario explanation
* Button to load sample data
* Optional model/provider info

### Main Input Area

* Policy upload
* Policy paste text area
* Comments upload
* Comments paste text area
* Analyze button

### Results Area

Use tabs:

1. Overview
2. Public Concerns
3. Policy Gaps
4. Recommendations
5. Executive Memo
## Judge-Impressing Dashboard Features

To make the hackathon demo more visual, credible, and understandable, the dashboard should include the following enhancements after the core pipeline is working.

### 1. Pre-Loaded Demo Scenario

The app must include a `Load Demo Scenario` button.

This button should load:

* `sample_data/attendance_policy.txt`
* `sample_data/student_comments.csv`

Purpose:

This avoids wasting demo time on manual file uploads and ensures a smooth presentation.

### 2. Visible Agent Pipeline View

The UI should visually show the multi-agent workflow:

Policy Extraction Agent → Public Sentiment Agent → Concern Clustering Agent → Gap Detection Agent → Recommendation Agent

Optional:

Survey Generator Agent

Purpose:

This helps judges understand that the project is a real multi-agent workflow, not a simple chatbot.

### 3. Evidence Quotes

Each concern cluster should include at least one actual quote from the uploaded comments.

Example:

Concern: Medical Exemptions
Evidence Quote: “There should be a medical exemption process for students who are sick or hospitalized.”

Purpose:

This makes the report more credible and shows that recommendations are grounded in real feedback.

### 4. Recommendation Priority Ranking

Recommendations should be ranked using three levels:

* Critical
* Important
* Nice-to-have

Purpose:

This helps decision-makers understand what should be fixed first.

### 5. Lightweight RAG Visibility

The Gap Detection Agent should explicitly compare:

* public concern
* policy text
* policy design principle from local knowledge base

Purpose:

This allows the team to honestly describe the system as using lightweight RAG-augmented gap detection.

### 6. Concern Frequency / Evidence Strength

Instead of claiming uncertain AI confidence, the app should show evidence-based signals such as:

* Mentioned in 8 out of 25 comments
* Concern Frequency: 32%
* Evidence Strength: High / Medium / Low

Purpose:

This is more defensible than saying “AI is 85% confident.”

### 7. Downloadable Executive Memo

The Executive Memo tab should include a download button.

Suggested file name:

`policy_consultation_memo.md`

Purpose:

This makes the output practical and useful for real decision-makers.

### 8. Optional Admin vs Student Perspective

If time remains, recommendations can be split into two columns:

* What Admin Should Do
* What Students Should Know

Purpose:

This improves real-world usability and makes the output easier to act on.

## 11. Error Handling

The app must handle:

* missing policy input
* missing comments input
* empty uploaded files
* unsupported file types
* missing API key
* LLM response parsing failure
* network/API error
* invalid CSV format

Errors should be shown with `st.error()` and should not crash the whole app.

## 12. Sample Data Requirement

The app must include demo data in:

```text
sample_data/attendance_policy.txt
sample_data/student_comments.csv
```

This ensures the demo works even if file upload fails.

## 13. Testing Plan

Minimum manual tests:

1. Run `streamlit run app.py`.
2. Confirm app loads.
3. Load sample data.
4. Click analyze.
5. Confirm all five agents run.
6. Confirm all result tabs display output.
7. Confirm no API key is committed.
8. Confirm app gives friendly error if API key is missing.

## 14. Design Principles

* Keep the MVP simple.
* Prioritize demo reliability.
* Use clear structured outputs.
* Do not over-engineer.
* Do not add database or login.
* Use sample data for a guaranteed demo.
* Make the final report look useful to decision-makers.

## 15. Final Architecture Summary

PolicyPulse AI is a local Streamlit app with a simple but clear multi-agent architecture. It uses file/text input, lightweight parsing, LLM-powered analysis agents, a local policy principles knowledge base, and a clean results dashboard. The system is designed for a 4-hour hackathon build and a 3–5 minute demo.
