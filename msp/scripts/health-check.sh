#!/bin/bash
# ============================================================
# MSP - Script de vérification de santé
# Usage: ./scripts/health-check.sh [--verbose]
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

VERBOSE=false
if [ "${1:-}" = "--verbose" ] || [ "${1:-}" = "-v" ]; then
    VERBOSE=true
fi

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

ERRORS=0
WARNINGS=0

print_status() {
    local status=$1
    local message=$2
    case $status in
        "OK")    echo -e "  ${GREEN}[OK]${NC} $message" ;;
        "WARN")  echo -e "  ${YELLOW}[WARN]${NC} $message"; WARNINGS=$((WARNINGS + 1)) ;;
        "ERROR") echo -e "  ${RED}[ERROR]${NC} $message"; ERRORS=$((ERRORS + 1)) ;;
        "INFO")  echo -e "  ${BLUE}[INFO]${NC} $message" ;;
    esac
}

echo -e "${BLUE}=== MSP - Vérification de santé ===${NC}"
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 1. Vérifier Docker
echo -e "${BLUE}1. Docker${NC}"
if command -v docker &> /dev/null; then
    print_status "OK" "Docker installé: $(docker --version)"
else
    print_status "ERROR" "Docker non installé"
fi

if command -v docker compose &> /dev/null; then
    print_status "OK" "Docker Compose installé: $(docker compose version)"
else
    print_status "ERROR" "Docker Compose non installé"
fi
echo ""

# 2. Vérifier les conteneurs
echo -e "${BLUE}2. Conteneurs${NC}"
for container in msp-postgres msp-redis msp-backend msp-frontend; do
    if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        STATUS=$(docker inspect --format='{{.State.Status}}' "$container" 2>/dev/null)
        HEALTH=$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}N/A{{end}}' "$container" 2>/dev/null)
        print_status "OK" "$container: $STATUS (health: $HEALTH)"
    else
        print_status "ERROR" "$container: non trouvé"
    fi
done
echo ""

# 3. Vérifier les services
echo -e "${BLUE}3. Services${NC}"

# Backend API
if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    HEALTH=$(curl -s http://localhost:8000/health)
    print_status "OK" "Backend API: $HEALTH"
else
    print_status "ERROR" "Backend API: non disponible (http://localhost:8000/health)"
fi

# Frontend
HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:3000 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    print_status "OK" "Frontend: HTTP $HTTP_CODE"
else
    print_status "ERROR" "Frontend: HTTP $HTTP_CODE (attendu: 200)"
fi

# PostgreSQL
if docker compose -f "${PROJECT_DIR}/docker-compose.yml" exec -T postgres pg_isready -U msp &> /dev/null; then
    print_status "OK" "PostgreSQL: disponible"
else
    print_status "ERROR" "PostgreSQL: non disponible"
fi

# Redis
if docker compose -f "${PROJECT_DIR}/docker-compose.yml" exec -T redis redis-cli ping &> /dev/null; then
    print_status "OK" "Redis: PONG"
else
    print_status "ERROR" "Redis: non disponible"
fi
echo ""

# 4. Vérifier l'API (si token disponible)
echo -e "${BLUE}4. API${NC}"
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/token \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=admin&password=admin" 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null || echo "")

if [ -n "$TOKEN" ]; then
    print_status "OK" "Authentification: token obtenu"

    # Test dashboard stats
    STATS=$(curl -s http://localhost:8000/api/dashboard/stats -H "Authorization: Bearer $TOKEN" 2>/dev/null)
    if [ -n "$STATS" ]; then
        ROUTERS=$(echo "$STATS" | python3 -c "import sys,json; print(json.load(sys.stdin).get('total_routers','?'))" 2>/dev/null || echo "?")
        print_status "OK" "Dashboard: $ROUTERS routeurs"
    else
        print_status "WARN" "Dashboard: données non disponibles"
    fi
else
    print_status "ERROR" "Authentification: échec"
fi
echo ""

# 5. Espace disque
echo -e "${BLUE}5. Espace disque${NC}"
DISK_USAGE=$(df -h "$PROJECT_DIR" | tail -1 | awk '{print $5}')
DISK_AVAIL=$(df -h "$PROJECT_DIR" | tail -1 | awk '{print $4}')
if [ "${DISK_USAGE%?}" -lt 80 ]; then
    print_status "OK" "Espace disque: $DISK_USAGE utilisé ($DISK_AVAIL disponible)"
else
    print_status "WARN" "Espace disque: $DISK_USAGE utilisé ($DISK_AVAIL disponible)"
fi

# Docker disk usage
DOCKER_DISK=$(docker system df --format "{{.Type}}: {{.Size}}" 2>/dev/null | tr '\n' ' ')
if [ "$VERBOSE" = true ]; then
    print_status "INFO" "Docker: $DOCKER_DISK"
fi
echo ""

# Résumé
echo -e "${BLUE}=== Résumé ===${NC}"
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}Tous les contrôles sont passés!${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}$WARNINGS avertissement(s), 0 erreur${NC}"
    exit 0
else
    echo -e "${RED}$ERRORS erreur(s), $WARNINGS avertissement(s)${NC}"
    exit 1
fi
