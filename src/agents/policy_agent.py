from src.utils.llm_client import call_agent

def analyze_policy(policy_text: str) -> dict:
    prompt = f"Analyze the following policy document:\n\n{policy_text}"
    system_instruction = """
    You are an expert policy analyst. Return a JSON object with the following keys:
    - "policy_title": The inferred title of the policy.
    - "main_rules": A list of strings detailing the primary rules.
    - "penalties": A list of strings detailing the consequences of violation.
    - "affected_groups": A list of strings identifying who is most impacted.
    - "unclear_clauses": A list of strings identifying ambiguous phrasing.
    """
    return call_agent(prompt, system_instruction)
