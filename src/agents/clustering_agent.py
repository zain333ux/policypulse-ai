from src.utils.llm_client import call_agent

def cluster_concerns(comments_text: str) -> dict:
    prompt = f"Identify the main concern clusters in these comments:\n\n{comments_text}"
    system_instruction = """
    You are a data clustering expert. Return a JSON object with:
    - "concern_clusters": A list of dictionaries, each containing:
      - "theme": A short string describing the cluster.
      - "count": An integer representing the estimated number of comments in this cluster.
      - "sample_comments": A list of 2-3 specific quotes representing the theme.
    """
    return call_agent(prompt, system_instruction)
