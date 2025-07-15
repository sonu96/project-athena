"""
Yield Optimization workflow using LangGraph

This workflow handles compound decisions based on the V1 design:
- Check rewards vs gas costs
- Apply emotional state multipliers
- Consult gas timing memories
- Execute compound operations
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, TypedDict

from langgraph.graph import StateGraph, START, END
from langsmith import traceable

from .state import WorkflowConfig
from ..core.position_manager import PositionManager
from ..integrations.cdp_integration import CDPIntegration
from ..core.memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class YieldOptimizationState(TypedDict):
    """State for yield optimization workflow"""
    # Context
    emotional_state: str
    treasury_balance: float
    days_until_bankruptcy: float
    risk_tolerance: float
    
    # Position data
    position_data: Dict[str, Any]
    pending_rewards: float
    current_apy: float
    
    # Gas data
    gas_price: Dict[str, float]
    gas_timing_memories: List[Dict[str, Any]]
    
    # Decision data
    should_compound: bool
    compound_reasoning: str
    required_multiplier: float
    expected_net_gain: float
    
    # Execution result
    execution_result: Dict[str, Any]
    
    # Costs and errors
    costs_incurred: List[Dict[str, float]]
    errors: List[str]
    warnings: List[str]


class YieldOptimizationNodes:
    """Nodes for the yield optimization workflow"""
    
    def __init__(self, position_manager: PositionManager, cdp: CDPIntegration, memory_manager: MemoryManager):
        self.position_manager = position_manager
        self.cdp = cdp
        self.memory_manager = memory_manager
    
    @traceable(name="check_position_state")
    async def check_position_state(self, state: YieldOptimizationState) -> YieldOptimizationState:
        """Check current position and rewards"""
        try:
            logger.info("📊 Checking Compound position state...")
            
            # Sync position with blockchain
            position = await self.position_manager.sync_position()
            
            # Get position metrics
            metrics = self.position_manager.get_position_metrics()
            
            state["position_data"] = metrics
            state["pending_rewards"] = position.pending_rewards
            state["current_apy"] = position.current_apy
            
            logger.info(f"✅ Position: {position.amount_supplied} USDC, Pending: ${position.pending_rewards:.4f}")
            
            # Check if position exists
            if position.amount_supplied == 0:
                state["warnings"].append("No active Compound position")
                state["should_compound"] = False
                state["compound_reasoning"] = "No position to compound"
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Error checking position: {e}")
            state["errors"].append(f"Position check failed: {str(e)}")
            state["should_compound"] = False
            return state
    
    @traceable(name="analyze_gas_conditions")
    async def analyze_gas_conditions(self, state: YieldOptimizationState) -> YieldOptimizationState:
        """Analyze current gas prices and timing"""
        try:
            logger.info("⛽ Analyzing gas conditions...")
            
            # Get current gas price
            gas_data = await self.cdp.get_gas_price()
            state["gas_price"] = gas_data
            
            # Get current time info
            now = datetime.now(timezone.utc)
            hour = now.hour
            day = now.strftime("%A")
            
            # Search for gas timing memories
            gas_memories = await self.memory_manager.search_memories(
                f"gas patterns {hour} {day} Base network timing",
                category="gas_timing",
                limit=5
            )
            
            state["gas_timing_memories"] = gas_memories
            
            # Analyze if it's a good time based on memories
            if gas_memories:
                # Extract confidence from memories
                avg_confidence = sum(
                    m.get("metadata", {}).get("confidence", 0.5) 
                    for m in gas_memories
                ) / len(gas_memories)
                
                logger.info(f"⏰ Gas timing confidence: {avg_confidence:.2%} based on {len(gas_memories)} memories")
                
                # Add timing analysis to state
                state["gas_price"]["timing_confidence"] = avg_confidence
                state["gas_price"]["is_optimal_time"] = avg_confidence > 0.7
            else:
                state["gas_price"]["timing_confidence"] = 0.5
                state["gas_price"]["is_optimal_time"] = False
            
            logger.info(f"💨 Current gas: {gas_data['gas_price_gwei']:.2f} gwei (${gas_data['estimated_cost_usd']:.4f})")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Error analyzing gas: {e}")
            state["errors"].append(f"Gas analysis failed: {str(e)}")
            return state
    
    @traceable(name="make_compound_decision")
    async def make_compound_decision(self, state: YieldOptimizationState) -> YieldOptimizationState:
        """Decide whether to compound based on V1 design logic"""
        try:
            logger.info("🤔 Making compound decision...")
            
            # Skip if no position
            if state["position_data"].get("amount_supplied", 0) == 0:
                state["should_compound"] = False
                state["compound_reasoning"] = "No active position"
                return state
            
            # Get decision from position manager (implements V1 logic)
            decision = await self.position_manager.should_compound(
                state["emotional_state"],
                state["gas_price"]
            )
            
            state["should_compound"] = decision["should_compound"]
            state["compound_reasoning"] = decision["reasoning"]
            state["required_multiplier"] = decision["required_multiplier"]
            state["expected_net_gain"] = decision.get("net_gain", 0)
            
            # Apply additional constraints based on emotional state
            if state["emotional_state"] == "desperate":
                # In desperate mode, check timing
                hour = datetime.now(timezone.utc).hour
                day = datetime.now(timezone.utc).strftime("%A")
                
                if not (2 <= hour <= 4 and day in ["Saturday", "Sunday"]):
                    if state["gas_price"].get("timing_confidence", 0) < 0.9:
                        state["should_compound"] = False
                        state["compound_reasoning"] += " [DESPERATE: Not optimal gas window]"
                        logger.warning("🚨 Desperate mode: Waiting for optimal gas window")
            
            elif state["emotional_state"] == "cautious":
                # In cautious mode, prefer good timing
                if not state["gas_price"].get("is_optimal_time", False):
                    if state["expected_net_gain"] < 1.0:  # Less than $1 net gain
                        state["should_compound"] = False
                        state["compound_reasoning"] += " [CAUTIOUS: Waiting for better timing]"
            
            # Log decision
            if state["should_compound"]:
                logger.info(f"✅ COMPOUND: {state['compound_reasoning']}")
            else:
                logger.info(f"❌ SKIP: {state['compound_reasoning']}")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Error in compound decision: {e}")
            state["errors"].append(f"Decision failed: {str(e)}")
            state["should_compound"] = False
            return state
    
    @traceable(name="execute_compound")
    async def execute_compound(self, state: YieldOptimizationState) -> YieldOptimizationState:
        """Execute the compound operation if decided"""
        try:
            if not state["should_compound"]:
                logger.info("⏭️ Skipping compound execution")
                state["execution_result"] = {
                    "executed": False,
                    "reason": "Decision was not to compound"
                }
                return state
            
            logger.info("🔄 Executing compound operation...")
            
            # Execute via position manager
            result = await self.position_manager.execute_compound(
                state["emotional_state"],
                state["compound_reasoning"]
            )
            
            state["execution_result"] = result
            
            if result["success"]:
                logger.info(f"✅ Compound successful! Net gain: ${result['net_gain']:.4f}")
                
                # Track cost
                state["costs_incurred"].append({
                    "type": "gas_compound",
                    "amount": result.get("gas_cost", 0),
                    "description": "Compound V3 gas cost"
                })
            else:
                logger.error(f"❌ Compound failed: {result.get('error', 'Unknown error')}")
                state["errors"].append(f"Compound execution failed: {result.get('error', '')}")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Error executing compound: {e}")
            state["errors"].append(f"Execution failed: {str(e)}")
            state["execution_result"] = {
                "executed": False,
                "success": False,
                "error": str(e)
            }
            return state
    
    @traceable(name="form_yield_memories")
    async def form_yield_memories(self, state: YieldOptimizationState) -> YieldOptimizationState:
        """Form memories about the yield optimization experience"""
        try:
            logger.info("🧠 Forming yield optimization memories...")
            
            # Only form memories if we made a decision (either way)
            if state.get("compound_reasoning"):
                
                # Form memory about the decision
                if state["should_compound"] and state.get("execution_result", {}).get("success"):
                    # Successful compound memory
                    memory_content = (
                        f"Successfully compounded {state['pending_rewards']:.4f} USDC with "
                        f"{state['required_multiplier']}x multiplier in {state['emotional_state']} state. "
                        f"Net gain: ${state['expected_net_gain']:.4f}"
                    )
                    
                    await self.memory_manager.add_memory(
                        content=memory_content,
                        category="compound_success",
                        importance=0.7,
                        metadata={
                            "emotional_state": state["emotional_state"],
                            "net_gain": state["expected_net_gain"],
                            "gas_price_gwei": state["gas_price"]["gas_price_gwei"],
                            "hour": datetime.now(timezone.utc).hour,
                            "day": datetime.now(timezone.utc).strftime("%A"),
                            "multiplier_used": state["required_multiplier"]
                        }
                    )
                
                elif not state["should_compound"]:
                    # Skipped compound memory (learn patience)
                    if "gas cost exceeds" in state["compound_reasoning"].lower():
                        memory_content = (
                            f"Wisely skipped compound in {state['emotional_state']} state. "
                            f"Rewards ${state['pending_rewards']:.4f} < {state['required_multiplier']}x gas cost"
                        )
                        
                        await self.memory_manager.add_memory(
                            content=memory_content,
                            category="compound_patience",
                            importance=0.6,
                            metadata={
                                "emotional_state": state["emotional_state"],
                                "rewards_saved": state["pending_rewards"],
                                "gas_avoided": state["gas_price"]["estimated_cost_usd"] * 250
                            }
                        )
                
                # Form gas timing memory if we have timing data
                if state["gas_price"].get("timing_confidence", 0) > 0:
                    hour = datetime.now(timezone.utc).hour
                    day = datetime.now(timezone.utc).strftime("%A")
                    
                    memory_content = (
                        f"Gas price {state['gas_price']['gas_price_gwei']:.2f} gwei at "
                        f"{hour}:00 UTC on {day}"
                    )
                    
                    await self.memory_manager.add_memory(
                        content=memory_content,
                        category="gas_timing",
                        importance=0.5,
                        metadata={
                            "hour": hour,
                            "day": day,
                            "gas_price_gwei": state["gas_price"]["gas_price_gwei"],
                            "confidence": state["gas_price"]["timing_confidence"]
                        }
                    )
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Error forming memories: {e}")
            state["warnings"].append(f"Memory formation failed: {str(e)}")
            return state
    
    def should_execute(self, state: YieldOptimizationState) -> str:
        """Conditional edge to determine if we should execute"""
        return "execute" if state["should_compound"] else "form_memories"


def create_yield_optimization_workflow(
    position_manager: PositionManager,
    cdp: CDPIntegration,
    memory_manager: MemoryManager
) -> StateGraph:
    """Create the yield optimization workflow"""
    
    # Initialize nodes
    nodes = YieldOptimizationNodes(position_manager, cdp, memory_manager)
    
    # Create workflow
    workflow = StateGraph(YieldOptimizationState)
    
    # Add nodes
    workflow.add_node("check_position", nodes.check_position_state)
    workflow.add_node("analyze_gas", nodes.analyze_gas_conditions)
    workflow.add_node("decide_compound", nodes.make_compound_decision)
    workflow.add_node("execute_compound", nodes.execute_compound)
    workflow.add_node("form_memories", nodes.form_yield_memories)
    
    # Define flow
    workflow.add_edge(START, "check_position")
    workflow.add_edge("check_position", "analyze_gas")
    workflow.add_edge("analyze_gas", "decide_compound")
    
    # Conditional edge based on decision
    workflow.add_conditional_edges(
        "decide_compound",
        nodes.should_execute,
        {
            "execute": "execute_compound",
            "form_memories": "form_memories"
        }
    )
    
    workflow.add_edge("execute_compound", "form_memories")
    workflow.add_edge("form_memories", END)
    
    return workflow.compile()