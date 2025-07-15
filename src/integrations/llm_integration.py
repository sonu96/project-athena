"""
LLM integration for AI decision making with cost tracking
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Literal
import logging
import json
from langsmith import traceable

from ..config.settings import settings
from .llm_factory import llm_factory, get_llm_response

logger = logging.getLogger(__name__)


class LLMIntegration:
    """Manages LLM interactions with cost tracking"""
    
    def __init__(self):
        # Initialize clients
        self.anthropic_client = None
        self.openai_client = None
        
        try:
            if settings.anthropic_api_key:
                from anthropic import AsyncAnthropic
                self.anthropic_client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        except ImportError:
            logger.warning("Anthropic SDK not available")
        
        try:
            if settings.openai_api_key:
                from openai import AsyncOpenAI
                self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        except ImportError:
            logger.warning("OpenAI SDK not available")
        
        # Model configurations with cost per token
        self.models = {
            "claude-3-sonnet": {
                "provider": "anthropic",
                "model_id": "claude-3-sonnet-20240229",
                "input_cost_per_1k": 0.003,
                "output_cost_per_1k": 0.015,
                "max_tokens": 4096
            },
            "claude-3-haiku": {
                "provider": "anthropic", 
                "model_id": "claude-3-haiku-20240307",
                "input_cost_per_1k": 0.00025,
                "output_cost_per_1k": 0.00125,
                "max_tokens": 4096
            },
            "gpt-4": {
                "provider": "openai",
                "model_id": "gpt-4-1106-preview",
                "input_cost_per_1k": 0.01,
                "output_cost_per_1k": 0.03,
                "max_tokens": 4096
            },
            "gpt-3.5": {
                "provider": "openai",
                "model_id": "gpt-3.5-turbo-1106",
                "input_cost_per_1k": 0.001,
                "output_cost_per_1k": 0.002,
                "max_tokens": 4096
            }
        }
        
        # Default models for different tasks (cost optimization)
        self.task_models = {
            "critical_decision": "claude-3-sonnet",
            "market_analysis": "claude-3-haiku",
            "routine_check": "gpt-3.5",
            "complex_reasoning": "gpt-4"
        }
    
    @traceable(name="llm_generate_response", metadata={"integration": "llm"})
    async def generate_response(
        self,
        prompt: str,
        task_type: str = "routine_check",
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate LLM response with automatic model selection and cost tracking"""
        try:
            # Select model based on task type
            model_key = self.task_models.get(task_type, "gpt-3.5")
            model_config = self.models[model_key]
            
            # Set max tokens if not specified
            if max_tokens is None:
                max_tokens = min(1000, model_config["max_tokens"])
            
            # Generate response based on provider
            if model_config["provider"] == "anthropic":
                response = await self._generate_anthropic_response(
                    prompt, system_prompt, model_config, temperature, max_tokens
                )
            else:
                response = await self._generate_openai_response(
                    prompt, system_prompt, model_config, temperature, max_tokens
                )
            
            # Calculate costs
            input_tokens = response.get("input_tokens", 0)
            output_tokens = response.get("output_tokens", 0)
            
            input_cost = (input_tokens / 1000) * model_config["input_cost_per_1k"]
            output_cost = (output_tokens / 1000) * model_config["output_cost_per_1k"]
            total_cost = input_cost + output_cost
            
            return {
                "content": response.get("content", ""),
                "model": model_key,
                "provider": model_config["provider"],
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "cost_usd": round(total_cost, 6),
                "cost_breakdown": {
                    "input_cost": round(input_cost, 6),
                    "output_cost": round(output_cost, 6)
                },
                "task_type": task_type,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating LLM response: {e}")
            return {
                "content": "",
                "error": str(e),
                "cost_usd": 0,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    @traceable(name="anthropic_llm_call", metadata={"provider": "anthropic"})
    async def _generate_anthropic_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str],
        model_config: Dict,
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """Generate response using Anthropic Claude"""
        if not self.anthropic_client:
            raise Exception("Anthropic client not initialized")
        
        messages = [{"role": "user", "content": prompt}]
        
        response = await self.anthropic_client.messages.create(
            model=model_config["model_id"],
            messages=messages,
            system=system_prompt or "You are Athena, an autonomous DeFi agent with survival instincts.",
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return {
            "content": response.content[0].text,
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens
        }
    
    @traceable(name="openai_llm_call", metadata={"provider": "openai"})
    async def _generate_openai_response(
        self,
        prompt: str,
        system_prompt: Optional[str],
        model_config: Dict,
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """Generate response using OpenAI GPT"""
        if not self.openai_client:
            raise Exception("OpenAI client not initialized")
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = await self.openai_client.chat.completions.create(
            model=model_config["model_id"],
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return {
            "content": response.choices[0].message.content,
            "input_tokens": response.usage.prompt_tokens,
            "output_tokens": response.usage.completion_tokens
        }
    
    async def analyze_market_conditions(
        self, 
        market_data: Dict[str, Any], 
        treasury_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze market conditions with context-aware model selection"""
        try:
            # Use cheaper model for routine analysis, expensive for critical situations
            if treasury_state.get("emotional_state") == "desperate":
                task_type = "critical_decision"
            else:
                task_type = "market_analysis"
            
            prompt = f"""Analyze the current market conditions and provide insights.

Market Data:
- BTC Price: ${market_data.get('btc_price', 0):,.0f} ({market_data.get('btc_24h_change', 0):+.1f}%)
- ETH Price: ${market_data.get('eth_price', 0):,.0f} ({market_data.get('eth_24h_change', 0):+.1f}%)
- DeFi TVL: ${market_data.get('defi_tvl', 0)/1e9:.1f}B
- Fear & Greed Index: {market_data.get('fear_greed_index', 50)}
- Gas Price: {market_data.get('gas_price_gwei', 0)} gwei

Treasury State:
- Balance: ${treasury_state.get('balance', 0):.2f}
- Emotional State: {treasury_state.get('emotional_state', 'unknown')}
- Days Until Bankruptcy: {treasury_state.get('days_remaining', 999)}

Provide:
1. Market condition classification (bull/bear/volatile/neutral)
2. Risk assessment (high/medium/low)
3. Recommended observation frequency
4. Key opportunities or threats

Be concise and focus on actionable insights."""

            system_prompt = """You are Athena, a DeFi agent with survival instincts. 
Your treasury is limited and you must be cost-conscious. 
Provide practical, actionable analysis focused on capital preservation and sustainable growth."""

            response = await self.generate_response(
                prompt=prompt,
                task_type=task_type,
                system_prompt=system_prompt,
                temperature=0.3,  # Lower temperature for more consistent analysis
                max_tokens=500
            )
            
            return {
                "analysis": response["content"],
                "cost": response["cost_usd"],
                "model_used": response["model"],
                "tokens_used": response["total_tokens"]
            }
            
        except Exception as e:
            logger.error(f"❌ Error analyzing market conditions: {e}")
            return {
                "analysis": "Error in market analysis",
                "cost": 0,
                "error": str(e)
            }
    
    async def make_decision(
        self,
        context: Dict[str, Any],
        options: List[str],
        memory_context: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Make a decision based on context and memories"""
        try:
            # Determine task criticality
            treasury_balance = context.get("treasury", {}).get("balance", 100)
            if treasury_balance < 30:
                task_type = "critical_decision"
            elif any("high_risk" in opt.lower() for opt in options):
                task_type = "complex_reasoning"
            else:
                task_type = "routine_check"
            
            # Format memories for context
            memory_summary = "\n".join([
                f"- {mem['content']} (importance: {mem['metadata'].get('importance', 0)})"
                for mem in memory_context[:5]  # Limit to top 5 memories
            ])
            
            prompt = f"""Make a decision based on the current context and past experiences.

Current Context:
{json.dumps(context, indent=2)}

Available Options:
{json.dumps(options, indent=2)}

Relevant Memories:
{memory_summary}

Choose the best option and explain your reasoning. Consider:
1. Current treasury state and survival needs
2. Risk vs. reward given the emotional state
3. Lessons learned from past experiences
4. Long-term sustainability

Response format:
Decision: [chosen option]
Reasoning: [brief explanation]
Confidence: [0.0-1.0]
Risk Assessment: [low/medium/high]"""

            response = await self.generate_response(
                prompt=prompt,
                task_type=task_type,
                temperature=0.5,
                max_tokens=300
            )
            
            # Parse response
            content = response["content"]
            decision_data = self._parse_decision_response(content, options)
            
            return {
                "decision": decision_data["decision"],
                "reasoning": decision_data["reasoning"],
                "confidence": decision_data["confidence"],
                "risk_assessment": decision_data["risk_assessment"],
                "cost": response["cost_usd"],
                "model_used": response["model"]
            }
            
        except Exception as e:
            logger.error(f"❌ Error making decision: {e}")
            return {
                "decision": options[0] if options else "no_action",
                "reasoning": "Error in decision making, choosing safe default",
                "confidence": 0.1,
                "risk_assessment": "high",
                "cost": 0,
                "error": str(e)
            }
    
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
            
            # Extract risk assessment  
            risk_assessment = "medium"
            if "Risk Assessment:" in content:
                risk_line = content.split("Risk Assessment:")[1].split("\n")[0].strip().lower()
                if "high" in risk_line:
                    risk_assessment = "high"
                elif "low" in risk_line:
                    risk_assessment = "low"
            
            return {
                "decision": decision,
                "reasoning": reasoning,
                "confidence": confidence,
                "risk_assessment": risk_assessment
            }
            
        except Exception as e:
            logger.error(f"Error parsing decision response: {e}")
            return {
                "decision": options[0] if options else "no_action",
                "reasoning": "Parse error",
                "confidence": 0.1,
                "risk_assessment": "high"
            }
    
    async def estimate_monthly_llm_costs(self, daily_operations: int = 24) -> Dict[str, float]:
        """Estimate monthly LLM costs based on usage patterns"""
        try:
            # Estimate token usage per operation type
            estimates = {
                "market_analysis": {
                    "frequency_per_day": daily_operations,
                    "avg_tokens": 800,
                    "model": self.task_models["market_analysis"]
                },
                "decisions": {
                    "frequency_per_day": daily_operations / 2,
                    "avg_tokens": 600,
                    "model": self.task_models["routine_check"]
                },
                "critical_decisions": {
                    "frequency_per_day": 1,  # Once per day average
                    "avg_tokens": 1000,
                    "model": self.task_models["critical_decision"]
                }
            }
            
            monthly_cost = 0
            breakdown = {}
            
            for operation, config in estimates.items():
                model_config = self.models[config["model"]]
                daily_tokens = config["frequency_per_day"] * config["avg_tokens"]
                monthly_tokens = daily_tokens * 30
                
                # Assume 60/40 input/output split
                input_tokens = monthly_tokens * 0.6
                output_tokens = monthly_tokens * 0.4
                
                cost = ((input_tokens / 1000) * model_config["input_cost_per_1k"] +
                       (output_tokens / 1000) * model_config["output_cost_per_1k"])
                
                breakdown[operation] = round(cost, 2)
                monthly_cost += cost
            
            return {
                "total_monthly_cost": round(monthly_cost, 2),
                "daily_average": round(monthly_cost / 30, 2),
                "breakdown": breakdown,
                "assumptions": {
                    "operations_per_day": daily_operations,
                    "days_per_month": 30
                }
            }
            
        except Exception as e:
            logger.error(f"Error estimating LLM costs: {e}")
            return {"total_monthly_cost": 0, "error": str(e)}