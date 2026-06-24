# PolicyPulse AI

PolicyPulse AI turns proposed policies and stakeholder comments into traceable concerns, policy gaps, prioritized recommendations, and an executive memo.

The production application is a Next.js frontend with a FastAPI backend. The original Streamlit implementation remains in `app.py` as a reference version.

> Public feedback is often collected but not properly understood. PolicyPulse AI connects each major finding to the exact policy passage or public comment that supports it.

## What this project includes

- Policy and comment ingestion from PDF, DOCX, TXT, CSV, pasted text, and spreadsheet exports.
- Structured policy analysis with evidence-linked findings.
- Comment-level sentiment and concern clustering.
- Policy gap detection with clear suggested fixes.
- Prioritized recommendations and an executive memo.
- Survey blueprint generation for situations where feedback has not yet been collected.
- Exportable Markdown and PDF reports.
- Accessible charts, light/dark themes, and responsive layouts.

## Agentic workflow

The production system is intentionally not a framework zoo. It uses a stable baseline with one main advanced orchestration path, plus one isolated comparison experiment.

| Layer | Role | Status |
| --- | --- | --- |
| Explicit Python workflow | Stable production baseline | Active |
| LangGraph | Main advanced orchestration implementation | Active |
| CrewAI | Small isolated comparison experiment | Experimental |

The production application does not mix LangGraph, CrewAI, AutoGen, and ADK inside the same runtime path.

## Technology stack

- Python
- FastAPI
- Streamlit
- Next.js
- React
- TypeScript
- Groq API as the default live LLM provider
- Optional xAI Grok support
- pandas for CSV handling
- PyMuPDF for PDF parsing
- python-docx for DOCX parsing
- Plotly and Streamlit charts for visualization

## Deployment

Frontend:

- Deployed on Vercel
- Root directory: `apps/web`
- API URL is supplied through `NEXT_PUBLIC_API_URL`

Backend:

- Deployed on Render
- Root directory: `apps/api`
- Build command: `pip install .`
- Start command: `uvicorn policypulse_api.main:app --host 0.0.0.0 --port $PORT`

Current blueprint:

- [`render.yaml`](./render.yaml)

## Repository layout

```text
apps/
  api/    FastAPI service, orchestration, schemas, reports, tests
  web/    Next.js application, analysis UI, survey UI, and evidence views
app.py    preserved Streamlit reference implementation
docs/     architecture notes, product documentation, and internal planning
experiments/
sample_data/
```

## Local setup

Requirements:

- Python 3.11+
- Node.js 22+
- A Groq API key for live analysis

Clone the repository and create your environment:

```powershell
git clone <repository-url>
cd policypulse-ai
Copy-Item .env.example .env
```

Add the core variables to `.env`:

```env
GROQ_API_KEY=your_key_here
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

Optional provider settings:

```env
# Use one provider explicitly when both keys are present
LLM_PROVIDER=groq
# Optional xAI Grok support
XAI_API_KEY=your_xai_key_here
XAI_MODEL=grok-4.3
```

Install and run the API:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".\apps\api[dev]"
uvicorn policypulse_api.main:app --app-dir apps/api --reload --port 8000
```

Install and run the web application in another terminal:

```powershell
cd apps\web
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). API documentation is available at [http://localhost:8000/docs](http://localhost:8000/docs).

Docker is also supported:

```powershell
docker compose up --build
```

## Configuration

| Variable | Required | Purpose |
| --- | --- | --- |
| `GROQ_API_KEY` | Live AI only | Server-side model access |
| `GROQ_MODEL` | No | Defaults to `llama-3.3-70b-versatile` |
| `XAI_API_KEY` | Live AI only | Optional xAI Grok API key |
| `XAI_MODEL` | No | Defaults to `grok-4.3` |
| `LLM_PROVIDER` | No | Explicit provider override: `groq` or `xai` |
| `ANALYSIS_ORCHESTRATOR` | No | `python` by default; set `langgraph` for the advanced orchestration path |
| `FRONTEND_ORIGIN` | Production | Allowed web origin for CORS |
| `NEXT_PUBLIC_API_URL` | Yes | Browser-visible FastAPI base URL |
| `UPSTASH_REDIS_REST_URL` | No | Optional temporary distributed job storage |
| `UPSTASH_REDIS_REST_TOKEN` | No | Optional Upstash credential |
| `GOOGLE_SCRIPT_URL` | Google Forms only | Deployed Apps Script Web App URL |
| `GOOGLE_SCRIPT_SECRET` | Google Forms only | Shared connector secret |

Without Upstash, the API uses an in-memory TTL store, which is appropriate for a single free Render instance.

### Google Forms setup

The connector source and deployment instructions are in [`integrations/google-apps-script`](./integrations/google-apps-script). It runs under the project owner’s Google account. Each generated form is linked to a Google Sheet, and an installable trigger refreshes a CSV file in Drive after every response. The owner also receives direct CSV and Excel export links.

## Testing

Backend:

```powershell
python -m pytest apps\api\tests -q
python -m ruff check apps\api
python -m mypy --config-file apps\api\pyproject.toml apps\api\policypulse_api
```

Optional orchestration work:

```powershell
pip install -e ".\apps\api[langgraph,experiments]"
$env:ANALYSIS_ORCHESTRATOR="langgraph"
.\.venv\Scripts\python.exe experiments\benchmark_orchestrators.py
.\.venv\Scripts\python.exe experiments\crewai_small_workflow.py
```

Frontend:

```powershell
cd apps\web
npm run lint
npm run typecheck
npm run build
npx playwright install chromium
npm run test:e2e
```

GitHub Actions runs backend, frontend, end-to-end, dependency, and secret checks on pushes and pull requests.

## Privacy and responsible AI

- Uploaded content is processed for the current analysis and is not permanently stored by the application.
- Temporary jobs expire automatically.
- Content is sent to the configured AI provider.
- Every generated finding must reference valid indexed evidence or be labeled as limited evidence.
- Outputs are AI-generated, require human review, and are not legal advice.
- Do not upload confidential or personally identifying data.

## Engineering trade-offs

This MVP intentionally avoids authentication, billing, permanent databases, microservices, Kubernetes, and heavy agent frameworks. Those additions would increase operational surface without improving the core value proposition:

clean UX + real AI workflow + traceable evidence + report export + reliable engineering.

The stable baseline uses explicit Python services and typed schemas so behavior is easy to inspect, test, and explain. LangGraph is available as the main advanced orchestration option, while the CrewAI comparison stays isolated under [`experiments/`](./experiments).

For model providers, the production pipeline supports both Groq and xAI Grok. If both keys are present, set `LLM_PROVIDER` explicitly so behavior stays predictable.

## Legacy Streamlit reference

The original Streamlit application is still available:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

It is preserved as a reference implementation for the earlier hackathon phase.
