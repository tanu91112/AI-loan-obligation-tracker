import re
from datetime import datetime, timedelta
from typing import Dict, Optional


def parse_deadline(text: str) -> Dict[str, Optional[str]]:
    """
    Parses deadline information from text and calculates expected dates.
    
    Args:
        text (str): Text containing deadline information
        
    Returns:
        Dict: Contains rule, calculated_date, and other relevant information
    """
    result = {
        "rule": "",
        "calculated_date": "",
        "frequency": "",
        "description": ""
    }
    
    # Look for deadline patterns
    deadline_patterns = [
        # Pattern for "X days/months after"
        r'(?i)(?:within|after|by|no later than)\s+(\d+)\s+(days?|months?|weeks?|years?)\s+(?:after|of|following)\s+(.*)',
        # Pattern for "X days/months of"
        r'(?i)(\d+)\s+(days?|months?|weeks?|years?)\s+(?:before|prior to)\s+(.*)',
        # Pattern for specific timeframes
        r'(?i)(?:monthly|quarterly|annually|yearly|semi-annually|bi-annually)',
        # Pattern for specific events
        r'(?i)(?:promptly|immediately|as soon as possible|without delay)',
        # Pattern for end of periods
        r'(?i)(?:end of|by end of)\s+(?:month|quarter|year|fiscal year|calendar year)',
    ]
    
    # Extract deadline rule
    for pattern in deadline_patterns[:3]:  # First three patterns that have date calculations
        match = re.search(pattern, text)
        if match:
            if len(match.groups()) >= 3:
                # Format: "within 30 days after month end"
                quantity = match.group(1)
                unit = match.group(2)
                reference = match.group(3)
                result["rule"] = f"within {quantity} {unit} after {reference}"
                
                # Calculate the expected date
                calculated_date = calculate_expected_date(quantity, unit, reference)
                if calculated_date:
                    result["calculated_date"] = calculated_date.strftime("%Y-%m-%d")
            
            elif len(match.groups()) >= 1:
                # For simple frequency patterns
                result["rule"] = match.group(0)
                result["frequency"] = match.group(0)
    
    # Handle immediate/prompt notifications
    immediate_patterns = [r'(?i)(?:promptly|immediately|as soon as possible|without delay)']
    for pattern in immediate_patterns:
        if re.search(pattern, text):
            result["rule"] = "immediate upon occurrence"
            result["calculated_date"] = "Upon Event"
            break
    
    # Handle end-of-period deadlines
    period_end_patterns = [
        r'(?i)(?:end of\s+)(month|quarter|year|fiscal year|calendar year)',
        r'(?i)(?:by end of\s+)(month|quarter|year|fiscal year|calendar year)'
    ]
    for pattern in period_end_patterns:
        match = re.search(pattern, text)
        if match:
            period = match.group(1)
            result["rule"] = f"by end of {period}"
            
            # Calculate approximate date based on period
            if "month" in period:
                result["calculated_date"] = "End of Month"
            elif "quarter" in period:
                result["calculated_date"] = "End of Quarter"
            elif "year" in period:
                result["calculated_date"] = "End of Year"
            break
    
    # If no specific rule was found, look for general timeframe words
    if not result["rule"]:
        general_patterns = [
            r'(?i)(?:monthly|quarterly|annually|yearly|semi-annually|bi-annually|event-based)',
            r'(?i)(?:within\s+\d+\s+days?)',
            r'(?i)(?:by\s+\w+\s+\d{1,2}(?:st|nd|rd|th)?,\s*\d{4})'  # Like "by March 15, 2024"
        ]
        
        for pattern in general_patterns:
            match = re.search(pattern, text)
            if match:
                result["rule"] = match.group(0)
                break
    
    # Set description if not already set
    if not result["description"] and result["rule"]:
        result["description"] = result["rule"]
    
    return result


def calculate_expected_date(quantity: str, unit: str, reference: str) -> Optional[datetime]:
    """
    Calculates an expected date based on quantity, unit, and reference point.
    
    Args:
        quantity (str): Number of units (e.g., "30")
        unit (str): Unit of time (e.g., "days", "months")
        reference (str): Reference point (e.g., "end of month", "quarter end")
        
    Returns:
        Optional[datetime]: Calculated date or None if calculation isn't possible
    """
    try:
        qty = int(quantity)
        today = datetime.today()
        
        # Handle different units
        if "day" in unit:
            return today + timedelta(days=qty)
        elif "week" in unit:
            return today + timedelta(weeks=qty)
        elif "month" in unit:
            # For months, we'll estimate (not exact due to varying month lengths)
            estimated_days = qty * 30
            return today + timedelta(days=estimated_days)
        elif "year" in unit:
            estimated_days = qty * 365
            return today + timedelta(days=estimated_days)
        
        # Handle reference points like "end of month", "end of quarter", etc.
        if "end of month" in reference.lower() or "month end" in reference.lower():
            # Calculate the last day of the current month
            import calendar
            last_day = calendar.monthrange(today.year, today.month)[1]
            month_end = today.replace(day=last_day)
            return month_end + timedelta(days=qty)
        
        elif "end of quarter" in reference.lower() or "quarter end" in reference.lower():
            # Calculate the end of the current quarter
            current_quarter = ((today.month - 1) // 3) + 1
            quarter_end_month = current_quarter * 3
            # Get the last day of that month
            import calendar
            last_day = calendar.monthrange(today.year, quarter_end_month)[1]
            quarter_end = today.replace(month=quarter_end_month, day=last_day)
            return quarter_end + timedelta(days=qty)
        
        elif "end of year" in reference.lower() or "year end" in reference.lower():
            # Calculate the end of the current year
            year_end = today.replace(month=12, day=31)
            return year_end + timedelta(days=qty)
        
        # If no special handling needed, just add the time period to today
        return today + timedelta(days=qty)
    
    except Exception:
        # If calculation fails, return None
        return None


def get_compliance_status(deadline_date: str) -> str:
    """
    Determines compliance status based on deadline date.
    
    Args:
        deadline_date (str): Expected deadline date in YYYY-MM-DD format
        
    Returns:
        str: Compliance status ("Compliant", "Due Soon", "Missed")
    """
    if not deadline_date or deadline_date == "Upon Event" or "End of" in deadline_date:
        # For ongoing/flexible deadlines, default to compliant
        return "Compliant"
    
    try:
        deadline = datetime.strptime(deadline_date, "%Y-%m-%d")
        today = datetime.today()
        
        # Calculate difference in days
        diff_days = (deadline - today).days
        
        if diff_days < 0:
            return "Missed"
        elif diff_days <= 7:  # Due within a week
            return "Due Soon"
        else:
            return "Compliant"
    
    except ValueError:
        # If date parsing fails, assume compliant
        return "Compliant"


if __name__ == "__main__":
    # Test the parser
    test_sentences = [
        "Monthly financial statements shall be provided within 30 days after the end of each month.",
        "Annual audited financial statements shall be delivered within 90 days after the fiscal year end.",
        "The Borrower shall notify the Lender promptly of any material adverse change.",
        "Quarterly compliance certificates shall be submitted within 45 days of quarter end."
    ]
    
    for sentence in test_sentences:
        result = parse_deadline(sentence)
        print(f"Sentence: {sentence}")
        print(f"Rule: {result['rule']}")
        print(f"Calculated Date: {result['calculated_date']}")
        print("---")