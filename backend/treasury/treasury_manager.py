from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
from .models import TreasuryEntry, AgentState

class TreasuryManager:
    """Manages agent's financial state and survival metrics"""
    
    def __init__(self, initial_balance: float = 1000.0):
        self.balance = initial_balance
        self.initial_balance = initial_balance
        self.history: List[TreasuryEntry] = []
        self.daily_costs: Dict[str, float] = {}
        
    def deduct_cost(self, amount: float, reason: str, gas_cost: float = None):
        """Deduct cost from treasury"""
        if amount > self.balance:
            raise ValueError(f"Insufficient funds: {amount} > {self.balance}")
            
        self.balance -= amount
        
        entry = TreasuryEntry(
            timestamp=datetime.now(),
            balance=self.balance,
            change=-amount,
            reason=reason,
            gas_cost=gas_cost
        )
        
        self.history.append(entry)
        
        # Track daily costs
        today = datetime.now().date().isoformat()
        self.daily_costs[today] = self.daily_costs.get(today, 0) + amount
        
    def add_revenue(self, amount: float, source: str):
        """Add revenue to treasury"""
        self.balance += amount
        
        entry = TreasuryEntry(
            timestamp=datetime.now(),
            balance=self.balance,
            change=amount,
            reason=f"Revenue: {source}"
        )
        
        self.history.append(entry)
        
    def get_daily_burn_rate(self) -> float:
        """Calculate average daily burn rate"""
        if not self.daily_costs:
            return 0.0
            
        return sum(self.daily_costs.values()) / len(self.daily_costs)
    
    def days_until_bankruptcy(self) -> float:
        """Calculate days until treasury reaches zero"""
        burn_rate = self.get_daily_burn_rate()
        if burn_rate <= 0:
            return float('inf')
            
        return self.balance / burn_rate
    
    def get_survival_status(self) -> str:
        """Get current survival status"""
        days_left = self.days_until_bankruptcy()
        
        if days_left < 1:
            return "CRITICAL"
        elif days_left < 7:
            return "WARNING"
        elif days_left < 30:
            return "CAUTION"
        else:
            return "STABLE"
    
    def get_agent_state(self, memory_count: int = 0) -> AgentState:
        """Get comprehensive agent state"""
        return AgentState(
            treasury_balance=self.balance,
            survival_status=self.get_survival_status(),
            days_until_bankruptcy=self.days_until_bankruptcy(),
            daily_burn_rate=self.get_daily_burn_rate(),
            memory_count=memory_count,
            last_decision=None  # Will be set by agent
        )
    
    def get_cost_breakdown(self) -> Dict[str, float]:
        """Get breakdown of costs by category"""
        breakdown = {}
        for entry in self.history:
            if entry.change < 0:  # Only costs
                category = self._categorize_cost(entry.reason)
                breakdown[category] = breakdown.get(category, 0) + abs(entry.change)
        return breakdown
    
    def _categorize_cost(self, reason: str) -> str:
        """Categorize cost based on reason"""
        reason_lower = reason.lower()
        if "llm" in reason_lower or "api" in reason_lower:
            return "LLM_Calls"
        elif "gas" in reason_lower:
            return "Gas_Fees"
        elif "transaction" in reason_lower:
            return "Transaction_Costs"
        else:
            return "Other_Costs"
    
    def get_treasury_summary(self) -> Dict:
        """Get comprehensive treasury summary"""
        return {
            "current_balance": self.balance,
            "initial_balance": self.initial_balance,
            "total_spent": self.initial_balance - self.balance,
            "daily_burn_rate": self.get_daily_burn_rate(),
            "days_until_bankruptcy": self.days_until_bankruptcy(),
            "survival_status": self.get_survival_status(),
            "cost_breakdown": self.get_cost_breakdown(),
            "total_entries": len(self.history)
        } 