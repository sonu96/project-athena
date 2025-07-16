#!/bin/bash

# Setup Google Cloud for Athena Agent

PROJECT_ID="project-athena-development"
REGION="us-central1"

echo "🔧 Setting up Google Cloud resources for Athena Agent"

# Create secrets in Secret Manager
echo "Creating secrets..."

# CDP API Key Name
echo -n "organizations/f3bd1b0a-2d7b-44cd-b560-d49e9daf9164/apiKeys/73d1baa3-06f6-4b81-afc7-0b0d3b9c3fce" | \
    gcloud secrets create cdp-api-key-name --data-file=- --replication-policy=automatic 2>/dev/null || \
    echo "Secret cdp-api-key-name already exists"

# CDP API Key Secret
cat << 'EOF' | gcloud secrets create cdp-api-key-secret --data-file=- --replication-policy=automatic 2>/dev/null || echo "Secret cdp-api-key-secret already exists"
-----BEGIN EC PRIVATE KEY-----
MHcCAQEEII3xPX7RRCsIIqOQh0YQfZMcZNr/FPAuVXXOYAavJ7F6oAoGCCqGSM49
AwEHoUQDQgAEB0GXkxspJmFXmAtIDeyLLjNOa4rOy50vgH6T7NyVMfM3pU+sQQyS
P5Fu1doJXJr3GfAOX6P9bFtQMx0fPAr88Q==
-----END EC PRIVATE KEY-----
EOF

# Mem0 API Key
echo -n "m0-qzvcLpNJJXKwVnnqiSwKUqRsAhCCNu09wcKw4YJy" | \
    gcloud secrets create mem0-api-key --data-file=- --replication-policy=automatic 2>/dev/null || \
    echo "Secret mem0-api-key already exists"

# LangSmith API Key
echo -n "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" | \
    gcloud secrets create langsmith-api-key --data-file=- --replication-policy=automatic 2>/dev/null || \
    echo "Secret langsmith-api-key already exists"

# Create BigQuery dataset
echo "Creating BigQuery dataset..."
bq mk --dataset --location=${REGION} ${PROJECT_ID}:athena_analytics 2>/dev/null || \
    echo "Dataset athena_analytics already exists"

# Create BigQuery tables
echo "Creating BigQuery tables..."

# Agent metrics table
bq mk --table ${PROJECT_ID}:athena_analytics.agent_metrics \
    timestamp:TIMESTAMP,agent_id:STRING,treasury_balance:FLOAT64,emotional_state:STRING,cycle_count:INT64,memories_formed:INT64,patterns_recognized:INT64,total_cost:FLOAT64,cost_per_decision:FLOAT64 \
    2>/dev/null || echo "Table agent_metrics already exists"

# Pool observations table
bq mk --table ${PROJECT_ID}:athena_analytics.pool_observations \
    timestamp:TIMESTAMP,pool_address:STRING,pool_type:STRING,tvl_usd:FLOAT64,volume_24h_usd:FLOAT64,fee_apy:FLOAT64,reward_apy:FLOAT64,observation_notes:STRING \
    2>/dev/null || echo "Table pool_observations already exists"

# Memory usage table
bq mk --table ${PROJECT_ID}:athena_analytics.memory_usage \
    timestamp:TIMESTAMP,memory_id:STRING,category:STRING,times_accessed:INT64,influenced_decisions:INT64,success_correlation:FLOAT64 \
    2>/dev/null || echo "Table memory_usage already exists"

echo "✅ Google Cloud setup complete!"
echo ""
echo "Next steps:"
echo "1. Create service account key and save as service-account-key.json"
echo "2. Run: python test_mainnet.py"
echo "3. Deploy: ./deploy_cloud.sh"