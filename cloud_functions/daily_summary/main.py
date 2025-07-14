"""
Cloud Function: Daily Summary
Generates daily performance summaries and consolidates learning
Analyzes agent performance and updates strategies
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


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DailySummaryEngine:
    """Generates daily summaries and performance analysis"""
    
    def __init__(self):
        self.firestore_client = firestore.Client()
        self.bigquery_client = bigquery.Client()
        self.dataset_id = os.getenv('BIGQUERY_DATASET', 'athena_defi_agent')
        self.anthropic_client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        
    async def get_daily_analysis_data(self) -> List[Dict[str, Any]]:
        """Get hourly analysis data from the past 24 hours"""
        try:
            # Get data from the last 24 hours
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            collection_ref = self.firestore_client.collection('hourly_analysis')
            query = collection_ref.where('timestamp', '>=', cutoff_time.isoformat()).order_by('timestamp')
            
            docs = query.stream()
            analysis_data = []
            
            for doc in docs:
                data = doc.to_dict()
                analysis_data.append(data)
            
            logger.info(f"Retrieved {len(analysis_data)} hourly analyses from last 24 hours")
            return analysis_data
            
        except Exception as e:
            logger.error(f"Error retrieving daily analysis data: {e}")
            return []
    
    async def get_daily_costs(self) -> Dict[str, Any]:
        """Get cost data from the past 24 hours"""
        try:
            # Get costs from the last 24 hours
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            collection_ref = self.firestore_client.collection('agent_costs')
            query = collection_ref.where('timestamp', '>=', cutoff_time.isoformat())
            
            docs = query.stream()
            costs = []
            
            for doc in docs:
                data = doc.to_dict()
                costs.append(data)
            
            # Calculate totals
            total_cost = sum(cost.get('cost_usd', 0) for cost in costs)
            cost_by_operation = {}
            
            for cost in costs:
                operation = cost.get('operation', 'unknown')
                cost_by_operation[operation] = cost_by_operation.get(operation, 0) + cost.get('cost_usd', 0)
            
            logger.info(f"Retrieved {len(costs)} cost entries. Total: ${total_cost:.4f}")
            
            return {
                'total_cost': total_cost,
                'cost_entries': len(costs),
                'cost_by_operation': cost_by_operation,
                'raw_costs': costs
            }
            
        except Exception as e:
            logger.error(f"Error retrieving daily costs: {e}")
            return {
                'total_cost': 0.0,
                'cost_entries': 0,
                'cost_by_operation': {},
                'raw_costs': []
            }
    
    async def get_agent_treasury_status(self) -> Dict[str, Any]:
        """Get current agent treasury status"""
        try:
            agent_ref = self.firestore_client.collection('agent_status').document('current')
            doc = agent_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            else:
                return {
                    'treasury_balance': 100.0,
                    'emotional_state': 'stable',
                    'days_until_bankruptcy': 30
                }
                
        except Exception as e:
            logger.error(f"Error retrieving treasury status: {e}")
            return {
                'treasury_balance': 100.0,
                'emotional_state': 'stable',
                'days_until_bankruptcy': 30
            }
    
    def analyze_daily_performance(self, analysis_data: List[Dict[str, Any]], cost_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze agent's daily performance"""
        try:
            if not analysis_data:
                return {
                    'total_analyses': 0,
                    'market_conditions': {},
                    'decision_actions': {},
                    'avg_confidence': 0.0,
                    'avg_urgency': 0.0,
                    'performance_score': 0.0
                }
            
            # Count market conditions
            market_conditions = {}
            decision_actions = {}
            confidences = []
            urgencies = []
            
            for analysis in analysis_data:
                # Market conditions
                condition = analysis.get('market_condition', 'unknown')
                market_conditions[condition] = market_conditions.get(condition, 0) + 1
                
                # Decision actions
                action = analysis.get('decision_action', 'unknown')
                decision_actions[action] = decision_actions.get(action, 0) + 1
                
                # Metrics
                if 'confidence' in analysis:
                    confidences.append(analysis['confidence'])
                if 'urgency' in analysis:
                    urgencies.append(analysis['urgency'])
            
            # Calculate averages
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            avg_urgency = sum(urgencies) / len(urgencies) if urgencies else 0.0
            
            # Calculate performance score (simple heuristic)
            performance_score = (avg_confidence * 0.4 + 
                               (10 - avg_urgency) / 10 * 0.3 + 
                               min(len(analysis_data) / 24, 1.0) * 0.3)
            
            return {
                'total_analyses': len(analysis_data),
                'market_conditions': market_conditions,
                'decision_actions': decision_actions,
                'avg_confidence': avg_confidence,
                'avg_urgency': avg_urgency,
                'performance_score': performance_score,
                'cost_efficiency': len(analysis_data) / max(cost_data['total_cost'], 0.01)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing daily performance: {e}")
            return {
                'total_analyses': 0,
                'market_conditions': {},
                'decision_actions': {},
                'avg_confidence': 0.0,
                'avg_urgency': 0.0,
                'performance_score': 0.0
            }
    
    async def generate_learning_insights(self, performance: Dict[str, Any], cost_data: Dict[str, Any], treasury_status: Dict[str, Any]) -> Dict[str, Any]:
        """Generate learning insights using LLM"""
        try:
            context = f"""
            Daily Performance Summary:
            - Total Analyses: {performance['total_analyses']}
            - Average Confidence: {performance['avg_confidence']:.2f}
            - Average Urgency: {performance['avg_urgency']:.2f}
            - Performance Score: {performance['performance_score']:.2f}
            - Market Conditions: {performance['market_conditions']}
            - Decision Actions: {performance['decision_actions']}
            
            Cost Analysis:
            - Total Daily Cost: ${cost_data['total_cost']:.4f}
            - Cost Entries: {cost_data['cost_entries']}
            - Cost by Operation: {cost_data['cost_by_operation']}
            
            Treasury Status:
            - Balance: ${treasury_status['treasury_balance']:.2f}
            - Emotional State: {treasury_status['emotional_state']}
            - Days Until Bankruptcy: {treasury_status['days_until_bankruptcy']}
            
            As an autonomous DeFi agent, analyze this daily performance and provide insights.
            What patterns do you notice? What should be optimized tomorrow?
            
            Respond with a JSON object containing:
            - key_insights: list of 3-5 key observations
            - optimization_suggestions: list of 3-5 specific improvements
            - risk_assessment: current risk level (low/medium/high)
            - survival_status: assessment of survival pressure
            - learning_priorities: what to focus on learning next
            """
            
            # Use sonnet for deeper analysis
            response = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=800,
                temperature=0.4,
                messages=[{
                    "role": "user",
                    "content": context
                }]
            )
            
            # Parse LLM response
            try:
                insights_text = response.content[0].text
                
                # Extract JSON from response
                start_idx = insights_text.find('{')
                end_idx = insights_text.rfind('}') + 1
                
                if start_idx >= 0 and end_idx > start_idx:
                    insights_json = json.loads(insights_text[start_idx:end_idx])
                else:
                    # Fallback if JSON parsing fails
                    insights_json = {
                        'key_insights': ['Performance data collected successfully'],
                        'optimization_suggestions': ['Continue monitoring market conditions'],
                        'risk_assessment': 'medium',
                        'survival_status': 'stable',
                        'learning_priorities': ['Market pattern recognition']
                    }
                
                return insights_json
                
            except json.JSONDecodeError:
                logger.warning("Failed to parse LLM insights as JSON")
                return {
                    'key_insights': ['Daily analysis completed'],
                    'optimization_suggestions': ['Review cost optimization'],
                    'risk_assessment': 'medium',
                    'survival_status': 'monitoring',
                    'learning_priorities': ['Pattern recognition improvement']
                }
            
        except Exception as e:
            logger.error(f"Error generating learning insights: {e}")
            return {
                'key_insights': [f'Analysis error: {str(e)}'],
                'optimization_suggestions': ['Review system performance'],
                'risk_assessment': 'high',
                'survival_status': 'needs_attention',
                'learning_priorities': ['Error recovery']
            }
    
    def store_daily_summary(self, performance: Dict[str, Any], cost_data: Dict[str, Any], 
                           treasury_status: Dict[str, Any], insights: Dict[str, Any]) -> None:
        """Store daily summary in databases"""
        try:
            summary_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'date': datetime.utcnow().strftime('%Y-%m-%d'),
                'summary_id': f"daily_{datetime.utcnow().strftime('%Y%m%d')}",
                'performance': performance,
                'costs': cost_data,
                'treasury_status': treasury_status,
                'insights': insights
            }
            
            # Store in Firestore
            summary_ref = self.firestore_client.collection('daily_summaries')
            summary_ref.document(summary_data['date']).set(summary_data)
            
            # Also update latest summary
            latest_ref = summary_ref.document('latest')
            latest_ref.set(summary_data)
            
            # Store in BigQuery (flattened)
            bq_data = {
                'timestamp': summary_data['timestamp'],
                'date': summary_data['date'],
                'total_analyses': performance['total_analyses'],
                'avg_confidence': performance['avg_confidence'],
                'avg_urgency': performance['avg_urgency'],
                'performance_score': performance['performance_score'],
                'total_cost': cost_data['total_cost'],
                'cost_entries': cost_data['cost_entries'],
                'treasury_balance': treasury_status['treasury_balance'],
                'emotional_state': treasury_status['emotional_state'],
                'days_until_bankruptcy': treasury_status['days_until_bankruptcy'],
                'risk_assessment': insights.get('risk_assessment', 'unknown'),
                'survival_status': insights.get('survival_status', 'unknown'),
                'raw_summary': json.dumps(summary_data)
            }
            
            table_id = f"{self.bigquery_client.project}.{self.dataset_id}.daily_summaries"
            errors = self.bigquery_client.insert_rows_json(table_id, [bq_data])
            
            if errors:
                logger.error(f"BigQuery summary insert errors: {errors}")
            else:
                logger.info(f"Stored daily summary: {summary_data['date']}")
                
        except Exception as e:
            logger.error(f"Error storing daily summary: {e}")
    
    def update_agent_costs(self, cost_amount: float) -> None:
        """Update agent cost tracking for summary generation"""
        try:
            cost_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'operation': 'daily_summary',
                'cost_usd': cost_amount,
                'cost_type': 'llm_analysis'
            }
            
            # Store in Firestore
            costs_ref = self.firestore_client.collection('agent_costs')
            costs_ref.add(cost_data)
            
            logger.info(f"Recorded daily summary cost: ${cost_amount:.4f}")
                
        except Exception as e:
            logger.error(f"Error updating summary costs: {e}")


@functions_framework.http
def daily_summary_http(request):
    """HTTP Cloud Function entry point"""
    return asyncio.run(daily_summary_main())


@functions_framework.cloud_event
def daily_summary_scheduler(cloud_event):
    """Cloud Scheduler entry point"""
    return asyncio.run(daily_summary_main())


async def daily_summary_main():
    """Main function for daily summary generation"""
    try:
        logger.info("Starting daily summary generation...")
        
        engine = DailySummaryEngine()
        
        # Get daily data
        analysis_data = await engine.get_daily_analysis_data()
        cost_data = await engine.get_daily_costs()
        treasury_status = await engine.get_agent_treasury_status()
        
        # Analyze performance
        performance = engine.analyze_daily_performance(analysis_data, cost_data)
        
        # Generate insights
        insights = await engine.generate_learning_insights(performance, cost_data, treasury_status)
        
        # Update costs (estimated LLM usage cost for summary)
        summary_cost = 0.15  # Estimated cost for sonnet analysis
        engine.update_agent_costs(summary_cost)
        
        # Store summary
        engine.store_daily_summary(performance, cost_data, treasury_status, insights)
        
        logger.info(f"Daily summary completed. Performance score: {performance['performance_score']:.2f}")
        
        return {
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'date': datetime.utcnow().strftime('%Y-%m-%d'),
            'total_analyses': performance['total_analyses'],
            'performance_score': performance['performance_score'],
            'total_cost': cost_data['total_cost'],
            'risk_assessment': insights.get('risk_assessment', 'unknown'),
            'survival_status': insights.get('survival_status', 'unknown'),
            'summary_cost': summary_cost
        }
        
    except Exception as e:
        logger.error(f"Daily summary failed: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }


if __name__ == "__main__":
    # For local testing
    result = asyncio.run(daily_summary_main())
    print(json.dumps(result, indent=2))