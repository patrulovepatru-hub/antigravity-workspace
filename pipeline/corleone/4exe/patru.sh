#!/bin/bash
# ╔═══════════════════════════════════════════════════════════════╗
# ║  PATRU.EXE - Influencer Management Toolkit                    ║
# ║  Instagram Integration + Influencer Payments                  ║
# ╚═══════════════════════════════════════════════════════════════╝

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORLEONE_DIR="$(dirname "$SCRIPT_DIR")"
source "$CORLEONE_DIR/config.env" 2>/dev/null || true

# Configuración
PATRU_VERSION="1.0.0"
PATRU_DATA="$SCRIPT_DIR/data"
PATRU_DB="$SCRIPT_DIR/influencers.json"
LM_STUDIO_URL="${LM_STUDIO_URL:-http://192.168.192.2:1234/v1}"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Banner
show_banner() {
    echo -e "${MAGENTA}"
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║     ██████╗  █████╗ ████████╗██████╗ ██╗   ██╗           ║"
    echo "║     ██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗██║   ██║           ║"
    echo "║     ██████╔╝███████║   ██║   ██████╔╝██║   ██║           ║"
    echo "║     ██╔═══╝ ██╔══██║   ██║   ██╔══██╗██║   ██║           ║"
    echo "║     ██║     ██║  ██║   ██║   ██║  ██║╚██████╔╝           ║"
    echo "║     ╚═╝     ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝            ║"
    echo "║                                                           ║"
    echo "║     Influencer Management + Instagram Payments            ║"
    echo "║     v$PATRU_VERSION                                              ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

log() { echo -e "${GREEN}[PATRU]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Inicializar base de datos de influencers
init_db() {
    if [[ ! -f "$PATRU_DB" ]]; then
        echo '{"influencers":[],"payments":[],"campaigns":[]}' > "$PATRU_DB"
        log "Base de datos creada: $PATRU_DB"
    fi
}

# ═══════════════════════════════════════════════════════════════
# INSTAGRAM FUNCTIONS
# ═══════════════════════════════════════════════════════════════

# Agregar influencer
influencer_add() {
    local username="$1"
    local platform="${2:-instagram}"
    local rate="${3:-0}"
    local category="${4:-general}"

    init_db

    local entry=$(cat <<EOF
{
    "id": "$(date +%s)",
    "username": "$username",
    "platform": "$platform",
    "rate_per_post": $rate,
    "category": "$category",
    "status": "active",
    "total_paid": 0,
    "posts_done": 0,
    "added_date": "$(date -Iseconds)"
}
EOF
)

    # Agregar al JSON
    local tmp=$(mktemp)
    jq ".influencers += [$entry]" "$PATRU_DB" > "$tmp" && mv "$tmp" "$PATRU_DB"

    log "Influencer agregado: @$username ($platform)"
    echo "  Rate: \$$rate/post | Categoría: $category"
}

# Listar influencers
influencer_list() {
    init_db
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  INFLUENCERS DATABASE${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"

    jq -r '.influencers[] | "  @\(.username) | \(.platform) | $\(.rate_per_post)/post | \(.category) | Paid: $\(.total_paid)"' "$PATRU_DB" 2>/dev/null || echo "  (vacío)"

    echo ""
}

# ═══════════════════════════════════════════════════════════════
# PAYMENT FUNCTIONS
# ═══════════════════════════════════════════════════════════════

# Registrar pago a influencer
payment_add() {
    local username="$1"
    local amount="$2"
    local description="${3:-Post promocional}"
    local method="${4:-paypal}"

    init_db

    local payment=$(cat <<EOF
{
    "id": "PAY-$(date +%s)",
    "influencer": "$username",
    "amount": $amount,
    "description": "$description",
    "method": "$method",
    "status": "pending",
    "date": "$(date -Iseconds)"
}
EOF
)

    # Agregar pago
    local tmp=$(mktemp)
    jq ".payments += [$payment]" "$PATRU_DB" > "$tmp" && mv "$tmp" "$PATRU_DB"

    # Actualizar total pagado al influencer
    jq "(.influencers[] | select(.username == \"$username\") | .total_paid) += $amount" "$PATRU_DB" > "$tmp" && mv "$tmp" "$PATRU_DB"
    jq "(.influencers[] | select(.username == \"$username\") | .posts_done) += 1" "$PATRU_DB" > "$tmp" && mv "$tmp" "$PATRU_DB"

    log "Pago registrado: @$username - \$$amount"
    echo "  Descripción: $description"
    echo "  Método: $method"
    echo "  ID: PAY-$(date +%s)"
}

# Listar pagos
payment_list() {
    init_db
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  PAYMENT HISTORY${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"

    jq -r '.payments[] | "  \(.id) | @\(.influencer) | $\(.amount) | \(.method) | \(.status)"' "$PATRU_DB" 2>/dev/null || echo "  (sin pagos)"

    local total=$(jq '[.payments[].amount] | add // 0' "$PATRU_DB")
    echo ""
    echo -e "  ${GREEN}Total pagado: \$$total${NC}"
    echo ""
}

# ═══════════════════════════════════════════════════════════════
# CAMPAIGN FUNCTIONS
# ═══════════════════════════════════════════════════════════════

# Crear campaña
campaign_create() {
    local name="$1"
    local budget="$2"
    local target="${3:-engagement}"

    init_db

    local campaign=$(cat <<EOF
{
    "id": "CAMP-$(date +%s)",
    "name": "$name",
    "budget": $budget,
    "spent": 0,
    "target": "$target",
    "status": "active",
    "influencers": [],
    "created": "$(date -Iseconds)"
}
EOF
)

    local tmp=$(mktemp)
    jq ".campaigns += [$campaign]" "$PATRU_DB" > "$tmp" && mv "$tmp" "$PATRU_DB"

    log "Campaña creada: $name"
    echo "  Budget: \$$budget | Target: $target"
}

# ═══════════════════════════════════════════════════════════════
# AI CONTENT GENERATION (via LM Studio)
# ═══════════════════════════════════════════════════════════════

content_generate() {
    local topic="$1"
    local platform="${2:-instagram}"
    local style="${3:-engaging}"

    log "Generando contenido con IA..."

    local prompt="Eres un experto en marketing de influencers para $platform.
Genera 3 ideas de posts sobre: $topic
Estilo: $style
Incluye: caption, hashtags sugeridos, mejor hora para publicar.
Formato: JSON"

    local response=$(curl -s "$LM_STUDIO_URL/chat/completions" \
        -H "Content-Type: application/json" \
        -d "{
            \"model\": \"local-model\",
            \"messages\": [{\"role\": \"user\", \"content\": \"$prompt\"}],
            \"temperature\": 0.8
        }" 2>/dev/null)

    if [[ -n "$response" ]]; then
        echo "$response" | jq -r '.choices[0].message.content' 2>/dev/null || echo "$response"
    else
        warn "LM Studio no disponible. Inicia el servidor en Windows."
    fi
}

# ═══════════════════════════════════════════════════════════════
# ANALYTICS
# ═══════════════════════════════════════════════════════════════

analytics_summary() {
    init_db
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  PATRU ANALYTICS SUMMARY${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"

    local total_influencers=$(jq '.influencers | length' "$PATRU_DB")
    local total_payments=$(jq '[.payments[].amount] | add // 0' "$PATRU_DB")
    local total_posts=$(jq '[.influencers[].posts_done] | add // 0' "$PATRU_DB")
    local active_campaigns=$(jq '[.campaigns[] | select(.status == "active")] | length' "$PATRU_DB")

    echo ""
    echo "  Influencers:      $total_influencers"
    echo "  Total pagado:     \$$total_payments"
    echo "  Posts realizados: $total_posts"
    echo "  Campañas activas: $active_campaigns"
    echo ""

    if [[ $total_posts -gt 0 ]]; then
        local avg_cost=$((total_payments / total_posts))
        echo "  Costo promedio/post: \$$avg_cost"
    fi
    echo ""
}

# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

main() {
    local cmd="$1"
    shift || true

    case "$cmd" in
        # Influencers
        add|influencer-add)
            influencer_add "$@"
            ;;
        list|influencers)
            influencer_list
            ;;

        # Payments
        pay|payment)
            payment_add "$@"
            ;;
        payments)
            payment_list
            ;;

        # Campaigns
        campaign)
            campaign_create "$@"
            ;;

        # Content
        content|generate)
            content_generate "$@"
            ;;

        # Analytics
        stats|analytics)
            analytics_summary
            ;;

        # Help
        help|-h|--help|"")
            show_banner
            echo "Comandos:"
            echo ""
            echo "  ${GREEN}Influencers:${NC}"
            echo "    patru add <@user> [platform] [rate] [category]"
            echo "    patru list"
            echo ""
            echo "  ${GREEN}Pagos:${NC}"
            echo "    patru pay <@user> <amount> [description] [method]"
            echo "    patru payments"
            echo ""
            echo "  ${GREEN}Campañas:${NC}"
            echo "    patru campaign <name> <budget> [target]"
            echo ""
            echo "  ${GREEN}Contenido (IA):${NC}"
            echo "    patru content <topic> [platform] [style]"
            echo ""
            echo "  ${GREEN}Analytics:${NC}"
            echo "    patru stats"
            echo ""
            ;;

        *)
            error "Comando desconocido: $cmd"
            echo "Usa: patru help"
            ;;
    esac
}

main "$@"
