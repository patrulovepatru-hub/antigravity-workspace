#!/bin/bash
# 🚀 ANTIGRAVITY LAUNCHPAD v2: DEBUG EDITION
# Verbose Logging | Error Handling | Real-time Feedback

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

PROJECT_ID="gen-lang-client-0988614926"
REGION="us-central1"
DB_INSTANCE="antigravity-memory-v1"

function log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

function error_exit() {
    echo -e "${RED}❌ ERROR: $1${NC}"
    exit 1
}

clear
echo -e "${CYAN}>>> ANTIGRAVITY LAUNCHPAD v2 DEBUG MODE <<<${NC}"
echo "---------------------------------------------"

# 1. GIT CHECK
log "Checking code status..."
git pull || log "⚠️ Git pull failed (continuing anyway...)"

# 2. INFRASTRUCTURE CHECK
log "Checking Cloud SQL Instance '$DB_INSTANCE'..."

# Try to describe instance to see if it exists
if gcloud sql instances describe $DB_INSTANCE --project=$PROJECT_ID &> /dev/null; then
    echo -e "${GREEN}✓ Database instance found!${NC}"
    
    # Check status
    STATUS=$(gcloud sql instances describe $DB_INSTANCE --project=$PROJECT_ID --format="value(state)")
    log "DB Status: $STATUS"
    
    if [ "$STATUS" != "RUNNABLE" ]; then
        log "⚠️ DB is not RUNNABLE yet. Waiting..."
        # Optional: wait logic, but for now we proceed
    fi
else
    log "⚠️ Database NOT FOUND. Attempting creation..."
    log "Executing: gcloud sql instances create..."
    
    # Verbosely create it (NO /dev/null)
    gcloud sql instances create $DB_INSTANCE \
        --database-version=POSTGRES_15 \
        --tier=db-custom-2-7680 \
        --region=$REGION \
        --storage-size=20GB \
        --project=$PROJECT_ID
        
    echo -e "${GREEN}✓ Database creation command finished.${NC}"
fi

# Secret creation (Idempotent)
log "Checking Secrets..."
if ! gcloud secrets describe antigravity-db-pass --project=$PROJECT_ID &> /dev/null; then
    log "Creating secret 'antigravity-db-pass'..."
    echo "supersecret" | gcloud secrets create antigravity-db-pass --data-file=- --project=$PROJECT_ID
else
    log "✓ Secret already exists."
fi

# 3. VERTEX AI CHECK
log "Checking Training Jobs..."
gcloud ai custom-jobs list --project=$PROJECT_ID --region=$REGION --limit=3 --format="table(displayName, state, createTime)"

# 4. DEPLOY WEBHOOK
log "Deploying Webhook to Cloud Run..."
cd llm-personal/whatsapp

# Create deploy script if missing (failsafe)
if [ ! -f deploy.sh ]; then
    error_exit "deploy.sh not found in $(pwd)"
fi

chmod +x deploy.sh
log "Running deploy.sh (Output visible below)..."
# Run WITHOUT silencing output
./deploy.sh

# Get URL Explicitly
log "Retrieving Service URL..."
URL=$(gcloud run services describe antigravity-whatsapp --region $REGION --format 'value(status.url)' --project=$PROJECT_ID)

echo ""
echo "============================================="
echo -e "${GREEN}✅ DEPLOYMENT FINISHED${NC}"
echo "============================================="
echo -e "Webhook URL: ${CYAN}$URL/webhook${NC}"
echo "============================================="
