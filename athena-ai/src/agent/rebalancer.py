"""
Smart Rebalancer - Memory-Driven Position Management

Uses learned patterns from Mem0 to make intelligent rebalancing decisions.
Optimizes for gas costs, compound timing, and APR maximization.
"""
import logging
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
import asyncio

from src.agent.memory import AthenaMemory, MemoryType
from src.integrations.quicknode_aerodrome import AerodromeAPI
from src.cdp.base_client import BaseClient
from config.settings import settings

logger = logging.getLogger(__name__)


class SmartRebalancer:
    """
    Intelligent rebalancing system that learns from patterns.
    
    Key features:
    - Memory-based APR prediction
    - Gas optimization using learned patterns
    - Compound timing optimization
    - Risk-adjusted rebalancing decisions
    """
    
    def __init__(self, 
                 memory: AthenaMemory,
                 aerodrome_api: AerodromeAPI,
                 base_client: BaseClient):
        """Initialize the smart rebalancer."""
        self.memory = memory
        self.api = aerodrome_api
        self.base_client = base_client
        
        # Rebalancing parameters (can be adjusted based on learning)
        self.min_apr_threshold = Decimal("20")  # Minimum acceptable APR
        self.rebalance_cost_multiplier = Decimal("2")  # Expected gain must be 2x cost
        self.compound_min_value = Decimal("50")  # Minimum rewards to compound
        self.max_slippage = Decimal("0.5")  # Maximum slippage tolerance
        
        # Performance tracking
        self.rebalance_history = []
        self.compound_history = []
        
    async def analyze_positions(self, positions: List[Dict]) -> List[Dict]:
        """
        Analyze all positions and return rebalancing recommendations.
        
        Args:
            positions: List of current positions with pool, value, apr data
            
        Returns:
            List of recommended actions with reasoning
        """
        recommendations = []
        
        for position in positions:
            # Get memories about this pool
            pool_memories = await self._get_pool_insights(position["pool_address"])
            
            # Predict future APR
            predicted_apr = await self._predict_apr(position, pool_memories)
            
            # Check if position needs rebalancing
            should_rebalance, reason = await self._should_rebalance(
                position, predicted_apr, pool_memories
            )
            
            if should_rebalance:
                # Find better opportunity
                better_pool = await self._find_better_pool(position)
                
                if better_pool:
                    # Calculate costs and benefits
                    analysis = await self._analyze_rebalance_profitability(
                        position, better_pool
                    )
                    
                    if analysis["profitable"]:
                        recommendations.append({
                            "action": "rebalance",
                            "from_pool": position["pool"],
                            "to_pool": better_pool["pair"],
                            "reason": reason,
                            "current_apr": float(position["apr"]),
                            "predicted_apr": float(predicted_apr),
                            "new_pool_apr": float(better_pool["apr"]),
                            "estimated_gain": analysis["estimated_gain"],
                            "gas_cost": analysis["gas_cost"],
                            "confidence": analysis["confidence"]
                        })
                        
        return recommendations
        
    async def _get_pool_insights(self, pool_address: str) -> List[Dict]:
        """Get historical memories and patterns for a pool."""
        # Query multiple memory categories
        memories = []
        
        # APR patterns
        apr_memories = await self.memory.recall(
            f"pool {pool_address} APR changes patterns",
            memory_type=MemoryType.PATTERN,
            limit=10
        )
        memories.extend(apr_memories)
        
        # TVL impact patterns
        tvl_memories = await self.memory.recall(
            f"TVL impact on APR pool {pool_address}",
            memory_type=MemoryType.LEARNING,
            limit=5
        )
        memories.extend(tvl_memories)
        
        # Historical performance
        perf_memories = await self.memory.recall(
            f"pool {pool_address} historical performance",
            memory_type=MemoryType.OBSERVATION,
            limit=20
        )
        memories.extend(perf_memories)
        
        return memories
        
    async def _predict_apr(self, position: Dict, memories: List[Dict]) -> Decimal:
        """
        Predict future APR based on memories and patterns.
        
        This is where Athena's learning shines - using past patterns
        to predict future pool behavior.
        """
        current_apr = position["apr"]
        current_tvl = position["tvl"]
        pool_age_days = (datetime.utcnow() - position.get("created_at", datetime.utcnow())).days
        
        # Extract patterns from memories
        apr_changes = []
        tvl_impacts = []
        
        for memory in memories:
            metadata = memory.get("metadata", {})
            
            # Look for APR degradation patterns
            if "apr_change" in metadata:
                apr_changes.append({
                    "change": Decimal(str(metadata["apr_change"])),
                    "days": metadata.get("days_elapsed", 0),
                    "tvl_ratio": metadata.get("tvl_ratio", 1)
                })
                
            # Look for TVL impact patterns
            if "tvl_impact_on_apr" in metadata:
                tvl_impacts.append({
                    "tvl_multiplier": Decimal(str(metadata["tvl_multiplier"])),
                    "apr_multiplier": Decimal(str(metadata["apr_multiplier"]))
                })
                
        # Calculate predicted APR
        predicted_apr = current_apr
        
        # Apply age-based degradation
        if pool_age_days < 7 and any("new pool" in str(m) for m in memories):
            # New pools typically lose 30-50% APR in first week
            age_factor = Decimal("0.7") if pool_age_days < 3 else Decimal("0.85")
            predicted_apr *= age_factor
            logger.info(f"Applied new pool degradation: {age_factor}")
            
        # Apply TVL-based predictions
        if tvl_impacts:
            avg_impact = sum(i["apr_multiplier"] for i in tvl_impacts) / len(tvl_impacts)
            predicted_apr *= avg_impact
            logger.info(f"Applied TVL impact: {avg_impact}")
            
        # Apply learned patterns
        if apr_changes:
            # Weight recent patterns more heavily
            weighted_change = sum(
                c["change"] * Decimal(str(1 / (c["days"] + 1)))
                for c in apr_changes[:5]
            )
            predicted_apr += weighted_change
            
        # Ensure reasonable bounds
        predicted_apr = max(Decimal("0"), min(predicted_apr, Decimal("500")))
        
        logger.info(f"Predicted APR for {position['pool']}: {current_apr}% -> {predicted_apr}%")
        return predicted_apr
        
    async def _should_rebalance(self, 
                               position: Dict, 
                               predicted_apr: Decimal,
                               memories: List[Dict]) -> Tuple[bool, str]:
        """
        Determine if a position should be rebalanced based on patterns.
        
        Returns:
            Tuple of (should_rebalance, reason)
        """
        current_apr = position["apr"]
        
        # Check for significant APR degradation
        apr_drop_percent = (current_apr - predicted_apr) / current_apr * 100 if current_apr > 0 else 0
        
        if apr_drop_percent > 30:
            return True, f"APR predicted to drop {apr_drop_percent:.1f}%"
            
        # Check if below minimum threshold
        if predicted_apr < self.min_apr_threshold:
            return True, f"APR below minimum threshold ({self.min_apr_threshold}%)"
            
        # Check for pattern-based signals
        for memory in memories:
            content = memory.get("content", "").lower()
            
            # Exit signals from learned patterns
            if "tvl exceeded optimal" in content and position["tvl"] > Decimal("10000000"):
                return True, "TVL exceeded optimal range based on patterns"
                
            if "gauge emissions ending" in content:
                return True, "Gauge emissions ending soon"
                
            if "better opportunity emerged" in content:
                # Check if this pattern is recent and relevant
                memory_date = memory.get("metadata", {}).get("timestamp")
                if memory_date and (datetime.utcnow() - datetime.fromisoformat(memory_date)).days < 1:
                    return True, "Better opportunity detected by pattern matching"
                    
        return False, ""
        
    async def _find_better_pool(self, current_position: Dict) -> Optional[Dict]:
        """
        Find a better pool to rebalance into using memories and current data.
        """
        # Get current opportunities from API
        opportunities = await self.api.search_opportunities(
            min_apr=float(current_position["apr"] * Decimal("1.2")),  # At least 20% better
            min_tvl=100000
        )
        
        if not opportunities:
            return None
            
        # Score opportunities based on memories
        scored_opportunities = []
        
        for opp in opportunities[:10]:  # Check top 10
            score = await self._score_opportunity(opp, current_position)
            scored_opportunities.append({**opp, "score": score})
            
        # Return best opportunity
        best = max(scored_opportunities, key=lambda x: x["score"])
        
        if best["score"] > 0.7:  # Confidence threshold
            return best
            
        return None
        
    async def _score_opportunity(self, pool: Dict, current_position: Dict) -> float:
        """Score a pool opportunity based on memories and patterns."""
        score = 0.5  # Base score
        
        # Query memories about this pool
        pool_memories = await self.memory.recall(
            f"pool {pool['pair']} performance patterns",
            limit=10
        )
        
        # Positive signals
        for memory in pool_memories:
            content = memory.get("content", "").lower()
            metadata = memory.get("metadata", {})
            
            if "stable apr" in content:
                score += 0.1
            if "growing tvl" in content and pool["tvl"] < Decimal("5000000"):
                score += 0.15
            if "high volume consistency" in content:
                score += 0.1
            if metadata.get("win_rate", 0) > 0.8:
                score += 0.2
                
        # Negative signals
        if pool["tvl"] > Decimal("20000000"):
            score -= 0.2  # Too much TVL based on patterns
        if "volatile" in str(pool_memories):
            score -= 0.1
        if pool.get("pool_age_days", 0) < 2:
            score -= 0.3  # Too new, risky
            
        # APR sustainability check
        if pool["incentive_apr"] > pool["fee_apr"] * 2:
            score -= 0.15  # Too dependent on emissions
            
        return max(0, min(1, score))
        
    async def _analyze_rebalance_profitability(self,
                                             from_position: Dict,
                                             to_pool: Dict) -> Dict:
        """
        Analyze if rebalancing is profitable considering gas costs.
        """
        # Get gas price prediction from memories
        gas_price = await self._predict_optimal_gas_price()
        
        # Estimate gas costs (withdraw + swap + deposit)
        estimated_gas = 500000  # Conservative estimate
        gas_cost_usd = (gas_price * estimated_gas / 10**9) * 2300  # Assume ETH = $2300
        
        # Calculate expected gains
        position_value = from_position["value_usd"]
        current_daily = position_value * from_position["apr"] / 36500
        new_daily = position_value * to_pool["apr"] / 36500
        daily_gain = new_daily - current_daily
        
        # Need to recover gas costs + profit
        days_to_profit = float(gas_cost_usd / daily_gain) if daily_gain > 0 else 999
        
        # Calculate confidence based on memories
        confidence = await self._calculate_rebalance_confidence(from_position, to_pool)
        
        return {
            "profitable": days_to_profit < 7 and confidence > 0.7,
            "gas_cost": float(gas_cost_usd),
            "daily_gain": float(daily_gain),
            "days_to_profit": days_to_profit,
            "estimated_gain": float(daily_gain * 30),  # 30-day gain
            "confidence": confidence
        }
        
    async def _predict_optimal_gas_price(self) -> Decimal:
        """Predict optimal gas price based on patterns."""
        # Query gas patterns
        gas_memories = await self.memory.recall(
            "gas price patterns optimal times",
            memory_type=MemoryType.PATTERN,
            limit=20
        )
        
        current_hour = datetime.utcnow().hour
        current_day = datetime.utcnow().strftime("%A")
        
        # Find patterns matching current time
        relevant_prices = []
        
        for memory in gas_memories:
            metadata = memory.get("metadata", {})
            
            if metadata.get("hour") == current_hour:
                relevant_prices.append(Decimal(str(metadata.get("gas_price", 20))))
            elif metadata.get("day") == current_day:
                relevant_prices.append(Decimal(str(metadata.get("gas_price", 25))))
                
        if relevant_prices:
            return sum(relevant_prices) / len(relevant_prices)
            
        # Default to conservative estimate
        return Decimal("30")
        
    async def _calculate_rebalance_confidence(self,
                                            from_position: Dict,
                                            to_pool: Dict) -> float:
        """Calculate confidence score for rebalancing decision."""
        confidence = 0.5
        
        # Query success rates for similar rebalances
        rebalance_memories = await self.memory.recall(
            f"rebalance from {from_position['apr']}% APR to {to_pool['apr']}% APR outcomes",
            memory_type=MemoryType.OUTCOME,
            limit=10
        )
        
        if rebalance_memories:
            successes = sum(1 for m in rebalance_memories if "success" in m.get("content", ""))
            success_rate = successes / len(rebalance_memories)
            confidence = 0.3 + (success_rate * 0.7)
            
        return confidence
        
    async def optimize_compound_timing(self, 
                                     pool_address: str,
                                     pending_rewards: Decimal) -> Dict:
        """
        Determine optimal timing for compounding rewards using patterns.
        
        Returns:
            Dict with recommendation and reasoning
        """
        # Get compound patterns from memory
        compound_memories = await self.memory.recall(
            f"compound timing patterns rewards {pending_rewards} gas optimization",
            memory_type=MemoryType.PATTERN,
            limit=15
        )
        
        # Get current and predicted gas prices
        current_gas = await self.base_client.get_gas_price()
        optimal_gas = await self._predict_optimal_gas_price()
        
        # Check if we should wait for better gas
        gas_savings_potential = float((current_gas - optimal_gas) / current_gas * 100)
        
        # Get compound ROI estimate
        roi_analysis = await self.api.estimate_compound_roi(
            pool_address, pending_rewards, current_gas
        )
        
        # Extract patterns from memories
        compound_patterns = {
            "min_rewards": Decimal("50"),
            "max_gas": Decimal("50"),
            "optimal_frequency_days": 3
        }
        
        for memory in compound_memories:
            metadata = memory.get("metadata", {})
            if "optimal_compound_threshold" in metadata:
                compound_patterns["min_rewards"] = Decimal(str(metadata["optimal_compound_threshold"]))
            if "max_profitable_gas" in metadata:
                compound_patterns["max_gas"] = Decimal(str(metadata["max_profitable_gas"]))
                
        # Make recommendation
        if pending_rewards < compound_patterns["min_rewards"]:
            return {
                "action": "wait",
                "reason": f"Rewards below optimal threshold ({compound_patterns['min_rewards']} minimum)",
                "wait_time_hours": 24
            }
            
        if current_gas > compound_patterns["max_gas"] and gas_savings_potential > 20:
            wait_hours = await self._estimate_hours_to_optimal_gas()
            return {
                "action": "wait",
                "reason": f"Gas {gas_savings_potential:.0f}% above optimal, wait {wait_hours}h",
                "wait_time_hours": wait_hours
            }
            
        if roi_analysis["profitable"]:
            return {
                "action": "compound",
                "reason": f"Profitable with {roi_analysis['breakeven_days']:.1f} day breakeven",
                "expected_gain": roi_analysis["daily_earnings"] * 30
            }
            
        return {
            "action": "wait", 
            "reason": "Not profitable at current gas prices",
            "wait_time_hours": 12
        }
        
    async def _estimate_hours_to_optimal_gas(self) -> int:
        """Estimate hours until gas prices reach optimal levels."""
        gas_patterns = await self.memory.recall(
            "gas price hourly patterns",
            memory_type=MemoryType.PATTERN,
            limit=24
        )
        
        current_hour = datetime.utcnow().hour
        
        # Find next low gas window
        for i in range(24):
            check_hour = (current_hour + i) % 24
            
            for pattern in gas_patterns:
                if pattern.get("metadata", {}).get("hour") == check_hour:
                    if pattern.get("metadata", {}).get("gas_category") == "low":
                        return i
                        
        return 6  # Default to 6 hours
        
    async def execute_rebalance(self,
                              from_position: Dict,
                              to_pool: Dict,
                              slippage: float = 0.5) -> Dict:
        """
        Execute a rebalancing transaction.
        
        Args:
            from_position: Current position to exit
            to_pool: New pool to enter
            slippage: Maximum slippage tolerance
            
        Returns:
            Transaction result
        """
        try:
            logger.info(f"Executing rebalance: {from_position['pool']} -> {to_pool['pair']}")
            
            # Step 1: Remove liquidity from current position
            remove_tx = await self.base_client.remove_liquidity(
                pool_address=from_position["pool_address"],
                liquidity_amount=from_position["lp_tokens"],
                min_amounts=[0, 0]  # Accept any amount due to slippage
            )
            
            if not remove_tx:
                raise Exception("Failed to remove liquidity")
                
            # Step 2: Get balances of received tokens
            token0_balance = await self.base_client.get_balance(from_position["token0"])
            token1_balance = await self.base_client.get_balance(from_position["token1"])
            
            # Step 3: Swap tokens if needed to match new pool requirements
            # This is simplified - in production would calculate optimal ratios
            
            # Step 4: Add liquidity to new pool
            add_tx = await self.base_client.add_liquidity(
                token_a=to_pool["token0"],
                token_b=to_pool["token1"],
                amount_a=token0_balance,
                amount_b=token1_balance,
                stable=to_pool["stable"]
            )
            
            if not add_tx:
                raise Exception("Failed to add liquidity to new pool")
                
            # Record rebalancing outcome for learning
            outcome = {
                "timestamp": datetime.utcnow(),
                "from_pool": from_position["pool"],
                "to_pool": to_pool["pair"],
                "from_apr": from_position["apr"],
                "to_apr": to_pool["apr"],
                "gas_cost": remove_tx.get("gas_used", 0) + add_tx.get("gas_used", 0),
                "success": True
            }
            
            # Store in memory for future learning
            await self.memory.remember(
                content=f"Successful rebalance: {from_position['pool']} ({from_position['apr']}%) -> {to_pool['pair']} ({to_pool['apr']}%)",
                memory_type=MemoryType.OUTCOME,
                category="rebalance_success",
                metadata=outcome,
                confidence=0.9
            )
            
            self.rebalance_history.append(outcome)
            
            return {
                "success": True,
                "from_pool": from_position["pool"],
                "to_pool": to_pool["pair"],
                "tx_hashes": [remove_tx["hash"], add_tx["hash"]],
                "gas_used": outcome["gas_cost"]
            }
            
        except Exception as e:
            logger.error(f"Rebalance failed: {e}")
            
            # Store failure for learning
            await self.memory.remember(
                content=f"Failed rebalance: {from_position['pool']} -> {to_pool['pair']}: {str(e)}",
                memory_type=MemoryType.OUTCOME,
                category="rebalance_failure",
                metadata={
                    "error": str(e),
                    "from_pool": from_position["pool"],
                    "to_pool": to_pool["pair"]
                },
                confidence=1.0
            )
            
            return {
                "success": False,
                "error": str(e)
            }
            
    async def learn_from_outcomes(self):
        """
        Analyze rebalancing history to improve future decisions.
        This is called periodically to refine patterns.
        """
        if len(self.rebalance_history) < 10:
            return  # Need more data
            
        # Analyze success patterns
        successful_rebalances = [r for r in self.rebalance_history if r["success"]]
        
        # Learn APR improvement patterns
        apr_improvements = [
            r["to_apr"] - r["from_apr"] 
            for r in successful_rebalances
        ]
        
        if apr_improvements:
            avg_improvement = sum(apr_improvements) / len(apr_improvements)
            
            # Store learning
            await self.memory.remember(
                content=f"Successful rebalances average {avg_improvement:.1f}% APR improvement",
                memory_type=MemoryType.LEARNING,
                category="rebalance_performance",
                metadata={
                    "avg_apr_improvement": float(avg_improvement),
                    "sample_size": len(successful_rebalances),
                    "success_rate": len(successful_rebalances) / len(self.rebalance_history)
                },
                confidence=0.8
            )
            
        # Learn gas optimization patterns
        gas_costs = [r["gas_cost"] for r in self.rebalance_history]
        if gas_costs:
            avg_gas = sum(gas_costs) / len(gas_costs)
            
            # Find patterns in low gas rebalances
            low_gas_rebalances = [
                r for r in self.rebalance_history 
                if r["gas_cost"] < avg_gas * 0.8
            ]
            
            if low_gas_rebalances:
                # Extract time patterns
                hours = [r["timestamp"].hour for r in low_gas_rebalances]
                most_common_hour = max(set(hours), key=hours.count)
                
                await self.memory.remember(
                    content=f"Optimal rebalancing hour: {most_common_hour}:00 UTC (avg gas savings 20%)",
                    memory_type=MemoryType.PATTERN,
                    category="gas_optimization",
                    metadata={
                        "optimal_hour": most_common_hour,
                        "avg_gas_savings": 0.2,
                        "sample_size": len(low_gas_rebalances)
                    },
                    confidence=0.7
                )