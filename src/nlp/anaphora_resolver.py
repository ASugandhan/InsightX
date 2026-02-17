"""
Anaphora Resolution
Resolves pronouns like "it", "that", "them" to actual entities
"""

import re
from typing import Dict, List, Optional
from parser import ParsedQuery
from conversation_state import ConversationState


class AnaphoraResolver:
    """Resolve anaphoric references in queries"""
    
    def __init__(self):
        # Pronouns to resolve
        self.anaphora = {
            'singular': ['it', 'this', 'that'],
            'plural': ['them', 'those', 'these'],
            'possessive': ['its', 'their']
        }
        
        print("✓ Anaphora Resolver initialized")
    
    def resolve(self, query: str, state: ConversationState) -> str:
        """
        Resolve anaphoric references in query
        
        Args:
            query: Original query with pronouns
            state: Conversation state with history
        
        Returns:
            Query with pronouns replaced by entities
        """
        
        if not state.turns:
            # No history, nothing to resolve
            return query
        
        # Check if query contains anaphora
        if not self._contains_anaphora(query):
            return query
        
        # Get recent entities from history
        recent_entities = self._get_recent_entities(state, window=3)
        
        if not recent_entities:
            return query
        
        # Resolve each type of anaphora
        resolved = query
        resolved = self._resolve_singular(resolved, recent_entities)
        resolved = self._resolve_plural(resolved, recent_entities)
        resolved = self._resolve_possessive(resolved, recent_entities)
        
        return resolved
    
    def _contains_anaphora(self, query: str) -> bool:
        """Check if query contains anaphoric references"""
        query_lower = query.lower()
        
        all_anaphora = (
            self.anaphora['singular'] + 
            self.anaphora['plural'] + 
            self.anaphora['possessive']
        )
        
        # Check for standalone pronouns (not part of other words)
        pattern = r'\b(' + '|'.join(all_anaphora) + r')\b'
        return bool(re.search(pattern, query_lower))
    
    def _get_recent_entities(self, state: ConversationState, window: int = 3) -> Dict:
        """
        Get entities from recent conversation turns
        
        Returns most recent entity of each type
        """
        recent_turns = state.get_last_n_turns(window)
        
        entities = {
            'transaction_type': None,
            'merchant_category': None,
            'age_group': None,
            'device_type': None,
            'state': None,
            'bank': None,
            'dimension': None
        }
        
        # Walk backwards through turns to get most recent of each type
        for turn in reversed(recent_turns):
            filters = turn.filters_applied
            
            if 'transaction_type' in filters and entities['transaction_type'] is None:
                entities['transaction_type'] = filters['transaction_type']
            
            if 'merchant_category' in filters and entities['merchant_category'] is None:
                entities['merchant_category'] = filters['merchant_category']
            
            if 'sender_age_group' in filters and entities['age_group'] is None:
                entities['age_group'] = filters['sender_age_group']
            
            if 'device_type' in filters and entities['device_type'] is None:
                entities['device_type'] = filters['device_type']
            
            if 'sender_state' in filters and entities['state'] is None:
                entities['state'] = filters['sender_state']
            
            if 'sender_bank' in filters and entities['bank'] is None:
                entities['bank'] = filters['sender_bank']
            
            if turn.parsed_query.dimensions and entities['dimension'] is None:
                entities['dimension'] = turn.parsed_query.dimensions[0]
        
        # Remove None values
        return {k: v for k, v in entities.items() if v is not None}
    
    def _resolve_singular(self, query: str, entities: Dict) -> str:
        """Resolve singular pronouns (it, this, that)"""
        
        query_lower = query.lower()
        
        for pronoun in self.anaphora['singular']:
            pattern = r'\b' + pronoun + r'\b'
            
            if re.search(pattern, query_lower):
                # Try to find the most relevant entity to replace
                replacement = self._find_best_entity(query_lower, entities)
                
                if replacement:
                    # Replace pronoun with entity
                    query = re.sub(pattern, replacement, query, flags=re.IGNORECASE)
                    break
        
        return query
    
    def _resolve_plural(self, query: str, entities: Dict) -> str:
        """Resolve plural pronouns (them, those, these)"""
        
        query_lower = query.lower()
        
        for pronoun in self.anaphora['plural']:
            pattern = r'\b' + pronoun + r'\b'
            
            if re.search(pattern, query_lower):
                # For plural, we might need multiple entities
                # For now, use the primary entity
                replacement = self._find_best_entity(query_lower, entities)
                
                if replacement:
                    query = re.sub(pattern, replacement, query, flags=re.IGNORECASE)
                    break
        
        return query
    
    def _resolve_possessive(self, query: str, entities: Dict) -> str:
        """Resolve possessive pronouns (its, their)"""
        
        query_lower = query.lower()
        
        for pronoun in self.anaphora['possessive']:
            pattern = r'\b' + pronoun + r'\b'
            
            if re.search(pattern, query_lower):
                replacement = self._find_best_entity(query_lower, entities)
                
                if replacement:
                    # For possessive, we need to adjust the replacement
                    # "its transactions" → "P2P transactions"
                    query = re.sub(pattern, replacement + "'s", query, flags=re.IGNORECASE)
                    break
        
        return query
    
    def _find_best_entity(self, query: str, entities: Dict) -> Optional[str]:
        """
        Find the most contextually relevant entity
        
        Uses heuristics based on query keywords
        """
        
        # If query mentions specific domain, prioritize that entity type
        if 'transaction' in query and 'transaction_type' in entities:
            return entities['transaction_type']
        
        if 'category' in query and 'merchant_category' in entities:
            return entities['merchant_category']
        
        if 'age' in query and 'age_group' in entities:
            return entities['age_group']
        
        if 'device' in query and 'device_type' in entities:
            return entities['device_type']
        
        if 'state' in query and 'state' in entities:
            return entities['state']
        
        if 'bank' in query and 'bank' in entities:
            return entities['bank']
        
        # Default: return the most recent entity (first in dict)
        if entities:
            return list(entities.values())[0]
        
        return None


# ============================================================================
# TESTING
# ============================================================================
if __name__ == "__main__":
    from parser import QueryParser
    from conversation_state import ConversationState
    
    print("\n" + "="*80)
    print("ANAPHORA RESOLVER TEST")
    print("="*80)
    
    resolver = AnaphoraResolver()
    parser = QueryParser()
    state = ConversationState(session_id="test-123")
    
    # Build conversation history
    history = [
        "Show me P2P transactions",
        "Filter to Maharashtra",
        "What about Android devices?"
    ]
    
    for query in history:
        parsed = parser.parse(query)
        state.add_turn(query, parsed)
    
    # Test anaphora resolution
    test_queries = [
        ("What is the average amount for it?", "Should resolve 'it' to Android/Maharashtra/P2P"),
        ("Show me the failure rate for them", "Should resolve 'them'"),
        ("What about its success rate?", "Should resolve 'its'"),
        ("Compare that with iOS", "Should resolve 'that' to Android"),
        ("Show me those transactions by age", "Should resolve 'those'"),
    ]
    
    print("\nConversation History:")
    for turn in state.turns:
        print(f"  - {turn.query}")
        print(f"    Filters: {turn.filters_applied}")
    
    print("\n" + "-"*80)
    print("ANAPHORA RESOLUTION TESTS")
    print("-"*80)
    
    for original, note in test_queries:
        resolved = resolver.resolve(original, state)
        
        print(f"\nOriginal:  {original}")
        print(f"Resolved:  {resolved}")
        print(f"Note:      {note}")
        
        if resolved != original:
            print(f"✅ RESOLVED")
        else:
            print(f"⚠️  NO CHANGE")
    
    print("\n" + "="*80)
    print("✓ ANAPHORA RESOLVER TEST COMPLETE")
    print("="*80)