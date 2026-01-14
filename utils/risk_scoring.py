"""
Risk scoring utilities for loan obligations.

This module provides functions to calculate and update risk scores for loan obligations
based on various factors like type, deadline proximity, and critical keywords.
"""


def calculate_risk_score(obligation: dict) -> int:
    """
    Calculates a risk score for a given obligation.
    
    Args:
        obligation (dict): The obligation dictionary containing obligation details
        
    Returns:
        int: Risk score (0-100) where higher values indicate higher risk
    """
    base_score = 0
    
    # Base risk by obligation type
    type_multipliers = {
        "Financial Covenant": 1.0,  # Highest risk - affects loan terms directly
        "Reporting": 0.6,           # Medium risk - compliance requirement
        "Notification": 0.4         # Lower risk - informational
    }
    
    base_score = type_multipliers.get(obligation.get('type', ''), 0.5) * 50
    
    # Risk level multiplier (from obligation extractor)
    risk_level_multipliers = {
        "High": 1.5,
        "Medium": 1.0,
        "Low": 0.5
    }
    
    risk_multiplier = risk_level_multipliers.get(obligation.get('risk_level', 'Medium'), 1.0)
    base_score *= risk_multiplier
    
    # Deadline urgency factor
    deadline_factor = calculate_deadline_risk(obligation.get('compliance_status', ''))
    base_score += deadline_factor
    
    # Ensure score stays within bounds
    risk_score = min(100, max(0, int(base_score)))
    
    return risk_score


def calculate_deadline_risk(compliance_status: str) -> int:
    """
    Calculates additional risk based on compliance status.
    
    Args:
        compliance_status (str): Current compliance status
        
    Returns:
        int: Additional risk points based on deadline status
    """
    if compliance_status == "Missed":
        return 30  # Significant risk for missed obligations
    elif compliance_status == "Due Soon":
        return 15  # Moderate risk for upcoming deadlines
    elif compliance_status == "Compliant":
        return 0   # No additional risk for compliant obligations
    else:
        return 5   # Default small risk for unknown status


def categorize_risk_level(score: int) -> str:
    """
    Categorizes risk score into human-readable risk level.
    
    Args:
        score (int): Risk score (0-100)
        
    Returns:
        str: Risk level category (Low, Medium, High)
    """
    if score < 30:
        return "Low"
    elif score < 70:
        return "Medium"
    else:
        return "High"


def update_obligation_risks(obligations: list) -> list:
    """
    Updates risk scores for a list of obligations.
    
    Args:
        obligations (list): List of obligation dictionaries
        
    Returns:
        list: Updated list of obligations with risk scores
    """
    for obligation in obligations:
        risk_score = calculate_risk_score(obligation)
        obligation['risk_score'] = risk_score
        obligation['risk_category'] = categorize_risk_level(risk_score)
    
    return obligations


def get_high_risk_obligations(obligations: list) -> list:
    """
    Filters and returns high-risk obligations.
    
    Args:
        obligations (list): List of obligation dictionaries
        
    Returns:
        list: List of high-risk obligations
    """
    return [ob for ob in obligations if categorize_risk_level(calculate_risk_score(ob)) == "High"]


def get_upcoming_deadlines(obligations: list, days_ahead: int = 14) -> list:
    """
    Gets obligations with deadlines approaching within specified days.
    
    Args:
        obligations (list): List of obligation dictionaries
        days_ahead (int): Number of days to look ahead
        
    Returns:
        list: List of obligations with upcoming deadlines
    """
    upcoming = []
    
    for obligation in obligations:
        status = obligation.get('compliance_status', '')
        if status == "Due Soon":
            upcoming.append(obligation)
    
    return upcoming


if __name__ == "__main__":
    # Test the risk scoring functions
    test_obligation = {
        "type": "Financial Covenant",
        "risk_level": "High",
        "compliance_status": "Due Soon"
    }
    
    score = calculate_risk_score(test_obligation)
    category = categorize_risk_level(score)
    
    print(f"Test obligation risk score: {score}")
    print(f"Risk category: {category}")
    
    # Test with a list of obligations
    test_obligations = [
        {"type": "Financial Covenant", "risk_level": "High", "compliance_status": "Missed"},
        {"type": "Reporting", "risk_level": "Medium", "compliance_status": "Due Soon"},
        {"type": "Notification", "risk_level": "Low", "compliance_status": "Compliant"}
    ]
    
    updated_obligations = update_obligation_risks(test_obligations)
    
    print("\nUpdated obligations with risk scores:")
    for i, ob in enumerate(updated_obligations):
        print(f"{i+1}. Type: {ob['type']}, Risk Score: {ob['risk_score']}, Category: {ob['risk_category']}")