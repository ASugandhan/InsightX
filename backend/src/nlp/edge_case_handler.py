"""
Edge Case Handler
Handles special cases and ambiguous queries
"""

from nlp.parser import ParsedQuery, QueryIntent


class EdgeCaseHandler:
    """Handle edge cases in conversation flow"""
    
    def __init__(self):
        print("✓ Edge Case Handler initialized")
    
    def handle_ambiguous_reference(self, query: str, parsed: ParsedQuery) -> tuple[ParsedQuery, str]:
        """
        Handle cases where reference is ambiguous
        
        Returns: (parsed_query, clarification_message)
        """
        
        clarification = None
        
        # Case 1: Multiple possible interpretations
        if self._has_multiple_interpretations(query):
            clarification = self._generate_clarification(query, parsed)
        
        # Case 2: Conflicting filters
        if self._has_conflicting_filters(parsed):
            clarification = "This query has conflicting filters. Please clarify."
        
        # Case 3: Too vague
        if self._is_too_vague(query, parsed):
            clarification = "Could you be more specific? Try adding more details."
        
        return parsed, clarification
    
    def _has_multiple_interpretations(self, query: str) -> bool:
        """Check if query could mean multiple things"""
        
        ambiguous_words = ['average', 'rate', 'amount', 'transactions']
        query_lower = query.lower()
        
        # Very short queries with common words are ambiguous
        word_count = len(query.split())
        if word_count <= 3:
            return any(word in query_lower for word in ambiguous_words)
        
        return False
    
    def _has_conflicting_filters(self, parsed: ParsedQuery) -> bool:
        """Check for conflicting filters"""
        
        filters = parsed.filters
        
        # Can't have both SUCCESS and FAILED
        if 'transaction_status' in filters:
            status = filters['transaction_status']
            if isinstance(status, list) and 'SUCCESS' in status and 'FAILED' in status:
                return True
        
        return False
    
    def _is_too_vague(self, query: str, parsed: ParsedQuery) -> bool:
        """Check if query is too vague"""
        
        # Very short queries with no filters/dimensions
        if len(query.split()) <= 2:
            if not parsed.filters and not parsed.dimensions:
                return True
        
        return False
    
    def _generate_clarification(self, query: str, parsed: ParsedQuery) -> str:
        """Generate clarification question"""
        
        if 'average' in query.lower():
            return "Did you mean average transaction amount, or average number of transactions?"
        
        if 'rate' in query.lower():
            return "Did you mean success rate, failure rate, or fraud flag rate?"
        
        return "Could you please rephrase your question with more details?"