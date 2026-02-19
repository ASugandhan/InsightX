"""
Query Enhancer
Uses RAG context to enhance query parsing
"""

from typing import Dict, List, Tuple
from nlp.parser import ParsedQuery, QueryIntent
from rag.rag_retriever import RAGRetriever


class QueryEnhancer:
    """Enhance queries with RAG context"""
    
    def __init__(self, persist_directory: str = "../data/chroma_db"):
        """Initialize query enhancer"""
        
        self.retriever = RAGRetriever(persist_directory)
        print("✓ Query Enhancer initialized")
    
    def enhance_parsed_query(self, query: str, parsed: ParsedQuery) -> Tuple[ParsedQuery, str]:
        """
        Enhance a parsed query with RAG context
        
        Args:
            query: Original query text
            parsed: Initially parsed query
        
        Returns:
            (enhanced_parsed_query, enhancement_explanation)
        """
        
        # Retrieve context
        context = self.retriever.retrieve_context(query, n_schema=5, n_examples=3)
        
        # Apply enhancements
        enhanced = self._apply_enhancements(query, parsed, context)
        
        # Generate explanation
        explanation = self._generate_explanation(parsed, enhanced, context)
        
        return enhanced, explanation
    
    def _apply_enhancements(self, query: str, parsed: ParsedQuery, context: Dict) -> ParsedQuery:
        """Apply context-based enhancements"""
        
        query_lower = query.lower()
        
        # Start with original parsed query
        enhanced_filters = parsed.filters.copy()
        enhanced_metrics = parsed.metrics.copy()
        enhanced_dimensions = parsed.dimensions.copy()
        confidence_boost = 0.0
        
        # Enhancement 1: Resolve "high-value" threshold
        if any(word in query_lower for word in ['high', 'expensive', 'costly', 'large', 'big']):
            if 'amount' in query_lower or 'value' in query_lower or 'transaction' in query_lower:
                # Check if we found the threshold in context
                for ctx in context['schema_context']:
                    if '5000' in ctx or '5,000' in ctx:
                        # Add threshold filter if not already present
                        if 'amount_inr' not in enhanced_filters:
                            enhanced_filters['amount_inr'] = {'min': 5000}
                            confidence_boost += 0.15
                        break
        
        # Enhancement 2: Resolve "low-value" threshold
        if any(word in query_lower for word in ['low', 'cheap', 'small', 'micro']):
            if 'amount' in query_lower or 'value' in query_lower or 'transaction' in query_lower:
                for ctx in context['schema_context']:
                    if '500' in ctx or 'micro' in ctx.lower():
                        if 'amount_inr' not in enhanced_filters:
                            enhanced_filters['amount_inr'] = {'max': 500}
                            confidence_boost += 0.15
                        break
        
        # Enhancement 3: Resolve "peak hours"
        if 'peak' in query_lower or 'busy' in query_lower or 'busiest' in query_lower:
            if 'hour' in query_lower or 'time' in query_lower:
                if 'hour_of_day' not in enhanced_dimensions:
                    enhanced_dimensions.append('hour_of_day')
                    confidence_boost += 0.10
                if 'count' not in enhanced_metrics:
                    enhanced_metrics.append('count')
        
        # Enhancement 4: Resolve "popular" queries
        if 'popular' in query_lower or 'most common' in query_lower:
            if 'category' in query_lower or 'merchant' in query_lower:
                if 'transaction_type' not in enhanced_filters:
                    enhanced_filters['transaction_type'] = 'P2M'
                if 'merchant_category' not in enhanced_dimensions:
                    enhanced_dimensions.append('merchant_category')
                if 'count' not in enhanced_metrics:
                    enhanced_metrics.append('count')
                confidence_boost += 0.15
        
        # Enhancement 5: Resolve "young users"
        if any(word in query_lower for word in ['young', 'youth', 'teenage']):
            if 'sender_age_group' not in enhanced_filters:
                enhanced_filters['sender_age_group'] = '18-25'
                confidence_boost += 0.10
        
        # Enhancement 6: Resolve "mobile users"
        if 'mobile' in query_lower and 'device' not in query_lower:
            if 'device_type' not in enhanced_filters:
                enhanced_filters['device_type'] = ['Android', 'iOS']
                confidence_boost += 0.10
        
        # Enhancement 7: Add implied metrics
        if 'problem' in query_lower or 'issue' in query_lower or 'fail' in query_lower:
            if not enhanced_metrics or 'count' in enhanced_metrics:
                if 'failure_rate' not in enhanced_metrics:
                    enhanced_metrics.append('failure_rate')
                if 'transaction_status' not in enhanced_filters:
                    enhanced_filters['transaction_status'] = 'FAILED'
                confidence_boost += 0.10
        
        # Enhancement 8: Learn from similar examples
        for example in context['example_queries']:
            # If very similar query, boost confidence
            if self._query_similarity(query, example['query']) > 0.8:
                confidence_boost += 0.15
                break
        
        # Create enhanced query
        enhanced_confidence = min(parsed.confidence + confidence_boost, 1.0)
        
        enhanced = ParsedQuery(
            intent=parsed.intent,
            metrics=enhanced_metrics if enhanced_metrics else parsed.metrics,
            dimensions=enhanced_dimensions if enhanced_dimensions else parsed.dimensions,
            filters=enhanced_filters if enhanced_filters else parsed.filters,
            original_query=query,
            confidence=enhanced_confidence
        )
        
        return enhanced
    
    def _generate_explanation(self, original: ParsedQuery, enhanced: ParsedQuery, context: Dict) -> str:
        """Generate explanation of enhancements"""
        
        changes = []
        
        # Check for added filters
        new_filters = set(enhanced.filters.keys()) - set(original.filters.keys())
        if new_filters:
            for f in new_filters:
                changes.append(f"Added filter: {f}={enhanced.filters[f]}")
        
        # Check for added metrics
        new_metrics = set(enhanced.metrics) - set(original.metrics)
        if new_metrics:
            changes.append(f"Added metrics: {', '.join(new_metrics)}")
        
        # Check for added dimensions
        new_dimensions = set(enhanced.dimensions) - set(original.dimensions)
        if new_dimensions:
            changes.append(f"Added dimensions: {', '.join(new_dimensions)}")
        
        # Check for confidence boost
        if enhanced.confidence > original.confidence:
            boost = (enhanced.confidence - original.confidence) * 100
            changes.append(f"Confidence boosted by {boost:.0f}%")
        
        if not changes:
            return "No enhancements applied"
        
        return " | ".join(changes)
    
    def _query_similarity(self, query1: str, query2: str) -> float:
        """Calculate simple query similarity"""
        
        # Simple word overlap similarity
        words1 = set(query1.lower().split())
        words2 = set(query2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        overlap = len(words1 & words2)
        total = len(words1 | words2)
        
        return overlap / total if total > 0 else 0.0


# ============================================================================
# TESTING
# ============================================================================
if __name__ == "__main__":
    import sys
    sys.path.append('..')
    
    from nlp.parser import QueryParser
    
    print("\n" + "="*80)
    print("QUERY ENHANCER TEST")
    print("="*80)
    
    parser = QueryParser()
    enhancer = QueryEnhancer()
    
    test_queries = [
        "Show me high-value transactions",
        "What are the peak hours?",
        "Show me transactions from young users",
        "Which categories are most popular?",
        "Show me mobile user transactions",
    ]
    
    print("\n" + "-"*80)
    print("ENHANCEMENT TESTS")
    print("-"*80)
    
    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"Query: {query}")
        print(f"{'='*80}")
        
        # Parse without RAG
        original = parser.parse(query)
        print(f"\n📊 Original Parse:")
        print(f"   Confidence: {original.confidence:.2f}")
        print(f"   Metrics: {original.metrics}")
        print(f"   Dimensions: {original.dimensions}")
        print(f"   Filters: {original.filters}")
        
        # Enhance with RAG
        enhanced, explanation = enhancer.enhance_parsed_query(query, original)
        print(f"\n✨ Enhanced Parse:")
        print(f"   Confidence: {enhanced.confidence:.2f} {'↑' if enhanced.confidence > original.confidence else ''}")
        print(f"   Metrics: {enhanced.metrics}")
        print(f"   Dimensions: {enhanced.dimensions}")
        print(f"   Filters: {enhanced.filters}")
        
        if explanation != "No enhancements applied":
            print(f"\n💡 Enhancements: {explanation}")
    
    print("\n" + "="*80)
    print("✓ QUERY ENHANCER TEST COMPLETE")
    print("="*80)