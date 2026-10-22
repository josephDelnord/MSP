#!/bin/bash
# ============================================================
# MSP - Script d'initialisation de la base de données
# Usage: ./scripts/init-db.sh [--reset]
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

RESET=false
if [ "${1:-}" = "--reset" ]; then
    RESET=true
fi

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== MSP - Initialisation de la base de données ===${NC}"

# Vérifier que PostgreSQL est en cours d'exécution
if ! docker ps --format '{{.Names}}' | grep -q '^msp-postgres'; then
    echo -e "${YELLOW}Démarrage de PostgreSQL...${NC}"
    docker compose -f "${PROJECT_DIR}/docker-compose.yml" up -d postgres
    echo "Attente du démarrage de PostgreSQL..."
    sleep 5
fi

echo "PostgreSQL est prêt."

if [ "$RESET" = true ]; then
    echo -e "${YELLOW}Mode RESET: suppression des données existantes...${NC}"
    docker compose -f "${PROJECT_DIR}/docker-compose.yml" exec -T postgres \
        psql -U msp -d msp_db -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO msp; GRANT ALL ON SCHEMA public TO public;"
    echo -e "${GREEN}Base de données réinitialisée.${NC}"
fi

# Créer les tables et insérer les données de démo via le backend
echo "Création des tables et insertion des données..."
docker compose -f "${PROJECT_DIR}/docker-compose.yml" exec -T backend \
    python -c "
from app.core.database import engine, Base, SessionLocal
from app.models.models import *
from app.main import _create_default_admin, _seed_sample_data

print('Création des tables...')
Base.metadata.create_all(bind=engine)

db = SessionLocal()
_create_default_admin(db)
_seed_sample_data(db)
db.close()
print('Initialisation terminée!')
"

echo -e "${GREEN}Base de données initialisée avec succès!${NC}"
echo ""
echo "Données créées:"
echo "  - Utilisateur admin (admin/admin)"
echo "  - 3 templates (hAP ac², hAP ax², Chateau LTE12)"
echo "  - 1 client de démo"
echo "  - 1 site de démo"
echo "  - 3 routeurs de démo"
