"""
Athena Agent - Main Orchestrator

Coordinates all subsystems and runs the cognitive loop.
"""

import asyncio
import logging
import signal
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from ..config import settings
from ..config.constants import COGNITIVE_CYCLE_MIN_INTERVAL_SECONDS
from .consciousness import ConsciousnessState
from .emotions import EmotionalEngine, EmotionalState
from .treasury import TreasuryManager
from ..workflows.cognitive_loop import create_cognitive_workflow, run_cognitive_cycle, should_run_cycle
from ..blockchain import CDPClient, WalletManager
from ..memory import MemoryClient
from ..database import FirestoreClient, BigQueryClient
from ..monitoring.langsmith_config import configure_langsmith
from ..aerodrome.observer import AerodromeObserver

logger = logging.getLogger(__name__)


class AthenaAgent:
    """
    Main agent orchestrator
    
    Responsibilities:
    - Initialize all subsystems
    - Run cognitive loop
    - Manage lifecycle
    - Handle errors and recovery
    """
    
    def __init__(self):
        self.agent_id = settings.agent_id
        self.running = False
        self.state: Optional[ConsciousnessState] = None
        
        # Core components
        self.treasury = TreasuryManager(settings.starting_treasury)
        self.cdp_client = CDPClient()
        self.wallet_manager = WalletManager()
        self.memory_client = MemoryClient()
        
        # Database clients
        self.firestore = FirestoreClient()
        self.bigquery = BigQueryClient()
        
        # Aerodrome observer with CDP integration
        self.aerodrome_observer = AerodromeObserver(self.cdp_client)
        
        # Workflow
        self.workflow = None
        
        # Shutdown handling
        self._shutdown_event = asyncio.Event()
        
        logger.info(f"🏛️ Athena Agent {self.agent_id} initializing...")
    
    async def initialize(self) -> bool:
        """
        Initialize all agent subsystems
        
        Returns:
            Success status
        """
        try:
            # Configure monitoring
            configure_langsmith()
            
            # Initialize blockchain
            logger.info("Initializing blockchain connection...")
            wallet_info = await self.cdp_client.initialize_wallet()
            if wallet_info.get("address"):
                self.wallet_manager.save_wallet_info(
                    wallet_info["address"],
                    wallet_info["network"]
                )
                logger.info(f"✅ Wallet initialized: {wallet_info['address']}")
            else:
                logger.warning("⚠️ Wallet initialization failed - running in simulation")
            
            # Initialize databases
            logger.info("Initializing databases...")
            await self.bigquery.ensure_dataset_exists()
            await self.bigquery.ensure_tables_exist()
            
            # Load or create initial state
            self.state = await self._load_or_create_state()
            
            # Create workflow
            self.workflow = create_cognitive_workflow()
            
            # Log initialization
            await self._log_initialization()
            
            logger.info("✅ Agent initialization complete")
            return True
            
        except Exception as e:
            logger.error(f"❌ Agent initialization failed: {e}", exc_info=True)
            return False
    
    async def run(self):
        """
        Main agent loop
        
        Runs cognitive cycles based on emotional state frequency
        """
        if not await self.initialize():
            logger.error("Failed to initialize agent")
            return
        
        self.running = True
        logger.info(f"🚀 Agent {self.agent_id} starting main loop")
        
        try:
            while self.running and not self._shutdown_event.is_set():
                # Check if we should run a cycle
                if should_run_cycle(self.state):
                    # Run cognitive cycle
                    cycle_start = datetime.utcnow()
                    
                    self.state = await run_cognitive_cycle(
                        self.workflow,
                        self.state
                    )
                    
                    # Update treasury from state
                    self.treasury.balance = self.state.treasury_balance
                    
                    # Save state
                    await self._save_state()
                    
                    # Log metrics
                    await self._log_cycle_metrics()
                    
                    cycle_duration = (datetime.utcnow() - cycle_start).total_seconds()
                    logger.info(f"Cycle completed in {cycle_duration:.1f}s")
                
                # Calculate next cycle time
                wait_time = self._calculate_wait_time()
                logger.info(f"Next cycle in {wait_time}s ({wait_time/60:.1f} minutes)")
                
                # Wait for next cycle or shutdown
                try:
                    await asyncio.wait_for(
                        self._shutdown_event.wait(),
                        timeout=wait_time
                    )
                    # Shutdown requested
                    break
                except asyncio.TimeoutError:
                    # Continue to next cycle
                    pass
                
        except Exception as e:
            logger.error(f"❌ Fatal error in agent loop: {e}", exc_info=True)
            self.state.errors.append(f"Fatal error: {str(e)}")
        
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("🛑 Agent shutting down...")
        self.running = False
        
        # Save final state
        if self.state:
            await self._save_state()
            
            # Log final summary
            summary = self.treasury.get_financial_summary()
            logger.info(f"Final treasury: ${summary['balance']:.2f}")
            logger.info(f"Total spent: ${summary['total_spent']:.2f}")
            logger.info(f"Cycles completed: {self.state.cycle_count}")
            logger.info(f"Memories formed: {len(await self.memory_client.get_all_memories())}")
        
        logger.info("✅ Agent shutdown complete")
    
    def request_shutdown(self):
        """Request graceful shutdown"""
        logger.info("Shutdown requested")
        self._shutdown_event.set()
    
    async def _load_or_create_state(self) -> ConsciousnessState:
        """Load existing state or create new"""
        
        # Try to load from Firestore
        saved_state = await self.firestore.get_agent_state(self.agent_id)
        
        if saved_state:
            logger.info("Loading saved agent state")
            state = ConsciousnessState.from_dict(saved_state)
            
            # Update treasury
            self.treasury.balance = state.treasury_balance
            
        else:
            logger.info("Creating new agent state")
            
            # Calculate initial emotional state
            initial_emotional, intensity = EmotionalEngine.calculate_emotional_state(
                self.treasury.calculate_runway()["days"]
            )
            
            state = ConsciousnessState(
                agent_id=self.agent_id,
                treasury_balance=self.treasury.balance,
                daily_burn_rate=0.0,
                days_until_bankruptcy=float('inf'),
                emotional_state=initial_emotional,
                emotional_intensity=intensity
            )
        
        return state
    
    async def _save_state(self):
        """Save current state to Firestore"""
        if self.state:
            await self.firestore.save_agent_state(
                self.agent_id,
                self.state.to_dict()
            )
    
    def _calculate_wait_time(self) -> float:
        """Calculate time until next cycle based on emotional state"""
        
        # Get base frequency from emotional state
        freq_minutes = self.state.get_observation_frequency_minutes()
        wait_seconds = freq_minutes * 60
        
        # Ensure minimum interval
        wait_seconds = max(wait_seconds, COGNITIVE_CYCLE_MIN_INTERVAL_SECONDS)
        
        # Add small random variation (±10%)
        import random
        variation = random.uniform(0.9, 1.1)
        wait_seconds *= variation
        
        return wait_seconds
    
    async def _log_initialization(self):
        """Log agent initialization"""
        await self.bigquery.log_agent_metrics(
            self.agent_id,
            {
                "cycle_count": 0,
                "treasury_balance": self.treasury.balance,
                "emotional_state": self.state.emotional_state.value,
                "emotional_intensity": self.state.emotional_intensity,
                "memories_formed": 0,
                "patterns_active": 0,
                "total_cost": 0.0,
                "llm_cost": 0.0,
                "days_until_bankruptcy": self.state.days_until_bankruptcy
            }
        )
    
    async def _log_cycle_metrics(self):
        """Log cycle metrics to BigQuery"""
        memories_count = len(await self.memory_client.get_all_memories())
        
        await self.bigquery.log_agent_metrics(
            self.agent_id,
            {
                "cycle_count": self.state.cycle_count,
                "treasury_balance": self.state.treasury_balance,
                "emotional_state": self.state.emotional_state.value,
                "emotional_intensity": self.state.emotional_intensity,
                "memories_formed": memories_count,
                "patterns_active": len(self.state.active_patterns),
                "total_cost": self.state.total_cost,
                "llm_cost": self.state.total_llm_cost,
                "days_until_bankruptcy": self.state.days_until_bankruptcy
            }
        )
    
    async def observe_top_pools(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Observe top Aerodrome pools using CDP
        
        Args:
            limit: Number of pools to observe
            
        Returns:
            List of pool data
        """
        try:
            pools = await self.aerodrome_observer.get_top_pools(limit)
            
            # Store observations
            for pool in pools:
                await self.bigquery.store_pool_observation({
                    "timestamp": datetime.utcnow(),
                    "agent_id": self.agent_id,
                    "pool_address": pool["address"],
                    "pool_type": pool["type"],
                    "tvl_usd": pool["tvl_usd"],
                    "volume_24h_usd": pool["volume_24h_usd"],
                    "fee_apy": pool["fee_apy"],
                    "reward_apy": pool["reward_apy"],
                    "observation_notes": f"CDP observation of {pool['symbol']}"
                })
            
            return pools
            
        except Exception as e:
            logger.error(f"Failed to observe pools: {e}")
            return []
    
    def get_wallet_info(self) -> Dict[str, Any]:
        """Get wallet information"""
        return {
            "address": self.cdp_client.get_wallet_address(),
            "network": self.cdp_client.network
        }
    
    async def get_balance(self) -> float:
        """Get wallet balance"""
        return await self.cdp_client.get_wallet_balance()
    
    async def get_wallet_address(self) -> str:
        """Get wallet address"""
        return self.cdp_client.get_wallet_address()


async def main():
    """Main entry point"""
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create agent
    agent = AthenaAgent()
    
    # Handle shutdown signals
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}")
        agent.request_shutdown()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run agent
    try:
        await agent.run()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        agent.request_shutdown()
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
    
    logger.info("Agent terminated")


if __name__ == "__main__":
    asyncio.run(main())