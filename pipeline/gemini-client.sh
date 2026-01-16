#!/bin/bash
# Cliente para Gemini API (Generative Language API)
# Proyecto: GOAT - Default Gemini Project
# Uso: ./gemini-client.sh "prompt" [modelo]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.env" 2>/dev/null || true

# Configuración GOAT
PROJECT_ID="${GCP_PROJECT:-gen-lang-client-0988614926}"
PROJECT_NAME="GOAT"
GCLOUD="/home/patricio/google-cloud-sdk/bin/gcloud"

# Obtener token de acceso
get_token() {
    $GCLOUD auth print-access-token 2>/dev/null
}

# Llamar a Gemini via Generative Language API
call_gemini() {
    local prompt="$1"
    local model="${2:-gemini-1.5-flash}"
    local token=$(get_token)

    # Endpoint de Generative Language API
    local endpoint="https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent"

    local response=$(curl -s -X POST "$endpoint" \
        -H "Authorization: Bearer $token" \
        -H "Content-Type: application/json" \
        -H "x-goog-user-project: $PROJECT_ID" \
        -d "{
            \"contents\": [{
                \"parts\": [{\"text\": \"$prompt\"}]
            }],
            \"generationConfig\": {
                \"temperature\": 0.7,
                \"maxOutputTokens\": 1024
            }
        }" 2>/dev/null)

    # Extraer texto de respuesta
    echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'candidates' in data:
        print(data['candidates'][0]['content']['parts'][0]['text'])
    elif 'error' in data:
        print('ERROR:', data['error'].get('message', data['error']))
    else:
        print(json.dumps(data, indent=2))
except Exception as e:
    print('Parse error:', e)
    print(sys.stdin.read())
" 2>/dev/null || echo "$response"
}

# Main
prompt="$1"
model="${2:-gemini-1.5-flash}"

if [[ -z "$prompt" ]]; then
    echo "=== $PROJECT_NAME - Gemini Client ==="
    echo ""
    echo "Uso: $0 \"prompt\" [modelo]"
    echo ""
    echo "Modelos:"
    echo "  gemini-1.5-flash  (barato, rápido) [default]"
    echo "  gemini-1.5-pro    (más capaz)"
    echo "  gemini-pro        (legacy)"
    exit 1
fi

echo "[$PROJECT_NAME] Modelo: $model" >&2
call_gemini "$prompt" "$model"
