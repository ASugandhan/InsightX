"""
RAG System Test Suite
"""

import sys
sys.path.append('src')

from rag.rag_system import RAGSystem
from nlp.parser import QueryParser


def test_rag_enhancements():
    """Test RAG enhancements"""
    
    print("\n" + "="*80)
    print("RAG ENHANCEMENT TEST")
    print("="*80)
    
    parser = QueryParser()
    rag = RAGSystem()
    
    test_cases = [
        ("Show me expensive transactions", "Should add amount filter >5000"),
        ("What are the busiest hours?", "Should group by hour_of_day"),
        ("Show me youth transactions", "Should filter age_group=18-25"),
        ("Which categories are most popular?", "Should add P2M filter + group by category"),
        ("Show me phone user transactions", "Should filter device=Android,iOS"),
    ]
    
    passed = 0
    
    for query, expected in test_cases:
        print(f"\n--- Test: {query} ---")
        print(f"Expected: {expected}")
        
        # Parse
        original = parser.parse(query)
        print(f"Original confidence: {original.confidence:.2f}")
        
        # Enhance with RAG
        enhanced, context, explanation = rag.process_query(query, original)
        print(f"Enhanced confidence: {enhanced.confidence:.2f}")
        print(f"Enhancements: {explanation}")
        
        # Verify improvement
        if enhanced.confidence > original.confidence:
            print("✅ PASS - Confidence improved")
            passed += 1
        else:
            print("❌ FAIL - No improvement")
    
    print(f"\n{'='*80}")
    print(f"Results: {passed}/{len(test_cases)} passed")
    print(f"{'='*80}")
    
    return passed == len(test_cases)


if __name__ == "__main__":
    success = test_rag_enhancements()
    sys.exit(0 if success else 1)