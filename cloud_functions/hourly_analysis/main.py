"""
Cloud Function: Hourly Analysis
Performs hourly market analysis using LangGraph workflows
Analyzes market conditions and triggers agent decision-making
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List

import functions_framework
from google.cloud import firestore, bigquery
from anthropic import Anthropic
import aiohttp


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HourlyAnalysisEngine:
    """Performs hourly market analysis and agent operations"""
    
    def __init__(self):
        self.firestore_client = firestore.Client()
        self.bigquery_client = bigquery.Client()
        self.dataset_id = os.getenv('BIGQUERY_DATASET', 'athena_defi_agent')
        self.anthropic_client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        
    async def get_recent_market_data(self, hours: int = 1) -> List[Dict[str, Any]]:
        """Get recent market data from Firestore"""
        try:
            # Get data from the last hour
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            collection_ref = self.firestore_client.collection('market_data')
            query = collection_ref.where('timestamp', '>=', cutoff_time.isoformat()).order_by('timestamp', direction=firestore.Query.DESCENDING).limit(20)
            
            docs = query.stream()
            market_data = []
            
            for doc in docs:
                data = doc.to_dict()
                market_data.append(data)
            
            logger.info(f"Retrieved {len(market_data)} market data points from last {hours} hours")
            return market_data
            
        except Exception as e:
            logger.error(f"Error retrieving market data: {e}")
            return []
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status from Firestore"""
        try:
            agent_ref = self.firestore_client.collection('agent_status').document('current')
            doc = agent_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            else:
                # Return default status if not found
                return {
                    'treasury_balance': 100.0,
                    'emotional_state': 'stable',
                    'days_until_bankruptcy': 30,
                    'last_update': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error retrieving agent status: {e}")
            return {
                'treasury_balance': 100.0,
                'emotional_state': 'stable',
                'days_until_bankruptcy': 30,
                'last_update': datetime.utcnow().isoformat()
            }
    
    def analyze_market_conditions(self, market_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze current market conditions"""
        try:
            if not market_data:
                return {
                    'condition': 'neutral',
                    'confidence': 0.0,
                    'reasoning': 'No market data available',
                    'volatility': 0.0
                }
            
            latest_data = market_data[0]
            
            # Extract price data
            bitcoin_change = 0
            ethereum_change = 0
            fear_greed_index = 50
            
            sources = latest_data.get('sources', {})
            
            if 'coingecko' in sources and sources['coingecko'].get('status') == 'success':
                coingecko_data = sources['coingecko']
                bitcoin_change = coingecko_data.get('bitcoin_24h_change', 0)
                ethereum_change = coingecko_data.get('ethereum_24h_change', 0)
            
            if 'fear_greed' in sources and sources['fear_greed'].get('status') == 'success':
                fear_greed_data = sources['fear_greed']
                fear_greed_index = fear_greed_data.get('fear_greed_index', 50)
            
            # Calculate average price change
            avg_change = (bitcoin_change + ethereum_change) / 2
            
            # Determine market condition
            condition = 'neutral'
            confidence = 0.6
            
            if avg_change > 5 and fear_greed_index > 70:
                condition = 'strong_bull'
                confidence = 0.9
            elif avg_change > 2:
                condition = 'bull'
                confidence = 0.8
            elif avg_change < -5 and fear_greed_index < 30:
                condition = 'strong_bear'
                confidence = 0.9
            elif avg_change < -2:
                condition = 'bear'
                confidence = 0.8
            elif abs(avg_change) > 3:
                condition = 'volatile'
                confidence = 0.7
            
            # Calculate volatility
            volatility = abs(avg_change) / 10  # Normalize to 0-1 scale
            
            return {
                'condition': condition,
                'confidence': confidence,
                'reasoning': f"Avg change: {avg_change:.2f}%, Fear/Greed: {fear_greed_index}",
                'volatility': min(volatility, 1.0),
                'bitcoin_change': bitcoin_change,
                'ethereum_change': ethereum_change,
                'fear_greed_index': fear_greed_index
            }
            
        except Exception as e:
            logger.error(f"Error analyzing market conditions: {e}")
            return {
                'condition': 'neutral',
                'confidence': 0.0,
                'reasoning': f'Analysis error: {str(e)}',
                'volatility': 0.5
            }
    
    async def make_agent_decision(self, market_analysis: Dict[str, Any], agent_status: Dict[str, Any]) -> Dict[str, Any]:
        """Make agent decision using LLM"""
        try:
            # Create decision context
            context = f"""
            Current Market Analysis:
            - Condition: {market_analysis['condition']}
            - Confidence: {market_analysis['confidence']:.2f}
            - Reasoning: {market_analysis['reasoning']}
            - Volatility: {market_analysis['volatility']:.2f}
            
            Agent Status:
            - Treasury Balance: ${agent_status['treasury_balance']:.2f}
            - Emotional State: {agent_status['emotional_state']}
            - Days Until Bankruptcy: {agent_status['days_until_bankruptcy']}
            
            As an autonomous DeFi agent with survival pressure, what should be my next action?
            Consider my emotional state and market conditions.
            
            Respond with a JSON object containing:
            - action: "observe", "analyze", "prepare", or "emergency"
            - reasoning: explanation of the decision
            - urgency: 1-10 scale
            - cost_estimate: estimated cost in USD
            """
            
            # Use cheaper model for routine decisions
            model = "claude-3-haiku-20240307" if agent_status['emotional_state'] in ['desperate', 'cautious'] else "claude-3-sonnet-20240229"
            
            response = self.anthropic_client.messages.create(
                model=model,
                max_tokens=500,
                temperature=0.3,
                messages=[{
                    "role": "user",
                    "content": context
                }]
            )
            
            # Parse LLM response
            try:
                decision_text = response.content[0].text
                
                # Extract JSON from response
                start_idx = decision_text.find('{')
                end_idx = decision_text.rfind('}') + 1
                
                if start_idx >= 0 and end_idx > start_idx:
                    decision_json = json.loads(decision_text[start_idx:end_idx])
                else:
                    # Fallback if JSON parsing fails
                    decision_json = {
                        'action': 'observe',
                        'reasoning': 'LLM response parsing failed, defaulting to observation',
                        'urgency': 5,
                        'cost_estimate': 0.05
                    }
                
                return decision_json
                
            except json.JSONDecodeError:
                logger.warning("Failed to parse LLM decision as JSON")
                return {
                    'action': 'observe',
                    'reasoning': 'LLM response not in valid JSON format',
                    'urgency': 5,
                    'cost_estimate': 0.05
                }
            
        except Exception as e:
            logger.error(f"Error making agent decision: {e}")
            return {
                'action': 'emergency',
                'reasoning': f'Decision making error: {str(e)}',
                'urgency': 9,
                'cost_estimate': 0.0
            }
    
    def update_agent_costs(self, cost_amount: float, operation: str) -> None:
        """Update agent cost tracking"""
        try:
            cost_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'operation': operation,
                'cost_usd': cost_amount,
                'cost_type': 'llm_analysis'
            }
            
            # Store in Firestore
            costs_ref = self.firestore_client.collection('agent_costs')
            costs_ref.add(cost_data)
            
            # Store in BigQuery
            table_id = f"{self.bigquery_client.project}.{self.dataset_id}.agent_costs"
            errors = self.bigquery_client.insert_rows_json(table_id, [cost_data])
            
            if errors:
                logger.error(f"BigQuery cost insert errors: {errors}")
            else:
                logger.info(f"Recorded cost: ${cost_amount:.4f} for {operation}")
                
        except Exception as e:
            logger.error(f"Error updating agent costs: {e}")
    
    def store_analysis_results(self, market_analysis: Dict[str, Any], decision: Dict[str, Any]) -> None:
        """Store analysis results in databases"""
        try:
            analysis_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'analysis_id': f"analysis_{int(datetime.utcnow().timestamp())}",
                'market_condition': market_analysis['condition'],
                'confidence': market_analysis['confidence'],
                'volatility': market_analysis['volatility'],
                'decision_action': decision['action'],
                'decision_reasoning': decision['reasoning'],
                'urgency': decision['urgency'],
                'estimated_cost': decision['cost_estimate']
            }
            
            # Store in Firestore
            analysis_ref = self.firestore_client.collection('hourly_analysis')
            analysis_ref.add(analysis_data)
            
            # Store in BigQuery
            table_id = f"{self.bigquery_client.project}.{self.dataset_id}.hourly_analysis"
            errors = self.bigquery_client.insert_rows_json(table_id, [analysis_data])
            
            if errors:
                logger.error(f"BigQuery analysis insert errors: {errors}")
            else:
                logger.info(f"Stored hourly analysis: {analysis_data['analysis_id']}")
                
        except Exception as e:
            logger.error(f"Error storing analysis results: {e}")


@functions_framework.http
def hourly_analysis_http(request):
    """HTTP Cloud Function entry point"""
    return asyncio.run(hourly_analysis_main())


@functions_framework.cloud_event
def hourly_analysis_scheduler(cloud_event):
    """Cloud Scheduler entry point"""
    return asyncio.run(hourly_analysis_main())


async def hourly_analysis_main():
    """Main function for hourly analysis"""
    try:
        logger.info("Starting hourly market analysis...")
        
        engine = HourlyAnalysisEngine()
        
        # Get recent market data and agent status
        market_data = await engine.get_recent_market_data(hours=1)
        agent_status = await engine.get_agent_status()
        
        # Analyze market conditions
        market_analysis = engine.analyze_market_conditions(market_data)
        
        # Make agent decision
        decision = await engine.make_agent_decision(market_analysis, agent_status)
        
        # Update costs (estimated LLM usage cost)
        estimated_cost = decision.get('cost_estimate', 0.05)
        engine.update_agent_costs(estimated_cost, 'hourly_analysis')
        
        # Store results
        engine.store_analysis_results(market_analysis, decision)
        
        logger.info(f"Hourly analysis completed. Market: {market_analysis['condition']}, Decision: {decision['action']}")
        
        return {
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'market_condition': market_analysis['condition'],
            'confidence': market_analysis['confidence'],
            'decision_action': decision['action'],
            'urgency': decision['urgency'],
            'estimated_cost': estimated_cost
        }
        
    except Exception as e:
        logger.error(f"Hourly analysis failed: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }


if __name__ == "__main__":
    # For local testing
    result = asyncio.run(hourly_analysis_main())
    print(json.dumps(result, indent=2))