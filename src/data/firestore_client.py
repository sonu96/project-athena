"""
Firestore client for real-time data storage and retrieval
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from google.cloud import firestore
from google.cloud.firestore_v1 import FieldFilter
import logging

from ..config.gcp_config import gcp_config
from ..config.settings import settings

logger = logging.getLogger(__name__)


class FirestoreClient:
    """Client for interacting with Firestore database"""
    
    def __init__(self):
        self.db = gcp_config.firestore_client
        self.collections = {
            'treasury': 'agent_data_treasury',
            'active_positions': 'agent_data_active_positions',
            'yield_opportunities': 'agent_data_yield_opportunities',
            'bridge_opportunities': 'agent_data_bridge_opportunities',
            'protocols': 'agent_data_protocols',
            'decisions': 'agent_data_decisions',
            'costs': 'agent_data_costs',
            'risk_alerts': 'agent_data_risk_alerts',
            'gas_prices': 'agent_data_gas_prices',
            'system_logs': 'agent_data_system_logs'
        }
    
    async def initialize_database(self) -> bool:
        """Initialize database with default documents"""
        try:
            # Initialize treasury with enhanced DeFi fields
            treasury_doc = {
                'agent_id': settings.agent_id,
                'balance_usd': 100.0,  # Starting seed money
                'balance_btc': 0.0,
                'total_value_locked': 0.0,
                'total_rewards_pending': 0.0,
                'daily_burn_rate': 0.0,
                'days_until_bankruptcy': 999,
                'emotional_state': 'stable',
                'risk_tolerance': 0.5,
                'confidence_level': 0.5,
                'survival_mode_active': False,
                'created_at': firestore.SERVER_TIMESTAMP,
                'last_updated': firestore.SERVER_TIMESTAMP,
                'initialization': True
            }
            
            self.db.collection(self.collections['treasury']).document('current_state').set(treasury_doc)
            
            # Initialize empty positions collection
            self.db.collection(self.collections['active_positions']).document('_init').set({
                'initialization': True,
                'timestamp': firestore.SERVER_TIMESTAMP
            })
            
            # Initialize yield opportunities collection
            self.db.collection(self.collections['yield_opportunities']).document('_init').set({
                'initialization': True,
                'timestamp': firestore.SERVER_TIMESTAMP
            })
            
            # Initialize gas prices tracking
            gas_doc = {
                'base': {'price_gwei': 0.0, 'updated': firestore.SERVER_TIMESTAMP},
                'ethereum': {'price_gwei': 0.0, 'updated': firestore.SERVER_TIMESTAMP},
                'arbitrum': {'price_gwei': 0.0, 'updated': firestore.SERVER_TIMESTAMP},
                'last_updated': firestore.SERVER_TIMESTAMP
            }
            
            self.db.collection(self.collections['gas_prices']).document('current').set(gas_doc)
            
            # Create initial system log
            self.db.collection(self.collections['system_logs']).add({
                'event': 'database_initialized',
                'timestamp': firestore.SERVER_TIMESTAMP,
                'details': {
                    'treasury_balance': 100.0,
                    'collections_created': list(self.collections.keys())
                }
            })
            
            logger.info("✅ Firestore database initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error initializing database: {e}")
            return False
    
    async def update_treasury(self, treasury_data: Dict[str, Any]) -> bool:
        """Update treasury state"""
        try:
            treasury_data['last_updated'] = firestore.SERVER_TIMESTAMP
            
            # Update current state
            self.db.collection(self.collections['treasury']).document('current_state').update(treasury_data)
            
            # Create daily snapshot if needed
            today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            snapshot_data = {
                **treasury_data,
                'snapshot_date': today,
                'snapshot_timestamp': firestore.SERVER_TIMESTAMP
            }
            
            self.db.collection(self.collections['treasury']).document('daily_snapshots').collection('snapshots').document(today).set(snapshot_data, merge=True)
            
            return True
        except Exception as e:
            logger.error(f"❌ Error updating treasury: {e}")
            return False
    
    async def get_current_treasury(self) -> Optional[Dict[str, Any]]:
        """Get current treasury state"""
        try:
            doc = self.db.collection(self.collections['treasury']).document('current_state').get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            logger.error(f"❌ Error getting treasury: {e}")
            return None
    
    async def update_market_condition(self, condition_data: Dict[str, Any]) -> bool:
        """Update market conditions"""
        try:
            condition_data['last_updated'] = firestore.SERVER_TIMESTAMP
            
            # Update current condition
            self.db.collection(self.collections['market_conditions']).document('current').set(condition_data, merge=True)
            
            # Store hourly snapshot
            hour_key = datetime.now(timezone.utc).strftime('%Y-%m-%d-%H')
            self.db.collection(self.collections['market_conditions']).document('hourly_snapshots').collection('snapshots').document(hour_key).set(condition_data, merge=True)
            
            return True
        except Exception as e:
            logger.error(f"❌ Error updating market condition: {e}")
            return False
    
    async def store_protocol_data(self, protocol: str, protocol_data: Dict[str, Any]) -> bool:
        """Store protocol yield data"""
        try:
            protocol_data['last_updated'] = firestore.SERVER_TIMESTAMP
            self.db.collection(self.collections['protocols']).document(protocol).set(protocol_data, merge=True)
            return True
        except Exception as e:
            logger.error(f"❌ Error storing protocol data: {e}")
            return False
    
    async def log_cost_event(self, cost_data: Dict[str, Any]) -> bool:
        """Log individual cost events"""
        try:
            cost_data['timestamp'] = firestore.SERVER_TIMESTAMP
            self.db.collection(self.collections['costs']).add(cost_data)
            
            # Update daily cost aggregation
            today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            daily_doc_ref = self.db.collection(self.collections['costs']).document(f'daily_{today}')
            
            # Use transaction for atomic update
            @firestore.transactional
            def update_daily_costs(transaction, doc_ref):
                doc = doc_ref.get(transaction=transaction)
                if doc.exists:
                    current_data = doc.to_dict()
                    current_total = current_data.get('total_cost', 0)
                    transaction.update(doc_ref, {
                        'total_cost': current_total + cost_data.get('amount', 0),
                        'cost_count': current_data.get('cost_count', 0) + 1,
                        'last_updated': firestore.SERVER_TIMESTAMP
                    })
                else:
                    transaction.set(doc_ref, {
                        'date': today,
                        'total_cost': cost_data.get('amount', 0),
                        'cost_count': 1,
                        'created_at': firestore.SERVER_TIMESTAMP,
                        'last_updated': firestore.SERVER_TIMESTAMP
                    })
            
            transaction = self.db.transaction()
            update_daily_costs(transaction, daily_doc_ref)
            
            return True
        except Exception as e:
            logger.error(f"❌ Error logging cost: {e}")
            return False
    
    async def store_decision(self, decision_data: Dict[str, Any]) -> str:
        """Store agent decision with metadata"""
        try:
            decision_data['timestamp'] = firestore.SERVER_TIMESTAMP
            doc_ref = self.db.collection(self.collections['decisions']).add(decision_data)
            return doc_ref[1].id
        except Exception as e:
            logger.error(f"❌ Error storing decision: {e}")
            return ""
    
    async def get_recent_decisions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent agent decisions"""
        try:
            query = (self.db.collection(self.collections['decisions'])
                    .order_by('timestamp', direction=firestore.Query.DESCENDING)
                    .limit(limit))
            
            decisions = []
            for doc in query.stream():
                decision = doc.to_dict()
                decision['id'] = doc.id
                decisions.append(decision)
            
            return decisions
        except Exception as e:
            logger.error(f"❌ Error getting recent decisions: {e}")
            return []
    
    async def get_cost_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get cost summary for the last N days"""
        try:
            end_date = datetime.now(timezone.utc)
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
            start_date = start_date.replace(day=start_date.day - days)
            
            query = (self.db.collection(self.collections['costs'])
                    .where(filter=FieldFilter('timestamp', '>=', start_date))
                    .where(filter=FieldFilter('timestamp', '<=', end_date)))
            
            total_cost = 0
            cost_by_type = {}
            cost_count = 0
            
            for doc in query.stream():
                cost = doc.to_dict()
                amount = cost.get('amount', 0)
                cost_type = cost.get('type', 'unknown')
                
                total_cost += amount
                cost_count += 1
                
                if cost_type not in cost_by_type:
                    cost_by_type[cost_type] = 0
                cost_by_type[cost_type] += amount
            
            return {
                'total_cost': total_cost,
                'average_daily_cost': total_cost / max(days, 1),
                'cost_by_type': cost_by_type,
                'cost_count': cost_count,
                'period_days': days
            }
        except Exception as e:
            logger.error(f"❌ Error getting cost summary: {e}")
            return {}
    
    async def log_system_event(self, event_type: str, details: Dict[str, Any]) -> bool:
        """Log system events for monitoring"""
        try:
            self.db.collection(self.collections['system_logs']).add({
                'event': event_type,
                'timestamp': firestore.SERVER_TIMESTAMP,
                'details': details
            })
            return True
        except Exception as e:
            logger.error(f"❌ Error logging system event: {e}")
            return False
    
    # ========== YIELD OPTIMIZATION METHODS ==========
    
    async def add_position(self, position_data: Dict[str, Any]) -> str:
        """Add a new active position"""
        try:
            position_data['timestamp'] = firestore.SERVER_TIMESTAMP
            doc_ref = self.db.collection(self.collections['active_positions']).add(position_data)
            return doc_ref[1].id
        except Exception as e:
            logger.error(f"❌ Error adding position: {e}")
            return ""
    
    async def update_position(self, position_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing position"""
        try:
            updates['last_updated'] = firestore.SERVER_TIMESTAMP
            self.db.collection(self.collections['active_positions']).document(position_id).update(updates)
            return True
        except Exception as e:
            logger.error(f"❌ Error updating position: {e}")
            return False
    
    async def get_active_positions(self) -> List[Dict[str, Any]]:
        """Get all active positions"""
        try:
            positions = []
            docs = self.db.collection(self.collections['active_positions']).where(
                'position_id', '!=', '_init'
            ).stream()
            
            for doc in docs:
                position = doc.to_dict()
                position['id'] = doc.id
                positions.append(position)
            
            return positions
        except Exception as e:
            logger.error(f"❌ Error getting active positions: {e}")
            return []
    
    async def add_yield_opportunity(self, opportunity: Dict[str, Any]) -> str:
        """Add a new yield opportunity"""
        try:
            opportunity['discovered_at'] = firestore.SERVER_TIMESTAMP
            doc_ref = self.db.collection(self.collections['yield_opportunities']).add(opportunity)
            return doc_ref[1].id
        except Exception as e:
            logger.error(f"❌ Error adding yield opportunity: {e}")
            return ""
    
    async def get_top_yield_opportunities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top yield opportunities by priority score"""
        try:
            opportunities = []
            docs = self.db.collection(self.collections['yield_opportunities']).order_by(
                'priority_score', direction=firestore.Query.DESCENDING
            ).limit(limit).stream()
            
            for doc in docs:
                if doc.id != '_init':
                    opp = doc.to_dict()
                    opp['id'] = doc.id
                    opportunities.append(opp)
            
            return opportunities
        except Exception as e:
            logger.error(f"❌ Error getting yield opportunities: {e}")
            return []
    
    async def add_bridge_opportunity(self, bridge_opp: Dict[str, Any]) -> str:
        """Add a cross-chain bridge opportunity"""
        try:
            bridge_opp['discovered_at'] = firestore.SERVER_TIMESTAMP
            doc_ref = self.db.collection(self.collections['bridge_opportunities']).add(bridge_opp)
            return doc_ref[1].id
        except Exception as e:
            logger.error(f"❌ Error adding bridge opportunity: {e}")
            return ""
    
    async def update_gas_prices(self, chain: str, price_gwei: float) -> bool:
        """Update gas price for a specific chain"""
        try:
            update_data = {
                f'{chain}.price_gwei': price_gwei,
                f'{chain}.updated': firestore.SERVER_TIMESTAMP,
                'last_updated': firestore.SERVER_TIMESTAMP
            }
            self.db.collection(self.collections['gas_prices']).document('current').update(update_data)
            return True
        except Exception as e:
            logger.error(f"❌ Error updating gas prices: {e}")
            return False
    
    async def add_risk_alert(self, alert: Dict[str, Any]) -> str:
        """Add a new risk alert"""
        try:
            alert['timestamp'] = firestore.SERVER_TIMESTAMP
            alert['acknowledged'] = False
            doc_ref = self.db.collection(self.collections['risk_alerts']).add(alert)
            return doc_ref[1].id
        except Exception as e:
            logger.error(f"❌ Error adding risk alert: {e}")
            return ""