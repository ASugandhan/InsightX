"""
Schema Validator - Prevents hallucinated columns and values
"""

class SchemaValidator:
    """Validates that LLM outputs match actual database schema"""
    
    VALID_METRICS = {
        'transaction_amount', 'transaction_count', 'count',
        'avg_amount', 'total_amount', 'success_rate', 'failure_rate'
    }
    
    VALID_DIMENSIONS = {
        'transaction_type', 'device_type', 'merchant_category',
        'sender_age_group', 'transaction_status', 'hour', 'day_of_week',
        'is_weekend', 'payment_mode'
    }
    
    VALID_FILTERS = VALID_DIMENSIONS.copy()
    
    VALID_VALUES = {
        'transaction_type': {'P2P', 'P2M'},
        'device_type': {'Android', 'iOS', 'Web'},
        'transaction_status': {'success', 'failure', 'pending'},
        'payment_mode': {'UPI', 'Card', 'Wallet', 'NetBanking'},
        'sender_age_group': {'18-25', '26-35', '36-45', '46-55', '56+'},
        'is_weekend': {0, 1, '0', '1', True, False}
    }
    
    def __init__(self):
        self.schema_errors = []
    
    def validate_parsed_query(self, parsed_query) -> dict:
        """Validate that parsed query doesn't contain hallucinated fields"""
        issues = []
        
        # Check metrics
        for metric in parsed_query.metrics:
            if metric not in self.VALID_METRICS:
                issues.append(f"Invalid metric '{metric}' - not in schema")
        
        # Check dimensions
        for dim in parsed_query.dimensions:
            if dim not in self.VALID_DIMENSIONS:
                issues.append(f"Invalid dimension '{dim}' - not in schema")
        
        # Check filters
        for key, value in parsed_query.filters.items():
            if key not in self.VALID_FILTERS:
                issues.append(f"Invalid filter '{key}' - not in schema")
            elif key in self.VALID_VALUES:
                if value not in self.VALID_VALUES[key]:
                    issues.append(f"Invalid value '{value}' for filter '{key}'")
        
        return {
            'is_valid': len(issues) == 0,
            'issues': issues,
            'confidence_penalty': -0.2 * len(issues)  # Reduce confidence for each issue
        }
