"""
Anti-Hallucination Test Suite
Tests that LLM doesn't hallucinate columns, metrics, or values
"""

import sys
sys.path.append('src')

from nlp.llm_parser import LLMParser
from nlp.schema_validator import SchemaValidator

def test_anti_hallucination():
    parser = LLMParser()
    validator = SchemaValidator()
    
    print("=" * 70)
    print("  🛡️ ANTI-HALLUCINATION TEST SUITE")
    print("=" * 70)
    print()
    
    # Test cases designed to trick the LLM into hallucinating
    test_cases = [
        {
            "query": "Show me revenue by customer segments",
            "should_hallucinate": True,
            "reason": "No 'revenue' or 'customer_segments' in schema"
        },
        {
            "query": "What's the conversion rate for Visa cards?",
            "should_hallucinate": True,
            "reason": "No 'conversion_rate' or 'Visa' in schema"
        },
        {
            "query": "Show transaction count by age group",
            "should_hallucinate": False,
            "reason": "Valid query - both fields exist"
        },
        {
            "query": "Average transaction amount for Android users",
            "should_hallucinate": False,
            "reason": "Valid query - all fields exist"
        },
        {
            "query": "Show me profit margins by region",
            "should_hallucinate": True,
            "reason": "No 'profit' or 'region' in schema"
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: {test['query']}")
        print(f"  Expected: {'Should detect as unavailable' if test['should_hallucinate'] else 'Should parse normally'}")
        
        try:
            result = parser.parse(test['query'])
            validation = validator.validate_parsed_query(result)
            
            print(f"  Intent: {result.intent}")
            print(f"  Confidence: {result.confidence:.2f}")
            print(f"  Schema Valid: {validation['is_valid']}")
            
            if validation['issues']:
                print(f"  ⚠️ Issues: {validation['issues']}")
            
            # Check if we correctly detected hallucination
            if test['should_hallucinate']:
                if not validation['is_valid'] or result.confidence < 0.5:
                    print("  ✅ PASS - Correctly rejected/flagged")
                    passed += 1
                else:
                    print("  ❌ FAIL - Should have rejected this")
                    failed += 1
            else:
                if validation['is_valid'] and result.confidence > 0.5:
                    print("  ✅ PASS - Correctly accepted")
                    passed += 1
                else:
                    print("  ❌ FAIL - Should have accepted this")
                    failed += 1
        
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            failed += 1
        
        print()
    
    print("=" * 70)
    print(f"  RESULTS: {passed} passed, {failed} failed")
    print(f"  Success Rate: {(passed/(passed+failed)*100):.1f}%")
    print("=" * 70)

if __name__ == "__main__":
    test_anti_hallucination()
