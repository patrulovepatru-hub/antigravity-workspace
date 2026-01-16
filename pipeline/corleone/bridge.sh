#!/bin/bash
# CORLEONE Bridge - Sincronización VM ↔ Windows (Antigravity)
#
# VM Ubuntu:    192.168.192.128
# Host Windows: 192.168.192.2 (gateway)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.env" 2>/dev/null || true

# Configuración del Bridge
VM_IP="192.168.192.128"
HOST_IP="${HOST_IP:-192.168.192.2}"
BRIDGE_PORT="${BRIDGE_PORT:-8765}"
CORLEONE_DIR="/home/patricio/pipeline/corleone"

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log() { echo -e "${GREEN}[BRIDGE]${NC} $1"; }
info() { echo -e "${CYAN}[INFO]${NC} $1"; }

# Iniciar servidor HTTP para compartir archivos
start_server() {
    log "Iniciando servidor de archivos..."
    info "Accede desde Windows: http://$VM_IP:$BRIDGE_PORT"
    info "Directorio: $CORLEONE_DIR"
    echo ""
    cd "$CORLEONE_DIR"
    python3 -m http.server "$BRIDGE_PORT" --bind 0.0.0.0
}

# Enviar archivo a Windows (requiere carpeta compartida o servidor en Windows)
send_to_antigravity() {
    local file="$1"
    local dest="${2:-/antigravity/inbox}"

    if [[ ! -f "$file" ]]; then
        echo "Error: Archivo no encontrado: $file"
        exit 1
    fi

    log "Enviando a Antigravity: $file"
    # Usar curl para enviar via HTTP POST (si Antigravity tiene endpoint)
    # O copiar a carpeta compartida

    # Opción 1: Copiar via SCP (si SSH está habilitado en Windows)
    # scp "$file" user@$HOST_IP:"$dest"

    # Opción 2: Guardar en carpeta de salida para sync manual
    cp "$file" "$CORLEONE_DIR/outputs/"
    info "Archivo listo en: $CORLEONE_DIR/outputs/$(basename "$file")"
    info "Descarga desde Windows: http://$VM_IP:$BRIDGE_PORT/outputs/$(basename "$file")"
}

# Recibir archivo de Windows
receive_from_antigravity() {
    local url="$1"
    local dest="${2:-$CORLEONE_DIR/data}"

    log "Descargando de Antigravity: $url"
    curl -s -o "$dest/$(basename "$url")" "$url"
    info "Guardado en: $dest/$(basename "$url")"
}

# Mostrar estado del bridge
status() {
    echo "╔═══════════════════════════════════════════════════╗"
    echo "║          CORLEONE ↔ ANTIGRAVITY BRIDGE            ║"
    echo "╚═══════════════════════════════════════════════════╝"
    echo ""
    echo "  VM Ubuntu:     $VM_IP"
    echo "  Host Windows:  $HOST_IP"
    echo "  Puerto:        $BRIDGE_PORT"
    echo ""
    echo "  Desde Windows accede a:"
    echo "    http://$VM_IP:$BRIDGE_PORT/data/      → Datos"
    echo "    http://$VM_IP:$BRIDGE_PORT/outputs/   → Resultados"
    echo "    http://$VM_IP:$BRIDGE_PORT/prompts/   → Prompts"
    echo ""
}

# Main
case "$1" in
    start|server)
        start_server
        ;;
    send)
        send_to_antigravity "$2" "$3"
        ;;
    receive|get)
        receive_from_antigravity "$2" "$3"
        ;;
    status)
        status
        ;;
    *)
        echo "╔═══════════════════════════════════════╗"
        echo "║     CORLEONE Bridge - Comandos        ║"
        echo "╚═══════════════════════════════════════╝"
        echo ""
        echo "  $0 start              Iniciar servidor"
        echo "  $0 status             Ver configuración"
        echo "  $0 send <archivo>     Enviar a Antigravity"
        echo "  $0 receive <url>      Recibir de Windows"
        echo ""
        ;;
esac
