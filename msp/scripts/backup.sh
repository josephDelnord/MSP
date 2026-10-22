#!/bin/bash
# ============================================================
# MSP - Script de sauvegarde de la base de données
# Usage: ./scripts/backup.sh [nom_optionnel]
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${PROJECT_DIR}/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="${1:-msp_backup_${TIMESTAMP}}"
BACKUP_FILE="${BACKUP_DIR}/${BACKUP_NAME}.sql"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}=== MSP - Sauvegarde de la base de données ===${NC}"

# Créer le dossier de backup
mkdir -p "$BACKUP_DIR"

# Vérifier que le conteneur PostgreSQL est en cours d'exécution
if ! docker ps --format '{{.Names}}' | grep -q '^msp-postgres'; then
    echo -e "${RED}Erreur: Le conteneur msp-postgres n'est pas en cours d'exécution${NC}"
    exit 1
fi

echo "Sauvegarde en cours: ${BACKUP_FILE}"

# Effectuer la sauvegarde
docker compose -f "${PROJECT_DIR}/docker-compose.yml" exec -T postgres \
    pg_dump -U msp -d msp_db \
    --clean --if-exists --create \
    --format=plain \
    --no-owner --no-privileges \
    > "$BACKUP_FILE"

# Compresser
 gzip -f "$BACKUP_FILE"
BACKUP_FILE="${BACKUP_FILE}.gz"

# Taille du backup
SIZE=$(du -h "$BACKUP_FILE" | cut -f1)

echo -e "${GREEN}Sauvegarde créée avec succès: ${BACKUP_FILE} (${SIZE})${NC}"

# Nettoyer les backups anciens (garder les 10 derniers)
echo "Nettoyage des anciens backups..."
ls -t "${BACKUP_DIR}"/msp_backup_*.sql.gz 2>/dev/null | tail -n +11 | xargs -r rm -f

echo -e "${GREEN}Terminé!${NC}"
