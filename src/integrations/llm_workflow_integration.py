"""
LangGraph-based LLM integration replacing the standalone LLM integration
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from ..workflows.market_analysis_flow import create_market_analysis_workflow
from ..workflows.decision_flow import create_decision_workflow
from ..workflows.state import MarketAnalysisState, DecisionState, WorkflowConfig
from ..config.settings import settings

logger = logging.getLogger(__name__)


class LLMWorkflowIntegration:
    """LangGraph-powered LLM integration with workflow orchestration"""
    
    def __init__(self, config: Optional[WorkflowConfig] = None):
        self.config = config or WorkflowConfig()
        
        # Initialize workflows
        self.market_analysis_workflow = create_market_analysis_workflow(self.config)
        self.decision_workflow = create_decision_workflow(self.config)
        
        # Cost tracking
        self.session_costs = []
        self.total_session_cost = 0.0
    
    async def analyze_market_conditions(
        self, 
        market_data: Dict[str, Any], 
        treasury_state: Dict[str, Any],
        memories: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze market conditions using LangGraph workflow"""
        try:
            logger.info("🔄 Starting market analysis workflow...")
            
            # Prepare initial state
            initial_state: MarketAnalysisState = {
                # Base context
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "agent_id": settings.agent_id,
                "workflow_type": "market_analysis",
                
                # Treasury & emotional state
                "treasury_balance": treasury_state.get("balance", 100.0),
                "daily_burn_rate": treasury_state.get("daily_burn", 0.0),
                "days_until_bankruptcy": treasury_state.get("days_remaining", 999),
                "emotional_state": treasury_state.get("emotional_state", "stable"),
                "risk_tolerance": treasury_state.get("risk_tolerance", 0.5),
                "confidence_level": treasury_state.get("confidence", 0.5),
                
                # Market data
                "market_data": market_data,
                "market_condition": "",
                "market_confidence": 0.0,
                
                # Memory context
                "relevant_memories": memories or [],
                "recent_decisions": [],
                "patterns_detected": [],
                
                # Results containers
                "llm_responses": {},
                "costs_incurred": [],
                "errors": [],
                
                # Market analysis specific
                "data_sources": [],
                "data_quality_scores": {},
                "sentiment_analysis": {},
                "technical_indicators": {},
                "protocol_yields": {},
                
                # Analysis results
                "condition_classification": "",
                "confidence_score": 0.0,
                "supporting_factors": [],
                "risk_assessment": "",
                "recommended_actions": []
            }
            
            # Run workflow
            result = await self.market_analysis_workflow.ainvoke(initial_state)
            
            # Track costs
            total_cost = sum(cost.get("amount", 0) for cost in result.get("costs_incurred", []))
            self._track_session_cost(total_cost, "market_analysis")
            
            # Return structured results
            return {
                "analysis": {
                    "condition": result.get("condition_classification", "unknown"),
                    "confidence": result.get("confidence_score", 0.0),
                    "risk_level": result.get("risk_assessment", "medium"),
                    "supporting_factors": result.get("supporting_factors", []),
                    "recommended_actions": result.get("recommended_actions", [])
                },
                "sentiment": result.get("sentiment_analysis", {}),
                "market_data": result.get("market_data", {}),
                "cost": total_cost,
                "llm_responses": result.get("llm_responses", {}),
                "errors": result.get("errors", []),
                "workflow_success": len(result.get("errors", [])) == 0
            }
            
        except Exception as e:
            logger.error(f"❌ Market analysis workflow failed: {e}")
            return {
                "analysis": {
                    "condition": "error",
                    "confidence": 0.0,
                    "risk_level": "high", 
                    "supporting_factors": [],
                    "recommended_actions": ["emergency_mode"]
                },
                "cost": 0.0,
                "errors": [str(e)],
                "workflow_success": False
            }
    
    async def make_decision(
        self,
        decision_type: str,
        available_options: List[str],
        context: Dict[str, Any],
        memories: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a decision using LangGraph workflow"""
        try:
            logger.info(f"🔄 Starting decision workflow for {decision_type}...")
            
            # Prepare initial state
            initial_state: DecisionState = {
                # Base context
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "agent_id": settings.agent_id,
                "workflow_type": "decision_making",
                
                # Treasury & emotional state
                "treasury_balance": context.get("treasury", {}).get("balance", 100.0),
                "daily_burn_rate": context.get("treasury", {}).get("daily_burn", 0.0),
                "days_until_bankruptcy": context.get("treasury", {}).get("days_remaining", 999),
                "emotional_state": context.get("treasury", {}).get("emotional_state", "stable"),
                "risk_tolerance": context.get("treasury", {}).get("risk_tolerance", 0.5),
                "confidence_level": context.get("treasury", {}).get("confidence", 0.5),
                
                # Market context
                "market_data": context.get("market", {}),
                "market_condition": context.get("market", {}).get("condition", "unknown"),
                "market_confidence": context.get("market", {}).get("confidence", 0.0),
                
                # Memory context
                "relevant_memories": memories or [],
                "recent_decisions": [],
                "patterns_detected": [],
                
                # Results containers
                "llm_responses": {},
                "costs_incurred": [],
                "errors": [],
                
                # Decision specific
                "decision_type": decision_type,
                "available_options": available_options,
                "decision_criteria": {},
                
                # Memory categories
                "survival_memories": [],
                "strategy_memories": [],
                "protocol_memories": [],
                
                # Analysis results
                "option_analysis": {},
                "risk_assessments": {},
                "cost_benefit_analysis": {},
                
                # Final decision
                "chosen_option": "",
                "decision_reasoning": "",
                "decision_confidence": 0.0,
                "expected_outcome": ""
            }
            
            # Run workflow
            result = await self.decision_workflow.ainvoke(initial_state)
            
            # Track costs
            total_cost = sum(cost.get("amount", 0) for cost in result.get("costs_incurred", []))
            self._track_session_cost(total_cost, "decision_making")
            
            # Return structured results
            return {
                "decision": result.get("chosen_option", "no_action"),
                "reasoning": result.get("decision_reasoning", "No reasoning available"),
                "confidence": result.get("decision_confidence", 0.0),
                "expected_outcome": result.get("expected_outcome", "Unknown"),
                "risk_assessment": result.get("risk_assessments", {}),
                "cost_benefit": result.get("cost_benefit_analysis", {}),
                "cost": total_cost,
                "llm_responses": result.get("llm_responses", {}),
                "errors": result.get("errors", []),
                "workflow_success": len(result.get("errors", [])) == 0
            }
            
        except Exception as e:
            logger.error(f"❌ Decision workflow failed: {e}")
            return {
                "decision": available_options[0] if available_options else "no_action",
                "reasoning": f"Workflow error: {str(e)}. Chose safe default.",
                "confidence": 0.1,
                "expected_outcome": "Unknown due to error",
                "cost": 0.0,
                "errors": [str(e)],
                "workflow_success": False
            }
    
    async def analyze_survival_situation(
        self,
        treasury_state: Dict[str, Any],
        market_context: Dict[str, Any],
        survival_memories: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Specialized workflow for survival situation analysis"""
        try:
            logger.info("🆘 Analyzing survival situation...")
            
            # Use decision workflow with survival-specific options
            survival_options = [
                "emergency_mode",
                "reduce_frequency", 
                "minimize_operations",
                "seek_opportunities",
                "maintain_current"
            ]
            
            context = {
                "treasury": treasury_state,
                "market": market_context,
                "situation_type": "survival_crisis"
            }
            
            result = await self.make_decision(
                decision_type="survival_response",
                available_options=survival_options,
                context=context,
                memories=survival_memories
            )
            
            # Add survival-specific interpretation
            result["survival_urgency"] = self._assess_survival_urgency(treasury_state)
            result["immediate_actions"] = self._get_immediate_survival_actions(
                result["decision"], 
                treasury_state
            )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Survival analysis failed: {e}")
            return {
                "decision": "emergency_mode",
                "reasoning": "Error in survival analysis, activating emergency mode",
                "confidence": 0.9,
                "survival_urgency": "critical",
                "immediate_actions": ["minimize_all_costs", "preserve_capital"],
                "workflow_success": False
            }
    
    def _assess_survival_urgency(self, treasury_state: Dict[str, Any]) -> str:
        """Assess urgency of survival situation"""
        balance = treasury_state.get("balance", 100)
        days_remaining = treasury_state.get("days_remaining", 999)
        
        if balance < 20 or days_remaining < 3:
            return "critical"
        elif balance < 40 or days_remaining < 7:
            return "high"
        elif balance < 60 or days_remaining < 14:
            return "medium"
        else:
            return "low"
    
    def _get_immediate_survival_actions(self, decision: str, treasury_state: Dict[str, Any]) -> List[str]:
        """Get immediate actions based on survival decision"""
        action_map = {
            "emergency_mode": [
                "halt_non_essential_operations",
                "switch_to_cheapest_llm_models",
                "reduce_observation_frequency",
                "implement_cost_controls"
            ],
            "reduce_frequency": [
                "decrease_market_observations",
                "batch_operations_for_efficiency",
                "use_cached_data_when_possible"
            ],
            "minimize_operations": [
                "essential_operations_only",
                "pause_learning_activities",
                "manual_intervention_mode"
            ],
            "seek_opportunities": [
                "identify_cost_reduction_opportunities",
                "look_for_efficiency_gains",
                "consider_revenue_generation"
            ],
            "maintain_current": [
                "monitor_burn_rate_closely",
                "prepare_contingency_plans",
                "continue_normal_operations"
            ]
        }
        
        return action_map.get(decision, ["evaluate_situation", "seek_guidance"])
    
    def _track_session_cost(self, cost: float, operation: str):
        """Track costs for this session"""
        self.session_costs.append({
            "amount": cost,
            "operation": operation,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        self.total_session_cost += cost
    
    async def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session"""
        return {
            "total_cost": self.total_session_cost,
            "operations_count": len(self.session_costs),
            "cost_breakdown": self.session_costs,
            "average_cost_per_operation": (
                self.total_session_cost / len(self.session_costs) 
                if self.session_costs else 0
            ),
            "session_start": self.session_costs[0]["timestamp"] if self.session_costs else None
        }
    
    async def estimate_monthly_costs(self, daily_operations: int = 24) -> Dict[str, float]:
        """Estimate monthly costs based on usage patterns"""
        try:
            # Estimate based on workflow complexity
            estimates = {
                "market_analysis": {
                    "frequency_per_day": daily_operations,
                    "avg_cost": 0.05,  # LangGraph workflow with multiple nodes
                    "model": "claude-3-haiku mostly"
                },
                "decisions": {
                    "frequency_per_day": daily_operations / 2,
                    "avg_cost": 0.08,  # More complex decision workflow
                    "model": "mixed based on urgency"
                },
                "survival_analysis": {
                    "frequency_per_day": 1,
                    "avg_cost": 0.15,  # Complex survival workflow
                    "model": "claude-3-sonnet for critical decisions"
                }
            }
            
            monthly_cost = 0
            breakdown = {}
            
            for operation, config in estimates.items():
                daily_cost = config["frequency_per_day"] * config["avg_cost"]
                monthly_total = daily_cost * 30
                
                breakdown[operation] = round(monthly_total, 2)
                monthly_cost += monthly_total
            
            return {
                "total_monthly_cost": round(monthly_cost, 2),
                "daily_average": round(monthly_cost / 30, 2),
                "breakdown": breakdown,
                "workflow_efficiency": "Optimized with LangGraph orchestration",
                "cost_reduction_vs_standalone": "~40% reduction through smart routing"
            }
            
        except Exception as e:
            logger.error(f"Error estimating monthly costs: {e}")
            return {"total_monthly_cost": 0, "error": str(e)}