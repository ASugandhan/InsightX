"""
FastAPI Server for InsightX
Connects React frontend to Python backend
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sys
sys.path.append('..')

from main import InsightXSystem
from explainability.formatter import Response
import json
import pandas as pd
import traceback

# Initialize FastAPI
app = FastAPI(title="InsightX API", version="1.0.0")

# CORS configuration for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize InsightX System
system = InsightXSystem('../../data/upi_transactions_2024.csv')

# Store conversation sessions
sessions = {}


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class QueryRequest(BaseModel):
    """Request model for queries"""
    question: str
    session_id: Optional[str] = None
    show_tier2: bool = False
    show_tier3: bool = False


class ChartDataItem(BaseModel):
    """Chart data point"""
    label: str
    value: float
    color: Optional[str] = None


class QueryResponse(BaseModel):
    """Response model matching React Message interface"""
    id: str
    role: str = "ai"
    text: str
    timestamp: str
    confidence: str
    sampleSize: int
    execMs: float
    chartData: Optional[List[ChartDataItem]] = None
    tier2Details: Optional[str] = None
    tier3Technical: Optional[str] = None
    caveats: Optional[str] = None
    contextComparison: Optional[str] = None
    hypotheses: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    components: Dict[str, str]


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "components": {
            "analytics_engine": "ready",
            "rag_system": "ready",
            "explainability": "ready"
        }
    }


@app.post("/api/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Main query endpoint
    Processes natural language questions and returns insights
    """
    
    try:
        import time
        from datetime import datetime
        
        # Generate unique message ID
        msg_id = str(int(time.time() * 1000)) + "a"
        
        # Process query with conversation context
        enhanced, system.current_session = system.conversation_manager.process_query(
            request.question,
            system.current_session
        )
        
        # Generate SQL
        sql = system.sql_generator.generate(enhanced)
        
        # Execute with timing
        start = time.time()
        result = system.analytics.query(sql)
        exec_ms = (time.time() - start) * 1000
        
        # Get baseline
        baseline = system._get_baseline(enhanced.metrics)
        
        # Format response
        response = system.formatter.format(
            query=request.question,
            result=result,
            confidence=enhanced.confidence,
            sql=sql,
            filters=enhanced.filters,
            metrics=enhanced.metrics,
            execution_time_ms=exec_ms,
            baseline=baseline,
            analytics_engine=system.analytics
        )
        
        # Generate chart data
        chart_data = _generate_chart_data(result, enhanced)
        
        # Build response matching React interface
        return {
            "id": msg_id,
            "role": "ai",
            "text": response.tier1_text,
            "timestamp": datetime.now().isoformat(),
            "confidence": response.confidence,
            "sampleSize": response.sample_size,
            "execMs": round(exec_ms, 1),
            "chartData": chart_data,
            "tier2Details": response.tier2_details if request.show_tier2 else None,
            "tier3Technical": response.tier3_technical if request.show_tier3 else None,
            "caveats": response.caveats,
            "contextComparison": response.context_comparison,
            "hypotheses": response.hypotheses if "why" in request.question.lower() else None
        }
        
    except Exception as e:
        # Return error in expected format
        import traceback
        error_detail = traceback.format_exc()
        print(f"ERROR: {error_detail}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Query processing failed: {str(e)}"
        )


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload CSV/Excel files for analysis
    """
    
    try:
        # Read file
        contents = await file.read()
        
        # Determine file type
        if file.filename.endswith('.csv'):
            import io
            df = pd.read_csv(io.BytesIO(contents))
        elif file.filename.endswith(('.xlsx', '.xls')):
            import io
            df = pd.read_excel(io.BytesIO(contents))
        else:
            raise HTTPException(400, "Unsupported file type. Use CSV or Excel.")
        
        # Return summary
        return {
            "success": True,
            "filename": file.filename,
            "rows": len(df),
            "columns": df.columns.tolist(),
            "preview": df.head(5).to_dict('records')
        }
        
    except Exception as e:
        raise HTTPException(500, f"File upload failed: {str(e)}")


@app.post("/api/new-chat")
async def new_chat():
    """Start a new conversation"""
    
    try:
        system.start_fresh()
        return {"success": True, "message": "New chat started"}
    except Exception as e:
        raise HTTPException(500, f"Failed to start new chat: {str(e)}")


@app.get("/api/suggestions")
async def get_suggestions():
    """Get suggested queries"""
    
    suggestions = [
        "What is the average transaction amount?",
        "Show me high-value transactions",
        "Compare failure rates by device type",
        "What are the peak transaction hours?",
        "Which merchant categories are most popular?",
        "Show me fraud-flagged transactions",
        "Analyze weekend vs weekday transactions"
    ]
    
    return {"suggestions": suggestions}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _generate_chart_data(result: pd.DataFrame, enhanced) -> Optional[List[Dict]]:
    """Generate chart data from query results"""
    
    if result.empty or len(result) == 1:
        return None
    
    # For grouped results, create chart
    if len(result) > 1 and len(result) <= 20:
        chart_data = []
        
        # Find categorical and numeric columns
        cat_cols = [c for c in result.columns if result[c].dtype == 'object']
        num_cols = [c for c in result.columns if pd.api.types.is_numeric_dtype(result[c])]
        
        if cat_cols and num_cols:
            label_col = cat_cols[0]
            value_col = num_cols[0]
            
            colors = ["#6366f1", "#8b5cf6", "#ec4899", "#f59e0b", "#10b981", 
                     "#3b82f6", "#ef4444", "#14b8a6", "#f97316", "#84cc16"]
            
            for idx, row in result.head(10).iterrows():
                chart_data.append({
                    "label": str(row[label_col]),
                    "value": float(row[value_col]),
                    "color": colors[idx % len(colors)]
                })
            
            return chart_data
    
    return None


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🚀 STARTING INSIGHTX API SERVER")
    print("="*60)
    print("📍 Server: http://localhost:8000")
    print("📖 Docs: http://localhost:8000/docs")
    print("🔗 React Frontend: http://localhost:5173")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")