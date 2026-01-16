#!/bin/bash
# Sistema de caché para respuestas de LLM (Ollama/Gemini)
# Evita llamadas repetidas = ahorro de créditos/tiempo

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CACHE_DIR="${CACHE_DIR:-$SCRIPT_DIR/cache}"
CACHE_TTL="${CACHE_TTL:-86400}"  # 24 horas en segundos

# Crear directorio de caché
mkdir -p "$CACHE_DIR"

# Generar hash único para una query
generate_hash() {
    local prompt="$1"
    local model="$2"
    echo -n "${model}:${prompt}" | sha256sum | cut -d' ' -f1
}

# Obtener ruta del archivo de caché
get_cache_file() {
    local hash="$1"
    echo "$CACHE_DIR/${hash}.cache"
}

# Verificar si existe caché válido
cache_exists() {
    local hash="$1"
    local cache_file=$(get_cache_file "$hash")

    if [[ ! -f "$cache_file" ]]; then
        return 1
    fi

    # Verificar TTL
    local file_age=$(($(date +%s) - $(stat -c %Y "$cache_file")))
    if [[ $file_age -gt $CACHE_TTL ]]; then
        rm "$cache_file"
        return 1
    fi

    return 0
}

# Leer de caché
cache_get() {
    local prompt="$1"
    local model="$2"
    local hash=$(generate_hash "$prompt" "$model")

    if cache_exists "$hash"; then
        cat "$(get_cache_file "$hash")"
        echo "[CACHE HIT]" >&2
        return 0
    fi

    return 1
}

# Guardar en caché
cache_set() {
    local prompt="$1"
    local model="$2"
    local response="$3"
    local hash=$(generate_hash "$prompt" "$model")
    local cache_file=$(get_cache_file "$hash")

    echo "$response" > "$cache_file"
    echo "[CACHE SET] $hash" >&2
}

# Limpiar caché expirado
cache_clean() {
    echo "Limpiando caché expirado (TTL: ${CACHE_TTL}s)..."
    local count=0
    for file in "$CACHE_DIR"/*.cache; do
        [[ -f "$file" ]] || continue
        local file_age=$(($(date +%s) - $(stat -c %Y "$file")))
        if [[ $file_age -gt $CACHE_TTL ]]; then
            rm "$file"
            ((count++))
        fi
    done
    echo "Eliminados: $count archivos"
}

# Estadísticas de caché
cache_stats() {
    local total=$(find "$CACHE_DIR" -name "*.cache" 2>/dev/null | wc -l)
    local size=$(du -sh "$CACHE_DIR" 2>/dev/null | cut -f1)
    echo "Entradas en caché: $total"
    echo "Tamaño total: $size"
}

# Wrapper para llamadas con caché
cached_call() {
    local prompt="$1"
    local model="$2"
    local command="$3"  # Comando a ejecutar si no hay caché

    # Intentar obtener de caché
    local cached_response
    if cached_response=$(cache_get "$prompt" "$model"); then
        echo "$cached_response"
        return 0
    fi

    # Ejecutar comando y cachear
    local response
    response=$(eval "$command")
    cache_set "$prompt" "$model" "$response"
    echo "$response"
}

# Main
case "$1" in
    get)
        cache_get "$2" "$3"
        ;;
    set)
        cache_set "$2" "$3" "$4"
        ;;
    clean)
        cache_clean
        ;;
    stats)
        cache_stats
        ;;
    *)
        echo "Uso: $0 <get|set|clean|stats> [args]"
        echo ""
        echo "Comandos:"
        echo "  get <prompt> <model>           Obtener de caché"
        echo "  set <prompt> <model> <response> Guardar en caché"
        echo "  clean                          Limpiar caché expirado"
        echo "  stats                          Ver estadísticas"
        ;;
esac
