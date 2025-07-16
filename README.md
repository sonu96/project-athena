# 🏛️ Athena DeFi Agent

An autonomous AI agent with emotional intelligence designed for leverage trading on Aerodrome Finance. V1 implements observation mode with memory formation and pattern recognition.

## 🌟 Features

### V1 - Observer Mode (Current)
- **Emotional Intelligence**: Dynamic states (desperate → cautious → stable → confident) affecting behavior
- **Memory Formation**: Learns patterns using Mem0 Cloud API
- **Cost-Aware Operation**: Tracks every operation for survival pressure
- **Pool Observation**: Monitors Aerodrome pools without trading
- **Pattern Recognition**: Identifies profitable opportunities
- **24/7 Operation**: Production-ready autonomous agent

### V2 - Trading Mode (Coming Soon)
- Active leverage trading (1-3x based on emotional state)
- Risk management and liquidation prevention
- P&L tracking and optimization

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Google Cloud Platform account
- CDP (Coinbase Developer Platform) API keys
- Mem0 Cloud API key
- LangSmith API key (optional but recommended)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/athena.git
cd athena
```

2. Create virtual environment:
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
cp deployment/.env.example .env
# Edit .env with your API keys and configuration
```

5. Run the agent:
```bash
python -m src.core.agent
```

## 📊 Architecture

```
Cognitive Loop:
START → Sense → Think → Feel → Decide → Learn → END
         ↑                                        ↓
         └────────────(next cycle)────────────────┘

Emotional States:
- DESPERATE (< 7 days): Survival mode, minimal operations
- CAUTIOUS (< 20 days): Conservative, careful observation  
- STABLE (< 90 days): Balanced approach
- CONFIDENT (> 90 days): Growth oriented, frequent observations
```

## 🔧 Configuration

See `deployment/.env.example` for all configuration options. Key settings:

- `STARTING_TREASURY`: Initial balance (default: $100)
- `NETWORK`: Blockchain network (use `base-sepolia` for testing)
- `OBSERVATION_MODE`: Set to `true` for V1 (no trading)

## 📈 Monitoring

- **LangSmith**: View cognitive loop traces
- **API**: Health checks and metrics at `http://localhost:8080`
- **WebSocket**: Real-time updates at `ws://localhost:8080/ws`

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test suite
pytest tests/unit/
```

## 🚢 Deployment

### Local Testing with Mainnet

```bash
# Test mainnet connection
python test_mainnet.py

# Run continuous test (10 minutes)
python test_mainnet.py --continuous 10
```

### Deploy to Google Cloud Run (24/7)

```bash
# Use the deployment script
./deploy_cloud.sh

# Or manually:
# 1. Build and push Docker image
docker build -t gcr.io/project-athena-development/athena-agent:latest .
docker push gcr.io/project-athena-development/athena-agent:latest

# 2. Deploy to Cloud Run
gcloud run deploy athena-agent-mainnet \
  --image gcr.io/project-athena-development/athena-agent:latest \
  --region us-central1 \
  --memory 4Gi \
  --cpu 2 \
  --min-instances 1 \
  --max-instances 3

# 3. Monitor logs
gcloud logging read "resource.labels.service_name=athena-agent-mainnet" --limit=50
```

### Production Configuration

Use `.env.mainnet` for production settings with BASE mainnet addresses.

## 📖 Documentation

- [CLAUDE.md](CLAUDE.md) - Comprehensive implementation guide
- [docs/API.md](docs/API.md) - API documentation
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) - Deployment guide
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - Technical architecture

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- LangChain team for LangGraph
- Coinbase for CDP AgentKit
- Mem0 for the memory system
- Aerodrome Finance for the protocol

---

**Built with ❤️ for the future of autonomous DeFi**