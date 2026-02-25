"""
LLM-based Query Parser using Gemini API (NEW SDK)
Falls back to rule-based parser if LLM fails
CLEAN + FIXED VERSION
"""

import os
import json
import re
from enum import Enum
from typing import List, Dict
from dataclasses import dataclass
from nlp.parser import QueryIntent

from google import genai
from dotenv import load_dotenv


from nlp.schema_validator import SchemaValidator
from nlp.query_clarifier import QueryClarifier
from nlp.temporal_parser import TemporalParser
from nlp.context_defaults import ContextDefaults
from rag.query_rewriter import QueryRewriter
from explainability.confidence_calibrator import ConfidenceCalibrator
try:
    from rag.query_enhancer import QueryEnhancer
    RAG_AVAILABLE = True
except Exception as e:
    RAG_AVAILABLE = False
# -----------------------------------------------------------------------------
# ENV SETUP
# -----------------------------------------------------------------------------
load_dotenv()

# -----------------------------------------------------------------------------
# DATA STRUCTURES
# -----------------------------------------------------------------------------

@dataclass
class ParsedQuery:
    intent: QueryIntent
    metrics: List[str]
    dimensions: List[str]
    filters: Dict
    original_query: str
    confidence: float = 0.9


# -----------------------------------------------------------------------------
# RULE-BASED FALLBACK PARSER
# -----------------------------------------------------------------------------

class QueryParser:
    """Deterministic rule-based parser"""

    def parse(self, query: str) -> ParsedQuery:
        q = query.lower()

        intent = QueryIntent.DESCRIPTIVE
        metrics, dimensions, filters = [], [], {}

        # ---- Intent ----
        if any(w in q for w in ["compare", "difference", "which is higher"]):
            intent = QueryIntent.COMPARATIVE
        elif any(w in q for w in ["trend", "over time", "peak", "by hour"]):
            intent = QueryIntent.TEMPORAL
        elif any(w in q for w in ["break down", "group by"]):
            intent = QueryIntent.SEGMENTATION
        elif "fraud" in q:
            intent = QueryIntent.RISK

        # ---- Metrics ----
        if "average" in q or "avg" in q:
            metrics.append("avg_amount")
        if "total" in q or "volume" in q:
            metrics.append("total_amount")
        if "how many" in q or "count" in q:
            metrics.append("count")
        if "success rate" in q:
            metrics.append("success_rate")
            filters["transaction_status"] = "SUCCESS"
        if "failure rate" in q:
            metrics.append("failure_rate")
            filters["transaction_status"] = "FAILED"
        if "fraud" in q:
            metrics.append("fraud_flag_rate")
            filters["fraud_flag"] = 1

        if not metrics:
            metrics.append("count")

        # ---- Dimensions ----
        if "device" in q:
            dimensions.append("device_type")
        if "age group" in q:
            dimensions.append("sender_age_group")
        if "merchant" in q:
            dimensions.append("merchant_category")
        if "hour" in q or "time" in q:
            dimensions.append("hour_of_day")
        if "state" in q:
            dimensions.append("sender_state")

        # ---- Filters ----
        if "p2p" in q:
            filters["transaction_type"] = "P2P"
        if "p2m" in q:
            filters["transaction_type"] = "P2M"
        if "weekend" in q:
            filters["is_weekend"] = 1
        if "android" in q:
            filters["device_type"] = "Android"
        if "ios" in q:
            filters["device_type"] = "iOS"
        if "food" in q:
            filters["merchant_category"] = "Food"

        age_match = re.search(r"(18-25|26-35|36-45|46-55|56\+)", q)
        if age_match:
            filters["sender_age_group"] = age_match.group(1)

        # Amount filters: "above 5000", ">= 1000", "more than 500"
        amount_gte = re.search(r"(?:above|over|more than|>=|greater than)\s*[\u20b9rs\.]*\s*(\d+)", q)
        amount_lte = re.search(r"(?:below|under|less than|<=)\s*[\u20b9rs\.]*\s*(\d+)", q)
        if amount_gte:
            filters["amount_inr"] = {"gte": int(amount_gte.group(1))}
        if amount_lte:
            filters["amount_inr"] = {"lte": int(amount_lte.group(1))}

        # Status filters
        if "failed" in q and "transaction_status" not in filters:
            filters["transaction_status"] = "FAILED"
        if "success" in q and "successful" in q and "transaction_status" not in filters:
            filters["transaction_status"] = "SUCCESS"

        return ParsedQuery(
            intent=intent,
            metrics=metrics,
            dimensions=dimensions,
            filters=filters,
            original_query=query,
            confidence=0.6
        )


# -----------------------------------------------------------------------------
# GEMINI LLM PARSER (NEW SDK) WITH FALLBACK
# -----------------------------------------------------------------------------

class LLMParser:
    """LLM-powered query parser using NEW Gemini SDK"""

    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")

        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
            self.model = "models/gemini-flash-latest"
            print("âœ“ LLM Parser initialized (Gemini Flash - NEW SDK)")
        else:
            self.client = None
            print("âš ï¸ LLM unavailable â€” using rule-based parser only")

        self.fallback_parser = QueryParser()
        
        # Enhanced components for accuracy improvement
        self.query_clarifier = QueryClarifier()
        self.temporal_parser = TemporalParser()
        self.context_defaults = ContextDefaults()
        self.query_rewriter = QueryRewriter()
        self.confidence_calibrator = ConfidenceCalibrator()

        # Load schema for LLM prompt building
        self.schema = self._load_schema()

        # -------------------------------------------------
        # RAG Enhancer (optional, non-blocking)
        # -------------------------------------------------
        if RAG_AVAILABLE:
            try:
                self.query_enhancer = QueryEnhancer(
                    persist_directory="../data/chroma_db",
                    analytics_engine=self.analytics_engine if hasattr(self, "analytics_engine") else None
                    )
                print("âœ“ RAG enhancement enabled")
            except Exception as e:
                print(f"âš ï¸ RAG unavailable: {e}")
                self.query_enhancer = None
        else:
            self.query_enhancer = None

    def parse(self, query: str, use_llm: bool = True) -> ParsedQuery:
        """Enhanced parsing with all improvements"""
        
        # Step 1: Query clarification (check if needs clarification)
        # Note: Clarification handling should be done at API layer
        # Here we just detect it
        needs_clarification = self.query_clarifier.needs_clarification(query)
        if needs_clarification:
            # Could log or flag this, but continue with parsing
            pass
        
        # Step 2: Query rewriting
        rewritten_query = self.query_rewriter.rewrite(query)
        
        # Step 3: Temporal parsing
        temporal_filters = self.temporal_parser.parse_temporal(query)
        
        # Step 4: LLM parsing
        if use_llm and self.client:
            try:
                parsed = self._llm_parse(rewritten_query)
                
                # Add temporal filters
                parsed.filters.update(temporal_filters)
                
                # Apply context defaults
                parsed = self.context_defaults.apply_defaults(parsed, query)
                
                # RAG enhancement
                if self.query_enhancer:
                    enhanced, explanation = self.query_enhancer.enhance_parsed_query(query, parsed)
                    
                    # Calibrate confidence
                    complexity = self.confidence_calibrator.assess_query_complexity(enhanced)
                    rag_boost = (enhanced.confidence - parsed.confidence)
                    
                    # Will assess result quality after execution
                    enhanced.confidence, _ = self.confidence_calibrator.calibrate(
                        parsed.confidence, complexity, rag_boost, 1.0  # Assume good quality for now
                    )
                    
                    return enhanced
                
                return parsed
                
            except Exception as e:
                print(f"LLM error: {e}, falling back to rule-based parser")
                # Fall back to rule-based
        
        # Fallback parsing
        fallback = self.fallback_parser.parse(query)
        fallback.filters.update(temporal_filters)
        fallback = self.context_defaults.apply_defaults(fallback, query)
        
        if self.query_enhancer:
            fallback, _ = self.query_enhancer.enhance_parsed_query(query, fallback)
        
        return fallback
    def _llm_parse(self, query: str) -> ParsedQuery:
        """Parse using Gemini LLM with retry logic"""
    
        prompt = self._build_prompt(query)
    
        # Retry logic for rate limits
        import time
        max_retries = 3
        last_error = None
    
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config={
                        "temperature": 0.1,  # Low temperature = less hallucination
                        "top_p": 0.8,
                        "top_k": 20,
                        "max_output_tokens": 1000
                    }
                )
            
            # Success! Process response
                text = response.text.strip()
                text = text.replace("```json", "").replace("```", "").strip()
                result = json.loads(text)
            
            # âœ… NORMALIZE METRICS FORMAT
                metrics = result.get("metrics", [])
                normalized_metrics = []

                for metric in metrics:
                    if isinstance(metric, str) and metric.startswith("{"):
                        try:
                            import ast
                            metric = ast.literal_eval(metric)
                        except:
                            pass
                        
                    if isinstance(metric, dict):
                        # Gemini returned dict: {'aggregation': 'avg', 'column': 'amount_inr'}
                        agg = (metric.get('function', '') or metric.get('aggregation', '')).lower()
                        col = metric.get('column', '').lower()
                    
                    # Map to expected format
                        if agg == 'avg' and 'amount' in col:
                            normalized_metrics.append('avg_amount')
                        elif agg == 'sum' and 'amount' in col:
                            normalized_metrics.append('total_amount')
                        elif agg == 'count':
                            normalized_metrics.append('count')
                        elif agg == 'median' and 'amount' in col:
                            normalized_metrics.append('median_amount')
                        elif agg and col:
                            normalized_metrics.append(f"{agg}_{col.replace('_inr', '')}")
                    else:
                        # Already string format
                        normalized_metrics.append(str(metric))
            
            # Fallback to original if normalization failed
                if not normalized_metrics and metrics:
                    normalized_metrics = [str(m) for m in metrics]

                # If still no metrics, use count as default
                if not normalized_metrics:
                    normalized_metrics = ['count']

                return ParsedQuery(
                    intent=QueryIntent(result["intent"]),
                    metrics=normalized_metrics,
                    dimensions=result["dimensions"],
                    filters=result["filters"],
                    original_query=query,
                    confidence=result.get("confidence", 0.9)
                )

            except Exception as e:
                last_error = e
                error_str = str(e)
            
            # Check if it's a rate limit error
                if '503' in error_str or 'UNAVAILABLE' in error_str or 'high demand' in error_str.lower():
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 3  # 3s, 6s, 9s
                        print(f"â³ Gemini rate limited, retrying in {wait_time}s... (attempt {attempt + 2}/{max_retries})")
                        time.sleep(wait_time)
                        continue
            
                # Not a rate limit error, or final attempt - raise it
                raise
    
        # All retries failed
        raise last_error

    def _build_prompt(self, query: str) -> str:
        return f"""
You are an expert query parser for payment transaction analytics.

DATABASE SCHEMA:
{json.dumps(self.schema, indent=2)}

USER QUERY:
"{query}"

Return ONLY valid JSON.

FORMAT:
{{
  "intent": "descriptive|comparative|temporal|segmentation|risk",
  "metrics": [],
  "dimensions": [],
  "filters": {{}},
  "confidence": 0.95
}}
"""

    def _load_schema(self):
        return {
            "table": "transactions",
            "columns": [
                "transaction_type",
                "merchant_category",
                "amount_inr",
                "transaction_status",
                "sender_age_group",
                "sender_state",
                "device_type",
                "network_type",
                "fraud_flag",
                "hour_of_day",
                "is_weekend"
            ]
        }


# -----------------------------------------------------------------------------
# TESTING
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    parser = LLMParser()

    queries = [
        "What is the average P2M transaction amount?",
        "Compare failure rates by device type",
        "Which age group has the highest fraud flag rate?",
        "Show me weekend transactions in Maharashtra",
        "What are the peak transaction hours?",
        "Break down transactions by merchant category",
        "How many food transactions on Android devices?",
        "What is the success rate for 18-25 age group?",
        "Total transaction volume",
        "P2P transactions by state"
    ]

    for q in queries:
        print("\nQuery:", q)
        pq = parser.parse(q)
        print("Intent:", pq.intent.value)
        print("Metrics:", pq.metrics)
        print("Dimensions:", pq.dimensions)
        print("Filters:", pq.filters)
        print("Confidence:", pq.confidence)


