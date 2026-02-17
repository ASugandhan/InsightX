"""
Comprehensive system tests for InsightX
"""

import sys
sys.path.append('src')

from main import InsightXSystem

def test_system():
    """Test end-to-end system with 15 diverse queries"""
    
    print("\n" + "="*80)
    print("INSIGHTX SYSTEM - COMPREHENSIVE TEST SUITE")
    print("="*80)
    
    # Initialize system
    print("\nInitializing system...")
    system = InsightXSystem('data/upi_transactions_2024.csv')
    
    # Test queries (15 diverse examples)
    test_queries = [
        # Descriptive
        ("What is the average transaction amount?", "descriptive"),
        ("What is the average P2M amount?", "descriptive_filtered"),
        ("How many transactions are there?", "descriptive_count"),
        ("What is the total transaction volume?", "descriptive_sum"),
        
        # Comparative
        ("Compare failure rates by device type", "comparative"),
        ("Which transaction type has highest average amount?", "comparative"),
        ("Compare fraud rates by age group", "comparative"),
        
        # Temporal
        ("Show me transactions by hour", "temporal"),
        ("What are peak transaction hours?", "temporal"),
        
        # Segmentation
        ("Break down transactions by age group", "segmentation"),
        ("Show me P2P transactions by state", "segmentation"),
        
        # Filtered
        ("What is average amount for weekend transactions?", "filtered"),
        ("How many Android users?", "filtered"),
        ("Show me food category transactions", "filtered"),
        ("18-25 age group fraud rate", "filtered"),
    ]
    
    results = {
        'total': len(test_queries),
        'passed': 0,
        'failed': 0,
        'errors': []
    }
    
    print(f"\nRunning {len(test_queries)} test queries...")
    print("-" * 80)
    
    for i, (query, category) in enumerate(test_queries, 1):
        print(f"\n[{i}/{len(test_queries)}] {category.upper()}")
        print(f"Query: {query}")
        
        try:
            response = system.ask(query)
            
            # Validation checks
            assert response is not None, "No response returned"
            assert response.tier1_text, "Empty response text"
            assert response.confidence in ["HIGH ✓", "MEDIUM ⚠️", "LOW ⚠️"], "Invalid confidence"
            assert response.sample_size > 0, "Zero sample size"
            
            print(f"✅ PASS - Confidence: {response.confidence}, Sample: {response.sample_size}")
            results['passed'] += 1
            
        except Exception as e:
            print(f"❌ FAIL - Error: {str(e)[:100]}")
            results['failed'] += 1
            results['errors'].append({
                'query': query,
                'category': category,
                'error': str(e)
            })
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Total Tests: {results['total']}")
    print(f"Passed: {results['passed']} ({results['passed']/results['total']*100:.1f}%)")
    print(f"Failed: {results['failed']} ({results['failed']/results['total']*100:.1f}%)")
    
    if results['errors']:
        print(f"\nFailed Tests:")
        for err in results['errors']:
            print(f"  - {err['category']}: {err['query']}")
            print(f"    Error: {err['error'][:100]}")
    
    print("="*80)
    
    # Success criteria: 80% pass rate
    pass_rate = results['passed'] / results['total']
    
    if pass_rate >= 0.8:
        print("\n🎉 SUCCESS! System is working well (>80% pass rate)")
        return True
    else:
        print(f"\n⚠️  WARNING! System needs improvement ({pass_rate*100:.1f}% pass rate)")
        return False

if __name__ == "__main__":
    success = test_system()
    sys.exit(0 if success else 1)