import json
from src.utils.llm_client import call_llm
from src.utils.json_utils import parse_json_from_llm

def generate_recommendations(policy_details: dict, gaps: dict) -> dict:
    if not policy_details or not gaps:
        raise ValueError("Policy details and gaps cannot be empty.")
        
    system_prompt = """You are a senior policy advisor. Based on the policy details and identified gaps, generate actionable recommendations.
Provide prioritized recommendations, suggestions for revised policy wording, questions for the next stakeholder meeting, and an executive memo.

Return ONLY a valid JSON object with these keys:
- "recommendations": array of objects, each with "priority" ("Critical", "Important", "Nice-to-have") and "action" (string)
- "revised_policy_suggestions": array of strings (suggested wording changes)
- "meeting_questions": array of strings (questions to ask in the next committee meeting)
- "executive_memo": string (a 2-3 paragraph summary memo addressed to leadership)
"""
    
    user_prompt = f"Policy Details:\n{json.dumps(policy_details, indent=2)}\n\nIdentified Gaps:\n{json.dumps(gaps, indent=2)}"
    
    response = call_llm(system_prompt, user_prompt)
    return parse_json_from_llm(response)
