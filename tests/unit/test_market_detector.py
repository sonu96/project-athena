"""
Unit tests for Market Detector
Tests market condition detection, confidence scoring, and pattern analysis
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from core.market_detector import MarketConditionDetector


class TestMarketConditionDetector:
    """Test suite for MarketConditionDetector"""
    
    @pytest.fixture
    def mock_firestore_client(self):
        """Mock Firestore client"""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        
        # Mock market data
        mock_doc = MagicMock()
        mock_doc.to_dict.return_value = {
            'timestamp': datetime.utcnow().isoformat(),
            'sources': {
                'coingecko': {
                    'status': 'success',
                    'bitcoin_price': 45000,
                    'bitcoin_24h_change': 5.2,
                    'ethereum_price': 3000,
                    'ethereum_24h_change': 4.8
                },
                'fear_greed': {
                    'status': 'success',
                    'fear_greed_index': 75,
                    'fear_greed_classification': 'Greed'
                }
            }
        }
        
        mock_collection.order_by.return_value.limit.return_value.stream.return_value = [mock_doc]
        mock_client.collection.return_value = mock_collection
        
        return mock_client
    
    @pytest.fixture
    def market_detector(self, mock_firestore_client):
        """Create MarketConditionDetector with mocked dependencies"""
        with patch('core.market_detector.firestore.Client', return_value=mock_firestore_client):
            return MarketConditionDetector()
    
    def test_initialization(self, market_detector):
        """Test MarketConditionDetector initialization"""
        assert market_detector.market_conditions == [
            "strong_bull", "bull", "neutral", "bear", "strong_bear", "volatile"
        ]
    
    @pytest.mark.asyncio
    async def test_detect_condition_strong_bull(self, market_detector):
        """Test strong bull market detection"""
        market_data = {
            'bitcoin_24h_change': 8.5,
            'ethereum_24h_change': 7.2,
            'fear_greed_index': 85,
            'overall_quality': 1.0
        }
        
        condition = await market_detector.detect_condition(market_data)
        
        assert condition['condition'] == 'strong_bull'
        assert condition['confidence'] >= 0.8
        assert 'supporting_factors' in condition
    
    @pytest.mark.asyncio
    async def test_detect_condition_bull(self, market_detector):
        """Test bull market detection"""
        market_data = {
            'bitcoin_24h_change': 3.5,
            'ethereum_24h_change': 4.2,
            'fear_greed_index': 65,
            'overall_quality': 1.0
        }
        
        condition = await market_detector.detect_condition(market_data)
        
        assert condition['condition'] == 'bull'
        assert condition['confidence'] >= 0.6
    
    @pytest.mark.asyncio
    async def test_detect_condition_strong_bear(self, market_detector):
        """Test strong bear market detection"""
        market_data = {
            'bitcoin_24h_change': -8.5,
            'ethereum_24h_change': -9.2,
            'fear_greed_index': 15,
            'overall_quality': 1.0
        }
        
        condition = await market_detector.detect_condition(market_data)
        
        assert condition['condition'] == 'strong_bear'
        assert condition['confidence'] >= 0.8
    
    @pytest.mark.asyncio
    async def test_detect_condition_bear(self, market_detector):
        """Test bear market detection"""
        market_data = {
            'bitcoin_24h_change': -4.5,
            'ethereum_24h_change': -3.8,
            'fear_greed_index': 25,
            'overall_quality': 1.0
        }
        
        condition = await market_detector.detect_condition(market_data)
        
        assert condition['condition'] == 'bear'
        assert condition['confidence'] >= 0.6
    
    @pytest.mark.asyncio
    async def test_detect_condition_volatile(self, market_detector):
        """Test volatile market detection"""
        market_data = {
            'bitcoin_24h_change': 6.5,
            'ethereum_24h_change': -4.2,
            'fear_greed_index': 45,
            'overall_quality': 1.0
        }
        
        condition = await market_detector.detect_condition(market_data)
        
        assert condition['condition'] == 'volatile'
        assert condition['confidence'] >= 0.6
    
    @pytest.mark.asyncio
    async def test_detect_condition_neutral(self, market_detector):
        """Test neutral market detection"""
        market_data = {
            'bitcoin_24h_change': 0.5,
            'ethereum_24h_change': -0.3,
            'fear_greed_index': 50,
            'overall_quality': 1.0
        }
        
        condition = await market_detector.detect_condition(market_data)
        
        assert condition['condition'] == 'neutral'
        assert condition['confidence'] >= 0.5
    
    @pytest.mark.asyncio
    async def test_detect_condition_poor_quality(self, market_detector):
        """Test condition detection with poor data quality"""
        market_data = {
            'bitcoin_24h_change': 5.0,
            'ethereum_24h_change': 4.0,
            'fear_greed_index': 70,
            'overall_quality': 0.3  # Poor quality
        }
        
        condition = await market_detector.detect_condition(market_data)
        
        # Confidence should be reduced due to poor data quality
        assert condition['confidence'] <= 0.5
        assert 'low_data_quality' in condition.get('risk_factors', [])
    
    def test_calculate_price_momentum_positive(self, market_detector):
        """Test positive price momentum calculation"""
        market_data = {
            'bitcoin_24h_change': 4.5,
            'ethereum_24h_change': 3.8
        }
        
        momentum = market_detector._calculate_price_momentum(market_data)
        expected = (4.5 + 3.8) / 2
        assert momentum == expected
    
    def test_calculate_price_momentum_negative(self, market_detector):
        """Test negative price momentum calculation"""
        market_data = {
            'bitcoin_24h_change': -3.2,
            'ethereum_24h_change': -4.1
        }
        
        momentum = market_detector._calculate_price_momentum(market_data)
        expected = (-3.2 + -4.1) / 2
        assert momentum == expected
    
    def test_calculate_price_momentum_missing_data(self, market_detector):
        """Test price momentum with missing data"""
        market_data = {}
        
        momentum = market_detector._calculate_price_momentum(market_data)
        assert momentum == 0.0
    
    def test_calculate_volatility_high(self, market_detector):
        """Test high volatility calculation"""
        market_data = {
            'bitcoin_24h_change': 8.5,
            'ethereum_24h_change': -6.2
        }
        
        volatility = market_detector._calculate_volatility(market_data)
        expected = abs(8.5 - (-6.2)) / 2
        assert volatility == expected
    
    def test_calculate_volatility_low(self, market_detector):
        """Test low volatility calculation"""
        market_data = {
            'bitcoin_24h_change': 1.2,
            'ethereum_24h_change': 1.5
        }
        
        volatility = market_detector._calculate_volatility(market_data)
        expected = abs(1.2 - 1.5) / 2
        assert volatility == expected
    
    def test_get_sentiment_score_extreme_greed(self, market_detector):
        """Test sentiment score for extreme greed"""
        score = market_detector._get_sentiment_score(90)
        assert score >= 0.8
    
    def test_get_sentiment_score_greed(self, market_detector):
        """Test sentiment score for greed"""
        score = market_detector._get_sentiment_score(70)
        assert 0.6 <= score < 0.8
    
    def test_get_sentiment_score_neutral(self, market_detector):
        """Test sentiment score for neutral"""
        score = market_detector._get_sentiment_score(50)
        assert 0.4 <= score <= 0.6
    
    def test_get_sentiment_score_fear(self, market_detector):
        """Test sentiment score for fear"""
        score = market_detector._get_sentiment_score(30)
        assert 0.2 <= score < 0.4
    
    def test_get_sentiment_score_extreme_fear(self, market_detector):
        """Test sentiment score for extreme fear"""
        score = market_detector._get_sentiment_score(10)
        assert score <= 0.2
    
    def test_analyze_trend_strength_strong_uptrend(self, market_detector):
        """Test strong uptrend analysis"""
        market_data = {
            'bitcoin_24h_change': 6.5,
            'ethereum_24h_change': 5.8,
            'fear_greed_index': 75
        }
        
        strength = market_detector._analyze_trend_strength(market_data)
        assert strength >= 0.7
    
    def test_analyze_trend_strength_strong_downtrend(self, market_detector):
        """Test strong downtrend analysis"""
        market_data = {
            'bitcoin_24h_change': -6.5,
            'ethereum_24h_change': -5.8,
            'fear_greed_index': 25
        }
        
        strength = market_detector._analyze_trend_strength(market_data)
        assert strength >= 0.7
    
    def test_analyze_trend_strength_weak(self, market_detector):
        """Test weak trend analysis"""
        market_data = {
            'bitcoin_24h_change': 1.0,
            'ethereum_24h_change': -0.5,
            'fear_greed_index': 50
        }
        
        strength = market_detector._analyze_trend_strength(market_data)
        assert strength <= 0.4
    
    def test_assess_market_risk_low(self, market_detector):
        """Test low market risk assessment"""
        condition_data = {
            'condition': 'bull',
            'confidence': 0.8,
            'volatility': 0.2
        }
        
        risk = market_detector._assess_market_risk(condition_data)
        assert risk == 'low'
    
    def test_assess_market_risk_medium(self, market_detector):
        """Test medium market risk assessment"""
        condition_data = {
            'condition': 'neutral',
            'confidence': 0.6,
            'volatility': 0.4
        }
        
        risk = market_detector._assess_market_risk(condition_data)
        assert risk == 'medium'
    
    def test_assess_market_risk_high(self, market_detector):
        """Test high market risk assessment"""
        condition_data = {
            'condition': 'volatile',
            'confidence': 0.5,
            'volatility': 0.8
        }
        
        risk = market_detector._assess_market_risk(condition_data)
        assert risk == 'high'
    
    @pytest.mark.asyncio
    async def test_get_historical_context(self, market_detector):
        """Test historical context retrieval"""
        context = await market_detector.get_historical_context(hours=24)
        
        assert 'recent_conditions' in context
        assert 'condition_persistence' in context
        assert 'trend_changes' in context
        assert isinstance(context['recent_conditions'], list)
    
    @pytest.mark.asyncio
    async def test_analyze_condition_persistence(self, market_detector):
        """Test condition persistence analysis"""
        historical_data = [
            {'condition': 'bull', 'timestamp': datetime.utcnow().isoformat()},
            {'condition': 'bull', 'timestamp': (datetime.utcnow() - timedelta(hours=1)).isoformat()},
            {'condition': 'neutral', 'timestamp': (datetime.utcnow() - timedelta(hours=2)).isoformat()}
        ]
        
        persistence = market_detector._analyze_condition_persistence(historical_data)
        
        assert 'current_streak' in persistence
        assert 'streak_condition' in persistence
        assert persistence['current_streak'] >= 2  # Two consecutive bull conditions
        assert persistence['streak_condition'] == 'bull'
    
    def test_detect_divergence_true(self, market_detector):
        """Test price-sentiment divergence detection"""
        market_data = {
            'bitcoin_24h_change': 5.0,  # Positive price movement
            'ethereum_24h_change': 4.0,
            'fear_greed_index': 25  # Fear sentiment
        }
        
        divergence = market_detector._detect_divergence(market_data)
        assert divergence is True
    
    def test_detect_divergence_false(self, market_detector):
        """Test no price-sentiment divergence"""
        market_data = {
            'bitcoin_24h_change': 5.0,  # Positive price movement
            'ethereum_24h_change': 4.0,
            'fear_greed_index': 75  # Greed sentiment (aligned)
        }
        
        divergence = market_detector._detect_divergence(market_data)
        assert divergence is False
    
    def test_get_supporting_factors_bull(self, market_detector):
        """Test supporting factors for bull market"""
        market_data = {
            'bitcoin_24h_change': 5.0,
            'ethereum_24h_change': 4.0,
            'fear_greed_index': 70
        }
        
        factors = market_detector._get_supporting_factors('bull', market_data)
        
        assert 'positive_momentum' in factors
        assert 'greed_sentiment' in factors
        assert isinstance(factors, list)
    
    def test_get_supporting_factors_bear(self, market_detector):
        """Test supporting factors for bear market"""
        market_data = {
            'bitcoin_24h_change': -5.0,
            'ethereum_24h_change': -4.0,
            'fear_greed_index': 30
        }
        
        factors = market_detector._get_supporting_factors('bear', market_data)
        
        assert 'negative_momentum' in factors
        assert 'fear_sentiment' in factors
        assert isinstance(factors, list)