"""
Conversation Manager
Main orchestrator for multi-turn conversations
"""

import uuid
from typing import Dict, Optional
from datetime import datetime  # ✅ ADD (for staleness check)

from parser import ParsedQuery
from llm_parser import LLMParser
from conversation_state import ConversationState
from context_inheritor import ContextInheritor
from anaphora_resolver import AnaphoraResolver


class ConversationManager:
    """Manage multi-turn conversations with context"""
    
    def __init__(self):
        self.parser = LLMParser()
        self.inheritor = ContextInheritor()
        self.anaphora_resolver = AnaphoraResolver()  
        self.sessions: Dict[str, ConversationState] = {}
        self.default_timeout = 30 
        
        print("✓ Conversation Manager initialized")
    
    def process_query(self, query: str, session_id: Optional[str] = None) -> tuple[ParsedQuery, str]:
        """
        Process a query within a conversation context
        (with anaphora resolution + staleness warning)
        """
        
        # Handle special commands
        if self._is_special_command(query):
            return self._handle_special_command(query, session_id)
        
        # Get or create session
        if session_id is None:
            session_id = self._create_session()
        
        state = self._get_or_create_state(session_id)

        if state.turns:
            time_since_last = (datetime.now() - state.last_activity).seconds / 60
            if time_since_last > 15:  # 15 minutes
                print(
                    f"⚠️  Note: {time_since_last:.0f} minutes since last query. "
                    f"Context may be stale."
                )
        
        # Clean expired sessions
        self._cleanup_expired_sessions()
        
        # STEP 1: Resolve anaphora BEFORE parsing
        resolved_query = self.anaphora_resolver.resolve(query, state)
        
        if resolved_query != query:
            print(f"🔄 Resolved: '{query}' → '{resolved_query}'")
        
        # STEP 2: Parse resolved query
        parsed = self.parser.parse(resolved_query)
        
        # STEP 3: Enhance with context
        enhanced = self.inheritor.enhance_query(parsed, state)
        
        # STEP 4: Add to conversation history
        state.add_turn(query, enhanced)  # store original query
        
        return enhanced, session_id
    
    def get_context_summary(self, session_id: str) -> str:
        """Get summary of active context for a session"""
        if session_id in self.sessions:
            return self.sessions[session_id].get_context_summary()
        return "No active session"
    
    def clear_context(self, session_id: str):
        """Clear context for a session"""
        if session_id in self.sessions:
            self.sessions[session_id].clear_context()
    
    def end_session(self, session_id: str):
        """End a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def get_conversation_history(self, session_id: str, n: int = 5):
        """Get last N turns of conversation"""
        if session_id in self.sessions:
            return self.sessions[session_id].get_last_n_turns(n)
        return []
    
    # ---------------- Private helpers ----------------
    
    def _create_session(self) -> str:
        """Create new session"""
        session_id = str(uuid.uuid4())[:8]
        self.sessions[session_id] = ConversationState(session_id=session_id)
        return session_id
    
    def _get_or_create_state(self, session_id: str) -> ConversationState:
        """Get existing state or create new"""
        if session_id not in self.sessions:
            self.sessions[session_id] = ConversationState(session_id=session_id)
        return self.sessions[session_id]
    
    def _cleanup_expired_sessions(self):
        """Remove expired sessions"""
        expired = [
            sid for sid, state in self.sessions.items()
            if state.is_expired(self.default_timeout)
        ]
        for sid in expired:
            del self.sessions[sid]
    
    def _is_special_command(self, query: str) -> bool:
        """Check if query is a special command"""
        query_lower = query.lower().strip()
        commands = [
            "start fresh", "clear context", "reset",
            "new conversation", "forget everything", "start over"
        ]
        return any(cmd in query_lower for cmd in commands)
    
    def _handle_special_command(self, query: str, session_id: Optional[str]):
        """Handle special commands like 'start fresh'"""
        
        if session_id and session_id in self.sessions:
            self.sessions[session_id].clear_context()
        
        from parser import ParsedQuery, QueryIntent
        
        parsed = ParsedQuery(
            intent=QueryIntent.UNKNOWN,
            metrics=[],
            dimensions=[],
            filters={},
            original_query=query,
            confidence=1.0
        )
        
        return parsed, session_id or self._create_session()


# ============================================================================
# TESTING
# ============================================================================
if __name__ == "__main__":
    print("\n" + "="*80)
    print("CONVERSATION MANAGER TEST")
    print("="*80)
    
    manager = ConversationManager()
    session_id = None
    
    # Simulate conversation
    conversation = [
        "Show me P2P transactions",
        "What about weekends?",
        "Break down by age group",
        "Start fresh",
        "Show me failure rates by device"
    ]
    
    for i, query in enumerate(conversation, 1):
        print(f"\n{'='*80}")
        print(f"Turn {i}: {query}")
        print(f"{'='*80}")
        
        enhanced, session_id = manager.process_query(query, session_id)
        
        print(f"\nParsed Query:")
        print(f"  Intent: {enhanced.intent.value}")
        print(f"  Metrics: {enhanced.metrics}")
        print(f"  Dimensions: {enhanced.dimensions}")
        print(f"  Filters: {enhanced.filters}")
        print(f"  Confidence: {enhanced.confidence:.2f}")
        
        print(f"\nActive Context: {manager.get_context_summary(session_id)}")
    
    print("\n" + "="*80)
    print("CONVERSATION HISTORY")
    print("="*80)
    
    history = manager.get_conversation_history(session_id)
    for turn in history:
        print(f"\nTurn {turn.turn_number}: {turn.query}")
        print(f"  Filters: {turn.filters_applied}")
    
    print("\n" + "="*80)
    print("✓ CONVERSATION MANAGER TEST COMPLETE")
    print("="*80)
