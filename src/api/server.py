"""
FastAPI server for agent monitoring and control

Provides health checks and basic metrics.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ..config import settings
from ..core.agent import AthenaAgent

logger = logging.getLogger(__name__)


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    agent_id: str
    version: str = "1.0.0"
    details: Optional[Dict[str, Any]] = None


class StatusResponse(BaseModel):
    """Agent status response"""
    agent_id: str
    running: bool
    cycle_count: int
    treasury_balance: float
    emotional_state: str
    days_until_bankruptcy: float
    memories_count: int
    patterns_count: int
    last_cycle: Optional[datetime]


def create_app(agent: Optional[AthenaAgent] = None) -> FastAPI:
    """
    Create FastAPI application
    
    Args:
        agent: Agent instance for monitoring
        
    Returns:
        FastAPI app
    """
    
    app = FastAPI(
        title="Athena Agent API",
        description="Monitoring and control API for Athena DeFi Agent",
        version="1.0.0"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Store agent reference
    app.state.agent = agent
    
    @app.get("/", response_model=Dict[str, str])
    async def root():
        """Root endpoint"""
        return {
            "service": "Athena Agent API",
            "version": "1.0.0",
            "status": "running"
        }
    
    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        """Health check endpoint"""
        
        details = {}
        
        # Check agent status
        if app.state.agent:
            details["agent_running"] = app.state.agent.running
            if app.state.agent.state:
                details["cycle_count"] = app.state.agent.state.cycle_count
                details["emotional_state"] = app.state.agent.state.emotional_state.value
        
        return HealthResponse(
            status="healthy",
            timestamp=datetime.utcnow(),
            agent_id=settings.agent_id,
            details=details
        )
    
    @app.get("/status", response_model=StatusResponse)
    async def get_status():
        """Get detailed agent status"""
        
        if not app.state.agent or not app.state.agent.state:
            raise HTTPException(status_code=503, detail="Agent not initialized")
        
        agent = app.state.agent
        state = agent.state
        
        # Get memory count
        try:
            memories = await agent.memory_client.get_all_memories()
            memory_count = len(memories)
        except:
            memory_count = 0
        
        return StatusResponse(
            agent_id=state.agent_id,
            running=agent.running,
            cycle_count=state.cycle_count,
            treasury_balance=state.treasury_balance,
            emotional_state=state.emotional_state.value,
            days_until_bankruptcy=state.days_until_bankruptcy,
            memories_count=memory_count,
            patterns_count=len(state.active_patterns),
            last_cycle=state.timestamp
        )
    
    @app.get("/metrics", response_model=Dict[str, Any])
    async def get_metrics():
        """Get agent metrics for monitoring"""
        
        if not app.state.agent or not app.state.agent.state:
            return {"status": "not_initialized"}
        
        agent = app.state.agent
        state = agent.state
        
        # Financial metrics
        financial = agent.treasury.get_financial_summary()
        
        # Operational metrics
        operational = {
            "cycle_count": state.cycle_count,
            "errors_count": len(state.errors),
            "warnings_count": len(state.warnings),
            "observation_frequency_minutes": state.get_observation_frequency_minutes(),
            "llm_model": state.llm_model,
            "total_llm_cost": state.total_llm_cost
        }
        
        # Learning metrics
        learning = {
            "patterns_active": len(state.active_patterns),
            "pending_memories": len(state.memory_formation_pending),
            "confidence_level": state.confidence_level
        }
        
        return {
            "timestamp": datetime.utcnow(),
            "financial": financial,
            "operational": operational,
            "learning": learning
        }
    
    @app.post("/shutdown")
    async def request_shutdown():
        """Request agent shutdown"""
        
        if not app.state.agent:
            raise HTTPException(status_code=503, detail="Agent not initialized")
        
        app.state.agent.request_shutdown()
        
        return {"status": "shutdown_requested"}
    
    @app.on_event("startup")
    async def startup_event():
        """Startup event handler"""
        logger.info("API server starting up")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Shutdown event handler"""
        logger.info("API server shutting down")
    
    return app