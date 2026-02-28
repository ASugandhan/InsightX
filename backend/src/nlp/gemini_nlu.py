"""
Gemini NLU v2.2 - With 5-Key Rotation System
Primary key used first. On 429, automatically rotates through 4 fallback keys.
"""

import os, json, re, time
from dotenv import load_dotenv
from nlp.key_manager import get_key_manager

load_dotenv()

SCHEMA = """
Table: transactions (250,000 UPI payment transactions, year 2024)

Columns:
- transaction_id     : STRING  - unique ID
- timestamp          : STRING  - datetime (YYYY-MM-DD HH:MM:SS)
- sender_id          : STRING  - sender UPI ID
- receiver_id        : STRING  - receiver UPI ID
- amount_inr         : FLOAT   - amount in Indian Rupees
- transaction_type   : STRING  - 'P2P' or 'P2M'
- transaction_status : STRING  - 'SUCCESS', 'FAILED', 'PENDING'
- merchant_category  : STRING  - 'Food','Retail','Travel',etc (NULL for P2P)
- sender_bank        : STRING  - sender bank name
- receiver_bank      : STRING  - receiver bank name
- sender_state       : STRING  - Indian state
- device_type        : STRING  - 'Android','iOS','Feature Phone'
- network_type       : STRING  - '4G','3G','2G','WiFi'
- hour_of_day        : INTEGER - 0-23
- is_weekend         : BOOLEAN - true if Sat/Sun
- sender_age_group   : STRING  - '18-25','26-35','36-45','46-60','60+'
- fraud_flag         : INTEGER - 1=fraud suspected, 0=clean
- failure_reason     : STRING  - reason if failed (NULL otherwise)
- latency_ms         : FLOAT   - processing time in milliseconds
- sender_upi_app     : STRING  - 'PhonePe','GPay','Paytm','BHIM',etc

DuckDB SQL Rules:
- Table name: transactions
- NEVER add LIMIT unless user asks for "top N" or "first N"
- Failure rate: ROUND(SUM(CASE WHEN transaction_status='FAILED' THEN 1 ELSE 0 END)*100.0/COUNT(*),2)
- Success rate: ROUND(SUM(CASE WHEN transaction_status='SUCCESS' THEN 1 ELSE 0 END)*100.0/COUNT(*),2)
- Fraud rate:   ROUND(SUM(fraud_flag)*100.0/COUNT(*),2)
- Always ROUND floats to 2 decimal places
- Use meaningful column aliases
- For time analysis: strftime('%H', timestamp) for hour, strftime('%m', timestamp) for month
- For weekend: is_weekend = true
"""

FALLBACK_TEMPLATES = [
    (["device", "device type"],
     "SELECT device_type, COUNT(*) as count, ROUND(SUM(CASE WHEN transaction_status='FAILED' THEN 1 ELSE 0 END)*100.0/COUNT(*),2) as failure_rate, ROUND(AVG(amount_inr),2) as avg_amount FROM transactions GROUP BY device_type ORDER BY failure_rate DESC",
     "Failure rate and transaction stats by device type"),
    (["bank", "sender bank", "receiver bank"],
     "SELECT sender_bank, COUNT(*) as count, ROUND(SUM(CASE WHEN transaction_status='FAILED' THEN 1 ELSE 0 END)*100.0/COUNT(*),2) as failure_rate FROM transactions GROUP BY sender_bank ORDER BY failure_rate DESC LIMIT 15",
     "Failure rate by bank"),
    (["fraud", "fraud flag", "fraud rate"],
     "SELECT sender_age_group, SUM(fraud_flag) as fraud_count, ROUND(SUM(fraud_flag)*100.0/COUNT(*),2) as fraud_rate FROM transactions GROUP BY sender_age_group ORDER BY fraud_count DESC",
     "Fraud trends by age group"),
    (["age", "age group"],
     "SELECT sender_age_group, COUNT(*) as count, ROUND(AVG(amount_inr),2) as avg_amount, ROUND(SUM(CASE WHEN transaction_status='FAILED' THEN 1 ELSE 0 END)*100.0/COUNT(*),2) as failure_rate FROM transactions GROUP BY sender_age_group ORDER BY count DESC",
     "Transaction stats by age group"),
    (["state", "location"],
     "SELECT sender_state, COUNT(*) as count, ROUND(SUM(CASE WHEN transaction_status='FAILED' THEN 1 ELSE 0 END)*100.0/COUNT(*),2) as failure_rate FROM transactions GROUP BY sender_state ORDER BY count DESC LIMIT 15",
     "Transaction volume and failure rate by state"),
    (["weekend", "weekday", "saturday", "sunday"],
     "SELECT is_weekend, COUNT(*) as count, ROUND(SUM(CASE WHEN transaction_status='FAILED' THEN 1 ELSE 0 END)*100.0/COUNT(*),2) as failure_rate, ROUND(AVG(amount_inr),2) as avg_amount FROM transactions GROUP BY is_weekend ORDER BY is_weekend",
     "Weekend vs weekday comparison"),
    (["hour", "time", "peak", "when"],
     "SELECT hour_of_day, COUNT(*) as count, ROUND(SUM(CASE WHEN transaction_status='FAILED' THEN 1 ELSE 0 END)*100.0/COUNT(*),2) as failure_rate FROM transactions GROUP BY hour_of_day ORDER BY hour_of_day",
     "Transaction pattern by hour of day"),
    (["network", "4g", "3g", "2g", "wifi"],
     "SELECT network_type, COUNT(*) as count, ROUND(SUM(CASE WHEN transaction_status='FAILED' THEN 1 ELSE 0 END)*100.0/COUNT(*),2) as failure_rate, ROUND(AVG(latency_ms),2) as avg_latency FROM transactions GROUP BY network_type ORDER BY failure_rate DESC",
     "Performance by network type"),
    (["merchant", "category", "p2m"],
     "SELECT merchant_category, COUNT(*) as count, ROUND(AVG(amount_inr),2) as avg_amount FROM transactions WHERE merchant_category IS NOT NULL GROUP BY merchant_category ORDER BY count DESC",
     "Transaction breakdown by merchant category"),
    (["upi app", "phonePe", "gpay", "paytm", "bhim", "app"],
     "SELECT sender_upi_app, COUNT(*) as count, ROUND(AVG(amount_inr),2) as avg_amount, ROUND(SUM(CASE WHEN transaction_status='FAILED' THEN 1 ELSE 0 END)*100.0/COUNT(*),2) as failure_rate FROM transactions GROUP BY sender_upi_app ORDER BY count DESC",
     "Transaction stats by UPI app"),
    (["latency", "slow", "speed", "performance"],
     "SELECT network_type, ROUND(AVG(latency_ms),2) as avg_latency, ROUND(MAX(latency_ms),2) as max_latency FROM transactions GROUP BY network_type ORDER BY avg_latency DESC",
     "Latency analysis by network type"),
    (["failure", "fail", "failed"],
     "SELECT transaction_status, COUNT(*) as count, ROUND(COUNT(*)*100.0/(SELECT COUNT(*) FROM transactions),2) as pct FROM transactions GROUP BY transaction_status ORDER BY count DESC",
     "Transaction status breakdown"),
    (["amount", "average", "avg", "money", "rupee"],
     "SELECT transaction_type, ROUND(AVG(amount_inr),2) as avg_amount, ROUND(MIN(amount_inr),2) as min_amount, ROUND(MAX(amount_inr),2) as max_amount FROM transactions GROUP BY transaction_type",
     "Amount statistics by transaction type"),
    (["p2p", "peer"],
     "SELECT transaction_type, COUNT(*) as count, ROUND(AVG(amount_inr),2) as avg_amount, ROUND(SUM(CASE WHEN transaction_status='FAILED' THEN 1 ELSE 0 END)*100.0/COUNT(*),2) as failure_rate FROM transactions GROUP BY transaction_type ORDER BY count DESC",
     "P2P vs P2M comparison"),
]


class GeminiNLU:
    def __init__(self):
        self.key_manager = get_key_manager()
        self.model = "models/gemini-flash-latest"
        print("GeminiNLU initialized (5-key rotation system)")

    def understand(self, question: str, conversation_history: list, rag_context: str = "", stop_event=None) -> dict:
        history_str = ""
        if conversation_history:
            history_str = "\nConversation history:\n"
            for msg in conversation_history[-6:]:
                role = "User" if msg["role"] == "user" else "Assistant"
                history_str += f"{role}: {msg['content'][:200]}\n"

        rag_str = f"\nFinancial domain knowledge:\n{rag_context}\n" if rag_context else ""

        prompt = f"""You are an expert SQL analyst for UPI transaction data in India.

DATABASE SCHEMA:
{SCHEMA}
{history_str}{rag_str}
Current question: "{question}"

Instructions:
1. Understand what the user wants (use conversation history for follow-ups)
2. Write a precise DuckDB SQL query answering using ALL 250,000 rows
3. For follow-up questions, incorporate filters/context from previous messages
4. Never limit results unless user says "top N" or "first N"
5. Match requested granularity exactly:
   - "hourly" => GROUP BY hour_of_day ORDER BY hour_of_day
   - "daily/weekly/monthly" => group by corresponding time bucket
6. If user asks for "failure rate over time", do NOT return only transaction_status split.
   Return a time-series with at least: time bucket + failure_rate.

Respond ONLY in this JSON format (no markdown, no explanation):
{{
    "sql": "SELECT ... FROM transactions ...",
    "intent": "brief description",
    "entities": ["key", "entities"],
    "is_followup": true
}}"""

        try:
            # Uses key rotation automatically - primary first, then fallbacks on 429
            raw = self.key_manager.generate(model=self.model, contents=prompt, stop_event=stop_event)
            if raw == "ABORTED":
                return self._fallback(question, conversation_history)
            raw = re.sub(r'^```json\s*', '', raw, flags=re.MULTILINE)
            raw = re.sub(r'^```\s*', '', raw, flags=re.MULTILINE)
            raw = re.sub(r'```\s*$', '', raw, flags=re.MULTILINE)
            raw = raw.strip()
            return json.loads(raw)
        except json.JSONDecodeError as e:
            print(f"GeminiNLU JSON parse error: {e}")
            return self._fallback(question, conversation_history)
        except Exception as e:
            print(f"GeminiNLU all keys failed: {e}")
            return self._fallback(question, conversation_history)

    def fix_sql(self, question: str, bad_sql: str, error: str, stop_event=None) -> str:
        prompt = f"""Fix this DuckDB SQL query. Return ONLY the corrected SQL.

Question: {question}
Failed SQL: {bad_sql}
Error: {error}
Table name: transactions
Only use these columns: transaction_id, timestamp, sender_id, receiver_id, amount_inr, transaction_type, transaction_status, merchant_category, sender_bank, receiver_bank, sender_state, device_type, network_type, hour_of_day, is_weekend, sender_age_group, fraud_flag, failure_reason, latency_ms, sender_upi_app"""

        try:
            raw = self.key_manager.generate(model=self.model, contents=prompt, stop_event=stop_event)
            if raw == "ABORTED":
                return "ABORTED"
            raw = re.sub(r'^```sql\s*', '', raw, flags=re.MULTILINE)
            raw = re.sub(r'^```\s*', '', raw, flags=re.MULTILINE)
            raw = re.sub(r'```\s*$', '', raw, flags=re.MULTILINE)
            return raw.strip()
        except Exception as e:
            print(f"GeminiNLU fix_sql failed: {e}")
            return "SELECT COUNT(*) as total FROM transactions"

    def _fallback(self, question: str, conversation_history: list = None) -> dict:
        q_lower = question.lower()
        is_followup = False
        if conversation_history and len(conversation_history) >= 2:
            followup_triggers = ["what about", "same for", "how about", "and for", "compare", "also", "now show"]
            is_followup = any(t in q_lower for t in followup_triggers)

        best_sql, best_intent, best_score = None, None, 0
        has_time_intent = any(k in q_lower for k in ["hour", "hourly", "daily", "weekly", "monthly", "trend", "over time", "timeline"])
        for keywords, sql, intent in FALLBACK_TEMPLATES:
            # Prefer whole-word style matching to avoid accidental substring hits
            score = 0
            for kw in keywords:
                if re.search(rf"\b{re.escape(kw)}\b", q_lower):
                    score += 1
                elif kw in q_lower:
                    score += 0.5

            # Boost time-granularity templates when user clearly asks trend/time
            if has_time_intent and ("hour" in intent.lower() or "weekend vs weekday" in intent.lower()):
                score += 1.5
            if score > best_score:
                best_score = score
                best_sql = sql
                best_intent = intent

        if best_sql and best_score > 0:
            return {"sql": best_sql, "intent": best_intent, "entities": [], "is_followup": is_followup}

        return {
            "sql": "SELECT COUNT(*) as total_transactions, ROUND(AVG(amount_inr),2) as avg_amount, ROUND(SUM(CASE WHEN transaction_status='FAILED' THEN 1 ELSE 0 END)*100.0/COUNT(*),2) as failure_rate, ROUND(SUM(fraud_flag)*100.0/COUNT(*),2) as fraud_rate FROM transactions",
            "intent": "general overview",
            "entities": [],
            "is_followup": is_followup
        }

