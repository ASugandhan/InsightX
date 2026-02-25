"""
InsightX System - Full Dynamic Pipeline
Flow: Question -> RAG (domain context) -> Gemini NLU (SQL) -> DuckDB (full 250k) -> Intelligence Layer -> Gemini Formatter -> Answer
"""

import sys
import time
import pandas as pd

sys.path.append('src')

from analytics.engine import AnalyticsEngine
from analytics.intelligence_layer import IntelligenceLayer
from nlp.gemini_nlu import GeminiNLU
from explainability.gemini_formatter import GeminiResponseFormatter
from rag.financial_knowledge_rag import FinancialKnowledgeRAG


class InsightXSystem:
    def __init__(self, csv_path: str):
        print("\n" + "="*60)
        print("  INSIGHTX - INTELLIGENT UPI ANALYTICS v2.0")
        print("="*60)

        # Core engine - loads ALL 250,000 rows into DuckDB
        self.analytics = AnalyticsEngine(csv_path)

        # Financial Knowledge RAG - answers WHY using domain expertise
        rag_dir = csv_path.replace('upi_transactions_2024.csv', 'financial_rag_db')
        self.rag = FinancialKnowledgeRAG(persist_directory=rag_dir)

        # Gemini NLU - understands questions, writes SQL dynamically
        self.nlu = GeminiNLU()

        # Intelligence Layer - YOUR original analytics: anomalies, benchmarks, trends
        self.intelligence = IntelligenceLayer(self.analytics.precomputed)

        # Gemini Formatter - converts data + insights into natural language
        self.formatter = GeminiResponseFormatter()

        # Conversation memory - full history passed to Gemini for context
        self.conversation_history = []

        print("\n✓ InsightX ready! Ask me anything about your UPI data.")
        print("="*60 + "\n")

    def ask(self, question: str) -> dict:
        """
        Main entry point. Ask anything in natural language.
        Full pipeline: RAG -> Gemini NLU -> DuckDB (250k) -> Intelligence -> Gemini Format

        Returns dict with answer, sql, insights, anomalies, chart data etc.
        """

        print(f"\n{'='*60}")
        print(f"Q: {question}")
        start_total = time.time()

        # ----------------------------------------------------------------
        # STEP 1: RAG - Retrieve financial domain knowledge (the WHY layer)
        # ----------------------------------------------------------------
        rag_context = ""
        if self.rag.should_use_rag(question):
            print("→ Retrieving financial domain knowledge...")
            rag_context = self.rag.retrieve(question, n_results=3)
            if rag_context:
                print(f"  ✓ Found relevant domain knowledge")

        # ----------------------------------------------------------------
        # STEP 2: Gemini NLU - Understand question, write SQL
        # ----------------------------------------------------------------
        print("→ Understanding question & generating SQL...")
        nlu_result = self.nlu.understand(
            question=question,
            conversation_history=self.conversation_history,
            rag_context=rag_context
        )

        sql = nlu_result.get("sql", "")
        intent = nlu_result.get("intent", question)
        entities = nlu_result.get("entities", [])
        is_followup = nlu_result.get("is_followup", False)

        print(f"  Intent: {intent}")
        print(f"  SQL: {sql[:120]}{'...' if len(sql) > 120 else ''}")

        # ----------------------------------------------------------------
        # STEP 3: DuckDB - Execute SQL on FULL 250,000 rows
        # ----------------------------------------------------------------
        print("→ Querying full 250,000 row dataset...")
        start_query = time.time()
        result = self._execute_sql_safely(question, sql)
        exec_ms = (time.time() - start_query) * 1000
        print(f"  ✓ {len(result)} result rows in {exec_ms:.1f}ms")

        # ----------------------------------------------------------------
        # STEP 4: Intelligence Layer - Analyze, detect anomalies, benchmark
        # ----------------------------------------------------------------
        print("→ Running intelligence analysis...")
        intelligence = self.intelligence.analyze(result, intent, sql)
        if intelligence.get("anomalies"):
            print(f"  ⚠ {len(intelligence['anomalies'])} anomalies detected")
        if intelligence.get("benchmark_comparison"):
            print(f"  ✓ Benchmark comparison ready")

        # ----------------------------------------------------------------
        # STEP 5: Gemini Formatter - Natural language answer with insights
        # ----------------------------------------------------------------
        print("→ Generating natural language answer...")
        answer = self.formatter.format(
            question=question,
            result=result,
            intent=intent,
            intelligence=intelligence,
            rag_context=rag_context
        )

        total_ms = (time.time() - start_total) * 1000
        print(f"  ✓ Done in {total_ms:.0f}ms total\n")
        print(f"Answer: {answer}")
        print("="*60)

        # ----------------------------------------------------------------
        # STEP 6: Update conversation history for follow-up context
        # ----------------------------------------------------------------
        self.conversation_history.append({"role": "user", "content": question})
        self.conversation_history.append({"role": "assistant", "content": answer})
        # Keep last 20 messages (10 exchanges)
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]

        return {
            "answer": answer,
            "sql": sql,
            "result": result,
            "execution_ms": exec_ms,
            "total_ms": total_ms,
            "insights": intelligence.get("insights", []),
            "anomalies": intelligence.get("anomalies", []),
            "proactive_tips": intelligence.get("proactive_tips", []),
            "benchmark_comparison": intelligence.get("benchmark_comparison", ""),
            "rag_context_used": bool(rag_context),
            "row_count": len(result),
            "intent": intent,
            "entities": entities,
            "is_followup": is_followup
        }

    def _execute_sql_safely(self, question: str, sql: str) -> pd.DataFrame:
        """Execute SQL, auto-fix with Gemini if it fails."""
        try:
            return self.analytics.query(sql)
        except Exception as e:
            print(f"  ⚠ SQL error: {e}. Asking Gemini to fix...")
            try:
                fixed = self.nlu.fix_sql(question, sql, str(e))
                return self.analytics.query(fixed)
            except Exception as e2:
                print(f"  ✗ Fix also failed: {e2}")
                return pd.DataFrame()

    def start_fresh(self):
        """Clear conversation history for a new chat."""
        self.conversation_history = []
        print("✓ Started fresh conversation")

    def get_overview(self) -> dict:
        """Get dataset overview stats."""
        overall = self.analytics.precomputed.get('overall', {})
        by_type = self.analytics.precomputed.get('by_type', [])
        by_device = self.analytics.precomputed.get('by_device', [])
        return {
            "overall": overall,
            "by_type": by_type,
            "by_device": by_device,
            "summary": (
                f"250,000 UPI transactions | "
                f"₹{overall.get('avg_amount', 0):,.0f} avg amount | "
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
