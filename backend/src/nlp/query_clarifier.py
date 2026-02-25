"""
Query Clarifier
Detects ambiguous queries and requests clarification
"""

class QueryClarifier:
    def __init__(self):
        self.ambiguous_patterns = {
            'transactions': ['What type?', 'Which metric?', 'Time period?'],
            'show me': ['What would you like to see?', 'Which dimension?'],
            'fraud': ['Fraud rate or fraud count?', 'Time period?'],
            'high': ['Define threshold (e.g., >₹5000)?'],
            'best': ['Best by which metric?']
        }
    
    def needs_clarification(self, query: str) -> bool:
        """Check if query needs clarification"""
        query_lower = query.lower().strip()
        
        # Too short
        if len(query.split()) <= 2:
            return True
        
        # Missing key information
        if any(pattern in query_lower for pattern in self.ambiguous_patterns.keys()):
            if not any(metric in query_lower for metric in ['average', 'total', 'count', 'rate']):
                return True
        
        return False
    
    def get_clarification_questions(self, query: str) -> list:
        """Generate clarification questions"""
        questions = []
        query_lower = query.lower()
        
        for pattern, qs in self.ambiguous_patterns.items():
            if pattern in query_lower:
                questions.extend(qs)
        
        return questions[:3]  # Max 3 questions
