"""
Gemini Response Formatter v2.2 - Uses 5-key rotation system
Formats SQL results into natural language answers like a financial analyst.
"""

import os
import pandas as pd
from dotenv import load_dotenv
from nlp.key_manager import get_key_manager

load_dotenv()


class GeminiResponseFormatter:
    def __init__(self):
        self.key_manager = get_key_manager()
        self.model = "models/gemini-flash-latest"
        print("GeminiResponseFormatter initialized (5-key rotation)")

    def format(self, question: str, result: pd.DataFrame, intent: str,
               intelligence: dict, rag_context: str = "") -> str:

        if result is None or result.empty:
            result_str = "No data found."
        elif result.shape[0] == 1:
            result_str = str(result.iloc[0].to_dict())
        else:
            result_str = result.to_string(index=False)

        insights = intelligence.get("insights", [])
        anomalies = intelligence.get("anomalies", [])
        benchmark = intelligence.get("benchmark_comparison", "")
        tips = intelligence.get("proactive_tips", [])

        insights_str = ""
        if insights:
            insights_str += "Key insights: " + "; ".join(insights) + "\n"
        if anomalies:
            insights_str += "Anomalies detected: " + "; ".join(anomalies) + "\n"
        if benchmark:
            insights_str += "Benchmark comparison: " + benchmark + "\n"

        rag_str = f"\nFinancial domain context:\n{rag_context}" if rag_context else ""
        tips_str = ("\n\nYou might also want to explore:\n" + "\n".join(f"- {t}" for t in tips)) if tips else ""

        prompt = f"""You are InsightX - an intelligent financial analyst AI for UPI transaction data.

The user asked: "{question}"
Intent: {intent}

Query Result:
{result_str}

{insights_str}{rag_str}

Your job:
- Answer the question directly and clearly using the actual numbers
- Explain what the numbers mean in simple terms
- Mention interesting patterns or anomalies if present
- Compare to benchmarks if available
- Be conversational and natural - like a smart analyst, not a robot
- Use Rs symbol for amounts, format large numbers with commas
- Keep it concise but insightful (2-4 sentences normally, more if complex)
- Do NOT say "based on the query result" or "according to the data"
{tips_str}

Respond naturally. No bullet points unless showing a breakdown."""

        try:
            text = self.key_manager.generate(model=self.model, contents=prompt)
            return text.strip()
        except Exception as e:
            print(f"GeminiFormatter all keys failed: {e}")
            return self._fallback_format(question, result, intelligence)

    def _fallback_format(self, question: str, result: pd.DataFrame, intelligence: dict) -> str:
        if result is None or result.empty:
            return "I couldn't find any data for your query. Please try rephrasing."
        lines = []
        if result.shape[0] == 1:
            for col, val in result.iloc[0].items():
                col_clean = col.replace('_', ' ').title()
                if isinstance(val, float):
                    lines.append(f"{col_clean}: {val:,.2f}")
                elif isinstance(val, int):
                    lines.append(f"{col_clean}: {val:,}")
                else:
                    lines.append(f"{col_clean}: {val}")
            answer = "\n".join(lines)
        else:
            answer = result.to_string(index=False)
        insights = intelligence.get("insights", [])
        if insights:
            answer += "\n\n" + "\n".join(insights)
        tips = intelligence.get("proactive_tips", [])
        if tips:
            answer += "\n\nYou might also explore:\n" + "\n".join(f"- {t}" for t in tips)
        return answer

