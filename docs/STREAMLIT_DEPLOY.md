# Streamlit Community Cloud deployment

This repository is already structured to deploy the Streamlit version directly from the repo root.

## App entrypoint

- Main file path: `app.py`
- Python dependencies file: `requirements.txt`

## Required secret

Add this in the Streamlit app **Secrets** panel:

```toml
GROQ_API_KEY = "your_groq_api_key_here"
```

## Optional secrets

Only add these if you want the Google Forms deployment features to work:

```toml
GOOGLE_SCRIPT_URL = "your_google_apps_script_web_app_url"
GOOGLE_SCRIPT_SECRET = "your_google_script_secret"
```

## Deploy steps

1. Push the latest code to GitHub.
2. Open [Streamlit Community Cloud](https://share.streamlit.io/).
3. Click **Create app**.
4. Select your repository: `zain333ux/policypulse-ai`
5. Branch: `main`
6. Main file path: `app.py`
7. Open **Advanced settings**.
8. Paste the required secrets.
9. Click **Deploy**.

## Notes

- The app reads secrets from local `.env` during development and from Streamlit secrets in Community Cloud.
- If Groq usage or quota limits are hit, live analysis can temporarily fail until quota resets.
- Large uploaded files can take longer because the analysis runs through multiple AI steps.
