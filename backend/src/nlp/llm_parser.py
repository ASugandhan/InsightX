"""
LLM Parser - Compatibility wrapper + Issue 1 Fix (Anti-Hallucination)
Wraps GeminiNLU and adds TWO-LAYER schema validation:
  Layer 1: Question-level keyword scan (works even without Gemini/API)
  Layer 2: SQL validation after Gemini generates SQL
Used by test_anti_hallucination.py test suite.
"""

import sys, os, re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nlp.gemini_nlu import GeminiNLU
from nlp.schema_validator import SchemaValidator, HALLUCINATED_COLUMNS, VALID_COLUMNS


# Concept-to-hallucinated-column mapping — catches bad queries at question level
QUESTION_HALLUCINATION_MAP = {
    "revenue":              "revenue (use amount_inr instead)",
    "revenues":             "revenue (use amount_inr instead)",
    "profit":               "profit (not in schema)",
    "profits":              "profit (not in schema)",
    "profit margin":        "profit_margin (not in schema)",
    "profit margins":       "profit_margin (not in schema)",
    "conversion rate":      "conversion_rate (not in schema)",
    "conversion rates":     "conversion_rate (not in schema)",
    "customer segment":     "customer_segment (not in schema)",
    "customer segments":    "customer_segment (not in schema)",
    "user segment":         "customer_segment (not in schema)",
    "user segments":        "customer_segment (not in schema)",
    "region":               "region (use sender_state instead)",
    "regions":              "region (use sender_state instead)",
    "country":              "country (use sender_state instead)",
    "countries":            "country (use sender_state instead)",
    "city":                 "city (use sender_state instead)",
    "cities":               "city (use sender_state instead)",
    "visa":                 "Visa card type (not in schema - only P2P/P2M)",
    "mastercard":           "Mastercard (not in schema)",
    "card type":            "card_type (not in schema)",
    "card types":           "card_type (not in schema)",
    "gender":               "gender (not in schema)",
    "income":               "income (not in schema)",
    "salary":               "salary (not in schema)",
    "salaries":             "salary (not in schema)",
    "email":                "email (not in schema)",
    "phone number":         "phone (not in schema)",
    "phone numbers":        "phone (not in schema)",
    "ltv":                  "ltv (not in schema)",
    "roi":                  "roi (not in schema)",
    "click rate":           "click_rate (not in schema)",
    "click rates":          "click_rate (not in schema)",
    "bounce rate":          "bounce_rate (not in schema)",
    "bounce rates":         "bounce_rate (not in schema)",
    "churn":                "churn_rate (not in schema)",
    "churn rate":           "churn_rate (not in schema)",
    "market share":         "market_share (not in schema)",
    "refund":               "refund (not in schema)",
    "refunds":              "refund (not in schema)",
    "rating":               "rating (not in schema)",
    "ratings":              "rating (not in schema)",
    "score":                "score (not in schema - use fraud_flag)",
    "credit score":         "credit_score (not in schema)",
}


class ParsedQuery:
    def __init__(self, intent, sql, confidence, entities,
                 is_followup=False, is_valid=True, issues=None):
        self.intent = intent
        self.sql = sql
        self.confidence = confidence
        self.entities = entities
        self.is_followup = is_followup
        self.is_valid = is_valid
        self.issues = issues or []

    def __repr__(self):
        return (f"ParsedQuery(intent='{self.intent}', "
                f"confidence={self.confidence:.2f}, valid={self.is_valid})")


class LLMParser:
    def __init__(self):
        self.nlu = GeminiNLU()
        self.validator = SchemaValidator()
        self._conversation_history = []
        print("LLMParser initialized (GeminiNLU + SchemaValidator)")

    def _scan_question_for_hallucinations(self, question: str) -> list:
        """
        Layer 1: Scan the question TEXT for known hallucinated concepts.
        This works independently of Gemini — catches bad intent before SQL is even generated.
        """
        q_lower = question.lower()
        found = []
        for concept, description in QUESTION_HALLUCINATION_MAP.items():
            if re.search(r'\b' + re.escape(concept) + r'\b', q_lower):
                found.append(description)
        return found

    def parse(self, question: str) -> ParsedQuery:
        """
        Parse a natural language question into a validated ParsedQuery.
        Two-layer hallucination detection:
          Layer 1 - question text scan (API-independent, always works)
          Layer 2 - SQL output validation (catches anything Gemini hallucinates)
        """
        # ---- LAYER 1: Question-level scan ----
        question_issues = self._scan_question_for_hallucinations(question)
        question_has_hallucination = len(question_issues) > 0

        # Call Gemini NLU (may fail/rate-limit, falls back internally)
        try:
            nlu_result = self.nlu.understand(
                question=question,
                conversation_history=self._conversation_history,
                rag_context=""
            )
        except Exception:
            nlu_result = {
                "sql": "SELECT COUNT(*) as total FROM transactions",
                "intent": "general overview",
                "entities": [],
                "is_followup": False
            }

        sql = nlu_result.get("sql", "")
        intent = nlu_result.get("intent", question)
        entities = nlu_result.get("entities", [])
        is_followup = nlu_result.get("is_followup", False)

        # ---- LAYER 2: SQL validation ----
        sql_validation = self.validator.validate_sql(sql)
        sql_issues = sql_validation.get("issues", [])

        # Combine all issues
        all_issues = question_issues + [i for i in sql_issues if i not in question_issues]
        is_valid = not question_has_hallucination and sql_validation["is_valid"]

        # Confidence adjustment
        base_confidence = 0.9
        if question_has_hallucination:
            # Strong penalty: question itself asks for non-existent data
            penalty = len(question_issues) * 0.3
            confidence = max(0.1, base_confidence - penalty)
        elif not sql_validation["is_valid"]:
            # Gemini hallucinated in SQL despite valid question
            penalty = len(sql_validation.get("hallucinated_columns", [])) * 0.25
            confidence = max(0.1, base_confidence - penalty)
        else:
            confidence = base_confidence

        # Extra penalty for vague queries
        if question.lower().strip() in {"show", "give", "list", "display"} or len(question.split()) <= 2:
            confidence = min(confidence, 0.6)

        return ParsedQuery(
            intent=intent, sql=sql, confidence=confidence,
            entities=entities, is_followup=is_followup,
            is_valid=is_valid, issues=all_issues
        )

    def parse_with_history(self, question: str, conversation_history: list) -> ParsedQuery:
        nlu_result = self.nlu.understand(
            question=question,
            conversation_history=conversation_history,
            rag_context=""
        )
        sql = nlu_result.get("sql", "")
        intent = nlu_result.get("intent", question)
        entities = nlu_result.get("entities", [])
        is_followup = nlu_result.get("is_followup", False)

        question_issues = self._scan_question_for_hallucinations(question)
        sql_val = self.validator.validate_sql(sql)
        all_issues = question_issues + sql_val.get("issues", [])
        is_valid = len(question_issues) == 0 and sql_val["is_valid"]

        confidence = 0.9
        if not is_valid:
            confidence = max(0.1, 0.9 - 0.3 * len(question_issues) - 0.25 * len(sql_val.get("hallucinated_columns", [])))

        return ParsedQuery(intent=intent, sql=sql, confidence=confidence,
                           entities=entities, is_followup=is_followup,
                           is_valid=is_valid, issues=all_issues)

    def update_history(self, question: str, answer: str):
        self._conversation_history.append({"role": "user", "content": question})
        self._conversation_history.append({"role": "assistant", "content": answer})
        if len(self._conversation_history) > 20:
            self._conversation_history = self._conversation_history[-20:]

    def clear_history(self):
        self._conversation_history = []

