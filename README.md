# 🏛️ Athena DeFi Agent

An autonomous AI agent with genuine survival instincts, unified consciousness via LangGraph, and adaptive behavior operating on the BASE network. V1 implements a focused Compound V3 yield strategy with emotional intelligence.

## 🌟 Features

### Core Capabilities
- **LangGraph Nervous System**: Unified consciousness through Sense → Think → Feel → Decide → Learn cycle
- **Emotional Intelligence**: Dynamic emotional states (desperate → cautious → stable → confident) that affect behavior
- **Adaptive Operation**: Automatically adjusts observation frequency and costs based on treasury health
- **Persistent Memory**: Uses Mem0 for memory formation and learning from experiences
- **Real Blockchain Integration**: CDP AgentKit for BASE network wallet management
- **Market Intelligence**: Observes and analyzes DeFi market conditions
- **Cost Consciousness**: Tracks every operation cost with survival pressure
- **Transparent Operations**: Full observability via LangSmith tracing

### V1 Specific Features (Compound V3 Strategy)
- **Yield Optimization**: Automated compounding on Compound V3 with profitability checks
- **Gas Pattern Learning**: Identifies optimal gas windows (weekends, 2-4 AM UTC)
- **Emotional Multipliers**: Requires 1.5x-3x gas coverage based on emotional state
- **Survival Memories**: Forms permanent memories during desperate situations
- **Position Tracking**: Complete position state management and performance metrics
- **Compound History**: Tracks all compound events with reasoning and outcomes

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    LANGGRAPH NERVOUS SYSTEM                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Sense → Think → Feel → Decide → Learn → (cycle)        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Emotional States: desperate ↔ cautious ↔ stable ↔ confident    │
│  Operational Modes: survival → conservative → normal → growth   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    V1 COMPOUND STRATEGY                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │ Position    │  │ Yield       │  │ Gas         │  │ Survival│ │
│  │ Manager     │  │ Optimizer   │  │ Patterns    │  │ Memory  │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        GCP PROJECT                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │ Cloud       │  │ Firestore   │  │ BigQuery    │  │ Secret  │ │
│  │ Functions   │  │ (Real-time) │  │ (Analytics) │  │ Manager │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+ (Required for CDP SDK)
- Google Cloud Platform account
- Coinbase Developer Platform account
- BASE testnet access (via CDP)
- API keys for: Anthropic, Mem0, CDP, LangSmith

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/athena-defi-agent.git
cd athena-defi-agent
```

2. Create virtual environment with Python 3.10+:
```bash
python3.10 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

5. Set up CDP (Coinbase Developer Platform):
```bash
# Follow the guide at docs/cdp_setup_guide.md
# Test your setup:
python test_cdp.py
```

6. Set up GCP:
```bash
# Install gcloud CLI if not already installed
# Run setup script
python scripts/setup_gcp.py
```

### Running the Agent

```bash
# Run V1 Compound strategy
python -m src.core.agent

# Run with Docker
docker-compose up

# Run with LangSmith tracing
LANGSMITH_API_KEY=your_key python -m src.core.agent

# Test V1 components
python test_v1_compound.py
```

## 🧠 LangGraph Nervous System

The agent uses a unified consciousness model with 5 cognitive nodes:

1. **Sense** 👁️ - Perceive environment (market data, wallet balance)
2. **Think** 🧠 - Analyze conditions and detect patterns
3. **Feel** 💭 - Update emotional state based on treasury health
4. **Decide** 🎯 - Make decisions based on emotional context
5. **Learn** 📚 - Form memories and consolidate experiences

### Emotional States & Behavior

| Days Until Bankruptcy | Emotional State | Operational Mode | Compound Multiplier | Observation Interval |
|-----------------------|-----------------|------------------|-------------------|---------------------|
| < 7 days              | Desperate 😱    | Survival         | 3.0x gas cost    | 4 hours            |
| < 20 days             | Cautious 😟     | Conservative     | 2.0x gas cost    | 2 hours            |
| < 90 days             | Stable 😊       | Normal           | 1.5x gas cost    | 1 hour             |
| > 90 days             | Confident 😎    | Growth           | 1.5x gas cost    | 30 minutes         |

### V1 Compound Strategy Behavior

- **Data Collection**: Gas prices every 5 min, Compound APY every 15 min
- **Yield Check**: Every 4 hours (adjusts with emotional state)
- **Gas Optimization**: Learns patterns, prefers 2-4 AM UTC weekends
- **Compound Logic**: Only compounds when `rewards > multiplier × gas_cost`
- **Survival Mode**: Forms permanent memories, ultra-conservative

## 📊 V1 Success Criteria

### Core Requirements
- ✅ 30+ days continuous operation
- ✅ Never bankrupt (maintain positive treasury)
- ✅ Net profitable after gas costs
- ✅ Successful Compound V3 integration
- ✅ Appropriate emotional state transitions

### Learning & Optimization
- ✅ Gas pattern identification (weekends, night hours)
- ✅ Optimal compound frequency discovered
- ✅ Survival memories formed during desperate times
- ✅ Average gas cost < $0.50 per compound
- ✅ Compound efficiency > 80%

### V1 Metrics
- Starting Capital: $30 USDC
- Target APY: 4-5% on Compound V3
- Gas Budget: < 20% of rewards
- Compound Frequency: Every 2-4 days (optimized)
- Emergency Threshold: < 7 days runway

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test suites
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
```

## 📈 Monitoring

- **LangSmith**: View agent decision traces at https://smith.langchain.com
- **GCP Console**: Monitor costs, logs, and performance
- **Daily Reports**: Check `reports/daily/` for operational summaries

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Anthropic for Claude AI
- LangChain team for LangGraph and LangSmith
- Coinbase for CDP AgentKit
- Mem0 for the memory system

---

**Built with ❤️ for the future of autonomous DeFi**