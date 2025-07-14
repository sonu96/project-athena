"""
Treasury management with emotional states and survival mechanisms
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import logging
import json

from ..data.firestore_client import FirestoreClient
from ..data.bigquery_client import BigQueryClient
from ..integrations.mem0_integration import Mem0Integration
from ..config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class TreasuryState:
    """Current treasury state with emotional indicators"""
    balance_usd: float
    daily_burn_rate: float
    days_until_bankruptcy: int
    emotional_state: str  # 'stable', 'cautious', 'desperate'
    risk_tolerance: float  # 0.0 to 1.0
    confidence_level: float  # 0.0 to 1.0
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'balance_usd': self.balance_usd,
            'daily_burn_rate': self.daily_burn_rate,
            'days_until_bankruptcy': self.days_until_bankruptcy,
            'emotional_state': self.emotional_state,
            'risk_tolerance': self.risk_tolerance,
            'confidence_level': self.confidence_level,
            'last_updated': self.last_updated.isoformat()
        }


class TreasuryManager:
    """Manages agent treasury with survival instincts"""
    
    def __init__(self, firestore_client: FirestoreClient, memory_integration: Mem0Integration):
        self.firestore = firestore_client
        self.memory = memory_integration
        self.current_state: Optional[TreasuryState] = None
        
        # Treasury thresholds
        self.thresholds = {
            'critical': settings.critical_treasury_threshold_usd,  # $25
            'warning': settings.warning_treasury_threshold_usd,    # $50
            'comfortable': 100.0
        }
        
        # Emotional state mappings
        self.emotional_states = {
            'desperate': {
                'threshold': self.thresholds['critical'],
                'risk_tolerance': 0.2,
                'confidence': 0.3,
                'description': 'Survival mode - extreme cost cutting required'
            },
            'cautious': {
                'threshold': self.thresholds['warning'],
                'risk_tolerance': 0.4,
                'confidence': 0.6,
                'description': 'Conservative mode - careful resource management'
            },
            'stable': {
                'threshold': self.thresholds['comfortable'],
                'risk_tolerance': 0.7,
                'confidence': 0.8,
                'description': 'Normal operations - balanced approach'
            },
            'confident': {
                'threshold': 150.0,
                'risk_tolerance': 0.8,
                'confidence': 0.9,
                'description': 'Growth mode - can take calculated risks'
            }
        }
        
        # Cost tracking
        self.cost_history: List[Dict[str, Any]] = []
        self.daily_costs: Dict[str, float] = {}
    
    async def initialize(self, starting_balance: float = None) -> bool:
        """Initialize treasury with starting balance"""
        try:
            if starting_balance is None:
                starting_balance = settings.agent_starting_treasury
            
            # Create initial state
            self.current_state = TreasuryState(
                balance_usd=starting_balance,
                daily_burn_rate=0.0,
                days_until_bankruptcy=999,
                emotional_state='stable',
                risk_tolerance=0.7,
                confidence_level=0.8
            )
            
            # Store in Firestore
            await self.firestore.update_treasury(self.current_state.to_dict())
            
            # Create initial memory
            await self.memory.add_memory(
                content=f"Treasury initialized with ${starting_balance}. Beginning agent life with stable emotional state.",
                metadata={
                    "category": "treasury_milestone",
                    "importance": 0.8,
                    "treasury_balance": starting_balance,
                    "emotional_state": "stable"
                }
            )
            
            # Log to BigQuery
            await self._log_treasury_snapshot("initialization")
            
            logger.info(f"✅ Treasury initialized with ${starting_balance}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error initializing treasury: {e}")
            return False
    
    async def track_cost(self, cost_amount: float, cost_type: str, description: str) -> bool:
        """Track individual cost and update treasury"""
        try:
            if not self.current_state:
                await self.load_state()
            
            # Update balance
            self.current_state.balance_usd -= cost_amount
            
            # Track cost
            cost_event = {
                'amount': cost_amount,
                'type': cost_type,
                'description': description,
                'timestamp': datetime.now(timezone.utc),
                'remaining_balance': self.current_state.balance_usd,
                'emotional_state': self.current_state.emotional_state
            }
            
            self.cost_history.append(cost_event)
            
            # Update daily costs
            today = datetime.now(timezone.utc).date().isoformat()
            if today not in self.daily_costs:
                self.daily_costs[today] = 0
            self.daily_costs[today] += cost_amount
            
            # Log to Firestore
            await self.firestore.log_cost_event({
                'amount_usd': cost_amount,
                'cost_type': cost_type,
                'description': description,
                'operation': 'agent_operation',
                'llm_tokens': 0,  # Will be set by LLM integration
                'api_calls': 1
            })
            
            # Update burn rate
            await self._update_burn_rate()
            
            # Update emotional state based on new balance
            await self._update_emotional_state()
            
            # Save updated state
            await self.firestore.update_treasury(self.current_state.to_dict())
            
            # Check for critical situations
            await self._check_survival_status()
            
            logger.info(f"💰 Cost tracked: ${cost_amount} ({cost_type}) - Remaining: ${self.current_state.balance_usd:.2f}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error tracking cost: {e}")
            return False
    
    async def _update_burn_rate(self):
        """Calculate and update daily burn rate"""
        try:
            # Get costs from last 7 days
            cost_summary = await self.firestore.get_cost_summary(days=7)
            
            if cost_summary and cost_summary.get('total_cost', 0) > 0:
                # Calculate average daily burn
                days = cost_summary.get('period_days', 7)
                self.current_state.daily_burn_rate = cost_summary['total_cost'] / days
                
                # Calculate days until bankruptcy
                if self.current_state.daily_burn_rate > 0:
                    self.current_state.days_until_bankruptcy = int(
                        self.current_state.balance_usd / self.current_state.daily_burn_rate
                    )
                else:
                    self.current_state.days_until_bankruptcy = 999
            
        except Exception as e:
            logger.error(f"Error updating burn rate: {e}")
    
    async def _update_emotional_state(self):
        """Update emotional state based on treasury level"""
        balance = self.current_state.balance_usd
        old_state = self.current_state.emotional_state
        
        # Determine new state based on balance
        if balance <= self.thresholds['critical']:
            new_state = 'desperate'
        elif balance <= self.thresholds['warning']:
            new_state = 'cautious'
        elif balance >= 150.0:
            new_state = 'confident'
        else:
            new_state = 'stable'
        
        if new_state != old_state:
            # Emotional state changed - update parameters
            state_config = self.emotional_states[new_state]
            self.current_state.emotional_state = new_state
            self.current_state.risk_tolerance = state_config['risk_tolerance']
            self.current_state.confidence_level = state_config['confidence']
            
            # Create memory of state change
            await self.memory.add_memory(
                content=f"Emotional state changed from {old_state} to {new_state} due to treasury level ${balance:.2f}. {state_config['description']}",
                metadata={
                    "category": "emotional_change",
                    "importance": 0.8,
                    "old_state": old_state,
                    "new_state": new_state,
                    "treasury_balance": balance,
                    "trigger": "treasury_level"
                }
            )
            
            # Log state transition to BigQuery
            await self._log_emotional_transition(old_state, new_state, balance)
            
            logger.info(f"🧠 Emotional state: {old_state} → {new_state} (${balance:.2f})")
    
    async def _check_survival_status(self):
        """Check if agent is in survival mode and take action"""
        if self.current_state.balance_usd <= self.thresholds['critical']:
            # SURVIVAL MODE ACTIVATED
            await self._activate_survival_mode()
        elif self.current_state.days_until_bankruptcy <= 5:
            # WARNING: Low runway
            await self._activate_warning_mode()
    
    async def _activate_survival_mode(self):
        """Activate emergency survival mode"""
        try:
            logger.warning(f"🚨 SURVIVAL MODE ACTIVATED! Balance: ${self.current_state.balance_usd:.2f}")
            
            # Query survival memories
            survival_memories = await self.memory.query_memories(
                query="survival emergency treasury critical low balance",
                category="survival_critical",
                limit=5
            )
            
            # Create survival event memory
            await self.memory.add_memory(
                content=f"SURVIVAL MODE ACTIVATED: Treasury at ${self.current_state.balance_usd:.2f}, "
                       f"{self.current_state.days_until_bankruptcy} days remaining. "
                       f"Implementing emergency cost reduction and conservative strategies.",
                metadata={
                    "category": "survival_critical",
                    "importance": 1.0,
                    "emergency": True,
                    "treasury_balance": self.current_state.balance_usd,
                    "burn_rate": self.current_state.daily_burn_rate
                }
            )
            
            # Log survival event
            await self.firestore.log_system_event(
                "survival_mode_activated",
                {
                    "treasury_balance": self.current_state.balance_usd,
                    "daily_burn_rate": self.current_state.daily_burn_rate,
                    "days_remaining": self.current_state.days_until_bankruptcy,
                    "survival_memories_found": len(survival_memories)
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Error activating survival mode: {e}")
    
    async def _activate_warning_mode(self):
        """Activate warning mode for low runway"""
        try:
            logger.warning(f"⚠️ WARNING MODE: Only {self.current_state.days_until_bankruptcy} days of runway remaining!")
            
            # Create warning memory
            await self.memory.add_memory(
                content=f"WARNING: Treasury runway critically low - only {self.current_state.days_until_bankruptcy} days remaining at current burn rate of ${self.current_state.daily_burn_rate:.2f}/day",
                metadata={
                    "category": "survival_critical",
                    "importance": 0.9,
                    "warning": True,
                    "days_remaining": self.current_state.days_until_bankruptcy
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Error activating warning mode: {e}")
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current treasury status"""
        if not self.current_state:
            await self.load_state()
        
        # Determine overall status
        if self.current_state.balance_usd <= self.thresholds['critical']:
            status = 'critical'
        elif self.current_state.balance_usd <= self.thresholds['warning']:
            status = 'warning'
        else:
            status = 'healthy'
        
        return {
            'balance': self.current_state.balance_usd,
            'daily_burn': self.current_state.daily_burn_rate,
            'days_remaining': self.current_state.days_until_bankruptcy,
            'emotional_state': self.current_state.emotional_state,
            'risk_tolerance': self.current_state.risk_tolerance,
            'confidence': self.current_state.confidence_level,
            'status': status,
            'thresholds': self.thresholds,
            'last_updated': self.current_state.last_updated.isoformat()
        }
    
    async def load_state(self) -> bool:
        """Load treasury state from Firestore"""
        try:
            treasury_data = await self.firestore.get_current_treasury()
            
            if treasury_data:
                self.current_state = TreasuryState(
                    balance_usd=treasury_data['balance_usd'],
                    daily_burn_rate=treasury_data.get('daily_burn_rate', 0),
                    days_until_bankruptcy=treasury_data.get('days_until_bankruptcy', 999),
                    emotional_state=treasury_data.get('emotional_state', 'stable'),
                    risk_tolerance=treasury_data.get('risk_tolerance', 0.5),
                    confidence_level=treasury_data.get('confidence_level', 0.5)
                )
                return True
            else:
                logger.warning("No treasury state found, initializing new treasury")
                await self.initialize()
                return True
                
        except Exception as e:
            logger.error(f"❌ Error loading treasury state: {e}")
            return False
    
    async def _log_treasury_snapshot(self, snapshot_type: str = "regular"):
        """Log treasury snapshot to BigQuery"""
        try:
            snapshot_data = {
                'balance_usd': self.current_state.balance_usd,
                'daily_burn_rate': self.current_state.daily_burn_rate,
                'days_until_bankruptcy': self.current_state.days_until_bankruptcy,
                'emotional_state': self.current_state.emotional_state,
                'risk_tolerance': self.current_state.risk_tolerance,
                'confidence_level': self.current_state.confidence_level,
                'snapshot_type': snapshot_type
            }
            
            await self.firestore.db.collection('agent_data_treasury').add({
                **snapshot_data,
                'timestamp': datetime.now(timezone.utc)
            })
            
        except Exception as e:
            logger.error(f"Error logging treasury snapshot: {e}")
    
    async def _log_emotional_transition(self, old_state: str, new_state: str, balance: float):
        """Log emotional state transition to BigQuery"""
        try:
            # This would be logged to BigQuery in production
            transition_data = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'previous_state': old_state,
                'new_state': new_state,
                'balance_usd': balance,
                'trigger': 'balance_change'
            }
            
            logger.info(f"Emotional transition logged: {transition_data}")
            
        except Exception as e:
            logger.error(f"Error logging emotional transition: {e}")
    
    async def generate_survival_report(self) -> Dict[str, Any]:
        """Generate comprehensive survival report"""
        try:
            status = await self.get_status()
            cost_summary = await self.firestore.get_cost_summary(days=7)
            
            # Calculate survival metrics
            survival_days_at_current_burn = (
                int(status['balance'] / status['daily_burn'])
                if status['daily_burn'] > 0 else 999
            )
            
            # Determine survival recommendations
            recommendations = []
            
            if status['emotional_state'] == 'desperate':
                recommendations.extend([
                    "CRITICAL: Immediately reduce all non-essential operations",
                    "Switch to minimum observation frequency",
                    "Use only cheapest LLM models",
                    "Focus solely on capital preservation"
                ])
            elif status['emotional_state'] == 'cautious':
                recommendations.extend([
                    "Reduce observation frequency by 50%",
                    "Limit expensive LLM calls",
                    "Focus on low-risk opportunities",
                    "Monitor burn rate closely"
                ])
            
            report = {
                'current_status': status,
                'cost_analysis': cost_summary,
                'survival_metrics': {
                    'days_until_bankruptcy': survival_days_at_current_burn,
                    'required_daily_burn_for_30_days': status['balance'] / 30,
                    'current_vs_sustainable_ratio': status['daily_burn'] / (status['balance'] / 30) if status['balance'] > 0 else 0
                },
                'recommendations': recommendations,
                'report_timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating survival report: {e}")
            return {}