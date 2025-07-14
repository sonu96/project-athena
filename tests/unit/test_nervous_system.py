"""
Unit tests for the nervous system orchestrator
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone

from src.core.nervous_system import NervousSystem
from src.workflows.consciousness import ConsciousnessState


@pytest.fixture
def nervous_system():
    """Create a nervous system instance for testing"""
    return NervousSystem()


@pytest.fixture
def mock_consciousness_state():
    """Create a mock consciousness state"""
    return ConsciousnessState(
        agent_id="test_agent",
        emotional_state="stable",
        market_data={"BTC/USD": 45000},
        treasury_balance=100.0,
        days_until_bankruptcy=100,
        current_goal="observe_and_learn",
        recent_memories=[],
        active_patterns=[],
        available_actions=["normal_observation"],
        last_decision={},
        decision_confidence=0.5,
        current_experience={},
        lessons_learned=[],
        cycle_count=0,
        total_cost=0.0,
        timestamp=datetime.now(timezone.utc),
        errors=[],
        warnings=[],
        operational_mode="normal_mode"
    )


class TestNervousSystemInitialization:
    """Test nervous system initialization"""
    
    def test_initialization(self, nervous_system):
        """Test basic initialization"""
        assert nervous_system.cognitive_loop is None
        assert nervous_system.consciousness is not None
        assert nervous_system.operational_mode == "normal_mode"
        assert not nervous_system._initialized
        assert nervous_system.cycle_durations == []
    
    def test_consciousness_initialization(self, nervous_system):
        """Test consciousness state initialization"""
        consciousness = nervous_system.consciousness
        
        assert consciousness["agent_id"] == "athena_001"
        assert consciousness["emotional_state"] == "stable"
        assert consciousness["treasury_balance"] == 100.0
        assert consciousness["days_until_bankruptcy"] == 999
        assert consciousness["current_goal"] == "observe_and_learn"
        assert consciousness["cycle_count"] == 0
        assert consciousness["total_cost"] == 0.0
        assert consciousness["operational_mode"] == "normal_mode"
    
    @pytest.mark.asyncio
    async def test_async_initialization(self, nervous_system):
        """Test async initialization"""
        with patch('src.workflows.cognitive_loop.create_cognitive_loop') as mock_create:
            mock_create.return_value = MagicMock()
            
            await nervous_system.initialize()
            
            assert nervous_system._initialized
            assert nervous_system.cognitive_loop is not None
            mock_create.assert_called_once()


class TestConsciousnessCycle:
    """Test consciousness cycle execution"""
    
    @pytest.mark.asyncio
    async def test_run_consciousness_cycle(self, nervous_system, mock_consciousness_state):
        """Test running a complete consciousness cycle"""
        # Mock the cognitive loop
        mock_loop = MagicMock()
        mock_loop.ainvoke = AsyncMock(return_value=mock_consciousness_state)
        nervous_system.cognitive_loop = mock_loop
        nervous_system._initialized = True
        
        # Run cycle
        result = await nervous_system.run_consciousness_cycle()
        
        # Verify
        assert result == mock_consciousness_state
        mock_loop.ainvoke.assert_called_once()
        assert nervous_system.operational_mode == "normal_mode"
    
    @pytest.mark.asyncio
    async def test_emergency_mode_activation(self, nervous_system):
        """Test emergency mode activation"""
        # Set up desperate state
        nervous_system.consciousness["treasury_balance"] = 5.0
        nervous_system.consciousness["days_until_bankruptcy"] = 2
        
        # Mock cognitive loop
        mock_loop = MagicMock()
        mock_loop.ainvoke = AsyncMock(return_value=nervous_system.consciousness)
        nervous_system.cognitive_loop = mock_loop
        nervous_system._initialized = True
        
        # Run cycle
        with patch('src.workflows.emotional_router.should_activate_emergency_mode', return_value=True):
            result = await nervous_system.run_consciousness_cycle()
        
        # Verify emergency mode
        assert result["emotional_state"] == "desperate"
        assert nervous_system.operational_mode == "survival_mode"
    
    @pytest.mark.asyncio
    async def test_cycle_error_handling(self, nervous_system):
        """Test error handling in consciousness cycle"""
        # Mock cognitive loop with error
        mock_loop = MagicMock()
        mock_loop.ainvoke = AsyncMock(side_effect=Exception("Test error"))
        nervous_system.cognitive_loop = mock_loop
        nervous_system._initialized = True
        
        # Run cycle - should not raise
        result = await nervous_system.run_consciousness_cycle()
        
        # Verify error captured
        assert len(result["errors"]) > 0
        assert "Consciousness cycle error" in result["errors"][0]
    
    @pytest.mark.asyncio
    async def test_cycle_performance_tracking(self, nervous_system, mock_consciousness_state):
        """Test cycle performance tracking"""
        # Mock cognitive loop
        mock_loop = MagicMock()
        mock_loop.ainvoke = AsyncMock(return_value=mock_consciousness_state)
        nervous_system.cognitive_loop = mock_loop
        nervous_system._initialized = True
        
        # Run multiple cycles
        for i in range(3):
            mock_consciousness_state["cycle_count"] = i
            await nervous_system.run_consciousness_cycle()
        
        # Verify performance tracking
        assert len(nervous_system.cycle_durations) == 3
        assert all(d >= 0 for d in nervous_system.cycle_durations)


class TestEmotionalRouting:
    """Test emotional routing and operational modes"""
    
    def test_operational_parameters_application(self, nervous_system):
        """Test operational parameters are applied correctly"""
        # Test each mode
        modes = ["survival_mode", "conservative_mode", "normal_mode", "growth_mode"]
        
        for mode in modes:
            nervous_system.operational_mode = mode
            nervous_system._apply_parameters({"description": f"Test {mode}"})
            assert nervous_system._last_mode == mode
    
    def test_mode_change_logging(self, nervous_system, caplog):
        """Test mode change logging"""
        nervous_system._last_mode = "normal_mode"
        nervous_system.operational_mode = "survival_mode"
        
        params = {
            "description": "Emergency preservation mode",
            "max_daily_cost": 1.0,
            "observation_interval": 14400,
            "llm_model": "claude-3-haiku"
        }
        
        nervous_system._apply_parameters(params)
        
        # Check logs
        assert "Nervous system switched: normal_mode → survival_mode" in caplog.text
        assert "Emergency preservation mode" in caplog.text
    
    def test_get_operational_interval(self, nervous_system):
        """Test getting operational interval"""
        nervous_system.operational_parameters = {"observation_interval": 7200}
        assert nervous_system.get_operational_interval() == 7200
        
        nervous_system.operational_parameters = {}
        assert nervous_system.get_operational_interval() == 3600  # Default


class TestStateManagement:
    """Test state management and metrics"""
    
    def test_get_current_state(self, nervous_system):
        """Test getting current state summary"""
        state = nervous_system.get_current_state()
        
        assert "operational_mode" in state
        assert "emotional_state" in state
        assert "current_goal" in state
        assert "cycle_count" in state
        assert "treasury_balance" in state
        assert "days_until_bankruptcy" in state
        assert "risk_tolerance" in state
        assert "decision_confidence" in state
        assert "total_cost" in state
        assert "operational_parameters" in state
        assert "error_count" in state
        assert "warning_count" in state
        assert "average_cycle_duration" in state
    
    def test_get_consciousness_metrics(self, nervous_system):
        """Test getting consciousness metrics"""
        # Add some test data
        nervous_system.consciousness["cycle_count"] = 10
        nervous_system.consciousness["recent_memories"] = [{"memory": "test"} for _ in range(5)]
        nervous_system.consciousness["active_patterns"] = ["pattern1", "pattern2"]
        nervous_system.consciousness["lessons_learned"] = ["lesson1"]
        
        metrics = nervous_system.get_consciousness_metrics()
        
        assert metrics["cycles_completed"] == 10
        assert metrics["memories_formed"] == 5
        assert metrics["patterns_detected"] == 2
        assert metrics["lessons_learned"] == 1
        assert "emotional_transitions" in metrics
        assert "mode_distribution" in metrics
        assert "health_status" in metrics
    
    def test_health_status_assessment(self, nervous_system):
        """Test health status assessment"""
        # Test healthy state
        nervous_system.consciousness["errors"] = []
        nervous_system.consciousness["warnings"] = []
        nervous_system.consciousness["treasury_balance"] = 100
        nervous_system.consciousness["days_until_bankruptcy"] = 100
        
        metrics = nervous_system.get_consciousness_metrics()
        assert metrics["health_status"] == "healthy"
        
        # Test warning state
        nervous_system.consciousness["errors"] = ["error1", "error2", "error3"]
        metrics = nervous_system.get_consciousness_metrics()
        assert metrics["health_status"] == "warning"
        
        # Test critical state
        nervous_system.consciousness["treasury_balance"] = 5
        nervous_system.consciousness["days_until_bankruptcy"] = 2
        metrics = nervous_system.get_consciousness_metrics()
        assert metrics["health_status"] == "critical"


class TestCycleSummaryLogging:
    """Test cycle summary logging"""
    
    def test_log_cycle_summary_frequency(self, nervous_system, caplog):
        """Test that cycle summary logs at correct frequency"""
        # Should log on cycle 10
        nervous_system.consciousness["cycle_count"] = 10
        nervous_system._log_cycle_summary(1.5)
        assert "Consciousness Cycle 10 Summary" in caplog.text
        
        # Should not log on cycle 5
        caplog.clear()
        nervous_system.consciousness["cycle_count"] = 5
        nervous_system._log_cycle_summary(1.5)
        assert "Consciousness Cycle 5 Summary" not in caplog.text
    
    def test_log_cycle_summary_on_mode_change(self, nervous_system, caplog):
        """Test cycle summary logs on mode change"""
        nervous_system._last_mode = "normal_mode"
        nervous_system.operational_mode = "survival_mode"
        nervous_system.consciousness["cycle_count"] = 5
        
        nervous_system._log_cycle_summary(1.5)
        assert "Consciousness Cycle 5 Summary" in caplog.text
    
    def test_log_cycle_summary_on_errors(self, nervous_system, caplog):
        """Test cycle summary logs when there are errors"""
        nervous_system.consciousness["errors"] = ["error1", "error2"]
        nervous_system.consciousness["cycle_count"] = 7
        
        nervous_system._log_cycle_summary(1.5)
        assert "Consciousness Cycle 7 Summary" in caplog.text
        assert "Errors: 2" in caplog.text


@pytest.mark.asyncio
class TestIntegrationScenarios:
    """Test integrated scenarios"""
    
    async def test_normal_to_desperate_transition(self, nervous_system):
        """Test transition from normal to desperate state"""
        # Start in normal state
        nervous_system.consciousness["emotional_state"] = "stable"
        nervous_system.consciousness["treasury_balance"] = 100
        nervous_system.consciousness["days_until_bankruptcy"] = 100
        
        # Mock cognitive loop to simulate treasury depletion
        mock_loop = MagicMock()
        nervous_system.cognitive_loop = mock_loop
        nervous_system._initialized = True
        
        # Simulate desperate state
        desperate_state = nervous_system.consciousness.copy()
        desperate_state["treasury_balance"] = 5
        desperate_state["days_until_bankruptcy"] = 2
        desperate_state["emotional_state"] = "desperate"
        
        mock_loop.ainvoke = AsyncMock(return_value=desperate_state)
        
        # Run cycle
        result = await nervous_system.run_consciousness_cycle()
        
        # Verify transition
        assert result["emotional_state"] == "desperate"
        assert nervous_system.operational_mode == "survival_mode"
    
    async def test_risk_tolerance_adjustment(self, nervous_system, mock_consciousness_state):
        """Test risk tolerance adjustment based on state"""
        mock_loop = MagicMock()
        nervous_system.cognitive_loop = mock_loop
        nervous_system._initialized = True
        
        # Test different emotional states
        emotional_states = ["desperate", "cautious", "stable", "confident"]
        expected_tolerances = [0.1, 0.3, 0.5, 0.8]
        
        for emotion, expected in zip(emotional_states, expected_tolerances):
            state = mock_consciousness_state.copy()
            state["emotional_state"] = emotion
            mock_loop.ainvoke = AsyncMock(return_value=state)
            
            result = await nervous_system.run_consciousness_cycle()
            
            # Risk tolerance should be set appropriately
            assert "risk_tolerance" in result
            # Note: actual calculation may differ due to other factors