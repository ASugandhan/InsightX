"""
SQL Generator - Converts ParsedQuery objects to executable SQL
"""

import sys
sys.path.append('..')

from nlp.parser import ParsedQuery, QueryIntent
from typing import List, Dict

class SQLGenerator:
    """Generate SQL queries from parsed natural language"""
    
    def __init__(self):
        self.table = "transactions"
        print("✓ SQL Generator initialized")
    
    def generate(self, parsed: ParsedQuery) -> str:
        """
        Main method: Convert ParsedQuery to SQL
        
        Args:
            parsed: ParsedQuery object with intent, metrics, dimensions, filters
            
        Returns:
            Valid SQL query string
        """
        
        # Build SQL parts
        select_clause = self._build_select(parsed)
        from_clause = f"FROM {self.table}"
        where_clause = self._build_where(parsed.filters)
        group_by_clause = self._build_group_by(parsed.dimensions)
        having_clause = self._build_having(parsed)
        order_by_clause = self._build_order_by(parsed)
        limit_clause = self._build_limit(parsed)
        
        # Assemble SQL
        sql_parts = [select_clause, from_clause]
        
        if where_clause:
            sql_parts.append(where_clause)
        
        if group_by_clause:
            sql_parts.append(group_by_clause)
        
        if having_clause:
            sql_parts.append(having_clause)
        
        if order_by_clause:
            sql_parts.append(order_by_clause)
        
        if limit_clause:
            sql_parts.append(limit_clause)
        
        sql = " ".join(sql_parts)
        
        return sql
    
    def _build_select(self, parsed: ParsedQuery) -> str:
        """Build SELECT clause with dimensions and metrics"""
        
        select_items = []
        
        # Add dimensions (for GROUP BY)
        for dim in parsed.dimensions:
            select_items.append(dim)
        
        # Add metrics with appropriate aggregations
        for metric in parsed.metrics:
            if metric == 'avg_amount':
                select_items.append("ROUND(AVG(amount_inr), 2) as avg_amount")
            
            elif metric == 'total_amount':
                select_items.append("ROUND(SUM(amount_inr), 2) as total_amount")
            
            elif metric == 'median_amount':
                select_items.append("ROUND(MEDIAN(amount_inr), 2) as median_amount")
            
            elif metric == 'count':
                select_items.append("COUNT(*) as count")
            
            elif metric == 'success_rate':
                select_items.append("""
                    ROUND(SUM(CASE WHEN transaction_status = 'SUCCESS' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as success_rate
                """.strip())
            
            elif metric == 'failure_rate':
                select_items.append("""
                    ROUND(SUM(CASE WHEN transaction_status = 'FAILED' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as failure_rate
                """.strip())
            
            elif metric == 'fraud_flag_rate':
                select_items.append("""
                    ROUND(SUM(fraud_flag) * 100.0 / COUNT(*), 2) as fraud_flag_rate
                """.strip())
            
            elif metric == 'min_amount':
                select_items.append("ROUND(MIN(amount_inr), 2) as min_amount")
            
            elif metric == 'max_amount':
                select_items.append("ROUND(MAX(amount_inr), 2) as max_amount")
        
        # If no metrics specified, default to count
        if not any(item.startswith('COUNT') or item.startswith('ROUND') for item in select_items):
            select_items.append("COUNT(*) as count")
        
        return "SELECT " + ", ".join(select_items)
    
    def _build_where(self, filters: Dict) -> str:
        """Build WHERE clause from filters"""
        
        if not filters:
            return ""
        
        conditions = []
        
        for col, val in filters.items():
            if isinstance(val, str):
                # String values need quotes
                conditions.append(f"{col} = '{val}'")
            elif isinstance(val, list):
                # Multiple values - use IN
                if all(isinstance(v, str) for v in val):
                    values = ", ".join([f"'{v}'" for v in val])
                else:
                    values = ", ".join([str(v) for v in val])
                conditions.append(f"{col} IN ({values})")
            elif isinstance(val, dict):
                # Range queries
                if 'min' in val and 'max' in val:
                    conditions.append(f"{col} BETWEEN {val['min']} AND {val['max']}")
                elif 'min' in val:
                    conditions.append(f"{col} >= {val['min']}")
                elif 'max' in val:
                    conditions.append(f"{col} <= {val['max']}")
            else:
                # Numeric or boolean
                conditions.append(f"{col} = {val}")
        
        return "WHERE " + " AND ".join(conditions)
    
    def _build_group_by(self, dimensions: List[str]) -> str:
        """Build GROUP BY clause"""
        
        if not dimensions:
            return ""
        
        return "GROUP BY " + ", ".join(dimensions)
    
    def _build_having(self, parsed: ParsedQuery) -> str:
        """Build HAVING clause (for filtering aggregated results)"""
        
        # Add HAVING logic if needed (e.g., "failure rate > 10%")
        # For now, return empty
        return ""
    
    def _build_order_by(self, parsed: ParsedQuery) -> str:
        """Build ORDER BY clause safely (GROUP BY compatible)"""

        # Map metrics to SELECT aliases (ONLY aggregated columns)
        metric_alias_map = {
            'avg_amount': 'avg_amount',
            'total_amount': 'total_amount',
            'median_amount': 'median_amount',
            'count': 'count',
            'success_rate': 'success_rate',
            'failure_rate': 'failure_rate',
            'fraud_flag_rate': 'fraud_flag_rate',
            'min_amount': 'min_amount',
            'max_amount': 'max_amount',
        }

        # Always prefer ordering by an aggregated metric
        if parsed.metrics:
            metric = parsed.metrics[0]
            if metric in metric_alias_map:
                return f"ORDER BY {metric_alias_map[metric]} DESC"

    # Temporal queries (safe because these are GROUP BY dimensions)
        if parsed.intent == QueryIntent.TEMPORAL:
            if 'hour_of_day' in parsed.dimensions:
                return "ORDER BY hour_of_day ASC"
            elif 'day_of_week' in parsed.dimensions:
                return "ORDER BY day_of_week ASC"

        return ""

    
    def _build_limit(self, parsed: ParsedQuery) -> str:
        """Build LIMIT clause"""
        
        # For grouped queries, limit to top 100 to prevent huge results
        if parsed.dimensions:
            return "LIMIT 100"
        
        return ""
    
    def validate_sql(self, sql: str) -> bool:
        """Validate SQL syntax (basic check)"""
        
        required = ['SELECT', 'FROM']
        sql_upper = sql.upper()
        
        return all(keyword in sql_upper for keyword in required)


# ============================================================================
# TESTING
# ============================================================================
if __name__ == "__main__":
    from nlp.parser import QueryParser
    
    parser = QueryParser()
    generator = SQLGenerator()
    
    print("\n" + "="*80)
    print("SQL GENERATOR COMPREHENSIVE TEST")
    print("="*80)
    
    test_cases = [
        # Descriptive queries
        "What is the average transaction amount?",
        "What is the average P2M amount?",
        "How many transactions are there?",
        "What is the total transaction volume?",
        
        # Comparative queries
        "Compare failure rates by device type",
        "Which transaction type has the highest average amount?",
        
        # Temporal queries
        "Show me transactions by hour",
        
        # Segmentation queries
        "Break down transactions by age group",
        "Show me P2P transactions by state",
        
        # Filtered queries
        "What is the average amount for weekend transactions?",
        "How many Android users?",
        "Show me food category transactions",
    ]
    
    success_count = 0
    
    for i, query in enumerate(test_cases, 1):
        print(f"\n{i}. Query: {query}")
        
        try:
            # Parse query
            parsed = parser.parse(query)
            
            # Generate SQL
            sql = generator.generate(parsed)
            
            # Validate
            if generator.validate_sql(sql):
                print(f"   ✅ SQL: {sql[:100]}..." if len(sql) > 100 else f"   ✅ SQL: {sql}")
                success_count += 1
            else:
                print(f"   ❌ INVALID SQL: {sql}")
        
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
    
    print("\n" + "="*80)
    print(f"RESULTS: {success_count}/{len(test_cases)} tests passed")
    
    if success_count == len(test_cases):
        print("🎉 ALL TESTS PASSED!")
    else:
        print(f"⚠️  {len(test_cases) - success_count} tests failed")
    
    print("="*80)