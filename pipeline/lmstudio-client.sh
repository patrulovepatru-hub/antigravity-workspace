#!/bin/bash
# ╔═══════════════════════════════════════════════════════════════╗
# ║  LM STUDIO CLIENT - Conexión a modelo local                   ║
# ║  PROPIEDAD INTELECTUAL: PATRICIO MIGUEL MARTIN MENDEZ         ║
# ╚═══════════════════════════════════════════════════════════════╝

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.env" 2>/dev/null || true

LM_URL="${LM_STUDIO_URL:-http://192.168.192.2:1234/v1}"

case "$1" in
    check|ping)
        echo -n "LM Studio ($LM_URL): "
        curl -s --connect-timeout 3 "$LM_URL/models" >/dev/null 2>&1 && echo "✅ OK" || echo "❌ DOWN"
        ;;
    models)
        curl -s "$LM_URL/models" | jq '.data[].id' 2>/dev/null || echo "No disponible"
        ;;
    chat|ask)
        shift
        curl -s "$LM_URL/chat/completions" \
            -H "Content-Type: application/json" \
            -d "{\"model\":\"local-model\",\"messages\":[{\"role\":\"user\",\"content\":\"$*\"}]}" \
            | jq -r '.choices[0].message.content' 2>/dev/null
        ;;
    *)
        echo "LM Studio Client"
        echo "  lm check       - Verificar conexión"
        echo "  lm models      - Listar modelos"
        echo "  lm chat <msg>  - Enviar mensaje"
        ;;
esac
