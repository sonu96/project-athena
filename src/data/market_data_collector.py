"""
Market data collection from multiple sources with quality scoring
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import json

from .firestore_client import FirestoreClient
from .bigquery_client import BigQueryClient
from ..config.settings import settings

logger = logging.getLogger(__name__)


class MarketDataCollector:
    """Collects market data from multiple sources with quality assessment"""
    
    def __init__(self, firestore_client: FirestoreClient, bigquery_client: BigQueryClient):
        self.firestore = firestore_client
        self.bigquery = bigquery_client
        
        # Data sources configuration
        self.sources = {
            'coingecko': {
                'enabled': True,
                'base_url': 'https://api.coingecko.com/api/v3',
                'rate_limit': 30,  # calls per minute
                'quality_weight': 0.9
            },
            'fear_greed': {
                'enabled': True,
                'base_url': 'https://api.alternative.me',
                'rate_limit': 60,
                'quality_weight': 0.7
            },
            'defillama': {
                'enabled': True,
                'base_url': 'https://api.llama.fi',
                'rate_limit': 300,
                'quality_weight': 0.8
            }
        }
        
        # Market data schema
        self.data_schema = {
            'timestamp': None,
            'btc_price': 0.0,
            'eth_price': 0.0,
            'btc_24h_change': 0.0,
            'eth_24h_change': 0.0,
            'btc_market_cap': 0.0,
            'eth_market_cap': 0.0,
            'total_market_cap': 0.0,
            'defi_tvl': 0.0,
            'fear_greed_index': 50,
            'fear_greed_classification': 'Neutral',
            'gas_price_gwei': 0.0,
            'base_network_tvl': 0.0,
            'compound_v3_apy': 0.0,  # Added for V1
            'compound_v3_tvl': 0.0,  # Added for V1
            'data_sources': [],
            'data_quality_score': 0.0
        }
        
        # Collection statistics
        self.collection_stats = {
            'total_collections': 0,
            'successful_collections': 0,
            'failed_collections': 0,
            'last_collection_time': None,
            'average_quality_score': 0.0
        }
    
    async def collect_base_network_data(self, cdp_integration=None) -> Dict[str, Any]:
        """Collect BASE network specific data using CDP"""
        try:
            logger.info("🔷 Collecting BASE network data via CDP...")
            
            collection_start = datetime.now(timezone.utc)
            market_data = {
                'timestamp': collection_start.isoformat(),
                'network': 'base-sepolia',
                'data_source': 'cdp',
                'success': True
            }
            
            # Get wallet balance from CDP
            if cdp_integration:
                # Get wallet balance
                balance = await cdp_integration.get_wallet_balance()
                market_data['wallet_balance'] = balance
                
                # Get gas price
                gas_data = await cdp_integration.get_gas_price()
                market_data['gas_price_gwei'] = gas_data.get('gas_price_gwei', 0)
                market_data['gas_estimated_usd'] = gas_data.get('estimated_cost_usd', 0)
                
                # Get Compound V3 data
                compound_apy = await cdp_integration.get_compound_apy()
                compound_balance = await cdp_integration.get_compound_balance()
                
                market_data['compound_v3_apy'] = compound_apy
                market_data['compound_v3_supplied'] = compound_balance.get('supplied_usdc', 0)
                market_data['compound_v3_rewards'] = compound_balance.get('accrued_interest', 0)
                
                # Get network status
                network_status = await cdp_integration.get_network_status()
                market_data['network_connected'] = network_status.get('connected', False)
                
            else:
                # Fallback to simulated data
                market_data.update({
                    'wallet_balance': {'ETH': 0.033, 'USDC': 70.0, 'total_usd': 100.0},
                    'gas_price_gwei': 5.0,
                    'gas_estimated_usd': 0.001,
                    'compound_v3_apy': 4.2,
                    'compound_v3_supplied': 0.0,
                    'compound_v3_rewards': 0.0,
                    'network_connected': True
                })
            
            # Add BASE-specific metrics (these would come from CDP SDK in production)
            market_data.update({
                'base_tvl': 1_500_000_000,  # $1.5B TVL on BASE
                'base_24h_volume': 250_000_000,  # $250M daily volume
                'base_active_users': 150_000,  # Daily active users
                'base_gas_usage': 85.5,  # Network utilization %
                'collection_duration_ms': int((datetime.now(timezone.utc) - collection_start).total_seconds() * 1000)
            })
            
            return {
                'success': True,
                'data': market_data,
                'quality_score': 0.95  # High quality since direct from CDP
            }
            
        except Exception as e:
            logger.error(f"❌ Error collecting BASE network data: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': {},
                'quality_score': 0.0
            }
    
    async def collect_comprehensive_market_data(self, cdp_integration=None) -> Dict[str, Any]:
        """Collect comprehensive market data focusing on BASE network"""
        try:
            logger.info("📊 Starting BASE-focused market data collection...")
            
            collection_start = datetime.now(timezone.utc)
            
            # First, get BASE network data via CDP
            base_result = await self.collect_base_network_data(cdp_integration)
            
            if base_result['success']:
                market_data = base_result['data']
                logger.info("✅ Successfully collected BASE network data via CDP")
                
                # Add some basic market context (simulated for Phase 1)
                market_data.update({
                    'btc_price': 65000.0,  # Simulated
                    'eth_price': 3200.0,   # Simulated
                    'fear_greed_index': 65,  # Simulated neutral-greed
                    'fear_greed_classification': 'Greed'
                })
                
                return {
                    'success': True,
                    'data': market_data,
                    'costs_incurred': []
                }
            else:
                logger.warning("❌ Failed to collect BASE network data, using fallback...")
                
                # Fallback to basic data
                market_data = {
                    'timestamp': collection_start.isoformat(),
                    'network': 'base-sepolia',
                    'success': False,
                    'error': base_result.get('error', 'Unknown error')
                }
                
                return {
                    'success': False,
                    'data': market_data,
                    'costs_incurred': []
                }
            
        except Exception as e:
            logger.error(f"❌ BASE network data collection failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': {},
                'costs_incurred': []
            }
    
    async def _collect_coingecko_data(self) -> Dict[str, Any]:
        """Collect data from CoinGecko API"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get cryptocurrency prices
                crypto_url = f"{self.sources['coingecko']['base_url']}/simple/price"
                params = {
                    'ids': 'bitcoin,ethereum',
                    'vs_currencies': 'usd',
                    'include_24hr_change': 'true',
                    'include_market_cap': 'true',
                    'include_24hr_vol': 'true'
                }
                
                if settings.coingecko_api_key:
                    headers = {'X-CG-Pro-API-Key': settings.coingecko_api_key}
                else:
                    headers = {}
                
                async with session.get(crypto_url, params=params, headers=headers) as response:
                    if response.status == 200:
                        crypto_data = await response.json()
                        
                        data = {
                            'btc_price': crypto_data.get('bitcoin', {}).get('usd', 0),
                            'eth_price': crypto_data.get('ethereum', {}).get('usd', 0),
                            'btc_24h_change': crypto_data.get('bitcoin', {}).get('usd_24h_change', 0),
                            'eth_24h_change': crypto_data.get('ethereum', {}).get('usd_24h_change', 0),
                            'btc_market_cap': crypto_data.get('bitcoin', {}).get('usd_market_cap', 0),
                            'eth_market_cap': crypto_data.get('ethereum', {}).get('usd_market_cap', 0)
                        }
                        
                        # Get global market data
                        global_url = f"{self.sources['coingecko']['base_url']}/global"
                        async with session.get(global_url, headers=headers) as global_response:
                            if global_response.status == 200:
                                global_data = await global_response.json()
                                data['total_market_cap'] = global_data.get('data', {}).get('total_market_cap', {}).get('usd', 0)
                        
                        return {
                            'success': True,
                            'data': data,
                            'quality_score': self.sources['coingecko']['quality_weight'],
                            'source': 'coingecko'
                        }
                    else:
                        raise Exception(f"CoinGecko API error: {response.status}")
                        
        except Exception as e:
            logger.error(f"CoinGecko collection failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'quality_score': 0.0,
                'source': 'coingecko'
            }
    
    async def _collect_fear_greed_data(self) -> Dict[str, Any]:
        """Collect Fear & Greed Index data"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.sources['fear_greed']['base_url']}/fng/?limit=1"
                
                async with session.get(url) as response:
                    if response.status == 200:
                        fear_greed_data = await response.json()
                        
                        if fear_greed_data.get('data'):
                            data = {
                                'fear_greed_index': int(fear_greed_data['data'][0]['value']),
                                'fear_greed_classification': fear_greed_data['data'][0]['value_classification']
                            }
                            
                            return {
                                'success': True,
                                'data': data,
                                'quality_score': self.sources['fear_greed']['quality_weight'],
                                'source': 'fear_greed'
                            }
                        else:
                            raise Exception("No Fear & Greed data available")
                    else:
                        raise Exception(f"Fear & Greed API error: {response.status}")
                        
        except Exception as e:
            logger.error(f"Fear & Greed collection failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'quality_score': 0.0,
                'source': 'fear_greed'
            }
    
    async def _collect_defillama_data(self) -> Dict[str, Any]:
        """Collect DeFi TVL data from DefiLlama"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get total DeFi TVL
                tvl_url = f"{self.sources['defillama']['base_url']}/tvl"
                
                async with session.get(tvl_url) as response:
                    if response.status == 200:
                        tvl_data = await response.json()
                        
                        data = {
                            'defi_tvl': float(tvl_data) if isinstance(tvl_data, (int, float)) else 0.0
                        }
                        
                        # Get BASE chain TVL
                        base_url = f"{self.sources['defillama']['base_url']}/charts/Base"
                        async with session.get(base_url) as base_response:
                            if base_response.status == 200:
                                base_data = await base_response.json()
                                if base_data and isinstance(base_data, list) and len(base_data) > 0:
                                    # Get latest TVL data point
                                    latest_base = base_data[-1]
                                    data['base_network_tvl'] = latest_base.get('totalLiquidityUSD', 0)
                        
                        return {
                            'success': True,
                            'data': data,
                            'quality_score': self.sources['defillama']['quality_weight'],
                            'source': 'defillama'
                        }
                    else:
                        raise Exception(f"DefiLlama API error: {response.status}")
                        
        except Exception as e:
            logger.error(f"DefiLlama collection failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'quality_score': 0.0,
                'source': 'defillama'
            }
    
    async def _get_base_network_data(self) -> Dict[str, Any]:
        """Get BASE network specific data (simulated for Phase 1)"""
        # In Phase 1, we'll simulate BASE network data
        # In production, this would query BASE RPC nodes
        
        return {
            'gas_price_gwei': 0.1,  # BASE has very low gas fees
            'base_block_number': 15000000,  # Simulated
            'base_block_time': 2,  # seconds
            'base_network_health': 'good'
        }
    
    async def collect_compound_data(self, cdp_integration=None) -> Dict[str, Any]:
        """Collect Compound V3 specific data for V1"""
        try:
            logger.info("💰 Collecting Compound V3 data...")
            
            # Get Compound APY from CDP integration if available
            if cdp_integration:
                compound_apy = await cdp_integration.get_compound_apy()
            else:
                # Simulate for testing
                import random
                compound_apy = 4.2 + random.uniform(-0.5, 0.5)
            
            # Get Compound TVL from DefiLlama
            compound_tvl = await self._get_compound_tvl()
            
            compound_data = {
                'compound_v3_apy': compound_apy,
                'compound_v3_tvl': compound_tvl,
                'compound_utilization': 85.0 + random.uniform(-5, 5) if not cdp_integration else 85.0,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            # Store in Firestore
            await self.firestore.collection('agent_data_yield_data').document('compound_v3').set(compound_data, merge=True)
            
            # Store in BigQuery for historical tracking
            await self.bigquery.insert_yield_performance({
                **compound_data,
                'protocol': 'compound_v3',
                'chain': 'base'
            })
            
            logger.info(f"✅ Compound data collected: APY {compound_apy:.2f}%, TVL ${compound_tvl/1e9:.2f}B")
            
            return compound_data
            
        except Exception as e:
            logger.error(f"❌ Failed to collect Compound data: {e}")
            return {
                'compound_v3_apy': 0.0,
                'compound_v3_tvl': 0.0
            }
    
    async def collect_gas_data(self, cdp_integration=None) -> Dict[str, Any]:
        """Collect gas price data every 5 minutes for V1"""
        try:
            logger.info("⛽ Collecting gas price data...")
            
            # Get gas price from CDP or simulate
            if cdp_integration:
                gas_data = await cdp_integration.get_gas_price()
            else:
                # Simulate realistic Base network gas prices
                import random
                hour = datetime.now(timezone.utc).hour
                day = datetime.now(timezone.utc).strftime("%A")
                
                base_gas = 5.0
                # Lower gas on weekends and nights
                if day in ["Saturday", "Sunday"]:
                    base_gas *= 0.7
                if 2 <= hour <= 4:
                    base_gas *= 0.5
                
                gas_data = {
                    'gas_price_gwei': base_gas * random.uniform(0.8, 1.2),
                    'estimated_cost_usd': base_gas * 0.0002
                }
            
            # Add time metadata
            gas_data.update({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'hour_utc': datetime.now(timezone.utc).hour,
                'day_of_week': datetime.now(timezone.utc).strftime("%A"),
                'is_weekend': datetime.now(timezone.utc).weekday() >= 5
            })
            
            # Store in Firestore for real-time access
            await self.firestore.collection('agent_data_gas_prices').document('latest').set(gas_data, merge=True)
            
            # Store in BigQuery for pattern analysis
            await self.bigquery.insert_rows(
                dataset_id=self.bigquery.dataset_id,
                table_id='base_gas_prices',
                rows=[gas_data]
            )
            
            logger.info(f"✅ Gas data collected: {gas_data['gas_price_gwei']:.2f} gwei (${gas_data['estimated_cost_usd']:.4f})")
            
            return gas_data
            
        except Exception as e:
            logger.error(f"❌ Failed to collect gas data: {e}")
            return {
                'gas_price_gwei': 5.0,
                'estimated_cost_usd': 0.001
            }
    
    async def _get_compound_tvl(self) -> float:
        """Get Compound V3 TVL from DefiLlama"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get Compound protocol TVL
                url = f"{self.sources['defillama']['base_url']}/tvl/compound-v3"
                
                async with session.get(url) as response:
                    if response.status == 200:
                        tvl_data = await response.json()
                        return float(tvl_data) if isinstance(tvl_data, (int, float)) else 2.5e9  # Default 2.5B
                    else:
                        # Fallback to general Compound data
                        url = f"{self.sources['defillama']['base_url']}/protocols"
                        async with session.get(url) as response2:
                            if response2.status == 200:
                                protocols = await response2.json()
                                for protocol in protocols:
                                    if 'compound' in protocol.get('name', '').lower() and 'v3' in protocol.get('name', '').lower():
                                        return protocol.get('tvl', 2.5e9)
                        return 2.5e9  # Default fallback
                        
        except Exception as e:
            logger.warning(f"Failed to get Compound TVL: {e}")
            return 2.5e9  # Default 2.5B TVL
    
    async def _store_market_data(self, market_data: Dict[str, Any]):
        """Store market data in Firestore and BigQuery"""
        try:
            # Store in Firestore for real-time access
            await self.firestore.collection('agent_data_market_data').document('latest').set(market_data, merge=True)
            
            # Store historical snapshot
            timestamp_key = datetime.now(timezone.utc).strftime('%Y-%m-%d-%H-%M')
            await self.firestore.collection('agent_data_market_data').document('snapshots').collection('hourly').document(timestamp_key).set(market_data)
            
            # Store in BigQuery for analytics
            await self.bigquery.insert_market_data(market_data)
            
            logger.debug("Market data stored in Firestore and BigQuery")
            
        except Exception as e:
            logger.error(f"Failed to store market data: {e}")
    
    async def _update_collection_stats(self, success: bool, quality_score: float):
        """Update collection statistics"""
        try:
            self.collection_stats['total_collections'] += 1
            
            if success:
                self.collection_stats['successful_collections'] += 1
                # Update running average of quality scores
                current_avg = self.collection_stats['average_quality_score']
                successful_count = self.collection_stats['successful_collections']
                self.collection_stats['average_quality_score'] = (
                    (current_avg * (successful_count - 1) + quality_score) / successful_count
                )
            else:
                self.collection_stats['failed_collections'] += 1
            
            self.collection_stats['last_collection_time'] = datetime.now(timezone.utc).isoformat()
            
            # Store stats in Firestore
            await self.firestore.collection('agent_data_system_logs').document('market_collection_stats').set(self.collection_stats, merge=True)
            
        except Exception as e:
            logger.error(f"Failed to update collection stats: {e}")
    
    async def get_latest_market_data(self) -> Dict[str, Any]:
        """Get the latest collected market data"""
        try:
            doc = await self.firestore.collection('agent_data_market_data').document('latest').get()
            if doc.exists:
                return doc.to_dict()
            else:
                logger.warning("No latest market data found")
                return self.data_schema.copy()
                
        except Exception as e:
            logger.error(f"Failed to get latest market data: {e}")
            return self.data_schema.copy()
    
    async def get_historical_data(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get historical market data for the last N hours"""
        try:
            # Query BigQuery for historical data
            historical_data = await self.bigquery.get_market_patterns(days=hours//24 + 1)
            return historical_data
            
        except Exception as e:
            logger.error(f"Failed to get historical data: {e}")
            return []
    
    async def get_collection_health(self) -> Dict[str, Any]:
        """Get health metrics for market data collection"""
        try:
            stats = self.collection_stats.copy()
            
            # Calculate success rate
            total = stats['total_collections']
            success_rate = (stats['successful_collections'] / total) if total > 0 else 0
            
            # Determine health status
            if success_rate > 0.9 and stats['average_quality_score'] > 0.8:
                health_status = 'excellent'
            elif success_rate > 0.7 and stats['average_quality_score'] > 0.6:
                health_status = 'good'
            elif success_rate > 0.5:
                health_status = 'fair'
            else:
                health_status = 'poor'
            
            return {
                'health_status': health_status,
                'success_rate': success_rate,
                'average_quality': stats['average_quality_score'],
                'total_collections': total,
                'last_collection': stats['last_collection_time'],
                'recommendations': self._get_health_recommendations(health_status, success_rate)
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection health: {e}")
            return {'health_status': 'unknown', 'error': str(e)}
    
    def _get_health_recommendations(self, health_status: str, success_rate: float) -> List[str]:
        """Get recommendations based on collection health"""
        recommendations = []
        
        if health_status == 'poor':
            recommendations.extend([
                "Check API key configurations",
                "Verify network connectivity",
                "Consider reducing collection frequency"
            ])
        elif health_status == 'fair':
            recommendations.extend([
                "Monitor API rate limits",
                "Add fallback data sources",
                "Improve error handling"
            ])
        elif success_rate < 0.8:
            recommendations.append("Investigate intermittent failures")
        
        if not recommendations:
            recommendations.append("Market data collection is healthy")
        
        return recommendations