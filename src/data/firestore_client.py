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

logger = logging.getLogger(__name__)


class FirestoreClient:
    """Client for interacting with Firestore database"""
    
    def __init__(self):
        self.db = gcp_config.firestore_client
        self.collections = {
            'treasury': 'agent_data_treasury',
            'market_conditions': 'agent_data_market_conditions',
            'protocols': 'agent_data_protocols',
            'decisions': 'agent_data_decisions',
            'costs': 'agent_data_costs',
            'system_logs': 'agent_data_system_logs'
        }
    
    async def initialize_database(self) -> bool:
        """Initialize database with default documents"""
        try:
            # Initialize treasury with starting balance
            treasury_doc = {
                'balance_usd': 100.0,  # Starting seed money
                'daily_burn_rate': 0.0,
                'days_until_bankruptcy': 999,
                'emotional_state': 'stable',
                'risk_tolerance': 0.5,
                'confidence_level': 0.5,
                'created_at': firestore.SERVER_TIMESTAMP,
                'last_updated': firestore.SERVER_TIMESTAMP,
                'initialization': True
            }
            
            self.db.collection(self.collections['treasury']).document('current_state').set(treasury_doc)
            
            # Initialize market conditions
            market_doc = {
                'condition_type': 'unknown',
                'confidence_score': 0.0,
                'last_updated': firestore.SERVER_TIMESTAMP,
                'initialization': True
            }
            
            self.db.collection(self.collections['market_conditions']).document('current').set(market_doc)
            
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