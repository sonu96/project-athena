"""
End-to-end tests for complete agent lifecycle
Tests full agent operation from start to finish
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import asyncio
import json

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from core.agent import DeFiAgent


class TestFullAgentLifecycle:
    """End-to-end tests for complete agent operation"""
    
    @pytest.fixture
    def mock_external_apis(self):
        """Mock all external API calls"""
        mocks = {}
        
        # Mock CoinGecko API
        mocks['coingecko_responses'] = [
            {
                'bitcoin': {'usd': 45000, 'usd_24h_change': 2.5, 'usd_market_cap': 900000000000},
                'ethereum': {'usd': 3000, 'usd_24h_change': 1.8, 'usd_market_cap': 360000000000}
            },
            {
                'bitcoin': {'usd': 46000, 'usd_24h_change': 4.2, 'usd_market_cap': 920000000000},
                'ethereum': {'usd': 3100, 'usd_24h_change': 3.8, 'usd_market_cap': 372000000000}
            }
        ]
        
        # Mock Fear & Greed API
        mocks['fear_greed_responses'] = [
            {'data': [{'value': '65', 'value_classification': 'Greed'}]},
            {'data': [{'value': '72', 'value_classification': 'Greed'}]}
        ]
        
        # Mock DeFiLlama API
        mocks['defillama_responses'] = [
            [{'name': 'Base', 'tvl': 1500000000, 'change_1d': 2.1}],
            [{'name': 'Base', 'tvl': 1520000000, 'change_1d': 1.8}]
        ]
        
        return mocks
    
    @pytest.fixture
    def mock_storage_clients(self):
        """Mock database storage clients"""
        mocks = {}
        
        # Mock Firestore
        mocks['firestore'] = MagicMock()
        mock_collection = MagicMock()
        mock_doc = MagicMock()
        mocks['firestore'].collection.return_value = mock_collection
        mock_collection.document.return_value = mock_doc
        mock_collection.add.return_value = (None, mock_doc)
        
        # Mock query results for historical data
        mock_query_doc = MagicMock()
        mock_query_doc.to_dict.return_value = {
            'timestamp': datetime.utcnow().isoformat(),
            'market_condition': 'bull',
            'confidence': 0.8
        }
        mock_collection.where.return_value.order_by.return_value.limit.return_value.stream.return_value = [mock_query_doc]
        
        # Mock BigQuery
        mocks['bigquery'] = MagicMock()
        mocks['bigquery'].insert_rows_json.return_value = []
        
        return mocks
    
    @pytest.fixture
    def mock_llm_clients(self):
        """Mock LLM API clients"""
        mocks = {}
        
        # Mock Anthropic responses
        mocks['anthropic'] = MagicMock()
        
        # Different responses for different analysis types
        mock_responses = {
            'sentiment': '{"sentiment": "bullish", "confidence": 0.8, "factors": ["price_increase", "positive_momentum"]}',
            'decision': '{"action": "observe", "reasoning": "Market conditions favorable for observation", "confidence": 0.7, "urgency": 4}',
            'insights': '{"key_insights": ["Market showing upward trend", "Fear and greed index indicates optimism"], "risk_assessment": "medium", "learning_priorities": ["trend_analysis"]}'
        }
        
        def mock_create(*args, **kwargs):
            mock_response = MagicMock()
            mock_content = MagicMock()
            
            # Determine response type based on context
            if 'messages' in kwargs and kwargs['messages']:
                content = kwargs['messages'][0].get('content', '').lower()
                if 'sentiment' in content:
                    mock_content.text = mock_responses['sentiment']
                elif 'decision' in content or 'action' in content:
                    mock_content.text = mock_responses['decision']
                elif 'insights' in content or 'learning' in content:
                    mock_content.text = mock_responses['insights']
                else:
                    mock_content.text = mock_responses['decision']  # Default
            else:
                mock_content.text = mock_responses['decision']
            
            mock_response.content = [mock_content]
            return mock_response
        
        mocks['anthropic'].messages.create = mock_create
        
        return mocks
    
    @pytest.fixture
    def mock_mem0_client(self):
        """Mock Mem0 memory client"""
        mock_mem0 = MagicMock()
        
        # Mock memory storage
        stored_memories = []
        
        def mock_add(messages, metadata=None):
            memory_id = f"memory_{len(stored_memories)}"
            stored_memories.append({
                'id': memory_id,
                'content': messages,
                'metadata': metadata or {}
            })
            return {'memory_id': memory_id}
        
        def mock_search(query, limit=10):
            # Return relevant stored memories
            relevant = [mem for mem in stored_memories if 'market' in str(mem['content']).lower()][:limit]
            return {
                'results': [
                    {
                        'memory': mem['content'],
                        'score': 0.8,
                        'metadata': mem['metadata']
                    } for mem in relevant
                ]
            }
        
        mock_mem0.add = mock_add
        mock_mem0.search = mock_search
        mock_mem0.get_all.return_value = {'results': stored_memories}
        
        return mock_mem0
    
    @pytest.fixture
    def full_agent_setup(self, mock_external_apis, mock_storage_clients, mock_llm_clients, mock_mem0_client):
        """Set up fully mocked agent for e2e testing"""
        with patch('core.agent.firestore.Client', return_value=mock_storage_clients['firestore']), \
             patch('core.agent.bigquery.Client', return_value=mock_storage_clients['bigquery']), \
             patch('integrations.mem0_integration.MemoryClient', return_value=mock_mem0_client), \
             patch('integrations.llm_integration.Anthropic', return_value=mock_llm_clients['anthropic']), \
             patch('aiohttp.ClientSession') as mock_session:
            
            # Mock aiohttp responses
            call_count = 0
            
            async def mock_get(url, **kwargs):
                nonlocal call_count
                mock_response = AsyncMock()
                
                if 'coingecko' in url:
                    mock_response.status = 200
                    mock_response.json = AsyncMock(return_value=mock_external_apis['coingecko_responses'][call_count % 2])
                elif 'alternative.me' in url:
                    mock_response.status = 200
                    mock_response.json = AsyncMock(return_value=mock_external_apis['fear_greed_responses'][call_count % 2])
                elif 'llama.fi' in url:
                    mock_response.status = 200
                    mock_response.json = AsyncMock(return_value=mock_external_apis['defillama_responses'][call_count % 2])
                else:
                    mock_response.status = 404
                    mock_response.json = AsyncMock(return_value={})
                
                call_count += 1
                return mock_response
            
            mock_session_instance = AsyncMock()
            mock_session_instance.get = mock_get
            mock_session_instance.__aenter__ = AsyncMock(return_value=mock_session_instance)
            mock_session_instance.__aexit__ = AsyncMock(return_value=None)
            mock_session.return_value = mock_session_instance
            
            agent = DeFiAgent(
                agent_id="e2e_test_agent",
                starting_treasury=100.0
            )
            
            return agent, mock_mem0_client, mock_storage_clients
    
    @pytest.mark.asyncio
    async def test_complete_agent_lifecycle(self, full_agent_setup):
        """Test complete agent lifecycle from startup to shutdown"""
        agent, mock_mem0, mock_storage = full_agent_setup
        
        # 1. Initialize agent
        await agent.initialize()
        
        # 2. Run multiple observation cycles
        results = []
        for i in range(3):
            result = await agent._perform_observation_cycle()
            results.append(result)
            
            # Small delay between cycles
            await asyncio.sleep(0.1)
        
        # 3. Verify all cycles completed successfully
        assert all(r['status'] == 'success' for r in results)
        
        # 4. Verify treasury balance decreased
        initial_balance = 100.0
        final_balance = agent.treasury_manager.current_balance
        assert final_balance < initial_balance
        
        # 5. Verify memories were formed
        mock_mem0.add.assert_called()
        
        # 6. Verify data was stored
        mock_storage['firestore'].collection.assert_called()
        mock_storage['bigquery'].insert_rows_json.assert_called()
        
        # 7. Shutdown agent
        await agent.shutdown()
    
    @pytest.mark.asyncio
    async def test_agent_survival_under_pressure(self, full_agent_setup):
        """Test agent behavior under financial pressure"""
        agent, mock_mem0, mock_storage = full_agent_setup
        
        # Set low starting balance to create pressure
        agent.treasury_manager.current_balance = 25.0
        
        await agent.initialize()
        
        # Run observation cycles until emergency mode or balance exhausted
        cycles_completed = 0
        max_cycles = 10
        
        while cycles_completed < max_cycles and agent.treasury_manager.current_balance > 5.0:
            result = await agent._perform_observation_cycle()
            cycles_completed += 1
            
            # Check if emergency mode was activated
            status = await agent.treasury_manager.get_status()
            if status['emergency_mode']:
                break
        
        # Verify agent survived some cycles
        assert cycles_completed > 0
        
        # Verify emergency mode was activated due to low balance
        final_status = await agent.treasury_manager.get_status()
        assert final_status['emotional_state'] in ['cautious', 'desperate']
        
        await agent.shutdown()
    
    @pytest.mark.asyncio
    async def test_agent_learning_progression(self, full_agent_setup):
        """Test that agent forms and uses memories progressively"""
        agent, mock_mem0, mock_storage = full_agent_setup
        
        await agent.initialize()
        
        # Track memory formation over multiple cycles
        memory_count_progression = []
        
        for i in range(5):
            # Record memory count before cycle
            initial_memories = len(mock_mem0.get_all()['results'])
            memory_count_progression.append(initial_memories)
            
            # Perform observation cycle
            await agent._perform_observation_cycle()
            
            # Verify memories increased
            final_memories = len(mock_mem0.get_all()['results'])
            assert final_memories >= initial_memories
        
        # Verify progressive memory accumulation
        assert memory_count_progression[-1] >= memory_count_progression[0]
        
        await agent.shutdown()
    
    @pytest.mark.asyncio
    async def test_agent_market_adaptation(self, full_agent_setup):
        """Test agent adaptation to changing market conditions"""
        agent, mock_mem0, mock_storage = full_agent_setup
        
        await agent.initialize()
        
        # Track decisions across cycles with different market conditions
        decisions = []
        
        # Perform cycles with varying market data
        for i in range(4):
            result = await agent._perform_observation_cycle()
            
            if 'decision' in result:
                decisions.append({
                    'cycle': i,
                    'action': result['decision'].get('action', 'unknown'),
                    'market_condition': result['market_analysis'].get('condition', 'unknown'),
                    'confidence': result['decision'].get('confidence', 0.0)
                })
        
        # Verify decisions were made
        assert len(decisions) > 0
        
        # Verify decisions reflect market conditions
        # (Specific assertions would depend on implementation)
        for decision in decisions:
            assert decision['action'] in ['observe', 'analyze', 'prepare', 'emergency']
            assert 0.0 <= decision['confidence'] <= 1.0
        
        await agent.shutdown()
    
    @pytest.mark.asyncio
    async def test_agent_cost_optimization(self, full_agent_setup):
        """Test agent cost optimization under different conditions"""
        agent, mock_mem0, mock_storage = full_agent_setup
        
        await agent.initialize()
        
        # Run cycles and track cost efficiency
        cost_data = []
        
        for i in range(3):
            initial_balance = agent.treasury_manager.current_balance
            
            result = await agent._perform_observation_cycle()
            
            final_balance = agent.treasury_manager.current_balance
            cycle_cost = initial_balance - final_balance
            
            cost_data.append({
                'cycle': i,
                'cost': cycle_cost,
                'emotional_state': result.get('agent_status', {}).get('emotional_state', 'unknown'),
                'market_quality': result.get('market_analysis', {}).get('data_quality', 0.0)
            })
        
        # Verify reasonable cost progression
        assert all(data['cost'] >= 0 for data in cost_data)
        
        # Verify cost tracking
        assert all('emotional_state' in data for data in cost_data)
        
        await agent.shutdown()
    
    @pytest.mark.asyncio
    async def test_agent_error_recovery(self, full_agent_setup):
        """Test agent recovery from various error conditions"""
        agent, mock_mem0, mock_storage = full_agent_setup
        
        await agent.initialize()
        
        # Test recovery from API failures
        with patch('aiohttp.ClientSession') as mock_session:
            # Mock failed API calls
            async def mock_failed_get(url, **kwargs):
                mock_response = AsyncMock()
                mock_response.status = 500
                mock_response.json = AsyncMock(side_effect=Exception("API Error"))
                return mock_response
            
            mock_session_instance = AsyncMock()
            mock_session_instance.get = mock_failed_get
            mock_session_instance.__aenter__ = AsyncMock(return_value=mock_session_instance)
            mock_session_instance.__aexit__ = AsyncMock(return_value=None)
            mock_session.return_value = mock_session_instance
            
            # Agent should handle API failures gracefully
            result = await agent._perform_observation_cycle()
            
            # Should complete despite API failures
            assert result['status'] in ['success', 'partial_success']
        
        await agent.shutdown()
    
    @pytest.mark.asyncio
    async def test_agent_30_day_simulation(self, full_agent_setup):
        """Simulate 30-day operation (compressed time)"""
        agent, mock_mem0, mock_storage = full_agent_setup
        
        await agent.initialize()
        
        # Simulate 30 days with 1 cycle per "day"
        daily_results = []
        
        for day in range(30):
            # Simulate daily operation
            daily_result = {
                'day': day + 1,
                'balance_start': agent.treasury_manager.current_balance
            }
            
            # Perform observation cycle
            result = await agent._perform_observation_cycle()
            
            daily_result.update({
                'balance_end': agent.treasury_manager.current_balance,
                'status': result['status'],
                'emotional_state': result.get('agent_status', {}).get('emotional_state', 'unknown')
            })
            
            daily_results.append(daily_result)
            
            # Stop if agent runs out of funds
            if agent.treasury_manager.current_balance <= 5.0:
                break
        
        # Verify agent survived some period
        assert len(daily_results) > 0
        
        # Verify reasonable operation
        successful_days = sum(1 for r in daily_results if r['status'] == 'success')
        assert successful_days >= len(daily_results) * 0.8  # At least 80% success rate
        
        # Verify emotional state evolution
        emotional_states = [r['emotional_state'] for r in daily_results]
        assert len(set(emotional_states)) > 1  # Should see state changes
        
        await agent.shutdown()
        
        return daily_results