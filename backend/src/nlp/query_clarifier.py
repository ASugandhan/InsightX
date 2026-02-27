"""
Query Clarifier - Issue 3 Fix: Vague/Ambiguous Queries
Detects vague queries and applies smart defaults or returns clarification question.
"""

from typing import Tuple

SMART_DEFAULTS = {
    "show transactions": (
        "SELECT transaction_status, COUNT(*) as count, ROUND(AVG(amount_inr),2) as avg_amount FROM transactions GROUP BY transaction_status ORDER BY count DESC",
        "Transaction breakdown by status"
    ),
    "show me transactions": (
        "SELECT transaction_status, COUNT(*) as count, ROUND(AVG(amount_inr),2) as avg_amount FROM transactions GROUP BY transaction_status ORDER BY count DESC",
        "Transaction breakdown by status"
    ),
    "show fraud": (
        "SELECT sender_age_group, SUM(fraud_flag) as fraud_count, ROUND(SUM(fraud_flag)*100.0/COUNT(*),2) as fraud_rate FROM transactions GROUP BY sender_age_group ORDER BY fraud_count DESC",
        "Fraud breakdown by age group"
    ),
    "show me fraud": (
        "SELECT sender_age_group, SUM(fraud_flag) as fraud_count, ROUND(SUM(fraud_flag)*100.0/COUNT(*),2) as fraud_rate FROM transactions GROUP BY sender_age_group ORDER BY fraud_count DESC",
        "Fraud breakdown by age group"
    ),
    "what about failures": (
        "SELECT failure_reason, COUNT(*) as count FROM transactions WHERE transaction_status='FAILED' AND failure_reason IS NOT NULL GROUP BY failure_reason ORDER BY count DESC",
        "Failure breakdown by reason"
    ),
    "what about weekends": (
        "SELECT is_weekend, COUNT(*) as count, ROUND(SUM(CASE WHEN transaction_status='FAILED' THEN 1 ELSE 0 END)*100.0/COUNT(*),2) as failure_rate, ROUND(AVG(amount_inr),2) as avg_amount FROM transactions GROUP BY is_weekend",
        "Weekend vs weekday comparison"
    ),
    "best performing device": (
        "SELECT device_type, COUNT(*) as count, ROUND(SUM(CASE WHEN transaction_status='SUCCESS' THEN 1 ELSE 0 END)*100.0/COUNT(*),2) as success_rate FROM transactions GROUP BY device_type ORDER BY success_rate DESC",
        "Device performance by success rate"
    ),
    "worst performing device": (
        "SELECT device_type, COUNT(*) as count, ROUND(SUM(CASE WHEN transaction_status='FAILED' THEN 1 ELSE 0 END)*100.0/COUNT(*),2) as failure_rate FROM transactions GROUP BY device_type ORDER BY failure_rate DESC",
        "Device performance by failure rate"
    ),
    "worst performing age group": (
        "SELECT sender_age_group, COUNT(*) as count, ROUND(SUM(CASE WHEN transaction_status='FAILED' THEN 1 ELSE 0 END)*100.0/COUNT(*),2) as failure_rate FROM transactions GROUP BY sender_age_group ORDER BY failure_rate DESC",
        "Age group performance by failure rate"
    ),
    "most popular merchant category": (
        "SELECT merchant_category, COUNT(*) as count, ROUND(AVG(amount_inr),2) as avg_amount FROM transactions WHERE merchant_category IS NOT NULL GROUP BY merchant_category ORDER BY count DESC",
        "Merchant categories by volume"
    ),
}

AMBIGUOUS_PATTERNS = {
    "show": "What would you like to see? e.g. 'show failure rates by device' or 'show fraud by age group'",
    "display": "What would you like to display? e.g. 'display transaction counts by state'",
    "list": "What would you like to list? e.g. 'list top 10 banks by failure rate'",
    "give": "What data are you looking for? e.g. 'give me fraud rates by state'",
}

TEMPORAL_PATTERNS = {
    "last month": "strftime('%m', timestamp) = strftime('%m', date('now', '-1 month'))",
    "this month": "strftime('%m', timestamp) = strftime('%m', 'now')",
    "last week": "timestamp >= date('now', '-7 days')",
    "yesterday": "date(timestamp) = date('now', '-1 day')",
    "weekends": "is_weekend = true",
    "weekend": "is_weekend = true",
    "weekdays": "is_weekend = false",
    "weekday": "is_weekend = false",
    "morning": "hour_of_day BETWEEN 6 AND 11",
    "afternoon": "hour_of_day BETWEEN 12 AND 17",
    "evening": "hour_of_day BETWEEN 18 AND 21",
    "night": "hour_of_day >= 22 OR hour_of_day < 6",
    "peak hours": "(hour_of_day BETWEEN 10 AND 12 OR hour_of_day BETWEEN 18 AND 21)",
}


class QueryClarifier:
    def __init__(self):
        self.smart_defaults = SMART_DEFAULTS
        self.ambiguous_patterns = AMBIGUOUS_PATTERNS
        self.temporal_patterns = TEMPORAL_PATTERNS

    def analyze(self, question: str) -> dict:
        q = question.lower().strip()
        result = {
            "is_vague": False, "is_ambiguous": False,
            "has_smart_default": False, "smart_default_sql": None,
            "smart_default_intent": None, "clarification_needed": None,
            "temporal_filter": None,
        }

        # Check smart defaults
        for pattern, (sql, intent) in self.smart_defaults.items():
            if q == pattern or q.startswith(pattern):
                result.update({"is_vague": True, "has_smart_default": True,
                               "smart_default_sql": sql, "smart_default_intent": intent})
                return result

        # Check purely ambiguous (1-2 word commands)
        words = q.split()
        if len(words) <= 2:
            for pattern, clarification in self.ambiguous_patterns.items():
                if words[0] == pattern:
                    result.update({"is_vague": True, "is_ambiguous": True,
                                   "clarification_needed": clarification})
                    return result

        # Check temporal patterns
        for temporal_kw, sql_filter in self.temporal_patterns.items():
            if temporal_kw in q:
                result["temporal_filter"] = sql_filter
                break

        return result

    def apply_temporal_rewrite(self, sql: str, temporal_filter: str) -> str:
        if not temporal_filter or not sql:
            return sql
        sql_upper = sql.upper()
        if "WHERE" in sql_upper:
            idx = sql_upper.index("WHERE") + 5
            return sql[:idx] + f" {temporal_filter} AND" + sql[idx:]
        elif "GROUP BY" in sql_upper:
            idx = sql_upper.index("GROUP BY")
            return sql[:idx] + f"WHERE {temporal_filter} " + sql[idx:]
        elif "ORDER BY" in sql_upper:
            idx = sql_upper.index("ORDER BY")
            return sql[:idx] + f"WHERE {temporal_filter} " + sql[idx:]
        else:
            return sql + f" WHERE {temporal_filter}"

    def get_default_for_ambiguous(self, question: str) -> Tuple[str, str]:
        q = question.lower()
        if "fraud" in q:
            return ("SELECT sender_age_group, SUM(fraud_flag) as fraud_count, ROUND(SUM(fraud_flag)*100.0/COUNT(*),2) as fraud_rate FROM transactions GROUP BY sender_age_group ORDER BY fraud_count DESC", "Fraud overview by age group")
        elif "fail" in q:
            return ("SELECT transaction_status, COUNT(*) as count FROM transactions GROUP BY transaction_status", "Transaction status breakdown")
        elif "amount" in q or "money" in q:
            return ("SELECT ROUND(AVG(amount_inr),2) as avg_amount, ROUND(MIN(amount_inr),2) as min_amount, ROUND(MAX(amount_inr),2) as max_amount FROM transactions", "Transaction amount statistics")
        else:
            return ("SELECT COUNT(*) as total_transactions, ROUND(AVG(amount_inr),2) as avg_amount, ROUND(SUM(CASE WHEN transaction_status='FAILED' THEN 1 ELSE 0 END)*100.0/COUNT(*),2) as failure_rate FROM transactions", "General overview")
