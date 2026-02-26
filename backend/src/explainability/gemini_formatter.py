"""
Gemini Response Formatter
Takes raw SQL results + intelligence insights and formats them
into a natural, conversational response like a financial analyst.
"""

import os
import json
import pandas as pd
from dotenv import load_dotenv
from google import genai

load_dotenv()


class GeminiResponseFormatter:
    """
    Uses Gemini to format SQL results into natural language answers.
    Combines data + insights into a conversational response.
    """

    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-flash-lite-latest"
        print("GeminiResponseFormatter initialized")

    def format(self, question: str, result: pd.DataFrame, intent: str,
               intelligence: dict, rag_context: str = "") -> str:
        """
        Format query result into a natural conversational answer.

        Args:
            question: Original user question
            result: SQL query result as DataFrame
            intent: What the user was asking
            intelligence: Dict from IntelligenceLayer with insights/anomalies
            rag_context: Optional financial domain context from RAG

        Returns:
            Natural language response string
        """

        # Convert result to readable format
        if result is None or result.empty:
            result_str = "No data found."
        elif result.shape[0] == 1:
            result_str = result.iloc[0].to_dict().__str__()
        else:
            result_str = result.to_string(index=False)

        # Build insights context
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

        tips_str = ""
        if tips:
            tips_str = "\n\nYou might also want to explore:\n" + "\n".join(f"- {t}" for t in tips)

        prompt = f"""You are InsightX — an intelligent financial analyst AI for UPI transaction data.

The user asked: "{question}"
Intent: {intent}

Query Result:
{result_str}

{insights_str}{rag_str}

Your job:
- Answer the question directly and clearly
- Use the actual numbers from the result (never make up numbers)
- Explain what the numbers mean in simple terms
- Mention any interesting patterns or anomalies if present
- Compare to benchmarks if available
- Be conversational and natural — like a smart analyst friend, not a robot
- Use ₹ symbol for amounts
- Format large numbers with commas (e.g., 1,25,000)
- Keep it concise but insightful — 2-4 sentences normally, more if complex
- Do NOT say "based on the query result" or "according to the data" — just answer naturally
- End with the proactive tips if any: {tips_str}

Respond naturally. No bullet points unless showing a breakdown.
"""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            print(f"Gemini formatter error: {e}")
            # Fallback: plain text result
            return self._fallback_format(question, result, intelligence)

    def _fallback_format(self, question: str, result: pd.DataFrame, intelligence: dict) -> str:
        """Plain text fallback when Gemini is unavailable."""
        if result is None or result.empty:
            return "I couldn't find any data for your query. Please try rephrasing."

        lines = []
        if result.shape[0] == 1:
            row = result.iloc[0]
            for col, val in row.items():
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
