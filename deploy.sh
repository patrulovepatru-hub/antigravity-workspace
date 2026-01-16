#!/bin/bash
# Deploy Antigravity Command Center to Google Cloud Run
# Usage: ./deploy.sh

set -e

# Configuration
PROJECT_ID="gen-lang-client-0988614926"
REGION="us-central1"
SERVICE_NAME="command-center"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "🚀 Deploying Antigravity Command Center to Cloud Run"
echo "   Project: $PROJECT_ID"
echo "   Region: $REGION"
echo ""

# Check if gcloud is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n 1 > /dev/null 2>&1; then
    echo "❌ Not authenticated. Run: gcloud auth login"
    exit 1
fi

# Set project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "📡 Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Build and push container
echo "🔨 Building container..."
gcloud builds submit --tag $IMAGE_NAME:latest .

# Deploy to Cloud Run
echo "☁️  Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME:latest \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --memory 256Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 3 \
    --port 8080

# Get the URL
URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')

echo ""
echo "✅ Deploy completado!"
echo ""
echo "🌐 Tu Command Center está disponible en:"
echo "   $URL"
echo ""
echo "📝 Siguiente paso: Actualiza CLOUD_URL en local_agent.js con esta URL"
echo ""
