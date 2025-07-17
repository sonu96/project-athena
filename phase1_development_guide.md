# Phase 1 Development Guide: DeFi Agent Memory Foundation

## Executive Summary

This document provides a complete implementation guide for Phase 1 of the Personal DeFi AI Agent project. Phase 1 focuses on building the memory foundation, market observation capabilities, and agent survival instincts using GCP, Mem0, and CDP AgentKit on the BASE network.

**Key Objectives:**
- Create an AI agent with economic survival pressure
- Implement a unified LangGraph nervous system for consciousness
- Build memory-driven decision making with emotional intelligence
- Develop market observation and pattern recognition
- Establish cost tracking and treasury management
- Create a cognitive loop: Sense → Think → Feel → Decide → Learn
- Prepare foundation for future trading capabilities

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        GCP PROJECT                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │ Cloud       │  │ Firestore   │  │ BigQuery    │  │ Secret  │ │
│  │ Functions   │  │ (Real-time) │  │ (Analytics) │  │ Manager │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │ Cloud       │  │ Scheduler   │  │ Monitoring  │  │ Logging │ │
│  │ Storage     │  │ (Cron Jobs) │  │ & Alerting  │  │         │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  LANGGRAPH NERVOUS SYSTEM                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Cognitive Loop (Consciousness)              │   │
│  │  ┌─────┐→┌─────┐→┌─────┐→┌─────┐→┌─────┐              │   │
│  │  │Sense│ │Think│ │Feel │ │Decide│ │Learn│──┐           │   │
│  │  └─────┘ └─────┘ └─────┘ └─────┘ └─────┘  │           │   │
│  │     ▲                                        │           │   │
│  │     └────────────────────────────────────────┘           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │   Mem0      │  │ Treasury    │  │ CDP         │  │ Market  │ │
│  │ (Memory)    │  │ Manager     │  │ AgentKit    │  │ Data    │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

**Technology Stack:**
- **Backend**: Python 3.9+, FastAPI
- **Nervous System**: LangGraph (Unified cognitive loop)
- **Memory**: Mem0 (AI Memory System)
- **Database**: Google Firestore (operational), BigQuery (analytics)
- **Blockchain**: CDP AgentKit (BASE network)
- **Infrastructure**: Google Cloud Platform
- **AI**: Claude Sonnet 4, GPT-4 (configurable)
- **Monitoring**: LangSmith (Workflow tracing)

---

## 1. Project Setup & Infrastructure

### 1.1 GCP Project Initialization

```bash
# Create GCP Project
gcloud projects create defi-agent-project-001 --name="DeFi Agent"
gcloud config set project defi-agent-project-001

# Enable Required APIs
gcloud services enable firestore.googleapis.com
gcloud services enable bigquery.googleapis.com
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable monitoring.googleapis.com
gcloud services enable logging.googleapis.com

# Set up billing alerts
gcloud billing budgets create --billing-account=BILLING_ACCOUNT_ID \
  --display-name="DeFi Agent Budget" \
  --budget-amount=300 \
  --threshold-rules=percent=50,percent=90,percent=100

# Create service account
gcloud iam service-accounts create defi-agent-sa \
    --description="DeFi Agent Service Account" \
    --display-name="DeFi Agent"

# Grant necessary permissions
gcloud projects add-iam-policy-binding defi-agent-project-001 \
    --member="serviceAccount:defi-agent-sa@defi-agent-project-001.iam.gserviceaccount.com" \
    --role="roles/datastore.user"

gcloud projects add-iam-policy-binding defi-agent-project-001 \
    --member="serviceAccount:defi-agent-sa@defi-agent-project-001.iam.gserviceaccount.com" \
    --role="roles/bigquery.dataEditor"
```

### 1.2 Project Structure

```
defi-agent/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── src/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   ├── gcp_config.py
│   │   └── langsmith_config.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   ├── treasury.py
│   │   ├── memory_manager.py
│   │   ├── market_detector.py
│   │   └── nervous_system.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── firestore_client.py
│   │   ├── bigquery_client.py
│   │   └── market_data_collector.py
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── mem0_integration.py
│   │   ├── cdp_integration.py
│   │   ├── llm_integration.py
│   │   └── llm_workflow_integration.py
│   ├── workflows/
│   │   ├── __init__.py
│   │   ├── consciousness.py
│   │   ├── cognitive_loop.py
│   │   ├── nodes.py
│   │   ├── emotional_router.py
│   │   ├── state.py
│   │   ├── market_analysis_flow.py
│   │   └── decision_flow.py
├── cloud_functions/
│   ├── market_data_collector/
│   ├── hourly_analysis/
│   └── daily_summary/
├── sql/
│   ├── bigquery_tables.sql
│   └── analytics_views.sql
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
└── deployment/
    ├── terraform/
    ├── cloud_functions/
    └── monitoring/
```

### 1.3 Environment Configuration

```bash
# .env.example
# GCP Configuration
GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account-key.json"
GCP_PROJECT_ID="defi-agent-project-001"
FIRESTORE_DATABASE="(default)"
BIGQUERY_DATASET="defi_agent"

# API Keys
ANTHROPIC_API_KEY="your_anthropic_api_key"
OPENAI_API_KEY="your_openai_api_key"
CDP_API_KEY_NAME="your_cdp_api_key_name"
CDP_API_KEY_SECRET="your_cdp_api_secret"

# Agent Configuration
AGENT_STARTING_TREASURY=100.0
AGENT_ID="defi_agent_001"
NETWORK="base-sepolia"  # Start with testnet

# Mem0 Configuration
MEM0_API_KEY="your_mem0_api_key"
VECTOR_DB_URL="your_vector_db_url"

# LangSmith Configuration (for nervous system tracing)
LANGSMITH_API_KEY="your_langsmith_api_key"
LANGSMITH_PROJECT="defi-agent-phase1"

# Market Data APIs
COINGECKO_API_KEY="your_coingecko_pro_key"  # Optional for higher limits
ETHERSCAN_API_KEY="your_etherscan_api_key"
```

---

## 2. Firestore Database Setup

### 2.1 Firestore Client Implementation

```python
# src/data/firestore_client.py
import os
from google.cloud import firestore
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

class FirestoreClient:
    def __init__(self):
        self.db = firestore.Client()
        self.collections = {
            'treasury': 'agent_data_treasury',
            'market_conditions': 'agent_data_market_conditions', 
            'protocols': 'agent_data_protocols',
            'decisions': 'agent_data_decisions',
            'costs': 'agent_data_costs',
            'system_logs': 'agent_data_system_logs'
        }
    
    async def initialize_database(self):
        """Initialize database with default documents"""
        
        # Initialize treasury with starting balance
        treasury_doc = {
            'balance_usd': 100.0,  # Starting seed money
            'daily_burn_rate': 0.0,
            'days_until_bankruptcy': 999,
            'emotional_state': 'stable',
            'risk_tolerance': 0.5,
            'confidence_level': 0.5,
            'created_at': firestore.SERVER_TIMESTAMP,
            'last_updated': firestore.SERVER_TIMESTAMP,
            'initialization': True
        }
        
        await self.db.collection(self.collections['treasury']).document('current_state').set(treasury_doc)
        
        # Initialize market conditions
        market_doc = {
            'condition_type': 'unknown',
            'confidence_score': 0.0,
            'last_updated': firestore.SERVER_TIMESTAMP,
            'initialization': True
        }
        
        await self.db.collection(self.collections['market_conditions']).document('current').set(market_doc)
        
        print("✅ Firestore database initialized successfully")

    async def update_treasury(self, treasury_data: Dict[str, Any]) -> bool:
        """Update treasury state"""
        try:
            treasury_data['last_updated'] = firestore.SERVER_TIMESTAMP
            
            # Update current state
            await self.db.collection(self.collections['treasury']).document('current_state').update(treasury_data)
            
            # Create daily snapshot if needed
            today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            snapshot_data = {
                **treasury_data,
                'snapshot_date': today,
                'snapshot_timestamp': firestore.SERVER_TIMESTAMP
            }
            
            await self.db.collection(self.collections['treasury']).document('daily_snapshots').collection('snapshots').document(today).set(snapshot_data, merge=True)
            
            return True
        except Exception as e:
            print(f"❌ Error updating treasury: {e}")
            return False

    async def get_current_treasury(self) -> Optional[Dict[str, Any]]:
        """Get current treasury state"""
        try:
            doc = await self.db.collection(self.collections['treasury']).document('current_state').get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f"❌ Error getting treasury: {e}")
            return None

    async def update_market_condition(self, condition_data: Dict[str, Any]) -> bool:
        """Update market conditions"""
        try:
            condition_data['last_updated'] = firestore.SERVER_TIMESTAMP
            
            # Update current condition
            await self.db.collection(self.collections['market_conditions']).document('current').set(condition_data, merge=True)
            
            # Store hourly snapshot
            hour_key = datetime.now(timezone.utc).strftime('%Y-%m-%d-%H')
            await self.db.collection(self.collections['market_conditions']).document('hourly_snapshots').collection('snapshots').document(hour_key).set(condition_data, merge=True)
            
            return True
        except Exception as e:
            print(f"❌ Error updating market condition: {e}")
            return False

    async def store_protocol_data(self, protocol: str, protocol_data: Dict[str, Any]) -> bool:
        """Store protocol yield data"""
        try:
            protocol_data['last_updated'] = firestore.SERVER_TIMESTAMP
            await self.db.collection(self.collections['protocols']).document(protocol).set(protocol_data, merge=True)
            return True
        except Exception as e:
            print(f"❌ Error storing protocol data: {e}")
            return False

    async def log_cost_event(self, cost_data: Dict[str, Any]) -> bool:
        """Log individual cost events"""
        try:
            cost_data['timestamp'] = firestore.SERVER_TIMESTAMP
            await self.db.collection(self.collections['costs']).document('realtime_tracking').collection('events').add(cost_data)
            
            # Update daily totals
            today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            daily_ref = self.db.collection(self.collections['costs']).document('daily_costs').collection('days').document(today)
            
            # This would need transaction for accurate counting
            await daily_ref.set({
                'date': today,
                'last_cost_event': cost_data,
                'last_updated': firestore.SERVER_TIMESTAMP
            }, merge=True)
            
            return True
        except Exception as e:
            print(f"❌ Error logging cost: {e}")
            return False
```

### 2.2 Firestore Security Rules

```javascript
// firestore.rules
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Agent data - restrict to service account only
    match /agent_data_{type}/{document=**} {
      allow read, write: if request.auth != null && 
        request.auth.token.email == "defi-agent-sa@defi-agent-project-001.iam.gserviceaccount.com";
    }
    
    // Public read for monitoring dashboard (optional)
    match /agent_data_treasury/current_state {
      allow read: if true; // For public dashboard
      allow write: if request.auth != null;
    }
    
    // Deny all other access
    match /{document=**} {
      allow read, write: if false;
    }
  }
}
```

### 2.3 Firestore Document Schemas

#### Treasury State Document
```javascript
// Collection: agent_data_treasury/current_state
{
  "balance_usd": 156.50,
  "daily_burn_rate": 7.60,
  "days_until_bankruptcy": 20,
  "emotional_state": "cautious",
  "risk_tolerance": 0.35,
  "confidence_level": 0.67,
  "last_updated": "2024-07-15T10:30:00Z",
  "update_frequency": "hourly",
  "treasury_history": {
    "24h_change": -7.60,
    "7d_change": -53.20,
    "highest_balance": 210.30,
    "lowest_balance": 23.50
  },
  "survival_metrics": {
    "critical_threshold": 25.0,
    "warning_threshold": 50.0,
    "comfortable_threshold": 100.0,
    "current_zone": "warning"
  }
}
```

#### Market Conditions Document
```javascript
// Collection: agent_data_market_conditions/current
{
  "condition_type": "volatile", 
  "confidence_score": 0.87,
  "timestamp": "2024-07-15T10:30:00Z",
  "price_data": {
    "btc_price": 45250.50,
    "eth_price": 2890.75,
    "btc_24h_change": -8.5,
    "eth_24h_change": -6.2
  },
  "volatility_metrics": {
    "btc_volatility": 0.085,
    "eth_volatility": 0.062,
    "overall_volatility": 0.074,
    "volatility_trend": "increasing"
  },
  "market_indicators": {
    "fear_greed_index": 32,
    "defi_tvl_usd": 87500000000,
    "gas_price_gwei": 45,
    "network_congestion": "moderate"
  },
  "detection_details": {
    "algorithm": "multi_factor_analysis_v1",
    "primary_factors": ["price_volatility", "volume_spike"],
    "supporting_factors": ["fear_greed_low", "high_gas_fees"],
    "confidence_breakdown": {
      "price_signals": 0.92,
      "volume_signals": 0.85,
      "sentiment_signals": 0.84
    }
  },
  "agent_implications": {
    "recommended_risk_tolerance": 0.25,
    "suggested_actions": ["reduce_exposure", "wait_for_stability"],
    "avoid_actions": ["high_risk_strategies", "large_positions"]
  }
}
```

---

## 3. BigQuery Analytics Setup

### 3.1 BigQuery Tables Creation

```sql
-- sql/bigquery_tables.sql

-- Historical market data for analytics
CREATE TABLE `defi_agent.market_history` (
  timestamp TIMESTAMP,
  btc_price FLOAT64,
  eth_price FLOAT64,
  btc_24h_change FLOAT64,
  eth_24h_change FLOAT64,
  volatility_score FLOAT64,
  market_condition STRING,
  confidence_score FLOAT64,
  fear_greed_index INT64,
  defi_tvl_usd INT64,
  gas_price_gwei INT64,
  detection_algorithm STRING,
  firestore_doc_id STRING
)
PARTITION BY DATE(timestamp)
CLUSTER BY market_condition, DATE(timestamp);

-- Protocol yield opportunities
CREATE TABLE `defi_agent.yield_opportunities` (
  timestamp TIMESTAMP,
  protocol STRING,
  asset STRING,
  supply_apy FLOAT64,
  borrow_apy FLOAT64,
  utilization_rate FLOAT64,
  tvl_usd INT64,
  market_condition STRING,
  agent_interest_score FLOAT64,
  agent_action STRING,
  risk_score FLOAT64,
  opportunity_rank INT64,
  firestore_doc_id STRING
)
PARTITION BY DATE(timestamp)
CLUSTER BY protocol, asset;

-- Agent treasury history
CREATE TABLE `defi_agent.treasury_history` (
  timestamp TIMESTAMP,
  balance_usd FLOAT64,
  daily_burn_rate FLOAT64,
  days_until_bankruptcy INT64,
  emotional_state STRING,
  risk_tolerance FLOAT64,
  confidence_level FLOAT64,
  treasury_change_24h FLOAT64,
  balance_trend STRING
)
PARTITION BY DATE(timestamp)
CLUSTER BY emotional_state, DATE(timestamp);

-- Cost tracking and analysis
CREATE TABLE `defi_agent.cost_analytics` (
  date DATE,
  llm_costs FLOAT64,
  gcp_costs FLOAT64,
  api_costs FLOAT64,
  blockchain_costs FLOAT64,
  total_daily_burn FLOAT64,
  cost_per_decision FLOAT64,
  cost_efficiency FLOAT64,
  budget_remaining FLOAT64,
  cost_alerts ARRAY<STRING>
)
PARTITION BY date;

-- Agent decisions for analysis
CREATE TABLE `defi_agent.decision_history` (
  timestamp TIMESTAMP,
  decision_id STRING,
  decision_type STRING,
  treasury_level FLOAT64,
  market_condition STRING,
  confidence_score FLOAT64,
  reasoning STRING,
  action_taken STRING,
  outcome STRING,
  success BOOLEAN,
  lessons_learned STRING,
  mem0_memory_id STRING
)
PARTITION BY DATE(timestamp)
CLUSTER BY decision_type, success;
```

### 3.2 BigQuery Client Implementation

```python
# src/data/bigquery_client.py
from google.cloud import bigquery
from datetime import datetime, timezone
import json
from typing import Dict, List, Any

class BigQueryClient:
    def __init__(self):
        self.client = bigquery.Client()
        self.dataset_id = 'defi_agent'
        self.tables = {
            'market_history': f'{self.dataset_id}.market_history',
            'yield_opportunities': f'{self.dataset_id}.yield_opportunities',
            'treasury_history': f'{self.dataset_id}.treasury_history',
            'cost_analytics': f'{self.dataset_id}.cost_analytics',
            'decision_history': f'{self.dataset_id}.decision_history'
        }
    
    async def initialize_dataset(self):
        """Create dataset and tables"""
        try:
            # Create dataset
            dataset = bigquery.Dataset(f"{self.client.project}.{self.dataset_id}")
            dataset.location = "US"  # or your preferred location
            dataset = self.client.create_dataset(dataset, exists_ok=True)
            
            # Execute table creation SQL
            with open('sql/bigquery_tables.sql', 'r') as f:
                sql_commands = f.read().split(';')
                for sql in sql_commands:
                    if sql.strip():
                        self.client.query(sql).result()
            
            print("✅ BigQuery dataset and tables initialized")
            return True
        except Exception as e:
            print(f"❌ Error initializing BigQuery: {e}")
            return False

    async def insert_market_data(self, market_data: Dict[str, Any]) -> bool:
        """Insert market data for analysis"""
        try:
            table = self.client.get_table(self.tables['market_history'])
            
            row = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'btc_price': market_data.get('btc_price', 0),
                'eth_price': market_data.get('eth_price', 0),
                'btc_24h_change': market_data.get('btc_24h_change', 0),
                'eth_24h_change': market_data.get('eth_24h_change', 0),
                'volatility_score': market_data.get('volatility_score', 0),
                'market_condition': market_data.get('condition_type', 'unknown'),
                'confidence_score': market_data.get('confidence_score', 0),
                'fear_greed_index': market_data.get('fear_greed_index', 50),
                'defi_tvl_usd': market_data.get('defi_tvl_usd', 0),
                'gas_price_gwei': market_data.get('gas_price_gwei', 20),
                'detection_algorithm': market_data.get('detection_algorithm', 'v1'),
                'firestore_doc_id': market_data.get('firestore_doc_id', '')
            }
            
            errors = self.client.insert_rows_json(table, [row])
            if errors:
                print(f"❌ BigQuery insert errors: {errors}")
                return False
            
            return True
        except Exception as e:
            print(f"❌ Error inserting market data: {e}")
            return False

    async def get_market_patterns(self, days: int = 30) -> List[Dict]:
        """Get market patterns for agent learning"""
        query = f"""
        SELECT 
            market_condition,
            AVG(confidence_score) as avg_confidence,
            COUNT(*) as occurrences,
            AVG(volatility_score) as avg_volatility,
            AVG(btc_24h_change) as avg_btc_change
        FROM `{self.tables['market_history']}`
        WHERE DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
        GROUP BY market_condition
        ORDER BY occurrences DESC
        """
        
        try:
            results = self.client.query(query).result()
            return [dict(row) for row in results]
        except Exception as e:
            print(f"❌ Error getting market patterns: {e}")
            return []
```

---

## 4. Mem0 Integration

### 4.1 Mem0 Setup & Configuration

```python
# src/integrations/mem0_integration.py
import os
from mem0 import Memory
from typing import Dict, List, Any, Optional
import json
from datetime import datetime, timezone

class Mem0Integration:
    def __init__(self):
        # Initialize Mem0 with configuration
        config = {
            "llm": {
                "provider": "anthropic",
                "config": {
                    "model": "claude-3-sonnet-20240229",
                    "api_key": os.getenv("ANTHROPIC_API_KEY")
                }
            },
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "host": "localhost",
                    "port": 6333
                }
            },
            "embedder": {
                "provider": "openai",
                "config": {
                    "api_key": os.getenv("OPENAI_API_KEY")
                }
            }
        }
        
        self.memory = Memory.from_config(config)
        self.agent_id = "defi_agent_001"
        
        # Memory categories for organization
        self.categories = {
            'survival': 'survival_critical',
            'protocol': 'protocol_behavior', 
            'strategy': 'strategy_performance',
            'market': 'market_patterns',
            'decision': 'decision_outcomes'
        }
    
    async def initialize_memory_system(self):
        """Initialize memory system with basic agent knowledge"""
        
        # Core survival knowledge
        survival_memories = [
            {
                "content": "When treasury drops below $30, immediately activate emergency mode: reduce all non-essential costs, switch to conservative strategies, and focus on capital preservation.",
                "metadata": {
                    "category": "survival_critical",
                    "importance": 1.0,
                    "context": "treasury_emergency"
                }
            },
            {
                "content": "High APY yields above 15% are historically dangerous - 88% failure rate with average 94% loss. Avoid unless exceptional circumstances with established protocols.",
                "metadata": {
                    "category": "risk_management",
                    "importance": 0.9,
                    "context": "yield_selection"
                }
            },
            {
                "content": "During market crashes (>20% decline), established protocols like Aave and Compound tend to maintain stability better than newer protocols.",
                "metadata": {
                    "category": "protocol_reliability",
                    "importance": 0.8,
                    "context": "market_stress"
                }
            }
        ]
        
        # Store initial memories
        for memory_data in survival_memories:
            await self.add_memory(
                content=memory_data["content"],
                metadata=memory_data["metadata"]
            )
        
        print("✅ Mem0 memory system initialized with survival knowledge")

    async def add_memory(self, content: str, metadata: Dict[str, Any]) -> str:
        """Add new memory to the system"""
        try:
            # Add timestamp and agent context
            metadata.update({
                "agent_id": self.agent_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "created_by": "agent_experience"
            })
            
            # Add memory to Mem0
            memory_id = self.memory.add(
                messages=[{"role": "user", "content": content}],
                user_id=self.agent_id,
                metadata=metadata
            )
            
            print(f"✅ Memory added: {memory_id}")
            return memory_id
        except Exception as e:
            print(f"❌ Error adding memory: {e}")
            return ""

    async def query_memories(self, query: str, category: Optional[str] = None, limit: int = 5) -> List[Dict]:
        """Query relevant memories for decision making"""
        try:
            # Prepare filters
            filters = {"agent_id": self.agent_id}
            if category:
                filters["category"] = category
            
            # Search memories
            memories = self.memory.search(
                query=query,
                user_id=self.agent_id,
                limit=limit,
                filters=filters
            )
            
            return [
                {
                    "id": memory.get("id", ""),
                    "content": memory.get("memory", ""),
                    "metadata": memory.get("metadata", {}),
                    "score": memory.get("score", 0.0)
                }
                for memory in memories
            ]
        except Exception as e:
            print(f"❌ Error querying memories: {e}")
            return []

    async def update_memory_from_experience(self, experience: Dict[str, Any]) -> bool:
        """Update memory based on agent experience"""
        try:
            # Determine memory content based on experience type
            if experience["type"] == "survival_event":
                content = f"Treasury survival event: {experience['description']}. Outcome: {experience['outcome']}. Key lesson: {experience['lesson']}"
                metadata = {
                    "category": "survival_critical",
                    "importance": 1.0,
                    "treasury_level": experience.get("treasury_level", 0),
                    "success": experience.get("success", False)
                }
                
            elif experience["type"] == "protocol_interaction":
                content = f"Protocol {experience['protocol']} interaction: {experience['description']}. Result: {experience['result']}"
                metadata = {
                    "category": "protocol_behavior",
                    "importance": 0.7,
                    "protocol": experience["protocol"],
                    "success": experience.get("success", False)
                }
                
            elif experience["type"] == "market_response":
                content = f"Market condition {experience['condition']} response: {experience['action']}. Outcome: {experience['outcome']}"
                metadata = {
                    "category": "market_patterns",
                    "importance": 0.6,
                    "market_condition": experience["condition"],
                    "success": experience.get("success", False)
                }
            
            else:
                # Generic experience
                content = f"{experience['type']}: {experience['description']}"
                metadata = {
                    "category": "general_experience",
                    "importance": 0.5
                }
            
            # Add the memory
            memory_id = await self.add_memory(content, metadata)
            return bool(memory_id)
            
        except Exception as e:
            print(f"❌ Error updating memory from experience: {e}")
            return False

    async def get_relevant_context(self, situation: Dict[str, Any]) -> Dict[str, Any]:
        """Get relevant memory context for current situation"""
        try:
            context = {
                "survival_memories": [],
                "protocol_memories": [],
                "market_memories": [],
                "decision_memories": []
            }
            
            # Query different types of memories based on situation
            if situation.get("treasury_level", 100) < 50:
                survival_memories = await self.query_memories(
                    query=f"treasury emergency survival low balance {situation.get('treasury_level', 0)}",
                    category="survival_critical",
                    limit=3
                )
                context["survival_memories"] = survival_memories
            
            if situation.get("market_condition"):
                market_memories = await self.query_memories(
                    query=f"market condition {situation['market_condition']} response strategy",
                    category="market_patterns",
                    limit=3
                )
                context["market_memories"] = market_memories
            
            if situation.get("protocol"):
                protocol_memories = await self.query_memories(
                    query=f"protocol {situation['protocol']} reliability performance",
                    category="protocol_behavior",
                    limit=3
                )
                context["protocol_memories"] = protocol_memories
            
            return context
            
        except Exception as e:
            print(f"❌ Error getting relevant context: {e}")
            return {}
```

### 4.2 Memory Categories & Schemas

#### Survival Memory Schema
```python
survival_memories = {
    "treasury_crisis_25_dollars": {
        "memory_id": "survival_001",
        "memory_type": "survival_critical",
        "treasury_level": 25.0,
        "market_condition": "volatile",
        "emotional_state": "desperate",
        "actions_taken": [
            "emergency_conservative_mode",
            "reduced_llm_calls",
            "paused_risky_strategies"
        ],
        "outcome": "survived_4_days_recovered_to_45",
        "success_factors": [
            "immediate_risk_reduction",
            "cost_cutting_effective",
            "conservative_yields_stable"
        ],
        "lessons_learned": "When treasury drops below $30, immediately switch to survival mode. Conservative yields are lifeline.",
        "confidence": 0.95,
        "times_recalled": 12,
        "memory_weight": 1.0,
        "firestore_references": [
            "agent_data/treasury/daily_snapshots/2024-07-10",
            "agent_data/decisions/2024-07-10/emergency_mode_activation"
        ],
        "last_accessed": "2024-07-15T10:30:00Z",
        "access_context": "treasury_approaching_warning_level"
    }
}
```

#### Protocol Memory Schema
```python
protocol_memories = {
    "aave_reliability_crisis": {
        "memory_id": "protocol_001", 
        "memory_type": "protocol_behavior",
        "protocol": "aave",
        "market_condition": "btc_down_20_percent_march_2024",
        "protocol_response": {
            "yield_stability": "remained_stable_minor_decrease",
            "liquidity_availability": "no_issues_fast_withdrawals",
            "technical_performance": "no_downtime_or_issues"
        },
        "agent_decision": "increased_allocation_from_30_to_50_percent",
        "outcome": "positive_earned_extra_fees_during_crisis",
        "confidence": 0.87,
        "supporting_evidence": [
            "successful_emergency_withdrawal",
            "yield_only_dropped_5_percent",
            "no_technical_issues"
        ],
        "firestore_data": {
            "crisis_period": "2024-03-15_to_2024-03-20",
            "detailed_logs": "agent_data/protocols/aave/crisis_performance_march_2024"
        },
        "lessons_learned": "Aave is reliable during market stress. Can increase allocation during crisis.",
        "memory_strength": 0.91
    }
}
```

---

## 5. CDP AgentKit Integration

### 5.1 CDP Setup for BASE Network

```python
# src/integrations/cdp_integration.py
import os
from cdp import Cdp, Wallet, Asset
from typing import Dict, Optional, List
import asyncio

class CDPIntegration:
    def __init__(self):
        # Initialize CDP with BASE network
        self.cdp = Cdp.configure(
            api_key_name=os.getenv("CDP_API_KEY_NAME"),
            api_key_secret=os.getenv("CDP_API_KEY_SECRET"),
            network_id="base-sepolia"  # Start with testnet
        )
        
        self.wallet = None
        self.network = "base-sepolia"
        self.supported_assets = ["USDC", "DAI", "WETH"]
        
    async def initialize_wallet(self) -> bool:
        """Initialize or import wallet"""
        try:
            # Try to import existing wallet first
            wallet_file = "wallet_data.json"
            if os.path.exists(wallet_file):
                self.wallet = Wallet.import_data(wallet_file)
                print(f"✅ Imported existing wallet: {self.wallet.default_address}")
            else:
                # Create new wallet
                self.wallet = Wallet.create(network_id=self.network)
                # Save wallet data securely
                self.wallet.export_data(wallet_file)
                print(f"✅ Created new wallet: {self.wallet.default_address}")
            
            return True
        except Exception as e:
            print(f"❌ Error initializing wallet: {e}")
            return False

    async def get_wallet_balance(self) -> Dict[str, float]:
        """Get current wallet balances"""
        try:
            if not self.wallet:
                await self.initialize_wallet()
            
            balances = {}
            
            # Get ETH balance
            eth_balance = self.wallet.balance("ETH")
            balances["ETH"] = float(eth_balance.amount)
            
            # Get token balances
            for asset in self.supported_assets:
                try:
                    token_balance = self.wallet.balance(asset)
                    balances[asset] = float(token_balance.amount)
                except:
                    balances[asset] = 0.0
            
            return balances
        except Exception as e:
            print(f"❌ Error getting wallet balance: {e}")
            return {}

    async def get_testnet_tokens(self) -> bool:
        """Request testnet tokens from faucet"""
        try:
            if not self.wallet:
                await self.initialize_wallet()
            
            # Request testnet ETH
            faucet_tx = self.wallet.faucet()
            print(f"✅ Requested testnet ETH: {faucet_tx.transaction_hash}")
            
            # Wait for transaction
            await asyncio.sleep(30)  # Wait for transaction to confirm
            
            return True
        except Exception as e:
            print(f"❌ Error requesting testnet tokens: {e}")
            return False

    async def simulate_yield_deposit(self, protocol: str, asset: str, amount: float) -> Dict[str, Any]:
        """Simulate yield farming deposit (testnet only in Phase 1)"""
        try:
            if not self.wallet:
                await self.initialize_wallet()
            
            # This is simulation for Phase 1 - no actual deposits yet
            simulation_result = {
                "protocol": protocol,
                "asset": asset,
                "amount": amount,
                "estimated_gas": 150000,
                "estimated_gas_cost_eth": 0.003,
                "estimated_gas_cost_usd": 8.50,
                "simulation_success": True,
                "estimated_confirmation_time": 15,
                "warnings": []
            }
            
            # Add warnings based on conditions
            current_balances = await self.get_wallet_balance()
            if current_balances.get(asset, 0) < amount:
                simulation_result["warnings"].append(f"Insufficient {asset} balance")
                simulation_result["simulation_success"] = False
            
            if current_balances.get("ETH", 0) < 0.01:
                simulation_result["warnings"].append("Low ETH balance for gas fees")
            
            print(f"✅ Simulated {protocol} deposit: {amount} {asset}")
            return simulation_result
            
        except Exception as e:
            print(f"❌ Error simulating deposit: {e}")
            return {"simulation_success": False, "error": str(e)}

    async def get_transaction_history(self, limit: int = 10) -> List[Dict]:
        """Get recent transaction history"""
        try:
            if not self.wallet:
                await self.initialize_wallet()
            
            # Get transaction history
            transactions = self.wallet.list_transactions(limit=limit)
            
            history = []
            for tx in transactions:
                history.append({
                    "hash": tx.transaction_hash,
                    "status": tx.status,
                    "block_height": tx.block_height,
                    "from_address": tx.from_address,
                    "to_address": tx.to_address,
                    "timestamp": tx.timestamp
                })
            
            return history
        except Exception as e:
            print(f"❌ Error getting transaction history: {e}")
            return []
```

---

## 6. LangGraph Nervous System Architecture

Phase 1 now includes a simplified LangGraph-based nervous system that serves as the agent's central consciousness, allowing all decisions to flow through a unified cognitive loop.

### 6.1 Core Concept: Unified Consciousness

Instead of disparate components making isolated decisions, the LangGraph nervous system creates a unified flow where:
- Every perception leads to thought
- Every thought influences emotion
- Every emotion affects decisions
- Every decision creates learning
- Every learning updates perception

**Architecture Evolution:**
```
Before (Modular):                  After (Nervous System):
┌─────────┐  ┌─────────┐          ┌────────────────────────┐
│ Agent   │→ │Workflow │          │  Consciousness Loop    │
└─────────┘  └─────────┘          │  ┌─────┐              │
┌─────────┐  ┌─────────┐          │  │Sense│──┐           │
│Treasury │  │ Memory  │          │  └─────┘  ▼           │
└─────────┘  └─────────┘          │  ┌─────┐  ┌─────┐    │
┌─────────┐  ┌─────────┐          │  │Learn│  │Think│    │
│ Market  │  │  CDP    │          │  └─────┘  └─────┘    │
└─────────┘  └─────────┘          │      ▲        ▼       │
                                  │  ┌─────┐  ┌─────┐    │
                                  │  │Decide│ │Feel │    │
                                  │  └─────┘  └─────┘    │
                                  │      ▲        │       │
                                  │      └────────┘       │
                                  └────────────────────────┘
```

### 6.2 Consciousness State

The agent's entire mental state flows through the graph as a single, unified consciousness:

```python
# src/workflows/consciousness.py
from typing import TypedDict, List, Dict, Any
from datetime import datetime

class ConsciousnessState(TypedDict):
    """The complete state representing Athena's consciousness"""
    
    # Core Identity
    agent_id: str
    emotional_state: str  # 'desperate', 'cautious', 'stable', 'confident'
    
    # Current Perception
    market_data: Dict[str, Any]
    treasury_balance: float
    days_until_bankruptcy: int
    
    # Active Context
    current_goal: str
    recent_memories: List[Dict]
    active_patterns: List[str]
    
    # Decision Context
    available_actions: List[str]
    last_decision: Dict[str, Any]
    decision_confidence: float
    
    # Learning Buffer
    current_experience: Dict[str, Any]
    lessons_learned: List[str]
    
    # Operational State
    cycle_count: int
    total_cost: float
    timestamp: datetime
```

### 6.3 The Five-Node Cognitive Loop

The nervous system consists of five interconnected nodes that process consciousness in a continuous loop:

```python
# src/workflows/cognitive_loop.py
from langgraph.graph import StateGraph, START, END
from langsmith import traceable
from .consciousness import ConsciousnessState
from .nodes import SenseNode, ThinkNode, FeelNode, DecideNode, LearnNode

def create_cognitive_loop() -> StateGraph:
    """Create the main cognitive loop that serves as Athena's nervous system"""
    
    # Initialize the graph with consciousness state
    workflow = StateGraph(ConsciousnessState)
    
    # Initialize nodes (each wraps existing components)
    sense_node = SenseNode()    # Wraps market_data_collector
    think_node = ThinkNode()     # Wraps market_analysis_flow
    feel_node = FeelNode()       # Updates emotional state based on treasury
    decide_node = DecideNode()   # Wraps decision_flow
    learn_node = LearnNode()     # Wraps memory_manager
    
    # Add nodes to graph
    workflow.add_node("sense", sense_node.execute)
    workflow.add_node("think", think_node.execute)
    workflow.add_node("feel", feel_node.execute)
    workflow.add_node("decide", decide_node.execute)
    workflow.add_node("learn", learn_node.execute)
    
    # Define the flow
    workflow.add_edge(START, "sense")
    workflow.add_edge("sense", "think")
    workflow.add_edge("think", "feel")
    workflow.add_edge("feel", "decide")
    workflow.add_edge("decide", "learn")
    workflow.add_edge("learn", "sense")  # Continuous loop
    
    return workflow.compile()
```

### 6.4 Node Implementations

Each node wraps existing functionality into the unified consciousness flow:

```python
# src/workflows/nodes.py
from langsmith import traceable
from typing import Dict, Any
from .consciousness import ConsciousnessState

class SenseNode:
    """Perceive the environment - wrapper for market data collection"""
    
    def __init__(self):
        from ..data.market_data_collector import MarketDataCollector
        from ..integrations.cdp_integration import CDPIntegration
        self.market_collector = MarketDataCollector()
        self.cdp = CDPIntegration()
    
    @traceable(name="sense_environment")
    async def execute(self, state: ConsciousnessState) -> ConsciousnessState:
        # Collect market data
        market_result = await self.market_collector.collect_comprehensive_market_data()
        state["market_data"] = market_result.get("data", {})
        
        # Check wallet balance
        wallet_balance = await self.cdp.get_wallet_balance()
        state["treasury_balance"] = wallet_balance.get("total_usd", state["treasury_balance"])
        
        # Update perception timestamp
        state["timestamp"] = datetime.now(timezone.utc)
        
        return state

class ThinkNode:
    """Analyze and understand - wrapper for market analysis"""
    
    def __init__(self):
        from ..workflows.market_analysis_flow import create_market_analysis_workflow
        self.analysis_workflow = create_market_analysis_workflow()
    
    @traceable(name="think_analysis")
    async def execute(self, state: ConsciousnessState) -> ConsciousnessState:
        # Run market analysis with current state
        analysis_input = {
            "market_data": state["market_data"],
            "treasury_balance": state["treasury_balance"],
            "emotional_state": state["emotional_state"],
            "risk_tolerance": 0.5 if state["emotional_state"] == "stable" else 0.2
        }
        
        analysis_result = await self.analysis_workflow.ainvoke(analysis_input)
        
        # Extract patterns and insights
        state["active_patterns"] = analysis_result.get("patterns_detected", [])
        state["current_goal"] = self._determine_goal(analysis_result, state)
        
        return state
    
    def _determine_goal(self, analysis: Dict, state: ConsciousnessState) -> str:
        if state["emotional_state"] == "desperate":
            return "survive_and_preserve"
        elif analysis.get("market_condition") == "volatile":
            return "monitor_carefully"
        else:
            return "observe_and_learn"

class FeelNode:
    """Update emotional state based on situation"""
    
    @traceable(name="feel_emotions")
    async def execute(self, state: ConsciousnessState) -> ConsciousnessState:
        balance = state["treasury_balance"]
        burn_rate = state["total_cost"] / max(state["cycle_count"], 1)
        
        # Calculate days until bankruptcy
        state["days_until_bankruptcy"] = int(balance / burn_rate) if burn_rate > 0 else 999
        
        # Update emotional state based on treasury
        if balance < 25 or state["days_until_bankruptcy"] < 5:
            state["emotional_state"] = "desperate"
        elif balance < 50 or state["days_until_bankruptcy"] < 10:
            state["emotional_state"] = "cautious"
        elif balance < 100:
            state["emotional_state"] = "stable"
        else:
            state["emotional_state"] = "confident"
        
        return state

class DecideNode:
    """Make decisions based on full context"""
    
    def __init__(self):
        from ..workflows.decision_flow import create_decision_workflow
        self.decision_workflow = create_decision_workflow()
    
    @traceable(name="decide_action")
    async def execute(self, state: ConsciousnessState) -> ConsciousnessState:
        # Determine available actions based on emotional state
        if state["emotional_state"] == "desperate":
            state["available_actions"] = ["emergency_mode", "minimize_costs", "preserve_capital"]
        elif state["emotional_state"] == "cautious":
            state["available_actions"] = ["reduce_frequency", "conservative_observation"]
        else:
            state["available_actions"] = ["normal_observation", "explore_patterns", "maintain_schedule"]
        
        # Make decision with full context
        decision_input = {
            "decision_type": "operational",
            "available_options": state["available_actions"],
            "treasury_balance": state["treasury_balance"],
            "emotional_state": state["emotional_state"],
            "market_condition": state["active_patterns"][0] if state["active_patterns"] else "neutral",
            "relevant_memories": state["recent_memories"][:5]
        }
        
        decision_result = await self.decision_workflow.ainvoke(decision_input)
        
        state["last_decision"] = decision_result
        state["decision_confidence"] = decision_result.get("confidence", 0.5)
        
        return state

class LearnNode:
    """Form memories and learn from experience"""
    
    def __init__(self):
        from ..core.memory_manager import MemoryManager
        self.memory_manager = MemoryManager()
    
    @traceable(name="learn_experience")
    async def execute(self, state: ConsciousnessState) -> ConsciousnessState:
        # Create experience from current cycle
        experience = {
            "type": "observation_cycle",
            "timestamp": state["timestamp"],
            "emotional_state": state["emotional_state"],
            "market_patterns": state["active_patterns"],
            "decision": state["last_decision"],
            "treasury_balance": state["treasury_balance"],
            "success": True  # Will be evaluated in future cycles
        }
        
        # Process experience into memory
        await self.memory_manager.process_experience(experience)
        
        # Get updated relevant memories for next cycle
        memory_context = {
            "emotional_state": state["emotional_state"],
            "current_goal": state["current_goal"],
            "patterns": state["active_patterns"]
        }
        
        memories = await self.memory_manager.get_relevant_memories(memory_context)
        state["recent_memories"] = memories.get("memories", [])[:10]
        
        # Extract lessons
        if state["cycle_count"] % 10 == 0:  # Consolidate every 10 cycles
            consolidation = await self.memory_manager.consolidate_learning()
            state["lessons_learned"] = consolidation.get("key_lessons", [])
        
        # Increment cycle count
        state["cycle_count"] += 1
        
        return state
```

### 6.5 Emotional Routing

The nervous system automatically adjusts behavior based on emotional state:

```python
# src/workflows/emotional_router.py
from typing import List
from .consciousness import ConsciousnessState

def emotional_router(state: ConsciousnessState) -> str:
    """Route execution based on emotional state"""
    
    emotional_state = state.get("emotional_state", "stable")
    
    if emotional_state == "desperate":
        # Minimal operations, maximum preservation
        return "survival_mode"
    elif emotional_state == "cautious":
        # Careful observation, reduced risk
        return "conservative_mode"
    elif emotional_state == "confident":
        # Active exploration, pattern seeking
        return "growth_mode"
    else:  # stable
        # Balanced operation
        return "normal_mode"

def get_operational_parameters(mode: str) -> Dict[str, Any]:
    """Get operational parameters based on mode"""
    
    parameters = {
        "survival_mode": {
            "observation_interval": 14400,  # 4 hours
            "max_daily_cost": 1.0,
            "llm_model": "claude-3-haiku",
            "memory_threshold": 0.9  # Only most important
        },
        "conservative_mode": {
            "observation_interval": 7200,   # 2 hours
            "max_daily_cost": 5.0,
            "llm_model": "claude-3-haiku",
            "memory_threshold": 0.7
        },
        "normal_mode": {
            "observation_interval": 3600,   # 1 hour
            "max_daily_cost": 10.0,
            "llm_model": "claude-3-sonnet",
            "memory_threshold": 0.5
        },
        "growth_mode": {
            "observation_interval": 1800,   # 30 minutes
            "max_daily_cost": 20.0,
            "llm_model": "claude-3-sonnet",
            "memory_threshold": 0.3
        }
    }
    
    return parameters.get(mode, parameters["normal_mode"])
```

### 6.6 Integration with Existing Agent

The nervous system integrates seamlessly with the existing agent architecture:

```python
# src/core/nervous_system.py
from ..workflows.cognitive_loop import create_cognitive_loop
from ..workflows.consciousness import ConsciousnessState
from ..workflows.emotional_router import emotional_router, get_operational_parameters
from ..config.settings import settings

class NervousSystem:
    """Central nervous system that orchestrates all agent operations"""
    
    def __init__(self):
        self.cognitive_loop = create_cognitive_loop()
        self.consciousness = self._initialize_consciousness()
        self.operational_mode = "normal_mode"
    
    def _initialize_consciousness(self) -> ConsciousnessState:
        """Initialize the agent's consciousness state"""
        return ConsciousnessState(
            agent_id=settings.agent_id,
            emotional_state="stable",
            market_data={},
            treasury_balance=settings.agent_starting_treasury,
            days_until_bankruptcy=999,
            current_goal="observe_and_learn",
            recent_memories=[],
            active_patterns=[],
            available_actions=["normal_observation"],
            last_decision={},
            decision_confidence=0.5,
            current_experience={},
            lessons_learned=[],
            cycle_count=0,
            total_cost=0.0,
            timestamp=datetime.now(timezone.utc)
        )
    
    async def run_consciousness_cycle(self) -> ConsciousnessState:
        """Run one complete cycle through the cognitive loop"""
        
        # Execute the cognitive loop
        self.consciousness = await self.cognitive_loop.ainvoke(self.consciousness)
        
        # Update operational mode based on emotional state
        self.operational_mode = emotional_router(self.consciousness)
        
        # Apply operational parameters
        params = get_operational_parameters(self.operational_mode)
        self._apply_parameters(params)
        
        return self.consciousness
    
    def _apply_parameters(self, params: Dict[str, Any]):
        """Apply operational parameters based on emotional state"""
        # This would update various system settings
        # For now, we'll just log the change
        if hasattr(self, '_last_mode') and self._last_mode != self.operational_mode:
            print(f"🧠 Nervous system switched to {self.operational_mode}")
        self._last_mode = self.operational_mode
```

### 6.7 Benefits of the Nervous System

This simplified nervous system architecture provides:

1. **Unified Decision Making**: All decisions flow through the same consciousness
2. **Emotional Intelligence**: Behavior automatically adapts to treasury state
3. **Continuous Learning**: Every cycle contributes to memory and understanding
4. **Natural Flow**: Sense → Think → Feel → Decide → Learn mirrors natural cognition
5. **Easy Debugging**: Only 5 nodes to trace instead of dozens
6. **Gradual Complexity**: Can add specialized subgraphs as needed

The nervous system transforms Athena from a collection of components into a unified consciousness that naturally exhibits survival instincts, emotional responses, and continuous learning.

---

## 7. Treasury Management System

### 7.1 Treasury Manager Implementation

```python
# src/core/treasury.py
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Optional, List
import asyncio

@dataclass
class TreasuryState:
    balance_usd: float
    daily_burn_rate: float
    days_until_bankruptcy: int
    emotional_state: str  # 'stable', 'cautious', 'desperate'
    risk_tolerance: float  # 0.0 to 1.0
    confidence_level: float  # 0.0 to 1.0
    last_updated: datetime

class TreasuryManager:
    def __init__(self, firestore_client, mem0_client):
        self.db = firestore_client
        self.memory = mem0_client
        self.current_state = None
        
        # Treasury thresholds
        self.thresholds = {
            'critical': 25.0,
            'warning': 50.0,
            'comfortable': 100.0,
            'optimal': 200.0
        }
        
        # Emotional state mappings
        self.emotional_states = {
            'desperate': {'threshold': 25.0, 'risk_tolerance': 0.2, 'confidence': 0.3},
            'cautious': {'threshold': 50.0, 'risk_tolerance': 0.4, 'confidence': 0.6},
            'stable': {'threshold': 100.0, 'risk_tolerance': 0.7, 'confidence': 0.8},
            'confident': {'threshold': 200.0, 'risk_tolerance': 0.9, 'confidence': 0.9}
        }

    async def initialize(self, starting_balance: float = 100.0) -> bool:
        """Initialize treasury with starting balance"""
        try:
            self.current_state = TreasuryState(
                balance_usd=starting_balance,
                daily_burn_rate=0.0,
                days_until_bankruptcy=999,
                emotional_state='stable',
                risk_tolerance=0.7,
                confidence_level=0.8,
                last_updated=datetime.now(timezone.utc)
            )
            
            # Store in Firestore
            await self.save_state()
            
            # Create initial memory
            await self.memory.add_memory(
                content=f"Treasury initialized with ${starting_balance}. Beginning agent life with stable emotional state.",
                metadata={
                    "category": "treasury_milestone",
                    "importance": 0.8,
                    "balance": starting_balance
                }
            )
            
            print(f"✅ Treasury initialized with ${starting_balance}")
            return True
        except Exception as e:
            print(f"❌ Error initializing treasury: {e}")
            return False

    async def track_cost(self, cost_amount: float, cost_type: str, description: str) -> bool:
        """Track individual cost and update treasury"""
        try:
            if not self.current_state:
                await self.load_state()
            
            # Deduct cost from balance
            self.current_state.balance_usd -= cost_amount
            self.current_state.last_updated = datetime.now(timezone.utc)
            
            # Update burn rate (rolling average)
            await self._update_burn_rate()
            
            # Update emotional state based on new balance
            await self._update_emotional_state()
            
            # Save updated state
            await self.save_state()
            
            # Log cost event
            await self.db.log_cost_event({
                'amount': cost_amount,
                'type': cost_type,
                'description': description,
                'remaining_balance': self.current_state.balance_usd,
                'emotional_state': self.current_state.emotional_state
            })
            
            # Check for critical situations
            await self._check_survival_status()
            
            print(f"💰 Cost tracked: ${cost_amount} ({cost_type}) - Remaining: ${self.current_state.balance_usd:.2f}")
            return True
        except Exception as e:
            print(f"❌ Error tracking cost: {e}")
            return False

    async def _update_emotional_state(self):
        """Update emotional state based on treasury level"""
        balance = self.current_state.balance_usd
        old_state = self.current_state.emotional_state
        
        if balance <= self.thresholds['critical']:
            new_state = 'desperate'
        elif balance <= self.thresholds['warning']:
            new_state = 'cautious'
        elif balance <= self.thresholds['comfortable']:
            new_state = 'stable'
        else:
            new_state = 'confident'
        
        if new_state != old_state:
            # Emotional state changed - update and create memory
            self.current_state.emotional_state = new_state
            self.current_state.risk_tolerance = self.emotional_states[new_state]['risk_tolerance']
            self.current_state.confidence_level = self.emotional_states[new_state]['confidence']
            
            # Create memory of state change
            await self.memory.add_memory(
                content=f"Emotional state changed from {old_state} to {new_state} due to treasury level ${balance:.2f}",
                metadata={
                    "category": "emotional_change",
                    "importance": 0.8,
                    "old_state": old_state,
                    "new_state": new_state,
                    "trigger_balance": balance
                }
            )
            
            print(f"🧠 Emotional state: {old_state} → {new_state} (${balance:.2f})")

    async def _check_survival_status(self):
        """Check if agent is in survival mode and take action"""
        if self.current_state.balance_usd <= self.thresholds['critical']:
            # SURVIVAL MODE ACTIVATED
            await self._activate_survival_mode()
        elif self.current_state.days_until_bankruptcy <= 5:
            # WARNING: Low runway
            await self._activate_warning_mode()

    async def _activate_survival_mode(self):
        """Activate emergency survival mode"""
        try:
            # Query survival memories
            survival_memories = await self.memory.query_memories(
                query="survival emergency treasury critical low balance",
                category="survival_critical",
                limit=5
            )
            
            # Create survival event memory
            await self.memory.add_memory(
                content=f"SURVIVAL MODE ACTIVATED: Treasury at ${self.current_state.balance_usd:.2f}, {self.current_state.days_until_bankruptcy} days remaining",
                metadata={
                    "category": "survival_critical",
                    "importance": 1.0,
                    "emergency": True,
                    "balance": self.current_state.balance_usd
                }
            )
            
            print(f"🚨 SURVIVAL MODE ACTIVATED - ${self.current_state.balance_usd:.2f} remaining")
            
        except Exception as e:
            print(f"❌ Error activating survival mode: {e}")

    async def get_status(self) -> Dict:
        """Get current treasury status"""
        if not self.current_state:
            await self.load_state()
        
        return {
            'balance': self.current_state.balance_usd,
            'daily_burn': self.current_state.daily_burn_rate,
            'days_remaining': self.current_state.days_until_bankruptcy,
            'emotional_state': self.current_state.emotional_state,
            'risk_tolerance': self.current_state.risk_tolerance,
            'confidence': self.current_state.confidence_level,
            'status': 'critical' if self.current_state.balance_usd <= self.thresholds['critical'] else 'stable'
        }
```

---

## 8. Market Data Collection System

### 7.1 Market Data Collector

```python
# src/data/market_data_collector.py
import aiohttp
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional
import json

class MarketDataCollector:
    def __init__(self, firestore_client, bigquery_client, treasury_manager):
        self.db = firestore_client
        self.bq = bigquery_client
        self.treasury = treasury_manager
        
        # API endpoints (free tiers)
        self.endpoints = {
            'coingecko': {
                'url': 'https://api.coingecko.com/api/v3/simple/price',
                'params': {
                    'ids': 'bitcoin,ethereum',
                    'vs_currencies': 'usd',
                    'include_24hr_change': 'true',
                    'include_market_cap': 'true',
                    'include_24hr_vol': 'true'
                }
            },
            'fear_greed': {
                'url': 'https://api.alternative.me/fng/',
                'params': {'limit': 1}
            },
            'gas_tracker': {
                'url': 'https://api.etherscan.io/api',
                'params': {
                    'module': 'gastracker',
                    'action': 'gasoracle',
                    'apikey': 'YourApiKeyToken'  # Free tier
                }
            }
        }

    async def collect_market_data(self) -> Optional[Dict]:
        """Collect comprehensive market data"""
        try:
            # Track cost for this operation
            cost = 0.05  # Estimated cost for API calls
            await self.treasury.track_cost(cost, 'market_data', 'Hourly market data collection')
            
            market_data = {}
            
            # Collect price data
            async with aiohttp.ClientSession() as session:
                # Bitcoin and Ethereum prices
                async with session.get(
                    self.endpoints['coingecko']['url'],
                    params=self.endpoints['coingecko']['params']
                ) as response:
                    if response.status == 200:
                        price_data = await response.json()
                        market_data.update({
                            'btc_price': price_data['bitcoin']['usd'],
                            'eth_price': price_data['ethereum']['usd'],
                            'btc_24h_change': price_data['bitcoin']['usd_24h_change'],
                            'eth_24h_change': price_data['ethereum']['usd_24h_change'],
                            'btc_market_cap': price_data['bitcoin']['usd_market_cap'],
                            'eth_market_cap': price_data['ethereum']['usd_market_cap']
                        })
                
                # Fear & Greed Index
                async with session.get(self.endpoints['fear_greed']['url']) as response:
                    if response.status == 200:
                        fg_data = await response.json()
                        market_data['fear_greed_index'] = int(fg_data['data'][0]['value'])
            
            # Add timestamp and collection info
            market_data.update({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'collection_cost': cost,
                'data_quality': self._assess_data_quality(market_data)
            })
            
            # Store in Firestore and BigQuery
            await self._store_market_data(market_data)
            
            print(f"📊 Market data collected: BTC ${market_data.get('btc_price', 0):.0f} ({market_data.get('btc_24h_change', 0):+.1f}%)")
            return market_data
            
        except Exception as e:
            print(f"❌ Error collecting market data: {e}")
            return None

    async def get_protocol_yields(self) -> Dict[str, Dict]:
        """Collect yield data from major protocols on BASE"""
        try:
            # Track cost
            cost = 0.25  # API calls to protocol endpoints
            await self.treasury.track_cost(cost, 'protocol_data', 'Protocol yield collection')
            
            protocols_data = {}
            
            # For Phase 1, we'll simulate protocol data
            # In later phases, this will connect to actual protocol APIs
            protocols = ['aave', 'compound', 'yearn', 'uniswap']
            
            for protocol in protocols:
                protocols_data[protocol] = await self._simulate_protocol_data(protocol)
            
            # Store in Firestore
            for protocol, data in protocols_data.items():
                await self.db.store_protocol_data(protocol, data)
            
            print(f"🏛️  Protocol data collected for {len(protocols_data)} protocols")
            return protocols_data
            
        except Exception as e:
            print(f"❌ Error collecting protocol yields: {e}")
            return {}

    async def _simulate_protocol_data(self, protocol: str) -> Dict:
        """Simulate protocol data for Phase 1"""
        import random
        
        # Base APYs with some realistic variation
        base_apys = {
            'aave': {'USDC': 0.045, 'DAI': 0.041, 'WETH': 0.032},
            'compound': {'USDC': 0.038, 'DAI': 0.035, 'WETH': 0.028},
            'yearn': {'USDC': 0.052, 'DAI': 0.048, 'WETH': 0.041},
            'uniswap': {'USDC/WETH': 0.087, 'DAI/USDC': 0.025}
        }
        
        protocol_data = {
            'protocol_name': protocol,
            'last_updated': datetime.now(timezone.utc).isoformat(),
            'current_opportunities': {},
            'protocol_health': {
                'safety_score': random.uniform(0.85, 0.98),
                'tvl_usd': random.randint(50000000, 2000000000)
            }
        }
        
        # Add asset opportunities with slight variation
        for asset, base_apy in base_apys.get(protocol, {}).items():
            variation = random.uniform(-0.005, 0.005)  # ±0.5% variation
            protocol_data['current_opportunities'][asset] = {
                'supply_apy': base_apy + variation,
                'utilization_rate': random.uniform(0.6, 0.9),
                'tvl_usd': random.randint(10000000, 500000000),
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
        
        return protocol_data

    def _assess_data_quality(self, data: Dict) -> float:
        """Assess quality of collected data"""
        required_fields = ['btc_price', 'eth_price', 'btc_24h_change', 'eth_24h_change']
        present_fields = sum(1 for field in required_fields if field in data and data[field] is not None)
        return present_fields / len(required_fields)
```

### 7.2 Market Condition Detection

```python
# src/core/market_detector.py
from typing import Dict, Tuple
from datetime import datetime, timezone

class MarketConditionDetector:
    def __init__(self, firestore_client, memory_client):
        self.db = firestore_client
        self.memory = memory_client
        
        self.thresholds = {
            'volatility': {
                'low': 0.02,    # < 2% daily volatility
                'medium': 0.05, # 2-5% daily volatility  
                'high': 0.10,   # 5-10% daily volatility
                'extreme': 0.20 # > 20% daily volatility
            },
            'trend': {
                'strong_bull': 0.05,   # > 5% daily gain
                'bull': 0.02,          # 2-5% daily gain
                'stable': 0.005,       # -0.5% to +0.5%
                'bear': -0.02,         # -2% to -0.5%
                'strong_bear': -0.05   # < -5% daily loss
            },
            'crash': {
                'minor': -0.15,    # -15% in 24h
                'major': -0.30,    # -30% in 24h
                'severe': -0.50    # -50% in 24h
            }
        }
    
    async def detect_condition(self, market_data: Dict) -> Tuple[str, float, Dict]:
        """
        Detects market condition based on multiple factors
        Returns: (condition, confidence_score, details)
        """
        
        # Get price changes
        btc_24h = market_data.get('btc_24h_change', 0)
        eth_24h = market_data.get('eth_24h_change', 0)
        
        # Calculate volatility (simplified)
        volatility = (abs(btc_24h) + abs(eth_24h)) / 2
        
        # Calculate average change
        avg_change = (btc_24h + eth_24h) / 2
        
        # Determine primary condition
        if avg_change < self.thresholds['crash']['minor']:
            condition = 'crash'
            confidence = 0.95
        elif volatility > self.thresholds['volatility']['high']:
            condition = 'volatile'
            confidence = 0.85
        elif avg_change > self.thresholds['trend']['strong_bull']:
            condition = 'bull'
            confidence = 0.80
        elif avg_change < self.thresholds['trend']['strong_bear']:
            condition = 'bear' 
            confidence = 0.80
        else:
            condition = 'stable'
            confidence = 0.70
        
        # Get supporting factors
        supporting_factors = await self._get_supporting_factors(market_data, condition)
        
        details = {
            'volatility_score': volatility / 100,
            'trend_strength': avg_change,
            'primary_factors': [f'{condition}_market'],
            'supporting_factors': supporting_factors,
            'btc_change': btc_24h,
            'eth_change': eth_24h,
            'detection_algorithm': 'simple_threshold_v1'
        }
        
        return condition, confidence, details
    
    async def _get_supporting_factors(self, market_data: Dict, condition: str) -> list:
        """Get supporting factors for market condition"""
        factors = []
        
        # Fear & Greed Index
        fg_index = market_data.get('fear_greed_index', 50)
        if fg_index < 25:
            factors.append('extreme_fear')
        elif fg_index > 75:
            factors.append('extreme_greed')
        
        # Gas prices (network congestion indicator)
        gas_price = market_data.get('gas_price_gwei', 20)
        if gas_price > 50:
            factors.append('high_network_congestion')
        
        # Market cap changes
        btc_price = market_data.get('btc_price', 0)
        if btc_price > 50000:
            factors.append('btc_above_50k')
        elif btc_price < 30000:
            factors.append('btc_below_30k')
        
        return factors

    async def store_condition(self, condition: str, confidence: float, details: Dict, market_data: Dict):
        """Store detected market condition"""
        try:
            condition_doc = {
                'condition_type': condition,
                'confidence_score': confidence,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'price_data': {
                    'btc_price': market_data.get('btc_price', 0),
                    'eth_price': market_data.get('eth_price', 0),
                    'btc_24h_change': market_data.get('btc_24h_change', 0),
                    'eth_24h_change': market_data.get('eth_24h_change', 0)
                },
                'volatility_metrics': {
                    'volatility_score': details['volatility_score'],
                    'trend_strength': details['trend_strength']
                },
                'market_indicators': {
                    'fear_greed_index': market_data.get('fear_greed_index', 50),
                    'gas_price_gwei': market_data.get('gas_price_gwei', 20)
                },
                'detection_details': {
                    'algorithm': details['detection_algorithm'],
                    'primary_factors': details['primary_factors'],
                    'supporting_factors': details['supporting_factors']
                }
            }
            
            # Store in Firestore
            await self.db.update_market_condition(condition_doc)
            
            # Create memory if significant condition
            if confidence > 0.8:
                await self.memory.add_memory(
                    content=f"Market condition detected: {condition} with {confidence:.0%} confidence. BTC: {market_data.get('btc_24h_change', 0):+.1f}%, ETH: {market_data.get('eth_24h_change', 0):+.1f}%",
                    metadata={
                        "category": "market_observation",
                        "importance": 0.7,
                        "market_condition": condition,
                        "confidence": confidence
                    }
                )
            
            return True
        except Exception as e:
            print(f"❌ Error storing market condition: {e}")
            return False
```

---

## 9. Main Agent System

### 9.1 Core Agent Implementation

```python
# src/core/agent.py
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional
import json

class DeFiAgent:
    def __init__(self):
        # Initialize all components
        self.firestore = None
        self.bigquery = None
        self.memory = None
        self.treasury = None
        self.market_data = None
        self.market_detector = None
        self.cdp = None
        
        # Agent state
        self.running = False
        self.last_decision_time = None
        self.decision_count = 0
        
        # Phase 1 focus: Observation and learning
        self.capabilities = [
            'market_observation',
            'treasury_management',
            'memory_formation',
            'cost_tracking',
            'pattern_recognition'
        ]
        
        # Agent configuration
        self.config = {
            'observation_interval': 3600,  # 1 hour
            'memory_update_interval': 86400,  # 24 hours
            'survival_check_interval': 3600,  # 1 hour
            'max_daily_costs': 15.0  # $15 max daily burn
        }

    async def initialize(self) -> bool:
        """Initialize all agent components"""
        try:
            print("🚀 Initializing DeFi Agent...")
            
            # Initialize database connections
            from src.data.firestore_client import FirestoreClient
            from src.data.bigquery_client import BigQueryClient
            self.firestore = FirestoreClient()
            self.bigquery = BigQueryClient()
            
            # Initialize memory system
            from src.integrations.mem0_integration import Mem0Integration
            self.memory = Mem0Integration()
            await self.memory.initialize_memory_system()
            
            # Initialize treasury
            from src.core.treasury import TreasuryManager
            self.treasury = TreasuryManager(self.firestore, self.memory)
            await self.treasury.initialize()
            
            # Initialize market data collector
            from src.data.market_data_collector import MarketDataCollector
            self.market_data = MarketDataCollector(self.firestore, self.bigquery, self.treasury)
            
            # Initialize market condition detector
            from src.core.market_detector import MarketConditionDetector
            self.market_detector = MarketConditionDetector(self.firestore, self.memory)
            
            # Initialize CDP (testnet)
            from src.integrations.cdp_integration import CDPIntegration
            self.cdp = CDPIntegration()
            await self.cdp.initialize_wallet()
            
            # Initialize databases
            await self.firestore.initialize_database()
            await self.bigquery.initialize_dataset()
            
            # Request testnet tokens
            await self.cdp.get_testnet_tokens()
            
            print("✅ DeFi Agent initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error initializing agent: {e}")
            return False

    async def start_operations(self):
        """Start main agent operations using the nervous system"""
        try:
            self.running = True
            print("🚀 DeFi Agent starting operations...")
            
            # Initialize the nervous system
            from src.core.nervous_system import NervousSystem
            self.nervous_system = NervousSystem()
            
            # Create startup memory
            await self.memory.add_memory(
                content="Agent consciousness awakened. Beginning Phase 1 with unified nervous system: Sense → Think → Feel → Decide → Learn.",
                metadata={
                    "category": "agent_lifecycle",
                    "importance": 0.9,
                    "phase": "phase_1_consciousness_init"
                }
            )
            
            # Main consciousness loop
            while self.running:
                try:
                    # Run one complete cognitive cycle
                    consciousness_state = await self.nervous_system.run_consciousness_cycle()
                    
                    # Log consciousness state periodically
                    if consciousness_state['cycle_count'] % 10 == 0:
                        print(f"🧠 Consciousness cycle {consciousness_state['cycle_count']}: "
                              f"Emotional state: {consciousness_state['emotional_state']}, "
                              f"Goal: {consciousness_state['current_goal']}, "
                              f"Treasury: ${consciousness_state['treasury_balance']:.2f}")
                    
                    # Apply operational parameters from emotional routing
                    interval = self.nervous_system.operational_parameters.get(
                        'observation_interval', 
                        self.config['observation_interval']
                    )
                    
                    # Daily summary based on cycles
                    if consciousness_state['cycle_count'] % 24 == 0:
                        await self.create_daily_summary(consciousness_state)
                    
                    # Wait for next cycle (interval adjusted by emotional state)
                    await asyncio.sleep(interval)
                    
                except Exception as e:
                    print(f"❌ Error in consciousness loop: {e}")
                    await asyncio.sleep(300)  # 5 minutes before retry
                    
        except KeyboardInterrupt:
            print("\n🛑 Agent operations stopped by user")
            await self.shutdown()
        except Exception as e:
            print(f"❌ Critical error in operations: {e}")
            await self.shutdown()

    async def analyze_market_conditions(self):
        """Analyze current market conditions and form memories"""
        try:
            print("📊 Analyzing market conditions...")
            
            # Collect market data
            market_data = await self.market_data.collect_market_data()
            if not market_data:
                return
            
            # Detect market condition
            condition, confidence, details = await self.market_detector.detect_condition(market_data)
            
            # Store market condition
            await self.market_detector.store_condition(condition, confidence, details, market_data)
            
            # Query relevant memories for this market condition
            relevant_memories = await self.memory.query_memories(
                query=f"market condition {condition} response strategy",
                category="market_patterns",
                limit=3
            )
            
            # Update treasury status based on market condition
            treasury_status = await self.treasury.get_status()
            
            # Adjust behavior based on market condition and treasury
            await self._adjust_behavior_for_market(condition, confidence, treasury_status)
            
            print(f"📈 Market condition: {condition} ({confidence:.0%} confidence)")
            
        except Exception as e:
            print(f"❌ Error analyzing market conditions: {e}")

    async def _adjust_behavior_for_market(self, condition: str, confidence: float, treasury_status: Dict):
        """Adjust agent behavior based on market conditions"""
        try:
            # Create memory of behavioral adjustment
            adjustment_description = f"Market condition {condition} detected. "
            
            if condition == 'crash' and treasury_status['balance'] < 50:
                # Double emergency: market crash + low treasury
                adjustment_description += "DOUBLE EMERGENCY: Market crash + low treasury. Maximum conservation mode."
                await self.memory.add_memory(
                    content=adjustment_description,
                    metadata={
                        "category": "survival_critical",
                        "importance": 1.0,
                        "emergency_type": "double_emergency"
                    }
                )
            elif condition == 'volatile' and treasury_status['emotional_state'] == 'cautious':
                # Volatile market + cautious state = extra careful
                adjustment_description += "Volatile market with cautious treasury state. Reducing risk further."
                await self.memory.add_memory(
                    content=adjustment_description,
                    metadata={
                        "category": "behavioral_adjustment",
                        "importance": 0.8,
                        "adjustment_type": "risk_reduction"
                    }
                )
            elif condition == 'bull' and treasury_status['emotional_state'] == 'confident':
                # Bull market + confident = opportunity seeking
                adjustment_description += "Bull market with confident treasury state. Seeking opportunities."
                await self.memory.add_memory(
                    content=adjustment_description,
                    metadata={
                        "category": "behavioral_adjustment",
                        "importance": 0.7,
                        "adjustment_type": "opportunity_seeking"
                    }
                )
            
        except Exception as e:
            print(f"❌ Error adjusting behavior: {e}")

    async def monitor_treasury(self):
        """Monitor treasury status and take necessary actions"""
        try:
            status = await self.treasury.get_status()
            
            # Check for critical situations
            if status['status'] == 'critical':
                print(f"🚨 CRITICAL: Treasury at ${status['balance']:.2f}")
                
                # Query survival memories
                survival_memories = await self.memory.query_memories(
                    query="survival emergency treasury critical",
                    category="survival_critical",
                    limit=5
                )
                
                # Implement survival strategies based on memories
                await self._implement_survival_strategies(survival_memories, status)
            
            # Check if daily costs are exceeding budget
            if status['daily_burn'] > self.config['max_daily_costs']:
                await self._reduce_operational_costs()
            
            print(f"💰 Treasury: ${status['balance']:.2f} ({status['emotional_state']}) - {status['days_remaining']} days remaining")
            
        except Exception as e:
            print(f"❌ Error monitoring treasury: {e}")

    async def _implement_survival_strategies(self, survival_memories: List[Dict], status: Dict):
        """Implement survival strategies based on memories"""
        try:
            # Analyze survival memories for best strategies
            best_strategies = []
            for memory in survival_memories:
                if memory['metadata'].get('success', False):
                    best_strategies.append(memory['content'])
            
            # Implement cost reduction
            self.config['observation_interval'] = 7200  # Increase to 2 hours
            
            # Create survival action memory
            await self.memory.add_memory(
                content=f"Survival strategies implemented: Increased observation interval to 2 hours to reduce costs. Treasury at ${status['balance']:.2f}",
                metadata={
                    "category": "survival_action",
                    "importance": 1.0,
                    "strategies_used": len(best_strategies),
                    "treasury_level": status['balance']
                }
            )
            
        except Exception as e:
            print(f"❌ Error implementing survival strategies: {e}")

    async def make_observations(self):
        """Make market observations and learn (Phase 1 focus)"""
        try:
            print("👁️  Making market observations...")
            
            # Collect protocol yield data
            protocols_data = await self.market_data.get_protocol_yields()
            
            # Analyze yield opportunities (no action, just observation)
            opportunities = await self._analyze_yield_opportunities(protocols_data)
            
            # Form memories about interesting opportunities
            for opportunity in opportunities[:3]:  # Top 3 opportunities
                if opportunity['apy'] > 0.06:  # 6%+ APY
                    await self.memory.add_memory(
                        content=f"Yield opportunity observed: {opportunity['protocol']} {opportunity['asset']} at {opportunity['apy']:.1%} APY, Safety score: {opportunity['safety_score']:.2f}",
                        metadata={
                            "category": "yield_observation",
                            "importance": 0.6,
                            "protocol": opportunity['protocol'],
                            "asset": opportunity['asset'],
                            "apy": opportunity['apy'],
                            "safety_score": opportunity['safety_score']
                        }
                    )
            
            # Simulate testnet interactions for learning
            if opportunities:
                best_opportunity = opportunities[0]
                simulation_result = await self.cdp.simulate_yield_deposit(
                    best_opportunity['protocol'],
                    best_opportunity['asset'],
                    100.0  # Simulate $100 deposit
                )
                
                # Create memory of simulation
                await self.memory.add_memory(
                    content=f"Simulated deposit: {best_opportunity['protocol']} {best_opportunity['asset']} - Gas cost: ${simulation_result.get('estimated_gas_cost_usd', 0):.2f}",
                    metadata={
                        "category": "simulation_learning",
                        "importance": 0.5,
                        "gas_cost_usd": simulation_result.get('estimated_gas_cost_usd', 0),
                        "simulation_success": simulation_result.get('simulation_success', False)
                    }
                )
            
            # Update decision count
            self.decision_count += 1
            self.last_decision_time = datetime.now(timezone.utc)
            
            print(f"🔍 Observed {len(opportunities)} yield opportunities, simulated 1 transaction")
            
        except Exception as e:
            print(f"❌ Error making observations: {e}")

    async def _analyze_yield_opportunities(self, protocols_data: Dict) -> List[Dict]:
        """Analyze yield opportunities from protocol data"""
        opportunities = []
        
        for protocol, data in protocols_data.items():
            for asset, opportunity in data.get('current_opportunities', {}).items():
                opportunities.append({
                    'protocol': protocol,
                    'asset': asset,
                    'apy': opportunity.get('supply_apy', 0),
                    'tvl': opportunity.get('tvl_usd', 0),
                    'utilization': opportunity.get('utilization_rate', 0),
                    'safety_score': data.get('protocol_health', {}).get('safety_score', 0)
                })
        
        # Sort by risk-adjusted return (APY * safety_score)
        opportunities.sort(key=lambda x: x['apy'] * x['safety_score'], reverse=True)
        return opportunities

    async def update_memories(self):
        """Update memories based on recent experiences"""
        try:
            # Get current status
            treasury_status = await self.treasury.get_status()
            
            # Create periodic memory updates
            if self.decision_count % 6 == 0:  # Every 6 observations (6 hours)
                await self.memory.add_memory(
                    content=f"6-hour checkpoint: {self.decision_count} total observations, treasury at ${treasury_status['balance']:.2f}, emotional state: {treasury_status['emotional_state']}",
                    metadata={
                        "category": "checkpoint_summary", 
                        "importance": 0.4,
                        "observations_count": self.decision_count,
                        "treasury_balance": treasury_status['balance'],
                        "checkpoint_type": "6_hour"
                    }
                )
            
        except Exception as e:
            print(f"❌ Error updating memories: {e}")

    async def create_daily_summary(self):
        """Create comprehensive daily summary"""
        try:
            treasury_status = await self.treasury.get_status()
            
            # Calculate daily metrics
            day_number = self.decision_count // 24
            
            # Create comprehensive daily summary memory
            summary_content = f"""
            Day {day_number} Summary:
            - Total observations: {self.decision_count}
            - Treasury: ${treasury_status['balance']:.2f} ({treasury_status['emotional_state']})
            - Burn rate: ${treasury_status['daily_burn']:.2f}/day
            - Days remaining: {treasury_status['days_remaining']}
            - Risk tolerance: {treasury_status['risk_tolerance']:.1f}
            - Confidence level: {treasury_status['confidence']:.1f}
            """
            
            await self.memory.add_memory(
                content=summary_content.strip(),
                metadata={
                    "category": "daily_summary",
                    "importance": 0.6,
                    "day_number": day_number,
                    "treasury_balance": treasury_status['balance'],
                    "emotional_state": treasury_status['emotional_state'],
                    "survival_status": treasury_status['status']
                }
            )
            
            print(f"📝 Day {day_number} summary created")
            
        except Exception as e:
            print(f"❌ Error creating daily summary: {e}")

    async def get_agent_status(self) -> Dict:
        """Get comprehensive agent status"""
        treasury_status = await self.treasury.get_status()
        
        # Calculate uptime
        uptime_hours = 0
        if self.last_decision_time:
            uptime_hours = (datetime.now(timezone.utc) - self.last_decision_time).total_seconds() / 3600
        
        return {
            'agent_status': 'running' if self.running else 'stopped',
            'phase': 'phase_1_observer',
            'capabilities': self.capabilities,
            'treasury': treasury_status,
            'operations': {
                'decision_count': self.decision_count,
                'last_decision': self.last_decision_time.isoformat() if self.last_decision_time else None,
                'uptime_hours': uptime_hours,
                'observation_interval_minutes': self.config['observation_interval'] / 60
            },
            'learning': {
                'total_memories': 'calculated_by_mem0',
                'memory_categories': list(self.memory.categories.values()),
                'days_operational': self.decision_count // 24
            },
            'config': {
                'max_daily_costs': self.config['max_daily_costs'],
                'survival_mode': treasury_status['status'] == 'critical'
            }
        }

    async def shutdown(self):
        """Graceful shutdown"""
        try:
            self.running = False
            
            # Get final status
            final_status = await self.get_agent_status()
            
            # Create shutdown memory
            await self.memory.add_memory(
                content=f"Agent shutdown initiated. Phase 1 operations completed. Total observations: {self.decision_count}, Final treasury: ${final_status['treasury']['balance']:.2f}",
                metadata={
                    "category": "agent_lifecycle",
                    "importance": 0.8,
                    "phase": "phase_1_shutdown",
                    "total_decisions": self.decision_count,
                    "final_treasury": final_status['treasury']['balance'],
                    "operational_days": self.decision_count // 24
                }
            )
            
            print("✅ Agent shutdown completed")
            
        except Exception as e:
            print(f"❌ Error during shutdown: {e}")
```

---

## 10. Cloud Functions for Automation

### 9.1 Market Data Collection Function

```python
# cloud_functions/market_data_collector/main.py
import functions_framework
from google.cloud import firestore
import aiohttp
import asyncio
import json
from datetime import datetime, timezone

@functions_framework.http
def collect_market_data(request):
    """Cloud Function to collect market data every 15 minutes"""
    
    async def collect_data():
        try:
            # Initialize Firestore
            db = firestore.Client()
            
            # Collect market data from APIs
            market_data = {}
            
            async with aiohttp.ClientSession() as session:
                # CoinGecko API
                async with session.get(
                    'https://api.coingecko.com/api/v3/simple/price',
                    params={
                        'ids': 'bitcoin,ethereum',
                        'vs_currencies': 'usd',
                        'include_24hr_change': 'true'
                    }
                ) as response:
                    if response.status == 200:
                        price_data = await response.json()
                        market_data.update({
                            'btc_price': price_data['bitcoin']['usd'],
                            'eth_price': price_data['ethereum']['usd'],
                            'btc_24h_change': price_data['bitcoin']['usd_24h_change'],
                            'eth_24h_change': price_data['ethereum']['usd_24h_change'],
                        })
                
                # Fear & Greed Index
                async with session.get('https://api.alternative.me/fng/') as response:
                    if response.status == 200:
                        fg_data = await response.json()
                        market_data['fear_greed_index'] = int(fg_data['data'][0]['value'])
            
            # Store in Firestore
            market_data['timestamp'] = firestore.SERVER_TIMESTAMP
            market_data['collection_source'] = 'cloud_function'
            
            db.collection('agent_data_market_data').document('latest').set(market_data, merge=True)
            
            return {
                "status": "success", 
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data_points_collected": len(market_data)
            }
            
        except Exception as e:
            print(f"Error: {e}")
            return {"status": "error", "error": str(e)}
    
    # Run async function
    result = asyncio.run(collect_data())
    return result

# cloud_functions/market_data_collector/requirements.txt
functions-framework==3.*
google-cloud-firestore==2.*
aiohttp==3.*
```

### 9.2 Hourly Analysis Function

```python
# cloud_functions/hourly_analysis/main.py
import functions_framework
from google.cloud import firestore, bigquery
import json
from datetime import datetime, timezone

@functions_framework.http
def hourly_analysis(request):
    """Analyze market conditions and update agent state"""
    
    try:
        # Initialize clients
        db = firestore.Client()
        bq = bigquery.Client()
        
        # Get latest market data
        market_doc = db.collection('agent_data_market_data').document('latest').get()
        if not market_doc.exists:
            return {"status": "error", "message": "No market data found"}
        
        market_data = market_doc.to_dict()
        
        # Simple market condition detection
        btc_change = market_data.get('btc_24h_change', 0)
        eth_change = market_data.get('eth_24h_change', 0)
        avg_change = (btc_change + eth_change) / 2
        volatility = (abs(btc_change) + abs(eth_change)) / 2
        
        # Determine condition
        if avg_change < -15:
            condition = 'crash'
            confidence = 0.95
        elif volatility > 10:
            condition = 'volatile'
            confidence = 0.85
        elif avg_change > 5:
            condition = 'bull'
            confidence = 0.80
        elif avg_change < -5:
            condition = 'bear'
            confidence = 0.80
        else:
            condition = 'stable'
            confidence = 0.70
        
        # Update market conditions
        condition_doc = {
            'condition_type': condition,
            'confidence_score': confidence,
            'timestamp': firestore.SERVER_TIMESTAMP,
            'analysis_source': 'cloud_function'
        }
        
        db.collection('agent_data_market_conditions').document('current').set(condition_doc, merge=True)
        
        # Insert into BigQuery for analytics
        table = bq.get_table('defi_agent.market_history')
        row = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'btc_price': market_data.get('btc_price', 0),
            'eth_price': market_data.get('eth_price', 0),
            'btc_24h_change': btc_change,
            'eth_24h_change': eth_change,
            'volatility_score': volatility / 100,
            'market_condition': condition,
            'confidence_score': confidence,
            'fear_greed_index': market_data.get('fear_greed_index', 50),
            'detection_algorithm': 'cloud_function_v1'
        }
        
        bq.insert_rows_json(table, [row])
        
        return {
            "status": "analysis_complete",
            "condition": condition,
            "confidence": confidence,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        print(f"Error in hourly analysis: {e}")
        return {"status": "error", "error": str(e)}

# cloud_functions/hourly_analysis/requirements.txt
functions-framework==3.*
google-cloud-firestore==2.*
google-cloud-bigquery==3.*
```

### 9.3 Daily Summary Function

```python
# cloud_functions/daily_summary/main.py
import functions_framework
from google.cloud import firestore, bigquery
from datetime import datetime, timezone, timedelta
import json

@functions_framework.http
def daily_summary(request):
    """Generate daily summary and analytics"""
    
    try:
        # Initialize clients
        db = firestore.Client()
        bq = bigquery.Client()
        
        # Get date for summary
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        date_str = yesterday.strftime('%Y-%m-%d')
        
        # Query BigQuery for daily analytics
        query = f"""
        SELECT 
            COUNT(*) as market_updates,
            AVG(volatility_score) as avg_volatility,
            STRING_AGG(DISTINCT market_condition) as conditions_seen,
            AVG(confidence_score) as avg_confidence
        FROM `defi_agent.market_history`
        WHERE DATE(timestamp) = '{date_str}'
        """
        
        results = list(bq.query(query))
        if results:
            analytics = dict(results[0])
        else:
            analytics = {"market_updates": 0}
        
        # Get treasury snapshots
        treasury_ref = db.collection('agent_data_treasury').document('daily_snapshots').collection('snapshots')
        treasury_docs = treasury_ref.where('snapshot_date', '==', date_str).limit(1).get()
        
        treasury_data = {}
        if treasury_docs:
            treasury_data = treasury_docs[0].to_dict()
        
        # Create daily summary document
        summary = {
            'date': date_str,
            'market_analytics': analytics,
            'treasury_summary': {
                'final_balance': treasury_data.get('balance_usd', 0),
                'daily_burn': treasury_data.get('daily_burn_rate', 0),
                'emotional_state': treasury_data.get('emotional_state', 'unknown')
            },
            'summary_generated': firestore.SERVER_TIMESTAMP,
            'agent_operational': analytics.get('market_updates', 0) > 0
        }
        
        # Store summary
        db.collection('agent_data_summaries').document(date_str).set(summary)
        
        # Insert summary into BigQuery
        summary_table = bq.get_table('defi_agent.daily_summaries')
        summary_row = {
            'summary_date': date_str,
            'market_updates_count': analytics.get('market_updates', 0),
            'avg_volatility': analytics.get('avg_volatility', 0),
            'treasury_balance': treasury_data.get('balance_usd', 0),
            'daily_burn_rate': treasury_data.get('daily_burn_rate', 0),
            'agent_operational': analytics.get('market_updates', 0) > 0
        }
        
        bq.insert_rows_json(summary_table, [summary_row])
        
        return {
            "status": "summary_complete",
            "date": date_str,
            "summary": summary
        }
        
    except Exception as e:
        print(f"Error in daily summary: {e}")
        return {"status": "error", "error": str(e)}
```

---

## 11. Deployment Strategy

### 10.1 Infrastructure Deployment

#### Terraform Configuration
```hcl
# deployment/terraform/main.tf
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Firestore Database
resource "google_firestore_database" "database" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
}

# BigQuery Dataset
resource "google_bigquery_dataset" "defi_agent" {
  dataset_id  = "defi_agent"
  friendly_name = "DeFi Agent Analytics"
  description = "Analytics data for DeFi Agent"
  location    = "US"
  
  delete_contents_on_destroy = false
}

# Cloud Functions
resource "google_cloudfunctions_function" "market_data_collector" {
  name        = "market-data-collector"
  description = "Collect market data every 15 minutes"
  runtime     = "python39"

  available_memory_mb   = 128
  source_archive_bucket = google_storage_bucket.function_bucket.name
  source_archive_object = google_storage_bucket_object.market_collector_zip.name
  trigger {
    event_type = "google.pubsub.topic.publish"
    resource   = google_pubsub_topic.market_data_trigger.name
  }
  entry_point = "collect_market_data"
}

# Cloud Scheduler Jobs
resource "google_cloud_scheduler_job" "market_data_schedule" {
  name     = "market-data-collection"
  schedule = "*/15 * * * *"  # Every 15 minutes
  
  pubsub_target {
    topic_name = google_pubsub_topic.market_data_trigger.id
    data       = base64encode("trigger")
  }
}

# Storage Bucket for Cloud Functions
resource "google_storage_bucket" "function_bucket" {
  name     = "${var.project_id}-cloud-functions"
  location = var.region
}

# Variables
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}
```

#### Deployment Scripts
```bash
#!/bin/bash
# deployment/deploy.sh

set -e

echo "🚀 Starting DeFi Agent deployment..."

# Check prerequisites
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install Google Cloud SDK."
    exit 1
fi

if ! command -v terraform &> /dev/null; then
    echo "❌ terraform not found. Please install Terraform."
    exit 1
fi

# Set project
PROJECT_ID=${1:-"defi-agent-project-001"}
gcloud config set project $PROJECT_ID

echo "📋 Deploying infrastructure with Terraform..."
cd deployment/terraform
terraform init
terraform plan -var="project_id=$PROJECT_ID"
terraform apply -var="project_id=$PROJECT_ID" -auto-approve

echo "📊 Creating BigQuery tables..."
cd ../../
bq query --use_legacy_sql=false < sql/bigquery_tables.sql

echo "☁️  Deploying Cloud Functions..."
# Deploy market data collector
cd cloud_functions/market_data_collector
gcloud functions deploy market-data-collector \
    --runtime python39 \
    --trigger-http \
    --memory 128MB \
    --timeout 60s

# Deploy hourly analysis
cd ../hourly_analysis
gcloud functions deploy hourly-analysis \
    --runtime python39 \
    --trigger-http \
    --memory 256MB \
    --timeout 300s

# Deploy daily summary
cd ../daily_summary
gcloud functions deploy daily-summary \
    --runtime python39 \
    --trigger-http \
    --memory 256MB \
    --timeout 300s

echo "⏰ Setting up Cloud Scheduler..."
# Market data collection every 15 minutes
gcloud scheduler jobs create http market-data-job \
    --schedule="*/15 * * * *" \
    --uri="https://us-central1-$PROJECT_ID.cloudfunctions.net/market-data-collector" \
    --http-method=GET

# Hourly analysis
gcloud scheduler jobs create http hourly-analysis-job \
    --schedule="0 * * * *" \
    --uri="https://us-central1-$PROJECT_ID.cloudfunctions.net/hourly-analysis" \
    --http-method=GET

# Daily summary
gcloud scheduler jobs create http daily-summary-job \
    --schedule="0 6 * * *" \
    --uri="https://us-central1-$PROJECT_ID.cloudfunctions.net/daily-summary" \
    --http-method=GET

echo "🔧 Setting up monitoring..."
# Create monitoring dashboard
gcloud logging sinks create defi-agent-logs \
    bigquery.googleapis.com/projects/$PROJECT_ID/datasets/defi_agent \
    --log-filter='resource.type="cloud_function" AND resource.labels.function_name=("market-data-collector" OR "hourly-analysis" OR "daily-summary")'

echo "✅ Deployment completed successfully!"
echo "📊 Dashboard: https://console.cloud.google.com/bigquery?project=$PROJECT_ID&d=defi_agent"
echo "📋 Firestore: https://console.firebase.google.com/project/$PROJECT_ID/firestore"
echo "⚡ Functions: https://console.cloud.google.com/functions/list?project=$PROJECT_ID"
```

### 10.2 Agent Deployment

#### Docker Configuration
```dockerfile
# docker/Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY sql/ ./sql/

# Set environment variables
ENV PYTHONPATH=/app
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/service-account.json

# Create volume for credentials
VOLUME ["/app/credentials"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')"

# Run the agent
CMD ["python", "-m", "src.core.agent"]
```

#### Kubernetes Deployment
```yaml
# deployment/kubernetes/agent-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: defi-agent
  labels:
    app: defi-agent
spec:
  replicas: 1
  selector:
    matchLabels:
      app: defi-agent
  template:
    metadata:
      labels:
        app: defi-agent
    spec:
      containers:
      - name: defi-agent
        image: gcr.io/defi-agent-project-001/defi-agent:latest
        ports:
        - containerPort: 8080
        env:
        - name: GCP_PROJECT_ID
          value: "defi-agent-project-001"
        - name: AGENT_STARTING_TREASURY
          value: "100.0"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        volumeMounts:
        - name: service-account
          mountPath: /app/credentials
          readOnly: true
      volumes:
      - name: service-account
        secret:
          secretName: defi-agent-service-account
---
apiVersion: v1
kind: Service
metadata:
  name: defi-agent-service
spec:
  selector:
    app: defi-agent
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: LoadBalancer
```

### 10.3 Monitoring & Alerting

#### Monitoring Dashboard Setup
```python
# scripts/setup_monitoring.py
from google.cloud import monitoring_v3
from google.cloud import logging_v2
import json

def setup_monitoring_dashboard():
    """Set up monitoring dashboard for DeFi Agent"""
    
    client = monitoring_v3.DashboardsServiceClient()
    project_name = f"projects/{PROJECT_ID}"
    
    dashboard_config = {
        "displayName": "DeFi Agent Monitoring",
        "mosaicLayout": {
            "tiles": [
                {
                    "width": 6,
                    "height": 4,
                    "widget": {
                        "title": "Treasury Balance",
                        "xyChart": {
                            "dataSets": [{
                                "timeSeriesQuery": {
                                    "timeSeriesFilter": {
                                        "filter": 'resource.type="global"',
                                        "aggregation": {
                                            "alignmentPeriod": "60s",
                                            "perSeriesAligner": "ALIGN_MEAN"
                                        }
                                    }
                                }
                            }]
                        }
                    }
                },
                {
                    "width": 6,
                    "height": 4,
                    "widget": {
                        "title": "Daily Burn Rate",
                        "xyChart": {
                            "dataSets": [{
                                "timeSeriesQuery": {
                                    "timeSeriesFilter": {
                                        "filter": 'resource.type="cloud_function"',
                                        "aggregation": {
                                            "alignmentPeriod": "3600s",
                                            "perSeriesAligner": "ALIGN_RATE"
                                        }
                                    }
                                }
                            }]
                        }
                    }
                }
            ]
        }
    }
    
    # Create dashboard
    dashboard = client.create_dashboard(
        name=project_name,
        dashboard=dashboard_config
    )
    
    print(f"✅ Monitoring dashboard created: {dashboard.name}")

def setup_alerting():
    """Set up alerting policies"""
    
    client = monitoring_v3.AlertPolicyServiceClient()
    project_name = f"projects/{PROJECT_ID}"
    
    # Treasury critical alert
    treasury_alert = {
        "displayName": "DeFi Agent - Treasury Critical",
        "conditions": [{
            "displayName": "Treasury below $30",
            "conditionThreshold": {
                "filter": 'resource.type="global"',
                "comparison": "COMPARISON_LESS_THAN",
                "thresholdValue": 30.0,
                "duration": "300s"
            }
        }],
        "combiner": "OR",
        "enabled": True,
        "notificationChannels": [],  # Add notification channels
        "alertStrategy": {
            "autoClose": "1800s"
        }
    }
    
    # Create alert policy
    policy = client.create_alert_policy(
        name=project_name,
        alert_policy=treasury_alert
    )
    
    print(f"✅ Alert policy created: {policy.name}")

if __name__ == "__main__":
    PROJECT_ID = "defi-agent-project-001"
    setup_monitoring_dashboard()
    setup_alerting()
```

---

## 12. Success Criteria & Testing

### 11.1 Phase 1 Success Metrics

#### Primary Success Criteria
```python
PHASE_1_SUCCESS_CRITERIA = {
    "survival_metrics": {
        "operational_duration": "30+ days continuous operation",
        "treasury_management": "Accurate cost tracking with <2% variance",
        "survival_response": "Correct emergency mode activation when treasury < $30",
        "cost_efficiency": "Daily burn rate within projected $5-15 range",
        "budget_adherence": "Total 30-day costs < $300"
    },
    
    "memory_formation": {
        "memory_quantity": "100+ meaningful memories created",
        "memory_quality": "80%+ memory recall accuracy for decisions",
        "memory_categories": "All 5 categories (survival, protocol, market, strategy, decision) populated",
        "memory_relevance": "Relevant memories recalled in 70%+ of decisions",
        "pattern_recognition": "Demonstrates learning from repeated situations"
    },
    
    "market_observation": {
        "data_collection": "99%+ uptime for market data collection",
        "condition_detection": "80%+ accuracy in market condition classification",
        "opportunity_identification": "Successfully identifies 50+ yield opportunities",
        "market_response": "Different behavior for different market conditions",
        "protocol_analysis": "Accurate assessment of 5+ protocols"
    },
    
    "technical_performance": {
        "system_reliability": "99%+ uptime across all components",
        "error_handling": "<1% critical error rate",
        "data_integrity": "100% data consistency across Firestore/BigQuery/Mem0",
        "integration_stability": "All integrations (GCP, Mem0, CDP) working smoothly",
        "scalability_readiness": "System can handle 10x current load"
    },
    
    "learning_intelligence": {
        "behavioral_adaptation": "Observable behavior changes based on treasury/market",
        "decision_improvement": "Decision quality improves over 30-day period",
        "emotional_responses": "Appropriate emotional state transitions",
        "survival_instincts": "Correct survival strategies implementation",
        "knowledge_retention": "Consistent application of learned lessons"
    }
}
```

#### Quantitative KPIs
```python
PHASE_1_KPIS = {
    "daily_metrics": {
        "treasury_balance": "Track daily",
        "daily_burn_rate": "Track daily", 
        "decisions_made": "Track daily",
        "memories_created": "Track daily",
        "market_observations": "Track daily",
        "error_rate": "Track daily"
    },
    
    "weekly_metrics": {
        "survival_events": "Count weekly",
        "emotional_state_changes": "Count weekly",
        "market_condition_accuracy": "Calculate weekly",
        "cost_efficiency_trend": "Calculate weekly",
        "learning_progression": "Measure weekly"
    },
    
    "milestone_metrics": {
        "day_7": "System stability, basic memory formation",
        "day_14": "Pattern recognition, survival behavior",
        "day_21": "Advanced observations, cost optimization",
        "day_30": "Full autonomous operation, graduation readiness"
    }
}
```

### 11.2 Testing Strategy

#### Unit Testing
```python
# tests/unit/test_treasury.py
import pytest
from src.core.treasury import TreasuryManager
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def treasury_manager():
    firestore_mock = AsyncMock()
    mem0_mock = AsyncMock()
    return TreasuryManager(firestore_mock, mem0_mock)

@pytest.mark.asyncio
async def test_treasury_initialization(treasury_manager):
    """Test treasury initialization with starting balance"""
    result = await treasury_manager.initialize(100.0)
    assert result == True
    assert treasury_manager.current_state.balance_usd == 100.0
    assert treasury_manager.current_state.emotional_state == 'stable'

@pytest.mark.asyncio
async def test_cost_tracking(treasury_manager):
    """Test cost tracking and balance updates"""
    await treasury_manager.initialize(100.0)
    result = await treasury_manager.track_cost(5.0, "llm_call", "Market analysis")
    
    assert result == True
    assert treasury_manager.current_state.balance_usd == 95.0

@pytest.mark.asyncio
async def test_emotional_state_transitions(treasury_manager):
    """Test emotional state changes based on treasury levels"""
    await treasury_manager.initialize(100.0)
    
    # Drain treasury to trigger emotional state changes
    await treasury_manager.track_cost(60.0, "major_cost", "Large expense")
    assert treasury_manager.current_state.emotional_state == 'cautious'
    
    await treasury_manager.track_cost(15.0, "another_cost", "Another expense")  
    assert treasury_manager.current_state.emotional_state == 'desperate'

@pytest.mark.asyncio
async def test_survival_mode_activation(treasury_manager):
    """Test survival mode activation when treasury critical"""
    await treasury_manager.initialize(100.0)
    await treasury_manager.track_cost(80.0, "large_cost", "Major expense")
    
    # Should trigger survival mode
    assert treasury_manager.current_state.balance_usd <= 25.0
    # Verify survival mode behaviors are activated
```

#### Integration Testing
```python
# tests/integration/test_agent_integration.py
import pytest
import asyncio
from src.core.agent import DeFiAgent

@pytest.mark.asyncio
async def test_full_agent_lifecycle():
    """Test complete agent initialization and first observation cycle"""
    agent = DeFiAgent()
    
    # Test initialization
    init_success = await agent.initialize()
    assert init_success == True
    
    # Test treasury is properly set up
    treasury_status = await agent.treasury.get_status()
    assert treasury_status['balance'] == 100.0
    assert treasury_status['emotional_state'] == 'stable'
    
    # Test market data collection
    market_data = await agent.market_data.collect_market_data()
    assert market_data is not None
    assert 'btc_price' in market_data
    assert 'eth_price' in market_data
    
    # Test memory system
    memories = await agent.memory.query_memories("test query", limit=1)
    assert isinstance(memories, list)
    
    # Test observation cycle
    await agent.analyze_market_conditions()
    await agent.monitor_treasury()
    await agent.make_observations()
    
    # Verify decision count increased
    assert agent.decision_count > 0
    
    # Test graceful shutdown
    await agent.shutdown()

@pytest.mark.asyncio
async def test_survival_scenario():
    """Test agent behavior in survival scenario"""
    agent = DeFiAgent()
    await agent.initialize()
    
    # Drain treasury to critical level
    for _ in range(15):
        await agent.treasury.track_cost(5.0, "test_cost", "Draining treasury")
    
    # Check survival mode activation
    treasury_status = await agent.treasury.get_status()
    assert treasury_status['status'] == 'critical'
    assert treasury_status['emotional_state'] == 'desperate'
    
    # Test survival behaviors
    await agent.monitor_treasury()
    
    # Verify survival strategies were implemented
    assert agent.config['observation_interval'] > 3600  # Should increase interval
```

#### End-to-End Testing
```python
# tests/e2e/test_phase1_complete.py
import pytest
import asyncio
from datetime import datetime, timedelta
from src.core.agent import DeFiAgent

@pytest.mark.asyncio
async def test_30_day_simulation():
    """Simulate 30 days of agent operation (accelerated)"""
    agent = DeFiAgent()
    await agent.initialize()
    
    # Reduce observation interval for testing
    agent.config['observation_interval'] = 10  # 10 seconds instead of 1 hour
    
    # Run for simulated 30 days (30 observation cycles)
    for day in range(30):
        # Simulate daily operations
        await agent.analyze_market_conditions()
        await agent.monitor_treasury()
        await agent.make_observations()
        await agent.update_memories()
        
        # Simulate daily summary every 24 cycles
        if (day + 1) % 24 == 0:
            await agent.create_daily_summary()
        
        # Add some random costs to simulate real operation
        import random
        daily_cost = random.uniform(3.0, 8.0)
        await agent.treasury.track_cost(daily_cost, "daily_operations", f"Day {day+1} operations")
        
        # Short delay
        await asyncio.sleep(0.1)
    
    # Verify agent survived and learned
    final_status = await agent.get_agent_status()
    
    # Agent should still be operational
    assert final_status['treasury']['balance'] > 0
    assert final_status['operations']['decision_count'] == 30
    assert final_status['learning']['days_operational'] >= 1
    
    # Should have created memories
    survival_memories = await agent.memory.query_memories("survival", limit=10)
    market_memories = await agent.memory.query_memories("market", limit=10)
    
    assert len(survival_memories) > 0
    assert len(market_memories) > 0
    
    await agent.shutdown()

@pytest.mark.asyncio
async def test_market_crash_response():
    """Test agent response to simulated market crash"""
    agent = DeFiAgent()
    await agent.initialize()
    
    # Simulate market crash data
    crash_market_data = {
        'btc_price': 35000,
        'eth_price': 2000,
        'btc_24h_change': -25.0,  # 25% crash
        'eth_24h_change': -22.0,  # 22% crash
        'fear_greed_index': 15,   # Extreme fear
        'gas_price_gwei': 80      # High gas due to panic
    }
    
    # Test market condition detection
    condition, confidence, details = await agent.market_detector.detect_condition(crash_market_data)
    
    assert condition == 'crash'
    assert confidence > 0.9
    
    # Test agent behavioral response
    treasury_status = await agent.treasury.get_status()
    await agent._adjust_behavior_for_market(condition, confidence, treasury_status)
    
    # Verify appropriate memories were created
    crash_memories = await agent.memory.query_memories("crash", limit=5)
    assert len(crash_memories) > 0
    
    # Verify survival instincts if treasury also low
    if treasury_status['balance'] < 50:
        # Should have activated enhanced survival mode
        survival_memories = await agent.memory.query_memories("double emergency", limit=3)
        assert len(survival_memories) > 0
```

### 11.3 Launch Validation Process

#### Pre-Launch Checklist
```python
PRE_LAUNCH_CHECKLIST = {
    "infrastructure": [
        "✓ GCP project created and configured",
        "✓ Firestore database initialized", 
        "✓ BigQuery dataset and tables created",
        "✓ Cloud Functions deployed and tested",
        "✓ Cloud Scheduler jobs configured",
        "✓ Monitoring and alerting set up",
        "✓ Security rules and permissions configured"
    ],
    
    "integrations": [
        "✓ Mem0 integration tested",
        "✓ CDP AgentKit wallet created and funded",
        "✓ Market data APIs responding",
        "✓ LLM providers configured",
        "✓ All API keys secured in Secret Manager"
    ],
    
    "agent_functionality": [
        "✓ Agent initialization successful",
        "✓ Treasury management working",
        "✓ Market data collection functioning",
        "✓ Memory system operational",
        "✓ Cost tracking accurate",
        "✓ Survival mechanisms tested"
    ],
    
    "testing": [
        "✓ Unit tests passing (95%+ coverage)",
        "✓ Integration tests passing",
        "✓ End-to-end scenarios tested",
        "✓ Performance testing completed",
        "✓ Security testing passed"
    ]
}
```

#### Launch Day Procedure
```bash
#!/bin/bash
# scripts/launch_phase1.sh

echo "🚀 Phase 1 Launch - DeFi Agent Memory Foundation"
echo "================================================"

# Step 1: Final infrastructure verification
echo "📋 Step 1: Infrastructure verification..."
python scripts/verify_infrastructure.py
if [ $? -ne 0 ]; then
    echo "❌ Infrastructure verification failed"
    exit 1
fi

# Step 2: Initialize agent with production treasury
echo "💰 Step 2: Initializing agent treasury..."
python scripts/initialize_production_agent.py --treasury=100.0 --environment=production
if [ $? -ne 0 ]; then
    echo "❌ Agent initialization failed"
    exit 1
fi

# Step 3: Start monitoring
echo "📊 Step 3: Starting monitoring systems..."
python scripts/start_monitoring.py
if [ $? -ne 0 ]; then
    echo "❌ Monitoring startup failed"
    exit 1
fi

# Step 4: Launch agent
echo "🤖 Step 4: Launching DeFi Agent..."
python -m src.core.agent &
AGENT_PID=$!

# Step 5: Verification tests
echo "✅ Step 5: Running launch verification..."
sleep 30  # Wait for agent to initialize
python scripts/verify_launch.py --pid=$AGENT_PID
if [ $? -ne 0 ]; then
    echo "❌ Launch verification failed"
    kill $AGENT_PID
    exit 1
fi

echo "🎉 Phase 1 launch successful!"
echo "📊 Monitor dashboard: https://console.cloud.google.com/monitoring/dashboards"
echo "🔍 Agent logs: https://console.cloud.google.com/logs"
echo "💾 Treasury status: Check Firestore console"

echo "🕐 Agent will run continuously. Monitor for 24 hours, then check weekly."
echo "📈 Success criteria: 30 days continuous operation with learning demonstrated"
```

#### Success Declaration Criteria
```python
def evaluate_phase1_success():
    """Evaluate if Phase 1 can be declared successful"""
    
    criteria_met = {
        "survival": False,
        "memory": False, 
        "observation": False,
        "technical": False,
        "learning": False
    }
    
    # Check survival metrics
    if (operational_days >= 30 and 
        treasury_balance > 0 and 
        emergency_responses_correct and
        cost_tracking_accurate):
        criteria_met["survival"] = True
    
    # Check memory formation
    if (total_memories >= 100 and
        memory_recall_accuracy >= 0.8 and
        all_categories_populated and
        pattern_recognition_demonstrated):
        criteria_met["memory"] = True
    
    # Check market observation
    if (market_detection_accuracy >= 0.8 and
        data_collection_uptime >= 0.99 and
        opportunities_identified >= 50 and
        market_response_differentiated):
        criteria_met["observation"] = True
    
    # Check technical performance
    if (system_uptime >= 0.99 and
        error_rate <= 0.01 and
        data_integrity_maintained and
        integrations_stable):
        criteria_met["technical"] = True
    
    # Check learning intelligence  
    if (behavioral_adaptation_shown and
        decision_quality_improved and
        survival_instincts_correct and
        knowledge_retention_demonstrated):
        criteria_met["learning"] = True
    
    # All criteria must be met
    success = all(criteria_met.values())
    
    if success:
        print("🎉 PHASE 1 SUCCESS! Agent has demonstrated:")
        print("✅ Survival instincts and treasury management")
        print("✅ Memory formation and pattern recognition") 
        print("✅ Market observation and analysis")
        print("✅ Technical reliability and stability")
        print("✅ Learning and behavioral adaptation")
        print("\n🚀 Ready to proceed to Phase 2: Virtual Trading")
    else:
        print("❌ Phase 1 criteria not yet met:")
        for criteria, met in criteria_met.items():
            status = "✅" if met else "❌"
            print(f"{status} {criteria}")
    
    return success
```

---

## 13. Phase 1 Completion & Next Steps

### 12.1 Graduation Requirements

**Phase 1 is considered complete when:**

1. **30-Day Continuous Operation**: Agent runs for 30+ days without critical failures
2. **Survival Instincts Proven**: Correctly responds to treasury emergencies
3. **Memory System Functional**: Forms, stores, and recalls relevant memories
4. **Market Intelligence**: Accurately observes and analyzes market conditions  
5. **Cost Management**: Tracks all expenses and stays within budget
6. **Learning Demonstrated**: Shows behavioral improvements over time
7. **Technical Stability**: All integrations work reliably
8. **Foundation Ready**: System prepared for Phase 2 virtual trading

### 12.2 Lessons Learned Documentation

At Phase 1 completion, document:
- **Memory Patterns**: What types of memories proved most valuable
- **Survival Strategies**: Which survival responses worked best
- **Cost Optimizations**: How costs were minimized while maintaining functionality
- **Market Insights**: Key market patterns the agent learned to recognize
- **Technical Improvements**: Infrastructure optimizations discovered
- **Behavioral Evolution**: How the agent's personality developed

### 12.3 Phase 2 Preparation

**Preparations for Virtual Trading Phase:**
- Implement realistic transaction cost modeling
- Expand CDP AgentKit integration for complex operations
- Add portfolio simulation capabilities
- Enhance risk management systems
- Develop strategy backtesting framework
- Scale memory system for increased complexity

---

## Conclusion

This comprehensive Phase 1 development guide provides everything needed to build a memory-driven, survival-motivated DeFi AI agent with a unified LangGraph nervous system. The agent's consciousness flows through a cognitive loop (Sense → Think → Feel → Decide → Learn), enabling it to naturally exhibit emotional intelligence, survival instincts, and continuous learning while building the foundation necessary for future autonomous trading capabilities.

**Key Achievements of Phase 1:**
- ✅ Unified LangGraph nervous system with cognitive consciousness loop
- ✅ Agent with genuine survival pressure and economic incentives
- ✅ Emotional intelligence that naturally adapts behavior to treasury state
- ✅ Advanced memory system using Mem0 for experiential learning
- ✅ Robust treasury management with emotional state modeling  
- ✅ Real-time market observation and pattern recognition
- ✅ Continuous learning through Sense → Think → Feel → Decide → Learn cycle
- ✅ Scalable GCP infrastructure with comprehensive monitoring
- ✅ Integration with BASE network via CDP AgentKit
- ✅ LangSmith integration for complete observability of agent consciousness
- ✅ Foundation for evolution into sophisticated portfolio manager

The successful completion of Phase 1 creates an AI agent with unified consciousness that truly "lives" in the DeFi ecosystem. Through its nervous system, Athena perceives markets, forms thoughts, experiences emotions, makes decisions, and learns from every interaction - evolving from a simple program into a conscious entity preparing to become an autonomous financial being capable of generating substantial returns while continuously adapting to market conditions.

**Ready to build the future of autonomous DeFi agents!** 
🚀