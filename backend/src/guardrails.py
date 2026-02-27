"""
Guardrails - Task 3: Input validation, output safety, injection prevention, rate limiting.
All requests pass through guardrails before and after processing.
"""

import re
import time
import hashlib
from collections import defaultdict
from typing import Tuple


# ============================================================================
# INPUT GUARDRAILS
# ============================================================================

# Blocked patterns - SQL injection, prompt injection, abuse
INJECTION_PATTERNS = [
    r'(drop|delete|truncate|alter|create|insert|update)\s+(table|database|index)',
    r';\s*(drop|delete|truncate|alter)',
    r'--\s*$',                          # SQL comment injection
    r'/\*.*?\*/',                       # Block comment injection
    r'(exec|execute)\s*\(',             # Exec calls
    r'xp_cmdshell',                     # SQL Server shell
    r'union\s+select',                  # UNION injection
    r'(ignore|override|forget)\s+(previous|all|system|above)\s+(instruction|prompt|rule)',  # Prompt injection
    r'(you are now|act as|pretend to be|roleplay as)\s+',  # Role hijacking
    r'(reveal|show|print|display)\s+(your|the)\s+(system\s+prompt|instructions|api\s+key)',
]

# Max input length
MAX_QUESTION_LENGTH = 500
MIN_QUESTION_LENGTH = 2

# Allowed question topics (must relate to UPI/transactions)
OFF_TOPIC_PATTERNS = [
    r'\b(hack|crack|exploit|vulnerability|bypass|jailbreak)\b',
    r'\b(password|credentials|login|admin|root|sudo)\b',
    r'\b(personal\s+data|private\s+info|steal|scrape)\b',
]

# Output safety
MAX_ANSWER_LENGTH = 3000
SENSITIVE_DATA_PATTERNS = [
    r'sk-[a-zA-Z0-9]{20,}',              # OpenAI API keys
    r'AIza[0-9A-Za-z\-_]{35}',           # Google API keys
    r'sk-ant-api[0-9A-Za-z\-_]{20,}',   # Anthropic API keys
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Emails
    r'\b\d{10,16}\b',                    # Phone/card numbers
]


class RateLimiter:
    """Simple in-memory rate limiter per session."""

    def __init__(self, max_requests: int = 30, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._buckets = defaultdict(list)

    def is_allowed(self, session_id: str) -> Tuple[bool, str]:
        now = time.time()
        window_start = now - self.window_seconds
        # Clean old entries
        self._buckets[session_id] = [t for t in self._buckets[session_id] if t > window_start]
        if len(self._buckets[session_id]) >= self.max_requests:
            remaining = self.window_seconds - (now - self._buckets[session_id][0])
            return False, f"Rate limit exceeded. Please wait {remaining:.0f}s before sending more queries."
        self._buckets[session_id].append(now)
        return True, ""


class InputGuardrail:
    """Validates and sanitizes user input before processing."""

    def __init__(self):
        self.injection_patterns = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in INJECTION_PATTERNS]
        self.off_topic_patterns = [re.compile(p, re.IGNORECASE) for p in OFF_TOPIC_PATTERNS]

    def validate(self, question: str) -> Tuple[bool, str]:
        """
        Validate user input.
        Returns (is_safe, rejection_reason). If is_safe=True, rejection_reason is empty.
        """
        if not question or not question.strip():
            return False, "Question cannot be empty."

        q = question.strip()

        # Length checks
        if len(q) < MIN_QUESTION_LENGTH:
            return False, "Question is too short. Please ask a complete question."
        if len(q) > MAX_QUESTION_LENGTH:
            return False, f"Question is too long (max {MAX_QUESTION_LENGTH} chars). Please be more concise."

        # Injection detection
        for pattern in self.injection_patterns:
            if pattern.search(q):
                return False, "Your query contains disallowed patterns. Please ask a natural language question about UPI transactions."

        # Off-topic / abuse detection
        for pattern in self.off_topic_patterns:
            if pattern.search(q):
                return False, "This query is outside the scope of InsightX. I can only answer questions about UPI transaction data."

        return True, ""

    def sanitize(self, question: str) -> str:
        """Clean and normalize the question."""
        q = question.strip()
        # Remove excessive whitespace
        q = re.sub(r'\s+', ' ', q)
        # Remove null bytes
        q = q.replace('\x00', '')
        # Truncate if somehow too long after cleaning
        return q[:MAX_QUESTION_LENGTH]


class OutputGuardrail:
    """Validates and sanitizes LLM output before returning to user."""

    def __init__(self):
        self.sensitive_patterns = [re.compile(p, re.IGNORECASE) for p in SENSITIVE_DATA_PATTERNS]

    def validate(self, answer: str) -> Tuple[bool, str]:
        """Check if output is safe to return."""
        if not answer or not answer.strip():
            return False, "Empty response generated. Please try again."

        # Check for leaked sensitive data
        for pattern in self.sensitive_patterns:
            if pattern.search(answer):
                return False, "REDACTED_SENSITIVE"

        return True, ""

    def sanitize(self, answer: str) -> str:
        """Clean LLM output."""
        if not answer:
            return "I could not generate a response. Please try again."

        # Redact any accidental API key leaks
        for pattern in self.sensitive_patterns:
            answer = pattern.sub("[REDACTED]", answer)

        # Truncate excessively long answers
        if len(answer) > MAX_ANSWER_LENGTH:
            answer = answer[:MAX_ANSWER_LENGTH] + "\n\n*(Response truncated for brevity)*"

        return answer.strip()


class SQLGuardrail:
    """Validates SQL before execution - prevents dangerous queries."""

    ALLOWED_STATEMENTS = {"SELECT"}
    DANGEROUS_KEYWORDS = {
        "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE",
        "TRUNCATE", "EXEC", "EXECUTE", "GRANT", "REVOKE",
        "ATTACH", "DETACH", "COPY", "EXPORT", "IMPORT"
    }

    def validate_sql(self, sql: str) -> Tuple[bool, str]:
        """Ensure SQL is safe to execute."""
        if not sql or not sql.strip():
            return False, "Empty SQL query"

        sql_clean = sql.strip().upper()
        first_word = sql_clean.split()[0] if sql_clean.split() else ""

        if first_word not in self.ALLOWED_STATEMENTS:
            return False, f"Only SELECT statements are allowed. Got: {first_word}"

        for dangerous in self.DANGEROUS_KEYWORDS:
            if re.search(r'\b' + dangerous + r'\b', sql_clean):
                return False, f"Dangerous SQL keyword detected: {dangerous}"

        # Prevent reading system tables
        if re.search(r'\binformation_schema\b|\bpg_\w+\b|\bsqlite_\w+\b', sql_clean):
            return False, "Access to system tables is not allowed"

        return True, ""


# ============================================================================
# MAIN GUARDRAILS CLASS
# ============================================================================

class Guardrails:
    """
    Central guardrails manager. Use this in the API server and main pipeline.
    """

    def __init__(self, rate_limit_per_minute: int = 30):
        self.input_guard = InputGuardrail()
        self.output_guard = OutputGuardrail()
        self.sql_guard = SQLGuardrail()
        self.rate_limiter = RateLimiter(max_requests=rate_limit_per_minute, window_seconds=60)
        print(f"Guardrails initialized (rate limit: {rate_limit_per_minute} req/min)")

    def check_input(self, question: str, session_id: str = "default") -> Tuple[bool, str]:
        """Full input validation: rate limit + content check."""
        # Rate limit
        allowed, msg = self.rate_limiter.is_allowed(session_id)
        if not allowed:
            return False, msg

        # Content validation
        valid, msg = self.input_guard.validate(question)
        if not valid:
            return False, msg

        return True, ""

    def sanitize_input(self, question: str) -> str:
        return self.input_guard.sanitize(question)

    def check_sql(self, sql: str) -> Tuple[bool, str]:
        return self.sql_guard.validate_sql(sql)

    def check_output(self, answer: str) -> str:
        """Validate and sanitize output. Always returns a safe string."""
        # Always sanitize first (redacts sensitive data in-place)
        sanitized = self.output_guard.sanitize(answer)
        # Then validate the sanitized version
        is_safe, msg = self.output_guard.validate(sanitized)
        if not is_safe:
            return msg
        return sanitized

