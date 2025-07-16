# V1 Development Guide: Aerodrome Finance Observer

## Executive Summary

This document provides a complete implementation guide for V1 of the Athena DeFi AI Agent project. V1 focuses on implementing an observation-only system for Aerodrome Finance with emotional intelligence, survival instincts, and continuous learning using GCP, Mem0 Cloud, and CDP AgentKit on the BASE network.

**Key Objectives:**
- Implement Aerodrome pool observation with $100 starting capital
- Create emotional state-driven decision making (desperate, cautious, stable, confident)
- Build pattern recognition through market observation
- Develop memory formation about market conditions and opportunities
- Establish survival memory formation during critical periods
- Prepare foundation for V2 trading capabilities

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        GCP PROJECT                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │ Cloud       │  │ Firestore   │  │ BigQuery    │  │ Secret  │ │
│  │ Functions   │  │ (Real-time) │  │ (Analytics) │  │ Manager │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  LANGGRAPH NERVOUS SYSTEM                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Cognitive Loop (Consciousness)              │   │
│  │  ┌─────┐→┌─────┐→┌─────┐→┌──────┐→┌─────┐             │   │
│  │  │Sense│ │Think│ │Feel │ │Decide│ │Learn│──┐          │   │
│  │  └─────┘ └─────┘ └─────┘ └──────┘ └─────┘  │          │   │
│  │     ▲                                         │          │   │
│  │     └─────────────────────────────────────────┘          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ Yield       │  │ Position    │  │ Emotional   │            │
│  │ Optimizer   │  │ Manager     │  │ Router      │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AERODROME OBSERVER                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │   CDP       │  │ Pool        │  │ Pattern     │  │ Mem0    │ │
│  │ AgentKit    │  │ Observer    │  │ Detector    │  │ Cloud   │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

**Technology Stack:**
- **Backend**: Python 3.10+, FastAPI
- **Nervous System**: LangGraph (Unified cognitive loop)
- **DeFi Protocol**: Aerodrome Finance on BASE (observation only)
- **Memory**: Mem0 Cloud API
- **Database**: Google Firestore (operational), BigQuery (analytics)
- **Blockchain**: CDP AgentKit (BASE network)
- **Infrastructure**: Google Cloud Platform
- **AI**: Dynamic LLM selection (Haiku → GPT-3.5 → Sonnet → Opus)
- **Monitoring**: LangSmith (Workflow tracing)

---

## 1. V1 Specific Components

### 1.1 Emotional State System

The emotional state system is the CORE of V1, driving all decisions:

```python
# src/workflows/emotional_router.py

class EmotionalState:
    DESPERATE = "desperate"    # < 7 days runway
    CAUTIOUS = "cautious"      # < 20 days runway  
    STABLE = "stable"          # < 90 days runway
    CONFIDENT = "confident"    # > 90 days runway

def emotional_router(state: ConsciousnessState) -> str:
    """Route execution based on emotional state"""
    days_remaining = state["days_until_bankruptcy"]
    
    if days_remaining < 7:
        return "survival_mode"
    elif days_remaining < 20:
        return "conservative_mode"
    elif days_remaining < 90:
        return "normal_mode"
    else:
        return "growth_mode"
```

### 1.2 Observation Decision Engine

V1's core logic for observation frequency based on emotional state:

```python
# src/core/consciousness.py

def get_observation_frequency_minutes(self) -> int:
    """Determine observation frequency based on emotional state"""
    
    frequencies = {
        EmotionalState.DESPERATE: 240,    # 4 hours - conserve resources
        EmotionalState.CAUTIOUS: 120,     # 2 hours - careful monitoring
        EmotionalState.STABLE: 60,        # 1 hour - regular observation
        EmotionalState.CONFIDENT: 30      # 30 minutes - aggressive learning
    }
    return frequencies.get(self.emotional_state, 60)
```

### 1.3 Survival Memory Formation

Critical for V1 - permanent memories during desperate times:

```python
# src/core/memory_manager.py

async def form_survival_memory(self, experience: Dict, emotional_state: str):
    """Form special survival memories during desperate times"""
    
    if emotional_state == "desperate":
        # These memories are PERMANENT and HIGH IMPORTANCE
        memory = {
            "content": f"[SURVIVAL] {experience['description']}",
            "category": "survival_critical",
            "importance": 1.0,  # Maximum importance
            "metadata": {
                "treasury_balance": experience["treasury_balance"],
                "days_left": experience["days_until_bankruptcy"],
                "action_taken": experience["action"],
                "outcome": experience["outcome"],
                "permanent": True  # Never forget survival lessons
            }
        }
```

---

## 2. V1 Data Collection Schedule

### 2.1 Pool Observation (Based on Emotional State)

```python
# src/workflows/nodes/sense.py

async def _sense_pools(aerodrome: AerodromeObserver, state: ConsciousnessState):
    """Observe Aerodrome pools for patterns"""
    
    try:
        pools = await aerodrome.get_top_pools(limit=10)
        
        # Analyze each pool
        for pool in pools:
            observation = {
                "timestamp": datetime.utcnow(),
                "pool_address": pool["address"],
                "tokens": pool["tokens"],
                "tvl_usd": pool["tvl_usd"],
                "volume_24h": pool["volume_24h"],
                "apy_total": pool["apy"]["total"],
                "volume_tvl_ratio": pool["volume_24h"] / pool["tvl_usd"]
            }
            
            # Store observation
            state.observed_pools.append(PoolObservation(**observation))
    except Exception as e:
        logger.error(f"Pool observation error: {e}")
```

### 2.2 Pattern Detection (During Think Node)

```python
# src/workflows/nodes/think.py

async def think_analysis(state: ConsciousnessState) -> ConsciousnessState:
    """Analyze observations and detect patterns"""
    
    # Analyze pool patterns
    patterns = []
    for pool in state.observed_pools:
        if pool.volume_tvl_ratio > 0.5:  # High activity
            patterns.append(Pattern(
                type="high_activity_pool",
                description=f"{pool.tokens} showing high volume/TVL ratio",
                confidence=0.8
            ))
    
    state.active_patterns = patterns
    return state
```

---

## 3. Cognitive Loop Workflow

### 3.1 LangGraph Workflow Definition

```python
# src/workflows/cognitive_loop.py

def create_cognitive_workflow(...):
    """Create the main cognitive loop workflow"""
    
    workflow = StateGraph(ConsciousnessState)
    
    # Add nodes
    workflow.add_node("sense", sense_environment)
    workflow.add_node("think", think_analysis)
    workflow.add_node("feel", feel_emotions)
    workflow.add_node("decide", make_decision)
    workflow.add_node("learn", learn_patterns)
    
    # Define linear flow for V1
    workflow.add_edge(START, "sense")
    workflow.add_edge("sense", "think")
    workflow.add_edge("think", "feel")
    workflow.add_edge("feel", "decide")
    workflow.add_edge("decide", "learn")
    workflow.add_edge("learn", END)
    
    return workflow.compile()
```

### 3.2 Memory Formation and Learning

V1 learns from observations and forms memories:

```python
# src/workflows/nodes/learn.py

async def learn_patterns(state: ConsciousnessState) -> ConsciousnessState:
    """Form memories from observations and patterns"""
    
    memory_client = MemoryClient()
    
    # Form memories about high-value patterns
    for pattern in state.active_patterns:
        if pattern.confidence > 0.7:
            memory = {
                "content": pattern.description,
                "category": "market_patterns",
                "metadata": {
                    "pattern_type": pattern.type,
                    "confidence": pattern.confidence,
                    "timestamp": datetime.utcnow().isoformat(),
                    "emotional_state": state.emotional_state.value
                }
            }
            
            await memory_client.add_memory(
                state.agent_id,
                memory["content"],
                memory["category"],
                memory["metadata"]
            )
    
    return state
```

---

## 4. Pool Observation Management

### 4.1 Pool Observation State

```python
@dataclass
class PoolObservation:
    """Observed Aerodrome pool data"""
    pool_address: str
    tokens: List[str]
    tvl_usd: float
    volume_24h: float
    apy_fees: float
    apy_rewards: float
    apy_total: float
    volume_tvl_ratio: float
    timestamp: datetime
    emotional_state_when_observed: str
```

### 4.2 Pattern Recognition

```python
@dataclass
class Pattern:
    """Recognized market pattern"""
    type: str  # high_activity, yield_spike, volume_surge
    description: str
    confidence: float
    pools_involved: List[str]
    timestamp: datetime
    
    def is_actionable(self, emotional_state: EmotionalState) -> bool:
        """Check if pattern warrants action based on emotional state"""
        
        confidence_thresholds = {
            EmotionalState.DESPERATE: 0.9,  # Only highest confidence
            EmotionalState.CAUTIOUS: 0.8,
            EmotionalState.STABLE: 0.7,
            EmotionalState.CONFIDENT: 0.6
        }
        
        return self.confidence >= confidence_thresholds.get(emotional_state, 0.8)
```

---

## 5. CDP AgentKit Integration

### 5.1 Wallet Management (Observation Only)

```python
# src/blockchain/cdp_client.py

class CDPClient:
    """CDP AgentKit wrapper for V1 observation"""
    
    def __init__(self):
        self.simulation_mode = not all([
            settings.cdp_api_key_name,
            settings.cdp_api_key_secret
        ])
        
        if self.simulation_mode:
            self._simulated_balance = settings.starting_treasury
    
    async def get_wallet_balance(self) -> float:
        """Get wallet balance in USD"""
        
        if self.simulation_mode:
            # Simulate slight balance changes
            return self._simulated_balance * random.uniform(0.98, 1.02)
        
        # Real CDP implementation would go here
        return 100.0
    
    async def get_gas_price(self) -> float:
        """Get current gas price in gwei"""
        
        if self.simulation_mode:
            # Simulate realistic gas patterns
            hour = datetime.utcnow().hour
            base_price = 1.5
            
            # Lower at night and weekends
            if 2 <= hour <= 6:
                base_price *= 0.7
            
            return base_price * random.uniform(0.8, 1.2)
```

---

## 6. V1 Success Metrics

### 6.1 Key Performance Indicators

```python
v1_success_metrics = {
    "survival": {
        "never_bankrupt": True,  # Must maintain positive balance
        "days_operational": 30,  # Minimum 30 days
        "cost_control": "< $100/month"  # Stay within budget
    },
    
    "observation_quality": {
        "pools_monitored": "> 100 unique",  # Diverse observation
        "patterns_identified": "> 10",  # Pattern recognition
        "memory_formation_rate": "> 3/day"  # Active learning
    },
    
    "learning": {
        "market_patterns_identified": True,
        "gas_patterns_identified": True,
        "survival_memories_formed": True,
        "pool_behavior_understood": True
    },
    
    "emotional_intelligence": {
        "state_transitions": "appropriate",
        "observation_frequency_adaptation": "correct",
        "cost_optimization_behavior": "demonstrated"
    }
}
```

### 6.2 Daily Performance Tracking

```sql
-- BigQuery query for V1 observation performance
SELECT 
    DATE(timestamp) as date,
    COUNT(DISTINCT pool_address) as unique_pools_observed,
    COUNT(*) as total_observations,
    AVG(confidence) as avg_pattern_confidence,
    COUNT(DISTINCT pattern_type) as pattern_types_found,
    STRING_AGG(DISTINCT emotional_state) as emotional_states
FROM `athena.observations`
WHERE DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY date
ORDER BY date DESC;
```

---

## 7. Testing V1 Implementation

### 7.1 Test Script

```python
# test_setup.py

async def test_v1_components():
    """Test V1 Aerodrome observer implementation"""
    
    # Test imports
    from src.core import AthenaAgent, ConsciousnessState, EmotionalState
    from src.workflows import create_cognitive_workflow
    from src.aerodrome import AerodromeObserver
    
    # Test consciousness state
    state = ConsciousnessState(
        agent_id="test",
        treasury_balance=100.0,
        emotional_state=EmotionalState.STABLE
    )
    
    # Test observation frequency
    frequency = state.get_observation_frequency_minutes()
    print(f"Observation frequency: {frequency} minutes")
    
    # Test cognitive workflow
    workflow = create_cognitive_workflow(...)
    result = await workflow.ainvoke(state)
```

### 7.2 Simulation Mode

V1 includes full simulation support for testing without real deployment:

```python
# Simulation provides:
- Realistic pool data (TVL, volume, APY)
- Gas price patterns (lower on weekends/nights)
- Wallet balance tracking
- Pattern detection
- Memory formation
- Emotional state transitions
```

---

## 8. V1 Launch Checklist

### Pre-Launch Requirements

```python
v1_launch_checklist = {
    "infrastructure": [
        "✓ GCP project configured",
        "✓ Firestore collections created",
        "✓ BigQuery tables initialized",
        "✓ Cloud Run deployment ready",
        "✓ Monitoring dashboards ready"
    ],
    
    "code": [
        "✓ CDP integration (simulation mode)",
        "✓ Aerodrome observer implemented",
        "✓ Cognitive loop workflow",
        "✓ Memory formation system",
        "✓ Pattern detection logic",
        "✓ Agent orchestration complete"
    ],
    
    "testing": [
        "✓ Component tests passing",
        "✓ Integration tests passing",
        "✓ Simulation mode working",
        "✓ Emotional state transitions",
        "✓ Memory formation verified"
    ],
    
    "configuration": [
        "✓ Starting treasury: $100",
        "✓ Aerodrome on BASE (observation)",
        "✓ Emotional thresholds set",
        "✓ Observation frequencies configured",
        "✓ Memory categories defined"
    ]
}
```

### Launch Command

```bash
# Launch V1 Aerodrome Observer
cd /path/to/athena

# Setup
cp deployment/.env.example .env
python scripts/setup.py

# Test
python test_setup.py

# Run V1 agent
python -m src.core.agent

# Or with API
python scripts/run_with_api.py

# Docker deployment
docker-compose up
```

---

## 9. V1 Operational Guide

### 9.1 Daily Operations

```python
# The agent automatically:
1. Observes Aerodrome pools based on emotional state (30min-4hr)
2. Detects patterns in pool behavior
3. Forms memories about market conditions
4. Adjusts observation frequency with treasury health
5. Tracks all operational costs
6. Maintains cost-aware behavior
```

### 9.2 Monitoring V1 Performance

Key metrics to monitor:
- Treasury balance trend
- Observation frequency and coverage
- Pattern detection accuracy
- Emotional state distribution
- Memory formation rate (target: 3+/day)
- Monthly operational cost (target: <$100)

### 9.3 Emergency Procedures

If agent enters desperate mode:
- Reduces observation to every 4 hours
- Uses cheapest LLM model (Haiku)
- Forms permanent survival memories
- Focuses on cost reduction
- Only observes highest-value patterns

---

## 10. V1 to V2 Evolution Path

### What V1 Proves

1. **Emotional Intelligence Works**: Agent adapts behavior to survival pressure
2. **Memory-Driven Learning**: Forms memories about market patterns
3. **Cost-Aware Operations**: Maintains budget with dynamic optimization
4. **Robust Architecture**: LangGraph cognitive loop handles complexity

### V2 Enhancements

After 30 days of successful V1 observation:
- Enable actual trading on Aerodrome
- Implement leverage management (1-3x)
- Add position execution logic
- Create risk management system
- Activate yield farming strategies

---

## Conclusion

V1 implements a focused, emotionally-intelligent DeFi observer that:
- ✅ Observes Aerodrome Finance pools continuously
- ✅ Learns market patterns through observation
- ✅ Adjusts behavior based on treasury health
- ✅ Forms memories about opportunities and risks
- ✅ Maintains operations within $100/month budget
- ✅ Demonstrates true autonomous intelligence

The successful completion of V1 proves that an AI agent with emotional intelligence and survival instincts can effectively observe and learn from DeFi markets, setting the foundation for active trading strategies in V2.

**Ready to deploy the Aerodrome Observer!** 🚀