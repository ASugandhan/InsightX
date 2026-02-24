import duckdb
import pandas as pd
import time

class AnalyticsEngine:
    def __init__(self, csv_path):
        print("Initializing Analytics Engine...")
        self.conn = duckdb.connect(':memory:')
        self.csv_path = csv_path
        self.precomputed = {}  # ADD THIS LINE
        
        self._load_data()
        self._create_indexes()
        self._precompute_metrics()  # ADD THIS LINE
        
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
            'merchant_category',
            'sender_age_group',
            'sender_state',
            'device_type',
            'network_type',
            'hour_of_day',
            'is_weekend',
            'sender_bank',
            'receiver_bank'
        ]
        
        for col in index_columns:
            try:
                self.conn.execute(f"CREATE INDEX idx_{col} ON transactions({col})")
                print(f"  ✓ Index on {col}")
            except Exception as e:
                print(f"  ⚠️  Could not index {col}: {e}")
    
    def _precompute_metrics(self):
        """Pre-compute frequently requested metrics"""
        print("Pre-computing common metrics...")
        
        start = time.time()
        
        # Overall statistics
        self.precomputed['overall'] = self.query("""
            SELECT 
                COUNT(*) as total_txns,
                ROUND(SUM(amount_inr), 2) as total_amount,
                ROUND(AVG(amount_inr), 2) as avg_amount,
                ROUND(MEDIAN(amount_inr), 2) as median_amount,
                ROUND(STDDEV(amount_inr), 2) as std_amount,
                ROUND(MIN(amount_inr), 2) as min_amount,
                ROUND(MAX(amount_inr), 2) as max_amount,
                SUM(CASE WHEN transaction_status = 'SUCCESS' THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN transaction_status = 'FAILED' THEN 1 ELSE 0 END) as failed_count,
                ROUND(SUM(CASE WHEN transaction_status = 'SUCCESS' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as success_rate,
                ROUND(SUM(CASE WHEN transaction_status = 'FAILED' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as failure_rate,
                SUM(fraud_flag) as fraud_flags,
                ROUND(SUM(fraud_flag) * 100.0 / COUNT(*), 2) as fraud_flag_rate
            FROM transactions
        """).to_dict('records')[0]
        
        # By transaction type
        self.precomputed['by_type'] = self.query("""
            SELECT 
                transaction_type,
                COUNT(*) as count,
                ROUND(AVG(amount_inr), 2) as avg_amount,
                ROUND(MEDIAN(amount_inr), 2) as median_amount,
                ROUND(SUM(CASE WHEN transaction_status = 'FAILED' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as failure_rate,
                ROUND(SUM(fraud_flag) * 100.0 / COUNT(*), 2) as fraud_flag_rate
            FROM transactions
            GROUP BY transaction_type
            ORDER BY count DESC
        """).to_dict('records')
        
        # By hour of day
        self.precomputed['by_hour'] = self.query("""
            SELECT 
                hour_of_day,
                COUNT(*) as count,
                ROUND(AVG(amount_inr), 2) as avg_amount,
                ROUND(SUM(CASE WHEN transaction_status = 'FAILED' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as failure_rate
            FROM transactions
            GROUP BY hour_of_day
            ORDER BY hour_of_day
        """).to_dict('records')
        
        # By age group
        self.precomputed['by_age'] = self.query("""
            SELECT 
                sender_age_group,
                COUNT(*) as count,
                ROUND(AVG(amount_inr), 2) as avg_amount,
                ROUND(SUM(fraud_flag) * 100.0 / COUNT(*), 2) as fraud_flag_rate
            FROM transactions
            GROUP BY sender_age_group
            ORDER BY count DESC
        """).to_dict('records')
        
        # By device type
        self.precomputed['by_device'] = self.query("""
            SELECT 
                device_type,
                COUNT(*) as count,
                ROUND(AVG(amount_inr), 2) as avg_amount,
                ROUND(SUM(CASE WHEN transaction_status = 'FAILED' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as failure_rate
            FROM transactions
            GROUP BY device_type
            ORDER BY count DESC
        """).to_dict('records')
        
        # By merchant category (for P2M only)
        self.precomputed['by_merchant'] = self.query("""
            SELECT 
                merchant_category,
                COUNT(*) as count,
                ROUND(AVG(amount_inr), 2) as avg_amount
            FROM transactions
            WHERE merchant_category IS NOT NULL
            GROUP BY merchant_category
            ORDER BY count DESC
        """).to_dict('records')
        
        elapsed = time.time() - start
        print(f"  ✓ Pre-computed {len(self.precomputed)} metric sets in {elapsed:.2f}s")
    
    def query(self, sql):
        """Execute SQL query and return DataFrame"""
        start = time.time()
        result = self.conn.execute(sql).df()
        elapsed = time.time() - start
        # print(f"Query executed in {elapsed*1000:.1f}ms")  # Comment out for less verbosity
        return result
    
    def get_precomputed(self, key: str):
        """Retrieve pre-computed metric"""
        return self.precomputed.get(key)
    
    def test_queries(self):
        """Test basic queries"""
        print("\n" + "="*60)
        print("TESTING QUERIES")
        print("="*60)
        
        # Test 1: Overall stats
        overall = self.get_precomputed('overall')
        print(f"\n1. Overall Statistics (Pre-computed):")
        print(f"   Total transactions: {overall['total_txns']:,}")
        print(f"   Average amount: ₹{overall['avg_amount']:,.2f}")
        print(f"   Success rate: {overall['success_rate']}%")
        print(f"   Fraud flag rate: {overall['fraud_flag_rate']}%")
        
        # Test 2: By type
        by_type = self.get_precomputed('by_type')
        print(f"\n2. By Transaction Type (Pre-computed):")
        for t in by_type:
            print(f"   {t['transaction_type']}: {t['count']:,} txns, avg ₹{t['avg_amount']:,.2f}")
        
        # Test 3: Regular query
        result = self.query("""
            SELECT 
                AVG(amount_inr) as avg_amount 
            FROM transactions
            WHERE transaction_type = 'P2M'
        """)
        print(f"\n3. Average P2M amount (Dynamic query): ₹{result['avg_amount'][0]:,.2f}")
        
        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED!")
        print("="*60)

if __name__ == "__main__":
    CSV_PATH = r"E:\E\Project\prj idea -7\insightx\data\upi_transactions_2024.csv"

    engine = AnalyticsEngine(CSV_PATH)
    engine.test_queries()