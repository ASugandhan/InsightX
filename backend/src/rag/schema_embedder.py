"""
Schema Embedder
Embeds database schema and business context into vector database
"""

import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict
import os


class SchemaEmbedder:
    """Embed schema knowledge for RAG retrieval"""
    
    def __init__(self, persist_directory: str = "../data/chroma_db"):
        """
        Initialize schema embedder
        
        Args:
            persist_directory: Where to store ChromaDB
        """
        
        # Initialize embedding model
        print("Loading embedding model...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✓ Embedding model loaded")
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="insightx_schema",
            metadata={"description": "UPI transaction schema and business context"}
        )
        
        print(f"✓ Schema Embedder initialized ({self.collection.count()} embeddings)")
    
    def embed_schema(self, force_refresh: bool = False):
        """
        Embed complete schema knowledge
        
        Args:
            force_refresh: Force re-embedding even if exists
        """
        
        # Check if already embedded
        if self.collection.count() > 0 and not force_refresh:
            print(f"✓ Schema already embedded ({self.collection.count()} items)")
            return
        
        print("Embedding schema knowledge...")
        
        # Get schema documents
        schema_docs = self._build_schema_documents()
        
        # Prepare for ChromaDB
        documents = []
        metadatas = []
        ids = []
        
        for i, doc in enumerate(schema_docs):
            documents.append(doc['text'])
            metadatas.append(doc['metadata'])
            ids.append(f"schema_{i}")
        
        # Embed and store
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"✓ Embedded {len(documents)} schema documents")
    
    def _build_schema_documents(self) -> List[Dict]:
        """Build schema documents for embedding"""
        
        documents = []
        
        # Column definitions
        columns = [
            {
                'text': "transaction_type: Type of payment (P2P person-to-person, P2M person-to-merchant, Bill Payment, Recharge)",
                'metadata': {'type': 'column', 'name': 'transaction_type', 'category': 'core'}
            },
            {
                'text': "amount_inr: Transaction amount in Indian Rupees. Use for average amount, total amount, high-value transactions",
                'metadata': {'type': 'column', 'name': 'amount_inr', 'category': 'metric'}
            },
            {
                'text': "transaction_status: SUCCESS or FAILED. Use for success rate, failure rate, failed transactions",
                'metadata': {'type': 'column', 'name': 'transaction_status', 'category': 'core'}
            },
            {
                'text': "merchant_category: Category for P2M transactions - Food, Grocery, Fuel, Entertainment, Shopping, Healthcare, Education, Transport, Utilities, Other",
                'metadata': {'type': 'column', 'name': 'merchant_category', 'category': 'dimension'}
            },
            {
                'text': "sender_age_group: Age group of sender - 18-25, 26-35, 36-45, 46-55, 56+. Use for demographic analysis",
                'metadata': {'type': 'column', 'name': 'sender_age_group', 'category': 'dimension'}
            },
            {
                'text': "device_type: Device used - Android, iOS, Web. Use for device analysis, platform comparison",
                'metadata': {'type': 'column', 'name': 'device_type', 'category': 'dimension'}
            },
            {
                'text': "fraud_flag: Binary flag (0 or 1). Value 1 means flagged for review, NOT confirmed fraud. Use for fraud analysis",
                'metadata': {'type': 'column', 'name': 'fraud_flag', 'category': 'metric'}
            },
            {
                'text': "hour_of_day: Hour when transaction occurred (0-23). Use for temporal analysis, peak hours",
                'metadata': {'type': 'column', 'name': 'hour_of_day', 'category': 'temporal'}
            },
            {
                'text': "is_weekend: Binary flag (0=weekday, 1=weekend). Use for weekend vs weekday analysis",
                'metadata': {'type': 'column', 'name': 'is_weekend', 'category': 'temporal'}
            },
            {
                'text': "sender_state: Indian state of sender (Maharashtra, Delhi, Karnataka, Tamil Nadu, etc). Use for geographic analysis",
                'metadata': {'type': 'column', 'name': 'sender_state', 'category': 'dimension'}
            },
            {
                'text': "sender_bank: Sender's bank (SBI, HDFC, ICICI, Axis, PNB, Kotak, IndusInd, Yes Bank)",
                'metadata': {'type': 'column', 'name': 'sender_bank', 'category': 'dimension'}
            },
            {
                'text': "network_type: Network type (4G, 5G, WiFi, 3G). Use for network performance analysis",
                'metadata': {'type': 'column', 'name': 'network_type', 'category': 'technical'}
            },
        ]
        
        documents.extend(columns)
        
        # Business context
        business_context = [
            {
                'text': "High-value transactions typically means amount > ₹5,000. Premium transactions > ₹10,000. Micro-transactions < ₹100",
                'metadata': {'type': 'business_rule', 'category': 'thresholds'}
            },
            {
                'text': "Peak hours are typically 8-10 AM (morning commute), 12-2 PM (lunch), 6-8 PM (evening commute), 8-10 PM (dinner)",
                'metadata': {'type': 'business_rule', 'category': 'temporal_patterns'}
            },
            {
                'text': "Failure rates above 10% are considered high. Success rates above 95% are excellent. Normal is 90-95%",
                'metadata': {'type': 'business_rule', 'category': 'benchmarks'}
            },
            {
                'text': "Fraud flag rate above 15% requires investigation. Normal fraud flag rate is 5-10%",
                'metadata': {'type': 'business_rule', 'category': 'fraud'}
            },
            {
                'text': "P2P transactions are typically lower amounts (₹500-2000). P2M transactions are higher (₹1000-5000)",
                'metadata': {'type': 'business_rule', 'category': 'transaction_patterns'}
            },
            {
                'text': "Food delivery transactions peak at lunch (12-2 PM) and dinner (8-10 PM) hours",
                'metadata': {'type': 'business_rule', 'category': 'merchant_patterns'}
            },
            {
                'text': "Weekend transactions are typically 25-30% of total. Higher leisure spending on weekends (entertainment, food)",
                'metadata': {'type': 'business_rule', 'category': 'temporal_patterns'}
            },
            {
                'text': "Young age group (18-25) has higher failure rates due to insufficient balance. Older groups (36+) more stable",
                'metadata': {'type': 'business_rule', 'category': 'demographic_patterns'}
            },
            {
                'text': "Android devices dominate (60-70% of transactions). iOS users typically higher transaction amounts",
                'metadata': {'type': 'business_rule', 'category': 'device_patterns'}
            },
            {
                'text': "5G networks have lowest failure rates. 3G networks highest failure rates (timeouts)",
                'metadata': {'type': 'business_rule', 'category': 'network_patterns'}
            },
        ]
        
        documents.extend(business_context)
        
        # Common query patterns
        query_patterns = [
            {
                'text': "When user asks about 'expensive' or 'costly' transactions, filter amount_inr > 5000",
                'metadata': {'type': 'query_pattern', 'intent': 'high_value'}
            },
            {
                'text': "When user asks about 'cheap' or 'small' transactions, filter amount_inr < 500",
                'metadata': {'type': 'query_pattern', 'intent': 'low_value'}
            },
            {
                'text': "When user asks about 'problems' or 'issues', look at failed transactions or high fraud flags",
                'metadata': {'type': 'query_pattern', 'intent': 'problems'}
            },
            {
                'text': "When user asks about 'best performing', look at high success rates or low fraud flags",
                'metadata': {'type': 'query_pattern', 'intent': 'performance'}
            },
            {
                'text': "When user asks about 'busiest times', group by hour_of_day and count transactions",
                'metadata': {'type': 'query_pattern', 'intent': 'temporal'}
            },
            {
                'text': "When user asks about 'popular categories', group by merchant_category for P2M transactions",
                'metadata': {'type': 'query_pattern', 'intent': 'category_analysis'}
            },
            {
                'text': "When user asks about 'young users' or 'youth', filter sender_age_group = 18-25",
                'metadata': {'type': 'query_pattern', 'intent': 'demographic'}
            },
            {
                'text': "When user asks about 'mobile users', include both Android and iOS device types",
                'metadata': {'type': 'query_pattern', 'intent': 'device'}
            },
        ]
        
        documents.extend(query_patterns)
        
        return documents
    
    def search(self, query: str, n_results: int = 5) -> List[Dict]:
        """
        Search for relevant schema context
        
        Args:
            query: User query
            n_results: Number of results to return
        
        Returns:
            List of relevant documents with metadata
        """
        
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        # Format results
        formatted = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                formatted.append({
                    'text': doc,
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'distance': results['distances'][0][i] if results.get('distances') else None
                })
        
        return formatted


# ============================================================================
# TESTING
# ============================================================================
if __name__ == "__main__":
    print("\n" + "="*80)
    print("SCHEMA EMBEDDER TEST")
    print("="*80)
    
    embedder = SchemaEmbedder()
    
    # Embed schema (only first time)
    embedder.embed_schema()
    
    # Test queries
    test_queries = [
        "What are high-value transactions?",
        "Show me failed transactions",
        "Which age group has most transactions?",
        "What are peak hours?",
        "Food delivery patterns",
    ]
    
    print("\n" + "-"*80)
    print("TESTING CONTEXT RETRIEVAL")
    print("-"*80)
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        results = embedder.search(query, n_results=3)
        
        print("  Relevant context:")
        for i, result in enumerate(results, 1):
            print(f"    {i}. {result['text'][:100]}...")
    
    print("\n" + "="*80)
    print("✓ SCHEMA EMBEDDER TEST COMPLETE")
    print("="*80)