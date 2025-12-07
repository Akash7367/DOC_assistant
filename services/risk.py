import re

# very simple rule-based risky-terms detector
RISK_TERMS = {
    'indemnify': 0.7,
    'liability': 0.6,
    'exclusive jurisdiction': 0.8,
    'termination for convenience': 0.5,
    'confidentiality breach': 0.9,
    'automatic renewal': 0.6,
    'limit of liability': 0.8
}

def evaluate_risk(text: str) -> dict:
    """Returns a simple risk report with detected terms and an overall score (0-1)."""
    found = []
    score = 0.0
    for term, weight in RISK_TERMS.items():
        if re.search(re.escape(term), text, flags=re.I):
            found.append({'term': term, 'weight': weight})
            score = max(score, weight)
    return {'overall_score': score, 'found': found}
