"""
Schema Validator - Issue 1 Fix: Anti-Hallucination
Validates that SQL queries only use columns that exist in the transactions table.
"""

import re

VALID_COLUMNS = {
    "transaction_id", "timestamp", "sender_id", "receiver_id",
    "amount_inr", "transaction_type", "transaction_status",
    "merchant_category", "sender_bank", "receiver_bank",
    "sender_state", "device_type", "network_type", "hour_of_day",
    "is_weekend", "sender_age_group", "fraud_flag", "failure_reason",
    "latency_ms", "sender_upi_app"
}

HALLUCINATED_COLUMNS = {
    "revenue", "profit", "profit_margin", "conversion_rate",
    "customer_segment", "region", "country", "city",
    "visa", "mastercard", "card_type", "card_number",
    "income", "salary", "balance", "account_number",
    "product", "category_id", "user_id", "session_id",
    "click_rate", "bounce_rate", "retention_rate",
    "churn_rate", "ltv", "cac", "roi",
    "gender", "name", "email", "phone",
    "zip_code", "postal_code", "address",
    "currency", "exchange_rate", "tax"
}

VALID_VALUES = {
    "transaction_type": {"P2P", "P2M"},
    "transaction_status": {"SUCCESS", "FAILED", "PENDING"},
    "device_type": {"Android", "iOS", "Feature Phone"},
    "network_type": {"4G", "3G", "2G", "WiFi"},
    "sender_age_group": {"18-25", "26-35", "36-45", "46-60", "60+"},
}


class SchemaValidator:
    def __init__(self):
        self.valid_columns = VALID_COLUMNS
        self.hallucinated_columns = HALLUCINATED_COLUMNS

    def validate_sql(self, sql: str) -> dict:
        if not sql or not sql.strip():
            return {"is_valid": False, "issues": ["Empty SQL"], "hallucinated_columns": [], "suggested_fix": ""}

        sql_lower = sql.lower()
        issues = []
        hallucinated = []

        for bad_col in self.hallucinated_columns:
            pattern = r'\b' + re.escape(bad_col) + r'\b'
            if re.search(pattern, sql_lower):
                hallucinated.append(bad_col)
                issues.append(f"Column '{bad_col}' does not exist in schema")

        is_valid = len(issues) == 0
        suggested_fix = ""
        if not is_valid:
            suggested_fix = f"Hallucinated columns: {hallucinated}. Valid columns: {sorted(self.valid_columns)}"

        return {"is_valid": is_valid, "issues": issues, "hallucinated_columns": hallucinated, "suggested_fix": suggested_fix}

    def validate_parsed_query(self, parsed_result) -> dict:
        issues = []
        if isinstance(parsed_result, dict):
            intent = parsed_result.get("intent", "")
            sql = parsed_result.get("sql", "")
            entities = parsed_result.get("entities", [])
        else:
            intent = getattr(parsed_result, "intent", "")
            sql = getattr(parsed_result, "sql", "")
            entities = getattr(parsed_result, "entities", [])

        intent_lower = intent.lower() if intent else ""
        for bad_col in self.hallucinated_columns:
            if re.search(r'\b' + re.escape(bad_col) + r'\b', intent_lower):
                issues.append(f"Intent references non-existent concept: '{bad_col}'")

        if sql:
            sql_val = self.validate_sql(sql)
            if not sql_val["is_valid"]:
                issues.extend(sql_val["issues"])

        return {"is_valid": len(issues) == 0, "issues": issues}

    def get_correction_hint(self, bad_column: str) -> str:
        hints = {
            "revenue": "amount_inr", "profit": "amount_inr",
            "region": "sender_state", "country": "sender_state",
            "card_type": "transaction_type", "gender": "sender_age_group",
            "user_id": "sender_id", "conversion_rate": "transaction_status (calculate success rate)",
        }
        return hints.get(bad_column.lower(), f"No equivalent for '{bad_column}' in schema")
