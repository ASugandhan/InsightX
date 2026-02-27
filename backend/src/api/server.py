"""
FastAPI Server for InsightX v2.2
Integrated: 5-Key Rotation + Guardrails + All 4 Issue Fixes
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sys, traceback, uuid
from datetime import datetime
import pandas as pd
import asyncio
import threading
import contextlib
from fastapi.concurrency import run_in_threadpool

sys.path.append('..')
from main import InsightXSystem
from guardrails import Guardrails
from nlp.key_manager import get_key_manager

app = FastAPI(title="InsightX API", version="2.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

system = InsightXSystem('../../data/upi_transactions_2024.csv')
guardrails = Guardrails(rate_limit_per_minute=30)


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
    needsClarification: bool = False
    blocked: bool = False


@app.get("/")
async def health_check():
    overview = system.get_overview()
    km = get_key_manager()
    key_status = km.status()
    available_keys = sum(1 for k in key_status["keys"] if k["available"])
    return {
        "status": "healthy",
        "version": "2.2.0",
        "pipeline": "5-Key Rotation + Guardrails + RAG + Gemini NLU + DuckDB(250k) + Intelligence",
        "fixes": ["anti-hallucination", "conversation-history", "smart-defaults", "sql-auto-fix", "guardrails", "key-rotation"],
        "dataset": overview["overall"],
        "summary": overview["summary"],
        "gemini_keys": f"{available_keys}/5 available"
    }


@app.get("/api/keys/status")
async def keys_status():
    """Check status of all 5 Gemini API keys."""
    km = get_key_manager()
    return km.status()


@app.post("/api/query", response_model=QueryResponse)
async def query(request: QueryRequest, http_request: Request):
    try:
        session_id = request.session_id or http_request.client.host or "default"

        is_safe, rejection_msg = guardrails.check_input(request.question, session_id)
        if not is_safe:
            return QueryResponse(
                id=str(uuid.uuid4()), role="ai", text=rejection_msg,
                timestamp=datetime.now().isoformat(), blocked=True
            )

        stop_event = threading.Event()

        async def check_disconnect():
            while not stop_event.is_set():
                if await http_request.is_disconnected():
                    print("Client disconnected, aborting query processing...")
                    stop_event.set()
                    break
                await asyncio.sleep(0.5)

        monitor_task = asyncio.create_task(check_disconnect())

        try:
            result = await run_in_threadpool(system.ask, request.question, session_id, stop_event)
        except Exception as e:
            if stop_event.is_set() or str(e) == "ClientDisconnected":
                raise HTTPException(status_code=499, detail="Client Closed Request")
            raise
        finally:
            stop_event.set()
            monitor_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await monitor_task

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
            isFollowup=result.get("is_followup", False),
            needsClarification=result.get("needs_clarification", False),
            blocked=result.get("blocked", False)
        )
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, str(e))


@app.post("/api/reset")
async def reset_conversation():
    system.start_fresh()
    return {"status": "ok", "message": "Conversation history cleared"}


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


def _generate_chart_data(result) -> Optional[List[Dict]]:
    if result is None or result.empty or len(result) <= 1:
        return None
    cat_cols = [c for c in result.columns if result[c].dtype == object]
    num_cols = [c for c in result.columns if pd.api.types.is_numeric_dtype(result[c])]
    if not cat_cols or not num_cols or len(result) > 20:
        return None
    colors = ["#6366f1","#8b5cf6","#ec4899","#f59e0b","#10b981","#3b82f6","#ef4444","#14b8a6","#f97316","#84cc16"]
    label_col, value_col = cat_cols[0], num_cols[0]
    chart_data = []
    for idx, row in result.head(10).iterrows():
        try:
            chart_data.append({"label": str(row[label_col]), "value": float(row[value_col]), "color": colors[idx % len(colors)]})
        except Exception:
            continue
    return chart_data if chart_data else None


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("  INSIGHTX API SERVER v2.2")
    print("  5-Key Rotation + Guardrails + All Fixes")
    print("="*60)
    print("  Server:   http://localhost:8000")
    print("  API Docs: http://localhost:8000/docs")
    print("="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
