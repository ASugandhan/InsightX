"""
InsightX System - Full Dynamic Pipeline v2.1
Fixes applied:
  Issue 1: Anti-hallucination via SchemaValidator
  Issue 2: Conversation history for follow-up context
  Issue 3: Smart defaults + query clarification for vague queries
  Issue 4: Robust SQL auto-fix with SQLFixer
  Task 3:  Guardrails on all input/output/SQL
"""

import sys
import time
import pandas as pd

sys.path.append('src')

from analytics.engine import AnalyticsEngine
from analytics.intelligence_layer import IntelligenceLayer
from nlp.gemini_nlu import GeminiNLU
from nlp.schema_validator import SchemaValidator
from nlp.query_clarifier import QueryClarifier
from nlp.sql_fixer import SQLFixer
from explainability.gemini_formatter import GeminiResponseFormatter
from rag.financial_knowledge_rag import FinancialKnowledgeRAG
from guardrails import Guardrails


class InsightXSystem:
    def __init__(self, csv_path: str):
        print("\n" + "="*60)
        print("  INSIGHTX - INTELLIGENT UPI ANALYTICS v2.1")
        print("="*60)

        self.analytics = AnalyticsEngine(csv_path)
        rag_dir = csv_path.replace('upi_transactions_2024.csv', 'financial_rag_db')
        self.rag = FinancialKnowledgeRAG(persist_directory=rag_dir)
        self.nlu = GeminiNLU()
        self.intelligence = IntelligenceLayer(self.analytics.precomputed)
        self.formatter = GeminiResponseFormatter()

        # Issue 1: Schema validation (anti-hallucination)
        self.schema_validator = SchemaValidator()

        # Issue 3: Query clarifier (vague query handling)
        self.query_clarifier = QueryClarifier()

        # Issue 4: Robust SQL fixer
        self.sql_fixer = SQLFixer()

        # Task 3: Guardrails
        self.guardrails = Guardrails(rate_limit_per_minute=30)

        # Issue 2: Conversation memory
        self.conversation_history = []

        print("\n InsightX v2.1 ready! All fixes + guardrails active.")
        print("="*60 + "\n")

    def ask(self, question: str, session_id: str = "default") -> dict:
        """
        Main entry point with all fixes + guardrails applied.
        """
        print(f"\n{'='*60}")
        print(f"Q: {question}")
        start_total = time.time()

        # ----------------------------------------------------------------
        # GUARDRAIL: Validate input (rate limit + content)
        # ----------------------------------------------------------------
        is_safe, rejection_msg = self.guardrails.check_input(question, session_id)
        if not is_safe:
            print(f"  BLOCKED: {rejection_msg}")
            return self._blocked_response(question, rejection_msg)

        # Sanitize input
        question = self.guardrails.sanitize_input(question)

        # ----------------------------------------------------------------
        # ISSUE 3: Check for vague/ambiguous queries first
        # ----------------------------------------------------------------
        clarifier_result = self.query_clarifier.analyze(question)

        if clarifier_result["is_ambiguous"] and clarifier_result["clarification_needed"]:
            # Return clarification question without calling Gemini
            clarification = clarifier_result["clarification_needed"]
            print(f"  Ambiguous query - requesting clarification")
            self.conversation_history.append({"role": "user", "content": question})
            self.conversation_history.append({"role": "assistant", "content": clarification})
            return {
                "answer": clarification,
                "sql": "", "result": pd.DataFrame(),
                "execution_ms": 0, "total_ms": 0,
                "insights": [], "anomalies": [], "proactive_tips": [],
                "benchmark_comparison": "", "rag_context_used": False,
                "row_count": 0, "intent": "clarification_needed",
                "entities": [], "is_followup": False,
                "needs_clarification": True
            }

        # ----------------------------------------------------------------
        # STEP 1: RAG - Financial domain knowledge
        # ----------------------------------------------------------------
        rag_context = ""
        if self.rag.should_use_rag(question):
            print("  Retrieving financial domain knowledge...")
            rag_context = self.rag.retrieve(question, n_results=3)
            if rag_context:
                print(f"  Found relevant domain knowledge")

        # ----------------------------------------------------------------
        # ISSUE 2 + STEP 2: Gemini NLU with conversation history
        # ----------------------------------------------------------------
        print("  Understanding question & generating SQL...")

        # Use smart default SQL if available (Issue 3)
        if clarifier_result["has_smart_default"]:
            sql = clarifier_result["smart_default_sql"]
            intent = clarifier_result["smart_default_intent"]
            entities = []
            is_followup = False
            print(f"  Using smart default SQL for vague query")
        else:
            nlu_result = self.nlu.understand(
                question=question,
                conversation_history=self.conversation_history,  # Issue 2
                rag_context=rag_context
            )
            sql = nlu_result.get("sql", "")
            intent = nlu_result.get("intent", question)
            entities = nlu_result.get("entities", [])
            is_followup = nlu_result.get("is_followup", False)

        # Apply temporal rewrite if detected (Issue 3)
        if clarifier_result.get("temporal_filter") and sql:
            sql = self.query_clarifier.apply_temporal_rewrite(sql, clarifier_result["temporal_filter"])

        print(f"  Intent: {intent}")
        print(f"  SQL: {sql[:120]}{'...' if len(sql) > 120 else ''}")

        # ----------------------------------------------------------------
        # ISSUE 1: Validate SQL for hallucinations
        # ----------------------------------------------------------------
        sql_validation = self.schema_validator.validate_sql(sql)
        if not sql_validation["is_valid"]:
            print(f"  HALLUCINATION DETECTED: {sql_validation['issues']}")
            # Try to fix with Gemini
            sql = self.sql_fixer.fix(question, sql, str(sql_validation["issues"]))
            print(f"  Fixed SQL: {sql[:100]}...")

        # ----------------------------------------------------------------
        # GUARDRAIL: Validate SQL safety before execution
        # ----------------------------------------------------------------
        sql_safe, sql_msg = self.guardrails.check_sql(sql)
        if not sql_safe:
            print(f"  UNSAFE SQL blocked: {sql_msg}")
            sql = "SELECT COUNT(*) as total_transactions, ROUND(AVG(amount_inr),2) as avg_amount FROM transactions"

        # ----------------------------------------------------------------
        # STEP 3: DuckDB - Execute on full 250,000 rows
        # ----------------------------------------------------------------
        print("  Querying full 250,000 row dataset...")
        start_query = time.time()
        result = self._execute_sql_safely(question, sql)
        exec_ms = (time.time() - start_query) * 1000
        print(f"  {len(result)} result rows in {exec_ms:.1f}ms")

        # ----------------------------------------------------------------
        # STEP 4: Intelligence Layer
        # ----------------------------------------------------------------
        print("  Running intelligence analysis...")
        intelligence = self.intelligence.analyze(result, intent, sql)

        # ----------------------------------------------------------------
        # STEP 5: Gemini Formatter
        # ----------------------------------------------------------------
        print("  Generating natural language answer...")
        raw_answer = self.formatter.format(
            question=question, result=result, intent=intent,
            intelligence=intelligence, rag_context=rag_context
        )

        # ----------------------------------------------------------------
        # GUARDRAIL: Sanitize output
        # ----------------------------------------------------------------
        answer = self.guardrails.check_output(raw_answer)

        total_ms = (time.time() - start_total) * 1000
        print(f"  Done in {total_ms:.0f}ms total\n")
        print(f"Answer: {answer}")
        print("="*60)

        # ----------------------------------------------------------------
        # ISSUE 2: Update conversation history
        # ----------------------------------------------------------------
        self.conversation_history.append({"role": "user", "content": question})
        self.conversation_history.append({"role": "assistant", "content": answer})
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]

        return {
            "answer": answer, "sql": sql, "result": result,
            "execution_ms": exec_ms, "total_ms": total_ms,
            "insights": intelligence.get("insights", []),
            "anomalies": intelligence.get("anomalies", []),
            "proactive_tips": intelligence.get("proactive_tips", []),
            "benchmark_comparison": intelligence.get("benchmark_comparison", ""),
            "rag_context_used": bool(rag_context),
            "row_count": len(result), "intent": intent,
            "entities": entities, "is_followup": is_followup,
            "needs_clarification": False
        }

    def _execute_sql_safely(self, question: str, sql: str) -> pd.DataFrame:
        """Execute SQL with Issue 4 fix: robust auto-correction."""
        try:
            return self.analytics.query(sql)
        except Exception as e:
            print(f"  SQL error: {e}. Auto-fixing...")
            try:
                fixed_sql = self.sql_fixer.fix(question, sql, str(e))
                # Validate fixed SQL is safe before executing
                safe, msg = self.guardrails.check_sql(fixed_sql)
                if not safe:
                    print(f"  Fixed SQL also unsafe: {msg}")
                    return pd.DataFrame()
                return self.analytics.query(fixed_sql)
            except Exception as e2:
                print(f"  Fix also failed: {e2}")
                return pd.DataFrame()

    def _blocked_response(self, question: str, reason: str) -> dict:
        return {
            "answer": reason, "sql": "", "result": pd.DataFrame(),
            "execution_ms": 0, "total_ms": 0, "insights": [],
            "anomalies": [], "proactive_tips": [], "benchmark_comparison": "",
            "rag_context_used": False, "row_count": 0,
            "intent": "blocked", "entities": [], "is_followup": False,
            "needs_clarification": False, "blocked": True
        }

    def start_fresh(self):
        """Clear conversation history."""
        self.conversation_history = []
        print("Started fresh conversation")

    def get_overview(self) -> dict:
        overall = self.analytics.precomputed.get('overall', {})
        by_type = self.analytics.precomputed.get('by_type', [])
        by_device = self.analytics.precomputed.get('by_device', [])
        return {
            "overall": overall, "by_type": by_type, "by_device": by_device,
            "summary": (
                f"250,000 UPI transactions | "
                f"Rs{overall.get('avg_amount', 0):,.0f} avg amount | "
                f"{overall.get('success_rate', 0):.1f}% success rate | "
                f"{overall.get('failure_rate', 0):.1f}% failure rate | "
                f"{overall.get('fraud_flag_rate', 0):.2f}% fraud rate"
            )
        }


if __name__ == "__main__":
    system = InsightXSystem('../data/upi_transactions_2024.csv')
    overview = system.get_overview()
    print("\nDataset:", overview["summary"])

    questions = [
        "How many total transactions are there?",
        "What is the failure rate for P2P transactions above 5000 rupees?",
        "Which device type has the highest failure rate?",
        "Why might weekends have more failures?",
        "Show fraud trends by age group",
        "What about by state?",
    ]
    for q in questions:
        system.ask(q)
