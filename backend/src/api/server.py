"""
FastAPI Server for InsightX v2.0
Full dynamic pipeline: RAG + Gemini NLU + DuckDB (250k) + Intelligence Layer + Gemini Formatter
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sys
import traceback
from datetime import datetime
import uuid
import pandas as pd

sys.path.append('..')
from main import InsightXSystem

app = FastAPI(title="InsightX API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize InsightX - loads all 250k rows on startup
system = InsightXSystem('../../data/upi_transactions_2024.csv')


# ============================================================================
# MODELS
# ============================================================================

class QueryRequest(BaseModel):
    question: str
    session_id: Optional[str] = None


class ChartDataItem(BaseModel):
    label: str
    value: float
    color: Optional[str] = None


class QueryResponse(BaseModel):
    id: str
    role: str = "ai"
    text: str
    timestamp: str
    sql: Optional[str] = None
    rowCount: int = 0
    executionMs: float = 0.0
    totalMs: float = 0.0
    insights: Optional[List[str]] = None
    anomalies: Optional[List[str]] = None
    proactiveTips: Optional[List[str]] = None
    benchmarkComparison: Optional[str] = None
    ragContextUsed: bool = False
    chartData: Optional[List[ChartDataItem]] = None
    intent: Optional[str] = None
    isFollowup: bool = False


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/")
async def health_check():
    overview = system.get_overview()
    return {
        "status": "healthy",
        "version": "2.0.0",
        "pipeline": "RAG + Gemini NLU + DuckDB(250k) + Intelligence + Gemini Format",
        "dataset": overview["overall"],
        "summary": overview["summary"]
    }


@app.post("/api/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    try:
        result = system.ask(request.question)
        chart_data = _generate_chart_data(result.get("result"))

        return QueryResponse(
            id=str(uuid.uuid4()),
            role="ai",
            text=result["answer"],
            timestamp=datetime.now().isoformat(),
            sql=result.get("sql", ""),
            rowCount=result.get("row_count", 0),
            executionMs=round(result.get("execution_ms", 0.0), 2),
            totalMs=round(result.get("total_ms", 0.0), 2),
            insights=result.get("insights", []),
            anomalies=result.get("anomalies", []),
            proactiveTips=result.get("proactive_tips", []),
            benchmarkComparison=result.get("benchmark_comparison", ""),
            ragContextUsed=result.get("rag_context_used", False),
            chartData=chart_data,
            intent=result.get("intent", ""),
            isFollowup=result.get("is_followup", False)
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/new-chat")
async def new_chat():
    try:
        system.start_fresh()
        return {"success": True, "message": "New conversation started"}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/overview")
async def get_overview():
    try:
        return system.get_overview()
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/suggestions")
async def get_suggestions():
    return {
        "suggestions": [
            "What is the overall failure rate?",
            "Which device type has the most failed transactions?",
            "Show me fraud trends by age group",
            "Compare P2P vs P2M average amounts",
            "What are the peak transaction hours?",
            "Which state has the highest transaction volume?",
            "Show failed transactions above 5000 rupees",
            "Which bank has the highest failure rate?",
            "How many fraud-flagged transactions are there?",
            "Compare weekend vs weekday failure rates",
            "Why do weekends have more failures?",
            "Which UPI app is most used?",
            "Show me high value transactions above 50000",
            "What is the average latency by network type?"
        ]
    }


@app.get("/api/precomputed")
async def get_precomputed():
    """Get all pre-computed metrics for dashboard display."""
    try:
        precomputed = system.analytics.precomputed
        return {
            "overall": precomputed.get("overall", {}),
            "by_type": precomputed.get("by_type", []),
            "by_hour": precomputed.get("by_hour", []),
            "by_device": precomputed.get("by_device", []),
            "by_merchant": precomputed.get("by_merchant", []),
            "by_age": precomputed.get("by_age", [])
        }
    except Exception as e:
        raise HTTPException(500, str(e))


# ============================================================================
# HELPERS
# ============================================================================

def _generate_chart_data(result) -> Optional[List[Dict]]:
    """Generate chart data from grouped query results."""
    if result is None or result.empty or len(result) <= 1:
        return None

    cat_cols = [c for c in result.columns if result[c].dtype == object]
    num_cols = [c for c in result.columns if pd.api.types.is_numeric_dtype(result[c])]

    if not cat_cols or not num_cols or len(result) > 20:
        return None

    colors = ["#6366f1", "#8b5cf6", "#ec4899", "#f59e0b", "#10b981",
              "#3b82f6", "#ef4444", "#14b8a6", "#f97316", "#84cc16"]

    label_col = cat_cols[0]
    value_col = num_cols[0]

    chart_data = []
    for idx, row in result.head(10).iterrows():
        try:
            chart_data.append({
                "label": str(row[label_col]),
                "value": float(row[value_col]),
                "color": colors[idx % len(colors)]
            })
        except Exception:
            continue

    return chart_data if chart_data else None


# ============================================================================
# RUN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("  INSIGHTX API SERVER v2.0")
    print("  Full Dynamic Pipeline Active")
    print("="*60)
    print("  Server:   http://localhost:8000")
    print("  API Docs: http://localhost:8000/docs")
    print("  Frontend: http://localhost:5173")
    print("="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
