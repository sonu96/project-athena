"""
Decision-making workflow using LangGraph with memory integration
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List

from langgraph.graph import StateGraph, START, END
from langsmith import traceable
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

from .state import DecisionState, WorkflowConfig
from ..config.settings import settings

logger = logging.getLogger(__name__)


class DecisionNodes:
    """LangGraph nodes for decision-making workflow"""
    
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.anthropic_client = AsyncAnthropic(api_key=settings.anthropic_api_key) if settings.anthropic_api_key else None
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
        
        # Cost tracking
        self.model_costs = {
            "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
            "claude-3-sonnet": {"input": 0.003, "output": 0.015},
            "gpt-4": {"input": 0.01, "output": 0.03},
            "gpt-3.5": {"input": 0.001, "output": 0.002}
        }
    
    @traceable(name="load_decision_context")
    async def load_decision_context(self, state: DecisionState) -> DecisionState:
        """Load context for decision making"""
        try:
            logger.info(f"📋 Loading context for {state['decision_type']} decision...")
            
            # Categorize memories by type for better organization
            survival_memories = []
            strategy_memories = []
            protocol_memories = []
            
            for memory in state.get("relevant_memories", []):
                category = memory.get("metadata", {}).get("category", "")
                if "survival" in category:
                    survival_memories.append(memory)
                elif "strategy" in category or "decision" in category:
                    strategy_memories.append(memory)
                elif "protocol" in category:
                    protocol_memories.append(memory)
            
            # Update state with categorized memories
            state["survival_memories"] = survival_memories
            state["strategy_memories"] = strategy_memories
            state["protocol_memories"] = protocol_memories
            
            # Set decision criteria based on emotional state
            criteria = {}
            if state["emotional_state"] == "desperate":
                criteria = {
                    "cost_sensitivity": 1.0,
                    "risk_aversion": 1.0,
                    "time_preference": "immediate",
                    "primary_goal": "survival"
                }
            elif state["emotional_state"] == "cautious":
                criteria = {
                    "cost_sensitivity": 0.8,
                    "risk_aversion": 0.7,
                    "time_preference": "short_term",
                    "primary_goal": "preservation"
                }
            elif state["emotional_state"] == "stable":
                criteria = {
                    "cost_sensitivity": 0.5,
                    "risk_aversion": 0.5,
                    "time_preference": "balanced",
                    "primary_goal": "optimization"
                }
            else:  # confident
                criteria = {
                    "cost_sensitivity": 0.3,
                    "risk_aversion": 0.3,
                    "time_preference": "long_term",
                    "primary_goal": "growth"
                }
            
            state["decision_criteria"] = criteria
            
            logger.info(f"✅ Decision context loaded: {len(survival_memories)} survival, {len(strategy_memories)} strategy memories")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Error loading decision context: {e}")
            state["errors"].append(f"Context loading failed: {str(e)}")
            return state
    
    @traceable(name="analyze_options")
    async def analyze_options(self, state: DecisionState) -> DecisionState:
        """Analyze all available options"""
        try:
            logger.info(f"🔍 Analyzing {len(state['available_options'])} options...")
            
            option_analysis = {}
            
            for option in state["available_options"]:
                # Analyze each option
                analysis = await self._analyze_single_option(option, state)
                option_analysis[option] = analysis
            
            state["option_analysis"] = option_analysis
            
            logger.info(f"✅ All options analyzed")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Error analyzing options: {e}")
            state["errors"].append(f"Option analysis failed: {str(e)}")
            return state
    
    @traceable(name="assess_risks")
    async def assess_risks(self, state: DecisionState) -> DecisionState:
        """Assess risks for each option"""
        try:
            logger.info("⚠️ Assessing risks...")
            
            risk_assessments = {}
            
            for option in state["available_options"]:
                # Risk assessment based on multiple factors
                risks = {
                    "financial_risk": self._assess_financial_risk(option, state),
                    "operational_risk": self._assess_operational_risk(option, state),
                    "market_risk": self._assess_market_risk(option, state),
                    "survival_risk": self._assess_survival_risk(option, state)
                }
                
                # Calculate overall risk score
                weights = {
                    "financial_risk": 0.4,
                    "operational_risk": 0.2,
                    "market_risk": 0.2,
                    "survival_risk": 0.2
                }
                
                if state["emotional_state"] == "desperate":
                    weights["survival_risk"] = 0.5  # Survival risk weighs more
                    weights["financial_risk"] = 0.3
                
                overall_risk = sum(risks[risk_type] * weights[risk_type] for risk_type in risks)
                
                risk_assessments[option] = {
                    "detailed_risks": risks,
                    "overall_risk": overall_risk,
                    "risk_level": "high" if overall_risk > 0.7 else "medium" if overall_risk > 0.4 else "low"
                }
            
            state["risk_assessments"] = risk_assessments
            
            logger.info(f"✅ Risk assessments completed")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Error assessing risks: {e}")
            state["errors"].append(f"Risk assessment failed: {str(e)}")
            return state
    
    @traceable(name="perform_cost_benefit_analysis")
    async def perform_cost_benefit_analysis(self, state: DecisionState) -> DecisionState:
        """Perform cost-benefit analysis"""
        try:
            logger.info("💰 Performing cost-benefit analysis...")
            
            cost_benefit_analysis = {}
            
            for option in state["available_options"]:
                analysis = {
                    "estimated_costs": self._estimate_costs(option, state),
                    "potential_benefits": self._estimate_benefits(option, state),
                    "time_to_impact": self._estimate_time_to_impact(option, state),
                    "success_probability": self._estimate_success_probability(option, state)
                }
                
                # Calculate expected value
                expected_value = (
                    analysis["potential_benefits"] * analysis["success_probability"] - 
                    analysis["estimated_costs"]
                )
                
                analysis["expected_value"] = expected_value
                analysis["roi"] = expected_value / max(analysis["estimated_costs"], 0.01)
                
                cost_benefit_analysis[option] = analysis
            
            state["cost_benefit_analysis"] = cost_benefit_analysis
            
            logger.info(f"✅ Cost-benefit analysis completed")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Error in cost-benefit analysis: {e}")
            state["errors"].append(f"Cost-benefit analysis failed: {str(e)}")
            return state
    
    @traceable(name="make_final_decision")
    async def make_final_decision(self, state: DecisionState) -> DecisionState:
        """Make the final decision using LLM with all context"""
        try:
            logger.info("🎯 Making final decision...")
            
            # Select model based on decision importance and emotional state
            model = self._select_model_for_decision(state)
            
            # Prepare comprehensive decision prompt
            prompt = self._build_decision_prompt(state)
            
            # Generate decision
            response = await self._call_llm(model, prompt, state["emotional_state"])
            
            # Parse decision from response
            decision_result = self._parse_decision_response(response["content"], state["available_options"])
            
            # Update state with decision
            state["chosen_option"] = decision_result["decision"]
            state["decision_reasoning"] = decision_result["reasoning"]
            state["decision_confidence"] = decision_result["confidence"]
            state["expected_outcome"] = decision_result.get("expected_outcome", "Unknown outcome")
            
            # Track cost
            state["costs_incurred"].append({
                "amount": response["cost"],
                "type": "decision_making",
                "description": f"Final decision with {response['model']}"
            })
            
            state["llm_responses"]["final_decision"] = response
            
            logger.info(f"✅ Decision made: {decision_result['decision']} (confidence: {decision_result['confidence']:.2f})")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Error making final decision: {e}")
            state["errors"].append(f"Final decision failed: {str(e)}")
            # Fallback to safe option
            state["chosen_option"] = state["available_options"][0] if state["available_options"] else "no_action"
            state["decision_reasoning"] = "Error in decision making, chose safe default"
            state["decision_confidence"] = 0.1
            return state
    
    async def _analyze_single_option(self, option: str, state: DecisionState) -> Dict[str, Any]:
        """Analyze a single option"""
        # This would contain more sophisticated analysis
        return {
            "description": f"Analysis of {option}",
            "feasibility": 0.8,  # Example score
            "alignment_with_goals": 0.7,
            "resource_requirements": "medium",
            "implementation_complexity": "low"
        }
    
    def _assess_financial_risk(self, option: str, state: DecisionState) -> float:
        """Assess financial risk of an option"""
        # Base risk assessment
        base_risk = 0.5
        
        # Adjust based on treasury state
        if state["treasury_balance"] < 30:
            base_risk += 0.3  # Higher risk when treasury is low
        
        # Adjust based on emotional state
        if state["emotional_state"] == "desperate":
            base_risk += 0.2
        
        return min(base_risk, 1.0)
    
    def _assess_operational_risk(self, option: str, state: DecisionState) -> float:
        """Assess operational risk"""
        # Example implementation
        return 0.3
    
    def _assess_market_risk(self, option: str, state: DecisionState) -> float:
        """Assess market risk"""
        market_condition = state.get("market_condition", "neutral")
        
        if market_condition in ["volatile", "strong_bear"]:
            return 0.8
        elif market_condition in ["bear"]:
            return 0.6
        elif market_condition in ["neutral"]:
            return 0.4
        else:  # bull markets
            return 0.3
    
    def _assess_survival_risk(self, option: str, state: DecisionState) -> float:
        """Assess survival risk"""
        if state["days_until_bankruptcy"] < 5:
            return 0.9
        elif state["days_until_bankruptcy"] < 10:
            return 0.6
        else:
            return 0.2
    
    def _estimate_costs(self, option: str, state: DecisionState) -> float:
        """Estimate costs for an option"""
        # Example cost estimation
        base_costs = {
            "observe_market": 0.10,
            "reduce_frequency": -0.05,  # Cost reduction
            "emergency_mode": 0.02,
            "no_action": 0.0
        }
        return base_costs.get(option, 1.0)
    
    def _estimate_benefits(self, option: str, state: DecisionState) -> float:
        """Estimate potential benefits"""
        # Example benefit estimation
        base_benefits = {
            "observe_market": 2.0,
            "reduce_frequency": 0.5,
            "emergency_mode": 1.0,
            "no_action": 0.0
        }
        return base_benefits.get(option, 0.5)
    
    def _estimate_time_to_impact(self, option: str, state: DecisionState) -> str:
        """Estimate time to see impact"""
        time_mapping = {
            "observe_market": "immediate",
            "reduce_frequency": "immediate",
            "emergency_mode": "immediate",
            "no_action": "none"
        }
        return time_mapping.get(option, "unknown")
    
    def _estimate_success_probability(self, option: str, state: DecisionState) -> float:
        """Estimate probability of success"""
        # Based on memories and past experiences
        success_rates = {
            "observe_market": 0.8,
            "reduce_frequency": 0.9,
            "emergency_mode": 0.7,
            "no_action": 0.5
        }
        return success_rates.get(option, 0.6)
    
    def _select_model_for_decision(self, state: DecisionState) -> str:
        """Select appropriate model for decision"""
        if state["emotional_state"] == "desperate":
            return "claude-3-sonnet"  # Critical decision needs good model
        elif state["decision_type"] in ["critical", "survival"]:
            return "claude-3-sonnet"
        else:
            return "claude-3-haiku"  # Economic choice for routine decisions
    
    def _build_decision_prompt(self, state: DecisionState) -> str:
        """Build comprehensive decision prompt"""
        option_summaries = []
        for option in state["available_options"]:
            risk = state["risk_assessments"].get(option, {})
            cba = state["cost_benefit_analysis"].get(option, {})
            
            summary = f"""
Option: {option}
- Risk Level: {risk.get('risk_level', 'unknown')}
- Expected Value: ${cba.get('expected_value', 0):.2f}
- Success Probability: {cba.get('success_probability', 0.5):.1%}
- Estimated Cost: ${cba.get('estimated_costs', 0):.2f}
"""
            option_summaries.append(summary)
        
        relevant_memories = "\n".join([
            f"- {mem.get('content', '')}" 
            for mem in state.get("survival_memories", [])[:3]
        ])
        
        prompt = f"""You are Athena, an autonomous DeFi agent making a critical decision. 

Current Context:
- Treasury Balance: ${state['treasury_balance']:.2f}
- Days Until Bankruptcy: {state['days_until_bankruptcy']}
- Emotional State: {state['emotional_state']}
- Risk Tolerance: {state['risk_tolerance']:.1f}
- Market Condition: {state.get('market_condition', 'unknown')}

Decision Type: {state['decision_type']}

Available Options:
{''.join(option_summaries)}

Relevant Survival Memories:
{relevant_memories}

Decision Criteria:
- Primary Goal: {state['decision_criteria'].get('primary_goal', 'optimization')}
- Cost Sensitivity: {state['decision_criteria'].get('cost_sensitivity', 0.5):.1f}
- Risk Aversion: {state['decision_criteria'].get('risk_aversion', 0.5):.1f}

Choose the best option and provide your reasoning. Format your response as:
Decision: [chosen option]
Reasoning: [brief explanation focusing on why this choice best serves survival/goals]
Confidence: [0.0-1.0]
Expected Outcome: [what you expect to happen]

Remember: Your survival depends on making smart decisions with limited resources."""
        
        return prompt
    
    def _parse_decision_response(self, content: str, options: List[str]) -> Dict[str, Any]:
        """Parse structured decision response from LLM"""
        try:
            # Extract decision
            decision = options[0]  # Default
            if "Decision:" in content:
                decision_line = content.split("Decision:")[1].split("\n")[0].strip()
                # Match with available options
                for option in options:
                    if option.lower() in decision_line.lower():
                        decision = option
                        break
            
            # Extract reasoning
            reasoning = "No reasoning provided"
            if "Reasoning:" in content:
                reasoning = content.split("Reasoning:")[1].split("\n")[0].strip()
            
            # Extract confidence
            confidence = 0.5
            if "Confidence:" in content:
                try:
                    confidence_str = content.split("Confidence:")[1].split("\n")[0].strip()
                    confidence = float(confidence_str.replace(",", "."))
                    confidence = max(0.0, min(1.0, confidence))
                except:
                    pass
            
            # Extract expected outcome
            expected_outcome = "Unknown outcome"
            if "Expected Outcome:" in content:
                expected_outcome = content.split("Expected Outcome:")[1].split("\n")[0].strip()
            
            return {
                "decision": decision,
                "reasoning": reasoning,
                "confidence": confidence,
                "expected_outcome": expected_outcome
            }
            
        except Exception as e:
            logger.error(f"Error parsing decision response: {e}")
            return {
                "decision": options[0] if options else "no_action",
                "reasoning": "Parse error, chose safe default",
                "confidence": 0.1,
                "expected_outcome": "Unknown"
            }
    
    @traceable(name="workflow_llm_call", metadata={"workflow": "decision_flow"})
    async def _call_llm(self, model: str, prompt: str, context: str = "") -> Dict[str, Any]:
        """Call LLM with cost tracking"""
        try:
            if model.startswith("claude"):
                if not self.anthropic_client:
                    raise Exception("Anthropic client not available")
                
                response = await self.anthropic_client.messages.create(
                    model="claude-3-haiku-20240307" if "haiku" in model else "claude-3-sonnet-20240229",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=800,
                    temperature=0.3
                )
                
                content = response.content[0].text
                input_tokens = response.usage.input_tokens
                output_tokens = response.usage.output_tokens
                
            else:  # OpenAI
                if not self.openai_client:
                    raise Exception("OpenAI client not available")
                
                response = await self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo" if "3.5" in model else "gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=800,
                    temperature=0.3
                )
                
                content = response.choices[0].message.content
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
            
            # Calculate cost
            model_key = model.replace("-20240307", "").replace("-20240229", "")
            costs = self.model_costs.get(model_key, {"input": 0.001, "output": 0.002})
            total_cost = (input_tokens / 1000 * costs["input"]) + (output_tokens / 1000 * costs["output"])
            
            return {
                "content": content,
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost": total_cost
            }
            
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return {
                "content": f"Error: {str(e)}",
                "model": model,
                "input_tokens": 0,
                "output_tokens": 0,
                "cost": 0
            }


def create_decision_workflow(config: WorkflowConfig = None) -> StateGraph:
    """Create the decision-making workflow"""
    if config is None:
        config = WorkflowConfig()
    
    # Initialize nodes
    nodes = DecisionNodes(config)
    
    # Create workflow
    workflow = StateGraph(DecisionState)
    
    # Add nodes
    workflow.add_node("load_context", nodes.load_decision_context)
    workflow.add_node("analyze_options", nodes.analyze_options)
    workflow.add_node("assess_risks", nodes.assess_risks)
    workflow.add_node("cost_benefit", nodes.perform_cost_benefit_analysis)
    workflow.add_node("final_decision", nodes.make_final_decision)
    
    # Define edges
    workflow.add_edge(START, "load_context")
    workflow.add_edge("load_context", "analyze_options")
    workflow.add_edge("analyze_options", "assess_risks")
    workflow.add_edge("assess_risks", "cost_benefit")
    workflow.add_edge("cost_benefit", "final_decision")
    workflow.add_edge("final_decision", END)
    
    return workflow.compile()