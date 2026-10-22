#!/bin/bash
# ============================================================
# MSP - Script de déploiement rapide
# Usage: ./scripts/deploy.sh [dev|prod]
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

MODE="${1:-dev}"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

cd "$PROJECT_DIR"

case "$MODE" in
    dev|development)
        echo -e "${BLUE}=== MSP - Déploiement en mode DÉVELOPPEMENT ===${NC}"
        echo ""
        echo "Construction et démarrage des services..."
        docker compose up -d --build
        echo ""
        echo -e "${GREEN}Services démarrés en mode développement!${NC}"
        echo ""
        ;;
    prod|production)
        echo -e "${BLUE}=== MSP - Déploiement en mode PRODUCTION ===${NC}"
        echo ""

        # Vérifier que le fichier .env.prod existe
        if [ ! -f "${PROJECT_DIR}/.env.prod" ]; then
            echo -e "${YELLOW}Le fichier .env.prod n'existe pas.${NC}"
            echo "Génération des secrets..."
            bash "${SCRIPT_DIR}/generate-secrets.sh"
        fi

        # Charger les variables d'environnement
        set -a
        source "${PROJECT_DIR}/.env.prod"
        set +a

        echo "Construction et démarrage des services de production..."
        docker compose -f docker-compose.yml -f docker/docker-compose.prod.yml up -d --build
        echo ""
        echo -e "${GREEN}Services démarrés en mode production!${NC}"
        echo ""
        echo "Services disponibles:"
        echo "  - Application:  https://msp.example.com (via Nginx)"
        echo "  - Grafana:      http://localhost:3001"
        echo "  - Prometheus:   http://localhost:9090"
        ;;
    test|testing)
        echo -e "${BLUE}=== MSP - Environnement de TEST ===${NC}"
        echo ""
        docker compose -f docker-compose.yml -f docker/docker-compose.test.yml up -d --build
        echo ""
        echo -e "${GREEN}Services démarrés en mode test!${NC}"
        ;;
    *)
        echo -e "${RED}Usage: $0 [dev|prod|test]${NC}"
        echo "  dev  - Développement local (défaut)"
        echo "  prod - Production avec monitoring"
        echo "  test - Environnement de test"
        exit 1
        ;;
esac

# Afficher le statut
echo "Statut des conteneurs:"
docker compose ps
echo ""

# Vérification de santé
echo "Vérification de santé..."
bash "${SCRIPT_DIR}/health-check.sh"
