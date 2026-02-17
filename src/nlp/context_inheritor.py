"""
Context Inheritance Logic
Merges previous context with current query
"""

from parser import ParsedQuery, QueryIntent
from conversation_state import ConversationState
from typing import Dict, List


class ContextInheritor:
    """Intelligently merge context from previous turns"""
    
    def __init__(self):
        print("✓ Context Inheritor initialized")
    
    def enhance_query(self, parsed: ParsedQuery, state: ConversationState) -> ParsedQuery:
        """
        Enhance current query with context from previous turns
        
        Args:
            parsed: Newly parsed query
            state: Current conversation state
        
        Returns:
            Enhanced ParsedQuery with inherited context
        """
        
        if not state.turns:
            # First turn, no context to inherit
            return parsed
        
        # Determine if this is a follow-up question
        is_followup = self._is_followup_question(parsed, state)
        
        if not is_followup:
            # Standalone question, don't inherit context
            return parsed
        
        # Inherit context
        enhanced = self._merge_with_context(parsed, state)
        
        return enhanced
    
    def _is_followup_question(self, parsed: ParsedQuery, state: ConversationState) -> bool:
        """
        Detect if this is a follow-up question
        
        Indicators of follow-up:
        - Short query (<5 words)
        - Contains anaphora ("it", "that", "them", "those")
        - Starts with "what about", "how about", "and", "also"
        - Has very few filters (adding to existing context)
        """
        
        query_lower = parsed.original_query.lower()
        word_count = len(parsed.original_query.split())
        
        # Explicit follow-up phrases
        followup_phrases = [
            'what about', 'how about', 'what if', 'also show',
            'and the', 'also', 'too', 'as well'
        ]
        
        if any(phrase in query_lower for phrase in followup_phrases):
            return True
        
        # Anaphora indicators
        anaphora = ['it', 'that', 'them', 'those', 'these', 'this']
        if any(word in query_lower.split() for word in anaphora):
            return True
        
        # Short queries with minimal context are likely follow-ups
        if word_count <= 5 and not parsed.filters:
            return True
        
        # Query only adds dimensions (grouping existing data)
        if parsed.dimensions and not parsed.filters and state.active_filters:
            return True
        
        return False
    
    def _merge_with_context(self, parsed: ParsedQuery, state: ConversationState) -> ParsedQuery:
        """Merge current query with active context"""
        
        # Start with current query
        enhanced_filters = parsed.filters.copy()
        enhanced_dimensions = parsed.dimensions.copy()
        enhanced_metrics = parsed.metrics.copy()
        
        # Inherit filters from context (if not overridden)
        for key, value in state.active_filters.items():
            if key not in enhanced_filters:
                enhanced_filters[key] = value
        
        # Inherit dimensions if current query doesn't specify
        if not enhanced_dimensions and state.last_dimensions:
            # Only inherit if current query doesn't change grouping
            if not self._changes_grouping(parsed):
                enhanced_dimensions = state.last_dimensions.copy()
        
        # Inherit metric if not specified
        if not enhanced_metrics and state.last_metric:
            enhanced_metrics = [state.last_metric]
        
        # Create enhanced query
        enhanced = ParsedQuery(
            intent=parsed.intent,
            metrics=enhanced_metrics,
            dimensions=enhanced_dimensions,
            filters=enhanced_filters,
            original_query=parsed.original_query,
            confidence=parsed.confidence * 0.95  # Slightly lower confidence for inherited context
        )
        
        return enhanced
    
    def _changes_grouping(self, parsed: ParsedQuery) -> bool:
        """Check if query explicitly changes grouping"""
        
        query_lower = parsed.original_query.lower()
        
        # Keywords that indicate dimension change
        grouping_keywords = ['break down', 'group by', 'by type', 'by age', 'by device', 'each']
        
        return any(keyword in query_lower for keyword in grouping_keywords)


# ============================================================================
# TESTING
# ============================================================================
if __name__ == "__main__":
    from parser import QueryParser
    from conversation_state import ConversationState
    
    print("\n" + "="*80)
    print("CONTEXT INHERITOR TEST")
    print("="*80)
    
    parser = QueryParser()
    inheritor = ContextInheritor()
    state = ConversationState(session_id="test-123")
    
    # Simulate conversation
    conversation = [
        ("Show me P2P transactions", "Initial query"),
        ("What about weekends?", "Follow-up: should inherit P2P filter"),
        ("Break down by age group", "Follow-up: should inherit P2P + weekend"),
        ("Compare failure rates by device", "New query: should NOT inherit"),
    ]
    
    for i, (query, note) in enumerate(conversation, 1):
        print(f"\n{'='*80}")
        print(f"Turn {i}: {query}")
        print(f"Note: {note}")
        print(f"{'='*80}")
        
        # Parse query
        parsed = parser.parse(query)
        print(f"\nParsed (before context):")
        print(f"  Filters: {parsed.filters}")
        print(f"  Dimensions: {parsed.dimensions}")
        
        # Enhance with context
        enhanced = inheritor.enhance_query(parsed, state)
        print(f"\nEnhanced (after context):")
        print(f"  Filters: {enhanced.filters}")
        print(f"  Dimensions: {enhanced.dimensions}")
        
        # Add to state
        state.add_turn(query, enhanced)
        
        # Show current context
        print(f"\nActive Context: {state.get_context_summary()}")
    
    print("\n" + "="*80)
    print("✓ CONTEXT INHERITOR TEST COMPLETE")
    print("="*80)