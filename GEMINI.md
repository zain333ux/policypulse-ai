# PolicyPulse AI — Project Context

## What we are building
A Streamlit app where a user uploads a policy document (PDF/TXT) and a public comments file (CSV/TXT). Five AI agents analyze them and produce a report dashboard.

## Tech stack
Python, Streamlit, OpenAI API (key in .env as OPENAI_API_KEY), PyMuPDF, pandas, plotly. All packages are already installed.

## Project path
C:\Users\abdul\policypulse-ai\

## File structure
app.py
requirements.txt
.env
sample_data/attendance_policy.txt
sample_data/student_comments.csv
src/parsers/pdf_parser.py
src/parsers/csv_parser.py
src/agents/policy_agent.py
src/agents/sentiment_agent.py
src/agents/clustering_agent.py
src/agents/gap_agent.py
src/agents/recommendation_agent.py
src/rag/knowledge_base.py
src/utils/llm_client.py

## The 5 agents and their JSON outputs
1. policy_agent: extracts policy_title, main_rules[], penalties[], affected_groups[], unclear_clauses[]
2. sentiment_agent: returns support_percentage, opposition_percentage, neutral_percentage, overall_mood
3. clustering_agent: returns concern_clusters[] each with theme, count, sample_comments[]
4. gap_agent: returns gaps[] each with concern, covered_in_policy (bool), gap description
5. recommendation_agent: returns recommendations[], revised_policy_suggestions[], meeting_questions[], executive_memo

## Streamlit UI — 5 tabs
Tab 1: Overview — policy summary, comment count, sentiment pie chart
Tab 2: Public Concerns — clusters, sample comments, urgency level
Tab 3: Policy Gaps — table showing concern, covered?, gap description
Tab 4: Recommendations — bullet list and revised clauses
Tab 5: Executive Memo — copyable text box

## Code rules
- Each agent is a single Python function taking text input and returning a dict
- Use python-dotenv to load API key
- Each agent calls OpenAI with a structured JSON prompt and parses the response
- Handle errors with try/except
- Keep all agents modular and independent
