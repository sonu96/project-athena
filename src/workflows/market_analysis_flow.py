"""
Market analysis workflow using LangGraph
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List

from langgraph.graph import StateGraph, START, END
from langsmith import traceable
import httpx
try:
    from anthropic import AsyncAnthropic
except ImportError:
    AsyncAnthropic = None

try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None

from .state import MarketAnalysisState, WorkflowConfig
from ..config.settings import settings
from ..integrations.mem0_integration import Mem0Integration

logger = logging.getLogger(__name__)


class MarketAnalysisNodes:
    """LangGraph nodes for market analysis workflow"""
    
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.anthropic_client = AsyncAnthropic(api_key=settings.anthropic_api_key) if AsyncAnthropic and settings.anthropic_api_key else None
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key) if AsyncOpenAI and settings.openai_api_key else None
        
        # Cost tracking
        self.model_costs = {
            "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
            "claude-3-sonnet": {"input": 0.003, "output": 0.015},
            "gpt-4": {"input": 0.01, "output": 0.03},
            "gpt-3.5": {"input": 0.001, "output": 0.002}
        }
    
    @traceable(name="collect_market_data")
    async def collect_market_data(self, state: MarketAnalysisState) -> MarketAnalysisState:
        """Collect real-time market data from multiple sources"""
        try:
            logger.info("🔍 Collecting market data...")
            
            # Collect from multiple sources
            market_data = {}
            data_quality_scores = {}
            
            # CoinGecko API (free tier)
            try:
                async with httpx.AsyncClient() as client:
                    # Get major cryptocurrency prices
                    crypto_response = await client.get(
                        "https://api.coingecko.com/api/v3/simple/price",
                        params={
                            "ids": "bitcoin,ethereum",
                            "vs_currencies": "usd",
                            "include_24hr_change": "true",
                            "include_market_cap": "true"
                        }
                    )
                    
                    if crypto_response.status_code == 200:
                        crypto_data = crypto_response.json()
                        market_data.update({
                            "btc_price": crypto_data.get("bitcoin", {}).get("usd", 0),
                            "eth_price": crypto_data.get("ethereum", {}).get("usd", 0),
                            "btc_24h_change": crypto_data.get("bitcoin", {}).get("usd_24h_change", 0),
                            "eth_24h_change": crypto_data.get("ethereum", {}).get("usd_24h_change", 0),
                            "btc_market_cap": crypto_data.get("bitcoin", {}).get("usd_market_cap", 0),
                            "eth_market_cap": crypto_data.get("ethereum", {}).get("usd_market_cap", 0)
                        })
                        data_quality_scores["coingecko"] = 1.0
                    else:
                        data_quality_scores["coingecko"] = 0.0
                        
            except Exception as e:
                logger.warning(f"Failed to collect CoinGecko data: {e}")
                data_quality_scores["coingecko"] = 0.0
            
            # Fear & Greed Index
            try:
                async with httpx.AsyncClient() as client:
                    fear_greed_response = await client.get(
                        "https://api.alternative.me/fng/?limit=1"
                    )
                    
                    if fear_greed_response.status_code == 200:
                        fear_greed_data = fear_greed_response.json()
                        if fear_greed_data.get("data"):
                            market_data["fear_greed_index"] = int(fear_greed_data["data"][0]["value"])
                            market_data["fear_greed_classification"] = fear_greed_data["data"][0]["value_classification"]
                            data_quality_scores["fear_greed"] = 1.0
                        else:
                            data_quality_scores["fear_greed"] = 0.0
                    else:
                        data_quality_scores["fear_greed"] = 0.0
                        
            except Exception as e:
                logger.warning(f"Failed to collect Fear & Greed data: {e}")
                data_quality_scores["fear_greed"] = 0.0
            
            # Add simulated data for missing pieces (Phase 1 focus)
            if not market_data.get("btc_price"):
                market_data.update({
                    "btc_price": 45000,  # Fallback values
                    "eth_price": 2800,
                    "btc_24h_change": 2.5,
                    "eth_24h_change": 1.8
                })
                data_quality_scores["fallback"] = 0.5
            
            # Add DeFi-specific data (simulated for Phase 1)
            market_data.update({
                "defi_tvl": 50_000_000_000,  # $50B simulated
                "gas_price_gwei": 25,
                "base_network_tvl": 2_000_000_000,  # $2B simulated
                "data_timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            # Calculate overall data quality
            overall_quality = sum(data_quality_scores.values()) / len(data_quality_scores) if data_quality_scores else 0.5
            
            # Update state
            state["market_data"] = market_data
            state["data_sources"] = list(data_quality_scores.keys())
            state["data_quality_scores"] = data_quality_scores
            
            # Track cost
            cost = {"amount": 0.0, "type": "market_data", "description": "Market data collection"}
            state["costs_incurred"].append(cost)
            
            logger.info(f"✅ Market data collected from {len(data_quality_scores)} sources (quality: {overall_quality:.2f})")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Error collecting market data: {e}")
            state["errors"].append(f"Market data collection failed: {str(e)}")
            return state
    
    @traceable(name="analyze_sentiment")
    async def analyze_sentiment(self, state: MarketAnalysisState) -> MarketAnalysisState:
        """Analyze market sentiment using LLM"""
        try:
            logger.info("🧠 Analyzing market sentiment...")
            
            # Select model based on treasury state
            model = self._select_model_for_task(state["emotional_state"], "sentiment_analysis")
            
            # Prepare market data summary
            market_data = state["market_data"]
            prompt = f"""Analyze the current cryptocurrency market sentiment based on the following data:

Market Metrics:
- BTC: ${market_data.get('btc_price', 0):,.0f} ({market_data.get('btc_24h_change', 0):+.1f}% 24h)
- ETH: ${market_data.get('eth_price', 0):,.0f} ({market_data.get('eth_24h_change', 0):+.1f}% 24h)
- Fear & Greed Index: {market_data.get('fear_greed_index', 50)} ({market_data.get('fear_greed_classification', 'Neutral')})
- DeFi TVL: ${market_data.get('defi_tvl', 0)/1e9:.1f}B
- Gas Price: {market_data.get('gas_price_gwei', 0)} gwei

Treasury Context:
- Agent Balance: ${state['treasury_balance']:.2f}
- Emotional State: {state['emotional_state']}
- Risk Tolerance: {state['risk_tolerance']:.1f}

Provide a concise sentiment analysis with:
1. Overall market sentiment (bullish/bearish/neutral/volatile)
2. Key driving factors
3. Risk level for DeFi operations
4. Recommended observation frequency

Keep response under 200 words and focus on actionable insights."""

            # Generate response
            response = await self._call_llm(model, prompt, state["emotional_state"])
            
            # Parse sentiment analysis
            content = response["content"]
            sentiment_analysis = {
                "analysis": content,
                "model_used": response["model"],
                "confidence": 0.7,  # Default, could be extracted from response
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Update state
            state["sentiment_analysis"] = sentiment_analysis
            state["llm_responses"]["sentiment"] = response
            state["costs_incurred"].append({
                "amount": response["cost"],
                "type": "llm_sentiment",
                "description": f"Sentiment analysis with {response['model']}"
            })
            
            logger.info(f"✅ Sentiment analysis completed using {response['model']} (${response['cost']:.4f})")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Error in sentiment analysis: {e}")
            state["errors"].append(f"Sentiment analysis failed: {str(e)}")
            return state
    
    @traceable(name="classify_market_condition")
    async def classify_market_condition(self, state: MarketAnalysisState) -> MarketAnalysisState:
        """Classify overall market condition"""
        try:
            logger.info("📊 Classifying market condition...")
            
            market_data = state["market_data"]
            
            # Rule-based classification with LLM enhancement
            btc_change = market_data.get("btc_24h_change", 0)
            eth_change = market_data.get("eth_24h_change", 0)
            fear_greed = market_data.get("fear_greed_index", 50)
            
            # Initial classification
            if btc_change > 5 and eth_change > 5:
                condition = "strong_bull"
                confidence = 0.8
            elif btc_change > 2 and eth_change > 2:
                condition = "bull"
                confidence = 0.7
            elif btc_change < -5 and eth_change < -5:
                condition = "strong_bear"
                confidence = 0.8
            elif btc_change < -2 and eth_change < -2:
                condition = "bear"
                confidence = 0.7
            elif abs(btc_change) > 3 or abs(eth_change) > 3:
                condition = "volatile"
                confidence = 0.6
            else:
                condition = "neutral"
                confidence = 0.5
            
            # Adjust based on Fear & Greed
            if fear_greed < 25 and condition in ["bull", "strong_bull"]:
                condition = "volatile"  # Fear despite positive moves
                confidence *= 0.8
            elif fear_greed > 75 and condition in ["bear", "strong_bear"]:
                condition = "volatile"  # Greed despite negative moves
                confidence *= 0.8
            
            # Supporting factors
            supporting_factors = []
            if abs(btc_change) > 3:
                supporting_factors.append(f"BTC significant move: {btc_change:+.1f}%")
            if abs(eth_change) > 3:
                supporting_factors.append(f"ETH significant move: {eth_change:+.1f}%")
            if fear_greed < 30:
                supporting_factors.append(f"High fear level: {fear_greed}")
            elif fear_greed > 70:
                supporting_factors.append(f"High greed level: {fear_greed}")
            
            # Risk assessment
            if condition in ["strong_bear", "volatile"]:
                risk_assessment = "high"
            elif condition in ["bear", "strong_bull"]:
                risk_assessment = "medium"
            else:
                risk_assessment = "low"
            
            # Recommended actions based on emotional state
            recommended_actions = []
            if state["emotional_state"] == "desperate":
                recommended_actions = ["minimize_operations", "capital_preservation", "emergency_mode"]
            elif state["emotional_state"] == "cautious":
                if condition in ["bull", "neutral"]:
                    recommended_actions = ["conservative_monitoring", "low_risk_opportunities"]
                else:
                    recommended_actions = ["reduce_activity", "preserve_capital"]
            else:
                if condition == "bull":
                    recommended_actions = ["active_monitoring", "moderate_opportunities"]
                elif condition == "bear":
                    recommended_actions = ["defensive_positioning", "wait_for_recovery"]
                else:
                    recommended_actions = ["normal_operations", "balanced_approach"]
            
            # Update state
            state["condition_classification"] = condition
            state["confidence_score"] = confidence
            state["supporting_factors"] = supporting_factors
            state["risk_assessment"] = risk_assessment
            state["recommended_actions"] = recommended_actions
            state["market_condition"] = condition
            state["market_confidence"] = confidence
            
            logger.info(f"✅ Market classified as {condition} (confidence: {confidence:.2f}, risk: {risk_assessment})")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Error classifying market condition: {e}")
            state["errors"].append(f"Market classification failed: {str(e)}")
            return state
    
    @traceable(name="query_relevant_memories")
    async def query_relevant_memories(self, state: MarketAnalysisState) -> MarketAnalysisState:
        """Query relevant memories for context"""
        try:
            logger.info("🧠 Querying relevant memories...")
            
            # This would integrate with the memory system
            # For now, return simulated relevant memories
            relevant_memories = [
                {
                    "content": f"Previous {state.get('condition_classification', 'unknown')} market conditions led to successful conservative strategies",
                    "importance": 0.7,
                    "category": "market_patterns"
                },
                {
                    "content": f"When emotional state is {state['emotional_state']}, focus on capital preservation",
                    "importance": 0.9,
                    "category": "survival_critical"
                }
            ]
            
            state["relevant_memories"] = relevant_memories
            
            # Track minimal cost for memory query
            state["costs_incurred"].append({
                "amount": 0.001,
                "type": "memory_query",
                "description": "Relevant memory retrieval"
            })
            
            logger.info(f"✅ Retrieved {len(relevant_memories)} relevant memories")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Error querying memories: {e}")
            state["errors"].append(f"Memory query failed: {str(e)}")
            return state
    
    def _select_model_for_task(self, emotional_state: str, task_type: str) -> str:
        """Select appropriate model based on context"""
        if emotional_state == "desperate":
            return "claude-3-haiku"  # Cheapest option
        elif task_type in ["critical_analysis", "complex_decision"]:
            return "claude-3-sonnet"  # Better quality
        else:
            return "claude-3-haiku"  # Default economical choice
    
    async def _call_llm(self, model: str, prompt: str, context: str = "") -> Dict[str, Any]:
        """Call LLM with cost tracking"""
        try:
            if model.startswith("claude"):
                if not self.anthropic_client:
                    raise Exception("Anthropic client not available")
                
                response = await self.anthropic_client.messages.create(
                    model="claude-3-haiku-20240307" if "haiku" in model else "claude-3-sonnet-20240229",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1000,
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
                    max_tokens=1000,
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


def create_market_analysis_workflow(config: WorkflowConfig = None) -> StateGraph:
    """Create the market analysis workflow"""
    if config is None:
        config = WorkflowConfig()
    
    # Initialize nodes
    nodes = MarketAnalysisNodes(config)
    
    # Create workflow
    workflow = StateGraph(MarketAnalysisState)
    
    # Add nodes
    workflow.add_node("collect_data", nodes.collect_market_data)
    workflow.add_node("analyze_sentiment", nodes.analyze_sentiment)
    workflow.add_node("classify_condition", nodes.classify_market_condition)
    workflow.add_node("query_memories", nodes.query_relevant_memories)
    
    # Define edges
    workflow.add_edge(START, "collect_data")
    workflow.add_edge("collect_data", "analyze_sentiment")
    workflow.add_edge("analyze_sentiment", "classify_condition")
    workflow.add_edge("classify_condition", "query_memories")
    workflow.add_edge("query_memories", END)
    
    return workflow.compile()