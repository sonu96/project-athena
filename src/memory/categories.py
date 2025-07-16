"""
Memory categorization system
"""

from typing import List


class MemoryCategories:
    """Define and manage memory categories"""
    
    MARKET_PATTERNS = "market_patterns"
    GAS_PATTERNS = "gas_patterns"
    POOL_BEHAVIOR = "pool_behavior"
    TIMING_PATTERNS = "timing_patterns"
    RISK_PATTERNS = "risk_patterns"
    SURVIVAL_MEMORIES = "survival_memories"
    GENERAL = "general"
    
    @classmethod
    def all_categories(cls) -> List[str]:
        """Get all memory categories"""
        return [
            cls.MARKET_PATTERNS,
            cls.GAS_PATTERNS,
            cls.POOL_BEHAVIOR,
            cls.TIMING_PATTERNS,
            cls.RISK_PATTERNS,
            cls.SURVIVAL_MEMORIES,
            cls.GENERAL
        ]
    
    @classmethod
    def is_valid_category(cls, category: str) -> bool:
        """Check if category is valid"""
        return category in cls.all_categories()