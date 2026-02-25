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
        print("âœ“ Embedding model loaded")
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="insightx_schema",
            metadata={"description": "UPI transaction schema and business context"}
        )
        
        print(f"âœ“ Schema Embedder initialized ({self.collection.count()} embeddings)")
    
    def embed_schema(self, force_refresh: bool = False):
        """
        Embed complete schema knowledge
        
        Args:
            force_refresh: Force re-embedding even if exists
        """
        
        # Check if already embedded
        if self.collection.count() > 0 and not force_refresh:
            print(f"âœ“ Schema already embedded ({self.collection.count()} items)")
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
        
        print(f"âœ“ Embedded {len(documents)} schema documents")
    
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
