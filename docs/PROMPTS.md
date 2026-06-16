# PROMPTS.md — PolicyPulse AI Fast Build Prompts

## Prompt 1 — Build Core Non-LLM Foundation

Read `AGENTS.md`, `docs/PRD.md`, `docs/ARCHITECTURE.md`, and `docs/TASKS.md`.

Implement the core non-LLM foundation for PolicyPulse AI.

Create or update:

* `src/parsers/file_parser.py`
* `src/parsers/comment_parser.py`
* `src/utils/json_utils.py`
* `src/utils/llm_client.py`
* `src/rag/knowledge_base.py`
* `.env.example`
* `requirements.txt` if needed

Requirements:

* Support PDF, TXT, DOCX policy files.
* Support CSV, TXT, and pasted comments.
* JSON utility must parse normal JSON and fenced JSON.
* LLM client must use `OPENAI_API_KEY` from `.env`.
* Knowledge base must return 10–15 policy design principles.
* Do not hard-code API keys.
* Do not add database, auth, LangChain, CrewAI, ChromaDB, FAISS, Flask, FastAPI, or Django.
* Keep changes simple and hackathon-safe.

After coding:

* Explain changed files.
* Explain how to test.
* Do not rewrite unrelated files.

---

## Prompt 2 — Build All AI Agents and Pipeline

Read `AGENTS.md`, `docs/PRD.md`, `docs/ARCHITECTURE.md`, and `docs/TASKS.md`.

Implement all AI agents and the full pipeline.

Create or update:

* `src/agents/policy_extraction_agent.py`
* `src/agents/sentiment_agent.py`
* `src/agents/concern_clustering_agent.py`
* `src/agents/gap_detection_agent.py`
* `src/agents/recommendation_agent.py`
* `src/agents/survey_generator_agent.py`
* `src/agents/pipeline.py`

Requirements:

* Each agent must return a structured dictionary.
* Use `call_llm()` from `src/utils/llm_client.py`.
* Use `parse_json_response()` from `src/utils/json_utils.py`.
* Concern clusters must include evidence quotes/sample comments.
* Gap detection must use policy principles from `src/rag/knowledge_base.py`.
* Recommendations must include priority ranking: Critical, Important, Nice-to-have.
* Survey Generator must generate a Google-Forms-ready survey template, not real Google Forms API integration.
* Pipeline must run core analysis end-to-end.
* Add clear errors for empty policy or empty comments.

Final pipeline output must include:

* policy_analysis
* sentiment_analysis
* concern_analysis
* gap_analysis
* recommendations

Optional survey output should be separate and should work with policy only.

After coding:

* Explain changed files.
* Explain how to test.
* Do not rewrite unrelated files.

---

## Prompt 3 — Build Streamlit UI

Read `AGENTS.md`, `docs/PRD.md`, `docs/ARCHITECTURE.md`, and `docs/TASKS.md`.

Update `app.py` into a complete Streamlit dashboard.

Requirements:

* Page title: PolicyPulse AI
* Caption: Turn public feedback into clear policy decisions.
* Add short project explanation.
* Add visible multi-agent pipeline view.
* Add `Load Demo Scenario` button.
* Load `sample_data/attendance_policy.txt`.
* Load `sample_data/student_comments.csv`.
* Support policy upload and pasted policy text.
* Support comments upload and pasted comments text.
* Add `Analyze Public Feedback` button.
* Add `Generate Feedback Survey` button.
* Store results in Streamlit session state.
* Show errors with `st.error()`.

Results tabs:

1. Overview
2. Public Concerns
3. Policy Gaps
4. Recommendations
5. Executive Memo
6. Survey Generator

Dashboard features:

* Show sentiment metrics.
* Show concern clusters with evidence quotes.
* Show concern frequency/evidence strength.
* Show gap table.
* Show priority-ranked recommendations.
* Show downloadable executive memo.
* Show survey template if generated.

Keep UI clean, professional, and demo-ready.

After coding:

* Explain changed files.
* Explain how to run:
  `streamlit run app.py`
* Do not rewrite unrelated files.

---

## Prompt 4 — Polish and Debug for Hackathon Demo

Read the full project.

Test and polish the app for a 3–5 minute hackathon demo.

Focus on:

* fixing import errors
* fixing parser errors
* fixing Streamlit UI issues
* improving result display
* making demo data load smoothly
* adding simple concern bar chart if easy
* improving Executive Memo formatting
* ensuring missing API key error is friendly
* ensuring no secrets are committed

Do not add complex features.
Do not add real Google Forms API integration.
Do not add authentication, database, deployment, LangChain, CrewAI, ChromaDB, FAISS, Flask, FastAPI, or Django.

After fixing:

* List bugs fixed.
* List remaining risks.
* Give final demo run steps.
