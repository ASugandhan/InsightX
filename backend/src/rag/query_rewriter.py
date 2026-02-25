"""
Query Rewriter
Rewrites ambiguous queries into clearer ones
"""

class QueryRewriter:
    def __init__(self):
        self.rewrites = {
            'show transactions': 'What is the transaction count by type?',
            'show me fraud': 'What is the fraud flag rate?',
            'best performing': 'Which has the highest success rate?',
            'worst performing': 'Which has the highest failure rate?',
            'most popular': 'Which has the highest transaction count?',
            'analyze payments': 'Show transaction distribution by type and category',
            'compare devices': 'Compare success rates by device type',
            'weekend analysis': 'Compare weekend vs weekday transaction patterns'
        }
    
    def rewrite(self, query: str) -> str:
        """Rewrite query for better understanding"""
        query_lower = query.lower().strip()
        
        for pattern, rewrite in self.rewrites.items():
            if pattern in query_lower:
                return rewrite
        
        return query  # Return original if no rewrite
