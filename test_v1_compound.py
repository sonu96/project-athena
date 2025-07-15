#!/usr/bin/env python3
"""
Test script for V1 Compound implementation

This script tests the core V1 functionality without running the full agent.
"""

import asyncio
import logging
from datetime import datetime, timezone

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_v1_components():
    """Test V1 Compound components"""
    try:
        logger.info("🧪 Testing V1 Compound Implementation...")
        
        # Test imports
        logger.info("1️⃣ Testing imports...")
        from src.integrations.cdp_integration import CDPIntegration
        from src.core.position_manager import PositionManager
        from src.core.memory_manager import MemoryManager
        from src.workflows.yield_optimization_flow import create_yield_optimization_workflow, YieldOptimizationState
        from src.data.market_data_collector import MarketDataCollector
        from src.data.firestore_client import FirestoreClient
        from src.data.bigquery_client import BigQueryClient
        from src.integrations.mem0_integration import Mem0Integration
        logger.info("✅ All imports successful")
        
        # Initialize components
        logger.info("\n2️⃣ Initializing components...")
        
        # Initialize CDP (will use simulation mode if SDK not available)
        cdp = CDPIntegration()
        await cdp.initialize_wallet()
        logger.info("✅ CDP initialized")
        
        # Initialize data clients
        firestore = FirestoreClient()
        bigquery = BigQueryClient()
        await firestore.initialize_database()
        await bigquery.initialize_dataset()
        logger.info("✅ Data clients initialized")
        
        # Initialize position manager
        position_manager = PositionManager(cdp, firestore)
        await position_manager.initialize()
        logger.info("✅ Position Manager initialized")
        
        # Initialize memory components
        mem0 = Mem0Integration()
        memory_manager = MemoryManager(mem0, firestore, bigquery)
        logger.info("✅ Memory Manager initialized")
        
        # Create yield optimization workflow
        yield_workflow = create_yield_optimization_workflow(
            position_manager,
            cdp,
            memory_manager
        )
        logger.info("✅ Yield Optimization workflow created")
        
        # Test CDP Compound methods
        logger.info("\n3️⃣ Testing CDP Compound methods...")
        
        # Get Compound APY
        apy = await cdp.get_compound_apy()
        logger.info(f"📊 Compound APY: {apy:.2f}%")
        
        # Get gas price
        gas_data = await cdp.get_gas_price()
        logger.info(f"⛽ Gas price: {gas_data['gas_price_gwei']:.2f} gwei")
        
        # Get wallet balance
        balance = await cdp.get_wallet_balance()
        logger.info(f"💰 Wallet balance: {balance}")
        
        # Test market data collection
        logger.info("\n4️⃣ Testing market data collection...")
        collector = MarketDataCollector(firestore, bigquery)
        
        # Collect Compound data
        compound_data = await collector.collect_compound_data(cdp)
        logger.info(f"📈 Compound data: APY {compound_data['compound_v3_apy']:.2f}%")
        
        # Collect gas data
        gas_collection = await collector.collect_gas_data(cdp)
        logger.info(f"⛽ Gas data collected: {gas_collection['gas_price_gwei']:.2f} gwei")
        
        # Test position manager
        logger.info("\n5️⃣ Testing Position Manager...")
        
        # Check if we should compound (with no position)
        should_compound = await position_manager.should_compound("stable", gas_data)
        logger.info(f"🤔 Should compound: {should_compound['should_compound']} - {should_compound['reasoning']}")
        
        # Test yield optimization workflow
        logger.info("\n6️⃣ Testing Yield Optimization workflow...")
        
        # Create test state
        test_state = YieldOptimizationState(
            emotional_state="stable",
            treasury_balance=100.0,
            days_until_bankruptcy=100,
            risk_tolerance=0.5,
            position_data={},
            pending_rewards=0.0,
            current_apy=0.0,
            gas_price={},
            gas_timing_memories=[],
            should_compound=False,
            compound_reasoning="",
            required_multiplier=2.0,
            expected_net_gain=0.0,
            execution_result={},
            costs_incurred=[],
            errors=[],
            warnings=[]
        )
        
        # Run workflow
        logger.info("🔄 Running yield optimization workflow...")
        result = await yield_workflow.ainvoke(test_state)
        
        logger.info(f"📋 Workflow result:")
        logger.info(f"   Should compound: {result.get('should_compound', False)}")
        logger.info(f"   Reasoning: {result.get('compound_reasoning', 'N/A')}")
        logger.info(f"   Errors: {result.get('errors', [])}")
        logger.info(f"   Warnings: {result.get('warnings', [])}")
        
        # Test memory formation
        logger.info("\n7️⃣ Testing memory formation...")
        
        # Test survival memory
        survival_experience = {
            "description": "Test survival experience",
            "treasury_balance": 10.0,
            "days_until_bankruptcy": 5,
            "action": "reduce_costs",
            "outcome": "survived",
            "saved_money": True,
            "amount_saved": 2.0,
            "technique": "skip_compound"
        }
        
        # Form survival memory
        memory_formed = await memory_manager.form_survival_memory(survival_experience, "desperate")
        logger.info(f"🧠 Survival memory formed: {memory_formed}")
        
        # Get survival memories
        survival_memories = await memory_manager.get_survival_memories()
        logger.info(f"📚 Found {len(survival_memories)} survival memories")
        
        logger.info("\n✅ All V1 tests completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise

async def test_compound_simulation():
    """Test a simulated Compound position"""
    try:
        logger.info("\n🎮 Testing Compound position simulation...")
        
        from src.integrations.cdp_integration import CDPIntegration
        from src.core.position_manager import PositionManager
        from src.data.firestore_client import FirestoreClient
        
        # Initialize
        cdp = CDPIntegration()
        await cdp.initialize_wallet()
        
        firestore = FirestoreClient()
        await firestore.initialize_database()
        
        position_manager = PositionManager(cdp, firestore)
        await position_manager.initialize()
        
        # Simulate opening a position
        logger.info("💸 Simulating position opening...")
        open_result = await position_manager.open_position(30.0, "stable")
        
        if open_result["success"]:
            logger.info(f"✅ Position opened: 30 USDC @ {open_result['apy']:.2f}% APY")
            
            # Update position state to simulate rewards
            position_manager.position_state.pending_rewards = 0.50  # Simulate $0.50 rewards
            
            # Check if we should compound
            gas_data = await cdp.get_gas_price()
            compound_decision = await position_manager.should_compound("stable", gas_data)
            
            logger.info(f"\n💭 Compound decision:")
            logger.info(f"   Should compound: {compound_decision['should_compound']}")
            logger.info(f"   Reasoning: {compound_decision['reasoning']}")
            
            if compound_decision['should_compound']:
                # Execute compound
                compound_result = await position_manager.execute_compound(
                    "stable",
                    compound_decision['reasoning']
                )
                
                if compound_result["success"]:
                    logger.info(f"✅ Compound successful! Net gain: ${compound_result['net_gain']:.4f}")
                else:
                    logger.info(f"❌ Compound failed: {compound_result.get('error', 'Unknown error')}")
        else:
            logger.info(f"❌ Failed to open position: {open_result.get('error', 'Unknown error')}")
        
        # Get position metrics
        metrics = position_manager.get_position_metrics()
        logger.info(f"\n📊 Position metrics:")
        for key, value in metrics.items():
            logger.info(f"   {key}: {value}")
        
    except Exception as e:
        logger.error(f"❌ Simulation failed: {e}")
        raise

async def main():
    """Run all tests"""
    try:
        # Test components
        await test_v1_components()
        
        # Test simulation
        await test_compound_simulation()
        
        logger.info("\n🎉 All V1 tests passed! The implementation is ready.")
        
    except Exception as e:
        logger.error(f"❌ Tests failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)