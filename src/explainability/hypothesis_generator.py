"""
Hypothesis Generator
Generates plausible explanations for "why" questions
"""

import pandas as pd
from typing import List, Dict, Tuple


class HypothesisGenerator:
    """Generate hypotheses for unexpected patterns"""
    
    def __init__(self):
        # Known patterns and their explanations
        self.pattern_library = self._build_pattern_library()
        print("✓ Hypothesis Generator initialized")
    
    def generate_hypotheses(self,
                           query: str,
                           result: pd.DataFrame,
                           filters: Dict,
                           metrics: List[str]) -> List[Dict]:
        """
        Generate hypotheses to explain results
        
        Returns:
            List of hypothesis dicts with 'hypothesis', 'confidence', 'evidence'
        """
        
        hypotheses = []
        
        # Detect pattern type
        pattern = self._detect_pattern(result, filters, metrics)
        
        if pattern == 'high_fraud_rate':
            hypotheses.extend(self._explain_high_fraud_rate(result, filters))
        
        elif pattern == 'high_failure_rate':
            hypotheses.extend(self._explain_high_failure_rate(result, filters))
        
        elif pattern == 'high_amount':
            hypotheses.extend(self._explain_high_amount(result, filters))
        
        elif pattern == 'low_amount':
            hypotheses.extend(self._explain_low_amount(result, filters))
        
        elif pattern == 'temporal_spike':
            hypotheses.extend(self._explain_temporal_spike(result, filters))
        
        elif pattern == 'demographic_difference':
            hypotheses.extend(self._explain_demographic_difference(result, filters))
        
        else:
            # Generic hypotheses
            hypotheses.extend(self._generate_generic_hypotheses(result, filters, metrics))
        
        # Rank by confidence
        hypotheses.sort(key=lambda h: h['confidence'], reverse=True)
        
        return hypotheses[:5]  # Top 5 hypotheses
    
    def _detect_pattern(self, result: pd.DataFrame, filters: Dict, metrics: List[str]) -> str:
        """Detect what kind of pattern we're explaining"""
        
        # Check fraud rate
        if 'fraud_flag_rate' in result.columns:
            rate = result['fraud_flag_rate'].iloc[0] if len(result) == 1 else result['fraud_flag_rate'].mean()
            if rate > 15:
                return 'high_fraud_rate'
        
        # Check failure rate
        if 'failure_rate' in result.columns:
            rate = result['failure_rate'].iloc[0] if len(result) == 1 else result['failure_rate'].mean()
            if rate > 10:
                return 'high_failure_rate'
        
        # Check amount
        if 'avg_amount' in result.columns:
            amount = result['avg_amount'].iloc[0] if len(result) == 1 else result['avg_amount'].mean()
            if amount > 3000:
                return 'high_amount'
            elif amount < 500:
                return 'low_amount'
        
        # Check temporal patterns
        if 'hour_of_day' in result.columns:
            return 'temporal_spike'
        
        # Check demographic differences
        if 'sender_age_group' in result.columns or 'device_type' in result.columns:
            return 'demographic_difference'
        
        return 'unknown'
    
    def _explain_high_fraud_rate(self, result: pd.DataFrame, filters: Dict) -> List[Dict]:
        """Explain high fraud flag rate"""
        
        hypotheses = []
        
        # Hypothesis 1: Transaction type vulnerability
        if filters.get('transaction_type') == 'P2M':
            hypotheses.append({
                'hypothesis': "P2M transactions have higher fraud risk due to merchant impersonation",
                'confidence': 0.85,
                'evidence': "P2M allows fraudsters to pose as legitimate merchants",
                'supporting_factors': [
                    "One-way transactions (no refunds)",
                    "Merchant verification gaps",
                    "Higher average amounts attract fraudsters"
                ]
            })
        
        # Hypothesis 2: Age group vulnerability
        if filters.get('sender_age_group') == '18-25':
            hypotheses.append({
                'hypothesis': "18-25 age group shows higher fraud due to less payment experience",
                'confidence': 0.75,
                'evidence': "Younger users may be less cautious with payment security",
                'supporting_factors': [
                    "Less experience spotting scams",
                    "Higher adoption of new payment methods",
                    "Greater likelihood of sharing payment details"
                ]
            })
        
        # Hypothesis 3: Network vulnerability
        if filters.get('network_type') in ['3G', 'WiFi']:
            hypotheses.append({
                'hypothesis': "Public WiFi or slower networks increase fraud risk",
                'confidence': 0.70,
                'evidence': "Unsecured networks expose transaction data",
                'supporting_factors': [
                    "Man-in-the-middle attacks possible",
                    "Session hijacking risk",
                    "Timeout-related security issues"
                ]
            })
        
        return hypotheses
    
    def _explain_high_failure_rate(self, result: pd.DataFrame, filters: Dict) -> List[Dict]:
        """Explain high failure rate"""
        
        hypotheses = []
        
        # Device-related
        if filters.get('device_type') == 'Web':
            hypotheses.append({
                'hypothesis': "Web transactions fail more due to timeout and session issues",
                'confidence': 0.80,
                'evidence': "Web browsers have stricter timeout policies",
                'supporting_factors': [
                    "Browser-based payment flows more complex",
                    "More steps = more failure points",
                    "User abandonment during process"
                ]
            })
        
        # Network-related
        if filters.get('network_type') == '3G':
            hypotheses.append({
                'hypothesis': "Slower 3G networks cause transaction timeouts",
                'confidence': 0.85,
                'evidence': "3G latency exceeds payment gateway timeout thresholds",
                'supporting_factors': [
                    "High latency (>200ms typical)",
                    "Packet loss more common",
                    "Connection drops during transaction"
                ]
            })
        
        return hypotheses
    
    def _explain_high_amount(self, result: pd.DataFrame, filters: Dict) -> List[Dict]:
        """Explain high transaction amounts"""
        
        hypotheses = []
        
        # Merchant category
        if filters.get('merchant_category') in ['Food', 'Shopping']:
            hypotheses.append({
                'hypothesis': "Food and Shopping categories have higher amounts due to bulk purchases",
                'confidence': 0.80,
                'evidence': "Users often buy groceries or multiple items in single transaction",
                'supporting_factors': [
                    "Family-size purchases common",
                    "Multi-item cart checkouts",
                    "Premium product selection"
                ]
            })
        
        # Age group
        if filters.get('sender_age_group') in ['36-45', '46-55']:
            hypotheses.append({
                'hypothesis': "Older age groups have higher disposable income and spending capacity",
                'confidence': 0.75,
                'evidence': "Career professionals in peak earning years",
                'supporting_factors': [
                    "Established careers with higher salaries",
                    "Family expenses (education, healthcare)",
                    "Lower financial risk aversion"
                ]
            })
        
        return hypotheses
    
    def _explain_low_amount(self, result: pd.DataFrame, filters: Dict) -> List[Dict]:
        """Explain low transaction amounts"""
        
        hypotheses = []
        
        # Bill payments and recharges
        if filters.get('transaction_type') in ['Bill Payment', 'Recharge']:
            hypotheses.append({
                'hypothesis': "Bill payments and recharges are typically fixed small amounts",
                'confidence': 0.90,
                'evidence': "Utility bills and mobile recharges have standard denominations",
                'supporting_factors': [
                    "Prepaid mobile plans (₹100-500)",
                    "Electricity/water bills (₹300-800)",
                    "DTH recharges (₹200-400)"
                ]
            })
        
        return hypotheses
    
    def _explain_temporal_spike(self, result: pd.DataFrame, filters: Dict) -> List[Dict]:
        """Explain temporal patterns"""
        
        hypotheses = []
        
        # Peak hours (likely in result)
        hypotheses.append({
            'hypothesis': "Peak transaction hours align with meal times and commute periods",
            'confidence': 0.85,
            'evidence': "Food delivery and transport dominate peak hours",
            'supporting_factors': [
                "Lunch hours (12-2 PM)",
                "Evening commute (6-8 PM)",
                "Dinner delivery (8-10 PM)"
            ]
        })
        
        return hypotheses
    
    def _explain_demographic_difference(self, result: pd.DataFrame, filters: Dict) -> List[Dict]:
        """Explain demographic differences"""
        
        hypotheses = []
        
        hypotheses.append({
            'hypothesis': "Different demographics show distinct payment behavior patterns",
            'confidence': 0.75,
            'evidence': "Age, location, and device choice correlate with spending habits",
            'supporting_factors': [
                "Urban vs rural access to merchants",
                "Age-related tech adoption",
                "Device type indicates economic segment"
            ]
        })
        
        return hypotheses
    
    def _generate_generic_hypotheses(self, result: pd.DataFrame, filters: Dict, metrics: List[str]) -> List[Dict]:
        """Generate generic hypotheses when pattern is unclear"""
        
        return [{
            'hypothesis': "Multiple factors likely contribute to this pattern",
            'confidence': 0.50,
            'evidence': "Further segmentation needed to identify root causes",
            'supporting_factors': [
                "Consider breaking down by additional dimensions",
                "Time-series analysis may reveal trends",
                "Correlation with external factors (seasonality, events)"
            ]
        }]
    
    def _build_pattern_library(self) -> Dict:
        """Build library of known patterns and explanations"""
        # Could be extended with machine learning in production
        return {}
    
    def format_hypotheses(self, hypotheses: List[Dict]) -> str:
        """Format hypotheses for display"""
        
        if not hypotheses:
            return "💡 No specific hypotheses generated - pattern not recognized"
        
        lines = ["💡 POSSIBLE EXPLANATIONS:"]
        lines.append("\nRanked by confidence:\n")
        
        for i, hypo in enumerate(hypotheses, 1):
            confidence_bar = "█" * int(hypo['confidence'] * 10)
            confidence_pct = f"{hypo['confidence']*100:.0f}%"
            
            lines.append(f"{i}. {hypo['hypothesis']}")
            lines.append(f"   Confidence: {confidence_bar} {confidence_pct}")
            lines.append(f"   Evidence: {hypo['evidence']}")
            
            if 'supporting_factors' in hypo:
                lines.append("   Supporting factors:")
                for factor in hypo['supporting_factors']:
                    lines.append(f"     • {factor}")
            
            lines.append("")  # Blank line between hypotheses
        
        return "\n".join(lines)


# ============================================================================
# TESTING
# ============================================================================
if __name__ == "__main__":
    print("\n" + "="*80)
    print("HYPOTHESIS GENERATOR TEST")
    print("="*80)
    
    generator = HypothesisGenerator()
    
    # Test Case 1: High fraud rate for P2M
    print("\n--- Test 1: Why is fraud rate high for P2M? ---")
    result = pd.DataFrame({'fraud_flag_rate': [18.5]})
    
    hypotheses = generator.generate_hypotheses(
        query="Why is fraud rate high for P2M?",
        result=result,
        filters={'transaction_type': 'P2M'},
        metrics=['fraud_flag_rate']
    )
    
    print(generator.format_hypotheses(hypotheses))
    
    # Test Case 2: High failure rate on 3G
    print("\n--- Test 2: Why do 3G transactions fail more? ---")
    result = pd.DataFrame({'failure_rate': [15.2]})
    
    hypotheses = generator.generate_hypotheses(
        query="Why do 3G transactions fail more?",
        result=result,
        filters={'network_type': '3G'},
        metrics=['failure_rate']
    )
    
    print(generator.format_hypotheses(hypotheses))
    
    print("\n" + "="*80)
    print("✓ HYPOTHESIS GENERATOR TEST COMPLETE")
    print("="*80)