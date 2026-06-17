import json
from src.utils.llm_client import call_llm
from src.utils.json_utils import parse_json_from_llm

def extract_policy_details(policy_text: str) -> dict:
    if not policy_text or not policy_text.strip():
        raise ValueError("Policy text cannot be empty.")
        
    system_prompt = """You are an expert policy analyst. Extract key details from the following policy document.
Return ONLY a valid JSON object with these keys:
- "policy_title": string
- "main_rules": array of strings
- "penalties": array of strings
- "affected_groups": array of strings
- "unclear_clauses": array of strings
"""
    
    user_prompt = f"Policy Document:\n{policy_text}"
    
    response = call_llm(system_prompt, user_prompt)
    return parse_json_from_llm(response)
