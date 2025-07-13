from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
import json
import os
from datetime import datetime

from mem0 import MemoryClient
from .models import DecisionContext, DecisionResult, AgentState, MemoryQuery
from .treasury import TreasuryManager
from .memory import MemoryManager
from .agent import DeFiYieldAgent

# Initialize FastAPI app
app = FastAPI(
    title="DeFi Yield Agent API",
    description="Memory-driven DeFi yield optimization agent",
    version="1.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
mem0_client = MemoryClient(api_key=os.getenv("MEM0_API_KEY"))
treasury_manager = TreasuryManager(initial_balance=float(os.getenv("INITIAL_TREASURY", "1000.0")))
memory_manager = MemoryManager(mem0_client)
agent = DeFiYieldAgent(treasury_manager, memory_manager)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "DeFi Yield Agent API",
        "version": "1.1.0",
        "status": "running"
    }

@app.get("/agent/state")
async def get_agent_state():
    """Get current agent state"""
    try:
        state = agent.get_agent_state()
        return state
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/treasury/summary")
async def get_treasury_summary():
    """Get treasury summary"""
    try:
        summary = treasury_manager.get_treasury_summary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/decide")
async def make_decision(context: DecisionContext):
    """Make a decision based on current context"""
    try:
        decision = agent.decide(context)
        return decision
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/memory/record/survival")
async def record_survival_event(
    event_type: str,
    treasury_level: float,
    action_taken: str,
    outcome: bool,
    context: Dict[str, Any] = None
):
    """Record a survival event"""
    try:
        memory_manager.record_survival_event(
            event_type=event_type,
            treasury_level=treasury_level,
            action_taken=action_taken,
            outcome=outcome,
            context=context
        )
        return {"message": "Survival event recorded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/memory/record/strategy")
async def record_strategy_performance(
    strategy_name: str,
    success_rate: float,
    avg_yield: float,
    gas_cost: float,
    context: Dict[str, Any] = None
):
    """Record strategy performance"""
    try:
        memory_manager.record_strategy_performance(
            strategy_name=strategy_name,
            success_rate=success_rate,
            avg_yield=avg_yield,
            gas_cost=gas_cost,
            context=context
        )
        return {"message": "Strategy performance recorded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/memory/query")
async def query_memories(query: MemoryQuery):
    """Query memories"""
    try:
        memories = memory_manager.query_memories(query)
        return {"memories": memories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memory/statistics")
async def get_memory_statistics():
    """Get memory statistics"""
    try:
        stats = memory_manager.get_memory_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/treasury/deduct")
async def deduct_cost(amount: float, reason: str, gas_cost: float = None):
    """Deduct cost from treasury"""
    try:
        treasury_manager.deduct_cost(amount, reason, gas_cost)
        return {"message": "Cost deducted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/treasury/add")
async def add_revenue(amount: float, source: str):
    """Add revenue to treasury"""
    try:
        treasury_manager.add_revenue(amount, source)
        return {"message": "Revenue added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket for real-time updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/agent")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time agent updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Send periodic agent state updates
            state = agent.get_agent_state()
            await websocket.send_text(json.dumps({
                "type": "agent_state",
                "data": state.dict(),
                "timestamp": datetime.now().isoformat()
            }))
            
            # Wait for 5 seconds before next update
            import asyncio
            await asyncio.sleep(5)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "treasury_balance": treasury_manager.balance,
        "survival_status": treasury_manager.get_survival_status()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 