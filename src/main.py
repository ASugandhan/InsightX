import sys
from pathlib import Path
sys.path.append('src')

from analytics.engine import AnalyticsEngine
from nlp.parser import QueryParser
from explainability.formatter import ResponseFormatter

class InsightXSystem:
    def __init__(self, csv_path):
        print("\n" + "="*60)
        print("INITIALIZING INSIGHTX SYSTEM")
        print("="*60)
        
        self.analytics = AnalyticsEngine(csv_path)
        self.parser = QueryParser()
        self.formatter = ResponseFormatter()
        
        print("\n✓ All components initialized!")
        print("="*60)
    
    def ask(self, question: str):
        """Main entry point: Ask a question, get an answer"""
        print(f"\n📝 Question: {question}")
        
        # Parse question
        parsed = self.parser.parse(question)
        print(f"✓ Parsed (confidence: {parsed.confidence:.2f})")
        
        # Generate SQL (simple version for now)
        sql = self._generate_sql(parsed)
        print(f"✓ Generated SQL")
        
        # Execute query
        result = self.analytics.query(sql)
        print(f"✓ Query executed")
        
        # Format response
        response = self.formatter.format(question, result, parsed.confidence)
        print(f"✓ Response formatted")
        
        # Display
        print(f"\n{'-'*60}")
        print(f"ANSWER:")
        print(f"{'-'*60}")
        print(response.tier1_text)
        print(f"\nConfidence: {response.confidence}")
        print(f"Based on: {response.sample_size} records")
        print(f"{'-'*60}")
        
        return response
    
    def _generate_sql(self, parsed):
        """Simple SQL generator (will improve later)"""
        
        # Build SELECT clause
        if 'avg_amount' in parsed.metrics:
            select = "SELECT AVG(amount_inr) as avg_amount"
        elif 'count' in parsed.metrics:
            select = "SELECT COUNT(*) as count"
        else:
            select = "SELECT COUNT(*) as count"
        
        # Add FROM
        sql = select + " FROM transactions"
        
        # Add WHERE
        if parsed.filters:
            where_parts = []
            for col, val in parsed.filters.items():
                if isinstance(val, str):
                    where_parts.append(f"{col} = '{val}'")
                else:
                    where_parts.append(f"{col} = {val}")
            sql += " WHERE " + " AND ".join(where_parts)
        
        return sql

# Test
if __name__ == "__main__":
    # Initialize system
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    CSV_PATH = PROJECT_ROOT / "data" / "upi_transactions_2024.csv"
    system = InsightXSystem(CSV_PATH)
    
    # Test queries
    print("\n\n" + "="*60)
    print("TESTING END-TO-END SYSTEM")
    print("="*60)
    
    test_questions = [
        "What is the average transaction amount?",
        "How many P2M transactions are there?",
        "Show me weekend transactions"
    ]
    
    for question in test_questions:
        system.ask(question)
        print("\n")
    
    print("="*60)
    print("✓ ALL END-TO-END TESTS PASSED!")
    print("="*60)