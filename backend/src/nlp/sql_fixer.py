"""
SQL Fixer v2.2 - Uses 5-key rotation system
Robust SQL error correction with key rotation on rate limit.
"""

import re
from nlp.key_manager import get_key_manager

SAFE_FALLBACK_SQL = (
    "SELECT COUNT(*) as total_transactions, "
    "ROUND(AVG(amount_inr),2) as avg_amount, "
    "ROUND(SUM(CASE WHEN transaction_status='FAILED' THEN 1 ELSE 0 END)*100.0/COUNT(*),2) as failure_rate, "
    "ROUND(SUM(fraud_flag)*100.0/COUNT(*),2) as fraud_rate "
    "FROM transactions"
)

COMMON_FIXES = {
    "column.*does not exist": "column_not_found",
    "table.*does not exist": "table_not_found",
    "syntax error": "syntax_error",
    "binder error": "binder_error",
    "conversion error": "type_error",
}


class SQLFixer:
    def __init__(self):
        self.key_manager = get_key_manager()
        self.model = "models/gemini-flash-latest"
        print("SQLFixer initialized (5-key rotation)")

    def fix(self, question: str, bad_sql: str, error: str, max_retries: int = 2) -> str:
        # Step 1: Quick pattern fix (no API)
        quick = self._quick_fix(bad_sql, error)
        if quick:
            return quick

        # Step 2: Gemini fix with key rotation
        schema_hint = (
            "Valid columns: transaction_id, timestamp, sender_id, receiver_id, amount_inr, "
            "transaction_type (P2P/P2M), transaction_status (SUCCESS/FAILED/PENDING), "
            "merchant_category, sender_bank, receiver_bank, sender_state, "
            "device_type (Android/iOS/Feature Phone), network_type (4G/3G/2G/WiFi), "
            "hour_of_day, is_weekend, sender_age_group, fraud_flag, failure_reason, "
            "latency_ms, sender_upi_app. Table: transactions (DuckDB)."
        )

        prompt = f"""Fix this DuckDB SQL query. Return ONLY the corrected SQL, no explanation.

User question: {question}
Failed SQL: {bad_sql}
Error: {error}

Schema: {schema_hint}

Rules:
- Table name must be: transactions
- Only use columns listed above
- Return ONLY the SQL query"""

        try:
            raw = self.key_manager.generate(model=self.model, contents=prompt)
            fixed = re.sub(r'^```sql\s*', '', raw, flags=re.MULTILINE)
            fixed = re.sub(r'^```\s*', '', fixed, flags=re.MULTILINE)
            fixed = re.sub(r'```\s*$', '', fixed, flags=re.MULTILINE)
            fixed = fixed.strip()
            if fixed.upper().startswith("SELECT"):
                return fixed
        except Exception as e:
            print(f"SQLFixer Gemini failed: {e}")

        print("SQLFixer: Using safe fallback")
        return SAFE_FALLBACK_SQL

    def _quick_fix(self, sql: str, error: str) -> str:
        error_lower = error.lower()
        if "table" in error_lower and "does not exist" in error_lower:
            fixed = re.sub(r'\bFROM\s+\w+\b', 'FROM transactions', sql, flags=re.IGNORECASE)
            fixed = re.sub(r'\bJOIN\s+\w+\b', 'JOIN transactions', fixed, flags=re.IGNORECASE)
            if fixed != sql:
                return fixed
        if "limit" in error_lower:
            fixed = re.sub(r'LIMIT\s+\S+', 'LIMIT 10', sql, flags=re.IGNORECASE)
            if fixed != sql:
                return fixed
        if "median" in error_lower:
            return re.sub(r'MEDIAN\s*\(', 'AVG(', sql, flags=re.IGNORECASE)
        return ""

    def validate_sql_safety(self, sql: str) -> bool:
        sql_upper = sql.strip().upper()
        dangerous = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "TRUNCATE", "EXEC", "EXECUTE"]
        return sql_upper.startswith("SELECT") and not any(kw in sql_upper for kw in dangerous)

