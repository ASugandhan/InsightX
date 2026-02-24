"""
Comprehensive Multi-Turn Conversation Tests
Tests 5+ turn conversations with various scenarios
"""

import sys
sys.path.append('src')

from main import InsightXSystem


def test_conversation(name: str, turns: list, system: InsightXSystem):
    """Test a single conversation scenario"""
    
    print("\n" + "="*80)
    print(f"TEST: {name}")
    print("="*80)
    
    results = []
    
    for i, (query, expected_filters) in enumerate(turns, 1):
        print(f"\n[Turn {i}/{len(turns)}] {query}")
        print("-" * 80)
        
        try:
            response = system.ask(query)
            
            # Get current context
            context = system.conversation_manager.get_context_summary(system.current_session)
            
            # Validate
            success = True
            notes = []
            
            if expected_filters:
                actual_filters = system.conversation_manager.sessions[system.current_session].active_filters
                
                for key, value in expected_filters.items():
                    if key in actual_filters:
                        if actual_filters[key] == value:
                            notes.append(f"✅ {key}={value}")
                        else:
                            notes.append(f"❌ {key}: expected {value}, got {actual_filters[key]}")
                            success = False
                    else:
                        notes.append(f"⚠️  Missing filter: {key}")
            
            results.append({
                'turn': i,
                'query': query,
                'success': success,
                'notes': notes
            })
            
            print(f"Status: {'✅ PASS' if success else '❌ FAIL'}")
            for note in notes:
                print(f"  {note}")
        
        except Exception as e:
            print(f"❌ ERROR: {e}")
            results.append({
                'turn': i,
                'query': query,
                'success': False,
                'notes': [f"Error: {str(e)}"]
            })
    
    # Summary
    passed = sum(1 for r in results if r['success'])
    print(f"\n{'='*80}")
    print(f"SUMMARY: {passed}/{len(results)} turns passed")
    print(f"{'='*80}")
    
    return passed == len(results)


def run_all_tests():
    """Run all conversation test scenarios"""
    
    print("\n" + "="*80)
    print("COMPREHENSIVE CONVERSATION TESTS")
    print("="*80)
    
    system = InsightXSystem('data/upi_transactions_2024.csv')
    
    test_scenarios = []
    
    # ========================================================================
    # SCENARIO 1: Basic Context Retention
    # ========================================================================
    scenario1 = [
        ("Show me P2P transactions", {'transaction_type': 'P2P'}),
        ("What about weekends?", {'transaction_type': 'P2P', 'is_weekend': 1}),
        ("Break down by age group", {'transaction_type': 'P2P', 'is_weekend': 1}),
    ]
    test_scenarios.append(("Basic Context Retention", scenario1))
    
    # ========================================================================
    # SCENARIO 2: Anaphora Resolution
    # ========================================================================
    system.start_fresh()
    scenario2 = [
        ("Show me Android transactions", {'device_type': 'Android'}),
        ("What is the average amount for it?", {'device_type': 'Android'}),
        ("Compare that with iOS", None),  # Should switch to iOS
    ]
    test_scenarios.append(("Anaphora Resolution", scenario2))
    
    # ========================================================================
    # SCENARIO 3: Context Reset
    # ========================================================================
    system.start_fresh()
    scenario3 = [
        ("Show me food category", {'merchant_category': 'Food'}),
        ("What about shopping?", {'merchant_category': 'Shopping'}),
        ("Start fresh", {}),
        ("Show me P2P", {'transaction_type': 'P2P'}),
    ]
    test_scenarios.append(("Context Reset", scenario3))
    
    # ========================================================================
    # SCENARIO 4: Progressive Filtering
    # ========================================================================
    system.start_fresh()
    scenario4 = [
        ("Show me all transactions", {}),
        ("Filter to Maharashtra", {'sender_state': 'Maharashtra'}),
        ("Only P2M", {'sender_state': 'Maharashtra', 'transaction_type': 'P2M'}),
        ("What about weekends?", {'sender_state': 'Maharashtra', 'transaction_type': 'P2M', 'is_weekend': 1}),
        ("18-25 age group only", {'sender_state': 'Maharashtra', 'transaction_type': 'P2M', 'is_weekend': 1, 'sender_age_group': '18-25'}),
    ]
    test_scenarios.append(("Progressive Filtering (5 turns)", scenario4))
    
    # ========================================================================
    # SCENARIO 5: Dimension Changes
    # ========================================================================
    system.start_fresh()
    scenario5 = [
        ("Show me P2P transactions", {'transaction_type': 'P2P'}),
        ("Break down by age", {'transaction_type': 'P2P'}),
        ("Now by device type", {'transaction_type': 'P2P'}),
        ("Actually by state", {'transaction_type': 'P2P'}),
    ]
    test_scenarios.append(("Dimension Changes", scenario5))
    
    # ========================================================================
    # SCENARIO 6: Complex Follow-ups
    # ========================================================================
    system.start_fresh()
    scenario6 = [
        ("What is the fraud flag rate?", {}),
        ("For 18-25 age group", {'sender_age_group': '18-25'}),
        ("On Android devices", {'sender_age_group': '18-25', 'device_type': 'Android'}),
        ("During weekends", {'sender_age_group': '18-25', 'device_type': 'Android', 'is_weekend': 1}),
        ("In Maharashtra", {'sender_age_group': '18-25', 'device_type': 'Android', 'is_weekend': 1, 'sender_state': 'Maharashtra'}),
        ("For food transactions", {'sender_age_group': '18-25', 'device_type': 'Android', 'is_weekend': 1, 'sender_state': 'Maharashtra', 'merchant_category': 'Food'}),
    ]
    test_scenarios.append(("Complex Follow-ups (6 turns)", scenario6))
    
    # Run all scenarios
    passed_scenarios = 0
    
    for name, turns in test_scenarios:
        if test_conversation(name, turns, system):
            passed_scenarios += 1
        system.start_fresh()
    
    # Final summary
    print("\n" + "="*80)
    print("FINAL RESULTS")
    print("="*80)
    print(f"Scenarios Passed: {passed_scenarios}/{len(test_scenarios)}")
    
    if passed_scenarios == len(test_scenarios):
        print("\n🎉 ALL CONVERSATION TESTS PASSED!")
        print("✅ Context retention working")
        print("✅ Anaphora resolution working")
        print("✅ Progressive filtering working")
        print("✅ Ready for Day 4!")
    else:
        print(f"\n⚠️  {len(test_scenarios) - passed_scenarios} scenarios failed")
        print("Review failures above")
    
    print("="*80)
    
    return passed_scenarios == len(test_scenarios)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)