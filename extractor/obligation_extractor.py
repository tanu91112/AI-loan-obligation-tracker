import re
from datetime import datetime
from typing import List, Dict, Tuple
from .deadline_parser import parse_deadline


class ObligationExtractor:
    """
    Extracts borrower obligations from loan agreement text using rule-based NLP.
    
    The extraction logic uses keyword-based and pattern-based matching to identify:
    - Obligation type (Financial Covenant / Reporting / Notification)
    - Obligation description
    - Frequency (Monthly / Quarterly / Annual / Event-based)
    - Deadline rule (e.g. "within 45 days of quarter end")
    - Responsible party (Borrower)
    - Risk level (Low / Medium / High)
    """
    
    def __init__(self):
        # Define patterns for different obligation types
        self.financial_covenant_patterns = [
            r'(?i)(?:maintain|require|covenant|agreement).*?(?:debt service coverage|interest coverage|leverage ratio|current ratio|quick ratio|working capital|debt to equity|total debt)',
            r'(?i)(?:financial covenant|financial ratio|ratio covenant).*?',
            r'(?i)(?:minimum|maximum).*?(?:balance sheet|equity|assets|liabilities|revenue|net worth|cash flow)'
        ]
        
        self.reporting_patterns = [
            r'(?i)(?:provide|submit|deliver|furnish|send).*?(?:report|statement|financial|quarterly|monthly|annual|yearly|audit)',
            r'(?i)(?:monthly|quarterly|annual).*?(?:report|statement|financial)',
            r'(?i)(?:financial statements?|income statement|balance sheet|cash flow statement|tax returns?)'
        ]
        
        self.notification_patterns = [
            r'(?i)(?:notify|inform|advise|tell|report).*?(?:change|event|default|breach|material|condition)',
            r'(?i)(?:promptly notify|immediately inform|without delay).*?(?:lender|agent|bank)',
            r'(?i)(?:notice of|notification of|inform of).*?(?:default|event|change|condition)'
        ]
        
        # Define frequency indicators
        self.frequency_indicators = {
            'Monthly': [r'(?i)\bmonth\b', r'(?i)\bmonthly\b', r'(?i)eom\b', r'(?i)end of month'],
            'Quarterly': [r'(?i)\bquarter\b', r'(?i)\bquarterly\b', r'(?i)q\d', r'(?i)end of quarter'],
            'Annual': [r'(?i)\byear\b', r'(?i)\bannual\b', r'(?i)\byearly\b', r'(?i)end of year'],
            'Event-based': [r'(?i)upon', r'(?i)when', r'(?i)if', r'(?i)as soon as', r'(?i)within.*?(?:days|hours|weeks)']
        }
        
        # Define risk indicators
        self.high_risk_keywords = [
            r'(?i)default', r'(?i)acceleration', r'(?i)foreclosure', r'(?i)penalty', 
            r'(?i)interest rate increase', r'(?i)event of default', r'(?i)material adverse',
            r'(?i)cross-default', r'(?i)cross-acceleration', r'(?i)forfeit', r'(?i)terminate'
        ]
        
        self.medium_risk_keywords = [
            r'(?i)fee', r'(?i)charge', r'(?i)cost', r'(?i)expense', r'(?i)compliance',
            r'(?i)remedy', r'(?i)cure period', r'(?i)waiver', r'(?i)consent'
        ]

    def extract_obligations(self, text: str) -> List[Dict]:
        """
        Extracts obligations from loan agreement text.
        
        Args:
            text (str): Loan agreement text
            
        Returns:
            List[Dict]: List of extracted obligations with structured data
        """
        obligations = []
        
        # Split text into sentences/paragraphs for processing
        sentences = self._split_into_sentences(text)
        
        for sentence in sentences:
            obligation = self._extract_single_obligation(sentence.strip())
            if obligation:
                obligations.append(obligation)
        
        # Deduplicate similar obligations
        obligations = self._deduplicate_obligations(obligations)
        
        return obligations

    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Splits text into sentences for processing.
        """
        # Split on periods, question marks, exclamation marks, and common sentence endings
        sentences = re.split(r'[.!?]+|;\s+|\n+', text)
        # Filter out empty sentences and very short ones
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        return sentences

    def _extract_single_obligation(self, sentence: str) -> Dict:
        """
        Extracts a single obligation from a sentence.
        
        Args:
            sentence (str): Sentence to analyze
            
        Returns:
            Dict: Obligation data if found, None otherwise
        """
        # Determine obligation type
        obligation_type = self._classify_obligation_type(sentence)
        if not obligation_type:
            return None
        
        # Extract obligation description
        description = self._extract_description(sentence, obligation_type)
        
        # Determine frequency
        frequency = self._determine_frequency(sentence)
        
        # Extract deadline information
        deadline_info = parse_deadline(sentence)
        
        # Determine risk level
        risk_level = self._calculate_risk_level(sentence)
        
        # Set responsible party
        responsible_party = "Borrower"
        
        # Determine compliance status (initially "Compliant" for new entries)
        compliance_status = "Compliant"
        
        return {
            "id": hash(sentence) % 1000000,  # Simple ID generation
            "type": obligation_type,
            "description": description,
            "frequency": frequency,
            "deadline_rule": deadline_info.get("rule", ""),
            "responsible_party": responsible_party,
            "risk_level": risk_level,
            "compliance_status": compliance_status,
            "next_deadline": deadline_info.get("calculated_date", "")
        }

    def _classify_obligation_type(self, sentence: str) -> str:
        """
        Classifies the type of obligation based on patterns.
        
        Args:
            sentence (str): Sentence to analyze
            
        Returns:
            str: Obligation type (Financial Covenant, Reporting, or Notification)
        """
        # Check for financial covenants
        for pattern in self.financial_covenant_patterns:
            if re.search(pattern, sentence):
                return "Financial Covenant"
        
        # Check for reporting obligations
        for pattern in self.reporting_patterns:
            if re.search(pattern, sentence):
                return "Reporting"
        
        # Check for notification obligations
        for pattern in self.notification_patterns:
            if re.search(pattern, sentence):
                return "Notification"
        
        return None

    def _extract_description(self, sentence: str, obligation_type: str) -> str:
        """
        Extracts the description of the obligation.
        
        Args:
            sentence (str): Sentence containing the obligation
            obligation_type (str): Type of obligation
            
        Returns:
            str: Description of the obligation
        """
        # Clean up the sentence to extract the core obligation
        # Remove common legal phrases and keep the core meaning
        clean_sentence = re.sub(r'(?i)\b(?:the|a|an|and|or|but|in|on|at|to|for|of|with|by)\b', '', sentence)
        
        # Remove some legal boilerplate
        clean_sentence = re.sub(r'(?i)\b(?:borrower shall|borrower will|it is agreed that|pursuant to|under this agreement)\b', '', clean_sentence)
        
        # Return a cleaned-up version of the sentence focusing on the obligation
        return sentence.strip()

    def _determine_frequency(self, sentence: str) -> str:
        """
        Determines the frequency of the obligation.
        
        Args:
            sentence (str): Sentence containing the obligation
            
        Returns:
            str: Frequency (Monthly, Quarterly, Annual, or Event-based)
        """
        # Check for each frequency type
        for freq, patterns in self.frequency_indicators.items():
            for pattern in patterns:
                if re.search(pattern, sentence):
                    return freq
        
        # Default to event-based if no specific frequency is found
        return "Event-based"

    def _calculate_risk_level(self, sentence: str) -> str:
        """
        Calculates the risk level based on keywords in the sentence.
        
        Args:
            sentence (str): Sentence to analyze
            
        Returns:
            str: Risk level (High, Medium, or Low)
        """
        # Count high risk keywords
        high_risk_count = sum(1 for pattern in self.high_risk_keywords if re.search(pattern, sentence))
        
        # Count medium risk keywords
        medium_risk_count = sum(1 for pattern in self.medium_risk_keywords if re.search(pattern, sentence))
        
        if high_risk_count > 0:
            return "High"
        elif medium_risk_count > 0:
            return "Medium"
        else:
            return "Low"

    def _deduplicate_obligations(self, obligations: List[Dict]) -> List[Dict]:
        """
        Removes duplicate obligations based on similarity.
        
        Args:
            obligations (List[Dict]): List of obligations to deduplicate
            
        Returns:
            List[Dict]: Deduplicated list of obligations
        """
        seen_descriptions = set()
        unique_obligations = []
        
        for obligation in obligations:
            # Use a normalized version of the description for comparison
            norm_desc = re.sub(r'\W+', '', obligation['description'].lower())
            if norm_desc not in seen_descriptions:
                seen_descriptions.add(norm_desc)
                unique_obligations.append(obligation)
        
        return unique_obligations


def extract_obligations_from_text(text: str) -> List[Dict]:
    """
    Convenience function to extract obligations from text.
    
    Args:
        text (str): Loan agreement text
        
    Returns:
        List[Dict]: List of extracted obligations
    """
    extractor = ObligationExtractor()
    return extractor.extract_obligations(text)


if __name__ == "__main__":
    # Test the extractor with sample text
    sample_text = """
    The Borrower shall maintain a debt service coverage ratio of at least 1.25 to 1.0.
    Monthly financial statements shall be provided within 30 days after the end of each month.
    The Borrower shall notify the Lender promptly of any material adverse change in its business.
    Annual audited financial statements shall be delivered within 90 days after the fiscal year end.
    """
    
    extractor = ObligationExtractor()
    obligations = extractor.extract_obligations(sample_text)
    
    print(f"Found {len(obligations)} obligations:")
    for i, obligation in enumerate(obligations, 1):
        print(f"\n{i}. Type: {obligation['type']}")
        print(f"   Description: {obligation['description']}")
        print(f"   Frequency: {obligation['frequency']}")
        print(f"   Risk Level: {obligation['risk_level']}")