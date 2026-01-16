#!/bin/bash
# ╔═══════════════════════════════════════════════════════════════╗
# ║  LOAD BALANCER - Distribución de cómputo AI                   ║
# ║  PROPIEDAD INTELECTUAL: PATRICIO MIGUEL MARTIN MENDEZ         ║
# ║  Todos los derechos reservados © 2024-2026                    ║
# ╚═══════════════════════════════════════════════════════════════╝

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIPELINE_DIR="$(dirname "$SCRIPT_DIR")"
source "$PIPELINE_DIR/config.env" 2>/dev/null || true

# ═══════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════
LM_STUDIO_URL="${LM_STUDIO_URL:-http://192.168.192.2:1234/v1}"
GEMINI_URL="https://generativelanguage.googleapis.com/v1beta"

# Estado de backends
declare -A BACKEND_STATUS
BACKEND_STATUS[lmstudio]="unknown"
BACKEND_STATUS[gemini]="unknown"

# Cola de overflow
QUEUE_DIR="$SCRIPT_DIR/queue"
mkdir -p "$QUEUE_DIR"

# Audit log
audit() {
    "$PIPELINE_DIR/logs/audit.sh" log "$1" "$2" "balancer" "$3" 2>/dev/null || true
}

# ═══════════════════════════════════════════════════════════════
# HEALTH CHECK
# ═══════════════════════════════════════════════════════════════
check_lmstudio() {
    local response=$(curl -s --connect-timeout 3 "$LM_STUDIO_URL/models" 2>/dev/null)
    if [[ -n "$response" && "$response" != *"error"* ]]; then
        BACKEND_STATUS[lmstudio]="healthy"
        return 0
    fi
    BACKEND_STATUS[lmstudio]="down"
    return 1
}

check_gemini() {
    # Gemini requiere auth, solo verificamos conectividad
    if curl -s --connect-timeout 3 "https://generativelanguage.googleapis.com" >/dev/null 2>&1; then
        BACKEND_STATUS[gemini]="available"
        return 0
    fi
    BACKEND_STATUS[gemini]="down"
    return 1
}

health_check() {
    echo "Verificando backends..."
    check_lmstudio && echo "  LM Studio: ✅ healthy" || echo "  LM Studio: ❌ down"
    check_gemini && echo "  Gemini:    ✅ available" || echo "  Gemini:    ❌ down"
}

# ═══════════════════════════════════════════════════════════════
# ROUTING
# ═══════════════════════════════════════════════════════════════
route_request() {
    local prompt="$1"
    local priority="${2:-normal}"  # normal, high, local-only, cloud-only

    audit "route_request" "priority=$priority" "pending"

    # Estrategia de routing
    case "$priority" in
        local-only)
            if check_lmstudio; then
                call_lmstudio "$prompt"
                return $?
            else
                echo "ERROR: LM Studio no disponible"
                return 1
            fi
            ;;
        cloud-only)
            call_gemini "$prompt"
            return $?
            ;;
        high)
            # Intentar local primero, fallback a cloud
            if check_lmstudio; then
                call_lmstudio "$prompt"
            else
                call_gemini "$prompt"
            fi
            ;;
        *)
            # Normal: local si disponible, sino cloud
            if check_lmstudio; then
                call_lmstudio "$prompt"
            elif check_gemini; then
                call_gemini "$prompt"
            else
                # Overflow: encolar
                queue_request "$prompt"
                echo "Request encolado (backends no disponibles)"
                return 2
            fi
            ;;
    esac
}

# ═══════════════════════════════════════════════════════════════
# BACKEND CALLS
# ═══════════════════════════════════════════════════════════════
call_lmstudio() {
    local prompt="$1"

    audit "call_lmstudio" "prompt_length=${#prompt}" "pending"

    local response=$(curl -s "$LM_STUDIO_URL/chat/completions" \
        -H "Content-Type: application/json" \
        -d "{
            \"model\": \"local-model\",
            \"messages\": [{\"role\": \"user\", \"content\": $(echo "$prompt" | jq -Rs .)}],
            \"temperature\": 0.7
        }" 2>/dev/null)

    if [[ -n "$response" ]]; then
        audit "call_lmstudio" "success" "success"
        echo "$response" | jq -r '.choices[0].message.content' 2>/dev/null || echo "$response"
        return 0
    fi

    audit "call_lmstudio" "failed" "error"
    return 1
}

call_gemini() {
    local prompt="$1"

    audit "call_gemini" "prompt_length=${#prompt}" "pending"

    # Usar el cliente de Gemini existente
    if [[ -x "$PIPELINE_DIR/corleone/gemini.sh" ]]; then
        "$PIPELINE_DIR/corleone/gemini.sh" "$prompt"
        audit "call_gemini" "success" "success"
    else
        echo "Gemini client no disponible"
        audit "call_gemini" "client_missing" "error"
        return 1
    fi
}

# ═══════════════════════════════════════════════════════════════
# OVERFLOW QUEUE
# ═══════════════════════════════════════════════════════════════
queue_request() {
    local prompt="$1"
    local id="Q-$(date +%s)"
    local file="$QUEUE_DIR/${id}.json"

    cat > "$file" <<EOF
{
    "id": "$id",
    "timestamp": "$(date -Iseconds)",
    "prompt": $(echo "$prompt" | jq -Rs .),
    "status": "pending"
}
EOF

    audit "queue_request" "id=$id" "queued"
    echo "$id"
}

process_queue() {
    echo "Procesando cola de overflow..."
    local processed=0

    for file in "$QUEUE_DIR"/*.json; do
        [[ -f "$file" ]] || continue

        local status=$(jq -r '.status' "$file")
        [[ "$status" == "pending" ]] || continue

        local prompt=$(jq -r '.prompt' "$file")
        local id=$(jq -r '.id' "$file")

        echo "Procesando: $id"

        if route_request "$prompt" "normal" >/dev/null; then
            jq '.status = "completed"' "$file" > "${file}.tmp" && mv "${file}.tmp" "$file"
            ((processed++))
        fi
    done

    echo "Procesados: $processed requests"
}

# ═══════════════════════════════════════════════════════════════
# STATUS
# ═══════════════════════════════════════════════════════════════
status() {
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║              LOAD BALANCER STATUS                         ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo ""

    health_check
    echo ""

    local queue_size=$(ls "$QUEUE_DIR"/*.json 2>/dev/null | wc -l)
    echo "  Queue size: $queue_size"
    echo ""
}

# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════
case "$1" in
    route|send)
        route_request "$2" "$3"
        ;;
    health|check)
        health_check
        ;;
    queue)
        queue_request "$2"
        ;;
    process)
        process_queue
        ;;
    status)
        status
        ;;
    *)
        echo "LOAD BALANCER - AI Request Distribution"
        echo "© PATRICIO MIGUEL MARTIN MENDEZ"
        echo ""
        echo "  lb route <prompt> [priority]   Enviar request"
        echo "  lb health                      Check backends"
        echo "  lb queue <prompt>              Encolar request"
        echo "  lb process                     Procesar cola"
        echo "  lb status                      Ver estado"
        echo ""
        echo "Prioridades: normal, high, local-only, cloud-only"
        ;;
esac
