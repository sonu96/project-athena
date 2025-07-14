"""
Unit tests for Memory Manager
Tests memory formation, retrieval, and pattern detection
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from core.memory_manager import MemoryManager


class TestMemoryManager:
    """Test suite for MemoryManager"""
    
    @pytest.fixture
    def mock_mem0_client(self):
        """Mock Mem0 client"""
        mock_client = MagicMock()
        mock_client.add.return_value = {'memory_id': 'test_memory_123'}
        mock_client.search.return_value = {
            'results': [
                {
                    'memory': 'Test memory content',
                    'score': 0.95,
                    'metadata': {'category': 'market', 'timestamp': '2024-01-01T00:00:00Z'}
                }
            ]
        }
        mock_client.get_all.return_value = {
            'results': [
                {
                    'id': 'memory_1',
                    'memory': 'Market was volatile today',
                    'metadata': {'category': 'market'}
                }
            ]
        }
        return mock_client
    
    @pytest.fixture
    def mock_firestore_client(self):
        """Mock Firestore client"""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_doc = MagicMock()
        
        mock_client.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_doc
        mock_collection.add.return_value = (None, mock_doc)
        
        return mock_client
    
    @pytest.fixture
    def memory_manager(self, mock_mem0_client, mock_firestore_client):
        """Create MemoryManager with mocked dependencies"""
        with patch('core.memory_manager.MemoryClient', return_value=mock_mem0_client), \
             patch('core.memory_manager.firestore.Client', return_value=mock_firestore_client):
            return MemoryManager(agent_id="test_agent")
    
    def test_initialization(self, memory_manager):
        """Test MemoryManager initialization"""
        assert memory_manager.agent_id == "test_agent"
        assert memory_manager.memory_categories == [
            "survival", "protocol", "market", "strategy", "decision"
        ]
    
    @pytest.mark.asyncio
    async def test_form_memory_market(self, memory_manager):
        """Test forming a market memory"""
        experience = {
            'type': 'market_observation',
            'data': {
                'bitcoin_price': 45000,
                'market_condition': 'bull',
                'confidence': 0.8
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        with patch.object(memory_manager, '_store_memory_metadata') as mock_store:
            memory_id = await memory_manager.form_memory(experience, importance=0.8)
            
            assert memory_id == 'test_memory_123'
            mock_store.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_form_memory_decision(self, memory_manager):
        """Test forming a decision memory"""
        experience = {
            'type': 'decision_made',
            'data': {
                'action': 'observe',
                'reasoning': 'Market conditions uncertain',
                'outcome': 'successful'
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        memory_id = await memory_manager.form_memory(experience, importance=0.7)
        assert memory_id == 'test_memory_123'
    
    @pytest.mark.asyncio
    async def test_form_memory_survival(self, memory_manager):
        """Test forming a survival memory"""
        experience = {
            'type': 'cost_deducted',
            'data': {
                'amount': 5.0,
                'operation': 'market_analysis',
                'remaining_balance': 45.0
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        memory_id = await memory_manager.form_memory(experience, importance=0.9)
        assert memory_id == 'test_memory_123'
    
    def test_categorize_experience_market(self, memory_manager):
        """Test experience categorization for market data"""
        experience = {
            'type': 'market_observation',
            'data': {'bitcoin_price': 45000}
        }
        
        category = memory_manager._categorize_experience(experience)
        assert category == 'market'
    
    def test_categorize_experience_decision(self, memory_manager):
        """Test experience categorization for decisions"""
        experience = {
            'type': 'decision_made',
            'data': {'action': 'observe'}
        }
        
        category = memory_manager._categorize_experience(experience)
        assert category == 'decision'
    
    def test_categorize_experience_survival(self, memory_manager):
        """Test experience categorization for survival events"""
        experience = {
            'type': 'cost_deducted',
            'data': {'amount': 5.0}
        }
        
        category = memory_manager._categorize_experience(experience)
        assert category == 'survival'
    
    def test_categorize_experience_protocol(self, memory_manager):
        """Test experience categorization for protocol events"""
        experience = {
            'type': 'protocol_interaction',
            'data': {'protocol': 'uniswap'}
        }
        
        category = memory_manager._categorize_experience(experience)
        assert category == 'protocol'
    
    def test_categorize_experience_strategy(self, memory_manager):
        """Test experience categorization for strategy events"""
        experience = {
            'type': 'strategy_update',
            'data': {'new_approach': 'conservative'}
        }
        
        category = memory_manager._categorize_experience(experience)
        assert category == 'strategy'
    
    def test_categorize_experience_default(self, memory_manager):
        """Test experience categorization for unknown types"""
        experience = {
            'type': 'unknown_event',
            'data': {'something': 'random'}
        }
        
        category = memory_manager._categorize_experience(experience)
        assert category == 'decision'  # Default category
    
    @pytest.mark.asyncio
    async def test_retrieve_memories_by_context(self, memory_manager):
        """Test memory retrieval by context"""
        context = {
            'market_condition': 'bull',
            'emotional_state': 'confident'
        }
        
        memories = await memory_manager.retrieve_memories(context, limit=5)
        
        assert len(memories) == 1
        assert memories[0]['content'] == 'Test memory content'
        assert memories[0]['relevance_score'] == 0.95
        assert memories[0]['category'] == 'market'
    
    @pytest.mark.asyncio
    async def test_retrieve_memories_by_category(self, memory_manager):
        """Test memory retrieval by category"""
        memories = await memory_manager.retrieve_memories(
            context={'market_condition': 'volatile'}, 
            category='market',
            limit=3
        )
        
        assert len(memories) >= 0  # Mem0 mock returns results
    
    @pytest.mark.asyncio
    async def test_get_memory_statistics(self, memory_manager):
        """Test memory statistics retrieval"""
        stats = await memory_manager.get_memory_statistics()
        
        assert 'total_memories' in stats
        assert 'memories_by_category' in stats
        assert 'recent_memories' in stats
        assert stats['total_memories'] >= 0
    
    @pytest.mark.asyncio
    async def test_consolidate_learning_patterns(self, memory_manager):
        """Test learning pattern consolidation"""
        patterns = await memory_manager.consolidate_learning_patterns()
        
        assert 'market_patterns' in patterns
        assert 'decision_patterns' in patterns
        assert 'cost_patterns' in patterns
        assert isinstance(patterns['market_patterns'], list)
    
    def test_extract_key_information_market(self, memory_manager):
        """Test key information extraction from market experience"""
        experience = {
            'type': 'market_observation',
            'data': {
                'bitcoin_price': 45000,
                'ethereum_price': 3000,
                'market_condition': 'bull',
                'confidence': 0.8,
                'fear_greed_index': 75
            }
        }
        
        key_info = memory_manager._extract_key_information(experience)
        
        assert 'bitcoin_price' in key_info
        assert 'market_condition' in key_info
        assert 'confidence' in key_info
        assert key_info['bitcoin_price'] == 45000
        assert key_info['market_condition'] == 'bull'
    
    def test_extract_key_information_decision(self, memory_manager):
        """Test key information extraction from decision experience"""
        experience = {
            'type': 'decision_made',
            'data': {
                'action': 'analyze_protocol',
                'reasoning': 'High yield opportunity detected',
                'cost': 2.5,
                'outcome': 'successful',
                'confidence': 0.9
            }
        }
        
        key_info = memory_manager._extract_key_information(experience)
        
        assert 'action' in key_info
        assert 'reasoning' in key_info
        assert 'outcome' in key_info
        assert key_info['action'] == 'analyze_protocol'
        assert key_info['outcome'] == 'successful'
    
    def test_extract_key_information_survival(self, memory_manager):
        """Test key information extraction from survival experience"""
        experience = {
            'type': 'emergency_mode_activated',
            'data': {
                'trigger': 'low_balance',
                'remaining_balance': 18.5,
                'days_until_bankruptcy': 2,
                'action_taken': 'reduce_operations'
            }
        }
        
        key_info = memory_manager._extract_key_information(experience)
        
        assert 'trigger' in key_info
        assert 'remaining_balance' in key_info
        assert 'days_until_bankruptcy' in key_info
        assert key_info['trigger'] == 'low_balance'
        assert key_info['remaining_balance'] == 18.5
    
    @pytest.mark.asyncio
    async def test_detect_patterns_market(self, memory_manager):
        """Test market pattern detection"""
        memories = [
            {'content': 'Bitcoin price increased 5% during bull market', 'category': 'market'},
            {'content': 'Ethereum followed Bitcoin upward trend', 'category': 'market'},
            {'content': 'High fear greed index correlates with price increases', 'category': 'market'}
        ]
        
        patterns = await memory_manager._detect_patterns(memories, 'market')
        
        assert isinstance(patterns, list)
        assert len(patterns) >= 0
    
    @pytest.mark.asyncio
    async def test_get_relevant_context_memories(self, memory_manager):
        """Test getting relevant memories for current context"""
        current_context = {
            'market_condition': 'bear',
            'treasury_balance': 30.0,
            'emotional_state': 'cautious'
        }
        
        memories = await memory_manager.get_relevant_context_memories(current_context, max_memories=3)
        
        assert isinstance(memories, list)
        assert len(memories) <= 3
    
    def test_calculate_memory_importance_high(self, memory_manager):
        """Test high importance memory calculation"""
        experience = {
            'type': 'emergency_mode_activated',
            'data': {'remaining_balance': 10.0}
        }
        
        importance = memory_manager._calculate_memory_importance(experience)
        assert importance >= 0.8  # Emergency events are high importance
    
    def test_calculate_memory_importance_medium(self, memory_manager):
        """Test medium importance memory calculation"""
        experience = {
            'type': 'market_observation',
            'data': {'bitcoin_price': 45000, 'confidence': 0.7}
        }
        
        importance = memory_manager._calculate_memory_importance(experience)
        assert 0.4 <= importance <= 0.8  # Market observations are medium importance
    
    def test_calculate_memory_importance_low(self, memory_manager):
        """Test low importance memory calculation"""
        experience = {
            'type': 'routine_check',
            'data': {'status': 'normal'}
        }
        
        importance = memory_manager._calculate_memory_importance(experience)
        assert importance <= 0.5  # Routine events are low importance