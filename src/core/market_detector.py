"""
Market condition detection and pattern recognition
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from ..data.firestore_client import FirestoreClient
from ..data.bigquery_client import BigQueryClient
from ..integrations.mem0_integration import Mem0Integration

logger = logging.getLogger(__name__)


class MarketConditionDetector:
    """Detects market conditions and patterns for informed decision making"""
    
    def __init__(self, firestore_client: FirestoreClient, memory_integration: Mem0Integration):
        self.firestore = firestore_client
        self.memory = memory_integration
        
        # Market condition thresholds
        self.thresholds = {
            'strong_bull': {'btc_change': 8.0, 'eth_change': 10.0, 'fear_greed': 75},
            'bull': {'btc_change': 3.0, 'eth_change': 4.0, 'fear_greed': 60},
            'neutral': {'btc_change': 1.5, 'eth_change': 2.0, 'fear_greed': 45},
            'bear': {'btc_change': -3.0, 'eth_change': -4.0, 'fear_greed': 35},
            'strong_bear': {'btc_change': -8.0, 'eth_change': -10.0, 'fear_greed': 20},
            'volatile': {'volatility_threshold': 5.0}
        }
        
        # Pattern detection parameters
        self.pattern_config = {
            'min_data_points': 10,
            'trend_window': 7,  # days
            'volatility_window': 3,  # days
            'correlation_threshold': 0.7
        }
        
        # Historical context
        self.market_history = []
        self.pattern_cache = {}
        
        # Detection statistics
        self.detection_stats = {
            'total_detections': 0,
            'condition_accuracy': {},
            'pattern_matches': 0,
            'false_positives': 0
        }
    
    async def detect_market_condition(self, market_data: Dict[str, Any]) -> Tuple[str, float, Dict[str, Any]]:
        """Detect current market condition with confidence score"""
        try:
            logger.info("🎯 Detecting market condition...")
            
            # Extract key metrics
            btc_change = market_data.get('btc_24h_change', 0)
            eth_change = market_data.get('eth_24h_change', 0)
            fear_greed = market_data.get('fear_greed_index', 50)
            btc_price = market_data.get('btc_price', 0)
            eth_price = market_data.get('eth_price', 0)
            
            # Calculate additional indicators
            volatility = await self._calculate_volatility(market_data)
            trend_strength = await self._calculate_trend_strength(market_data)
            volume_profile = await self._analyze_volume_profile(market_data)
            
            # Primary condition detection
            primary_condition, primary_confidence = self._classify_primary_condition(
                btc_change, eth_change, fear_greed, volatility
            )
            
            # Secondary analysis for refinement
            refined_condition, refined_confidence = await self._refine_condition_with_context(
                primary_condition, primary_confidence, market_data
            )
            
            # Generate supporting factors
            supporting_factors = self._get_supporting_factors(
                refined_condition, btc_change, eth_change, fear_greed, volatility
            )
            
            # Calculate final confidence
            final_confidence = self._calculate_final_confidence(
                primary_confidence, refined_confidence, len(supporting_factors)
            )
            
            # Create detailed analysis
            analysis_details = {
                'primary_indicators': {
                    'btc_24h_change': btc_change,
                    'eth_24h_change': eth_change,
                    'fear_greed_index': fear_greed
                },
                'technical_indicators': {
                    'volatility': volatility,
                    'trend_strength': trend_strength,
                    'volume_profile': volume_profile
                },
                'supporting_factors': supporting_factors,
                'confidence_breakdown': {
                    'primary_confidence': primary_confidence,
                    'context_confidence': refined_confidence,
                    'factor_bonus': len(supporting_factors) * 0.05
                },
                'risk_assessment': self._assess_market_risk(refined_condition, volatility),
                'detection_timestamp': datetime.now(timezone.utc).isoformat(),
                'detection_algorithm': 'hybrid_v1.0'
            }
            
            # Store detection result
            await self._store_detection_result(refined_condition, final_confidence, analysis_details)
            
            # Update memory with significant market events
            await self._update_market_memories(refined_condition, market_data, analysis_details)
            
            # Update detection statistics
            await self._update_detection_stats(refined_condition, final_confidence)
            
            logger.info(f"✅ Market condition: {refined_condition} (confidence: {final_confidence:.2f})")
            
            return refined_condition, final_confidence, analysis_details
            
        except Exception as e:
            logger.error(f"❌ Market condition detection failed: {e}")
            return 'unknown', 0.0, {'error': str(e)}
    
    def _classify_primary_condition(self, btc_change: float, eth_change: float, 
                                   fear_greed: int, volatility: float) -> Tuple[str, float]:
        """Classify market condition based on primary indicators"""
        
        # Check for high volatility first
        if volatility > self.thresholds['volatile']['volatility_threshold']:
            return 'volatile', 0.8
        
        # Check strong conditions
        if (btc_change >= self.thresholds['strong_bull']['btc_change'] and 
            eth_change >= self.thresholds['strong_bull']['eth_change']):
            confidence = 0.9 if fear_greed >= self.thresholds['strong_bull']['fear_greed'] else 0.7
            return 'strong_bull', confidence
        
        if (btc_change <= self.thresholds['strong_bear']['btc_change'] and 
            eth_change <= self.thresholds['strong_bear']['eth_change']):
            confidence = 0.9 if fear_greed <= self.thresholds['strong_bear']['fear_greed'] else 0.7
            return 'strong_bear', confidence
        
        # Check moderate conditions
        if (btc_change >= self.thresholds['bull']['btc_change'] and 
            eth_change >= self.thresholds['bull']['eth_change']):
            confidence = 0.8 if fear_greed >= self.thresholds['bull']['fear_greed'] else 0.6
            return 'bull', confidence
        
        if (btc_change <= self.thresholds['bear']['btc_change'] and 
            eth_change <= self.thresholds['bear']['eth_change']):
            confidence = 0.8 if fear_greed <= self.thresholds['bear']['fear_greed'] else 0.6
            return 'bear', confidence
        
        # Default to neutral
        confidence = 0.6 if 35 <= fear_greed <= 65 else 0.4
        return 'neutral', confidence
    
    async def _refine_condition_with_context(self, primary_condition: str, primary_confidence: float,
                                           market_data: Dict[str, Any]) -> Tuple[str, float]:
        """Refine condition using historical context and patterns"""
        try:
            # Get recent market history
            recent_conditions = await self._get_recent_conditions(days=3)
            
            # Check for condition persistence
            if recent_conditions and len(recent_conditions) >= 2:
                recent_condition_types = [cond['condition'] for cond in recent_conditions]
                
                # If same condition for 2+ periods, increase confidence
                if all(cond == primary_condition for cond in recent_condition_types[-2:]):
                    refined_confidence = min(primary_confidence + 0.1, 1.0)
                    return primary_condition, refined_confidence
                
                # Check for trend reversal patterns
                if len(set(recent_condition_types[-3:])) >= 2:
                    # Market is transitioning, reduce confidence
                    refined_confidence = primary_confidence * 0.8
                    return primary_condition, refined_confidence
            
            # Check for divergence between price and sentiment
            price_sentiment_alignment = self._check_price_sentiment_alignment(market_data)
            if not price_sentiment_alignment:
                # Divergence detected, reduce confidence
                refined_confidence = primary_confidence * 0.7
                return primary_condition, refined_confidence
            
            return primary_condition, primary_confidence
            
        except Exception as e:
            logger.warning(f"Context refinement failed: {e}")
            return primary_condition, primary_confidence
    
    async def _calculate_volatility(self, market_data: Dict[str, Any]) -> float:
        """Calculate market volatility based on recent price movements"""
        try:
            # Get recent price data
            historical_data = await self._get_recent_price_data(days=3)
            
            if len(historical_data) < 3:
                # Fallback to current data
                btc_change = abs(market_data.get('btc_24h_change', 0))
                eth_change = abs(market_data.get('eth_24h_change', 0))
                return (btc_change + eth_change) / 2
            
            # Calculate price volatility
            btc_changes = [data.get('btc_24h_change', 0) for data in historical_data]
            eth_changes = [data.get('eth_24h_change', 0) for data in historical_data]
            
            btc_volatility = np.std(btc_changes) if len(btc_changes) > 1 else 0
            eth_volatility = np.std(eth_changes) if len(eth_changes) > 1 else 0
            
            return (btc_volatility + eth_volatility) / 2
            
        except Exception as e:
            logger.warning(f"Volatility calculation failed: {e}")
            # Fallback calculation
            btc_change = abs(market_data.get('btc_24h_change', 0))
            eth_change = abs(market_data.get('eth_24h_change', 0))
            return (btc_change + eth_change) / 2
    
    async def _calculate_trend_strength(self, market_data: Dict[str, Any]) -> float:
        """Calculate trend strength based on price momentum"""
        try:
            # Get recent data for trend analysis
            historical_data = await self._get_recent_price_data(days=7)
            
            if len(historical_data) < 3:
                return 0.5  # Neutral trend strength
            
            # Calculate price trends
            btc_prices = [data.get('btc_price', 0) for data in historical_data]
            eth_prices = [data.get('eth_price', 0) for data in historical_data]
            
            # Simple linear trend calculation
            btc_trend = (btc_prices[-1] - btc_prices[0]) / btc_prices[0] if btc_prices[0] > 0 else 0
            eth_trend = (eth_prices[-1] - eth_prices[0]) / eth_prices[0] if eth_prices[0] > 0 else 0
            
            # Convert to strength metric (0-1)
            avg_trend = (btc_trend + eth_trend) / 2
            trend_strength = min(abs(avg_trend) * 10, 1.0)  # Scale to 0-1
            
            return trend_strength
            
        except Exception as e:
            logger.warning(f"Trend strength calculation failed: {e}")
            return 0.5
    
    async def _analyze_volume_profile(self, market_data: Dict[str, Any]) -> str:
        """Analyze volume profile (simulated for Phase 1)"""
        # In Phase 1, we'll simulate volume analysis
        # In production, this would analyze actual trading volumes
        
        defi_tvl = market_data.get('defi_tvl', 0)
        base_tvl = market_data.get('base_network_tvl', 0)
        
        # Simple heuristic based on TVL
        if base_tvl > 3_000_000_000:  # $3B
            return 'high_volume'
        elif base_tvl > 1_000_000_000:  # $1B
            return 'medium_volume'
        else:
            return 'low_volume'
    
    def _get_supporting_factors(self, condition: str, btc_change: float, 
                              eth_change: float, fear_greed: int, volatility: float) -> List[str]:
        """Get factors supporting the detected condition"""
        factors = []
        
        if condition in ['bull', 'strong_bull']:
            if btc_change > 5:
                factors.append(f'Strong BTC momentum: +{btc_change:.1f}%')
            if eth_change > 5:
                factors.append(f'Strong ETH momentum: +{eth_change:.1f}%')
            if fear_greed > 70:
                factors.append(f'High market greed: {fear_greed}')
        
        elif condition in ['bear', 'strong_bear']:
            if btc_change < -5:
                factors.append(f'BTC decline: {btc_change:.1f}%')
            if eth_change < -5:
                factors.append(f'ETH decline: {eth_change:.1f}%')
            if fear_greed < 30:
                factors.append(f'High market fear: {fear_greed}')
        
        elif condition == 'volatile':
            if volatility > 5:
                factors.append(f'High price volatility: {volatility:.1f}%')
            if abs(btc_change) > 3 and abs(eth_change) > 3:
                factors.append('Significant price swings in major assets')
        
        elif condition == 'neutral':
            if 40 <= fear_greed <= 60:
                factors.append('Balanced market sentiment')
            if -2 <= btc_change <= 2 and -2 <= eth_change <= 2:
                factors.append('Stable price action')
        
        return factors
    
    def _calculate_final_confidence(self, primary_confidence: float, 
                                  refined_confidence: float, factor_count: int) -> float:
        """Calculate final confidence score"""
        # Weight the confidences
        weighted_confidence = (primary_confidence * 0.6 + refined_confidence * 0.4)
        
        # Bonus for supporting factors
        factor_bonus = min(factor_count * 0.05, 0.2)
        
        # Final confidence
        final_confidence = min(weighted_confidence + factor_bonus, 1.0)
        
        return round(final_confidence, 2)
    
    def _assess_market_risk(self, condition: str, volatility: float) -> str:
        """Assess market risk level"""
        if condition in ['strong_bear', 'volatile'] or volatility > 8:
            return 'high'
        elif condition in ['bear'] or volatility > 5:
            return 'medium'
        elif condition in ['neutral']:
            return 'low'
        else:  # bull markets
            return 'medium'  # Bull markets have their own risks
    
    def _check_price_sentiment_alignment(self, market_data: Dict[str, Any]) -> bool:
        """Check if price movements align with sentiment indicators"""
        btc_change = market_data.get('btc_24h_change', 0)
        eth_change = market_data.get('eth_24h_change', 0)
        fear_greed = market_data.get('fear_greed_index', 50)
        
        avg_price_change = (btc_change + eth_change) / 2
        
        # Check for alignment
        if avg_price_change > 2 and fear_greed > 60:
            return True  # Positive price, positive sentiment
        elif avg_price_change < -2 and fear_greed < 40:
            return True  # Negative price, negative sentiment
        elif -2 <= avg_price_change <= 2 and 40 <= fear_greed <= 60:
            return True  # Neutral price, neutral sentiment
        else:
            return False  # Divergence detected
    
    async def _get_recent_conditions(self, days: int = 3) -> List[Dict[str, Any]]:
        """Get recent market conditions from storage"""
        try:
            # Query Firestore for recent conditions
            query = (self.firestore.db.collection('agent_data_market_conditions')
                    .order_by('timestamp', direction='DESCENDING')
                    .limit(days * 24))  # Assuming hourly collections
            
            conditions = []
            async for doc in query.stream():
                conditions.append(doc.to_dict())
            
            return conditions
            
        except Exception as e:
            logger.warning(f"Failed to get recent conditions: {e}")
            return []
    
    async def _get_recent_price_data(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get recent price data for analysis"""
        try:
            # Query recent market data
            query = (self.firestore.db.collection('agent_data_market_data')
                    .order_by('timestamp', direction='DESCENDING')
                    .limit(days * 24))
            
            price_data = []
            async for doc in query.stream():
                data = doc.to_dict()
                if 'btc_price' in data and 'eth_price' in data:
                    price_data.append(data)
            
            return price_data[:days]  # Return most recent data points
            
        except Exception as e:
            logger.warning(f"Failed to get recent price data: {e}")
            return []
    
    async def _store_detection_result(self, condition: str, confidence: float, details: Dict[str, Any]):
        """Store detection result for historical analysis"""
        try:
            detection_data = {
                'condition': condition,
                'confidence': confidence,
                'details': details,
                'timestamp': datetime.now(timezone.utc)
            }
            
            # Store in Firestore
            await self.firestore.update_market_condition(detection_data)
            
            # Store in BigQuery for analytics
            # This would be implemented in production
            
        except Exception as e:
            logger.error(f"Failed to store detection result: {e}")
    
    async def _update_market_memories(self, condition: str, market_data: Dict[str, Any], 
                                    analysis: Dict[str, Any]):
        """Update memory with significant market events"""
        try:
            # Create memory for significant market conditions
            if condition in ['strong_bull', 'strong_bear', 'volatile']:
                content = f"Significant market event detected: {condition} market condition. "
                content += f"BTC: {market_data.get('btc_24h_change', 0):+.1f}%, "
                content += f"ETH: {market_data.get('eth_24h_change', 0):+.1f}%, "
                content += f"Fear/Greed: {market_data.get('fear_greed_index', 50)}"
                
                await self.memory.add_memory(
                    content=content,
                    metadata={
                        "category": "market_patterns",
                        "importance": 0.8,
                        "market_condition": condition,
                        "confidence": analysis.get('confidence_breakdown', {}).get('primary_confidence', 0),
                        "volatility": analysis.get('technical_indicators', {}).get('volatility', 0)
                    }
                )
        
        except Exception as e:
            logger.warning(f"Failed to update market memories: {e}")
    
    async def _update_detection_stats(self, condition: str, confidence: float):
        """Update detection statistics"""
        try:
            self.detection_stats['total_detections'] += 1
            
            # Track condition frequency
            if condition not in self.detection_stats['condition_accuracy']:
                self.detection_stats['condition_accuracy'][condition] = {
                    'count': 0,
                    'avg_confidence': 0.0
                }
            
            condition_stats = self.detection_stats['condition_accuracy'][condition]
            condition_stats['count'] += 1
            
            # Update average confidence
            prev_avg = condition_stats['avg_confidence']
            count = condition_stats['count']
            condition_stats['avg_confidence'] = (prev_avg * (count - 1) + confidence) / count
            
            # Store stats
            await self.firestore.log_system_event(
                "market_detection_stats",
                self.detection_stats
            )
            
        except Exception as e:
            logger.warning(f"Failed to update detection stats: {e}")
    
    async def get_detection_performance(self) -> Dict[str, Any]:
        """Get performance metrics for market detection"""
        try:
            return {
                'total_detections': self.detection_stats['total_detections'],
                'condition_breakdown': self.detection_stats['condition_accuracy'],
                'average_confidence': np.mean([
                    stats['avg_confidence'] 
                    for stats in self.detection_stats['condition_accuracy'].values()
                ]) if self.detection_stats['condition_accuracy'] else 0.0,
                'most_common_condition': max(
                    self.detection_stats['condition_accuracy'].items(),
                    key=lambda x: x[1]['count']
                )[0] if self.detection_stats['condition_accuracy'] else 'unknown'
            }
            
        except Exception as e:
            logger.error(f"Failed to get detection performance: {e}")
            return {'error': str(e)}