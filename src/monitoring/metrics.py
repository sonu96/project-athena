"""
Metrics Collection for Athena Agent

Tracks performance and operational metrics.
"""

import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Collects and tracks agent metrics
    """
    
    def __init__(self):
        self.metrics = {
            "operations": {},
            "costs": {},
            "performance": {}
        }
        logger.info("✅ Metrics collector initialized")
    
    def record_operation(self, operation: str, duration: float, success: bool):
        """Record an operation metric"""
        if operation not in self.metrics["operations"]:
            self.metrics["operations"][operation] = {
                "count": 0,
                "success": 0,
                "failed": 0,
                "total_duration": 0
            }
        
        self.metrics["operations"][operation]["count"] += 1
        self.metrics["operations"][operation]["total_duration"] += duration
        
        if success:
            self.metrics["operations"][operation]["success"] += 1
        else:
            self.metrics["operations"][operation]["failed"] += 1
    
    def record_cost(self, category: str, amount: float):
        """Record a cost metric"""
        if category not in self.metrics["costs"]:
            self.metrics["costs"][category] = {
                "total": 0,
                "count": 0
            }
        
        self.metrics["costs"][category]["total"] += amount
        self.metrics["costs"][category]["count"] += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "operations": self.metrics["operations"],
            "costs": self.metrics["costs"],
            "performance": self.metrics["performance"]
        }