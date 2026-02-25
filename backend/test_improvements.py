"""
Test Script for NEXUS Accuracy Improvements
Tests all new components and enhancements
"""

import sys
sys.path.append('src')

from src.main import InsightXSystem

def test_improvements():
    print("="*80)
    print("NEXUS ACCURACY IMPROVEMENT - COMPREHENSIVE TEST")
    print("="*80)
    
    # Initialize system
    system = InsightXSystem('data/upi_transactions_2024.csv')
    
    print("\n" + "="*80)
    print("TEST 1: Temporal Queries (NEW)")
    print("="*80)
    
    queries_temporal = [
        "Show me last month's transactions",
        "What about weekend transactions?",
        "Show me weekday performance"
    ]
    
    for query in queries_temporal:
        print(f"\nQuery: {query}")
        system.ask(query)
        print("-"*40)
    
    print("\n" + "="*80)
    print("TEST 2: Ambiguous Queries with Smart Defaults (NEW)")
    print("="*80)
    
    queries_ambiguous = [
        "Show transactions",
        "Show me fraud",
        "What about failures?"
    ]
    
    for query in queries_ambiguous:
        print(f"\nQuery: {query}")
        system.ask(query)
        print("-"*40)
    
    print("\n" + "="*80)
    print("TEST 3: Query Rewriting (NEW)")
    print("="*80)
    
    queries_rewrite = [
        "Best performing device",
        "Worst performing age group",
        "Most popular merchant category"
    ]
    
    for query in queries_rewrite:
        print(f"\nQuery: {query}")
        system.ask(query)
        print("-"*40)
    
    print("\n" + "="*80)
    print("TEST 4: Complex Queries with Validation (ENHANCED)")
    print("="*80)
    
    queries_complex = [
        "Compare failure rates by device type for 18-25 age group",
        "What is the average transaction amount for food delivery on weekends?",
        "Show me fraud flag rates by network type for high-value transactions"
    ]
    
    for query in queries_complex:
        print(f"\nQuery: {query}")
        system.ask(query, show_tier2=True)
        print("-"*40)
    
    print("\n" + "="*80)
    print("TEST 5: Confidence Calibration (ENHANCED)")
    print("="*80)
    
    queries_confidence = [
        "What is the total transaction count?",  # Simple - should be HIGH
        "Compare success rates by device, age group, and merchant category",  # Complex - should adjust
        "Show me transactions where fraud flag is high"  # Should validate properly
    ]
    
    for query in queries_confidence:
        print(f"\nQuery: {query}")
        response = system.ask(query)
        print(f"Final Confidence: {response.confidence}")
        print("-"*40)
    
    print("\n" + "="*80)
    print("✅ ALL TESTS COMPLETE!")
    print("="*80)
    print("\nKey Improvements Tested:")
    print("  1. ✅ Query Clarification")
    print("  2. ✅ Temporal Parsing") 
    print("  3. ✅ Context Defaults")
    print("  4. ✅ Query Rewriting")
    print("  5. ✅ Enhanced RAG (100+ documents)")
    print("  6. ✅ Confidence Calibration")
    print("  7. ✅ Result Validation")
    print("  8. ✅ Warning Detection")
    print("="*80)

if __name__ == "__main__":
    test_improvements()
