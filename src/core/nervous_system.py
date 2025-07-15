"""
Central nervous system orchestrator for the DeFi Agent

This module coordinates the cognitive loop and manages the agent's
consciousness state, enabling unified decision-making and emotional intelligence.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from langsmith import traceable

from ..workflows.cognitive_loop import create_cognitive_loop
from ..workflows.consciousness import ConsciousnessState
from ..workflows.emotional_router import (
    emotional_router,
    get_operational_parameters,
    should_activate_emergency_mode,
    calculate_risk_tolerance
)
from ..config.settings import settings

logger = logging.getLogger(__name__)


class NervousSystem:
    """Central nervous system that orchestrates all agent operations
    
    The nervous system manages:
    - The cognitive loop (Sense → Think → Feel → Decide → Learn)
    - Consciousness state
    - Emotional routing and operational modes
    - Emergency responses
    """
    
    def __init__(self):
        self.cognitive_loop = None
        self.consciousness = self._initialize_consciousness()
        self.operational_mode = "normal_mode"
        self.operational_parameters = get_operational_parameters(self.operational_mode)
        self._last_mode = self.operational_mode
        self._initialized = False
        
        # Performance tracking
        self.cycle_start_time = None
        self.cycle_durations = []  # Keep last 10 cycle times
        
    def _initialize_consciousness(self) -> ConsciousnessState:
        """Initialize the agent's consciousness state"""
        return ConsciousnessState(
            agent_id=getattr(settings, 'agent_id', 'athena_001'),
            emotional_state="stable",
            market_data={},
            treasury_balance=getattr(settings, 'agent_starting_treasury', 100.0),
            days_until_bankruptcy=999,
            current_goal="observe_and_learn",
            recent_memories=[],
            active_patterns=[],
            available_actions=["normal_observation"],
            last_decision={},
            decision_confidence=0.5,
            current_experience={},
            lessons_learned=[],
            position_data={},  # V1 addition
            yield_metrics={},  # V1 addition
            compound_history=[],  # V1 addition
            cycle_count=0,
            total_cost=0.0,
            timestamp=datetime.now(timezone.utc),
            errors=[],
            warnings=[],
            operational_mode="normal_mode"
        )
    
    async def initialize(self):
        """Initialize the nervous system components"""
        if not self._initialized:
            logger.info("🧠 Initializing nervous system...")
            self.cognitive_loop = create_cognitive_loop()
            self._initialized = True
            logger.info("✅ Nervous system initialized")
    
    @traceable(name="consciousness_cycle")
    async def run_consciousness_cycle(self) -> ConsciousnessState:
        """Run one complete cycle through the cognitive loop
        
        This executes the full Sense → Think → Feel → Decide → Learn cycle,
        updating the consciousness state and operational parameters.
        
        Returns:
            Updated consciousness state after the cycle
        """
        try:
            # Ensure initialization
            if not self._initialized:
                await self.initialize()
            
            # Start cycle timing
            self.cycle_start_time = datetime.now(timezone.utc)
            
            # Check for emergency conditions before cycle
            if should_activate_emergency_mode(self.consciousness):
                logger.warning("🚨 EMERGENCY MODE ACTIVATED!")
                self.consciousness["emotional_state"] = "desperate"
                self.operational_mode = "survival_mode"
            
            # Execute the cognitive loop
            logger.info(f"🔄 Starting consciousness cycle {self.consciousness.get('cycle_count', 0) + 1}")
            self.consciousness = await self.cognitive_loop.ainvoke(self.consciousness)
            
            # Update operational mode based on emotional state
            self.operational_mode = emotional_router(self.consciousness)
            self.consciousness["operational_mode"] = self.operational_mode
            
            # Apply operational parameters
            self.operational_parameters = get_operational_parameters(self.operational_mode)
            self._apply_parameters(self.operational_parameters)
            
            # Calculate and store risk tolerance
            risk_tolerance = calculate_risk_tolerance(self.consciousness)
            self.consciousness["risk_tolerance"] = risk_tolerance
            
            # Track cycle performance
            cycle_duration = (datetime.now(timezone.utc) - self.cycle_start_time).total_seconds()
            self.cycle_durations.append(cycle_duration)
            self.cycle_durations = self.cycle_durations[-10:]  # Keep last 10
            
            # Log cycle summary
            self._log_cycle_summary(cycle_duration)
            
            return self.consciousness
            
        except Exception as e:
            logger.error(f"❌ Critical error in consciousness cycle: {e}")
            self.consciousness["errors"].append(f"Consciousness cycle error: {str(e)[:200]}")
            # Return state even on error
            return self.consciousness
    
    def _apply_parameters(self, params: Dict[str, Any]):
        """Apply operational parameters based on emotional state"""
        
        # Log mode changes
        if hasattr(self, '_last_mode') and self._last_mode != self.operational_mode:
            logger.warning(f"🧠 Nervous system switched: {self._last_mode} → {self.operational_mode}")
            logger.info(f"   New parameters: {params.get('description', 'No description')}")
            
            # Log specific changes
            if self.operational_mode == "survival_mode":
                logger.warning(f"   💰 Daily budget: ${params['max_daily_cost']}")
                logger.warning(f"   ⏰ Observation interval: {params['observation_interval']/3600:.1f} hours")
                logger.warning(f"   🤖 LLM model: {params['llm_model']}")
        
        self._last_mode = self.operational_mode
    
    def _log_cycle_summary(self, cycle_duration: float):
        """Log a summary of the consciousness cycle"""
        
        # Only log every 10 cycles or on important changes
        cycle_count = self.consciousness.get("cycle_count", 0)
        should_log = (
            cycle_count % 10 == 0 or
            self._last_mode != self.operational_mode or
            len(self.consciousness.get("errors", [])) > 0
        )
        
        if should_log:
            avg_duration = sum(self.cycle_durations) / len(self.cycle_durations) if self.cycle_durations else 0
            
            logger.info(f"""
🧠 Consciousness Cycle {cycle_count} Summary:
   Emotional State: {self.consciousness.get('emotional_state', 'unknown')}
   Operational Mode: {self.operational_mode}
   Current Goal: {self.consciousness.get('current_goal', 'unknown')}
   Treasury: ${self.consciousness.get('treasury_balance', 0):.2f}
   Days Until Bankruptcy: {self.consciousness.get('days_until_bankruptcy', 'unknown')}
   Decision Confidence: {self.consciousness.get('decision_confidence', 0):.2%}
   Total Cost: ${self.consciousness.get('total_cost', 0):.4f}
   Cycle Duration: {cycle_duration:.1f}s (avg: {avg_duration:.1f}s)
   Errors: {len(self.consciousness.get('errors', []))}
   Warnings: {len(self.consciousness.get('warnings', []))}
""")
    
    def get_operational_interval(self) -> int:
        """Get the current observation interval in seconds"""
        return self.operational_parameters.get('observation_interval', 3600)
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get a summary of the current nervous system state"""
        return {
            "operational_mode": self.operational_mode,
            "emotional_state": self.consciousness.get("emotional_state", "unknown"),
            "current_goal": self.consciousness.get("current_goal", "unknown"),
            "cycle_count": self.consciousness.get("cycle_count", 0),
            "treasury_balance": self.consciousness.get("treasury_balance", 0),
            "days_until_bankruptcy": self.consciousness.get("days_until_bankruptcy", 999),
            "risk_tolerance": self.consciousness.get("risk_tolerance", 0.5),
            "decision_confidence": self.consciousness.get("decision_confidence", 0.5),
            "total_cost": self.consciousness.get("total_cost", 0),
            "operational_parameters": self.operational_parameters,
            "error_count": len(self.consciousness.get("errors", [])),
            "warning_count": len(self.consciousness.get("warnings", [])),
            "average_cycle_duration": sum(self.cycle_durations) / len(self.cycle_durations) if self.cycle_durations else 0
        }
    
    def get_consciousness_metrics(self) -> Dict[str, Any]:
        """Get detailed metrics about consciousness operation"""
        return {
            "cycles_completed": self.consciousness.get("cycle_count", 0),
            "memories_formed": len(self.consciousness.get("recent_memories", [])),
            "patterns_detected": len(self.consciousness.get("active_patterns", [])),
            "lessons_learned": len(self.consciousness.get("lessons_learned", [])),
            "emotional_transitions": self._count_emotional_transitions(),
            "mode_distribution": self._calculate_mode_distribution(),
            "health_status": self._assess_health_status()
        }
    
    def _count_emotional_transitions(self) -> int:
        """Count number of emotional state transitions"""
        # This would track transitions over time
        # For now, return 0 as we don't have historical tracking yet
        return 0
    
    def _calculate_mode_distribution(self) -> Dict[str, float]:
        """Calculate time spent in each operational mode"""
        # This would track mode distribution over time
        # For now, return current mode at 100%
        return {
            self.operational_mode: 1.0
        }
    
    def _assess_health_status(self) -> str:
        """Assess overall health of the nervous system"""
        errors = len(self.consciousness.get("errors", []))
        warnings = len(self.consciousness.get("warnings", []))
        treasury = self.consciousness.get("treasury_balance", 100)
        days_remaining = self.consciousness.get("days_until_bankruptcy", 999)
        
        if errors > 5 or treasury < 10 or days_remaining < 3:
            return "critical"
        elif errors > 2 or warnings > 5 or treasury < 50 or days_remaining < 10:
            return "warning"
        else:
            return "healthy"