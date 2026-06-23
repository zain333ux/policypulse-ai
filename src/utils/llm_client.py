import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

def call_llm(system_prompt: str, user_prompt: str) -> str:
    """Calls Groq API. Single entry point for all agents.
    Uses llama-3.3-70b-versatile for fast, cost-effective hackathon inference.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is missing. Add it to your .env file.")

    client = Groq(api_key=api_key)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3
    )

    return response.choices[0].message.content
