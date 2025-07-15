"""
Position Manager for DeFi positions tracking

This module tracks and manages DeFi positions, starting with Compound V3.
It monitors position health, calculates rewards, and maintains position history.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict, field

logger = logging.getLogger(__name__)


@dataclass
class PositionState:
    """State of a DeFi position"""
    protocol: str = "compound_v3"
    chain: str = "base"
    asset: str = "USDC"
    amount_supplied: float = 0.0
    entry_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    entry_apy: float = 0.0
    current_apy: float = 0.0
    total_earned: float = 0.0
    pending_rewards: float = 0.0
    last_compound: Optional[datetime] = None
    compound_count: int = 0
    gas_spent: float = 0.0
    net_profit: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        data = asdict(self)
        # Convert datetime objects to ISO format
        data['entry_timestamp'] = self.entry_timestamp.isoformat()
        data['last_compound'] = self.last_compound.isoformat() if self.last_compound else None
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PositionState':
        """Create from dictionary"""
        # Convert ISO strings back to datetime
        if 'entry_timestamp' in data and isinstance(data['entry_timestamp'], str):
            data['entry_timestamp'] = datetime.fromisoformat(data['entry_timestamp'])
        if 'last_compound' in data and data['last_compound']:
            data['last_compound'] = datetime.fromisoformat(data['last_compound'])
        return cls(**data)


@dataclass
class CompoundHistory:
    """Record of a compound event"""
    timestamp: datetime
    rewards_amount: float
    gas_cost: float
    net_gain: float
    apy_at_compound: float
    tx_hash: str
    emotional_state: str
    decision_reasoning: str


class PositionManager:
    """Manages DeFi positions and tracks performance"""
    
    def __init__(self, cdp_integration, firestore_client=None):
        self.cdp = cdp_integration
        self.firestore = firestore_client
        self.position_state = PositionState()
        self.compound_history: List[CompoundHistory] = []
        self._initialized = False
    
    async def initialize(self) -> bool:
        """Initialize position manager and load existing position"""
        try:
            logger.info("📊 Initializing Position Manager...")
            
            # Load existing position from database if available
            if self.firestore:
                position_data = await self.firestore.get_document(
                    "positions",
                    f"{self.position_state.protocol}_{self.position_state.asset}"
                )
                
                if position_data:
                    self.position_state = PositionState.from_dict(position_data)
                    logger.info(f"✅ Loaded existing position: {self.position_state.amount_supplied} USDC")
                    
                    # Load compound history
                    history_data = await self.firestore.get_collection(
                        "compound_history",
                        filters=[("protocol", "==", self.position_state.protocol)],
                        order_by="timestamp",
                        limit=100
                    )
                    
                    self.compound_history = [
                        CompoundHistory(**record) for record in history_data
                    ]
                    logger.info(f"✅ Loaded {len(self.compound_history)} compound events")
            
            # Sync with current chain state
            await self.sync_position()
            
            self._initialized = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize position manager: {e}")
            return False
    
    async def sync_position(self) -> PositionState:
        """Sync position state with blockchain"""
        try:
            # Get current position from CDP/Compound
            compound_balance = await self.cdp.get_compound_balance()
            
            # Update position state
            self.position_state.amount_supplied = compound_balance["supplied_usdc"]
            self.position_state.current_apy = compound_balance["supply_apy"]
            self.position_state.pending_rewards = await self.cdp.get_pending_rewards()
            
            # Calculate total earned (previous + pending)
            self.position_state.total_earned = (
                self.position_state.total_earned + 
                compound_balance.get("accrued_interest", 0)
            )
            
            # Calculate net profit
            self.position_state.net_profit = (
                self.position_state.total_earned - self.position_state.gas_spent
            )
            
            logger.info(f"📊 Position synced: {self.position_state.amount_supplied} USDC @ {self.position_state.current_apy:.2f}% APY")
            
            # Save to database
            if self.firestore:
                await self.firestore.set_document(
                    "positions",
                    f"{self.position_state.protocol}_{self.position_state.asset}",
                    self.position_state.to_dict()
                )
            
            return self.position_state
            
        except Exception as e:
            logger.error(f"❌ Failed to sync position: {e}")
            return self.position_state
    
    async def should_compound(self, emotional_state: str, gas_price: Dict[str, float]) -> Dict[str, Any]:
        """Determine if we should compound based on rewards vs gas"""
        try:
            # Get pending rewards
            pending_rewards = self.position_state.pending_rewards
            
            # Get gas cost estimate
            gas_cost_usd = gas_price.get("estimated_cost_usd", 1.0) * 250  # Compound uses ~250k gas
            
            # Apply emotional state multipliers from V1 design
            required_multiplier = {
                "desperate": 3.0,  # Need 3x gas in rewards
                "cautious": 2.0,   # Need 2x gas in rewards
                "stable": 1.5,     # Need 1.5x gas in rewards
                "confident": 1.5   # Need 1.5x gas in rewards
            }.get(emotional_state, 2.0)
            
            # Check profitability
            is_profitable = pending_rewards >= (gas_cost_usd * required_multiplier)
            
            # Calculate days since last compound
            days_since_compound = 0
            if self.position_state.last_compound:
                time_diff = datetime.now(timezone.utc) - self.position_state.last_compound
                days_since_compound = time_diff.total_seconds() / 86400
            
            # Build decision reasoning
            reasoning = f"Pending rewards: ${pending_rewards:.4f}, Gas cost: ${gas_cost_usd:.2f}, "
            reasoning += f"Required multiplier: {required_multiplier}x ({emotional_state} state), "
            reasoning += f"Days since compound: {days_since_compound:.1f}"
            
            if not is_profitable:
                reasoning += f" - NOT PROFITABLE (need ${gas_cost_usd * required_multiplier:.4f} in rewards)"
            else:
                net_gain = pending_rewards - gas_cost_usd
                reasoning += f" - PROFITABLE (net gain: ${net_gain:.4f})"
            
            return {
                "should_compound": is_profitable,
                "pending_rewards": pending_rewards,
                "gas_cost": gas_cost_usd,
                "required_multiplier": required_multiplier,
                "net_gain": pending_rewards - gas_cost_usd if is_profitable else 0,
                "days_since_compound": days_since_compound,
                "reasoning": reasoning
            }
            
        except Exception as e:
            logger.error(f"❌ Error in compound decision: {e}")
            return {
                "should_compound": False,
                "reasoning": f"Error: {str(e)}"
            }
    
    async def execute_compound(self, emotional_state: str, decision_reasoning: str) -> Dict[str, Any]:
        """Execute compound operation"""
        try:
            # Execute compound via CDP
            result = await self.cdp.compound_rewards()
            
            if result["success"]:
                # Update position state
                self.position_state.compound_count += 1
                self.position_state.last_compound = datetime.now(timezone.utc)
                self.position_state.gas_spent += result["gas_cost"]
                self.position_state.total_earned += result["amount_compounded"]
                self.position_state.net_profit = self.position_state.total_earned - self.position_state.gas_spent
                
                # Record in history
                compound_event = CompoundHistory(
                    timestamp=datetime.now(timezone.utc),
                    rewards_amount=result["amount_compounded"],
                    gas_cost=result["gas_cost"],
                    net_gain=result["net_gain"],
                    apy_at_compound=self.position_state.current_apy,
                    tx_hash=result["tx_hash"],
                    emotional_state=emotional_state,
                    decision_reasoning=decision_reasoning
                )
                
                self.compound_history.append(compound_event)
                
                # Save to database
                if self.firestore:
                    await self.firestore.add_document(
                        "compound_history",
                        asdict(compound_event)
                    )
                    await self.firestore.set_document(
                        "positions",
                        f"{self.position_state.protocol}_{self.position_state.asset}",
                        self.position_state.to_dict()
                    )
                
                logger.info(f"✅ Compound #{self.position_state.compound_count} successful! Net gain: ${result['net_gain']:.4f}")
                
                return {
                    "success": True,
                    "compound_number": self.position_state.compound_count,
                    "net_gain": result["net_gain"],
                    "total_profit": self.position_state.net_profit
                }
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to execute compound: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def open_position(self, amount: float, emotional_state: str) -> Dict[str, Any]:
        """Open a new Compound position"""
        try:
            # Get current APY
            current_apy = await self.cdp.get_compound_apy()
            
            # Supply to Compound
            result = await self.cdp.supply_to_compound(amount)
            
            if result["success"]:
                # Initialize position state
                self.position_state = PositionState(
                    amount_supplied=amount,
                    entry_apy=current_apy,
                    current_apy=current_apy,
                    gas_spent=result["gas_cost"]
                )
                
                # Save to database
                if self.firestore:
                    await self.firestore.set_document(
                        "positions",
                        f"{self.position_state.protocol}_{self.position_state.asset}",
                        self.position_state.to_dict()
                    )
                    
                    # Record position opening event
                    await self.firestore.add_document(
                        "position_events",
                        {
                            "event_type": "position_opened",
                            "protocol": self.position_state.protocol,
                            "amount": amount,
                            "apy": current_apy,
                            "emotional_state": emotional_state,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "tx_hash": result["tx_hash"]
                        }
                    )
                
                logger.info(f"✅ Opened Compound position: {amount} USDC @ {current_apy:.2f}% APY")
                
                return {
                    "success": True,
                    "amount": amount,
                    "apy": current_apy,
                    "gas_cost": result["gas_cost"]
                }
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to open position: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_position_metrics(self) -> Dict[str, Any]:
        """Get comprehensive position metrics"""
        metrics = {
            "protocol": self.position_state.protocol,
            "asset": self.position_state.asset,
            "amount_supplied": self.position_state.amount_supplied,
            "current_apy": self.position_state.current_apy,
            "total_earned": self.position_state.total_earned,
            "gas_spent": self.position_state.gas_spent,
            "net_profit": self.position_state.net_profit,
            "compound_count": self.position_state.compound_count,
            "pending_rewards": self.position_state.pending_rewards,
            "position_age_days": 0,
            "average_compound_frequency": 0,
            "roi_percentage": 0
        }
        
        # Calculate position age
        if self.position_state.entry_timestamp:
            age = datetime.now(timezone.utc) - self.position_state.entry_timestamp
            metrics["position_age_days"] = age.total_seconds() / 86400
        
        # Calculate average compound frequency
        if self.position_state.compound_count > 0 and metrics["position_age_days"] > 0:
            metrics["average_compound_frequency"] = (
                metrics["position_age_days"] / self.position_state.compound_count
            )
        
        # Calculate ROI
        if self.position_state.amount_supplied > 0:
            metrics["roi_percentage"] = (
                self.position_state.net_profit / self.position_state.amount_supplied * 100
            )
        
        return metrics
    
    def get_compound_patterns(self) -> Dict[str, Any]:
        """Analyze compound history for patterns"""
        if not self.compound_history:
            return {
                "total_compounds": 0,
                "patterns": []
            }
        
        patterns = {
            "total_compounds": len(self.compound_history),
            "average_gas_cost": sum(c.gas_cost for c in self.compound_history) / len(self.compound_history),
            "average_rewards": sum(c.rewards_amount for c in self.compound_history) / len(self.compound_history),
            "average_net_gain": sum(c.net_gain for c in self.compound_history) / len(self.compound_history),
            "best_compound": max(self.compound_history, key=lambda c: c.net_gain) if self.compound_history else None,
            "worst_compound": min(self.compound_history, key=lambda c: c.net_gain) if self.compound_history else None,
            "emotional_state_distribution": {}
        }
        
        # Analyze by emotional state
        for event in self.compound_history:
            state = event.emotional_state
            if state not in patterns["emotional_state_distribution"]:
                patterns["emotional_state_distribution"][state] = {
                    "count": 0,
                    "total_net_gain": 0,
                    "average_net_gain": 0
                }
            
            patterns["emotional_state_distribution"][state]["count"] += 1
            patterns["emotional_state_distribution"][state]["total_net_gain"] += event.net_gain
        
        # Calculate averages
        for state, data in patterns["emotional_state_distribution"].items():
            if data["count"] > 0:
                data["average_net_gain"] = data["total_net_gain"] / data["count"]
        
        return patterns