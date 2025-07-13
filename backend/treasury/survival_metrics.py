class SurvivalMetrics:
    """Calculates days until bankruptcy and other survival metrics."""
    
    def __init__(self):
        pass

    def days_until_bankruptcy(self, balance: float, burn_rate: float) -> float:
        """Calculate days until treasury reaches zero."""
        if burn_rate <= 0:
            return float('inf')
        return balance / burn_rate
