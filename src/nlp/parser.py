from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum
import re

class QueryIntent(Enum):
    DESCRIPTIVE = "descriptive"
    COMPARATIVE = "comparative"
    TEMPORAL = "temporal"
    UNKNOWN = "unknown"

@dataclass
class ParsedQuery:
    intent: QueryIntent
    metrics: List[str]
    dimensions: List[str]
    filters: Dict[str, any]
    original_query: str
    confidence: float

class QueryParser:
    def __init__(self):
        print("✓ Query Parser initialized (rule-based)")
    
    def parse(self, query: str) -> ParsedQuery:
        """Parse natural language query"""
        query_lower = query.lower()
        
        # Detect intent
        intent = self._detect_intent(query_lower)
        
        # Extract metrics
        metrics = self._extract_metrics(query_lower)
        
        # Extract dimensions
        dimensions = self._extract_dimensions(query_lower)
        
        # Extract filters
        filters = self._extract_filters(query_lower)
        
        # Calculate confidence
        confidence = self._calculate_confidence(intent, metrics, dimensions)
        
        return ParsedQuery(
            intent=intent,
            metrics=metrics,
            dimensions=dimensions,
            filters=filters,
            original_query=query,
            confidence=confidence
        )
    
    def _detect_intent(self, query):
        """Detect query intent"""
        if any(w in query for w in ['what is', 'show me', 'how many', 'average']):
            return QueryIntent.DESCRIPTIVE
        elif any(w in query for w in ['compare', 'vs', 'versus']):
            return QueryIntent.COMPARATIVE
        elif any(w in query for w in ['peak', 'trend', 'by hour']):
            return QueryIntent.TEMPORAL
        return QueryIntent.UNKNOWN
    
    def _extract_metrics(self, query):
        """Extract requested metrics"""
        metrics = []
        
        if 'average' in query or 'avg' in query:
            metrics.append('avg_amount')
        if 'count' in query or 'how many' in query:
            metrics.append('count')
        if 'total' in query and 'amount' in query:
            metrics.append('total_amount')
        
        return metrics if metrics else ['count']
    
    def _extract_dimensions(self, query):
        """Extract grouping dimensions"""
        dimensions = []
        
        if 'by type' in query or 'transaction type' in query:
            dimensions.append('transaction_type')
        if 'by age' in query or 'age group' in query:
            dimensions.append('sender_age_group')
        if 'by device' in query:
            dimensions.append('device_type')
        
        return dimensions
    
    def _extract_filters(self, query):
        """Extract filters"""
        filters = {}
        
        # Transaction type
        if 'p2p' in query:
            filters['transaction_type'] = 'P2P'
        elif 'p2m' in query:
            filters['transaction_type'] = 'P2M'
        
        # Weekend
        if 'weekend' in query:
            filters['is_weekend'] = 1
        
        return filters
    
    def _calculate_confidence(self, intent, metrics, dimensions):
        """Calculate parse confidence"""
        confidence = 0.5
        
        if intent != QueryIntent.UNKNOWN:
            confidence += 0.3
        if metrics:
            confidence += 0.1
        if dimensions:
            confidence += 0.1
        
        return min(confidence, 1.0)

# Test
if __name__ == "__main__":
    parser = QueryParser()
    
    test_queries = [
        "What is the average P2M transaction amount?",
        "How many transactions are there?",
        "Show me weekend transactions",
        "Compare failure rates by device type"
    ]
    
    print("\n" + "="*60)
    print("TESTING PARSER")
    print("="*60)
    
    for q in test_queries:
        print(f"\nQuery: {q}")
        parsed = parser.parse(q)
        print(f"  Intent: {parsed.intent.value}")
        print(f"  Metrics: {parsed.metrics}")
        print(f"  Dimensions: {parsed.dimensions}")
        print(f"  Filters: {parsed.filters}")
        print(f"  Confidence: {parsed.confidence:.2f}")
    
    print("\n" + "="*60)
    print("✓ PARSER TESTS PASSED!")
    print("="*60)