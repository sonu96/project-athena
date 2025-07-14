"""
Unit tests for LangGraph Workflows
Tests market analysis and decision workflows
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from workflows.market_analysis_flow import MarketAnalysisWorkflow
from workflows.decision_flow import DecisionWorkflow
from workflows.state import AgentState, MarketAnalysisState, DecisionState


class TestMarketAnalysisWorkflow:
    """Test suite for MarketAnalysisWorkflow"""
    
    @pytest.fixture
    def mock_llm_client(self):
        """Mock LLM client"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = '{"sentiment": "bullish", "confidence": 0.8}'
        mock_client.messages.create.return_value = mock_response
        return mock_client
    
    @pytest.fixture
    def workflow(self, mock_llm_client):
        """Create MarketAnalysisWorkflow with mocked dependencies"""
        with patch('workflows.market_analysis_flow.Anthropic', return_value=mock_llm_client):
            return MarketAnalysisWorkflow()
    
    def test_initialization(self, workflow):
        """Test workflow initialization"""
        assert workflow.workflow is not None
        assert hasattr(workflow, 'llm_client')
    
    @pytest.mark.asyncio
    async def test_collect_market_data_node(self, workflow):
        """Test market data collection node"""
        initial_state = MarketAnalysisState(
            agent_id="test_agent",
            treasury_balance=100.0,
            emotional_state="stable",
            raw_market_data={}
        )
        
        with patch('workflows.market_analysis_flow.MarketDataCollector') as mock_collector:
            mock_instance = AsyncMock()
            mock_instance.collect_all_data.return_value = {
                'sources': {
                    'coingecko': {'status': 'success', 'bitcoin_price': 45000},
                    'fear_greed': {'status': 'success', 'fear_greed_index': 75}
                },
                'overall_quality': 0.9
            }
            mock_collector.return_value = mock_instance
            
            result_state = await workflow.collect_market_data(initial_state)
            
            assert result_state['market_data_collected'] is True
            assert 'sources' in result_state['raw_market_data']
            assert result_state['data_quality'] == 0.9
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_node(self, workflow):
        """Test sentiment analysis node"""
        state = MarketAnalysisState(
            agent_id="test_agent",
            treasury_balance=100.0,
            emotional_state="stable",
            raw_market_data={
                'sources': {
                    'coingecko': {'bitcoin_price': 45000, 'bitcoin_24h_change': 5.0},
                    'fear_greed': {'fear_greed_index': 75}
                }
            },
            market_data_collected=True,
            data_quality=0.9
        )
        
        result_state = await workflow.analyze_sentiment(state)
        
        assert result_state['sentiment_analyzed'] is True
        assert 'sentiment_analysis' in result_state
    
    @pytest.mark.asyncio
    async def test_classify_condition_node(self, workflow):
        """Test market condition classification node"""
        state = MarketAnalysisState(
            agent_id="test_agent",
            treasury_balance=100.0,
            emotional_state="stable",
            raw_market_data={
                'sources': {
                    'coingecko': {'bitcoin_24h_change': 5.0, 'ethereum_24h_change': 4.0},
                    'fear_greed': {'fear_greed_index': 75}
                }
            },
            sentiment_analysis={'sentiment': 'bullish', 'confidence': 0.8},
            sentiment_analyzed=True
        )
        
        with patch('workflows.market_analysis_flow.MarketConditionDetector') as mock_detector:
            mock_instance = AsyncMock()
            mock_instance.detect_condition.return_value = {
                'condition': 'bull',
                'confidence': 0.8,
                'supporting_factors': ['positive_momentum'],
                'risk_level': 'low'
            }
            mock_detector.return_value = mock_instance
            
            result_state = await workflow.classify_condition(state)
            
            assert result_state['condition_classified'] is True
            assert result_state['market_condition']['condition'] == 'bull'
            assert result_state['market_condition']['confidence'] == 0.8
    
    @pytest.mark.asyncio
    async def test_query_memories_node(self, workflow):
        """Test memory query node"""
        state = MarketAnalysisState(
            agent_id="test_agent",
            treasury_balance=100.0,
            emotional_state="stable",
            market_condition={'condition': 'bull', 'confidence': 0.8},
            condition_classified=True
        )
        
        with patch('workflows.market_analysis_flow.MemoryManager') as mock_memory:
            mock_instance = AsyncMock()
            mock_instance.retrieve_memories.return_value = [
                {'content': 'Previous bull market was profitable', 'relevance_score': 0.9}
            ]
            mock_memory.return_value = mock_instance
            
            result_state = await workflow.query_memories(state)
            
            assert result_state['memories_queried'] is True
            assert len(result_state['relevant_memories']) == 1
            assert result_state['relevant_memories'][0]['content'] == 'Previous bull market was profitable'
    
    @pytest.mark.asyncio
    async def test_full_workflow_execution(self, workflow):
        """Test complete workflow execution"""
        initial_state = MarketAnalysisState(
            agent_id="test_agent",
            treasury_balance=100.0,
            emotional_state="stable",
            raw_market_data={}
        )
        
        with patch('workflows.market_analysis_flow.MarketDataCollector'), \
             patch('workflows.market_analysis_flow.MarketConditionDetector'), \
             patch('workflows.market_analysis_flow.MemoryManager'):
            
            result = await workflow.run_analysis(initial_state)
            
            assert result['memories_queried'] is True
            assert 'market_condition' in result
            assert 'relevant_memories' in result
    
    def test_should_continue_analysis_true(self, workflow):
        """Test continuation condition - should continue"""
        state = MarketAnalysisState(
            agent_id="test_agent",
            treasury_balance=100.0,
            emotional_state="stable",
            data_quality=0.8,
            market_data_collected=True
        )
        
        result = workflow._should_continue_analysis(state)
        assert result == "continue"
    
    def test_should_continue_analysis_false(self, workflow):
        """Test continuation condition - should end"""
        state = MarketAnalysisState(
            agent_id="test_agent",
            treasury_balance=100.0,
            emotional_state="stable",
            data_quality=0.2,  # Poor quality
            market_data_collected=True
        )
        
        result = workflow._should_continue_analysis(state)
        assert result == "end"


class TestDecisionWorkflow:
    """Test suite for DecisionWorkflow"""
    
    @pytest.fixture
    def mock_llm_client(self):
        """Mock LLM client"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = '{"action": "observe", "reasoning": "Market uncertain", "confidence": 0.7}'
        mock_client.messages.create.return_value = mock_response
        return mock_client
    
    @pytest.fixture
    def decision_workflow(self, mock_llm_client):
        """Create DecisionWorkflow with mocked dependencies"""
        with patch('workflows.decision_flow.Anthropic', return_value=mock_llm_client):
            return DecisionWorkflow()
    
    def test_initialization(self, decision_workflow):
        """Test decision workflow initialization"""
        assert decision_workflow.workflow is not None
        assert hasattr(decision_workflow, 'llm_client')
    
    @pytest.mark.asyncio
    async def test_load_decision_context_node(self, decision_workflow):
        """Test decision context loading node"""
        initial_state = DecisionState(
            agent_id="test_agent",
            treasury_balance=75.0,
            emotional_state="cautious",
            market_condition={'condition': 'volatile', 'confidence': 0.6},
            decision_criteria={}
        )
        
        with patch('workflows.decision_flow.MemoryManager') as mock_memory:
            mock_instance = AsyncMock()
            mock_instance.retrieve_memories.return_value = [
                {'content': 'Volatile markets require caution', 'category': 'strategy'}
            ]
            mock_memory.return_value = mock_instance
            
            result_state = await decision_workflow.load_decision_context(initial_state)
            
            assert result_state['context_loaded'] is True
            assert 'decision_criteria' in result_state
            assert len(result_state['context_memories']) == 1
    
    @pytest.mark.asyncio
    async def test_analyze_options_node(self, decision_workflow):
        """Test options analysis node"""
        state = DecisionState(
            agent_id="test_agent",
            treasury_balance=75.0,
            emotional_state="cautious",
            market_condition={'condition': 'volatile', 'confidence': 0.6},
            decision_criteria={'risk_tolerance': 0.3, 'urgency': 6},
            context_loaded=True
        )
        
        result_state = await decision_workflow.analyze_options(state)
        
        assert result_state['options_analyzed'] is True
        assert 'available_options' in result_state
        assert isinstance(result_state['available_options'], list)
    
    @pytest.mark.asyncio
    async def test_assess_risks_node(self, decision_workflow):
        """Test risk assessment node"""
        state = DecisionState(
            agent_id="test_agent",
            treasury_balance=75.0,
            emotional_state="cautious",
            available_options=[
                {'action': 'observe', 'cost': 0.05},
                {'action': 'analyze_deep', 'cost': 0.20}
            ],
            options_analyzed=True
        )
        
        result_state = await decision_workflow.assess_risks(state)
        
        assert result_state['risks_assessed'] is True
        assert 'risk_assessments' in result_state
        assert len(result_state['risk_assessments']) == len(state['available_options'])
    
    @pytest.mark.asyncio
    async def test_cost_benefit_analysis_node(self, decision_workflow):
        """Test cost-benefit analysis node"""
        state = DecisionState(
            agent_id="test_agent",
            treasury_balance=75.0,
            emotional_state="cautious",
            available_options=[
                {'action': 'observe', 'cost': 0.05, 'expected_value': 0.1}
            ],
            risk_assessments=[
                {'action': 'observe', 'risk_score': 0.2}
            ],
            risks_assessed=True
        )
        
        result_state = await decision_workflow.cost_benefit_analysis(state)
        
        assert result_state['cost_benefit_done'] is True
        assert 'cost_benefit_analysis' in result_state
        assert isinstance(result_state['cost_benefit_analysis'], dict)
    
    @pytest.mark.asyncio
    async def test_final_decision_node(self, decision_workflow):
        """Test final decision node"""
        state = DecisionState(
            agent_id="test_agent",
            treasury_balance=75.0,
            emotional_state="cautious",
            cost_benefit_analysis={
                'recommended_action': 'observe',
                'expected_roi': 1.5,
                'confidence': 0.7
            },
            cost_benefit_done=True
        )
        
        result_state = await decision_workflow.final_decision(state)
        
        assert result_state['decision_made'] is True
        assert 'final_decision' in result_state
        assert result_state['final_decision']['action'] is not None
    
    @pytest.mark.asyncio
    async def test_full_decision_workflow(self, decision_workflow):
        """Test complete decision workflow execution"""
        initial_state = DecisionState(
            agent_id="test_agent",
            treasury_balance=75.0,
            emotional_state="cautious",
            market_condition={'condition': 'volatile', 'confidence': 0.6},
            decision_criteria={}
        )
        
        with patch('workflows.decision_flow.MemoryManager'):
            result = await decision_workflow.make_decision(initial_state)
            
            assert result['decision_made'] is True
            assert 'final_decision' in result
    
    def test_calculate_option_value_high_confidence(self, decision_workflow):
        """Test option value calculation with high confidence"""
        option = {'expected_value': 1.0, 'confidence': 0.9}
        risk_score = 0.2
        
        value = decision_workflow._calculate_option_value(option, risk_score)
        expected = 1.0 * 0.9 * (1 - 0.2)  # expected_value * confidence * (1 - risk)
        assert abs(value - expected) < 0.01
    
    def test_calculate_option_value_low_confidence(self, decision_workflow):
        """Test option value calculation with low confidence"""
        option = {'expected_value': 1.0, 'confidence': 0.3}
        risk_score = 0.8
        
        value = decision_workflow._calculate_option_value(option, risk_score)
        expected = 1.0 * 0.3 * (1 - 0.8)
        assert abs(value - expected) < 0.01
    
    def test_should_continue_decision_true(self, decision_workflow):
        """Test decision continuation - should continue"""
        state = DecisionState(
            agent_id="test_agent",
            treasury_balance=75.0,
            emotional_state="stable",
            context_loaded=True,
            options_analyzed=True
        )
        
        result = decision_workflow._should_continue_decision(state)
        assert result == "continue"
    
    def test_should_continue_decision_emergency(self, decision_workflow):
        """Test decision continuation - emergency mode"""
        state = DecisionState(
            agent_id="test_agent",
            treasury_balance=15.0,  # Very low balance
            emotional_state="desperate",
            context_loaded=True
        )
        
        result = decision_workflow._should_continue_decision(state)
        assert result == "emergency"
    
    def test_get_decision_criteria_confident(self, decision_workflow):
        """Test decision criteria for confident state"""
        criteria = decision_workflow._get_decision_criteria("confident", 150.0)
        
        assert criteria['risk_tolerance'] >= 0.7
        assert criteria['urgency'] <= 4
        assert criteria['exploration_bonus'] >= 0.3
    
    def test_get_decision_criteria_desperate(self, decision_workflow):
        """Test decision criteria for desperate state"""
        criteria = decision_workflow._get_decision_criteria("desperate", 15.0)
        
        assert criteria['risk_tolerance'] <= 0.2
        assert criteria['urgency'] >= 8
        assert criteria['exploration_bonus'] <= 0.1