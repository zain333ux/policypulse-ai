import json
import requests
from src.utils.llm_client import call_llm
from src.utils.json_utils import parse_json_from_llm

def generate_survey(policy_text: str, llm_call=None) -> dict:
    """Generates a structured civic feedback survey based on the policy text.
    Returns a dictionary matching the strict JSON format required.
    """
    fallback_data = {
        "title": "Survey Not Available",
        "description": "Fallback survey due to generation error",
        "sections": [],
        "google_forms_steps": [
            "Manually create Google Form based on policy insights"
        ]
    }

    if not policy_text or not policy_text.strip():
        return fallback_data
        
    system_prompt = """You are a professional civic survey designer. Based on the provided policy document, generate a structured feedback survey template to collect public/student feedback.
The survey must be highly professional, structured, and feel like a real-world civic consultation form.
Keep the total number of questions between 8 to 12.
The survey must include:
- Questions to capture general public feedback and sentiment
- A satisfaction rating question
- Open-ended improvement suggestions

Return ONLY a valid JSON object matching this schema:
{
  "title": "Survey Title",
  "description": "Survey Description",
  "sections": [
    {
      "section_name": "Section name (e.g. Demographics, Policy Feedback, Rating)",
      "questions": [
        {
          "question": "Question text",
          "type": "multiple_choice | rating | text",
          "options": ["Option A", "Option B"] // Must be present if type is multiple_choice, empty list otherwise
        }
      ]
    }
  ],
  "google_forms_steps": [
    "Step 1: Go to Google Forms and create a blank form.",
    "Step 2: Add sections matching the blueprint layout.",
    "Step 3: Insert questions, set types (multiple choice, rating, text), and configure answer options."
  ]
}

Strictly follow these rules:
1. Return ONLY the raw JSON string.
2. DO NOT wrap the output in markdown code blocks like ```json ... ```.
3. DO NOT include explanations, introduction, or trailing text.
"""
    
    user_prompt = f"Policy Document:\n{policy_text}"
    
    try:
        if llm_call is not None:
            response = llm_call(system_prompt, user_prompt)
        else:
            response = call_llm(system_prompt, user_prompt)
        return parse_json_from_llm(response)
    except Exception:
        return fallback_data

GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyyozQ4ZYTJh-vqG6WBuSRALepGihip6ABD-52yzBwiyZvIv0NKWBzAthC-1k_3gW6x0A/exec"

def deploy_google_form(survey_json):
    try:
        # Map nested sections to flat questions schema expected by the Google Apps Script Web App
        flat_questions = []
        sections = survey_json.get("sections", [])
        for section in sections:
            for q in section.get("questions", []):
                flat_questions.append({
                    "question": q.get("question", ""),
                    "type": q.get("type", "text"),
                    "options": q.get("options", [])
                })
                
        # If no sections but there are already flat questions (e.g. fallback or old format)
        if not flat_questions and "questions" in survey_json:
            flat_questions = survey_json.get("questions", [])
            
        flat_payload = {
            "title": survey_json.get("title", "Policy Feedback Survey"),
            "description": survey_json.get("description", ""),
            "questions": flat_questions
        }

        response = requests.post(
            GOOGLE_SCRIPT_URL,
            json=flat_payload
        )
        return response.json()
    except Exception as e:
        return {
            "error": str(e),
            "url": None,
            "edit_url": None
        }
