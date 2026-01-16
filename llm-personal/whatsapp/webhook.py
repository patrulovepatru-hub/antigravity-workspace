#!/usr/bin/env python3
"""
WhatsApp Webhook Handler
Receives messages from Twilio, sends to LLM, returns response
"""

from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from google.cloud import aiplatform
import os
import json

app = Flask(__name__)

# Configuration
PROJECT_ID = os.getenv("GCP_PROJECT", "gen-lang-client-0988614926")
LOCATION = os.getenv("GCP_LOCATION", "us-central1")
ENDPOINT_ID = os.getenv("ENDPOINT_ID", "")  # Set after deployment
MODEL_NAME = "antigravity-personal-v1"

# Fallback to local LLM
LOCAL_LLM = os.getenv("LOCAL_LLM", "http://host.docker.internal:1234/v1/chat/completions")

# Conversation history (in-memory, use Redis in production)
conversations = {}

def ask_vertex_ai(message, history):
    """Call fine-tuned model on Vertex AI"""
    try:
        if not ENDPOINT_ID:
            return None
            
        aiplatform.init(project=PROJECT_ID, location=LOCATION)
        endpoint = aiplatform.Endpoint(ENDPOINT_ID)
        
        response = endpoint.predict(instances=[{
            "prompt": format_prompt(message, history),
            "max_tokens": 500,
            "temperature": 0.7
        }])
        
        return response.predictions[0]
    except Exception as e:
        print(f"Vertex AI error: {e}")
        return None

def ask_local_llm(message, history):
    """Fallback to local LLM"""
    import requests
    
    try:
        response = requests.post(LOCAL_LLM, json={
            "model": "local-model",
            "messages": [
                {"role": "system", "content": "You are Antigravity, a personal AI assistant."},
                *[{"role": m["role"], "content": m["content"]} for m in history[-10:]],
                {"role": "user", "content": message}
            ],
            "max_tokens": 500,
            "temperature": 0.7
        }, timeout=30)
        
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Local LLM error: {e}")
        return None

def format_prompt(message, history):
    """Format conversation for the model"""
    prompt = "You are Antigravity, a personal AI assistant.\n\n"
    for h in history[-10:]:
        role = "User" if h["role"] == "user" else "Assistant"
        prompt += f"{role}: {h['content']}\n"
    prompt += f"User: {message}\nAssistant:"
    return prompt

@app.route("/webhook", methods=["POST"])
def webhook():
    """Handle incoming WhatsApp messages"""
    # Get message details
    incoming_msg = request.values.get("Body", "").strip()
    from_number = request.values.get("From", "")
    
    if not incoming_msg:
        return "OK", 200
    
    print(f"📱 Message from {from_number}: {incoming_msg}")
    
    # Get conversation history
    history = conversations.get(from_number, [])
    history.append({"role": "user", "content": incoming_msg})
    
    # Try Vertex AI first, fallback to local
    response = ask_vertex_ai(incoming_msg, history)
    if not response:
        response = ask_local_llm(incoming_msg, history)
    if not response:
        response = "Sorry, I'm having trouble connecting. Please try again later."
    
    # Save to history
    history.append({"role": "assistant", "content": response})
    conversations[from_number] = history[-20:]  # Keep last 20 messages
    
    print(f"🤖 Response: {response[:100]}...")
    
    # Send response via Twilio
    resp = MessagingResponse()
    resp.message(response)
    
    return str(resp)

@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok", "model": MODEL_NAME}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    print(f"🚀 WhatsApp webhook running on port {port}")
    app.run(host="0.0.0.0", port=port)
