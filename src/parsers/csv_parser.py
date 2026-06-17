import pandas as pd
import io

def parse_comments(file_content: bytes, filename: str) -> str:
    """Parses CSV or TXT bytes from Streamlit and returns a formatted string of comments."""
    if filename.lower().endswith('.csv'):
        df = pd.read_csv(io.BytesIO(file_content))
        # Use 'comment' column if it exists, otherwise use the last column
        if 'comment' in df.columns:
            comments = df['comment'].dropna().astype(str).tolist()
        else:
            comments = df.iloc[:, -1].dropna().astype(str).tolist()
        return "\n".join([f"- {c}" for c in comments])
    else:
        return file_content.decode("utf-8", errors="ignore")
