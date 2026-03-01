"""
Gemini Response Formatter v2.3 - Uses 5-key rotation system
Formats SQL results into clean, structured, user-facing answers.
"""

import re
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
               intelligence: dict, rag_context: str = "", stop_event=None) -> str:

        result_str = self._format_result_for_prompt(result)

        insights = intelligence.get("insights", [])
        anomalies = intelligence.get("anomalies", [])
        benchmark = intelligence.get("benchmark_comparison", "")
        tips = intelligence.get("proactive_tips", [])

        insights_str = ""
        if insights:
            insights_str += "Key insights: " + "; ".join(insights[:5]) + "\n"
        if anomalies:
            insights_str += "Anomalies detected: " + "; ".join(anomalies[:5]) + "\n"
        if benchmark:
            insights_str += "Benchmark comparison: " + benchmark + "\n"

        rag_str = f"\nFinancial domain context:\n{rag_context}" if rag_context else ""
        tips_str = ("\n\nOptional follow-up ideas:\n" + "\n".join(f"- {t}" for t in tips[:3])) if tips else ""

        prompt = f"""You are Nexus, a financial analytics assistant for UPI data.
If you introduce yourself, use the name "Nexus" (never "InsightX").

User question: "{question}"
Intent: {intent}

Query result:
{result_str}

{insights_str}{rag_str}

Return a clean, organized long-form answer in this exact structure:
Overview:
<2-4 lines answering the question directly>

Detailed breakdown:
- <metric/finding 1 with value>
- <metric/finding 2 with value>
- <metric/finding 3 with value>
- <additional findings if relevant>

Interpretation:
<1-2 short paragraphs explaining what the numbers imply>

Assumptions and caveats:
- <assumption/limitation 1>
- <assumption/limitation 2>

Recommended next checks:
- <next analysis 1>
- <next analysis 2>

Rules:
- Keep it organized, detailed, and scannable (ChatGPT-like).
- Use plain text. No LaTeX, no equations, no code fences.
- Use currency as "Rs " with comma-separated numbers.
- Do not add hype/fluff openings.
- If data is empty, say that directly and suggest 1-2 better queries.
{tips_str}
"""

        try:
            text = self.key_manager.generate(model=self.model, contents=prompt, stop_event=stop_event)
            if text == "ABORTED":
                return "Query generation stopped by user."
            return self._clean_response(text)
        except Exception as e:
            print(f"GeminiFormatter all keys failed: {e}")
            return self._fallback_format(result, intelligence)

    def _fallback_format(self, result: pd.DataFrame, intelligence: dict) -> str:
        if result is None or result.empty:
            return (
                "Short answer:\n"
                "I could not find matching data for this query.\n\n"
                "Key numbers:\n"
                "- No rows returned\n\n"
                "What this means:\n"
                "The current query filters may be too narrow or mismatched.\n\n"
                "Next step:\n"
                "Try a broader query, for example: overall revenue by month."
            )

        lines = ["Short answer:", "Here is the latest result from your query.", "", "Key numbers:"]
        if result.shape[0] == 1:
            for col, val in result.iloc[0].items():
                col_clean = col.replace('_', ' ').title()
                if isinstance(val, float):
                    lines.append(f"- {col_clean}: {val:,.2f}")
                elif isinstance(val, int):
                    lines.append(f"- {col_clean}: {val:,}")
                else:
                    lines.append(f"- {col_clean}: {val}")
        else:
            preview = result.head(3)
            for _, row in preview.iterrows():
                row_parts = [f"{c}: {row[c]}" for c in preview.columns[:3]]
                lines.append("- " + " | ".join(row_parts))
            if len(result) > 3:
                lines.append(f"- ... and {len(result) - 3} more rows")

        lines += ["", "What this means:", "This summarizes the latest transaction pattern from the dataset."]

        next_step = None
        insights = intelligence.get("insights", [])
        tips = intelligence.get("proactive_tips", [])
        if insights:
            next_step = insights[0]
        elif tips:
            next_step = tips[0]
        else:
            next_step = "Ask a comparison query (for example, month-over-month trend) for deeper insight."

        lines += ["", "Next step:", next_step]
        return "\n".join(lines).strip()

    def _format_result_for_prompt(self, result: pd.DataFrame) -> str:
        if result is None or result.empty:
            return "No data found."
        if result.shape[0] == 1:
            return str(result.iloc[0].to_dict())

        preview = result.head(15)
        return (
            f"Rows: {len(result)}, Columns: {list(result.columns)}\n"
            f"Preview:\n{preview.to_string(index=False)}"
        )

    def _clean_response(self, text: str) -> str:
        cleaned = (text or "").strip()
        cleaned = re.sub(r"^```[a-zA-Z]*\\s*", "", cleaned)
        cleaned = re.sub(r"\\s*```$", "", cleaned)
        cleaned = cleaned.replace("\\text{Rs }", "Rs ")
        cleaned = cleaned.replace("\\times", "x")
        cleaned = cleaned.replace("$", "")
        cleaned = re.sub(r"\\s{3,}", "\n\n", cleaned)
        return cleaned.strip()
