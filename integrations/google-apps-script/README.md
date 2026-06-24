# Google Forms Connector

This free Google Apps Script Web App creates a Google Form in the project
owner's account and links it to:

- a Google Sheets response workbook;
- an automatically refreshed CSV file in Google Drive;
- direct CSV and Excel export URLs.

## Setup

1. Open [script.google.com](https://script.google.com) and create a new project.
2. Replace the default script with [`Code.gs`](./Code.gs).
3. In **Project Settings → Script Properties**, add:

   ```text
   POLICYPULSE_SECRET=<generate-a-long-random-secret>
   ```

4. Select **Deploy → New deployment → Web app**.
5. Choose:
   - Execute as: **Me**
   - Who has access: **Anyone**
6. Authorize Forms, Sheets, Drive, and trigger permissions.
7. Copy the Web App URL into the API `.env`:

   ```env
   GOOGLE_SCRIPT_URL=https://script.google.com/macros/s/.../exec
   GOOGLE_SCRIPT_SECRET=<the-same-random-secret>
   ```

8. Restart the FastAPI service.

## Response workflow

When PolicyPulse creates a form, the connector also creates a linked response
Sheet and installs an `onFormSubmit` trigger. Each response is stored in the
Sheet by Google Forms, and the trigger refreshes a CSV file in the owner's
Google Drive.

Only the Google account that owns or has access to these files can open the
edit, Sheet, CSV, and Excel links.

