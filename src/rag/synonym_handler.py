"""
Synonym Handler
Maps common synonyms to database terms
"""

class SynonymHandler:
    """Handle query synonyms and aliases"""
    
    def __init__(self):
        self.synonyms = self._build_synonym_map()
        print("✓ Synonym Handler initialized")
    
    def _build_synonym_map(self) -> dict:
        """Build synonym mapping"""
        
        return {
            # Transaction types
            'person to person': 'P2P',
            'peer to peer': 'P2P',
            'send money': 'P2P',
            'person to merchant': 'P2M',
            'payment': 'P2M',
            'purchase': 'P2M',
            'buy': 'P2M',
            
            # Amounts
            'expensive': 'high-value',
            'costly': 'high-value',
            'large': 'high-value',
            'big': 'high-value',
            'cheap': 'low-value',
            'small': 'low-value',
            'tiny': 'low-value',
            
            # Time
            'busy': 'peak',
            'busiest': 'peak',
            'rush hour': 'peak',
            'popular time': 'peak',
            
            # Demographics
            'youth': 'young',
            'teenage': 'young',
            'kids': 'young',
            'elderly': 'old',
            'seniors': 'old',
            
            # Devices
            'phone': 'mobile',
            'smartphone': 'mobile',
            'iPhone': 'iOS',
            'iPad': 'iOS',
            
            # Status
            'unsuccessful': 'failed',
            'didn\'t work': 'failed',
            'broken': 'failed',
            'successful': 'success',
            'worked': 'success',
            
            # Categories
            'restaurants': 'food',
            'dining': 'food',
            'supermarket': 'grocery',
            'gas': 'fuel',
            'petrol': 'fuel',
            'movies': 'entertainment',
            'games': 'entertainment',
        }
    
    def normalize_query(self, query: str) -> str:
        """Replace synonyms with standard terms"""
        
        normalized = query
        
        for synonym, standard in self.synonyms.items():
            # Case-insensitive replacement
            import re
            pattern = r'\b' + re.escape(synonym) + r'\b'
            normalized = re.sub(pattern, standard, normalized, flags=re.IGNORECASE)
        
        return normalized