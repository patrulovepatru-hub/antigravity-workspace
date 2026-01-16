#!/bin/bash
# 🏗️ Antigravity Premium Infrastructure Setup
# Spending those credits wisely! 💸

PROJECT_ID="gen-lang-client-0988614926"
REGION="us-central1"
DB_INSTANCE="antigravity-memory"
DB_PASSWORD=$(openssl rand -base64 12)

echo "🚀 Starting Premium Infrastructure Setup..."
echo "💰 Project: $PROJECT_ID"

# 1. Enable APIs
echo "🔌 Enabling Premium APIs..."
gcloud services enable \
    sqladmin.googleapis.com \
    secretmanager.googleapis.com \
    aiplatform.googleapis.com \
    redis.googleapis.com \
    cloudbuild.googleapis.com \
    --project=$PROJECT_ID

# 2. Secret Manager (Safety First)
echo "🔐 Setting up Secret Manager..."
echo -n "$DB_PASSWORD" | gcloud secrets create antigravity-db-pass --data-file=- --project=$PROJECT_ID || true

# 3. Cloud SQL (PostgreSQL 15) - The Brain's Memory
echo "🧠 Provisioning Cloud SQL (Postgres 15)..."
echo "   (This takes ~5-10 mins, go grab a coffee ☕)"
gcloud sql instances create $DB_INSTANCE \
    --database-version=POSTGRES_15 \
    --tier=db-custom-4-15360 \
    --region=$REGION \
    --root-password=$DB_PASSWORD \
    --file-storage-type=SSD \
    --storage-size=100GB \
    --storage-auto-increase \
    --backup-start-time=04:00 \
    --project=$PROJECT_ID

# Create database
gcloud sql databases create antigravity_db --instance=$DB_INSTANCE --project=$PROJECT_ID

# 4. Redis (Short-term memory / Cache)
echo "⚡ Provisioning Redis (Memory Cache)..."
gcloud redis instances create antigravity-cache \
    --size=5 \
    --region=$REGION \
    --tier=STANDARD_HA \
    --project=$PROJECT_ID

echo ""
echo "==========================================="
echo "✅ INFRASTRUCTURE SETUP COMPLETE"
echo "==========================================="
echo "📝 DB Instance: $DB_INSTANCE"
echo "🔐 DB Password saved in Secret Manager"
echo "⚡ Redis: antigravity-cache"
echo "==========================================="
