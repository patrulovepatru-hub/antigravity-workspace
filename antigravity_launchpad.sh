#!/bin/bash
# 🚀 ANTIGRAVITY LAUNCHPAD v3: ULTRA DEBUG EDITION
# Full Observability | API Call Tracing | Log File Generation

set -e

# Enable Bash tracing (Show every command executed)
set -x

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
LOG_FILE="antigravity_debug.log"

# Function to log both to screen and file
function log() {
    TIMESTAMP=$(date +'%H:%M:%S')
    echo -e "${BLUE}[$TIMESTAMP]${NC} $1" | tee -a "$LOG_FILE"
}

function debug_gcloud() {
    # Wrapper to run gcloud with debug verbosity
    log "Executing gcloud with debug tracing..."
    "$@" --verbosity=debug 2>&1 | tee -a "$LOG_FILE"
}

# Start Logging
echo ">>> ANTIGRAVITY LAUNCHPAD v3 <<<" > "$LOG_FILE"
date >> "$LOG_FILE"

clear
echo -e "${CYAN}>>> ANTIGRAVITY LAUNCHPAD v3 (ULTRA DEBUG) <<<${NC}"
log "Detailed logs are being saved to: $(pwd)/$LOG_FILE"
echo "---------------------------------------------"

# 1. GIT CHECK
log "Checking code status..."
git pull || log "⚠️ Git pull failed (continuing anyway...)"

# 2. INFRASTRUCTURE CHECK
log "Checking Cloud SQL Instance '$DB_INSTANCE'..."

# Use debug wrapper to see API calls
if gcloud sql instances describe $DB_INSTANCE --project=$PROJECT_ID &> /dev/null; then
    echo -e "${GREEN}✓ Database instance found!${NC}"
    
    STATUS=$(gcloud sql instances describe $DB_INSTANCE --project=$PROJECT_ID --format="value(state)")
    log "DB Status: $STATUS"
    
    if [ "$STATUS" != "RUNNABLE" ]; then
        log "⚠️ DB is not RUNNABLE yet (Status: $STATUS)."
        # Optional: wait loop could be added here
    fi
else
    log "⚠️ Database NOT FOUND. Attempting creation..."
    log "Detailed API call traces enabled below:"
    
    # Run creation with debug flags to see HTTP requests
    debug_gcloud gcloud sql instances create $DB_INSTANCE \
        --database-version=POSTGRES_15 \
        --tier=db-custom-2-7680 \
        --region=$REGION \
        --storage-size=20GB \
        --project=$PROJECT_ID
        
    echo -e "${GREEN}✓ Database creation command finished.${NC}"
fi

# Secret creation
log "Checking Secrets..."
if ! gcloud secrets describe antigravity-db-pass --project=$PROJECT_ID &> /dev/null; then
    log "Creating secret..."
    echo "supersecret" | debug_gcloud gcloud secrets create antigravity-db-pass --data-file=- --project=$PROJECT_ID
else
    log "✓ Secret already exists."
fi

# 3. VERTEX AI CHECK
log "Checking Training Jobs..."
gcloud ai custom-jobs list --project=$PROJECT_ID --region=$REGION --limit=3 --format="table(displayName, state, createTime)"

# 4. DEPLOY WEBHOOK
log "Deploying Webhook to Cloud Run..."
cd llm-personal/whatsapp

if [ ! -f deploy.sh ]; then
    echo -e "${RED}❌ ERROR: deploy.sh not found in $(pwd)${NC}"
    exit 1
fi

chmod +x deploy.sh
log "Running deploy.sh..."
# Execute deploy script with tracing
bash -x ./deploy.sh 2>&1 | tee -a "../../$LOG_FILE"

# Get URL
log "Retrieving Service URL..."
URL=$(gcloud run services describe antigravity-whatsapp --region $REGION --format 'value(status.url)' --project=$PROJECT_ID)

echo ""
echo "============================================="
echo -e "${GREEN}✅ DEPLOYMENT FINISHED${NC}"
echo "============================================="
echo -e "Webhook URL: ${CYAN}$URL/webhook${NC}"
echo "============================================="
