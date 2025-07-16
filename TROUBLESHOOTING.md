# Troubleshooting Guide

This document contains common issues encountered during the development and deployment of the Athena DeFi Agent, along with their solutions.

## Table of Contents
- [Memory System Issues](#memory-system-issues)
- [Firestore API Issues](#firestore-api-issues)
- [LLM Integration Issues](#llm-integration-issues)
- [CDP Integration Issues](#cdp-integration-issues)
- [Workflow Issues](#workflow-issues)
- [Market Data Collection Issues](#market-data-collection-issues)
- [Enhanced Architecture Issues](#enhanced-architecture-issues)

---

## Memory System Issues

### Issue: Mem0 Cloud API Connection Issues
**Error Messages:**
```
❌ Failed to initialize Mem0 Cloud: Invalid API key
❌ Error adding memory to Mem0 cloud: Connection timeout
```

**Root Cause:**
- Missing or invalid Mem0 Cloud API key
- Network connectivity issues to Mem0 Cloud service
- Switched from local Mem0 (with OpenAI dependency) to Mem0 Cloud API

**Solution:**
1. Ensure valid Mem0 Cloud API key in `.env`:
```bash
MEM0_API_KEY="your_mem0_cloud_api_key"
```
2. Get API key from https://mem0.ai/dashboard
3. Verify connectivity:
```python
python -c "from src.integrations.mem0_cloud import test_mem0_cloud; import asyncio; asyncio.run(test_mem0_cloud())"
```

**Files Updated:**
- `src/core/agent.py`
- `src/core/treasury.py`
- `src/core/memory_manager.py`
- `src/core/market_detector.py`
- `src/workflows/nodes.py`
- `src/workflows/market_analysis_flow.py`
- `src/integrations/__init__.py`

---

## Firestore API Issues

### Issue: Missing Firestore Client Methods
**Error Messages:**
```
❌ Failed to initialize position manager: 'FirestoreClient' object has no attribute 'get_document'
❌ Failed to collect gas data: 'FirestoreClient' object has no attribute 'collection'
```

**Root Cause:**
- Code was calling non-existent methods on FirestoreClient
- FirestoreClient exposes the raw Firestore client as `self.db`

**Solution:**
Replace custom method calls with direct Firestore API:

```python
# Before
position_data = await self.firestore.get_document("positions", doc_id)
await self.firestore.collection('agent_data').document('doc').set(data)

# After
doc_ref = self.firestore.db.collection("positions").document(doc_id)
doc = doc_ref.get()
position_data = doc.to_dict() if doc.exists else None
self.firestore.db.collection('agent_data').document('doc').set(data)
```

**Files Updated:**
- `src/core/position_manager.py`
- `src/data/market_data_collector.py`

---

## LLM Integration Issues

### Issue: OpenAI API Key Required When Using Gemini
**Error Messages:**
```
❌ Agent initialization failed: The api_key client option must be set either by passing api_key to the client or by setting the OPENAI_API_KEY environment variable
```

**Root Cause:**
- Workflows importing OpenAI/Anthropic clients without try/except blocks
- Mem0 local version requires OpenAI for embeddings

**Solution:**
1. Wrap optional LLM imports in try/except:
```python
try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None
```

2. Use Mem0 Cloud instead of local Mem0 (no OpenAI dependency)
3. Configure Gemini as primary LLM through `llm_factory.py`

**Files Updated:**
- `src/integrations/llm_integration.py`
- `src/workflows/decision_flow.py`
- `src/workflows/market_analysis_flow.py`

---

## CDP Integration Issues

### Issue: CDP SDK Not Available
**Warning Message:**
```
CDP SDK not available. Running in simulation mode.
```

**Root Cause:**
- CDP SDK requires Python 3.10+
- CDP SDK not installed or import fails

**Solution:**
1. Ensure Python 3.10+ is used
2. Install CDP SDK: `pip install cdp-sdk`
3. Code automatically falls back to simulation mode when SDK unavailable

**Current Status:**
- Running in simulation mode for Phase 1 (observer only)
- Wallet connected: `0x2f9930A9d7018Ef28a8577ca9fA2125dA511A0A8`

---

## Workflow Issues

### Issue: Recursion Limit Reached
**Error Message:**
```
❌ Critical error in consciousness cycle: Recursion limit of 25 reached without hitting a stop condition.
```

**Root Cause:**
- Cognitive loop workflow created an infinite loop within the graph
- LangGraph has a default recursion limit of 25

**Solution:**
Change the workflow to end after each cycle:
```python
# Before
workflow.add_edge("learn", "sense")  # Infinite loop

# After  
workflow.add_edge("learn", END)      # End after each cycle
```

The agent's main loop calls the workflow repeatedly, avoiding recursion issues.

**Files Updated:**
- `src/workflows/cognitive_loop.py`

---

## Market Data Collection Issues

### Issue: External API Dependencies
**Error Messages:**
```
DefiLlama collection failed: DefiLlama API error: 404
CoinGecko collection failed: CoinGecko API error: 429
```

**Root Cause:**
- Agent was trying to use external APIs (CoinGecko, DefiLlama) for market data
- No API keys configured for these services
- Agent should use CDP for BASE network data

**Solution:**
1. Created `collect_base_network_data()` method that uses CDP
2. Updated `collect_comprehensive_market_data()` to prioritize BASE data
3. Pass CDP integration to market data collector

```python
# Agent now passes CDP to market data collector
market_result = await self.market_data_collector.collect_comprehensive_market_data(self.cdp)
```

**Files Updated:**
- `src/data/market_data_collector.py`
- `src/core/agent.py`

---

## Common Solutions

### Environment Variables
Ensure these are set in your `.env` file:
```bash
# Required
CDP_API_KEY_NAME="your_cdp_key"
CDP_API_KEY_SECRET="your_cdp_secret"
MEM0_API_KEY="your_mem0_cloud_key"
GOOGLE_APPLICATION_CREDENTIALS="path/to/gcp-key.json"

# Optional (not required with current setup)
OPENAI_API_KEY="only_if_using_openai"
ANTHROPIC_API_KEY="only_if_using_claude"
```

### Python Version
- Use Python 3.10+ for full CDP support
- Virtual environment: `python3.10 -m venv venv310`

### Quick Checks
1. **Memory System**: Verify Mem0 Cloud is working
```bash
python -c "from src.integrations.mem0_cloud import Mem0CloudIntegration; print('✅ Mem0 Cloud available')"
```

2. **CDP Status**: Check wallet connection
```bash
python -c "import asyncio; from src.integrations.cdp_integration import CDPIntegration; cdp = CDPIntegration(); asyncio.run(cdp.initialize_wallet())"
```

3. **Agent Status**: Run status check
```bash
python -m src.core.agent --status
```

---

## Debugging Tips

1. **Enable Debug Logging**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

2. **Check Component Initialization Order**:
- Firestore/BigQuery → Mem0 Cloud → CDP → Core Components

3. **Monitor Costs**:
- Check `wallet_data/athena_production_wallet.json` for balance updates
- Monitor BigQuery for cost tracking data

4. **Workflow Debugging**:
- Use LangSmith for workflow traces
- Check recursion limits and cycle counts

---

## Enhanced Architecture Issues

### Issue: LLM Workflow Integration Not Working
**Error Messages:**
```
❌ ImportError: cannot import name 'LLMWorkflowIntegration' from 'src.integrations'
❌ Dynamic model selection not activating based on treasury balance
```

**Root Cause:**
- New LLM workflow integration module not fully implemented
- Missing imports in workflow nodes
- Model selection logic not connected to treasury state

**Solution:**
1. Ensure `llm_workflow_integration.py` exists and is properly imported
2. Update workflow nodes to use integrated LLM functionality:
```python
from ..integrations.llm_workflow_integration import LLMWorkflowIntegration
```
3. Connect treasury balance to model selection in workflows

### Issue: Parallel Processing Not Executing
**Error Messages:**
```
❌ Parallel tasks timing out
❌ asyncio.gather() not executing tasks concurrently
```

**Root Cause:**
- Workflow nodes not properly configured for async execution
- Missing await statements in parallel task execution

**Solution:**
1. Ensure all node functions are async:
```python
async def parallel_sense(state):
    results = await asyncio.gather(
        sense_market(),
        sense_wallet(),
        sense_memories()
    )
```
2. Configure LangGraph for parallel execution support

### Issue: Enhanced State Not Persisting
**Error Messages:**
```
❌ AttributeError: 'ConsciousnessState' object has no attribute 'llm_model'
❌ State missing enhanced fields after workflow execution
```

**Root Cause:**
- State definition mismatch between enhanced and basic versions
- Migration from basic to enhanced state incomplete

**Solution:**
1. Update state definitions in `src/workflows/state.py`
2. Ensure all workflow nodes use enhanced state structure
3. Add migration logic for existing state data

---

## Contact & Support

For issues not covered here:
1. Check logs in CloudWatch/GCP Logging
2. Review LangSmith traces for workflow issues
3. Open an issue on GitHub with error logs
4. Review docs/ENHANCED_ARCHITECTURE.md for implementation details