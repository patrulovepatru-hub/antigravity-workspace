#!/bin/bash
# Pipeline: Análisis de Audiencia con Encriptación
# Flujo: Datos → Encriptar → Gemini → Antigravity → Sheets

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.env"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[PIPELINE]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# Crear directorios si no existen
mkdir -p "$DATA_DIR/raw" "$DATA_DIR/encrypted" "$DATA_DIR/processed"

# Función: Encriptar datos de entrada
encrypt_input() {
    local input_file="$1"
    local encrypted_file="$DATA_DIR/encrypted/$(basename "$input_file").enc"

    log "Encriptando: $input_file"
    "$SCRIPT_DIR/encrypt.sh" "$input_file" "$encrypted_file"
    echo "$encrypted_file"
}

# Función: Llamar a Gemini para optimizar prompt
call_gemini() {
    local data="$1"
    local prompt_template="$2"

    log "Llamando a Gemini ($GEMINI_MODEL)..."

    # Construir prompt para análisis de audiencia
    local full_prompt="Eres un experto en análisis de audiencia y marketing digital.
Analiza los siguientes datos de encuestas y genera insights sobre:
1. Intereses principales de la audiencia
2. Tendencias detectadas
3. Recomendaciones de contenido

Datos:
$data

Formato de salida: JSON con campos 'intereses', 'tendencias', 'recomendaciones'"

    # Llamar a Vertex AI
    local response=$("$GCLOUD_PATH/gcloud" ai models predict \
        --region="$GEMINI_REGION" \
        --model="publishers/google/models/$GEMINI_MODEL" \
        --json-request="{\"instances\":[{\"content\":\"$full_prompt\"}]}" \
        2>/dev/null || echo '{"error": "API call failed"}')

    echo "$response"
}

# Función: Procesar datos de Instagram
process_instagram() {
    local input_file="$1"
    log "Procesando datos de Instagram..."

    if [[ "$ENCRYPT_ALL_DATA" == "true" ]]; then
        local encrypted=$(encrypt_input "$input_file")
        # Desencriptar temporalmente para procesar
        local temp_file=$(mktemp)
        "$SCRIPT_DIR/decrypt.sh" "$encrypted" "$temp_file"
        local data=$(cat "$temp_file")
        rm "$temp_file"
    else
        local data=$(cat "$input_file")
    fi

    call_gemini "$data" "instagram"
}

# Función: Procesar datos de LinkedIn
process_linkedin() {
    local input_file="$1"
    log "Procesando datos de LinkedIn..."

    if [[ "$ENCRYPT_ALL_DATA" == "true" ]]; then
        local encrypted=$(encrypt_input "$input_file")
        local temp_file=$(mktemp)
        "$SCRIPT_DIR/decrypt.sh" "$encrypted" "$temp_file"
        local data=$(cat "$temp_file")
        rm "$temp_file"
    else
        local data=$(cat "$input_file")
    fi

    call_gemini "$data" "linkedin"
}

# Función principal
main() {
    local source="$1"
    local input_file="$2"

    if [[ -z "$source" || -z "$input_file" ]]; then
        echo "Uso: $0 <instagram|linkedin> <archivo_datos>"
        echo ""
        echo "Ejemplo:"
        echo "  $0 instagram data/encuesta_ig.json"
        exit 1
    fi

    log "Iniciando pipeline de análisis..."
    log "Fuente: $source"
    log "Encriptación: $ENCRYPT_ALL_DATA"

    case "$source" in
        instagram)
            process_instagram "$input_file"
            ;;
        linkedin)
            process_linkedin "$input_file"
            ;;
        *)
            error "Fuente no soportada: $source (usa: instagram, linkedin)"
            ;;
    esac

    log "Pipeline completado."
}

main "$@"
