"""
Treasury Management System

Tracks financial state and implements survival pressure through cost tracking.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class Transaction:
    """Represents a financial transaction"""
    timestamp: datetime
    amount: float
    category: str
    description: str
    balance_after: float


class TreasuryManager:
    """
    Manages the agent's financial state and survival metrics
    """
    
    def __init__(self, starting_balance: float = 100.0):
        self.balance = starting_balance
        self.starting_balance = starting_balance
        self.total_spent = 0.0
        self.total_earned = 0.0
        
        # Transaction history (keep last 1000)
        self.transactions: deque[Transaction] = deque(maxlen=1000)
        
        # Cost tracking by category
        self.costs_by_category: Dict[str, float] = {
            "llm": 0.0,
            "gas": 0.0,
            "memory": 0.0,
            "api": 0.0,
            "other": 0.0
        }
        
        # Daily cost tracking (last 30 days)
        self.daily_costs: deque[Tuple[datetime, float]] = deque(maxlen=30)
        self.hourly_costs: deque[Tuple[datetime, float]] = deque(maxlen=24)
        
        # Initialize first daily entry
        self.daily_costs.append((datetime.utcnow().date(), 0.0))
        self.hourly_costs.append((datetime.utcnow().replace(minute=0, second=0), 0.0))
        
        logger.info(f"💰 Treasury initialized with ${starting_balance:.2f}")
    
    def record_cost(self, amount: float, category: str, description: str) -> float:
        """
        Record a cost and update balance
        
        Returns:
            New balance after cost
        """
        if amount < 0:
            raise ValueError("Cost amount must be positive")
        
        # Update balance
        self.balance -= amount
        self.total_spent += amount
        
        # Update category tracking
        if category in self.costs_by_category:
            self.costs_by_category[category] += amount
        else:
            self.costs_by_category["other"] += amount
        
        # Create transaction
        tx = Transaction(
            timestamp=datetime.utcnow(),
            amount=-amount,
            category=category,
            description=description,
            balance_after=self.balance
        )
        self.transactions.append(tx)
        
        # Update daily/hourly tracking
        self._update_time_based_costs(amount)
        
        logger.debug(f"💸 Cost recorded: ${amount:.4f} for {description} | Balance: ${self.balance:.2f}")
        
        return self.balance
    
    def record_earning(self, amount: float, description: str) -> float:
        """
        Record an earning (for V2 trading profits)
        
        Returns:
            New balance after earning
        """
        if amount < 0:
            raise ValueError("Earning amount must be positive")
        
        # Update balance
        self.balance += amount
        self.total_earned += amount
        
        # Create transaction
        tx = Transaction(
            timestamp=datetime.utcnow(),
            amount=amount,
            category="earning",
            description=description,
            balance_after=self.balance
        )
        self.transactions.append(tx)
        
        logger.info(f"💵 Earning recorded: ${amount:.2f} from {description} | Balance: ${self.balance:.2f}")
        
        return self.balance
    
    def get_burn_rate(self) -> Dict[str, float]:
        """
        Calculate burn rate at different time scales
        
        Returns:
            Dict with hourly, daily, and weekly burn rates
        """
        now = datetime.utcnow()
        
        # Hourly burn rate (average of last 24 hours)
        hourly_total = sum(cost for _, cost in self.hourly_costs)
        hourly_rate = hourly_total / max(1, len(self.hourly_costs))
        
        # Daily burn rate (average of last 7 days)
        recent_daily = [
            cost for date, cost in self.daily_costs 
            if (now.date() - date).days < 7
        ]
        daily_rate = sum(recent_daily) / max(1, len(recent_daily))
        
        # Weekly burn rate (average of last 30 days)
        weekly_rate = sum(cost for _, cost in self.daily_costs) / max(1, len(self.daily_costs)) * 7
        
        return {
            "hourly": hourly_rate,
            "daily": daily_rate,
            "weekly": weekly_rate
        }
    
    def calculate_runway(self) -> Dict[str, float]:
        """
        Calculate runway in different time units
        
        Returns:
            Dict with runway in hours, days, and weeks
        """
        burn_rates = self.get_burn_rate()
        
        runway = {}
        
        # Calculate runway for each time scale
        if burn_rates["hourly"] > 0:
            runway["hours"] = self.balance / burn_rates["hourly"]
        else:
            runway["hours"] = float('inf')
        
        if burn_rates["daily"] > 0:
            runway["days"] = self.balance / burn_rates["daily"]
        else:
            runway["days"] = float('inf')
        
        if burn_rates["weekly"] > 0:
            runway["weeks"] = self.balance / burn_rates["weekly"]
        else:
            runway["weeks"] = float('inf')
        
        return runway
    
    def get_cost_breakdown(self) -> Dict[str, Dict[str, float]]:
        """
        Get detailed cost breakdown by category
        
        Returns:
            Dict with totals and percentages by category
        """
        total = sum(self.costs_by_category.values())
        
        breakdown = {}
        for category, amount in self.costs_by_category.items():
            breakdown[category] = {
                "total": amount,
                "percentage": (amount / total * 100) if total > 0 else 0,
                "average_per_tx": amount / max(1, len([t for t in self.transactions if t.category == category]))
            }
        
        return breakdown
    
    def get_financial_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive financial summary
        """
        burn_rates = self.get_burn_rate()
        runway = self.calculate_runway()
        breakdown = self.get_cost_breakdown()
        
        return {
            "balance": self.balance,
            "starting_balance": self.starting_balance,
            "total_spent": self.total_spent,
            "total_earned": self.total_earned,
            "net_change": self.balance - self.starting_balance,
            "burn_rates": burn_rates,
            "runway": runway,
            "cost_breakdown": breakdown,
            "transaction_count": len(self.transactions),
            "days_active": (datetime.utcnow() - self.transactions[0].timestamp).days if self.transactions else 0
        }
    
    def _update_time_based_costs(self, amount: float):
        """Update hourly and daily cost tracking"""
        now = datetime.utcnow()
        current_hour = now.replace(minute=0, second=0, microsecond=0)
        current_date = now.date()
        
        # Update hourly costs
        if self.hourly_costs and self.hourly_costs[-1][0] == current_hour:
            # Update existing hour
            self.hourly_costs[-1] = (current_hour, self.hourly_costs[-1][1] + amount)
        else:
            # New hour
            self.hourly_costs.append((current_hour, amount))
        
        # Update daily costs
        if self.daily_costs and self.daily_costs[-1][0] == current_date:
            # Update existing day
            self.daily_costs[-1] = (current_date, self.daily_costs[-1][1] + amount)
        else:
            # New day
            self.daily_costs.append((current_date, amount))
    
    def should_activate_survival_mode(self) -> bool:
        """Determine if survival mode should be activated"""
        runway = self.calculate_runway()
        return runway["days"] < 3
    
    def get_recent_transactions(self, limit: int = 10) -> List[Transaction]:
        """Get recent transactions"""
        return list(self.transactions)[-limit:]
    
    def estimate_time_until_milestone(self, milestone: float) -> Optional[timedelta]:
        """
        Estimate time until balance reaches a milestone
        
        Args:
            milestone: Target balance
            
        Returns:
            Timedelta if reachable, None if not
        """
        burn_rate = self.get_burn_rate()["daily"]
        
        if milestone >= self.balance:
            # We need to earn money (V2 feature)
            return None
        elif burn_rate > 0:
            days_until = (self.balance - milestone) / burn_rate
            return timedelta(days=days_until)
        else:
            return None