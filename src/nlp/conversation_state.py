"""
Conversation State Management
Stores conversation history and context
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from parser import ParsedQuery

@dataclass
class ConversationTurn:
    """Single turn in a conversation"""
    turn_number: int
    query: str
    parsed_query: ParsedQuery
    response_summary: str  # Brief summary of answer
    timestamp: datetime
    filters_applied: Dict
    entities_mentioned: Dict


@dataclass
class ConversationState:
    """Complete conversation state"""
    session_id: str
    turns: List[ConversationTurn] = field(default_factory=list)
    active_filters: Dict = field(default_factory=dict)
    active_entities: Dict = field(default_factory=dict)
    last_dimensions: List[str] = field(default_factory=list)
    last_metric: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    
    def add_turn(self, query: str, parsed: ParsedQuery, response_summary: str = ""):
        """Add a turn to conversation history"""
        turn = ConversationTurn(
            turn_number=len(self.turns) + 1,
            query=query,
            parsed_query=parsed,
            response_summary=response_summary,
            timestamp=datetime.now(),
            filters_applied=parsed.filters.copy(),
            entities_mentioned=self._extract_entities(parsed)
        )
        
        self.turns.append(turn)
        self.last_activity = datetime.now()
        
        # Update active context
        self._update_active_context(parsed)
    
    def _extract_entities(self, parsed: ParsedQuery) -> Dict:
        """Extract entities from parsed query"""
        entities = {}
        
        # Extract from filters
        for key, value in parsed.filters.items():
            entities[key] = value
        
        # Extract dimensions
        if parsed.dimensions:
            entities['dimensions'] = parsed.dimensions
        
        # Extract metrics
        if parsed.metrics:
            entities['metrics'] = parsed.metrics
        
        return entities
    
    def _update_active_context(self, parsed: ParsedQuery):
        """Update active context with new information"""
        
        # Merge filters (new filters override old ones)
        for key, value in parsed.filters.items():
            self.active_filters[key] = value
        
        # Update entities
        for key, value in self._extract_entities(parsed).items():
            self.active_entities[key] = value
        
        # Track last dimensions
        if parsed.dimensions:
            self.last_dimensions = parsed.dimensions
        
        # Track last metric
        if parsed.metrics:
            self.last_metric = parsed.metrics[0]
    
    def get_last_turn(self) -> Optional[ConversationTurn]:
        """Get the most recent turn"""
        return self.turns[-1] if self.turns else None
    
    def get_last_n_turns(self, n: int = 5) -> List[ConversationTurn]:
        """Get last N turns"""
        return self.turns[-n:] if len(self.turns) >= n else self.turns
    
    def clear_context(self):
        """Clear active context (but keep history)"""
        self.active_filters = {}
        self.active_entities = {}
        self.last_dimensions = []
        self.last_metric = None
    
    def is_expired(self, timeout_minutes: int = 30) -> bool:
        """Check if session has expired"""
        elapsed = datetime.now() - self.last_activity
        return elapsed > timedelta(minutes=timeout_minutes)
    
    def get_context_summary(self) -> str:
        """Get human-readable context summary"""
        parts = []
        
        if self.active_filters:
            filter_str = ", ".join([f"{k}={v}" for k, v in self.active_filters.items()])
            parts.append(f"Filters: {filter_str}")
        
        if self.last_dimensions:
            parts.append(f"Grouping by: {', '.join(self.last_dimensions)}")
        
        if self.last_metric:
            parts.append(f"Metric: {self.last_metric}")
        
        return " | ".join(parts) if parts else "No active context"


# ============================================================================
# TESTING
# ============================================================================
if __name__ == "__main__":
    from parser import QueryParser, QueryIntent
    
    print("\n" + "="*80)
    print("CONVERSATION STATE TEST")
    print("="*80)
    
    # Create state
    state = ConversationState(session_id="test-123")
    parser = QueryParser()
    
    # Simulate conversation
    conversation = [
        "Show me P2P transactions",
        "What about weekends?",
        "Break down by age group"
    ]
    
    for i, query in enumerate(conversation, 1):
        print(f"\nTurn {i}: {query}")
        
        # Parse query
        parsed = parser.parse(query)
        
        # Add to state
        state.add_turn(query, parsed, f"Showing results for turn {i}")
        
        # Show context
        print(f"Active Context: {state.get_context_summary()}")
        print(f"Active Filters: {state.active_filters}")
    
    print("\n" + "="*80)
    print("CONVERSATION HISTORY")
    print("="*80)
    
    for turn in state.turns:
        print(f"\nTurn {turn.turn_number}: {turn.query}")
        print(f"  Filters: {turn.filters_applied}")
        print(f"  Timestamp: {turn.timestamp.strftime('%H:%M:%S')}")
    
    print("\n" + "="*80)
    print("✓ CONVERSATION STATE TEST COMPLETE")
    print("="*80)