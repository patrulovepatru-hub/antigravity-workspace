#!/bin/bash
# Deploy WhatsApp webhook to Cloud Run

PROJECT_ID="gen-lang-client-0988614926"
REGION="us-central1"
SERVICE_NAME="antigravity-whatsapp"

echo "🚀 Deploying WhatsApp Webhook to Cloud Run"

# Build and deploy
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
    --region $REGION \
    --allow-unauthenticated \
    --memory 512Mi \
    --port 8080

# Get URL
URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')

echo ""
echo "✅ Deployed!"
echo "📱 Webhook URL: $URL/webhook"
echo ""
echo "Next steps:"
echo "1. Go to https://console.twilio.com"
echo "2. Set WhatsApp sandbox webhook to: $URL/webhook"
echo "3. Test by sending a message to your Twilio WhatsApp number"
