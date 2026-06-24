/**
 * PolicyPulse AI Google Forms connector.
 *
 * Deploy as a Web App:
 * - Execute as: Me
 * - Who has access: Anyone
 *
 * Before deployment, add a Script Property:
 * POLICYPULSE_SECRET = the same value used by GOOGLE_SCRIPT_SECRET in the API.
 */

/**
 * Run this function ONCE from the Apps Script editor to authorize all required permissions.
 */
function setupAuthorization() {
  Logger.log("Authorization successful!");
}

function doPost(event) {
  try {
    const payload = JSON.parse(event.postData.contents || "{}");
    assertAuthorized(payload.secret);

    if (payload.action === "create_form") {
      return jsonResponse({ ok: true, deployment: createPolicyPulseForm(payload.blueprint) });
    }
    if (payload.action === "get_responses") {
      return jsonResponse(getResponsesCsv(payload.form_id));
    }
    return jsonResponse({ ok: false, error: "Unsupported action." });
  } catch (error) {
    return jsonResponse({ ok: false, error: String(error.message || error) });
  }
}

function assertAuthorized(secret) {
  const expected = PropertiesService.getScriptProperties().getProperty("POLICYPULSE_SECRET");
  if (!expected || !secret || secret !== expected) {
    throw new Error("Unauthorized PolicyPulse request.");
  }
}

function createPolicyPulseForm(blueprint) {
  const sections = blueprint.sections || [];
  const title = blueprint.title || "Policy Feedback Survey";
  const description = blueprint.description || "";

  const form = FormApp.create(title);
  form.setDescription(description);
  form.setConfirmationMessage("Thank you. Your response has been recorded.");
  form.setProgressBar(true);

  if (sections.length > 0) {
    sections.forEach(function(section, sectionIndex) {
      const secTitle = section.title || section.section_name || "";
      const secDesc = section.description || "";
      if (sectionIndex > 0) {
        form.addPageBreakItem().setTitle(secTitle).setHelpText(secDesc);
      } else {
        form.addSectionHeaderItem().setTitle(secTitle).setHelpText(secDesc);
      }
      const questions = section.questions || [];
      questions.forEach(function(question) {
        addQuestion(form, question);
      });
    });
  } else if (blueprint.questions && blueprint.questions.length > 0) {
    // Fallback if flat questions are sent
    blueprint.questions.forEach(function(question) {
      addQuestion(form, question);
    });
  } else {
    throw new Error("Survey blueprint has no questions or sections.");
  }

  const spreadsheet = SpreadsheetApp.create(title + " — Responses");
  form.setDestination(FormApp.DestinationType.SPREADSHEET, spreadsheet.getId());
  SpreadsheetApp.flush();
  Utilities.sleep(1500);
  const responseSheet = findResponseSheet(spreadsheet);

  // Create initial empty CSV in Drive
  const csvFile = DriveApp.createFile(
    title + " — Responses.csv",
    buildCsvFromSheet(responseSheet),
    MimeType.CSV
  );

  // Store metadata linking form ID to spreadsheet and CSV IDs
  PropertiesService.getScriptProperties().setProperty(
    "FORM_" + form.getId(),
    JSON.stringify({
      spreadsheetId: spreadsheet.getId(),
      csvFileId: csvFile.getId()
    })
  );

  // Programmatically create Form submit trigger to keep the CSV in Drive synced
  ScriptApp.newTrigger('syncResponsesToCsv')
    .forForm(form)
    .onFormSubmit()
    .create();

  const spreadsheetId = spreadsheet.getId();
  return {
    form_url: form.getPublishedUrl(),
    edit_url: form.getEditUrl(),
    response_sheet_url: spreadsheet.getUrl(),
    csv_file_url: csvFile.getUrl(),
    csv_export_url:
      "https://docs.google.com/spreadsheets/d/" +
      spreadsheetId +
      "/export?format=csv&gid=" +
      responseSheet.getSheetId(),
    xlsx_export_url:
      "https://docs.google.com/spreadsheets/d/" + spreadsheetId + "/export?format=xlsx",
    form_id: form.getId(),
    spreadsheet_id: spreadsheetId,
    message:
      "The form is live. Responses are synced to Google Sheets and a CSV copy in Drive. Changes sync automatically on submit."
  };
}

function addQuestion(form, question) {
  let item;
  const title = question.question;

  if (question.type === "multiple_choice") {
    item = form.addMultipleChoiceItem();
    item.setChoiceValues(question.options || []);
  } else if (question.type === "checkboxes") {
    item = form.addCheckboxItem();
    item.setChoiceValues(question.options || []);
  } else if (question.type === "linear_scale" || question.type === "rating") {
    item = form.addScaleItem();
    const minVal = question.scale_min !== undefined ? question.scale_min : 1;
    const maxVal = question.scale_max !== undefined ? question.scale_max : 5;
    item.setBounds(minVal, maxVal);
    item.setLabels(question.scale_min_label || "", question.scale_max_label || "");
  } else if (question.type === "paragraph") {
    item = form.addParagraphTextItem();
  } else {
    item = form.addTextItem();
  }

  item.setTitle(title);
  item.setRequired(Boolean(question.required));
  if (question.purpose && item.setHelpText) {
    item.setHelpText(question.purpose);
  }
}

function syncResponsesToCsv(event) {
  try {
    const form = event.source;
    const stored = PropertiesService.getScriptProperties().getProperty("FORM_" + form.getId());
    if (!stored) {
      return;
    }
    const metadata = JSON.parse(stored);
    const spreadsheet = SpreadsheetApp.openById(metadata.spreadsheetId);
    const csv = buildCsvFromSheet(findResponseSheet(spreadsheet));
    DriveApp.getFileById(metadata.csvFileId).setContent(csv);
  } catch (err) {
    Logger.log("Failed syncing response to CSV: " + String(err));
  }
}

function getResponsesCsv(formId) {
  const stored = PropertiesService.getScriptProperties().getProperty("FORM_" + formId);
  if (!stored) {
    throw new Error("No metadata found for form ID: " + formId);
  }
  const metadata = JSON.parse(stored);
  const spreadsheet = SpreadsheetApp.openById(metadata.spreadsheetId);
  const sheet = findResponseSheet(spreadsheet);
  const csvContent = buildCsvFromSheet(sheet);
  return {
    ok: true,
    form_id: formId,
    csv: csvContent
  };
}

function findResponseSheet(spreadsheet) {
  const sheets = spreadsheet.getSheets();
  const named = sheets.find(function(sheet) {
    return /^Form Responses/i.test(sheet.getName());
  });
  if (named) {
    return named;
  }
  return sheets.reduce(function(best, sheet) {
    return sheet.getLastColumn() > best.getLastColumn() ? sheet : best;
  }, sheets[0]);
}

function buildCsvFromSheet(sheet) {
  const values = sheet.getDataRange().getDisplayValues();
  return values
    .map(function(row) {
      return row
        .map(function(value) {
          return '"' + String(value).replace(/"/g, '""') + '"';
        })
        .join(",");
    })
    .join("\r\n");
}

function jsonResponse(payload) {
  return ContentService.createTextOutput(JSON.stringify(payload)).setMimeType(
    ContentService.MimeType.JSON
  );
}
