import json
import re
from json import JSONDecodeError


def _strip_code_fences(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def _extract_balanced_json_object(text: str) -> str | None:
    start_idx = text.find("{")
    if start_idx == -1:
        return None

    depth = 0
    in_string = False
    escape = False

    for index in range(start_idx, len(text)):
        char = text[index]

        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start_idx : index + 1]

    return None


def _try_load(candidate: str) -> dict | None:
    try:
        return json.loads(candidate)
    except JSONDecodeError:
        return None


def parse_json_from_llm(response_text: str) -> dict:
    """Parses JSON from an LLM response, handling fences and extra wrapper text."""
    candidates: list[str] = []

    raw = response_text.strip()
    if raw:
        candidates.append(raw)

    stripped = _strip_code_fences(response_text)
    if stripped and stripped not in candidates:
        candidates.append(stripped)

    match = re.search(r"```(?:json)?\s*(.*?)\s*```", response_text, re.DOTALL | re.IGNORECASE)
    if match:
        fenced = match.group(1).strip()
        if fenced and fenced not in candidates:
            candidates.append(fenced)

    for text in list(candidates):
        balanced = _extract_balanced_json_object(text)
        if balanced and balanced not in candidates:
            candidates.append(balanced)

    for candidate in candidates:
        parsed = _try_load(candidate)
        if parsed is not None:
            return parsed

    raise ValueError(f"Failed to parse JSON from LLM response. Response: {response_text[:160]}...")
