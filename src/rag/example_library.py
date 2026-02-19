"""
Example Query Library
Stores and retrieves example queries for few-shot learning
"""

import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict


class ExampleLibrary:
    """Store and retrieve example query-response pairs"""
    
    def __init__(self, persist_directory: str = "../data/chroma_db"):
        """Initialize example library"""
        
        # Reuse embedding model (if already loaded)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="insightx_examples",
            metadata={"description": "Example queries and their correct interpretations"}
        )
        
        print(f"✓ Example Library initialized ({self.collection.count()} examples)")
    
    def load_examples(self, force_refresh: bool = False):
        """Load example queries into library"""
        
        if self.collection.count() > 0 and not force_refresh:
            print(f"✓ Examples already loaded ({self.collection.count()} items)")
            return
        
        print("Loading example queries...")
        
        examples = self._build_example_queries()
        
        documents = []
        metadatas = []
        ids = []
        
        for i, example in enumerate(examples):
            documents.append(example['query'])
            metadatas.append({
                'intent': example['intent'],
                'metrics': ','.join(example['metrics']),
                'filters': str(example['filters']),
                'dimensions': ','.join(example.get('dimensions', []))
            })
            ids.append(f"example_{i}")
        
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"✓ Loaded {len(examples)} example queries")
    
    def _build_example_queries(self) -> List[Dict]:
        """Build example query library"""
        
        return [
            # Simple descriptive queries
            {
                'query': "What is the average transaction amount?",
                'intent': 'descriptive',
                'metrics': ['avg_amount'],
                'filters': {},
                'dimensions': []
            },
            {
                'query': "How many transactions are there?",
                'intent': 'descriptive',
                'metrics': ['count'],
                'filters': {},
                'dimensions': []
            },
            {
                'query': "What is the total transaction volume?",
                'intent': 'descriptive',
                'metrics': ['total_amount'],
                'filters': {},
                'dimensions': []
            },
            
            # Filtered queries
            {
                'query': "What is the average P2M amount?",
                'intent': 'descriptive',
                'metrics': ['avg_amount'],
                'filters': {'transaction_type': 'P2M'},
                'dimensions': []
            },
            {
                'query': "Show me weekend transactions",
                'intent': 'descriptive',
                'metrics': ['count'],
                'filters': {'is_weekend': 1},
                'dimensions': []
            },
            {
                'query': "How many failed transactions?",
                'intent': 'descriptive',
                'metrics': ['count'],
                'filters': {'transaction_status': 'FAILED'},
                'dimensions': []
            },
            
            # Comparative queries
            {
                'query': "Compare failure rates by device type",
                'intent': 'comparative',
                'metrics': ['failure_rate'],
                'filters': {},
                'dimensions': ['device_type']
            },
            {
                'query': "Which age group has highest average amount?",
                'intent': 'comparative',
                'metrics': ['avg_amount'],
                'filters': {},
                'dimensions': ['sender_age_group']
            },
            
            # Temporal queries
            {
                'query': "What are the peak transaction hours?",
                'intent': 'temporal',
                'metrics': ['count'],
                'filters': {},
                'dimensions': ['hour_of_day']
            },
            {
                'query': "Show me transactions by hour",
                'intent': 'temporal',
                'metrics': ['count'],
                'filters': {},
                'dimensions': ['hour_of_day']
            },
            
            # Complex queries (with context)
            {
                'query': "Show me expensive transactions",
                'intent': 'descriptive',
                'metrics': ['count'],
                'filters': {'amount_inr': {'min': 5000}},  # high-value threshold
                'dimensions': []
            },
            {
                'query': "Which merchant categories are most popular?",
                'intent': 'comparative',
                'metrics': ['count'],
                'filters': {'transaction_type': 'P2M'},
                'dimensions': ['merchant_category']
            },
            {
                'query': "Show me fraud-flagged transactions",
                'intent': 'descriptive',
                'metrics': ['count', 'fraud_flag_rate'],
                'filters': {'fraud_flag': 1},
                'dimensions': []
            },
            
            # Demographic queries
            {
                'query': "How do young users transact?",
                'intent': 'descriptive',
                'metrics': ['avg_amount', 'count'],
                'filters': {'sender_age_group': '18-25'},
                'dimensions': []
            },
            {
                'query': "Show me mobile user transactions",
                'intent': 'descriptive',
                'metrics': ['count'],
                'filters': {'device_type': ['Android', 'iOS']},
                'dimensions': []
            },
        ]
    
    def find_similar(self, query: str, n_results: int = 3) -> List[Dict]:
        """Find similar example queries"""
        
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        formatted = []
        if results['documents'] and results['documents'][0]:
            for i in range(len(results['documents'][0])):
                formatted.append({
                    'query': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {}
                })
        
        return formatted


# ============================================================================
# TESTING
# ============================================================================
if __name__ == "__main__":
    print("\n" + "="*80)
    print("EXAMPLE LIBRARY TEST")
    print("="*80)
    
    library = ExampleLibrary()
    library.load_examples()
    
    # Test queries
    test_queries = [
        "What's the average P2P transaction value?",
        "Show me high-value transactions",
        "Which devices have most failures?",
        "What time do people transact most?",
    ]
    
    print("\n" + "-"*80)
    print("FINDING SIMILAR EXAMPLES")
    print("-"*80)
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        similar = library.find_similar(query, n_results=2)
        
        print("  Similar examples:")
        for i, ex in enumerate(similar, 1):
            print(f"    {i}. {ex['query']}")
            print(f"       Intent: {ex['metadata'].get('intent')}")
            print(f"       Metrics: {ex['metadata'].get('metrics')}")
    
    print("\n" + "="*80)
    print("✓ EXAMPLE LIBRARY TEST COMPLETE")
    print("="*80)