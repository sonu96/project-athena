# 🏛️ Athena DeFi Agent

An autonomous AI agent with genuine survival instincts, memory-driven decision making, and market observation capabilities operating on the BASE network.

## 🌟 Features

- **Emotional AI**: Agent with survival pressure and emotional states (stable → cautious → desperate)
- **Persistent Memory**: Uses Mem0 for memory formation and learning from experiences
- **Market Intelligence**: Observes and analyzes DeFi market conditions
- **Cost Consciousness**: Tracks every operation cost with treasury management
- **Transparent Operations**: Full observability via LangSmith tracing

## 🏗️ Architecture

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
│                     AGENT CORE SYSTEM                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │   Mem0      │  │ LangGraph   │  │ CDP         │  │ Market  │ │
│  │ (Memory)    │  │ (Workflow)  │  │ AgentKit    │  │ Data    │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Google Cloud Platform account
- BASE testnet access
- API keys for: Anthropic, Mem0, CDP, LangSmith

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/athena-defi-agent.git
cd athena-defi-agent
```

2. Create virtual environment:
```bash
python -m venv venv
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

5. Set up GCP:
```bash
# Install gcloud CLI if not already installed
# Run setup script
python scripts/setup_gcp.py
```

### Running the Agent

```bash
# Run locally
python -m src.core.agent

# Run with Docker
docker-compose up

# Run with LangSmith tracing
LANGSMITH_API_KEY=your_key python -m src.core.agent
```

## 📊 Phase 1 Success Criteria

- ✅ 30+ days continuous operation
- ✅ 100+ meaningful memories formed
- ✅ <$300 total operational costs
- ✅ Accurate market condition detection
- ✅ Appropriate emotional state transitions

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