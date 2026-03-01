"""
Financial Knowledge RAG
Stores and retrieves UPI/financial domain knowledge to answer WHY questions.
Uses simple TF-IDF style keyword matching as primary retrieval (no model download needed).
ChromaDB + SentenceTransformer used only if already cached locally.
"""

import os
from typing import List


# ============================================================================
# FINANCIAL KNOWLEDGE BASE
# ============================================================================

FINANCIAL_KNOWLEDGE = [
    {
        "id": "rbi_001",
        "text": "RBI mandates UPI transaction failure rate below 0.5% for payment providers. Failure rate above 1% triggers regulatory review. Above 5% indicates serious infrastructure issues.",
        "tags": ["failure_rate", "rbi", "threshold", "regulatory", "benchmark"]
    },
    {
        "id": "rbi_002",
        "text": "NPCI sets UPI success rate benchmark at 99.5% or above. Most top banks maintain 97-99% success rates. Success rates below 95% are considered poor performance.",
        "tags": ["success_rate", "npci", "benchmark", "bank", "performance"]
    },
    {
        "id": "rbi_003",
        "text": "RBI guidelines require UPI transactions to complete within 30 seconds. Latency above 3000ms is considered high. Industry benchmark latency is 800-1200ms.",
        "tags": ["latency", "speed", "rbi", "performance", "slow"]
    },
    {
        "id": "rbi_004",
        "text": "UPI daily transaction limit is Rs 1,00,000 per user per day for most banks. Some banks allow up to Rs 2,00,000. Transactions above Rs 2,000 may require additional authentication.",
        "tags": ["limit", "amount", "daily", "threshold", "maximum"]
    },
    {
        "id": "rbi_005",
        "text": "RBI requires UPI fraud rate below 0.01% of transaction volume. Industry average fraud rate is 0.015-0.03%. Fraud rates above 0.1% require mandatory reporting to RBI.",
        "tags": ["fraud", "rbi", "threshold", "regulatory", "fraud_rate"]
    },
    {
        "id": "bench_001",
        "text": "Industry average UPI failure rate is 4-6% overall. P2P failure rate is typically 3-4%. P2M failure rate is 5-7% due to merchant-side issues.",
        "tags": ["failure_rate", "p2p", "p2m", "benchmark", "industry", "average"]
    },
    {
        "id": "bench_002",
        "text": "Weekend UPI transactions have 15-25% higher failure rates than weekdays. This is due to lower bank staffing, higher transaction volumes, and delayed settlement on weekends.",
        "tags": ["weekend", "failure_rate", "pattern", "timing", "weekday", "saturday", "sunday"]
    },
    {
        "id": "bench_003",
        "text": "Feature phone UPI failure rates are 2-3x higher than Android or iOS. USSD-based UPI on feature phones is slower and less stable than app-based UPI.",
        "tags": ["device", "feature_phone", "failure_rate", "android", "ios", "mobile"]
    },
    {
        "id": "bench_004",
        "text": "2G network UPI failure rate is 3-4x higher than 4G. Network timeouts cause 40% of UPI failures. WiFi has the lowest failure rate among all network types.",
        "tags": ["network", "2g", "4g", "wifi", "failure_rate", "timeout", "connectivity"]
    },
    {
        "id": "bench_005",
        "text": "High-value transactions above Rs 10,000 have 2x higher failure rates than small transactions. Additional bank authentication steps and fraud checks cause higher failure rates for large amounts.",
        "tags": ["high_value", "amount", "failure_rate", "authentication", "large", "expensive"]
    },
    {
        "id": "bench_006",
        "text": "UPI transactions peak between 10 AM - 12 PM and 6 PM - 9 PM. Late night transactions (12 AM - 5 AM) are 80% lower in volume but have 10-15% higher fraud rates.",
        "tags": ["peak_hours", "timing", "volume", "fraud", "pattern", "hour", "night"]
    },
    {
        "id": "fraud_001",
        "text": "Common UPI fraud red flags: transactions at unusual hours (12AM-5AM), rapid repeat transactions within 5 minutes, transactions to new receivers above Rs 5000, sudden spike in frequency.",
        "tags": ["fraud", "red_flags", "detection", "pattern", "suspicious", "alert"]
    },
    {
        "id": "fraud_002",
        "text": "Age group 18-25 has 2x higher fraud victimization rate than 36-45. Older users (60+) are 3x more likely to fall for UPI scams. Social engineering is the primary fraud method.",
        "tags": ["fraud", "age_group", "demographics", "scam", "elderly", "young"]
    },
    {
        "id": "fraud_003",
        "text": "States with highest UPI fraud rates: Jharkhand, Bihar, Rajasthan (Jamtara scam belt). States with lowest fraud: Kerala, Karnataka, Maharashtra. Metro cities have 60% of total fraud volume.",
        "tags": ["fraud", "state", "geography", "jamtara", "region", "location"]
    },
    {
        "id": "fraud_004",
        "text": "P2P transactions above Rs 50,000 have fraud rates 5x the average. Travel and Entertainment merchant categories have higher fraud incidence than Food or Retail.",
        "tags": ["fraud", "p2p", "high_value", "merchant_category", "travel", "entertainment"]
    },
    {
        "id": "spend_001",
        "text": "Age group 26-35 has highest UPI transaction volume and average amount. Age group 18-25 has highest frequency but lower average amounts. Age group 60+ prefers smaller, more frequent transactions.",
        "tags": ["age_group", "spending", "volume", "frequency", "demographic", "young", "elderly"]
    },
    {
        "id": "spend_002",
        "text": "P2M average transaction amount is 30-40% higher than P2P. Food and Retail have highest transaction counts. Travel and Entertainment have highest average amounts.",
        "tags": ["p2m", "p2p", "merchant_category", "amount", "spending", "food", "retail", "travel"]
    },
    {
        "id": "spend_003",
        "text": "Monday has highest transaction count for P2M (merchant payments). Sunday is highest for P2P (personal transfers). Festival seasons see 3-5x normal transaction volumes.",
        "tags": ["weekday", "weekend", "p2p", "p2m", "seasonal", "festival", "monday", "sunday"]
    },
    {
        "id": "spend_004",
        "text": "PhonePe and Google Pay together account for 80%+ of UPI transactions. Paytm has highest average transaction amount. BHIM UPI has highest merchant penetration in rural areas.",
        "tags": ["upi_app", "phonePe", "googlepay", "paytm", "bhim", "market_share", "app"]
    },
    {
        "id": "bank_001",
        "text": "Public sector banks (SBI, PNB, BOI) have higher failure rates (6-8%) than private banks (HDFC, ICICI, Axis) which maintain 3-5%. Payment banks have the lowest failure rates (1-2%).",
        "tags": ["bank", "failure_rate", "public_bank", "private_bank", "sbi", "hdfc", "icici"]
    },
    {
        "id": "bank_002",
        "text": "Bank server downtime causes 35% of UPI failures. Insufficient balance causes 30%. Wrong UPI ID causes 20%. Network timeout causes 15% of failures.",
        "tags": ["failure_reason", "bank", "downtime", "timeout", "balance", "wrong_id", "cause"]
    },
    {
        "id": "insight_001",
        "text": "Nexus dataset baseline: 250,000 transactions 2024, success rate ~95%, failure rate ~5%, fraud flag rate ~0.19%, average amount Rs 1,311. These are the baseline benchmarks.",
        "tags": ["baseline", "dataset", "nexus", "benchmark", "overall", "average"]
    },
    {
        "id": "insight_002",
        "text": "Failure rate thresholds for this dataset: above 7% is HIGH concern, 4-7% is NORMAL, below 4% is GOOD. Fraud rate above 0.3% is concerning. These apply to the Nexus UPI dataset.",
        "tags": ["threshold", "failure_rate", "fraud_rate", "good", "high", "normal", "concern"]
    },
]


class FinancialKnowledgeRAG:
    """
    Financial domain knowledge retrieval using keyword matching.
    Fast, no model download required. Works offline.
    """

    def __init__(self, persist_directory: str = "../../data/financial_rag_db"):
        # No heavy initialization - just load knowledge in memory
        self.knowledge = FINANCIAL_KNOWLEDGE
        print(f"Financial Knowledge RAG ready ({len(self.knowledge)} knowledge entries)")

    def retrieve(self, query: str, n_results: int = 3) -> str:
        """
        Retrieve relevant financial knowledge using keyword matching.
        Fast, no network, no model required.
        """
        query_lower = query.lower()
        query_words = set(query_lower.split())

        scored = []
        for item in self.knowledge:
            # Score = number of matching tags + partial text match
            tag_matches = sum(1 for tag in item["tags"] if tag in query_lower or any(w in tag for w in query_words if len(w) > 3))
            text_matches = sum(1 for word in query_words if len(word) > 3 and word in item["text"].lower())
            score = tag_matches * 2 + text_matches

            if score > 0:
                scored.append((score, item["text"]))

        # Sort by relevance, take top n
        scored.sort(key=lambda x: x[0], reverse=True)
        top = [text for _, text in scored[:n_results]]

        return "\n\n".join(top) if top else ""

    def should_use_rag(self, question: str) -> bool:
        """Determine if RAG context would help for this question."""
        rag_triggers = [
            "why", "reason", "cause", "because", "explain",
            "normal", "good", "bad", "high", "low", "unusual",
            "benchmark", "standard", "expected", "compare",
            "should", "typical", "pattern", "trend", "concern",
            "rbi", "npci", "regulation", "guideline", "rule",
            "what does", "what is", "tell me about"
        ]
        question_lower = question.lower()
        return any(trigger in question_lower for trigger in rag_triggers)
