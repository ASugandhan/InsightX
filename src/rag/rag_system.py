"""
Complete RAG System
Combines all RAG components
"""

from rag.rag_retriever import RAGRetriever
from rag.query_enhancer import QueryEnhancer
from rag.synonym_handler import SynonymHandler
from nlp.parser import ParsedQuery


class RAGSystem:
    """Complete RAG system for InsightX"""
    
    def __init__(self, persist_directory: str = "../data/chroma_db"):
        """Initialize complete RAG system"""
        
        print("Initializing RAG System...")
        
        self.retriever = RAGRetriever(persist_directory)
        self.enhancer = QueryEnhancer(persist_directory)
        self.synonym_handler = SynonymHandler()
        
        print("✓ RAG System initialized")
    
    def process_query(self, query: str, parsed: ParsedQuery) -> tuple:
        """
        Complete RAG processing pipeline
        
        Args:
            query: Original query
            parsed: Initially parsed query
        
        Returns:
            (enhanced_query, context, explanation)
        """
        
        # Step 1: Normalize synonyms
        normalized_query = self.synonym_handler.normalize_query(query)
        
        # Step 2: Retrieve context
        context = self.retriever.retrieve_context(normalized_query)
        
        # Step 3: Enhance query
        enhanced, explanation = self.enhancer.enhance_parsed_query(normalized_query, parsed)
        
        return enhanced, context, explanation