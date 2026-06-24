# Orchestration Evaluation

This document keeps the production decision disciplined:

- explicit Python workflow is the stable baseline
- LangGraph is the main advanced orchestration option
- CrewAI is isolated to a separate experiment and is not imported by production code

## Current verification

- Backend regression suite: `16 passed`
- Orchestrator parity test: explicit Python and LangGraph return matching outputs with the same fake LLM responses
- Benchmark script: `experiments/benchmark_orchestrators.py`
- CrewAI experiment smoke check: import and LLM construction passed after installing `crewai` and `litellm`

## Evaluation table

| Option | Role in repo | Reliability status | Latency status | Cost proxy | Implementation complexity |
| --- | --- | --- | --- | --- | --- |
| Explicit Python | Production baseline | Strongest current confidence. Full backend suite passes and this is the default path. | `31.99 ms` average in the local fake-LLM benchmark. | `5` structured LLM calls per production run. | Low. No extra orchestration dependency. |
| LangGraph | Main advanced production orchestration | Good confidence. Parity test passed against the Python baseline using identical fake outputs. | `68.27 ms` average in the same local benchmark. | `5` structured LLM calls per production run. | Medium. Adds one orchestration dependency and graph state wiring. |
| CrewAI experiment | Separate comparison only | Partial confidence. Import and model-construction smoke checks passed, but no live kickoff was run in this pass. | Not benchmarked yet in this repo. | `3` task-level calls in the current small experiment file. | High. Adds a heavier dependency surface plus `litellm` routing. |

## Recommendation

Use explicit Python as the default production setting while the project is still optimizing reliability and demo readiness.

Use LangGraph when you want:

- graph visualization
- explicit fan-out and fan-in orchestration
- future human approval checkpoints
- resumable workflow state

Keep CrewAI out of production. The current repo benefits more from a clean evidence-first pipeline than from a role-play style multi-agent runtime.

## How to reproduce

```powershell
pip install -e ".\apps\api[langgraph,experiments]"
$env:PYTHONPATH="D:\ccccc\Desktop\policypulse-ai\apps\api"
.\.venv\Scripts\python.exe experiments\benchmark_orchestrators.py
.\.venv\Scripts\python.exe -m pytest apps\api\tests -q
.\.venv\Scripts\python.exe experiments\crewai_small_workflow.py
```

The final command requires a valid `GROQ_API_KEY` and was intentionally kept outside the production app path.
