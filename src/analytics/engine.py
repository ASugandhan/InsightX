import duckdb
import pandas as pd
import time
from pathlib import Path

class AnalyticsEngine:
    def __init__(self, csv_path):
        print("Initializing Analytics Engine...")
        self.conn = duckdb.connect(':memory:')
        self.csv_path = csv_path
        self._load_data()
        self._create_indexes()
        print("✓ Analytics Engine ready!")
    
    def _load_data(self):
        """Load CSV into DuckDB"""
        print(f"Loading data from {self.csv_path}...")
        start = time.time()
        
        self.conn.execute(f"""
            CREATE TABLE transactions AS 
            SELECT * FROM read_csv_auto('{self.csv_path}')
        """)
        
        count = self.conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
        elapsed = time.time() - start
        print(f"✓ Loaded {count:,} rows in {elapsed:.2f}s")
    
    def _create_indexes(self):
        """Create indexes on filter columns"""
        print("Creating indexes...")
        
        index_columns = [
            'transaction_type',
            'transaction_status',
            'sender_age_group',
            'device_type',
            'hour_of_day'
        ]
        
        for col in index_columns:
            try:
                self.conn.execute(f"CREATE INDEX idx_{col} ON transactions({col})")
                print(f"  ✓ Index on {col}")
            except Exception as e:
                print(f"  ✗ Failed to index {col}: {e}")
    
    def query(self, sql):
        """Execute SQL query and return DataFrame"""
        start = time.time()
        result = self.conn.execute(sql).df()
        elapsed = time.time() - start
        print(f"Query executed in {elapsed*1000:.1f}ms")
        return result
    
    def test_queries(self):
        """Test basic queries"""
        print("\n" + "="*60)
        print("TESTING QUERIES")
        print("="*60)
        
        # Test 1: Count
        result = self.query("SELECT COUNT(*) as count FROM transactions")
        print(f"\n1. Total transactions: {result['count'][0]:,}")
        
        # Test 2: Average amount
        result = self.query("""
            SELECT AVG(amount_inr) as avg_amount 
            FROM transactions
        """)
        print(f"2. Average amount: ₹{result['avg_amount'][0]:.2f}")
        
        # Test 3: By type
        result = self.query("""
            SELECT 
                transaction_type,
                COUNT(*) as count,
                AVG(amount_inr) as avg_amount
            FROM transactions
            GROUP BY transaction_type
        """)
        print(f"\n3. By transaction type:")
        print(result)
        
        # Test 4: Success rate
        result = self.query("""
            SELECT 
                ROUND(SUM(CASE WHEN transaction_status='SUCCESS' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as success_rate
            FROM transactions
        """)
        print(f"\n4. Success rate: {result['success_rate'][0]}%")
        
        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED!")
        print("="*60)

# Test it
if __name__ == "__main__":
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
    CSV_PATH = PROJECT_ROOT / "data" / "upi_transactions_2024.csv"
    engine = AnalyticsEngine(str(CSV_PATH))
    engine.test_queries()