"""
Node implementations for the cognitive loop

Each node wraps existing functionality into the unified consciousness flow,
maintaining the Sense → Think → Feel → Decide → Learn cycle.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List

from langsmith import traceable

from .consciousness import ConsciousnessState
from ..data.market_data_collector import MarketDataCollector
from ..integrations.cdp_integration import CDPIntegration
from ..workflows.market_analysis_flow import create_market_analysis_workflow
from ..workflows.decision_flow import create_decision_workflow
from ..core.memory_manager import MemoryManager
from ..data.firestore_client import FirestoreClient
from ..data.bigquery_client import BigQueryClient
from ..integrations.mem0_integration import Mem0Integration

logger = logging.getLogger(__name__)


class SenseNode:
    """Perceive the environment - wrapper for market data collection and wallet monitoring"""
    
    def __init__(self):
        self.market_collector = None
        self.cdp = None
        self._initialized = False
    
    async def _ensure_initialized(self):
        """Lazy initialization of components"""
        if not self._initialized:
            firestore = FirestoreClient()
            bigquery = BigQueryClient()
            self.market_collector = MarketDataCollector(firestore, bigquery)
            self.cdp = CDPIntegration()
            await self.cdp.initialize_wallet()
            self._initialized = True
    
    @traceable(name="sense_environment")
    async def execute(self, state: ConsciousnessState) -> ConsciousnessState:
        """Sense the environment and update perception"""
        try:
            await self._ensure_initialized()
            
            logger.info("👁️ Sensing environment...")
            
            # Collect market data
            market_result = await self.market_collector.collect_comprehensive_market_data()
            if market_result['success']:
                state["market_data"] = market_result.get("data", {})
            else:
                state["warnings"].append(f"Market data collection failed: {market_result.get('error')}")
                # Use previous market data if available
                if not state.get("market_data"):
                    state["market_data"] = {}
            
            # Check wallet balance
            try:
                wallet_balance = await self.cdp.get_wallet_balance()
                state["treasury_balance"] = wallet_balance.get("total_usd", state.get("treasury_balance", 100.0))
            except Exception as e:
                logger.warning(f"Failed to get wallet balance: {e}")
                # Keep previous balance
            
            # Update perception timestamp
            state["timestamp"] = datetime.now(timezone.utc)
            
            # Add perception cost
            state["total_cost"] = state.get("total_cost", 0.0) + 0.02  # Base sensing cost
            
            logger.info(f"✅ Environment sensed - Balance: ${state['treasury_balance']:.2f}")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Error in sense node: {e}")
            state["errors"].append(f"Sense error: {str(e)[:100]}")
            return state


class ThinkNode:
    """Analyze and understand - wrapper for market analysis"""
    
    def __init__(self):
        self.analysis_workflow = None
        self._initialized = False
    
    async def _ensure_initialized(self):
        """Lazy initialization of workflow"""
        if not self._initialized:
            self.analysis_workflow = create_market_analysis_workflow()
            self._initialized = True
    
    @traceable(name="think_analysis")
    async def execute(self, state: ConsciousnessState) -> ConsciousnessState:
        """Analyze market conditions and detect patterns"""
        try:
            await self._ensure_initialized()
            
            logger.info("🧠 Thinking and analyzing...")
            
            # Prepare analysis input
            analysis_input = {
                "market_data": state.get("market_data", {}),
                "treasury_balance": state.get("treasury_balance", 100.0),
                "emotional_state": state.get("emotional_state", "stable"),
                "risk_tolerance": self._get_risk_tolerance(state["emotional_state"]),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "agent_id": state.get("agent_id", "athena_001"),
                "workflow_type": "market_analysis"
            }
            
            # Run market analysis
            analysis_result = await self.analysis_workflow.ainvoke(analysis_input)
            
            # Extract patterns and insights
            state["active_patterns"] = analysis_result.get("patterns_detected", [])
            
            # Determine current goal based on analysis
            state["current_goal"] = self._determine_goal(analysis_result, state)
            
            # Add market condition to state
            if "market_condition" in analysis_result:
                state["market_data"]["condition"] = analysis_result["market_condition"]
                state["market_data"]["confidence"] = analysis_result.get("market_confidence", 0.5)
            
            # Track analysis cost
            analysis_cost = sum(cost.get("amount", 0) for cost in analysis_result.get("costs_incurred", []))
            state["total_cost"] = state.get("total_cost", 0.0) + analysis_cost
            
            logger.info(f"✅ Analysis complete - Goal: {state['current_goal']}, Patterns: {len(state['active_patterns'])}")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Error in think node: {e}")
            state["errors"].append(f"Think error: {str(e)[:100]}")
            return state
    
    def _get_risk_tolerance(self, emotional_state: str) -> float:
        """Get risk tolerance based on emotional state"""
        risk_map = {
            "desperate": 0.2,
            "cautious": 0.4,
            "stable": 0.6,
            "confident": 0.8
        }
        return risk_map.get(emotional_state, 0.5)
    
    def _determine_goal(self, analysis: Dict, state: ConsciousnessState) -> str:
        """Determine current goal based on analysis and emotional state"""
        emotional_state = state.get("emotional_state", "stable")
        market_condition = analysis.get("market_condition", "neutral")
        
        if emotional_state == "desperate":
            return "survive_and_preserve"
        elif market_condition == "volatile":
            return "monitor_carefully"
        elif emotional_state == "confident" and market_condition in ["bull", "strong_bull"]:
            return "explore_opportunities"
        else:
            return "observe_and_learn"


class FeelNode:
    """Update emotional state based on situation"""
    
    @traceable(name="feel_emotions")
    async def execute(self, state: ConsciousnessState) -> ConsciousnessState:
        """Update emotional state based on treasury and conditions"""
        try:
            logger.info("💭 Feeling and updating emotional state...")
            
            balance = state.get("treasury_balance", 100.0)
            cycle_count = max(state.get("cycle_count", 0), 1)
            total_cost = state.get("total_cost", 0.0)
            
            # Calculate burn rate
            burn_rate = total_cost / cycle_count
            
            # Calculate days until bankruptcy
            if burn_rate > 0:
                state["days_until_bankruptcy"] = int(balance / burn_rate)
            else:
                state["days_until_bankruptcy"] = 999
            
            # Update emotional state based on treasury and survival outlook
            previous_state = state.get("emotional_state", "stable")
            
            if balance < 25 or state["days_until_bankruptcy"] < 5:
                state["emotional_state"] = "desperate"
            elif balance < 50 or state["days_until_bankruptcy"] < 10:
                state["emotional_state"] = "cautious"
            elif balance < 100 or state["days_until_bankruptcy"] < 30:
                state["emotional_state"] = "stable"
            else:
                state["emotional_state"] = "confident"
            
            # Log emotional state changes
            if previous_state != state["emotional_state"]:
                logger.warning(f"😱 Emotional state changed: {previous_state} → {state['emotional_state']}")
                logger.warning(f"   Balance: ${balance:.2f}, Days until bankruptcy: {state['days_until_bankruptcy']}")
            
            logger.info(f"✅ Emotional state: {state['emotional_state']} (${balance:.2f}, {state['days_until_bankruptcy']} days)")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Error in feel node: {e}")
            state["errors"].append(f"Feel error: {str(e)[:100]}")
            return state


class DecideNode:
    """Make decisions based on full context"""
    
    def __init__(self):
        self.decision_workflow = None
        self._initialized = False
    
    async def _ensure_initialized(self):
        """Lazy initialization of workflow"""
        if not self._initialized:
            self.decision_workflow = create_decision_workflow()
            self._initialized = True
    
    @traceable(name="decide_action")
    async def execute(self, state: ConsciousnessState) -> ConsciousnessState:
        """Make decisions based on emotional state and context"""
        try:
            await self._ensure_initialized()
            
            logger.info("🎯 Making decision...")
            
            # Determine available actions based on emotional state
            emotional_state = state.get("emotional_state", "stable")
            
            if emotional_state == "desperate":
                state["available_actions"] = ["emergency_mode", "minimize_costs", "preserve_capital"]
            elif emotional_state == "cautious":
                state["available_actions"] = ["reduce_frequency", "conservative_observation", "maintain_reserves"]
            elif emotional_state == "confident":
                state["available_actions"] = ["active_monitoring", "explore_patterns", "optimize_learning"]
            else:  # stable
                state["available_actions"] = ["normal_observation", "balanced_approach", "maintain_schedule"]
            
            # Prepare decision input
            decision_input = {
                "decision_type": "operational",
                "available_options": state["available_actions"],
                "treasury_balance": state.get("treasury_balance", 100.0),
                "emotional_state": emotional_state,
                "market_condition": state.get("active_patterns", ["neutral"])[0] if state.get("active_patterns") else "neutral",
                "relevant_memories": state.get("recent_memories", [])[:5],
                "days_until_bankruptcy": state.get("days_until_bankruptcy", 999),
                "current_goal": state.get("current_goal", "observe_and_learn"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "agent_id": state.get("agent_id", "athena_001"),
                "workflow_type": "decision"
            }
            
            # Make decision
            decision_result = await self.decision_workflow.ainvoke(decision_input)
            
            # Update state with decision
            state["last_decision"] = {
                "action": decision_result.get("chosen_option", "maintain_current"),
                "reasoning": decision_result.get("decision_reasoning", ""),
                "confidence": decision_result.get("decision_confidence", 0.5),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            state["decision_confidence"] = decision_result.get("decision_confidence", 0.5)
            
            # Track decision cost
            decision_cost = sum(cost.get("amount", 0) for cost in decision_result.get("costs_incurred", []))
            state["total_cost"] = state.get("total_cost", 0.0) + decision_cost
            
            logger.info(f"✅ Decision made: {state['last_decision']['action']} (confidence: {state['decision_confidence']:.2f})")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Error in decide node: {e}")
            state["errors"].append(f"Decide error: {str(e)[:100]}")
            # Fallback decision
            state["last_decision"] = {
                "action": "maintain_current",
                "reasoning": "Error in decision making, maintaining current approach",
                "confidence": 0.1,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            return state


class LearnNode:
    """Form memories and learn from experience"""
    
    def __init__(self):
        self.memory_manager = None
        self._initialized = False
    
    async def _ensure_initialized(self):
        """Lazy initialization of memory components"""
        if not self._initialized:
            firestore = FirestoreClient()
            bigquery = BigQueryClient()
            mem0 = Mem0Integration(firestore, bigquery)
            await mem0.initialize_memory_system()
            self.memory_manager = MemoryManager(mem0, firestore, bigquery)
            self._initialized = True
    
    @traceable(name="learn_experience")
    async def execute(self, state: ConsciousnessState) -> ConsciousnessState:
        """Process experience and form memories"""
        try:
            await self._ensure_initialized()
            
            logger.info("📚 Learning from experience...")
            
            # Create experience from current cycle
            experience = {
                "type": "consciousness_cycle",
                "timestamp": state.get("timestamp", datetime.now(timezone.utc)),
                "cycle_number": state.get("cycle_count", 0),
                "emotional_state": state.get("emotional_state", "stable"),
                "treasury_balance": state.get("treasury_balance", 100.0),
                "days_until_bankruptcy": state.get("days_until_bankruptcy", 999),
                "market_patterns": state.get("active_patterns", []),
                "current_goal": state.get("current_goal", "observe_and_learn"),
                "decision": state.get("last_decision", {}),
                "decision_confidence": state.get("decision_confidence", 0.5),
                "total_cost": state.get("total_cost", 0.0),
                "errors_count": len(state.get("errors", [])),
                "warnings_count": len(state.get("warnings", [])),
                "success": len(state.get("errors", [])) == 0
            }
            
            # Process experience into memory
            await self.memory_manager.process_experience(experience)
            
            # Get updated relevant memories for next cycle
            memory_context = {
                "emotional_state": state.get("emotional_state", "stable"),
                "current_goal": state.get("current_goal", "observe_and_learn"),
                "patterns": state.get("active_patterns", []),
                "treasury_status": "critical" if state.get("days_until_bankruptcy", 999) < 10 else "normal"
            }
            
            memories_result = await self.memory_manager.get_relevant_memories(memory_context)
            state["recent_memories"] = memories_result.get("memories", [])[:10]
            
            # Consolidate learning every 10 cycles
            if state.get("cycle_count", 0) % 10 == 0 and state.get("cycle_count", 0) > 0:
                consolidation = await self.memory_manager.consolidate_learning()
                state["lessons_learned"] = consolidation.get("key_lessons", [])
                logger.info(f"📖 Consolidated learning: {len(state['lessons_learned'])} lessons")
            
            # Increment cycle count
            state["cycle_count"] = state.get("cycle_count", 0) + 1
            
            # Clear errors and warnings for next cycle (keep last 5)
            state["errors"] = state.get("errors", [])[-5:]
            state["warnings"] = state.get("warnings", [])[-5:]
            
            logger.info(f"✅ Learning complete - Cycle {state['cycle_count']}, Memories: {len(state['recent_memories'])}")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Error in learn node: {e}")
            state["errors"].append(f"Learn error: {str(e)[:100]}")
            return state