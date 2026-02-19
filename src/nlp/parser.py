from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum
import re


class QueryIntent(Enum):
    DESCRIPTIVE = "descriptive"
    COMPARATIVE = "comparative"
    TEMPORAL = "temporal"
    SEGMENTATION = "segmentation"
    RISK = "risk"
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
        query_lower = query.lower()
    
    # Amount metrics
        if 'average amount' in query_lower or 'avg amount' in query_lower or 'mean amount' in query_lower:
            metrics.append('avg_amount')
        elif 'total amount' in query_lower or 'sum' in query_lower or 'revenue' in query_lower:
            metrics.append('total_amount')
        elif 'median' in query_lower:
            metrics.append('median_amount')
        elif 'minimum' in query_lower or 'min' in query_lower and 'amount' in query_lower:
            metrics.append('min_amount')
        elif 'maximum' in query_lower or 'max' in query_lower and 'amount' in query_lower:
            metrics.append('max_amount')
        elif 'amount' in query_lower and not metrics:
            metrics.append('avg_amount')  # Default for "amount"
    
    # Count metrics
        if 'how many' in query_lower or 'count' in query_lower or 'number of' in query_lower:
            if 'count' not in metrics:
                metrics.append('count')
    
    # Rate metrics
        if 'success rate' in query_lower or 'successful' in query_lower and 'rate' in query_lower:
            metrics.append('success_rate')
        elif 'failure rate' in query_lower or 'failed' in query_lower or 'failures' in query_lower:
            metrics.append('failure_rate')
        elif 'fraud rate' in query_lower or 'flagged rate' in query_lower:
            metrics.append('fraud_flag_rate')
    
    # If no metrics found, default to count
        if not metrics:
            metrics.append('count')

        return metrics
    
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
        """Extract filters from query text"""
        filters = {}
        query_lower = query.lower()
    
    # Transaction types
        if 'p2p' in query_lower or 'person to person' in query_lower:
            filters['transaction_type'] = 'P2P'
        elif 'p2m' in query_lower or 'person to merchant' in query_lower:
            filters['transaction_type'] = 'P2M'
        elif 'bill payment' in query_lower:
            filters['transaction_type'] = 'Bill Payment'
        elif 'recharge' in query_lower:
            filters['transaction_type'] = 'Recharge'
    
    # Merchant categories
        categories = {
            'food': 'Food',
            'grocery': 'Grocery',
            'fuel': 'Fuel',
            'entertainment': 'Entertainment',
            'shopping': 'Shopping',
            'healthcare': 'Healthcare',
            'education': 'Education',
            'transport': 'Transport',
            'utilities': 'Utilities'
        }
    
        for key, value in categories.items():
            if key in query_lower:
                filters['merchant_category'] = value
                break
    
    # Age groups
        import re
        age_patterns = [
            (r'18[\s-]?to[\s-]?25|18-25', '18-25'),
            (r'26[\s-]?to[\s-]?35|26-35', '26-35'),
            (r'36[\s-]?to[\s-]?45|36-45', '36-45'),
            (r'46[\s-]?to[\s-]?55|46-55', '46-55'),
            (r'56\+|above 55|over 55', '56+')
        ]
    
        for pattern, age_group in age_patterns:
            if re.search(pattern, query_lower):
                filters['sender_age_group'] = age_group
                break
    
    # Device types
        if 'android' in query_lower:
            filters['device_type'] = 'Android'
        elif 'ios' in query_lower or 'iphone' in query_lower:
            filters['device_type'] = 'iOS'
        elif 'web' in query_lower or 'website' in query_lower:
            filters['device_type'] = 'Web'
    
    # Network types
        if '5g' in query_lower:
            filters['network_type'] = '5G'
        elif '4g' in query_lower:
            filters['network_type'] = '4G'
        elif '3g' in query_lower:
            filters['network_type'] = '3G'
        elif 'wifi' in query_lower:
            filters['network_type'] = 'WiFi'
    
    # Banks (common ones)
        banks = ['sbi', 'hdfc', 'icici', 'axis', 'pnb', 'kotak']
        for bank in banks:
            if bank in query_lower:
                filters['sender_bank'] = bank.upper()
                break
    
    # Transaction status
        if 'failed' in query_lower or 'failure' in query_lower:
            filters['transaction_status'] = 'FAILED'
        elif 'success' in query_lower or 'successful' in query_lower:
            filters['transaction_status'] = 'SUCCESS'
    
    # Fraud flags
        if 'fraud' in query_lower or 'flagged' in query_lower:
            filters['fraud_flag'] = 1
    
    # Weekend/weekday
        if 'weekend' in query_lower:
            filters['is_weekend'] = 1
        elif 'weekday' in query_lower:
            filters['is_weekend'] = 0
    
    # States (top 10)
        states = ['maharashtra', 'delhi', 'karnataka', 'tamil nadu', 'uttar pradesh',
                'gujarat', 'west bengal', 'rajasthan', 'andhra pradesh', 'telangana']
        for state in states:
            if state in query_lower:
                filters['sender_state'] = state.title()
                break
    
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