#!/usr/bin/env python3
"""Simple health check server for Phase 1 deployment"""

import os
import json
import asyncio
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Athena Agent Phase 1", version="1.0.0")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Athena DeFi Agent",
        "phase": "1",
        "status": "running",
        "mode": "observation",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "agent_id": os.getenv("AGENT_ID", "athena-phase1-prod"),
            "network": os.getenv("NETWORK", "base"),
            "observation_mode": True,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }
    )

@app.get("/status")
async def status():
    """Status endpoint with environment info"""
    return {
        "agent": {
            "id": os.getenv("AGENT_ID", "athena-phase1-prod"),
            "phase": 1,
            "running": True,
            "observation_mode": True
        },
        "environment": {
            "project_id": os.getenv("GCP_PROJECT_ID"),
            "dataset": os.getenv("BIGQUERY_DATASET"),
            "network": os.getenv("NETWORK"),
            "env": os.getenv("ENV", "production")
        },
        "services": {
            "bigquery": "configured",
            "pool_collector": "https://us-central1-athena-defi-agent-1752635199.cloudfunctions.net/aerodrome-pool-collector",
            "memory": "mem0-cloud"
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/metrics")
async def metrics():
    """Basic metrics endpoint"""
    return {
        "uptime_seconds": 0,  # Would track actual uptime
        "pools_observed": 0,  # Would track from BigQuery
        "memories_formed": 0,  # Would track from Mem0
        "last_observation": None,
        "timestamp": datetime.utcnow().isoformat()
    }

async def background_task():
    """Background task that would run observations"""
    while True:
        logger.info(f"Background task running - {datetime.utcnow()}")
        # In production, this would:
        # 1. Fetch Aerodrome pool data
        # 2. Store observations in BigQuery
        # 3. Form memories with Mem0
        # 4. Update emotional state
        await asyncio.sleep(300)  # 5 minutes

@app.on_event("startup")
async def startup_event():
    """Startup tasks"""
    logger.info("🚀 Athena Agent Phase 1 Starting...")
    logger.info(f"   Project: {os.getenv('GCP_PROJECT_ID')}")
    logger.info(f"   Network: {os.getenv('NETWORK')}")
    logger.info(f"   Agent ID: {os.getenv('AGENT_ID')}")
    
    # Start background task
    asyncio.create_task(background_task())

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    logger.info(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)