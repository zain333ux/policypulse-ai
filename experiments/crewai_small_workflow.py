from __future__ import annotations

import os

from crewai import Agent, Crew, LLM, Process, Task


DEMO_POLICY = """
University Attendance Policy

Students must maintain at least 85% attendance in every course.
The policy does not define a medical exemption, disability accommodation,
or appeal process for exceptional cases.
""".strip()

DEMO_COMMENTS = [
    "Working students may miss classes because of shifts. We need an appeal path.",
    "Medical emergencies are real, and the policy should mention exemptions.",
    "Please include disability accommodations explicitly.",
]


def build_llm() -> LLM:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("Set GROQ_API_KEY before running the CrewAI comparison experiment.")
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    return LLM(
        model=f"groq/{model}",
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
        temperature=0.1,
    )


def run_experiment(policy_text: str, comments: list[str]) -> str:
    llm = build_llm()
    policy_agent = Agent(
        role="Policy extraction analyst",
        goal="Extract the rules, affected groups, and unclear clauses from the policy.",
        backstory="You turn raw policy text into concise structured findings for downstream agents.",
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )
    concern_agent = Agent(
        role="Concern clustering analyst",
        goal="Group comments into the strongest recurring concern themes.",
        backstory="You synthesize student and public feedback into evidence-backed themes.",
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )
    recommendation_agent = Agent(
        role="Recommendation analyst",
        goal="Draft the smallest set of practical changes that address the main policy gaps.",
        backstory="You convert extracted policy gaps into action-ready recommendations for leadership.",
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )

    policy_task = Task(
        description=(
            "Read the policy below and return JSON with keys "
            "`main_rules`, `affected_groups`, and `unclear_clauses`.\n\n"
            f"Policy:\n{policy_text}"
        ),
        expected_output="A JSON object summarizing the policy structure.",
        agent=policy_agent,
    )
    concern_task = Task(
        description=(
            "Read the comments below and return JSON with keys "
            "`top_concerns` and `affected_groups`.\n\n"
            "Comments:\n" + "\n".join(f"- {comment}" for comment in comments)
        ),
        expected_output="A JSON object summarizing the recurring concerns.",
        agent=concern_agent,
    )
    recommendation_task = Task(
        description=(
            "Using the policy summary and concern summary from the previous tasks, "
            "return JSON with keys `gaps`, `recommendations`, and `executive_memo`."
        ),
        expected_output="A JSON object containing gaps, recommendations, and a short memo.",
        agent=recommendation_agent,
        context=[policy_task, concern_task],
    )

    crew = Crew(
        name="PolicyPulse comparison experiment",
        agents=[policy_agent, concern_agent, recommendation_agent],
        tasks=[policy_task, concern_task, recommendation_task],
        process=Process.sequential,
        verbose=False,
    )
    result = crew.kickoff()
    return str(result)


if __name__ == "__main__":
    print(run_experiment(DEMO_POLICY, DEMO_COMMENTS))
