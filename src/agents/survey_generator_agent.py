import json
import os
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

GOOGLE_SCRIPT_URL = os.getenv("GOOGLE_SCRIPT_URL", "")
GOOGLE_SCRIPT_SECRET = os.getenv("GOOGLE_SCRIPT_SECRET", "")

def deploy_google_form(survey_json):
    if not GOOGLE_SCRIPT_URL:
        return {
            "error": "Google Forms deployment is disabled. Configure GOOGLE_SCRIPT_URL and GOOGLE_SCRIPT_SECRET to enable it.",
            "url": None,
            "edit_url": None
        }
    try:
        payload = {
            "action": "create_form",
            "secret": GOOGLE_SCRIPT_SECRET,
            "blueprint": survey_json
        }

        response = requests.post(
            GOOGLE_SCRIPT_URL,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        if data.get("ok"):
            deployment = data.get("deployment", {})
            return {
                "url": deployment.get("form_url"),
                "edit_url": deployment.get("edit_url"),
                "form_id": deployment.get("form_id"),
                "csv_file_url": deployment.get("csv_file_url"),
                "csv_export_url": deployment.get("csv_export_url"),
                "spreadsheet_url": deployment.get("response_sheet_url"),
                "error": None
            }
        else:
            return {
                "error": data.get("error", "Google Apps Script error"),
                "url": None,
                "edit_url": None
            }
    except Exception as e:
        return {
            "error": str(e),
            "url": None,
            "edit_url": None
        }

def fetch_form_responses(form_id: str) -> dict:
    if not GOOGLE_SCRIPT_URL:
        return {
            "error": "Google Forms deployment is disabled. Configure GOOGLE_SCRIPT_URL to enable fetching.",
            "csv": None
        }
    try:
        payload = {
            "action": "get_responses",
            "secret": GOOGLE_SCRIPT_SECRET,
            "form_id": form_id
        }
        response = requests.post(
            GOOGLE_SCRIPT_URL,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        if data.get("ok"):
            return {
                "csv": data.get("csv"),
                "error": None
            }
        else:
            return {
                "error": data.get("error", "Failed to fetch responses from Google Forms."),
                "csv": None
            }
    except Exception as e:
        return {
            "error": str(e),
            "csv": None
        }
