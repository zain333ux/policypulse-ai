import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def call_llm(system_prompt: str, user_prompt: str) -> str:
    """Calls OpenAI API. Single entry point for all agents.
    Uses gpt-4o-mini for fast, cost-effective hackathon inference.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is missing. Add it to your .env file.")

    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3
    )

    return response.choices[0].message.content
