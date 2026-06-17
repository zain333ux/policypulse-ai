import json
from src.utils.llm_client import call_llm
from src.utils.json_utils import parse_json_from_llm

def cluster_concerns(comments: list[str]) -> dict:
    if not comments:
        raise ValueError("Comments list cannot be empty.")
        
    system_prompt = """You are an expert qualitative researcher. Group the following list of public comments into common thematic clusters or concerns.
Return ONLY a valid JSON object with the key "concern_clusters", which is an array of objects.
Each object in the array must have:
- "theme": string (the name of the concern cluster)
- "count": integer (estimated number of comments falling into this theme)
- "sample_comments": array of strings (2-3 direct quotes or sample comments serving as evidence)
- "urgency_level": string ("High", "Medium", or "Low")
"""
    
    comments_text = "\n".join([f"- {c}" for c in comments])
    user_prompt = f"Public Comments:\n{comments_text}"
    
    response = call_llm(system_prompt, user_prompt)
    return parse_json_from_llm(response)
