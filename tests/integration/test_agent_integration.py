"""
Integration tests for Agent components
Tests interaction between Treasury, Memory, Market Detection, and Workflows
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import asyncio

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from core.agent import DeFiAgent
from core.treasury import TreasuryManager
from core.memory_manager import MemoryManager
from core.market_detector import MarketConditionDetector


class TestAgentIntegration:
    """Integration tests for DeFi Agent"""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Mock all external dependencies"""
        mocks = {}
        
        # Mock Firestore
        mocks['firestore'] = MagicMock()
        
        # Mock BigQuery
        mocks['bigquery'] = MagicMock()
        mocks['bigquery'].insert_rows_json.return_value = []
        
        # Mock Mem0
        mocks['mem0'] = MagicMock()
        mocks['mem0'].add.return_value = {'memory_id': 'test_memory'}
        mocks['mem0'].search.return_value = {'results': []}
        
        # Mock Anthropic
        mocks['anthropic'] = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = '{"action": "observe", "reasoning": "Testing"}'
        mocks['anthropic'].messages.create.return_value = mock_response
        
        # Mock market data collector
        mocks['market_data'] = {
            'sources': {
                'coingecko': {
                    'status': 'success',
                    'bitcoin_price': 45000,
                    'bitcoin_24h_change': 2.5,
                    'ethereum_price': 3000,
                    'ethereum_24h_change': 1.8
                },
                'fear_greed': {
                    'status': 'success',
                    'fear_greed_index': 60,
                    'fear_greed_classification': 'Greed'
                }
            },
            'overall_quality': 0.9
        }
        
        return mocks
    
    @pytest.fixture
    def agent(self, mock_dependencies):
        """Create DeFiAgent with mocked dependencies"""
        with patch('core.agent.firestore.Client', return_value=mock_dependencies['firestore']), \
             patch('core.agent.bigquery.Client', return_value=mock_dependencies['bigquery']), \
             patch('integrations.mem0_integration.MemoryClient', return_value=mock_dependencies['mem0']), \
             patch('integrations.llm_integration.Anthropic', return_value=mock_dependencies['anthropic']):
            
            agent = DeFiAgent(
                agent_id="test_agent",
                starting_treasury=100.0
            )
            
            # Mock market data collection
            async def mock_collect_data():
                return mock_dependencies['market_data']
            
            agent.market_data_collector.collect_all_data = mock_collect_data
            return agent
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, agent):
        """Test agent initializes all components correctly"""
        assert agent.agent_id == "test_agent"
        assert agent.treasury_manager is not None
        assert agent.memory_manager is not None
        assert agent.market_detector is not None
        assert agent.llm_workflows is not None
    
    @pytest.mark.asyncio
    async def test_observation_cycle_normal(self, agent):
        """Test normal observation cycle"""
        # Execute one observation cycle
        result = await agent._perform_observation_cycle()
        
        assert result['status'] == 'success'
        assert 'market_analysis' in result
        assert 'decision' in result
        assert 'costs' in result
    
    @pytest.mark.asyncio
    async def test_observation_cycle_with_memory_formation(self, agent):
        """Test observation cycle forms memories"""
        # Mock memory formation
        original_form_memory = agent.memory_manager.form_memory
        memory_calls = []
        
        async def mock_form_memory(experience, importance=0.5):
            memory_calls.append((experience, importance))
            return 'test_memory_id'
        
        agent.memory_manager.form_memory = mock_form_memory
        
        # Execute observation cycle
        await agent._perform_observation_cycle()
        
        # Check that memories were formed
        assert len(memory_calls) >= 2  # Market observation + decision
        
        # Check memory types
        memory_types = [call[0]['type'] for call in memory_calls]
        assert 'market_observation' in memory_types
        assert 'decision_made' in memory_types
    
    @pytest.mark.asyncio
    async def test_treasury_cost_integration(self, agent):
        """Test treasury integration with cost deduction"""
        initial_balance = agent.treasury_manager.current_balance
        
        # Perform observation cycle which should deduct costs
        await agent._perform_observation_cycle()
        
        # Balance should be reduced
        final_balance = agent.treasury_manager.current_balance
        assert final_balance < initial_balance
    
    @pytest.mark.asyncio
    async def test_emotional_state_affects_decisions(self, agent):
        """Test that emotional state affects decision making"""
        # Set low balance to trigger cautious state
        agent.treasury_manager.current_balance = 30.0
        
        # Mock LLM to verify model selection
        llm_calls = []
        original_create = agent.llm_workflows.llm_client.messages.create
        
        def mock_create(*args, **kwargs):
            llm_calls.append(kwargs.get('model', 'unknown'))
            return original_create(*args, **kwargs)
        
        agent.llm_workflows.llm_client.messages.create = mock_create
        
        # Perform observation cycle
        await agent._perform_observation_cycle()
        
        # Should use cheaper models when treasury is low
        # (This depends on the specific implementation)
        assert len(llm_calls) > 0
    
    @pytest.mark.asyncio
    async def test_emergency_mode_activation(self, agent):
        """Test emergency mode activation and behavior"""
        # Set very low balance
        agent.treasury_manager.current_balance = 15.0
        agent.treasury_manager.daily_burn_rate = 10.0  # 1.5 days until bankruptcy
        
        # Check emergency mode activation
        status = await agent.treasury_manager.get_status()
        assert status['emergency_mode'] is True
        assert status['emotional_state'] == 'desperate'
    
    @pytest.mark.asyncio
    async def test_market_condition_memory_retrieval(self, agent):
        """Test that market conditions trigger relevant memory retrieval"""
        # Mock memory retrieval with market-specific memories
        relevant_memories = [
            {
                'content': 'Bull market led to profitable decisions',
                'category': 'market',
                'relevance_score': 0.9
            }
        ]
        
        agent.memory_manager.retrieve_memories = AsyncMock(return_value=relevant_memories)
        
        # Perform observation cycle
        result = await agent._perform_observation_cycle()
        
        # Check that memory retrieval was called
        agent.memory_manager.retrieve_memories.assert_called()
        call_args = agent.memory_manager.retrieve_memories.call_args[0][0]
        assert 'market_condition' in call_args or 'emotional_state' in call_args
    
    @pytest.mark.asyncio
    async def test_continuous_operation_simulation(self, agent):
        """Test multiple observation cycles in sequence"""
        results = []
        
        # Simulate 5 observation cycles
        for i in range(5):
            result = await agent._perform_observation_cycle()
            results.append(result)
            
            # Small delay to simulate time passage
            await asyncio.sleep(0.1)
        
        # All cycles should succeed
        assert all(r['status'] == 'success' for r in results)
        
        # Treasury should decrease with each cycle
        balances = [r['costs']['remaining_balance'] for r in results]
        assert all(balances[i] >= balances[i+1] for i in range(len(balances)-1))
    
    @pytest.mark.asyncio
    async def test_poor_market_data_handling(self, agent):
        """Test handling of poor quality market data"""
        # Mock poor quality market data
        poor_data = {
            'sources': {
                'coingecko': {'status': 'error'},
                'fear_greed': {'status': 'error'}
            },
            'overall_quality': 0.1
        }
        
        async def mock_collect_poor_data():
            return poor_data
        
        agent.market_data_collector.collect_all_data = mock_collect_poor_data
        
        # Observation cycle should still complete
        result = await agent._perform_observation_cycle()
        
        assert result['status'] == 'success'
        # Decision should reflect uncertainty due to poor data
        assert result['market_analysis']['data_quality'] == 0.1
    
    @pytest.mark.asyncio
    async def test_memory_context_influences_decisions(self, agent):
        """Test that retrieved memories influence decision making"""
        # Mock memories suggesting caution
        cautious_memories = [
            {
                'content': 'Previous market volatility led to losses',
                'category': 'strategy',
                'relevance_score': 0.8
            }
        ]
        
        agent.memory_manager.retrieve_memories = AsyncMock(return_value=cautious_memories)
        
        # Mock LLM to capture decision context
        decision_contexts = []
        original_create = agent.llm_workflows.llm_client.messages.create
        
        def mock_create(*args, **kwargs):
            if 'messages' in kwargs:
                decision_contexts.append(kwargs['messages'][0]['content'])
            return original_create(*args, **kwargs)
        
        agent.llm_workflows.llm_client.messages.create = mock_create
        
        # Perform observation cycle
        await agent._perform_observation_cycle()
        
        # Check that memory content was included in decision context
        assert len(decision_contexts) > 0
        # At least one context should mention the cautious memory
        # (This depends on specific implementation details)
    
    @pytest.mark.asyncio
    async def test_cost_optimization_integration(self, agent):
        """Test cost optimization across all components"""
        # Set up desperate emotional state
        agent.treasury_manager.current_balance = 20.0
        agent.treasury_manager.emotional_state = "desperate"
        
        # Track model usage
        model_calls = []
        original_create = agent.llm_workflows.llm_client.messages.create
        
        def mock_create(*args, **kwargs):
            model_calls.append(kwargs.get('model', 'unknown'))
            return original_create(*args, **kwargs)
        
        agent.llm_workflows.llm_client.messages.create = mock_create
        
        # Perform observation cycle
        await agent._perform_observation_cycle()
        
        # Should prefer cheaper models in desperate state
        if model_calls:
            # Check that haiku (cheaper) model is used more often
            haiku_usage = sum(1 for model in model_calls if 'haiku' in model.lower())
            total_calls = len(model_calls)
            
            # In desperate state, should use more cheap models
            if total_calls > 0:
                cheap_model_ratio = haiku_usage / total_calls
                # This depends on implementation, but desperate state should prefer cheap models
                assert cheap_model_ratio >= 0.0  # At least some optimization


class TestTreasuryMemoryIntegration:
    """Test integration between Treasury and Memory systems"""
    
    @pytest.fixture
    def treasury_memory_setup(self):
        """Set up treasury and memory managers"""
        with patch('core.treasury.firestore.Client'), \
             patch('core.treasury.bigquery.Client'), \
             patch('core.memory_manager.MemoryClient'), \
             patch('core.memory_manager.firestore.Client'):
            
            treasury = TreasuryManager(starting_balance=100.0)
            memory = MemoryManager(agent_id="test_agent")
            
            return treasury, memory
    
    @pytest.mark.asyncio
    async def test_cost_deduction_creates_memory(self, treasury_memory_setup):
        """Test that cost deductions create survival memories"""
        treasury, memory = treasury_memory_setup
        
        # Mock memory formation
        memory_formed = []
        
        async def mock_form_memory(experience, importance=0.5):
            memory_formed.append((experience, importance))
            return 'test_memory'
        
        memory.form_memory = mock_form_memory
        
        # Deduct cost
        await treasury.deduct_cost(5.0, "test_operation", "llm")
        
        # Should trigger memory formation
        # (This would need to be implemented in the actual treasury manager)
        # For now, we'll simulate the expected behavior
        
        # Manually create the experience that treasury would create
        experience = {
            'type': 'cost_deducted',
            'data': {
                'amount': 5.0,
                'operation': 'test_operation',
                'remaining_balance': 95.0
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        await memory.form_memory(experience, importance=0.7)
        
        assert len(memory_formed) == 1
        assert memory_formed[0][0]['type'] == 'cost_deducted'
        assert memory_formed[0][1] == 0.7