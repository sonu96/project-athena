#!/usr/bin/env python3
"""
Run agent with API server

This script starts both the agent and the API server.
"""

import asyncio
import logging
import threading
import uvicorn
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.core.agent import AthenaAgent
from src.api.server import create_app
from src.config import settings


def run_api_server(agent: AthenaAgent):
    """Run API server in separate thread"""
    app = create_app(agent)
    
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower()
    )


async def main():
    """Main entry point"""
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Athena Agent with API server...")
    
    # Create agent
    agent = AthenaAgent()
    
    # Start API server in separate thread
    api_thread = threading.Thread(
        target=run_api_server,
        args=(agent,),
        daemon=True
    )
    api_thread.start()
    
    logger.info(f"API server started at http://{settings.api_host}:{settings.api_port}")
    
    # Run agent
    try:
        await agent.run()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        agent.request_shutdown()
    
    logger.info("Agent terminated")


if __name__ == "__main__":
    asyncio.run(main())