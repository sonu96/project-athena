"""
Main DeFi Agent orchestrator - coordinates all components
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
import json

from .treasury import TreasuryManager
from .memory_manager import MemoryManager
from .market_detector import MarketConditionDetector
from ..data.firestore_client import FirestoreClient
from ..data.bigquery_client import BigQueryClient
from ..data.market_data_collector import MarketDataCollector
from ..integrations.mem0_integration import Mem0Integration
from ..integrations.cdp_integration import CDPIntegration
from ..integrations.llm_workflow_integration import LLMWorkflowIntegration
from ..workflows.state import WorkflowConfig
from ..config.settings import settings
from ..config.langsmith_config import enable_tracing, monitor_workflow

logger = logging.getLogger(__name__)


class DeFiAgent:
    """Athena - Autonomous DeFi AI Agent with survival instincts"""
    
    def __init__(self):
        # Core components
        self.firestore: Optional[FirestoreClient] = None
        self.bigquery: Optional[BigQueryClient] = None
        self.treasury: Optional[TreasuryManager] = None
        self.memory_manager: Optional[MemoryManager] = None
        self.market_detector: Optional[MarketConditionDetector] = None
        self.market_data_collector: Optional[MarketDataCollector] = None
        self.cdp: Optional[CDPIntegration] = None
        self.llm_workflows: Optional[LLMWorkflowIntegration] = None
        
        # Integrations
        self.mem0: Optional[Mem0Integration] = None
        
        # Agent state
        self.running = False
        self.last_observation_time: Optional[datetime] = None
        self.observation_count = 0
        self.decisions_made = 0
        
        # Phase 1 configuration
        self.phase = "phase_1_observer"
        self.capabilities = [
            'market_observation',
            'memory_formation',
            'cost_tracking',
            'survival_instincts',
            'pattern_recognition'
        ]
        
        # Operational configuration
        self.config = {
            'observation_interval': settings.observation_interval_seconds,
            'memory_update_interval': settings.memory_update_interval_seconds,
            'survival_check_interval': settings.survival_check_interval_seconds,
            'max_daily_costs': settings.max_daily_costs_usd,
            'auto_survival_mode': True,
            'learning_enabled': True
        }
        
        # Performance metrics
        self.metrics = {
            'uptime_start': None,
            'total_observations': 0,
            'successful_decisions': 0,
            'survival_events': 0,
            'memories_formed': 0,
            'total_costs': 0.0
        }
    
    @monitor_workflow("agent_initialization")
    async def initialize(self) -> bool:
        """Initialize all agent components"""
        try:
            logger.info("🏛️ Initializing Athena DeFi Agent...")
            
            # Enable LangSmith tracing
            enable_tracing("athena_agent_session", {
                "agent_id": settings.agent_id,
                "phase": self.phase,
                "initialization_time": datetime.now(timezone.utc).isoformat()
            })
            
            # Initialize data layer
            self.firestore = FirestoreClient()
            self.bigquery = BigQueryClient()
            
            # Initialize databases
            await self.firestore.initialize_database()
            await self.bigquery.initialize_dataset()
            
            # Initialize integrations
            self.mem0 = Mem0Integration(self.firestore, self.bigquery)
            await self.mem0.initialize_memory_system()
            
            # Initialize CDP wallet
            self.cdp = CDPIntegration()
            await self.cdp.initialize_wallet()
            
            # Initialize core components
            self.treasury = TreasuryManager(self.firestore, self.mem0)
            await self.treasury.initialize()
            
            self.memory_manager = MemoryManager(self.mem0, self.firestore, self.bigquery)
            self.market_detector = MarketConditionDetector(self.firestore, self.mem0)
            self.market_data_collector = MarketDataCollector(self.firestore, self.bigquery)
            
            # Initialize LLM workflows
            workflow_config = WorkflowConfig(
                enable_tracing=True,
                project_name="athena-defi-phase1"
            )
            self.llm_workflows = LLMWorkflowIntegration(workflow_config)
            
            # Request testnet tokens
            await self.cdp.get_testnet_tokens()
            
            # Initialize metrics
            self.metrics['uptime_start'] = datetime.now(timezone.utc)
            
            # Log successful initialization
            await self.firestore.log_system_event(
                "agent_initialized",
                {
                    "agent_id": settings.agent_id,
                    "phase": self.phase,
                    "capabilities": self.capabilities,
                    "config": self.config
                }
            )
            
            logger.info("✅ Athena DeFi Agent initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Agent initialization failed: {e}")
            return False
    
    @monitor_workflow("agent_operations")
    async def start_operations(self) -> None:
        """Start main agent operations loop"""
        try:
            self.running = True
            logger.info("🚀 Athena starting operations...")
            
            # Create startup memory
            await self.mem0.add_memory(
                content="Agent operations started. Beginning Phase 1: Market observation and memory formation with survival instincts active.",
                metadata={
                    "category": "agent_lifecycle",
                    "importance": 0.9,
                    "phase": self.phase,
                    "startup_time": datetime.now(timezone.utc).isoformat()
                }
            )
            
            # Main operations loop
            while self.running:
                try:
                    loop_start = datetime.now(timezone.utc)
                    
                    # Check survival status first
                    await self._check_survival_status()
                    
                    # Perform hourly observation
                    await self._perform_observation_cycle()
                    
                    # Update memories and learning
                    await self._update_learning()
                    
                    # Generate daily summary if needed
                    await self._generate_daily_summary_if_needed()
                    
                    # Calculate next observation time
                    next_observation = loop_start + timedelta(seconds=self.config['observation_interval'])
                    sleep_duration = (next_observation - datetime.now(timezone.utc)).total_seconds()
                    
                    if sleep_duration > 0:
                        logger.info(f"💤 Sleeping for {sleep_duration:.0f} seconds until next observation...")
                        await asyncio.sleep(sleep_duration)
                    
                except asyncio.CancelledError:
                    logger.info("🛑 Agent operations cancelled")
                    break
                except Exception as e:
                    logger.error(f"❌ Error in operations loop: {e}")
                    # Continue running despite errors
                    await asyncio.sleep(60)  # Wait 1 minute before retry
            
        except Exception as e:
            logger.error(f"❌ Critical error in agent operations: {e}")
        finally:
            await self._shutdown_cleanup()
    
    async def _perform_observation_cycle(self):
        """Perform a complete observation cycle"""
        try:
            cycle_start = datetime.now(timezone.utc)
            logger.info(f"👁️ Starting observation cycle #{self.observation_count + 1}")
            
            # Collect market data
            market_result = await self.market_data_collector.collect_comprehensive_market_data()
            
            if not market_result['success']:
                logger.warning(f"Market data collection failed: {market_result.get('error')}")
                return
            
            market_data = market_result['data']
            
            # Detect market condition
            condition, confidence, analysis = await self.market_detector.detect_market_condition(market_data)
            
            # Get treasury state
            treasury_status = await self.treasury.get_status()
            
            # Track observation cost
            observation_cost = 0.02  # Base cost for data collection
            await self.treasury.track_cost(observation_cost, "market_observation", "Hourly market observation cycle")
            
            # Get relevant memories for context
            context = {
                "treasury": treasury_status,
                "market": {
                    "condition": condition,
                    "confidence": confidence,
                    "data": market_data
                },
                "task": "market_observation"
            }
            
            memories = await self.memory_manager.get_relevant_memories(context)
            
            # Analyze market conditions using LLM workflow
            analysis_result = await self.llm_workflows.analyze_market_conditions(
                market_data=market_data,
                treasury_state=treasury_status,
                memories=memories.get("market_memories", [])
            )
            
            # Track LLM cost
            llm_cost = analysis_result.get("cost", 0)
            if llm_cost > 0:
                await self.treasury.track_cost(llm_cost, "llm_analysis", "Market condition analysis")
            
            # Process the experience for memory formation
            experience = {
                "type": "market_observation",
                "timestamp": cycle_start.isoformat(),
                "market_condition": condition,
                "confidence": confidence,
                "treasury_state": treasury_status["emotional_state"],
                "analysis": analysis_result.get("analysis", {}),
                "cost": observation_cost + llm_cost,
                "success": analysis_result.get("workflow_success", True)
            }
            
            await self.memory_manager.process_experience(experience)
            
            # Make decisions based on observations
            await self._make_observation_decisions(context, analysis_result)
            
            # Update metrics
            self.observation_count += 1
            self.metrics['total_observations'] += 1
            self.metrics['total_costs'] += observation_cost + llm_cost
            self.last_observation_time = cycle_start
            
            cycle_duration = (datetime.now(timezone.utc) - cycle_start).total_seconds()
            logger.info(f"✅ Observation cycle completed in {cycle_duration:.1f}s (cost: ${observation_cost + llm_cost:.4f})")
            
        except Exception as e:
            logger.error(f"❌ Observation cycle failed: {e}")
            # Track failure
            await self.treasury.track_cost(0.001, "system_error", f"Observation cycle error: {str(e)[:100]}")
    
    async def _make_observation_decisions(self, context: Dict[str, Any], analysis_result: Dict[str, Any]):
        """Make decisions based on market observations"""
        try:
            treasury_state = context["treasury"]
            market_condition = context["market"]["condition"]
            emotional_state = treasury_state["emotional_state"]
            
            # Define available actions based on emotional state
            if emotional_state == "desperate":
                available_options = [
                    "emergency_mode",
                    "reduce_frequency",
                    "minimize_operations"
                ]
            elif emotional_state == "cautious":
                available_options = [
                    "reduce_frequency",
                    "conservative_monitoring",
                    "maintain_current"
                ]
            else:
                available_options = [
                    "increase_monitoring",
                    "maintain_current",
                    "explore_opportunities"
                ]
            
            # Get decision context
            decision_context = {
                "treasury": treasury_state,
                "market": context["market"],
                "analysis": analysis_result,
                "situation_urgency": self._assess_situation_urgency(treasury_state, market_condition)
            }
            
            # Get relevant memories
            memories = await self.memory_manager.get_relevant_memories(decision_context)
            
            # Make decision using LLM workflow
            decision_result = await self.llm_workflows.make_decision(
                decision_type="observation_response",
                available_options=available_options,
                context=decision_context,
                memories=memories.get("recent_decisions", [])
            )
            
            # Track decision cost
            decision_cost = decision_result.get("cost", 0)
            if decision_cost > 0:
                await self.treasury.track_cost(decision_cost, "decision_making", "Observation decision")
            
            # Implement the decision
            await self._implement_decision(decision_result)
            
            # Store decision for learning
            decision_experience = {
                "type": "decision_outcome",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "decision": decision_result.get("decision"),
                "reasoning": decision_result.get("reasoning"),
                "confidence": decision_result.get("confidence"),
                "context": decision_context,
                "cost": decision_cost,
                "success": decision_result.get("workflow_success", True)
            }
            
            await self.memory_manager.process_experience(decision_experience)
            
            self.decisions_made += 1
            self.metrics['successful_decisions'] += 1 if decision_result.get("workflow_success") else 0
            
            logger.info(f"🎯 Decision made: {decision_result.get('decision')} (confidence: {decision_result.get('confidence', 0):.2f})")
            
        except Exception as e:
            logger.error(f"❌ Decision making failed: {e}")
    
    async def _implement_decision(self, decision_result: Dict[str, Any]):
        """Implement the agent's decision"""
        try:
            decision = decision_result.get("decision", "maintain_current")
            
            if decision == "emergency_mode":
                # Activate emergency mode
                self.config['observation_interval'] = 7200  # 2 hours
                logger.warning("🆘 Emergency mode activated - reduced observation frequency")
                
            elif decision == "reduce_frequency":
                # Reduce observation frequency
                self.config['observation_interval'] = min(self.config['observation_interval'] * 1.5, 7200)
                logger.info(f"⏰ Observation frequency reduced to {self.config['observation_interval']/3600:.1f} hours")
                
            elif decision == "increase_monitoring":
                # Increase monitoring frequency
                self.config['observation_interval'] = max(self.config['observation_interval'] * 0.75, 1800)
                logger.info(f"⏰ Observation frequency increased to {self.config['observation_interval']/3600:.1f} hours")
                
            elif decision == "minimize_operations":
                # Minimize all operations
                self.config['observation_interval'] = 14400  # 4 hours
                logger.warning("🔻 Operations minimized - maximum cost reduction")
                
            # Log decision implementation
            await self.firestore.log_system_event(
                "decision_implemented",
                {
                    "decision": decision,
                    "new_config": self.config,
                    "reasoning": decision_result.get("reasoning", ""),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Decision implementation failed: {e}")
    
    def _assess_situation_urgency(self, treasury_state: Dict[str, Any], market_condition: str) -> str:
        """Assess the urgency of the current situation"""
        balance = treasury_state.get("balance", 100)
        days_remaining = treasury_state.get("days_remaining", 999)
        emotional_state = treasury_state.get("emotional_state", "stable")
        
        if emotional_state == "desperate" or balance < 25:
            return "critical"
        elif emotional_state == "cautious" or market_condition in ["volatile", "strong_bear"]:
            return "high"
        elif market_condition in ["bear"]:
            return "medium"
        else:
            return "low"
    
    async def _check_survival_status(self):
        """Check and respond to survival status"""
        try:
            treasury_status = await self.treasury.get_status()
            
            if treasury_status["status"] == "critical":
                # Critical survival situation
                logger.warning(f"🚨 CRITICAL SURVIVAL STATUS: ${treasury_status['balance']:.2f} remaining")
                
                # Generate survival report
                survival_report = await self.treasury.generate_survival_report()
                
                # Use survival analysis workflow
                survival_result = await self.llm_workflows.analyze_survival_situation(
                    treasury_state=treasury_status,
                    market_context=await self.market_data_collector.get_latest_market_data(),
                    survival_memories=[]  # Would get from memory system
                )
                
                # Implement survival strategies
                await self._implement_survival_strategies(survival_result)
                
                self.metrics['survival_events'] += 1
                
        except Exception as e:
            logger.error(f"❌ Survival check failed: {e}")
    
    async def _implement_survival_strategies(self, survival_result: Dict[str, Any]):
        """Implement survival strategies"""
        try:
            strategies = survival_result.get("immediate_actions", [])
            
            for strategy in strategies:
                if strategy == "minimize_all_costs":
                    self.config['observation_interval'] = 14400  # 4 hours max
                elif strategy == "emergency_mode":
                    self.config['max_daily_costs'] = 5.0  # Reduce daily budget
                elif strategy == "preserve_capital":
                    # Stop all non-essential operations
                    pass
            
            logger.warning(f"🛡️ Survival strategies implemented: {strategies}")
            
        except Exception as e:
            logger.error(f"❌ Survival strategy implementation failed: {e}")
    
    async def _update_learning(self):
        """Update learning and memory consolidation"""
        try:
            # Check if it's time for memory update
            if (self.last_observation_time and 
                (datetime.now(timezone.utc) - self.last_observation_time).total_seconds() >= 
                self.config['memory_update_interval']):
                
                # Consolidate learning
                consolidation = await self.memory_manager.consolidate_learning()
                self.metrics['memories_formed'] = consolidation.get('memory_stats', {}).get('total_memories', 0)
                
        except Exception as e:
            logger.warning(f"Learning update failed: {e}")
    
    async def _generate_daily_summary_if_needed(self):
        """Generate daily summary if it's a new day"""
        try:
            now = datetime.now(timezone.utc)
            if (self.last_observation_time and 
                now.date() > self.last_observation_time.date()):
                
                # Generate daily summary
                summary = await self._generate_daily_summary()
                
                # Store summary
                await self.firestore.log_system_event("daily_summary", summary)
                
        except Exception as e:
            logger.warning(f"Daily summary generation failed: {e}")
    
    async def _generate_daily_summary(self) -> Dict[str, Any]:
        """Generate comprehensive daily summary"""
        treasury_status = await self.treasury.get_status()
        session_summary = await self.llm_workflows.get_session_summary()
        
        return {
            "date": datetime.now(timezone.utc).date().isoformat(),
            "observations": self.observation_count,
            "decisions": self.decisions_made,
            "treasury": treasury_status,
            "costs": session_summary.get("total_cost", 0),
            "survival_events": self.metrics['survival_events'],
            "agent_health": "operational" if self.running else "stopped"
        }
    
    async def get_status(self) -> Dict[str, Any]:
        """Get comprehensive agent status"""
        try:
            treasury_status = await self.treasury.get_status()
            
            uptime = (
                (datetime.now(timezone.utc) - self.metrics['uptime_start']).total_seconds()
                if self.metrics['uptime_start'] else 0
            )
            
            return {
                "agent_id": settings.agent_id,
                "status": "running" if self.running else "stopped",
                "phase": self.phase,
                "uptime_hours": uptime / 3600,
                "observations": self.observation_count,
                "decisions": self.decisions_made,
                "treasury": treasury_status,
                "capabilities": self.capabilities,
                "config": self.config,
                "metrics": self.metrics,
                "last_observation": self.last_observation_time.isoformat() if self.last_observation_time else None
            }
            
        except Exception as e:
            logger.error(f"❌ Status check failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def shutdown(self):
        """Graceful shutdown"""
        try:
            logger.info("🛑 Shutting down Athena DeFi Agent...")
            self.running = False
            
            # Generate final status
            final_status = await self.get_status()
            
            # Create shutdown memory
            if self.mem0:
                await self.mem0.add_memory(
                    content=f"Agent shutdown initiated. Final status: {self.observation_count} observations, "
                           f"{self.decisions_made} decisions, ${final_status.get('treasury', {}).get('balance', 0):.2f} remaining.",
                    metadata={
                        "category": "agent_lifecycle",
                        "importance": 0.8,
                        "shutdown_reason": "graceful_shutdown"
                    }
                )
            
            # Log shutdown
            if self.firestore:
                await self.firestore.log_system_event("agent_shutdown", final_status)
            
            logger.info("✅ Athena DeFi Agent shutdown complete")
            
        except Exception as e:
            logger.error(f"❌ Shutdown error: {e}")
    
    async def _shutdown_cleanup(self):
        """Cleanup during shutdown"""
        try:
            if self.firestore:
                await self.firestore.log_system_event(
                    "agent_stopped",
                    {
                        "stop_time": datetime.now(timezone.utc).isoformat(),
                        "final_metrics": self.metrics
                    }
                )
        except Exception as e:
            logger.warning(f"Cleanup warning: {e}")


# Convenience function to run the agent
async def run_agent():
    """Run the Athena DeFi Agent"""
    agent = DeFiAgent()
    
    try:
        # Initialize
        if await agent.initialize():
            # Start operations
            await agent.start_operations()
        else:
            logger.error("Agent initialization failed")
            
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Agent runtime error: {e}")
    finally:
        await agent.shutdown()


if __name__ == "__main__":
    asyncio.run(run_agent())