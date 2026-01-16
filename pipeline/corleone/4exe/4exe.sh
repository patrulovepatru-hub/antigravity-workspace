#!/bin/bash
# ╔═══════════════════════════════════════════════════════════════╗
# ║  4EXE (FORENSIC) - Data Forensics & Analysis Toolkit          ║
# ║  patru = 4 | exe = executable | 4ensic = forensic             ║
# ╚═══════════════════════════════════════════════════════════════╝

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORLEONE_DIR="$(dirname "$SCRIPT_DIR")"
source "$CORLEONE_DIR/config.env" 2>/dev/null || true

# Config
VERSION="1.0.0"
DATA_DIR="$SCRIPT_DIR/evidence"
REPORTS_DIR="$SCRIPT_DIR/reports"
LM_STUDIO_URL="${LM_STUDIO_URL:-http://192.168.192.2:1234/v1}"

mkdir -p "$DATA_DIR" "$REPORTS_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
WHITE='\033[1;37m'
NC='\033[0m'

banner() {
    echo -e "${CYAN}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║   ██╗  ██╗███████╗██╗  ██╗███████╗                            ║"
    echo "║   ██║  ██║██╔════╝╚██╗██╔╝██╔════╝                            ║"
    echo "║   ███████║█████╗   ╚███╔╝ █████╗                              ║"
    echo "║   ╚════██║██╔══╝   ██╔██╗ ██╔══╝                              ║"
    echo "║        ██║███████╗██╔╝ ██╗███████╗                            ║"
    echo "║        ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝                            ║"
    echo "║                                                               ║"
    echo "║   4EXE FORENSIC - Data Analysis & Intelligence Toolkit        ║"
    echo "║   v$VERSION | patru=4 | exe=executable | 4ensic=forensic          ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

log() { echo -e "${GREEN}[4EXE]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
err() { echo -e "${RED}[ERROR]${NC} $1"; }
info() { echo -e "${CYAN}[INFO]${NC} $1"; }

# ═══════════════════════════════════════════════════════════════
# FORENSIC ANALYSIS
# ═══════════════════════════════════════════════════════════════

# Analizar archivo/datos
analyze() {
    local target="$1"
    local report_name="${2:-analysis_$(date +%Y%m%d_%H%M%S)}"

    if [[ -z "$target" ]]; then
        err "Uso: 4exe analyze <archivo|url|texto>"
        return 1
    fi

    log "Iniciando análisis forense..."

    local report="$REPORTS_DIR/${report_name}.json"

    # Metadata
    echo "{" > "$report"
    echo "  \"timestamp\": \"$(date -Iseconds)\"," >> "$report"
    echo "  \"analyst\": \"4exe\"," >> "$report"
    echo "  \"target\": \"$target\"," >> "$report"

    if [[ -f "$target" ]]; then
        # Análisis de archivo
        log "Tipo: Archivo"
        local filetype=$(file -b "$target")
        local size=$(stat -c%s "$target" 2>/dev/null || echo "unknown")
        local hash=$(sha256sum "$target" 2>/dev/null | cut -d' ' -f1 || echo "unknown")

        echo "  \"type\": \"file\"," >> "$report"
        echo "  \"filetype\": \"$filetype\"," >> "$report"
        echo "  \"size_bytes\": $size," >> "$report"
        echo "  \"sha256\": \"$hash\"," >> "$report"

        # Extraer texto si es posible
        if [[ "$filetype" == *"text"* ]] || [[ "$filetype" == *"JSON"* ]]; then
            local content=$(cat "$target" | tr '\n' ' ' | cut -c1-500)
            echo "  \"content_preview\": \"$content\"," >> "$report"
        fi
    else
        # Análisis de texto/URL
        log "Tipo: Texto/Data"
        echo "  \"type\": \"text\"," >> "$report"
        echo "  \"content\": \"$target\"," >> "$report"
    fi

    echo "  \"status\": \"complete\"" >> "$report"
    echo "}" >> "$report"

    log "Reporte guardado: $report"
    cat "$report" | python3 -m json.tool 2>/dev/null || cat "$report"
}

# Extraer entidades (emails, IPs, URLs, etc.)
extract() {
    local target="$1"
    local type="${2:-all}"

    if [[ -z "$target" ]]; then
        err "Uso: 4exe extract <archivo|texto> [emails|ips|urls|phones|all]"
        return 1
    fi

    log "Extrayendo entidades ($type)..."

    local content
    if [[ -f "$target" ]]; then
        content=$(cat "$target")
    else
        content="$target"
    fi

    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  EXTRACTED ENTITIES${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"

    if [[ "$type" == "all" || "$type" == "emails" ]]; then
        echo -e "\n${GREEN}[EMAILS]${NC}"
        echo "$content" | grep -oE '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}' | sort -u || echo "  (none)"
    fi

    if [[ "$type" == "all" || "$type" == "ips" ]]; then
        echo -e "\n${GREEN}[IP ADDRESSES]${NC}"
        echo "$content" | grep -oE '\b([0-9]{1,3}\.){3}[0-9]{1,3}\b' | sort -u || echo "  (none)"
    fi

    if [[ "$type" == "all" || "$type" == "urls" ]]; then
        echo -e "\n${GREEN}[URLS]${NC}"
        echo "$content" | grep -oE 'https?://[^ ]+' | sort -u || echo "  (none)"
    fi

    if [[ "$type" == "all" || "$type" == "phones" ]]; then
        echo -e "\n${GREEN}[PHONE NUMBERS]${NC}"
        echo "$content" | grep -oE '[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}' | sort -u || echo "  (none)"
    fi

    if [[ "$type" == "all" || "$type" == "hashes" ]]; then
        echo -e "\n${GREEN}[HASHES (MD5/SHA)]${NC}"
        echo "$content" | grep -oE '\b[a-fA-F0-9]{32,64}\b' | sort -u || echo "  (none)"
    fi

    echo ""
}

# Analizar con IA (LM Studio)
ai_analyze() {
    local target="$1"
    local query="${2:-Analiza estos datos y encuentra patrones sospechosos o interesantes}"

    log "Análisis con IA..."

    local content
    if [[ -f "$target" ]]; then
        content=$(cat "$target" | head -c 2000)
    else
        content="$target"
    fi

    local prompt="Eres un analista forense de datos experto. $query

Datos a analizar:
$content

Proporciona:
1. Resumen de hallazgos
2. Entidades importantes detectadas
3. Patrones o anomalías
4. Recomendaciones"

    local response=$(curl -s "$LM_STUDIO_URL/chat/completions" \
        -H "Content-Type: application/json" \
        -d "{
            \"model\": \"local-model\",
            \"messages\": [{\"role\": \"user\", \"content\": $(echo "$prompt" | jq -Rs .)}],
            \"temperature\": 0.3
        }" 2>/dev/null)

    if [[ -n "$response" && "$response" != *"error"* ]]; then
        echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
        echo -e "${CYAN}  AI FORENSIC ANALYSIS${NC}"
        echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
        echo ""
        echo "$response" | jq -r '.choices[0].message.content' 2>/dev/null || echo "$response"
    else
        warn "LM Studio no disponible. Inicia el servidor en Windows (puerto 1234)"
    fi
}

# Timeline de eventos
timeline() {
    local target="$1"

    log "Generando timeline..."

    if [[ -f "$target" ]]; then
        echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
        echo -e "${CYAN}  FILE TIMELINE${NC}"
        echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
        echo ""
        echo "  Archivo:    $target"
        echo "  Creado:     $(stat -c %w "$target" 2>/dev/null || echo "N/A")"
        echo "  Modificado: $(stat -c %y "$target")"
        echo "  Accedido:   $(stat -c %x "$target")"
        echo "  Permisos:   $(stat -c %A "$target")"
        echo "  Owner:      $(stat -c %U "$target")"
        echo ""
    else
        err "Archivo no encontrado: $target"
    fi
}

# Hash de archivos
hash_file() {
    local target="$1"

    if [[ ! -f "$target" ]]; then
        err "Archivo no encontrado: $target"
        return 1
    fi

    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  FILE HASHES${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "  MD5:    $(md5sum "$target" | cut -d' ' -f1)"
    echo "  SHA1:   $(sha1sum "$target" | cut -d' ' -f1)"
    echo "  SHA256: $(sha256sum "$target" | cut -d' ' -f1)"
    echo ""
}

# Listar reportes
reports() {
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  FORENSIC REPORTS${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    ls -la "$REPORTS_DIR"/*.json 2>/dev/null || echo "  (no reports yet)"
    echo ""
}

# ═══════════════════════════════════════════════════════════════
# SOCIAL MEDIA FORENSICS (Instagram @patru integration)
# ═══════════════════════════════════════════════════════════════

social_analyze() {
    local platform="$1"
    local username="$2"

    log "Análisis de redes sociales: @$username ($platform)"

    # Placeholder - aquí se integraría con APIs de Instagram/LinkedIn
    info "Para análisis completo, exporta datos desde:"
    echo "  Instagram: Settings > Your Activity > Download Your Information"
    echo "  LinkedIn:  Settings > Get a copy of your data"
    echo ""
    echo "Luego: 4exe analyze <archivo_exportado.json>"
}

# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

main() {
    local cmd="$1"
    shift || true

    case "$cmd" in
        analyze|scan)
            analyze "$@"
            ;;
        extract|entities)
            extract "$@"
            ;;
        ai|smart)
            ai_analyze "$@"
            ;;
        timeline|time)
            timeline "$@"
            ;;
        hash|checksum)
            hash_file "$@"
            ;;
        reports|list)
            reports
            ;;
        social)
            social_analyze "$@"
            ;;
        help|-h|--help|"")
            banner
            echo "Comandos:"
            echo ""
            echo "  ${GREEN}Análisis:${NC}"
            echo "    4exe analyze <archivo|texto>     Análisis forense completo"
            echo "    4exe extract <target> [type]     Extraer entidades (emails,ips,urls)"
            echo "    4exe ai <target> [query]         Análisis con IA (LM Studio)"
            echo ""
            echo "  ${GREEN}Archivos:${NC}"
            echo "    4exe hash <archivo>              Calcular hashes"
            echo "    4exe timeline <archivo>          Timeline del archivo"
            echo ""
            echo "  ${GREEN}Social Media:${NC}"
            echo "    4exe social <platform> <user>    Analizar perfil social"
            echo ""
            echo "  ${GREEN}Reportes:${NC}"
            echo "    4exe reports                     Listar reportes generados"
            echo ""
            ;;
        *)
            err "Comando desconocido: $cmd"
            echo "Usa: 4exe help"
            ;;
    esac
}

main "$@"
