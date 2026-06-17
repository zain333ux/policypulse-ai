import fitz

def extract_text_from_pdf(file_path_or_bytes) -> str:
    if isinstance(file_path_or_bytes, bytes):
        doc = fitz.open(stream=file_path_or_bytes, filetype="pdf")
    else:
        doc = fitz.open(file_path_or_bytes)
    
    text = ""
    for page in doc:
        text += page.get_text() + "\n"
    doc.close()
    return text

def parse_policy_document(file_content: bytes, filename: str) -> str:
    """Parses PDF or TXT bytes from Streamlit and returns plain text."""
    if filename.lower().endswith('.pdf'):
        return extract_text_from_pdf(file_content)
    else:
        return file_content.decode("utf-8", errors="ignore")
