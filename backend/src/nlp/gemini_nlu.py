"""
Gemini NLU - Natural Language Understanding
Understands user intent and generates SQL dynamically.
Uses RAG context and conversation history for full understanding.
"""

import os
import json
import re
from dotenv import load_dotenv
from google import genai

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


class GeminiNLU:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-flash-latest"
        print("GeminiNLU initialized")

    def understand(self, question: str, conversation_history: list, rag_context: str = "") -> dict:
        """
        Understand user question and generate SQL.

        Args:
            question: Current user question
            conversation_history: List of {role, content} dicts
            rag_context: Financial domain knowledge from RAG

        Returns:
            dict: sql, intent, entities, is_followup
        """

        # Build conversation context
        history_str = ""
        if conversation_history:
            history_str = "\nConversation history:\n"
            for msg in conversation_history[-6:]:
                role = "User" if msg["role"] == "user" else "Assistant"
                history_str += f"{role}: {msg['content'][:200]}\n"

        # RAG context
        rag_str = ""
        if rag_context:
            rag_str = f"\nFinancial domain knowledge (use for context, not for SQL):\n{rag_context}\n"

        prompt = f"""You are an expert SQL analyst for UPI transaction data in India.

DATABASE SCHEMA:
{SCHEMA}
{history_str}{rag_str}
Current question: "{question}"

Instructions:
1. Understand what the user wants (use conversation history for follow-ups like "what about weekends?" or "same for P2P?")
2. Write a precise DuckDB SQL query that answers using ALL 250,000 rows
3. For follow-up questions, incorporate filters/context from previous messages
4. Never limit results unless user says "top N" or "first N"

Respond ONLY in this JSON format (no markdown, no explanation outside JSON):
{{
    "sql": "SELECT ... FROM transactions ...",
    "intent": "brief description of what user wants",
    "entities": ["key", "entities", "detected"],
    "is_followup": true
}}"""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            raw = response.text.strip()
            # Strip markdown code fences
            raw = re.sub(r'^```json\s*', '', raw, flags=re.MULTILINE)
            raw = re.sub(r'^```\s*', '', raw, flags=re.MULTILINE)
            raw = re.sub(r'```\s*$', '', raw, flags=re.MULTILINE)
            raw = raw.strip()
            return json.loads(raw)

        except json.JSONDecodeError as e:
            print(f"GeminiNLU JSON parse error: {e}\nRaw: {raw[:300]}")
            return self._fallback(question)
        except Exception as e:
            print(f"GeminiNLU error: {e}")
            return self._fallback(question)

    def fix_sql(self, question: str, bad_sql: str, error: str) -> str:
        """Ask Gemini to fix a bad SQL query."""
        prompt = f"""Fix this DuckDB SQL query.

Question: {question}
Failed SQL: {bad_sql}
Error: {error}

Rules: Table is named 'transactions'. Return ONLY the corrected SQL query, nothing else."""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            fixed = response.text.strip()
            fixed = re.sub(r'^```sql\s*', '', fixed, flags=re.MULTILINE)
            fixed = re.sub(r'^```\s*', '', fixed, flags=re.MULTILINE)
            fixed = re.sub(r'```\s*$', '', fixed, flags=re.MULTILINE)
            return fixed.strip()
        except Exception as e:
            print(f"SQL fix error: {e}")
            return "SELECT COUNT(*) as total FROM transactions"

    def _fallback(self, question: str) -> dict:
        """Safe fallback when Gemini fails."""
        return {
            "sql": "SELECT COUNT(*) as total_transactions, ROUND(AVG(amount_inr),2) as avg_amount, ROUND(SUM(CASE WHEN transaction_status='FAILED' THEN 1 ELSE 0 END)*100.0/COUNT(*),2) as failure_rate FROM transactions",
            "intent": "general overview of transactions",
            "entities": [],
            "is_followup": False
        }
