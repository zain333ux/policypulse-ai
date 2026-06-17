from src.utils.llm_client import call_agent
from src.rag.knowledge_base import POLICY_DESIGN_PRINCIPLES

def analyze_gaps(policy_text: str, concern_clusters: list) -> dict:
    import json
    prompt = f"Policy:\n{policy_text}\n\nPublic Concerns:\n{json.dumps(concern_clusters, indent=2)}"
    system_instruction = f"""
    You are a policy gap analyst. Review the policy against public concerns and the following principles:
    {POLICY_DESIGN_PRINCIPLES}
    
    Return a JSON object with:
    - "gaps": A list of dictionaries, each containing:
      - "concern": A short string describing the issue from the public.
      - "covered_in_policy": A boolean indicating if the policy currently addresses this concern.
      - "gap_description": A brief explanation of the disconnect between the policy and public needs.
    """
    return call_agent(prompt, system_instruction)
