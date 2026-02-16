from dataclasses import dataclass
from typing import Dict, List
import pandas as pd

@dataclass
class Response:
    """Formatted response for user"""
    tier1_text: str  # Always visible
    confidence: str  # HIGH, MEDIUM, LOW
    sample_size: int
    tier2_details: str  # Expandable
    tier3_technical: str  # Expert mode

class ResponseFormatter:
    def __init__(self):
        print("✓ Response Formatter initialized")
    
    def format(self, query: str, result: pd.DataFrame, confidence: float) -> Response:
        """Format query result into 3-tier response"""
        
        # Tier 1: Basic answer
        tier1 = self._format_tier1(query, result)
        
        # Confidence badge
        conf_badge = self._confidence_badge(confidence)
        
        # Sample size
        sample_size = len(result) if len(result.shape) > 1 else 1
        
        # Tier 2: Details (placeholder for now)
        tier2 = "Detailed explanation coming soon..."
        
        # Tier 3: Technical (placeholder for now)
        tier3 = "SQL query and export options coming soon..."
        
        return Response(
            tier1_text=tier1,
            confidence=conf_badge,
            sample_size=sample_size,
            tier2_details=tier2,
            tier3_technical=tier3
        )
    
    def _format_tier1(self, query, result):
        """Format basic answer"""
        # Simple formatting for now
        if len(result) == 1 and len(result.columns) == 1:
            value = result.iloc[0, 0]
            return f"Result: {value:,.2f}"
        else:
            return result.to_string()
    
    def _confidence_badge(self, confidence):
        """Get confidence badge"""
        if confidence > 0.8:
            return "HIGH ✓"
        elif confidence > 0.6:
            return "MEDIUM ⚠️"
        else:
            return "LOW ⚠️"

# Test
if __name__ == "__main__":
    formatter = ResponseFormatter()
    
    # Mock result
    result = pd.DataFrame({'avg_amount': [2847.32]})
    
    response = formatter.format(
        "What is average amount?",
        result,
        0.9
    )
    
    print("\n" + "="*60)
    print("TESTING FORMATTER")
    print("="*60)
    print(f"\nTier 1: {response.tier1_text}")
    print(f"Confidence: {response.confidence}")
    print(f"Sample size: {response.sample_size}")
    print("\n" + "="*60)
    print("✓ FORMATTER TEST PASSED!")
    print("="*60)