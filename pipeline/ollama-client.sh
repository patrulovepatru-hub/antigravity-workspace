#!/bin/bash
# Cliente para llamar a Ollama en Host Windows desde VM Ubuntu
# Uso: ./ollama-client.sh "prompt" [modelo]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.env" 2>/dev/null || true

# Configuración de Ollama (Host Windows)
OLLAMA_HOST="${OLLAMA_HOST:-192.168.192.2}"
OLLAMA_PORT="${OLLAMA_PORT:-11434}"
OLLAMA_MODEL="${2:-llama3:8b}"
OLLAMA_URL="http://${OLLAMA_HOST}:${OLLAMA_PORT}"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[OLLAMA]${NC} $1" >&2; }
error() { echo -e "${RED}[ERROR]${NC} $1" >&2; exit 1; }

# Verificar conectividad
check_connection() {
    log "Verificando conexión a Ollama ($OLLAMA_URL)..."
    if ! curl -s --connect-timeout 5 "$OLLAMA_URL/api/tags" > /dev/null 2>&1; then
        error "No se puede conectar a Ollama en $OLLAMA_URL

Asegúrate de que en Windows:
1. Ollama está corriendo: ollama serve
2. Firewall permite puerto 11434
3. OLLAMA_HOST=0.0.0.0:11434 está configurado"
    fi
    log "Conexión OK"
}

# Listar modelos disponibles
list_models() {
    log "Modelos disponibles:"
    curl -s "$OLLAMA_URL/api/tags" | jq -r '.models[].name' 2>/dev/null || echo "Error listando modelos"
}

# Llamar a Ollama
call_ollama() {
    local prompt="$1"
    local model="$2"

    log "Modelo: $model"
    log "Enviando prompt..."

    local response=$(curl -s "$OLLAMA_URL/api/generate" \
        -H "Content-Type: application/json" \
        -d "{
            \"model\": \"$model\",
            \"prompt\": \"$prompt\",
            \"stream\": false
        }" 2>/dev/null)

    if [[ -z "$response" ]]; then
        error "Sin respuesta de Ollama"
    fi

    # Extraer solo la respuesta
    echo "$response" | jq -r '.response' 2>/dev/null || echo "$response"
}

# Pre-procesar datos de audiencia (tarea específica)
preprocess_audience_data() {
    local data="$1"

    local prompt="Eres un analista de datos. Pre-procesa estos datos de encuestas de redes sociales:
1. Limpia datos irrelevantes o spam
2. Extrae keywords principales
3. Clasifica sentimiento (positivo/neutro/negativo)
4. Resume en JSON estructurado

Datos:
$data

Responde SOLO con JSON válido."

    call_ollama "$prompt" "$OLLAMA_MODEL"
}

# Main
main() {
    local action="$1"
    shift || true

    case "$action" in
        --check)
            check_connection
            ;;
        --list)
            check_connection
            list_models
            ;;
        --preprocess)
            check_connection
            preprocess_audience_data "$1"
            ;;
        --help|-h)
            echo "Uso: $0 <opción>"
            echo ""
            echo "Opciones:"
            echo "  --check              Verificar conexión a Ollama"
            echo "  --list               Listar modelos disponibles"
            echo "  --preprocess <data>  Pre-procesar datos de audiencia"
            echo "  <prompt> [modelo]    Enviar prompt directo"
            echo ""
            echo "Variables de entorno:"
            echo "  OLLAMA_HOST  Host de Ollama (default: 192.168.192.2)"
            echo "  OLLAMA_PORT  Puerto (default: 11434)"
            ;;
        *)
            if [[ -n "$action" ]]; then
                check_connection
                call_ollama "$action" "${1:-$OLLAMA_MODEL}"
            else
                echo "Uso: $0 --help"
            fi
            ;;
    esac
}

main "$@"
