import sys
sys.path.append('src')

from typing import List
import pandas as pd
from analytics.engine import AnalyticsEngine
from analytics.sql_generator import SQLGenerator
from nlp.conversation_manager import ConversationManager
from explainability.formatter import ResponseFormatter
import time


class InsightXSystem:
    def __init__(self, csv_path):
        print("\n" + "="*60)
        print("INITIALIZING INSIGHTX SYSTEM")
        print("="*60)
        
        self.analytics = AnalyticsEngine(csv_path)
        self.sql_generator = SQLGenerator()
        self.conversation_manager = ConversationManager()
        self.formatter = ResponseFormatter()
        
        # Track current session
        self.current_session = None
        self._last_caveats = "" 

        print("\n✓ All components initialized!")
        print("="*60)
    
    def ask(self, question: str, show_tier2: bool = False, show_tier3: bool = False):
        """
        Main entry point with full explainability
        
        Args:
            question: User's question
            show_tier2: Show detailed explanation
            show_tier3: Show technical details
        """
        
        print(f"\n📝 Question: {question}")
        
        # Process with conversation context
        enhanced, self.current_session = self.conversation_manager.process_query(
            question,
            self.current_session
        )
        
        # Show context
        context = self.conversation_manager.get_context_summary(self.current_session)
        if context != "No active context":
            print(f"🔗 Context: {context}")
        
        print(f"✓ Parsed (confidence: {enhanced.confidence:.2f})")
        
        # Generate SQL
        sql = self.sql_generator.generate(enhanced)
        print(f"✓ Generated SQL")
        
        # Execute query with timing
        start_time = time.time()
        result = self.analytics.query(sql)
        execution_time_ms = (time.time() - start_time) * 1000
        print(f"✓ Query executed ({len(result)} rows, {execution_time_ms:.1f}ms)")
        
        # Get baseline for comparison
        baseline = self._get_baseline(enhanced.metrics)
        
        # Format response with full explainability
        response = self.formatter.format(
            query=question,
            result=result,
            confidence=enhanced.confidence,
            sql=sql,
            filters=enhanced.filters,
            metrics=enhanced.metrics,
            execution_time_ms=execution_time_ms,
            baseline=baseline,
            analytics_engine=self.analytics
        )
        
        print(f"✓ Response formatted")
        
        # Display Tier 1 (always)
        print(f"\n{'='*60}")
        print(f"ANSWER")
        print(f"{'='*60}")
        print(response.tier1_text)
        print(f"\nConfidence: {response.confidence}")
        print(f"Sample Size: {response.sample_size:,} records")
        
        # Display context comparison
        if response.context_comparison and "No baseline" not in response.context_comparison:
            print(f"\n{response.context_comparison}")
        
        # Display caveats
        if (
            response.caveats
            and "No significant" not in response.caveats
            and response.caveats != self._last_caveats
        ):
            print(f"\n{response.caveats}")
            self._last_caveats = response.caveats
        
        # Display hypotheses if relevant
        if "why" in question.lower() and response.hypotheses and "No specific" not in response.hypotheses:
            print(f"\n{response.hypotheses}")
            return response
        
        print(f"{'='*60}")
        
        # Show Tier 2 if requested
        if show_tier2:
            print(f"\n{'='*60}")
            print(f"DETAILED EXPLANATION (Tier 2)")
            print(f"{'='*60}")
            print(response.tier2_details)
        else:
            print(f"\n💡 Tip: Add show_tier2=True to see detailed explanation")
        
        # Show Tier 3 if requested
        if show_tier3:
            print(f"\n{'='*60}")
            print(f"TECHNICAL DETAILS (Tier 3)")
            print(f"{'='*60}")
            print(response.tier3_technical)
        else:
            print(f"💡 Tip: Add show_tier3=True to see SQL and technical details")
        
        return response
    
    def _get_baseline(self, metrics: List[str]) -> pd.DataFrame:
        """Get baseline data for comparison"""
        
        if not metrics:
            return None
        
        # Use precomputed overall stats as baseline
        overall = self.analytics.get_precomputed('overall')
        
        if overall:
            import pandas as pd
            baseline_data = {}
            
            for metric in metrics:
                if metric == 'avg_amount':
                    baseline_data['avg_amount'] = overall['avg_amount']
                elif metric == 'success_rate':
                    baseline_data['success_rate'] = overall['success_rate']
                elif metric == 'failure_rate':
                    baseline_data['failure_rate'] = overall['failure_rate']
                elif metric == 'fraud_flag_rate':
                    baseline_data['fraud_flag_rate'] = overall['fraud_flag_rate']
            
            if baseline_data:
                return pd.DataFrame([baseline_data])
        
        return None
    
    def start_fresh(self):
        """Start a fresh conversation"""
        if self.current_session:
            self.conversation_manager.clear_context(self.current_session)
            print("✓ Context cleared - starting fresh!")


# ============================================================================
# DEMO
# ============================================================================
if __name__ == "__main__":
    system = InsightXSystem('../data/upi_transactions_2024.csv')
    
    print("\n\n" + "="*60)
    print("DAY 4 DEMO: FULL EXPLAINABILITY")
    print("="*60)
    
    # Demo 1: Basic query with all tiers
    print("\n📌 DEMO 1: Basic Query")
    print("-" * 60)
    system.ask("What is the average P2M transaction amount?", show_tier2=True, show_tier3=True)
    
    # Demo 2: Why question with hypotheses
    print("\n\n📌 DEMO 2: 'Why' Question")
    print("-" * 60)
    system.ask("Why is the P2M amount higher?")
    
    # Demo 3: Multi-turn with context
    print("\n\n📌 DEMO 3: Multi-turn Conversation")
    print("-" * 60)
    system.ask("Show me P2P transactions")
    system.ask("What about weekends?")
    system.ask("Why might weekend transactions differ?")
    
    print("\n" + "="*60)
    print("✓ DAY 4 DEMO COMPLETE!")
    print("="*60)