import json
import re

def parse_json_from_llm(response_text: str) -> dict:
    """Parses JSON from an LLM response, handling optional markdown fences."""
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass
    
    match = re.search(r"```(?:json)?\n(.*?)\n```", response_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
            
    # Try finding first { and last } if above fails
    start_idx = response_text.find('{')
    end_idx = response_text.rfind('}')
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        try:
            return json.loads(response_text[start_idx:end_idx+1])
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Failed to parse JSON from LLM response. Response: {response_text[:100]}...")
