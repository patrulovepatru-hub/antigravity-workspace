#!/bin/bash
# Deploy a Google Cloud Run
# Usa tus $300 de créditos

PROJECT_ID="tu-proyecto-gcp"  # Cambiar por tu project ID
SERVICE_NAME="fundex-bot"
REGION="europe-west1"

echo "🚀 Desplegando Fundex Bot a Cloud Run..."

# Build y push imagen
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

# Deploy a Cloud Run
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars WEBHOOK_SECRET=fundex2024

echo ""
echo "✅ Desplegado!"
echo ""
echo "Tu URL será algo como:"
echo "https://fundex-bot-xxxxx-ew.a.run.app"
echo ""
echo "Endpoints:"
echo "  GET  /health  - Check si está vivo"
echo "  GET  /status  - Ver balance y PnL"
echo "  POST /webhook - Recibe alertas de TradingView"
