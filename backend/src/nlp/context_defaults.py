"""
Context-Aware Defaults
Applies smart defaults based on context
"""

class ContextDefaults:
    def __init__(self):
        self.defaults = {
            'show_transactions': {
                'metrics': ['count', 'avg_amount'],
                'dimensions': ['transaction_type']
            },
            'show_fraud': {
                'metrics': ['fraud_flag_rate', 'count'],
                'filters': {'fraud_flag': 1}
            },
            'show_failures': {
                'metrics': ['failure_rate', 'count'],
                'filters': {'transaction_status': 'FAILED'}
            },
            'compare': {
                'dimensions': ['transaction_type', 'device_type']
            },
            'analyze': {
                'dimensions': ['merchant_category', 'sender_age_group']
            }
        }
    
    def apply_defaults(self, parsed_query, original_query: str):
        """Apply smart defaults based on query intent"""
        query_lower = original_query.lower()
        
        # If no metrics specified, add defaults
        if not parsed_query.metrics or parsed_query.metrics == ['count']:
            for pattern, defaults in self.defaults.items():
                if pattern.replace('_', ' ') in query_lower:
                    if 'metrics' in defaults:
                        parsed_query.metrics = defaults['metrics']
                    if 'filters' in defaults:
                        parsed_query.filters.update(defaults['filters'])
                    if 'dimensions' in defaults and not parsed_query.dimensions:
                        parsed_query.dimensions = defaults['dimensions']
                    break
        
        return parsed_query
