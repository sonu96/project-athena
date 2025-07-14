"""
Cloud Function: Market Data Collector
Collects real-time market data from multiple sources and stores in Firestore/BigQuery
Triggered every 15 minutes via Cloud Scheduler
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any

import functions_framework
from google.cloud import firestore, bigquery
import aiohttp
import os


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MarketDataCollector:
    """Collects market data from multiple sources"""
    
    def __init__(self):
        self.firestore_client = firestore.Client()
        self.bigquery_client = bigquery.Client()
        self.dataset_id = os.getenv('BIGQUERY_DATASET', 'athena_defi_agent')
        
    async def collect_coingecko_data(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Collect data from CoinGecko API"""
        try:
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': 'bitcoin,ethereum',
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_market_cap': 'true',
                'include_24hr_vol': 'true'
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    return {
                        'source': 'coingecko',
                        'timestamp': datetime.utcnow().isoformat(),
                        'bitcoin_price': data['bitcoin']['usd'],
                        'bitcoin_24h_change': data['bitcoin']['usd_24h_change'],
                        'bitcoin_market_cap': data['bitcoin']['usd_market_cap'],
                        'ethereum_price': data['ethereum']['usd'],
                        'ethereum_24h_change': data['ethereum']['usd_24h_change'],
                        'ethereum_market_cap': data['ethereum']['usd_market_cap'],
                        'data_quality': 1.0,
                        'status': 'success'
                    }
                else:
                    logger.error(f"CoinGecko API error: {response.status}")
                    return {'source': 'coingecko', 'status': 'error', 'data_quality': 0.0}
                    
        except Exception as e:
            logger.error(f"CoinGecko collection error: {e}")
            return {'source': 'coingecko', 'status': 'error', 'data_quality': 0.0}
    
    async def collect_fear_greed_data(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Collect Fear & Greed Index data"""
        try:
            url = "https://api.alternative.me/fng/"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data['data']:
                        latest = data['data'][0]
                        return {
                            'source': 'fear_greed',
                            'timestamp': datetime.utcnow().isoformat(),
                            'fear_greed_index': int(latest['value']),
                            'fear_greed_classification': latest['value_classification'],
                            'data_quality': 1.0,
                            'status': 'success'
                        }
                else:
                    logger.error(f"Fear & Greed API error: {response.status}")
                    return {'source': 'fear_greed', 'status': 'error', 'data_quality': 0.0}
                    
        except Exception as e:
            logger.error(f"Fear & Greed collection error: {e}")
            return {'source': 'fear_greed', 'status': 'error', 'data_quality': 0.0}
    
    async def collect_defillama_data(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Collect DeFiLlama data for BASE network"""
        try:
            # Get BASE chain TVL
            url = "https://api.llama.fi/chains"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Find BASE network data
                    base_data = None
                    for chain in data:
                        if chain.get('name', '').lower() == 'base':
                            base_data = chain
                            break
                    
                    if base_data:
                        return {
                            'source': 'defillama',
                            'timestamp': datetime.utcnow().isoformat(),
                            'base_tvl': base_data.get('tvl', 0),
                            'base_24h_change': base_data.get('change_1d', 0),
                            'data_quality': 1.0,
                            'status': 'success'
                        }
                    else:
                        return {'source': 'defillama', 'status': 'error', 'data_quality': 0.0}
                else:
                    logger.error(f"DeFiLlama API error: {response.status}")
                    return {'source': 'defillama', 'status': 'error', 'data_quality': 0.0}
                    
        except Exception as e:
            logger.error(f"DeFiLlama collection error: {e}")
            return {'source': 'defillama', 'status': 'error', 'data_quality': 0.0}
    
    async def collect_all_data(self) -> Dict[str, Any]:
        """Collect data from all sources in parallel"""
        async with aiohttp.ClientSession() as session:
            tasks = [
                self.collect_coingecko_data(session),
                self.collect_fear_greed_data(session),
                self.collect_defillama_data(session)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            market_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'collection_id': f"collection_{int(datetime.utcnow().timestamp())}",
                'sources': {}
            }
            
            total_quality = 0
            successful_sources = 0
            
            for result in results:
                if isinstance(result, dict) and 'source' in result:
                    source = result['source']
                    market_data['sources'][source] = result
                    
                    if result.get('status') == 'success':
                        successful_sources += 1
                        total_quality += result.get('data_quality', 0)
                else:
                    logger.error(f"Unexpected result: {result}")
            
            # Calculate overall data quality
            market_data['overall_quality'] = total_quality / len(tasks) if tasks else 0
            market_data['successful_sources'] = successful_sources
            market_data['total_sources'] = len(tasks)
            
            return market_data
    
    def store_firestore(self, data: Dict[str, Any]) -> None:
        """Store data in Firestore for real-time access"""
        try:
            collection_ref = self.firestore_client.collection('market_data')
            doc_ref = collection_ref.document(data['collection_id'])
            doc_ref.set(data)
            
            # Also update latest data document
            latest_ref = collection_ref.document('latest')
            latest_ref.set(data)
            
            logger.info(f"Stored market data in Firestore: {data['collection_id']}")
            
        except Exception as e:
            logger.error(f"Firestore storage error: {e}")
    
    def store_bigquery(self, data: Dict[str, Any]) -> None:
        """Store data in BigQuery for analytics"""
        try:
            table_id = f"{self.bigquery_client.project}.{self.dataset_id}.market_data"
            
            # Flatten data for BigQuery
            rows = []
            for source, source_data in data['sources'].items():
                if source_data.get('status') == 'success':
                    row = {
                        'timestamp': data['timestamp'],
                        'collection_id': data['collection_id'],
                        'source': source,
                        'data_quality': source_data.get('data_quality', 0),
                        'raw_data': json.dumps(source_data)
                    }
                    
                    # Add specific fields based on source
                    if source == 'coingecko':
                        row.update({
                            'bitcoin_price': source_data.get('bitcoin_price'),
                            'bitcoin_24h_change': source_data.get('bitcoin_24h_change'),
                            'ethereum_price': source_data.get('ethereum_price'),
                            'ethereum_24h_change': source_data.get('ethereum_24h_change')
                        })
                    elif source == 'fear_greed':
                        row.update({
                            'fear_greed_index': source_data.get('fear_greed_index'),
                            'fear_greed_classification': source_data.get('fear_greed_classification')
                        })
                    elif source == 'defillama':
                        row.update({
                            'base_tvl': source_data.get('base_tvl'),
                            'base_24h_change': source_data.get('base_24h_change')
                        })
                    
                    rows.append(row)
            
            if rows:
                errors = self.bigquery_client.insert_rows_json(table_id, rows)
                if errors:
                    logger.error(f"BigQuery insert errors: {errors}")
                else:
                    logger.info(f"Stored {len(rows)} rows in BigQuery")
            else:
                logger.warning("No successful data to store in BigQuery")
                
        except Exception as e:
            logger.error(f"BigQuery storage error: {e}")


@functions_framework.http
def market_data_collector_http(request):
    """HTTP Cloud Function entry point"""
    return asyncio.run(market_data_collector_main())


@functions_framework.cloud_event
def market_data_collector_scheduler(cloud_event):
    """Cloud Scheduler entry point"""
    return asyncio.run(market_data_collector_main())


async def market_data_collector_main():
    """Main function for market data collection"""
    try:
        logger.info("Starting market data collection...")
        
        collector = MarketDataCollector()
        
        # Collect all market data
        market_data = await collector.collect_all_data()
        
        # Store in both Firestore and BigQuery
        collector.store_firestore(market_data)
        collector.store_bigquery(market_data)
        
        logger.info(f"Market data collection completed. Quality: {market_data['overall_quality']:.2f}")
        
        return {
            'status': 'success',
            'timestamp': market_data['timestamp'],
            'collection_id': market_data['collection_id'],
            'overall_quality': market_data['overall_quality'],
            'successful_sources': market_data['successful_sources'],
            'total_sources': market_data['total_sources']
        }
        
    except Exception as e:
        logger.error(f"Market data collection failed: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }


if __name__ == "__main__":
    # For local testing
    result = asyncio.run(market_data_collector_main())
    print(json.dumps(result, indent=2))