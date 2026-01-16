#!/bin/bash
# CORLEONE - Cliente Gemini con API Key
# Uso: ./gemini.sh "prompt" [modelo]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.env" 2>/dev/null || true
source "$SCRIPT_DIR/../config.env" 2>/dev/null || true

# Verificar API Key
if [[ -z "$GEMINI_API_KEY" ]]; then
    echo "═══════════════════════════════════════════════════"
    echo "  CORLEONE necesita API Key de Gemini"
    echo "═══════════════════════════════════════════════════"
    echo ""
    echo "1. Ve a: https://aistudio.google.com/app/apikey"
    echo "2. Crea una API key"
    echo "3. Agrégala a: $SCRIPT_DIR/config.env"
    echo "   export GEMINI_API_KEY=\"tu-key-aqui\""
    echo ""
    exit 1
fi

call_gemini() {
    local prompt="$1"
    local model="${2:-$DEFAULT_MODEL}"

    local endpoint="https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${GEMINI_API_KEY}"

    local response=$(curl -s -X POST "$endpoint" \
        -H "Content-Type: application/json" \
        -d "{
            \"contents\": [{
                \"parts\": [{\"text\": \"$prompt\"}]
            }],
            \"generationConfig\": {
                \"temperature\": 0.7,
                \"maxOutputTokens\": 2048
            }
        }" 2>/dev/null)

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
except:
    pass
" 2>/dev/null || echo "$response"
}

# Main
prompt="$1"
model="${2:-$DEFAULT_MODEL}"

if [[ -z "$prompt" ]]; then
    echo "╔═══════════════════════════════════════╗"
    echo "║       CORLEONE - Gemini Client        ║"
    echo "╚═══════════════════════════════════════╝"
    echo ""
    echo "Uso: $0 \"prompt\" [modelo]"
    echo ""
    echo "Modelos:"
    echo "  gemini-1.5-flash  (default, barato)"
    echo "  gemini-1.5-pro    (premium)"
    exit 0
fi

echo "[CORLEONE] $model" >&2
call_gemini "$prompt" "$model"
