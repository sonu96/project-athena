"""
Sense Node - Perceive the environment

Gathers data from multiple sources in parallel:
- Market data from Aerodrome pools
- Wallet balance from CDP
- Gas prices from network
- Recent memories from Mem0
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List

from langsmith import traceable

from ...core.consciousness import ConsciousnessState, PoolObservation
from ...blockchain.cdp_client import CDPClient
from ...aerodrome.observer import AerodromeObserver
from ...memory.client import MemoryClient
from ...database.firestore_client import FirestoreClient

logger = logging.getLogger(__name__)


@traceable(name="sense_environment")
async def sense_environment(state: ConsciousnessState) -> ConsciousnessState:
    """
    Sense the environment by gathering data from multiple sources
    
    This node runs multiple async operations in parallel for efficiency
    """
    logger.info(f"👁️ Sensing environment - Cycle {state.cycle_count}")
    
    try:
        # Initialize clients
        cdp_client = CDPClient()
        aerodrome = AerodromeObserver()
        memory_client = MemoryClient()
        firestore = FirestoreClient()
        
        # Run all sensing operations in parallel
        results = await asyncio.gather(
            _sense_wallet(cdp_client, state),
            _sense_pools(aerodrome, state),
            _sense_gas_prices(cdp_client, state),
            _sense_memories(memory_client, state),
            return_exceptions=True
        )
        
        # Process results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                operation_names = ["wallet", "pools", "gas", "memories"]
                logger.error(f"Error sensing {operation_names[i]}: {result}")
                state.warnings.append(f"Failed to sense {operation_names[i]}: {str(result)}")
        
        # Update parallel task tracking
        state.parallel_tasks = []
        state.task_results = {}
        
        # Record sensing cost
        sensing_cost = 0.001  # Base sensing cost
        state.update_treasury(state.treasury_balance - sensing_cost, sensing_cost)
        state.total_llm_cost += sensing_cost
        
        logger.info(f"✅ Environment sensed - Balance: ${state.treasury_balance:.2f}, Pools: {len(state.observed_pools)}")
        
    except Exception as e:
        logger.error(f"❌ Critical error in sense node: {e}")
        state.errors.append(f"Sense error: {str(e)}")
    
    return state


async def _sense_wallet(cdp_client: CDPClient, state: ConsciousnessState) -> None:
    """Sense wallet balance and update treasury"""
    try:
        balance = await cdp_client.get_wallet_balance()
        
        # In V1, we're not trading so balance should remain stable
        # This would change in V2 when we start trading
        if balance != state.treasury_balance:
            logger.info(f"💰 Balance update: ${state.treasury_balance:.2f} → ${balance:.2f}")
            state.update_treasury(balance)
            
    except Exception as e:
        logger.error(f"Failed to get wallet balance: {e}")
        # Keep previous balance on error
        

async def _sense_pools(aerodrome: AerodromeObserver, state: ConsciousnessState) -> None:
    """Sense Aerodrome pool data"""
    try:
        # Get top pools by TVL
        pools = await aerodrome.get_top_pools(limit=5)
        
        # Clear old observations
        state.observed_pools = []
        
        # Add new observations
        for pool in pools:
            obs = PoolObservation(
                pool_address=pool["address"],
                pool_type=pool["type"],
                token0_symbol=pool["token0_symbol"],
                token1_symbol=pool["token1_symbol"],
                tvl_usd=pool["tvl_usd"],
                volume_24h_usd=pool["volume_24h_usd"],
                fee_apy=pool["fee_apy"],
                reward_apy=pool["reward_apy"],
                timestamp=datetime.utcnow(),
                notes=f"Volume/TVL ratio: {pool['volume_24h_usd']/pool['tvl_usd']:.2%}"
            )
            state.add_observation(obs)
            
        logger.debug(f"Observed {len(pools)} Aerodrome pools")
        
    except Exception as e:
        logger.error(f"Failed to sense pools: {e}")
        state.warnings.append("Pool observation failed")


async def _sense_gas_prices(cdp_client: CDPClient, state: ConsciousnessState) -> None:
    """Sense current gas prices"""
    try:
        gas_price = await cdp_client.get_gas_price()
        state.gas_price_gwei = gas_price
        
        # Add to market data
        state.market_data["gas_price_gwei"] = gas_price
        state.market_data["gas_price_usd"] = gas_price * 0.000000001 * 2500  # Rough ETH price
        
        logger.debug(f"Gas price: {gas_price} gwei")
        
    except Exception as e:
        logger.error(f"Failed to get gas price: {e}")


async def _sense_memories(memory_client: MemoryClient, state: ConsciousnessState) -> None:
    """Query recent relevant memories"""
    try:
        # Build context for memory search
        context = _build_memory_context(state)
        
        # Search for relevant memories
        memories = await memory_client.search_memories(
            query=context,
            limit=10,
            category="market_patterns" if state.observed_pools else None
        )
        
        # Update state with relevant memories
        state.recent_memories = memories
        
        logger.debug(f"Retrieved {len(memories)} relevant memories")
        
    except Exception as e:
        logger.error(f"Failed to retrieve memories: {e}")
        state.recent_memories = []


def _build_memory_context(state: ConsciousnessState) -> str:
    """Build context string for memory search"""
    parts = []
    
    # Add emotional context
    parts.append(f"Emotional state: {state.emotional_state.value}")
    
    # Add financial context
    parts.append(f"Treasury: ${state.treasury_balance:.2f}")
    parts.append(f"Days runway: {state.days_until_bankruptcy:.1f}")
    
    # Add market context if available
    if state.observed_pools:
        top_pool = state.observed_pools[0]
        parts.append(f"Observing: {top_pool.token0_symbol}/{top_pool.token1_symbol}")
        parts.append(f"TVL: ${top_pool.tvl_usd:,.0f}")
    
    # Add time context
    now = datetime.utcnow()
    parts.append(f"Time: {now.strftime('%A %H:%M UTC')}")
    
    return " | ".join(parts)