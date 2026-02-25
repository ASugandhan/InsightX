"""
Temporal Parser
Handles date/time expressions
"""

from datetime import datetime, timedelta
import re

class TemporalParser:
    def __init__(self, data_year: int = 2024):
        self.data_year = data_year
        self.patterns = {
            'last_month': lambda: self._last_month(),
            'last_week': lambda: self._last_week(),
            'yesterday': lambda: self._yesterday(),
            'today': lambda: self._today(),
            'this_month': lambda: self._this_month(),
            'this_week': lambda: self._this_week(),
            'weekend': lambda: {'is_weekend': 1},
            'weekday': lambda: {'is_weekend': 0}
        }
    
    def parse_temporal(self, query: str) -> dict:
        """Extract temporal filters from query"""
        query_lower = query.lower()
        filters = {}
        
        for pattern, func in self.patterns.items():
            if pattern.replace('_', ' ') in query_lower:
                filters.update(func())
                break
        
        return filters
    
    def _last_month(self):
        # For demo data, map to specific months
        # In production, calculate actual dates
        return {'month': 11}  # November as example
    
    def _last_week(self):
        return {'week': 48}  # Week 48 as example
    
    def _this_month(self):
        return {'month': 12}  # December
    
    def _this_week(self):
        return {'week': 52}  # Week 52
    
    def _yesterday(self):
        return {'day': 23}
    
    def _today(self):
        return {'day': 24}
