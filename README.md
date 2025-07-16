# 🏛️ Athena DeFi Agent

An autonomous AI agent with emotional intelligence designed for leverage trading on Aerodrome Finance. Features enterprise-grade security with Google Cloud Secret Manager and guaranteed cost protection with a $30 spending limit.

## 🌟 Features

### V1 - Observer Mode (Current)
- **Emotional Intelligence**: Dynamic states (desperate → cautious → stable → confident) affecting behavior
- **Memory Formation**: Learns patterns using Mem0 Cloud API
- **Cost Protection**: Guaranteed $30 spending limit with automatic shutdown
- **Enterprise Security**: Zero secret exposure with Google Cloud Secret Manager
- **Pool Observation**: Monitors Aerodrome pools without trading
- **Pattern Recognition**: Identifies profitable opportunities
- **24/7 Operation**: Production-ready autonomous agent with cost protection

### 🔐 Security & Cost Management
- **Google Cloud Secret Manager**: All secrets stored securely, zero code exposure
- **$30 Hard Limit**: Automatic shutdown prevents overspending
- **Real-time Cost Tracking**: Monitor spending across all services
- **Progressive Alerts**: Warnings at $5, $10, $20, $25, and $30
- **Emergency Mode**: Switches to cheapest models at $20 spent
- **Cost-Aware LLM Selection**: Model choice based on budget and emotional state

### V2 - Trading Mode (Coming Soon)
- Active leverage trading (1-3x based on emotional state)
- Risk management and liquidation prevention
- P&L tracking and optimization

## 🚀 Quick Start

### Prerequisites
- Python 3.11+ (required for CDP SDK)
- Google Cloud Platform account with billing enabled
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
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
pip install google-cloud-secret-manager  # For secure secret management
```

4. Set up Google Cloud Secret Manager:
```bash
# Create Google Cloud project
gcloud projects create athena-agent-prod --name="Athena DeFi Agent Production"
gcloud config set project athena-agent-prod

# Enable required APIs
gcloud services enable secretmanager.googleapis.com
gcloud services enable aiplatform.googleapis.com

# Authenticate
gcloud auth application-default login
```

5. Configure secrets securely:
```bash
# Copy the secure template
cp .env.example .env
# Edit .env with your API keys (for development only)

# For production, migrate to Secret Manager:
python3.11 scripts/migrate_secrets.py

# Verify secret storage:
python3.11 scripts/test_secrets.py
```

6. Run the agent:
```bash
python -m src.core.agent
```

## 📊 Architecture

```
Cognitive Loop with Cost Protection:
START → Sense → Think → Feel → Decide → Learn → END
         ↑                                        ↓
         └────────────(next cycle)────────────────┘
                              |
                    Cost Manager ($30 limit)
                              |
                    ┌─────────┴─────────┐
                    ↓                   ↓
              LLM Router         Secret Manager
           (Budget-aware)        (Secure storage)

Emotional States & Model Selection:
- DESPERATE (< 7 days): gemini-2.0-flash-exp (free tier)
- CAUTIOUS (< 20 days): gemini-2.0-flash-exp (free tier)
- STABLE (< 90 days): gemini-1.5-pro ($1.25/1M tokens)
- CONFIDENT (> 90 days): gemini-1.5-pro ($1.25/1M tokens)

Cost Protection Alerts:
$5 → Warning | $10 → Reduce frequency | $20 → Emergency mode
$25 → Prepare shutdown | $30 → HARD STOP
```

## 🔧 Configuration

### Environment Configuration
See `.env.example` for all configuration options. Key settings:

**Security (Production):**
- Use Google Cloud Secret Manager for all secrets
- Never commit `.env` files with real secrets
- All sensitive credentials stored securely

**Agent Settings:**
- `STARTING_TREASURY`: Initial balance (default: $100)
- `NETWORK`: Blockchain network (`base` for mainnet, `base-sepolia` for testing)
- `OBSERVATION_MODE`: Set to `false` for V1 (observation only)
- `GCP_PROJECT_ID`: Google Cloud project (`athena-agent-prod`)

**Cost Protection:**
- `MAX_DAILY_COST`: Currently fixed at $30 hard limit
- Cost tracking automatic - no configuration needed
- Emergency shutdown built-in

## 📈 Monitoring

### Real-time Monitoring
- **Cost Dashboard**: Built-in spending tracker with $30 limit
- **LangSmith**: View cognitive loop traces and LLM calls
- **Google Cloud Console**: Secret Manager and project monitoring
- **API**: Health checks and metrics at `http://localhost:8080`
- **WebSocket**: Real-time updates at `ws://localhost:8080/ws`

### Cost Monitoring Commands
```bash
# Check current spending
python3.11 -c "from src.monitoring.cost_manager import cost_manager; print(cost_manager.get_cost_summary())"

# Test cost protection
python3.11 test_cost_limit_enforcement.py

# Monitor real-time costs during operation
tail -f logs/cost_tracking.json
```

## 🧪 Testing

### Unit Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test suite
pytest tests/unit/
```

### Integration Tests
```bash
# Test mainnet connection and data fetching
python3.11 test_mainnet.py

# Test Secret Manager integration
python3.11 scripts/test_secrets.py

# Test cost management system
python3.11 test_cost_limit_enforcement.py

# Test Gemini API integration
python3.11 test_direct_gemini.py

# Test memory system
python3.11 test_mem0_direct.py

# Test LangSmith tracing
python3.11 test_langsmith.py
```

### Security Tests
```bash
# Verify no secrets in repository
git log --all -S "your_actual_secret_here" --source --all

# Test secret retrieval from Secret Manager
gcloud secrets versions access latest --secret="cdp-api-key-name" --project=athena-agent-prod

# Verify cost protection
python3.11 test_final_cost_system.py
```

## 🚢 Deployment

### Local Testing with Mainnet

```bash
# Test mainnet connection with cost protection
python3.11 test_mainnet.py

# Test complete system with cost management
python3.11 test_final_cost_system.py
```

### Production Deployment to Google Cloud Run

**Prerequisites:**
- Google Cloud project `athena-agent-prod` created ✅
- Secret Manager with all secrets configured ✅
- Billing enabled and $30 cost protection active ✅

```bash
# 1. Build and push Docker image
docker build -t gcr.io/athena-agent-prod/athena-agent:latest .
docker push gcr.io/athena-agent-prod/athena-agent:latest

# 2. Deploy to Cloud Run with Secret Manager integration
gcloud run deploy athena-agent \
  --image gcr.io/athena-agent-prod/athena-agent:latest \
  --region us-central1 \
  --memory 4Gi \
  --cpu 2 \
  --min-instances 1 \
  --max-instances 3 \
  --set-env-vars GCP_PROJECT_ID=athena-agent-prod \
  --set-env-vars GOOGLE_VERTEX_PROJECT=athena-agent-prod \
  --set-env-vars STARTING_TREASURY=100.0 \
  --project athena-agent-prod

# 3. Monitor deployment
gcloud run services describe athena-agent --region us-central1 --project athena-agent-prod

# 4. Monitor logs and costs
gcloud logging read "resource.labels.service_name=athena-agent" --limit=50 --project athena-agent-prod
```

### Security & Cost Protection Features

✅ **Production Ready:**
- All secrets in Google Cloud Secret Manager
- Zero secret exposure in code or containers
- $30 hard spending limit with automatic shutdown
- Real-time cost monitoring and alerts
- Emergency mode activation at $20
- Daily cost reset and tracking

✅ **Monitoring:**
- LangSmith traces for all LLM calls
- Cost breakdown by service (Gemini, Mem0, Google Cloud)
- Secret Manager audit logs
- Cloud Run metrics and logs

## 📖 Documentation

### Core Documentation
- [CLAUDE.md](CLAUDE.md) - Comprehensive implementation guide
- [SECURITY_IMPLEMENTATION.md](SECURITY_IMPLEMENTATION.md) - Security and Secret Manager setup
- [COST_MANAGEMENT_SUMMARY.md](COST_MANAGEMENT_SUMMARY.md) - Cost protection overview

### Development Documentation
- [.env.example](.env.example) - Configuration template
- [scripts/migrate_secrets.py](scripts/migrate_secrets.py) - Secret migration tool
- [src/config/secret_manager.py](src/config/secret_manager.py) - Secret Manager integration
- [src/monitoring/cost_manager.py](src/monitoring/cost_manager.py) - Cost protection system

### Testing Documentation
- Run `python3.11 test_final_cost_system.py` for complete system test
- See test files for individual component testing
- Security validation with Secret Manager integration

## 🤝 Contributing

### Security Requirements
⚠️ **NEVER commit secrets or API keys!**

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Use `.env.example` as template, never commit real `.env` files
4. Test with cost protection: `python3.11 test_final_cost_system.py`
5. Verify no secrets: `git log --all -S "potential_secret" --source --all`
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Development Guidelines
- All secrets must use Google Cloud Secret Manager in production
- Cost protection must be tested for any LLM integration
- Test files with hardcoded secrets should be in `.gitignore`
- Use `python3.11` (required for CDP SDK)
- Follow the existing architecture patterns

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- LangChain team for LangGraph cognitive architecture
- Coinbase for CDP AgentKit blockchain integration
- Mem0 for the cloud memory system
- Google Cloud for Secret Manager and Vertex AI
- Aerodrome Finance for the DeFi protocol
- LangSmith for tracing and monitoring

## 🛡️ Security & Financial Protection

**✅ Enterprise-Grade Security:**
- Zero secret exposure with Google Cloud Secret Manager
- All credentials encrypted and centrally managed
- Audit logs for all secret access
- No hardcoded keys in codebase

**✅ Financial Protection:**
- Guaranteed $30 spending limit
- Real-time cost monitoring
- Automatic emergency shutdown
- Progressive alerts and budget controls

---

**🤖 Built with ❤️ and enterprise-grade security for the future of autonomous DeFi**

*"An AI agent that's smart enough to trade, secure enough to trust, and wise enough to protect your budget."*