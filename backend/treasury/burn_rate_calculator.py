from typing import Dict

class BurnRateCalculator:
    """Calculates daily operating costs for the agent."""
    
    def __init__(self):
        pass

    def get_daily_burn_rate(self, daily_costs: Dict[str, float]) -> float:
        """Calculate average daily burn rate from a dictionary of daily costs."""
        if not daily_costs:
            return 0.0
        return sum(daily_costs.values()) / len(daily_costs)
