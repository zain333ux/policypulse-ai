import json
from src.utils.llm_client import call_llm
from src.utils.json_utils import parse_json_from_llm

def analyze_sentiment(comments: list[str]) -> dict:
    if not comments:
        raise ValueError("Comments list cannot be empty.")
        
    system_prompt = """You are an expert in public sentiment analysis. Analyze the following list of public comments regarding a policy.
Return ONLY a valid JSON object with these keys:
- "support_percentage": integer (0-100)
- "opposition_percentage": integer (0-100)
- "neutral_percentage": integer (0-100)
- "overall_mood": string (a short phrase describing the general emotional tone, e.g., "Highly frustrated", "Cautiously optimistic")
"""
    
    comments_text = "\n".join([f"- {c}" for c in comments])
    user_prompt = f"Public Comments:\n{comments_text}"
    
    response = call_llm(system_prompt, user_prompt)
    return parse_json_from_llm(response)
