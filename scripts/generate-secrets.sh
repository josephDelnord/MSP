#!/bin/bash
# ============================================================
# MSP - Génération de secrets sécurisés
# Usage: ./scripts/generate-secrets.sh [--output .env.prod]
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

OUTPUT_FILE="${PROJECT_DIR}/.env.prod"
if [ "${1:-}" = "--output" ] && [ -n "${2:-}" ]; then
    OUTPUT_FILE="$2"
fi

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== MSP - Génération de secrets sécurisés ===${NC}"

# Fonction de génération de secret
generate_secret() {
    openssl rand -base64 48 | tr -d '/+=' | head -c 64
}

generate_password() {
    openssl rand -base64 24 | tr -d '/+=' | head -c 32
}

# Générer les secrets
SECRET_KEY=$(generate_secret)
DB_PASSWORD=$(generate_password)
REDIS_PASSWORD=$(generate_password)
GRAFANA_PASSWORD=$(generate_password)

# Créer le fichier .env.prod
cat > "$OUTPUT_FILE" << EOF
# ============================================================
# MSP - Configuration Production
# Généré automatiquement le $(date '+%Y-%m-%d %H:%M:%S')
# NE PAS COMMITER CE FICHIER DANS GIT!
# ============================================================

# Application
SECRET_KEY=${SECRET_KEY}
DEBUG=false

# Base de données
DB_USER=msp
DB_PASSWORD=${DB_PASSWORD}
DB_NAME=msp_db

# Redis
REDIS_PASSWORD=${REDIS_PASSWORD}

# CORS
CORS_ORIGINS=["https://msp.example.com"]

# Grafana
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
GRAFANA_ROOT_URL=https://grafana.msp.example.com

# URLs
VITE_API_URL=https://api.msp.example.com
EOF

chmod 600 "$OUTPUT_FILE"

echo -e "${GREEN}Fichier de secrets créé: ${OUTPUT_FILE}${NC}"
echo ""
echo -e "${YELLOW}Secrets générés (à conserver en lieu sûr):${NC}"
echo "  SECRET_KEY:        ${SECRET_KEY:0:20}..."
echo "  DB_PASSWORD:       ${DB_PASSWORD:0:10}..."
echo "  REDIS_PASSWORD:    ${REDIS_PASSWORD:0:10}..."
echo "  GRAFANA_PASSWORD:  ${GRAFANA_PASSWORD:0:10}..."
echo ""
echo -e "${YELLOW}Pour utiliser ces secrets en production:${NC}"
echo "  docker compose -f docker-compose.yml -f docker/docker-compose.prod.yml --env-file ${OUTPUT_FILE} up -d"
echo ""
echo -e "${RED}IMPORTANT: Ce fichier contient des secrets. Ne le partagez pas!${NC}"
