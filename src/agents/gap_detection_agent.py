import json
from src.utils.llm_client import call_llm
from src.utils.json_utils import parse_json_from_llm
from src.rag.knowledge_base import get_policy_design_principles

def detect_gaps(policy_details: dict, concern_clusters: dict) -> dict:
    if not policy_details or not concern_clusters:
        raise ValueError("Policy details and concern clusters cannot be empty.")
        
    principles = "\n".join([f"- {p}" for p in get_policy_design_principles()])
    
    system_prompt = f"""You are a legal and policy compliance expert. Compare the extracted policy details with the public concern clusters.
Identify gaps where the policy fails to address major public concerns or violates core policy design principles.

Core Policy Design Principles:
{principles}

Return ONLY a valid JSON object with the key "gaps", which is an array of objects.
Each object in the array must have:
- "concern": string (the public concern or principle at issue)
- "covered_in_policy": boolean (true if the policy attempts to address it, false if completely missing)
- "gap_description": string (detailed explanation of the gap or missing protection)
"""
    
    user_prompt = f"Policy Details:\n{json.dumps(policy_details, indent=2)}\n\nPublic Concern Clusters:\n{json.dumps(concern_clusters, indent=2)}"
    
    response = call_llm(system_prompt, user_prompt)
    return parse_json_from_llm(response)
