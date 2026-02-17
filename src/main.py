import sys
sys.path.append('src')

from analytics.engine import AnalyticsEngine
from analytics.sql_generator import SQLGenerator
from nlp.conversation_manager import ConversationManager  
from explainability.formatter import ResponseFormatter

class InsightXSystem:
    def __init__(self, csv_path):
        print("\n" + "="*60)
        print("INITIALIZING INSIGHTX SYSTEM")
        print("="*60)
        
        self.analytics = AnalyticsEngine(csv_path)
        self.sql_generator = SQLGenerator()
        self.conversation_manager = ConversationManager()  # NEW
        self.formatter = ResponseFormatter()
        
        # Track current session
        self.current_session = None  # NEW
        
        print("\n✓ All components initialized!")
        print("="*60)
    
    def ask(self, question: str):
        """Main entry point with conversation context"""
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
        
        # Execute query
        result = self.analytics.query(sql)
        print(f"✓ Query executed ({len(result)} rows)")
        
        # Format response
        response = self.formatter.format(question, result, enhanced.confidence)
        print(f"✓ Response formatted")
        
        # Display
        print(f"\n{'-'*60}")
        print(f"ANSWER:")
        print(f"{'-'*60}")
        print(response.tier1_text)
        print(f"\nConfidence: {response.confidence}")
        print(f"Based on: {response.sample_size} records")
        print(f"{'-'*60}")
        
        return response
    
    def start_fresh(self):
        """Start a fresh conversation"""
        if self.current_session:
            self.conversation_manager.clear_context(self.current_session)
            print("✓ Context cleared - starting fresh!")


# ============================================================================
# MULTI-TURN CONVERSATION TEST
# ============================================================================
if __name__ == "__main__":
    system = InsightXSystem('data/upi_transactions_2024.csv')
    
    print("\n\n" + "="*60)
    print("TESTING MULTI-TURN CONVERSATIONS")
    print("="*60)
    
    # Conversation 1: With context
    print("\n📞 CONVERSATION 1: Context Retention")
    print("-" * 60)
    
    system.ask("Show me P2P transactions")
    system.ask("What about weekends?")
    system.ask("Break down by age group")
    
    # Conversation 2: Fresh start
    print("\n📞 CONVERSATION 2: Fresh Start")
    print("-" * 60)
    
    system.ask("Start fresh")
    system.ask("Compare failure rates by device type")
    
    print("\n" + "="*60)
    print("✓ MULTI-TURN CONVERSATION TEST COMPLETE!")
    print("="*60)