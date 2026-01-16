#!/bin/bash
# Pre-procesamiento local de datos (antes de enviar a LLM)
# Limpia, filtra y reduce datos para ahorrar tokens/créditos

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.env" 2>/dev/null || true

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[PREPROCESS]${NC} $1" >&2; }

# Limpiar texto básico
clean_text() {
    local input="$1"
    echo "$input" | \
        # Remover URLs
        sed -E 's|https?://[^ ]+||g' | \
        # Remover menciones @usuario
        sed -E 's|@[a-zA-Z0-9_]+||g' | \
        # Remover hashtags excesivos (mantener algunos)
        sed -E 's|#[a-zA-Z0-9_]+||g' | \
        # Normalizar espacios
        tr -s ' ' | \
        # Remover líneas vacías
        grep -v '^[[:space:]]*$' || true
}

# Filtrar spam/ruido común
filter_spam() {
    local input="$1"
    echo "$input" | \
        # Filtrar líneas muy cortas (< 10 chars)
        awk 'length > 10' | \
        # Filtrar patrones de spam comunes
        grep -v -i -E '(follow me|check my|link in bio|dm for|free money|giveaway)' || true
}

# Extraer keywords (frecuencia de palabras)
extract_keywords() {
    local input="$1"
    local top_n="${2:-20}"

    echo "$input" | \
        # Convertir a minúsculas
        tr '[:upper:]' '[:lower:]' | \
        # Separar palabras
        tr -cs '[:alpha:]' '\n' | \
        # Filtrar stopwords comunes
        grep -v -E '^(the|a|an|is|are|was|were|be|been|being|have|has|had|do|does|did|will|would|could|should|may|might|must|shall|can|need|dare|ought|used|to|of|in|for|on|with|at|by|from|as|into|through|during|before|after|above|below|between|under|again|further|then|once|here|there|when|where|why|how|all|each|few|more|most|other|some|such|no|nor|not|only|own|same|so|than|too|very|just|also|now|and|but|or|if|because|until|while|although|though|even|i|you|he|she|it|we|they|me|him|her|us|them|my|your|his|its|our|their|this|that|these|those|que|de|la|el|en|y|a|los|las|un|una|es|se|del|por|con|para|su|al|lo|como|más|pero|sus|le|ya|o|porque|cuando|muy|sin|sobre|también|me|hasta|hay|donde|quien|desde|todo|nos|durante|todos|uno|les|ni|contra|otros|ese|eso|ante|ellos|e|esto|mi|antes|algunos|qué|unos|yo|otro|otras|otra|él|tanto|esa|estos|mucho|quienes|nada|muchos|cual|poco|ella|estar|estas|algunas|algo|nosotros|tu|ellas|ese|ti)$' | \
        # Contar frecuencia
        sort | uniq -c | sort -rn | \
        # Top N
        head -n "$top_n" | \
        # Formatear como JSON array
        awk '{print "\"" $2 "\""}' | paste -sd, | sed 's/^/[/;s/$/]/'
}

# Agregar datos por categoría
aggregate_data() {
    local input="$1"
    local total_lines=$(echo "$input" | wc -l)
    local total_chars=$(echo "$input" | wc -c)
    local avg_length=$((total_chars / (total_lines + 1)))

    cat <<EOF
{
  "stats": {
    "total_entries": $total_lines,
    "total_chars": $total_chars,
    "avg_length": $avg_length
  },
  "keywords": $(extract_keywords "$input" 15),
  "sample": $(echo "$input" | head -5 | jq -R -s 'split("\n") | .[:-1]')
}
EOF
}

# Pipeline completo de pre-procesamiento
preprocess_full() {
    local input_file="$1"
    local output_file="${2:-/dev/stdout}"

    if [[ ! -f "$input_file" ]]; then
        echo "Error: Archivo no encontrado: $input_file" >&2
        exit 1
    fi

    log "Procesando: $input_file"

    local data=$(cat "$input_file")
    local original_size=${#data}

    log "Tamaño original: $original_size bytes"

    # Aplicar filtros
    data=$(clean_text "$data")
    data=$(filter_spam "$data")

    local processed_size=${#data}
    local reduction=$((100 - (processed_size * 100 / original_size)))

    log "Tamaño procesado: $processed_size bytes (reducción: ${reduction}%)"

    # Generar output agregado
    aggregate_data "$data" > "$output_file"

    log "Output: $output_file"
}

# Main
case "$1" in
    --clean)
        clean_text "$(cat "${2:-/dev/stdin}")"
        ;;
    --filter)
        filter_spam "$(cat "${2:-/dev/stdin}")"
        ;;
    --keywords)
        extract_keywords "$(cat "${2:-/dev/stdin}")" "$3"
        ;;
    --aggregate)
        aggregate_data "$(cat "${2:-/dev/stdin}")"
        ;;
    --full)
        preprocess_full "$2" "$3"
        ;;
    --help|-h)
        echo "Uso: $0 <opción> [archivo]"
        echo ""
        echo "Opciones:"
        echo "  --clean [archivo]        Limpiar texto (URLs, menciones, etc.)"
        echo "  --filter [archivo]       Filtrar spam/ruido"
        echo "  --keywords [archivo] [n] Extraer top N keywords"
        echo "  --aggregate [archivo]    Agregar estadísticas"
        echo "  --full <input> [output]  Pipeline completo"
        echo ""
        echo "Ejemplo:"
        echo "  $0 --full data/encuesta.txt data/processed.json"
        ;;
    *)
        if [[ -f "$1" ]]; then
            preprocess_full "$1"
        else
            echo "Uso: $0 --help"
        fi
        ;;
esac
