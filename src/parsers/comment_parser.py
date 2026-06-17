import pandas as pd

def parse_comments_csv(file) -> list[str]:
    try:
        df = pd.read_csv(file)
        
        # Check columns case-insensitively for synonyms
        target_col = None
        possible_columns = ['comment', 'comments', 'feedback', 'text', 'review', 'reviews', 'response', 'responses', 'content', 'message', 'messages']
        
        # Normalize column names to lowercase and trim spaces
        normalized_cols = {col.lower().strip(): col for col in df.columns}
        
        # Try to find one of the possible columns
        for col_name in possible_columns:
            if col_name in normalized_cols:
                target_col = normalized_cols[col_name]
                break
                
        # If no specific column matches, fallback to the first text/string column or first column
        if target_col is None:
            if not df.empty:
                string_cols = [c for c in df.columns if df[c].dtype == object]
                if string_cols:
                    target_col = string_cols[0]
                else:
                    target_col = df.columns[0]
            else:
                raise ValueError("The uploaded CSV file is empty.")
                
        comments = df[target_col].dropna().astype(str).tolist()
        return [c.strip() for c in comments if c.strip()]
    except Exception as e:
        raise ValueError(f"Error reading CSV: {e}")

def parse_comments_txt(file) -> list[str]:
    try:
        content = file.read().decode("utf-8")
        return parse_comments_text(content)
    except Exception as e:
        raise ValueError(f"Error reading TXT: {e}")

def parse_comments_text(raw_text: str) -> list[str]:
    if not raw_text:
        return []
    comments = raw_text.split('\n')
    return [c.strip() for c in comments if c.strip()]

def parse_comments_file(file) -> list[str]:
    if file is None:
        return []
    filename = file.name.lower()
    if filename.endswith(".csv"):
        return parse_comments_csv(file)
    elif filename.endswith(".txt"):
        return parse_comments_txt(file)
    else:
        raise ValueError("Unsupported file type. Please upload a CSV or TXT.")
