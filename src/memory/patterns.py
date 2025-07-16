"""
Pattern recognition system for memory formation
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..core.consciousness import Pattern

logger = logging.getLogger(__name__)


class PatternRecognizer:
    """
    Identifies and tracks patterns in observations
    """
    
    def __init__(self):
        self.pattern_history: Dict[str, List[Dict[str, Any]]] = {}
    
    def analyze_for_patterns(
        self,
        observations: List[Dict[str, Any]],
        pattern_type: str
    ) -> Optional[Pattern]:
        """
        Analyze observations for patterns
        
        Args:
            observations: List of observations
            pattern_type: Type of pattern to look for
            
        Returns:
            Pattern if found
        """
        if pattern_type == "volume_spike":
            return self._detect_volume_spike(observations)
        elif pattern_type == "yield_consistency":
            return self._detect_yield_consistency(observations)
        elif pattern_type == "time_correlation":
            return self._detect_time_correlation(observations)
        else:
            return None
    
    def _detect_volume_spike(
        self,
        observations: List[Dict[str, Any]]
    ) -> Optional[Pattern]:
        """Detect volume spike patterns"""
        
        if len(observations) < 3:
            return None
        
        # Calculate average volume
        volumes = [obs.get("volume_24h_usd", 0) for obs in observations]
        avg_volume = sum(volumes) / len(volumes)
        
        # Check for spikes
        spikes = [v for v in volumes if v > avg_volume * 1.5]
        
        if len(spikes) >= 2:
            return Pattern(
                id=f"volume_spike_{datetime.utcnow().timestamp()}",
                description=f"Volume spikes detected - {len(spikes)} occurrences above 150% average",
                category="market_patterns",
                confidence=0.7,
                occurrences=len(spikes),
                first_seen=datetime.utcnow(),
                last_seen=datetime.utcnow()
            )
        
        return None
    
    def _detect_yield_consistency(
        self,
        observations: List[Dict[str, Any]]
    ) -> Optional[Pattern]:
        """Detect consistent yield patterns"""
        
        if len(observations) < 5:
            return None
        
        # Check yield stability
        yields = [obs.get("total_apy", 0) for obs in observations]
        avg_yield = sum(yields) / len(yields)
        
        # Calculate standard deviation
        variance = sum((y - avg_yield) ** 2 for y in yields) / len(yields)
        std_dev = variance ** 0.5
        
        # Low standard deviation indicates consistency
        if std_dev < avg_yield * 0.1:  # Less than 10% variation
            return Pattern(
                id=f"yield_consistency_{datetime.utcnow().timestamp()}",
                description=f"Consistent yields around {avg_yield:.1%} APY",
                category="pool_behavior",
                confidence=0.8,
                occurrences=len(observations),
                first_seen=datetime.utcnow(),
                last_seen=datetime.utcnow()
            )
        
        return None
    
    def _detect_time_correlation(
        self,
        observations: List[Dict[str, Any]]
    ) -> Optional[Pattern]:
        """Detect time-based patterns"""
        
        if len(observations) < 10:
            return None
        
        # Group by hour
        hourly_data = {}
        for obs in observations:
            if "timestamp" in obs:
                hour = obs["timestamp"].hour
                if hour not in hourly_data:
                    hourly_data[hour] = []
                hourly_data[hour].append(obs)
        
        # Find hours with consistent patterns
        for hour, hour_obs in hourly_data.items():
            if len(hour_obs) >= 3:
                # Check for consistent behavior
                gas_prices = [o.get("gas_price_gwei", 0) for o in hour_obs]
                if gas_prices and max(gas_prices) < 10:  # Low gas
                    return Pattern(
                        id=f"time_pattern_{hour}",
                        description=f"Low gas prices consistently at {hour}:00 UTC",
                        category="timing_patterns",
                        confidence=0.75,
                        occurrences=len(hour_obs),
                        first_seen=datetime.utcnow(),
                        last_seen=datetime.utcnow()
                    )
        
        return None