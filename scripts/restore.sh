#!/bin/bash
# ============================================================
# MSP - Script de restauration de la base de données
# Usage: ./scripts/restore.sh <fichier_backup.sql[.gz]>
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [ $# -lt 1 ]; then
    echo -e "${RED}Usage: $0 <fichier_backup.sql[.gz]> comedor${NC}"
    echo "Backups disponibles:"
    ls -lh "${PROJECT_DIR}/backups/"*.sql* 2>/dev/null || echo "  Aucun backup trouvé"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}Erreur: Le fichier ${BACKUP_FILE} n'existe pas${NC}"
    exit 1
fi

echo -e "${YELLOW}=== MSP - Restauration de la base de données ===${NC}"
echo -e "${YELLOW}ATTENTION: Cette opération va écraser la base de données actuelle!${NC}"
read -p "Êtes-vous sûr? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Restauration annulée."
    exit 0
fi

# Vérifier que PostgreSQL est en cours d'exécution
if ! docker ps --format '{{.Names}}' | grep -q '^msp-postgres'; then
    echo -e "${RED}Erreur: Le conteneur msp-postgres n'est pas en cours d'exécution${NC}"
    exit 1
fi

echo "Restauration en cours depuis: ${BACKUP_FILE}"

# Décompresser si nécessaire
if [[ "$BACKUP_FILE" == *.gz ]]; then
    TEMP_FILE=$(mktemp)
    gunzip -c "$BACKUP_FILE" > "$TEMP_FILE"
    BACKUP_FILE="$TEMP_FILE"
    CLEANUP_TEMP=true
else
    CLEANUP_TEMP=false
fi

# Restaurer
docker compose -f "${PROJECT_DIR}/docker-compose.yml" exec -T postgres \
    psql -U msp -d msp_db < "$BACKUP_FILE"

# Nettoyer le fichier temporaire
if [ "$CLEANUP_TEMP" = true ]; then
    rm -f "$BACKUP_FILE"
fi

echo -e "${GREEN}Restauration terminée avec succès!${NC}"
