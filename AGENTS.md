# AGENTS.md

## Project Name
PolicyPulse AI

## Project Purpose
PolicyPulse AI is a hackathon MVP for Education + Civic Tech. It helps universities, student bodies, NGOs, and civic organizations analyze proposed policies and public/student comments.

The app allows a user to upload:
1. A policy document
2. Public/student feedback comments

Then multiple AI agents analyze the content and generate:
- policy summary
- support/opposition analysis
- concern clusters
- affected groups
- policy gaps
- recommended improvements
- executive memo

## Tech Stack
- Python
- Streamlit
- OpenAI API as default LLM
- Gemini API optional
- pandas for CSV handling
- PyMuPDF for PDF parsing
- python-docx for DOCX parsing
- Plotly/Streamlit charts for visualization
- No database for MVP
- No login/auth for MVP

## Core Rules
1. Do not invent packages, APIs, file paths, or environment variables.
2. Use simple Python functions as agents. Do not use CrewAI, LangChain, ChromaDB, FAISS, Flask, FastAPI, or Django unless explicitly requested.
3. Keep the app local-demo friendly and hackathon-safe.
4. Never hard-code API keys or secrets.
5. Use `.env` for keys and `.env.example` for placeholders.
6. Do not commit `.env` or `.venv`.
7. Keep the UI clean, professional, and easy to demo in 3–5 minutes.
8. All AI agent outputs should be structured dictionaries or JSON-like Python objects.
9. Add graceful error handling for missing files, empty comments, missing API keys, and LLM failures.
10. Do not overbuild. Focus on a working MVP first.

## MVP Scope
The MVP must support:
- Uploading or pasting policy text
- Uploading or pasting public/student comments
- Running a multi-agent analysis pipeline
- Showing final results in Streamlit tabs
- Providing a demo-ready executive memo

## Out of Scope
Do not build:
- authentication
- database
- payments
- user accounts
- cloud deployment
- real-time collaboration
- complex vector database
- government API integrations
- legal/medical/financial claims

## Agent Pipeline
The project should use five logical agents:

1. Policy Extraction Agent
   - Extracts main rules, deadlines, affected groups, penalties, and unclear clauses.

2. Public Sentiment Agent
   - Analyzes support, opposition, neutral/mixed feedback, emotional tone, and urgency.

3. Concern Clustering Agent
   - Groups comments into themes and finds repeated concerns.

4. Gap Detection Agent
   - Compares policy content with public concerns and identifies missing protections or unclear areas.

5. Recommendation Agent
   - Generates recommended changes, revised wording, meeting questions, and an executive memo.

## UI Requirements
The Streamlit UI should include:
- App title and short explanation
- Policy upload/paste section
- Comments upload/paste section
- Analyze button
- Progress spinners for each agent
- Results in tabs:
  - Overview
  - Public Concerns
  - Policy Gaps
  - Recommendations
  - Executive Memo

## Demo Requirement
The app must work with prepared sample data even if uploads fail.

Use demo scenario:
University Attendance Policy requiring 85% attendance with no clear exemption or appeal process.

Comments should include concerns about:
- working students
- medical cases
- disability accommodations
- students living far away
- appeal process
- fairness
- transport issues
- support for attendance discipline

## Development Workflow
For every coding task:
1. Read AGENTS.md first.
2. Propose a short implementation plan.
3. Make small focused changes.
4. Do not rewrite unrelated files.
5. Run or explain how to run the app after changes.
6. Summarize changed files and remaining risks.

## Testing Requirements
At minimum, verify:
- Streamlit app starts without import errors.
- Sample policy and comments load correctly.
- Each agent returns structured output.
- Full pipeline completes without crashing.
- Results display clearly in the UI.

## Presentation Goal
The final app should help us say:

“Public feedback is often collected but not properly understood. PolicyPulse AI uses multiple AI agents to turn policies and comments into clear concerns, gaps, and actionable recommendations.”