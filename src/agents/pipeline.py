from src.agents.policy_extraction_agent import extract_policy_details
from src.agents.sentiment_agent import analyze_sentiment
from src.agents.concern_clustering_agent import cluster_concerns
from src.agents.gap_detection_agent import detect_gaps
from src.agents.recommendation_agent import generate_recommendations
from src.agents.survey_generator_agent import generate_survey

def run_pipeline(policy_text: str, comments: list[str]) -> dict:
    """Runs the full analysis pipeline using the provided policy text and comments."""
    if not policy_text or not policy_text.strip():
        raise ValueError("Policy text cannot be empty.")
    if not comments:
        raise ValueError("Comments cannot be empty.")
        
    # 1. Extract policy details
    policy_analysis = extract_policy_details(policy_text)
    
    # 2. Analyze sentiment of comments
    sentiment_analysis = analyze_sentiment(comments)
    
    # 3. Cluster concerns from comments
    concern_analysis = cluster_concerns(comments)
    
    # 4. Detect gaps by comparing policy and concerns
    gap_analysis = detect_gaps(policy_analysis, concern_analysis)
    
    # 5. Generate recommendations based on gaps
    recommendations = generate_recommendations(policy_analysis, gap_analysis)
    
    # 6. Generate survey
    survey = generate_survey(policy_text)
    
    return {
        "policy_analysis": policy_analysis,
        "sentiment_analysis": sentiment_analysis,
        "concern_analysis": concern_analysis,
        "gap_analysis": gap_analysis,
        "recommendations": recommendations,
        "survey": survey
    }

def run_survey_generation(policy_text: str) -> dict:
    """Runs only the survey generation based on the policy."""
    if not policy_text or not policy_text.strip():
        raise ValueError("Policy text cannot be empty.")
        
    return generate_survey(policy_text)
