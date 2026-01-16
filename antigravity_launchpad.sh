#!/bin/bash
# 🚀 ANTIGRAVITY LAUNCHPAD: The One-Click Wonder
# Orchestrates Infrastructure, Deployment, and AI Training
# Cost-Optimized for Maximum Runway & ROI

set -e

# Colors for "Wonderful Execution"
GREEN='\033[0;32m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PROJECT_ID="gen-lang-client-0988614926"
REGION="us-central1"
DB_INSTANCE="antigravity-memory-v1"

function print_header() {
    clear
    echo -e "${PURPLE}"
    echo "    ___  _   _  _____  ___  _____  ______   ___  _   _  ___  _____  __   __"
    echo "   / _ \| \ | ||_   _||_ _||  __ \|  _  \ / _ \| | | ||_ _||_   _| \ \ / /"
    echo "  / /_\ \  \| |  | |   | | | |  \/| | | |/ /_\ \ | | | | |   | |    \ V / "
    echo "  |  _  | . \` |  | |   | | | | __ | |/ / |  _  | | | | | |   | |     \ /  "
    echo "  | | | | |\  |  | |  _| |_| |_\ \|    /  | | | \ \_/ /_| |_  | |     | |  "
    echo "  \_| |_/_| \_/  \_/ |___/ \____/|_|\_\  \_| |_/ \___/ \___/  \_/     \_/  "
    echo "                                                                           "
    echo -e "${CYAN}        >>> PERSONAL AI EMPIRE BUILDER v1.0 <<<${NC}"
    echo -e "${BLUE}        Target: Google Cloud Platform ($PROJECT_ID)${NC}"
    echo ""
}

function spinner() {
    local pid=$1
    local delay=0.1
    local spinstr='|/-\'
    while [ "$(ps a | awk '{print $1}' | grep $pid)" ]; do
        local temp=${spinstr#?}
        printf " [%c]  " "$spinstr"
        local spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
}

print_header

# 1. GIT UPDATE
echo -e "${YELLOW}[1/5] 🔄 Syncing Codebase...${NC}"
git pull &> /dev/null
echo -e "${GREEN}✓ Codebase is up to date${NC}"
sleep 1

# 2. INFRASTRUCTURE (Optimized)
echo -e "${YELLOW}[2/5] 🏗️ Provisioning Premium Infrastructure (Cost Optimized)...${NC}"
echo -e "${CYAN}      Creating Cloud SQL (Postgres) & Secrets...${NC}"

# Check if DB exists to avoid error
if gcloud sql instances describe $DB_INSTANCE --project=$PROJECT_ID &> /dev/null; then
    echo -e "${GREEN}✓ Database $DB_INSTANCE already exists (Skipping creation)${NC}"
else
    # Create DB password
    DB_PASSWORD=$(openssl rand -base64 12)
    echo -n "$DB_PASSWORD" | gcloud secrets create antigravity-db-pass --data-file=- --project=$PROJECT_ID &> /dev/null || true
    
    # Create Instance (Optimized: 2 vCPU, 8GB RAM - $60-80/mo instead of $200)
    gcloud sql instances create $DB_INSTANCE \
        --database-version=POSTGRES_15 \
        --tier=db-custom-2-7680 \
        --region=$REGION \
        --root-password=$DB_PASSWORD \
        --storage-size=20GB \
        --storage-auto-increase \
        --project=$PROJECT_ID &
    
    PID=$!
    spinner $PID
    wait $PID
    echo -e "${GREEN}✓ Database Created Successfully${NC}"
    
    # Create DB
    gcloud sql databases create antigravity_db --instance=$DB_INSTANCE --project=$PROJECT_ID &> /dev/null
fi

# 3. VERTEX AI TRAINING CHECK
echo -e "${YELLOW}[3/5] 🧠 Checking Brain Training Status...${NC}"
# Simple check for jobs
JOBS=$(gcloud ai custom-jobs list --project=$PROJECT_ID --region=$REGION --format="value(state)" --limit=1)
if [[ "$JOBS" == "JOB_STATE_RUNNING" || "$JOBS" == "JOB_STATE_PENDING" ]]; then
    echo -e "${GREEN}✓ Fine-tuning is currently RUNNING${NC}"
    echo -e "${BLUE}      (You will receive an email when your brain is ready)${NC}"
else
    echo -e "${YELLOW}ℹ️ No active training job found (or finished).${NC}"
    echo -e "      To start training, run: python3 llm-personal/training/train.py"
fi
sleep 1

# 4. DEPLOY WEBHOOK
echo -e "${YELLOW}[4/5] 🚀 Deploying WhatsApp Webhook to Cloud Run...${NC}"
cd llm-personal/whatsapp
chmod +x deploy.sh
# Run deploy script silently but show progress
./deploy.sh > /dev/null 2>&1 &
PID=$!
spinner $PID
wait $PID

# Get URL
URL=$(gcloud run services describe antigravity-whatsapp --region $REGION --format 'value(status.url)' --project=$PROJECT_ID)
echo -e "${GREEN}✓ Webhook Deployed!${NC}"
echo -e "${CYAN}      URL: $URL/webhook${NC}"
cd ../..

# 5. SUMMARY
print_header
echo -e "${GREEN}✅ MISSION ACCOMPLISHED!${NC}"
echo ""
echo -e "${YELLOW}📱 NEXT STEPS FOR MARKETING & INCOME:${NC}"
echo "---------------------------------------------------"
echo "1. Copy this URL: ${CYAN}$URL/webhook${NC}"
echo "2. Configure Twilio Sandbox with this URL"
echo "3. Once the AI finishes training (~24h), it will automatically"
echo "   power this webhook."
echo ""
echo -e "${BLUE}Resources Provisioned:${NC}"
echo "- Database: $DB_INSTANCE (For email lists & leads)"
echo "- Connectors: WhatsApp Webhook (Active)"
echo "- AI Brain: Llama 3 (Training/Pending)"
echo ""
echo "You are ready to grow. 🚀"
