"""
Integration tests for the cognitive loop workflow
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timezone

from src.workflows.cognitive_loop import create_cognitive_loop
from src.workflows.consciousness import ConsciousnessState
from src.workflows.nodes import SenseNode, ThinkNode, FeelNode, DecideNode, LearnNode


@pytest.fixture
def initial_consciousness():
    """Create initial consciousness state for testing"""
    return ConsciousnessState(
        agent_id="test_agent",
        emotional_state="stable",
        market_data={},
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


@pytest.fixture
def mock_market_data():
    """Mock market data response"""
    return {
        "success": True,
        "data": {
            "BTC/USD": {
                "price": 45000,
                "change_24h": 2.5,
                "volume": 1000000
            },
            "ETH/USD": {
                "price": 3000,
                "change_24h": -1.2,
                "volume": 500000
            }
        }
    }


@pytest.fixture
def mock_wallet_balance():
    """Mock wallet balance response"""
    return {
        "total_usd": 95.0,
        "assets": {
            "ETH": {"balance": 0.01, "usd_value": 30.0},
            "USDC": {"balance": 65.0, "usd_value": 65.0}
        }
    }


@pytest.fixture
def mock_analysis_result():
    """Mock market analysis result"""
    return {
        "market_condition": "volatile",
        "market_confidence": 0.75,
        "patterns_detected": ["high_volatility", "btc_dominance"],
        "recommended_actions": ["monitor_closely", "reduce_exposure"],
        "costs_incurred": [{"type": "llm", "amount": 0.05}],
        "workflow_success": True
    }


@pytest.fixture
def mock_decision_result():
    """Mock decision result"""
    return {
        "chosen_option": "reduce_frequency",
        "decision_reasoning": "High volatility detected, conserving resources",
        "decision_confidence": 0.8,
        "expected_outcome": "Lower costs while maintaining awareness",
        "costs_incurred": [{"type": "llm", "amount": 0.03}],
        "workflow_success": True
    }


class TestCognitiveLoopCreation:
    """Test cognitive loop creation and structure"""
    
    def test_create_cognitive_loop(self):
        """Test creating the cognitive loop"""
        loop = create_cognitive_loop()
        
        assert loop is not None
        # Would test graph structure if we had access to internals
        # For now just verify it's callable
        assert hasattr(loop, 'ainvoke')


@pytest.mark.asyncio
class TestFullCognitiveLoop:
    """Test full cognitive loop execution"""
    
    async def test_complete_cycle(self, initial_consciousness, mock_market_data, 
                                 mock_wallet_balance, mock_analysis_result, 
                                 mock_decision_result):
        """Test a complete cognitive cycle with all nodes"""
        
        # Create the cognitive loop
        loop = create_cognitive_loop()
        
        # Mock all external dependencies
        with patch('src.workflows.nodes.MarketDataCollector') as MockCollector, \
             patch('src.workflows.nodes.CDPIntegration') as MockCDP, \
             patch('src.workflows.nodes.create_market_analysis_workflow') as MockAnalysis, \
             patch('src.workflows.nodes.create_decision_workflow') as MockDecision, \
             patch('src.workflows.nodes.MemoryManager') as MockMemory:
            
            # Setup sense node mocks
            mock_collector = MockCollector.return_value
            mock_collector.collect_comprehensive_market_data = AsyncMock(return_value=mock_market_data)
            
            mock_cdp = MockCDP.return_value
            mock_cdp.initialize_wallet = AsyncMock()
            mock_cdp.get_wallet_balance = AsyncMock(return_value=mock_wallet_balance)
            
            # Setup think node mocks
            mock_analysis_workflow = MagicMock()
            mock_analysis_workflow.ainvoke = AsyncMock(return_value=mock_analysis_result)
            MockAnalysis.return_value = mock_analysis_workflow
            
            # Setup decide node mocks
            mock_decision_workflow = MagicMock()
            mock_decision_workflow.ainvoke = AsyncMock(return_value=mock_decision_result)
            MockDecision.return_value = mock_decision_workflow
            
            # Setup learn node mocks
            mock_memory_manager = MockMemory.return_value
            mock_memory_manager.process_experience = AsyncMock()
            mock_memory_manager.get_relevant_memories = AsyncMock(
                return_value={"memories": [{"content": "Previous observation"}]}
            )
            mock_memory_manager.consolidate_learning = AsyncMock(
                return_value={"key_lessons": ["Volatility requires caution"]}
            )
            
            # Run the cognitive loop
            result = await loop.ainvoke(initial_consciousness)
            
            # Verify state progression
            assert result["cycle_count"] == 1
            assert result["market_data"] == mock_market_data["data"]
            assert result["treasury_balance"] == 95.0  # Updated from wallet
            assert result["active_patterns"] == ["high_volatility", "btc_dominance"]
            assert result["last_decision"]["action"] == "reduce_frequency"
            assert result["decision_confidence"] == 0.8
            assert result["total_cost"] > 0  # Costs were tracked
            
            # Verify all nodes were executed
            mock_collector.collect_comprehensive_market_data.assert_called_once()
            mock_cdp.get_wallet_balance.assert_called_once()
            mock_analysis_workflow.ainvoke.assert_called_once()
            mock_decision_workflow.ainvoke.assert_called_once()
            mock_memory_manager.process_experience.assert_called_once()
    
    async def test_cycle_with_market_data_failure(self, initial_consciousness):
        """Test cycle handling when market data collection fails"""
        
        loop = create_cognitive_loop()
        
        with patch('src.workflows.nodes.MarketDataCollector') as MockCollector, \
             patch('src.workflows.nodes.CDPIntegration') as MockCDP:
            
            # Mock failed market data collection
            mock_collector = MockCollector.return_value
            mock_collector.collect_comprehensive_market_data = AsyncMock(
                return_value={"success": False, "error": "API timeout"}
            )
            
            mock_cdp = MockCDP.return_value
            mock_cdp.initialize_wallet = AsyncMock()
            mock_cdp.get_wallet_balance = AsyncMock(
                return_value={"total_usd": 100.0}
            )
            
            # Mock other nodes to handle empty market data
            with patch('src.workflows.nodes.create_market_analysis_workflow'), \
                 patch('src.workflows.nodes.create_decision_workflow'), \
                 patch('src.workflows.nodes.MemoryManager'):
                
                result = await loop.ainvoke(initial_consciousness)
                
                # Should have warning about failed market data
                assert any("Market data collection failed" in w for w in result["warnings"])
                assert result["cycle_count"] == 1
    
    async def test_cycle_error_recovery(self, initial_consciousness):
        """Test cycle recovery from node errors"""
        
        loop = create_cognitive_loop()
        
        with patch('src.workflows.nodes.MarketDataCollector') as MockCollector:
            # Mock an exception in sense node
            mock_collector.side_effect = Exception("Network error")
            
            # The loop should handle the error gracefully
            result = await loop.ainvoke(initial_consciousness)
            
            # Should have error recorded
            assert len(result["errors"]) > 0
            assert "Sense error" in result["errors"][0]
            # But cycle should still complete
            assert result["cycle_count"] == 1


@pytest.mark.asyncio
class TestEmotionalStateTransitions:
    """Test emotional state transitions through the loop"""
    
    async def test_treasury_depletion_transition(self, initial_consciousness):
        """Test emotional state changes as treasury depletes"""
        
        loop = create_cognitive_loop()
        
        # Start with healthy treasury
        initial_consciousness["treasury_balance"] = 100.0
        
        with patch('src.workflows.nodes.MarketDataCollector'), \
             patch('src.workflows.nodes.CDPIntegration') as MockCDP, \
             patch('src.workflows.nodes.create_market_analysis_workflow'), \
             patch('src.workflows.nodes.create_decision_workflow'), \
             patch('src.workflows.nodes.MemoryManager'):
            
            mock_cdp = MockCDP.return_value
            mock_cdp.initialize_wallet = AsyncMock()
            
            # First cycle - moderate balance
            mock_cdp.get_wallet_balance = AsyncMock(
                return_value={"total_usd": 45.0}
            )
            result1 = await loop.ainvoke(initial_consciousness)
            assert result1["emotional_state"] == "cautious"
            
            # Second cycle - low balance
            mock_cdp.get_wallet_balance = AsyncMock(
                return_value={"total_usd": 20.0}
            )
            result2 = await loop.ainvoke(result1)
            assert result2["emotional_state"] == "desperate"
            assert result2["available_actions"] == ["emergency_mode", "minimize_costs", "preserve_capital"]
    
    async def test_decision_confidence_impact(self, initial_consciousness, 
                                           mock_market_data, mock_wallet_balance):
        """Test how decision confidence affects future cycles"""
        
        loop = create_cognitive_loop()
        
        with patch('src.workflows.nodes.MarketDataCollector') as MockCollector, \
             patch('src.workflows.nodes.CDPIntegration') as MockCDP, \
             patch('src.workflows.nodes.create_market_analysis_workflow') as MockAnalysis, \
             patch('src.workflows.nodes.create_decision_workflow') as MockDecision, \
             patch('src.workflows.nodes.MemoryManager'):
            
            # Setup basic mocks
            MockCollector.return_value.collect_comprehensive_market_data = AsyncMock(
                return_value=mock_market_data
            )
            MockCDP.return_value.initialize_wallet = AsyncMock()
            MockCDP.return_value.get_wallet_balance = AsyncMock(
                return_value=mock_wallet_balance
            )
            
            # Mock high confidence decision
            high_confidence_result = {
                "chosen_option": "active_monitoring",
                "decision_confidence": 0.95,
                "costs_incurred": []
            }
            MockDecision.return_value.ainvoke = AsyncMock(
                return_value=high_confidence_result
            )
            
            # Default analysis mock
            MockAnalysis.return_value.ainvoke = AsyncMock(
                return_value={"patterns_detected": [], "costs_incurred": []}
            )
            
            result = await loop.ainvoke(initial_consciousness)
            
            assert result["decision_confidence"] == 0.95
            assert result["last_decision"]["confidence"] == 0.95


@pytest.mark.asyncio
class TestMemoryIntegration:
    """Test memory formation and retrieval in the loop"""
    
    async def test_memory_formation(self, initial_consciousness):
        """Test that experiences are properly formed into memories"""
        
        loop = create_cognitive_loop()
        
        with patch('src.workflows.nodes.MarketDataCollector'), \
             patch('src.workflows.nodes.CDPIntegration'), \
             patch('src.workflows.nodes.create_market_analysis_workflow'), \
             patch('src.workflows.nodes.create_decision_workflow'), \
             patch('src.workflows.nodes.MemoryManager') as MockMemory:
            
            mock_memory_manager = MockMemory.return_value
            mock_memory_manager.process_experience = AsyncMock()
            mock_memory_manager.get_relevant_memories = AsyncMock(
                return_value={"memories": []}
            )
            
            # Run cycle
            await loop.ainvoke(initial_consciousness)
            
            # Verify experience was processed
            mock_memory_manager.process_experience.assert_called_once()
            call_args = mock_memory_manager.process_experience.call_args[0][0]
            
            assert call_args["type"] == "consciousness_cycle"
            assert "timestamp" in call_args
            assert "emotional_state" in call_args
            assert "treasury_balance" in call_args
            assert "decision" in call_args
    
    async def test_memory_consolidation(self, initial_consciousness):
        """Test memory consolidation every 10 cycles"""
        
        loop = create_cognitive_loop()
        
        # Set cycle count to trigger consolidation
        initial_consciousness["cycle_count"] = 9  # Will become 10 after increment
        
        with patch('src.workflows.nodes.MarketDataCollector'), \
             patch('src.workflows.nodes.CDPIntegration'), \
             patch('src.workflows.nodes.create_market_analysis_workflow'), \
             patch('src.workflows.nodes.create_decision_workflow'), \
             patch('src.workflows.nodes.MemoryManager') as MockMemory:
            
            mock_memory_manager = MockMemory.return_value
            mock_memory_manager.process_experience = AsyncMock()
            mock_memory_manager.get_relevant_memories = AsyncMock(
                return_value={"memories": []}
            )
            mock_memory_manager.consolidate_learning = AsyncMock(
                return_value={"key_lessons": ["Test lesson 1", "Test lesson 2"]}
            )
            
            result = await loop.ainvoke(initial_consciousness)
            
            # Verify consolidation was called
            mock_memory_manager.consolidate_learning.assert_called_once()
            assert result["lessons_learned"] == ["Test lesson 1", "Test lesson 2"]
            assert result["cycle_count"] == 10


@pytest.mark.asyncio
class TestCostTracking:
    """Test cost tracking through the cognitive loop"""
    
    async def test_cumulative_cost_tracking(self, initial_consciousness):
        """Test that costs accumulate correctly through the loop"""
        
        loop = create_cognitive_loop()
        
        with patch('src.workflows.nodes.MarketDataCollector') as MockCollector, \
             patch('src.workflows.nodes.CDPIntegration') as MockCDP, \
             patch('src.workflows.nodes.create_market_analysis_workflow') as MockAnalysis, \
             patch('src.workflows.nodes.create_decision_workflow') as MockDecision, \
             patch('src.workflows.nodes.MemoryManager'):
            
            # Setup mocks
            MockCollector.return_value.collect_comprehensive_market_data = AsyncMock(
                return_value={"success": True, "data": {}}
            )
            MockCDP.return_value.initialize_wallet = AsyncMock()
            MockCDP.return_value.get_wallet_balance = AsyncMock(
                return_value={"total_usd": 100.0}
            )
            
            # Mock costs from different nodes
            MockAnalysis.return_value.ainvoke = AsyncMock(
                return_value={
                    "patterns_detected": [],
                    "costs_incurred": [{"type": "llm", "amount": 0.05}]
                }
            )
            MockDecision.return_value.ainvoke = AsyncMock(
                return_value={
                    "chosen_option": "maintain_current",
                    "decision_confidence": 0.5,
                    "costs_incurred": [{"type": "llm", "amount": 0.03}]
                }
            )
            
            result = await loop.ainvoke(initial_consciousness)
            
            # Base cost (0.02) + analysis (0.05) + decision (0.03) = 0.10
            assert result["total_cost"] == 0.10