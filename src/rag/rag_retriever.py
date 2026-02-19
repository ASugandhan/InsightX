"""
RAG Retriever
Retrieves relevant context from schema and examples
"""

from typing import List, Dict, Optional
from rag.schema_embedder import SchemaEmbedder
from rag.example_library import ExampleLibrary
import chromadb
from chromadb.utils import embedding_functions           

class RAGRetriever:
    """Retrieve relevant context for query enhancement"""
    
    def __init__(self, persist_directory, analytics_engine=None):
        self.analytics_engine = analytics_engine

        # Embedding function (shared across system)
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

        # Chroma client
        self.client = chromadb.Client(
            chromadb.config.Settings(
                persist_directory=persist_directory,
                anonymized_telemetry=False
            )
        )

        # Main collection (used by RAG + similarity)
        self.collection = self.client.get_or_create_collection(
            name="insightx_rag",
            embedding_function=self.embedding_fn
        )

        # Existing components
        self.schema_embedder = SchemaEmbedder(persist_directory)
        self.example_library = ExampleLibrary(persist_directory)

        print("✓ RAG Retriever initialized (collection + engine attached)")
    
    def get_collection(self):
        """Expose Chroma collection safely"""
        return self.collection


    def get_engine(self):
        """Expose analytics engine (read-only usage)"""
        return self.analytics_engine
    
    def retrieve_context(self, query: str, n_schema: int = 5, n_examples: int = 3) -> Dict:
        """
        Retrieve all relevant context for a query
        
        Args:
            query: User's natural language query
            n_schema: Number of schema documents to retrieve
            n_examples: Number of example queries to retrieve
        
        Returns:
            Dict with schema_context and example_queries
        """
        
        # Get schema context
        schema_results = self.schema_embedder.search(query, n_results=n_schema)
        
        # Get similar examples
        example_results = self.example_library.find_similar(query, n_results=n_examples)
        
        # Format context
        context = {
            'schema_context': self._format_schema_context(schema_results),
            'example_queries': self._format_examples(example_results),
            'suggestions': self._generate_suggestions(schema_results, query)
        }
        
        return context
    
    def _format_schema_context(self, results: List[Dict]) -> List[str]:
        """Format schema context for prompt"""
        
        formatted = []
        
        for result in results:
            text = result['text']
            metadata = result.get('metadata', {})
            
            # Add type indicator
            doc_type = metadata.get('type', 'unknown')
            
            if doc_type == 'column':
                formatted.append(f"📊 Column: {text}")
            elif doc_type == 'business_rule':
                formatted.append(f"💼 Rule: {text}")
            elif doc_type == 'query_pattern':
                formatted.append(f"🔍 Pattern: {text}")
            else:
                formatted.append(text)
        
        return formatted
    
    def _format_examples(self, results: List[Dict]) -> List[Dict]:
        """Format example queries"""
        
        formatted = []
        
        for result in results:
            formatted.append({
                'query': result['query'],
                'intent': result['metadata'].get('intent'),
                'metrics': result['metadata'].get('metrics', '').split(',') if result['metadata'].get('metrics') else [],
                'dimensions': result['metadata'].get('dimensions', '').split(',') if result['metadata'].get('dimensions') else []
            })
        
        return formatted
    
    def _generate_suggestions(self, schema_results: List[Dict], query: str) -> List[str]:
        """Generate query suggestions based on context"""
        
        suggestions = []
        query_lower = query.lower()
        
        # Check for common patterns
        for result in schema_results:
            metadata = result.get('metadata', {})
            
            if metadata.get('type') == 'query_pattern':
                # Extract suggestion from pattern
                text = result['text']
                if 'filter' in text.lower():
                    suggestions.append("Consider adding specific filters")
                if 'group by' in text.lower():
                    suggestions.append("Consider grouping by a dimension")
        
        # Check for missing context
        if 'high' in query_lower or 'expensive' in query_lower or 'large' in query_lower:
            if not any('5000' in r['text'] or 'threshold' in r['text'] for r in schema_results):
                suggestions.append("Define 'high-value' threshold (e.g., >₹5,000)")
        
        if 'peak' in query_lower or 'busy' in query_lower:
            suggestions.append("Group by hour_of_day to find peak times")
        
        if 'popular' in query_lower or 'most' in query_lower:
            suggestions.append("Use COUNT with GROUP BY to find most popular")
        
        return list(set(suggestions))  # Remove duplicates
    
    def get_column_info(self, column_name: str) -> Optional[str]:
        """Get information about a specific column"""
        
        results = self.schema_embedder.search(column_name, n_results=1)
        
        if results and column_name.lower() in results[0]['text'].lower():
            return results[0]['text']
        
        return None
    
    def get_business_rule(self, topic: str) -> Optional[str]:
        """Get business rule about a topic"""
        
        results = self.schema_embedder.search(topic, n_results=3)
        
        for result in results:
            if result.get('metadata', {}).get('type') == 'business_rule':
                return result['text']
        
        return None


# ============================================================================
# TESTING
# ============================================================================
if __name__ == "__main__":
    import sys
    sys.path.append('..')
    
    print("\n" + "="*80)
    print("RAG RETRIEVER TEST")
    print("="*80)
    
    retriever = RAGRetriever()
    
    # Test queries
    test_queries = [
        "Show me high-value transactions",
        "What are peak hours?",
        "Compare failure rates by device",
        "Which age group spends most?",
    ]
    
    print("\n" + "-"*80)
    print("CONTEXT RETRIEVAL")
    print("-"*80)
    
    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"Query: {query}")
        print(f"{'='*80}")
        
        context = retriever.retrieve_context(query, n_schema=3, n_examples=2)
        
        print("\n📚 Schema Context:")
        for i, ctx in enumerate(context['schema_context'], 1):
            print(f"  {i}. {ctx}")
        
        print("\n📖 Similar Examples:")
        for i, ex in enumerate(context['example_queries'], 1):
            print(f"  {i}. {ex['query']}")
            print(f"     → Intent: {ex['intent']}, Metrics: {ex['metrics']}")
        
        if context['suggestions']:
            print("\n💡 Suggestions:")
            for sugg in context['suggestions']:
                print(f"  • {sugg}")
    
    print("\n" + "="*80)
    print("✓ RAG RETRIEVER TEST COMPLETE")
    print("="*80)