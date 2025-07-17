#!/usr/bin/env python3
"""Main entry point for Athena Agent production deployment"""

import asyncio
import logging
import os
import signal
import sys
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.agent import AthenaAgent
from api.server import create_app, run_server
from config import settings
from monitoring.langsmith_config import configure_langsmith

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global agent instance
agent = None
shutdown_event = asyncio.Event()

def signal_handler(sig, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {sig}, initiating graceful shutdown...")
    shutdown_event.set()

async def run_agent():
    """Run the agent in production mode"""
    global agent
    
    logger.info("🚀 Starting Athena Agent Phase 1 Production")
    logger.info(f"   Project: {settings.gcp_project_id}")
    logger.info(f"   Agent ID: {settings.agent_id}")
    logger.info(f"   Network: {settings.network}")
    logger.info(f"   Observation Mode: {settings.observation_mode}")
    
    # Configure monitoring
    configure_langsmith()
    
    # Initialize agent
    agent = AthenaAgent()
    
    try:
        # Initialize subsystems
        success = await agent.initialize()
        if not success:
            logger.error("Failed to initialize agent")
            return False
        
        logger.info("✅ Agent initialized successfully")
        
        # Start API server in background
        app = create_app(agent)
        api_task = asyncio.create_task(
            run_server(app, host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
        )
        
        # Run agent
        logger.info("🏃 Starting cognitive loop...")
        agent_task = asyncio.create_task(agent.run())
        
        # Wait for shutdown signal
        await shutdown_event.wait()
        
        # Graceful shutdown
        logger.info("Shutting down agent...")
        await agent.shutdown()
        
        # Cancel tasks
        api_task.cancel()
        agent_task.cancel()
        
        try:
            await api_task
            await agent_task
        except asyncio.CancelledError:
            pass
        
        logger.info("✅ Agent shutdown complete")
        return True
        
    except Exception as e:
        logger.error(f"Critical error in agent: {e}", exc_info=True)
        return False

def main():
    """Main entry point"""
    # Set up signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Print startup banner
    print("""
    ╔═══════════════════════════════════════╗
    ║      ATHENA DEFI AGENT - PHASE 1      ║
    ║         Production Deployment         ║
    ╚═══════════════════════════════════════╝
    """)
    
    print(f"    Started at: {datetime.utcnow().isoformat()}")
    print(f"    Environment: {settings.env}")
    print(f"    Version: 1.0.0")
    print()
    
    # Run async main
    try:
        success = asyncio.run(run_agent())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()