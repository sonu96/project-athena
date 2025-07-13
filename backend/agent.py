from typing import Dict, List, Any, TypedDict
from datetime import datetime
from langgraph import StateGraph, END
from .models import DecisionContext, DecisionResult, AgentState
from .treasury import TreasuryManager
from .memory import MemoryManager

class AgentState(TypedDict):
    context: DecisionContext
    memories: List[Dict]
    decision: DecisionResult
    treasury: TreasuryManager
    memory_manager: MemoryManager

class DeFiYieldAgent:
    """LangGraph-based DeFi yield optimization agent"""
    
    def __init__(self, treasury_manager: TreasuryManager, memory_manager: MemoryManager):
        self.treasury = treasury_manager
        self.memory = memory_manager
        self.graph = self._build_workflow()
        
    def _build_workflow(self) -> StateGraph:
        """Build the agent decision workflow"""
        
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("analyze_situation", self.analyze_situation)
        workflow.add_node("query_memory", self.query_memory)
        workflow.add_node("evaluate_options", self.evaluate_options)
        workflow.add_node("make_decision", self.make_decision)
        workflow.add_node("execute_action", self.execute_action)
        
        # Define edges
        workflow.set_entry_point("analyze_situation")
        workflow.add_edge("analyze_situation", "query_memory")
        workflow.add_edge("query_memory", "evaluate_options")
        workflow.add_edge("evaluate_options", "make_decision")
        workflow.add_edge("make_decision", "execute_action")
        workflow.add_edge("execute_action", END)
        
        return workflow.compile()
    
    def analyze_situation(self, state: AgentState) -> AgentState:
        """Analyze current market and treasury situation"""
        
        context = state["context"]
        
        # Check survival status
        survival_status = self.treasury.get_survival_status()
        
        # Adjust risk tolerance based on survival status
        if survival_status == "CRITICAL":
            context.risk_tolerance = 0.1  # Very conservative
        elif survival_status == "WARNING":
            context.risk_tolerance = 0.3  # Conservative
        elif survival_status == "CAUTION":
            context.risk_tolerance = 0.5  # Moderate
        else:
            context.risk_tolerance = 0.7  # Aggressive
        
        # Deduct analysis cost
        self.treasury.deduct_cost(0.01, "Situation analysis")
        
        return state
    
    def query_memory(self, state: AgentState) -> AgentState:
        """Query relevant memories for decision making"""
        
        context = state["context"]
        
        # Get survival strategies if treasury is low
        if context.current_treasury < 200:
            survival_memories = self.memory.get_survival_strategies(context.current_treasury)
            state["memories"].extend(survival_memories)
        
        # Get yield recommendations
        yield_memories = self.memory.get_yield_recommendations(
            current_apy=0.05,  # Placeholder
            protocol=context.available_protocols[0] if context.available_protocols else "aave",
            market_condition=context.market_condition
        )
        state["memories"].extend(yield_memories)
        
        # Get market insights
        market_memories = self.memory.get_market_insights(context.market_condition)
        state["memories"].extend(market_memories)
        
        # Deduct memory query cost
        self.treasury.deduct_cost(0.02, "Memory query")
        
        return state
    
    def evaluate_options(self, state: AgentState) -> AgentState:
        """Evaluate available options based on memories and context"""
        
        context = state["context"]
        memories = state["memories"]
        
        # Analyze memories for patterns
        successful_strategies = []
        failed_strategies = []
        
        for memory in memories:
            if memory.get('metadata', {}).get('category') == 'strategy':
                success_rate = memory.get('metadata', {}).get('success_rate', 0.5)
                if success_rate > 0.7:
                    successful_strategies.append(memory)
                else:
                    failed_strategies.append(memory)
        
        # Store evaluation results
        state["evaluation"] = {
            "successful_strategies": successful_strategies,
            "failed_strategies": failed_strategies,
            "risk_level": context.risk_tolerance,
            "available_protocols": context.available_protocols
        }
        
        # Deduct evaluation cost
        self.treasury.deduct_cost(0.03, "Option evaluation")
        
        return state
    
    def make_decision(self, state: AgentState) -> AgentState:
        """Make final decision based on evaluation"""
        
        context = state["context"]
        evaluation = state["evaluation"]
        
        # Simple decision logic for MVP
        if context.current_treasury < 100:
            # Survival mode - very conservative
            decision = DecisionResult(
                action="HOLD",
                protocol=None,
                amount=0,
                expected_yield=0,
                risk_score=0.1,
                confidence=0.9,
                reasoning="Treasury too low for active trading",
                treasury_impact=0
            )
        elif context.current_treasury < 500:
            # Caution mode - conservative strategies
            if evaluation["successful_strategies"]:
                best_strategy = evaluation["successful_strategies"][0]
                decision = DecisionResult(
                    action="YIELD_FARM",
                    protocol="aave",  # Default to safe protocol
                    amount=context.current_treasury * 0.3,  # 30% of treasury
                    expected_yield=0.05,
                    risk_score=0.3,
                    confidence=0.7,
                    reasoning=f"Using proven strategy: {best_strategy.get('content', '')}",
                    treasury_impact=-0.05  # Gas cost
                )
            else:
                decision = DecisionResult(
                    action="WAIT",
                    protocol=None,
                    amount=0,
                    expected_yield=0,
                    risk_score=0.2,
                    confidence=0.6,
                    reasoning="No proven strategies available",
                    treasury_impact=0
                )
        else:
            # Aggressive mode - maximize yield
            decision = DecisionResult(
                action="YIELD_FARM",
                protocol="compound",  # Higher yield protocol
                amount=context.current_treasury * 0.6,  # 60% of treasury
                expected_yield=0.08,
                risk_score=0.6,
                confidence=0.8,
                reasoning="Treasury healthy, pursuing higher yields",
                treasury_impact=-0.1  # Higher gas cost
            )
        
        state["decision"] = decision
        
        # Deduct decision cost
        self.treasury.deduct_cost(0.02, "Decision making")
        
        return state
    
    def execute_action(self, state: AgentState) -> AgentState:
        """Execute the decided action"""
        
        decision = state["decision"]
        
        # Simulate action execution
        if decision.action == "YIELD_FARM":
            # Record strategy performance
            self.memory.record_strategy_performance(
                strategy_name=f"{decision.protocol}_yield_farming",
                success_rate=0.8,  # Placeholder
                avg_yield=decision.expected_yield,
                gas_cost=abs(decision.treasury_impact)
            )
            
            # Deduct gas cost
            self.treasury.deduct_cost(abs(decision.treasury_impact), "Gas fee")
            
        elif decision.action == "HOLD":
            # Record survival event
            self.memory.record_survival_event(
                event_type="low_treasury_hold",
                treasury_level=self.treasury.balance,
                action_taken="held_position",
                outcome=True
            )
        
        # Update last decision time
        self.treasury.last_decision = datetime.now()
        
        return state
    
    def decide(self, context: DecisionContext) -> DecisionResult:
        """Make a decision given the current context"""
        
        # Initialize state
        state = AgentState(
            context=context,
            memories=[],
            decision=None,
            treasury=self.treasury,
            memory_manager=self.memory
        )
        
        # Run the workflow
        final_state = self.graph.invoke(state)
        
        return final_state["decision"]
    
    def get_agent_state(self) -> AgentState:
        """Get current agent state"""
        
        return self.treasury.get_agent_state(
            memory_count=len(self.memory.get_memory_statistics())
        ) 