import fitz  # PyMuPDF
import docx

def extract_text_from_pdf(file) -> str:
    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text.strip()
    except Exception as e:
        raise ValueError(f"Error reading PDF: {e}")

def extract_text_from_txt(file) -> str:
    try:
        return file.read().decode("utf-8").strip()
    except Exception as e:
        raise ValueError(f"Error reading TXT: {e}")

def extract_text_from_docx(file) -> str:
    try:
        doc = docx.Document(file)
        return "\n".join([para.text for para in doc.paragraphs]).strip()
    except Exception as e:
        raise ValueError(f"Error reading DOCX: {e}")

def parse_policy_file(file) -> str:
    if file is None:
        return ""
    filename = file.name.lower()
    if filename.endswith(".pdf"):
        return extract_text_from_pdf(file)
    elif filename.endswith(".txt"):
        return extract_text_from_txt(file)
    elif filename.endswith(".docx"):
        return extract_text_from_docx(file)
    else:
        raise ValueError("Unsupported file type. Please upload a PDF, TXT, or DOCX.")
