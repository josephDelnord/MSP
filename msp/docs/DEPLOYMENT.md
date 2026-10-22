# Guide de déploiement - MSP

## Prérequis

- Docker 24.0+ et Docker Compose v2
- Make (optionnel mais recommandé)
- 4 GB RAM minimum
- 10 GB d'espace disque

## Déploiement en développement (local)

### Méthode 1: Avec Make (recommandé)

```bash
# Cloner le projet
cd /home/josephneo/biba

# Installation complète
make install

# Ou étape par étape:
make up          # Démarrer les services
make status      # Vérifier le statut
make health      # Vérifier la santé
```

### Méthode 2: Avec Docker Compose directement

```bash
cd /home/josephneo/biba

# Démarrer tous les services
docker compose up -d

# Voir les logs
docker compose logs -f

# Arrêter
docker compose down
```

### Méthode 3: Avec le script de déploiement

```bash
./scripts/deploy.sh dev
```

## Accès à l'application

| Service | URL | Identifiants |
|---------|-----|-------------|
| Application Web | http://localhost:3000 | admin / admin |
| API Backend | http://localhost:8000 | - |
| Documentation API | http://localhost:8000/docs | - |
| PostgreSQL | localhost:5432 | msp / msp_password |
| Redis | localhost:6379 | - |

## Déploiement en production

### 1. Générer les secrets

```bash
./scripts/generate-secrets.sh
# Crée le fichier .env.prod avec des secrets aléatoires
```

### 2. Configurer les variables

Éditer `.env.prod`:
```bash
# Domaine
CORS_ORIGINS=["https://msp.votredomaine.com"]
VITE_API_URL=https://api.msp.votredomaine.com
GRAFANA_ROOT_URL=https://grafana.msp.votredomaine.com

# Modifier les mots de passe générés si nécessaire
```

### 3. Configurer SSL (Let's Encrypt)

```bash
# Installer certbot
sudo apt install certbot

# Générer les certificats
sudo certbot certonly --standalone -d msp.votredomaine.com -d api.msp.votredomaine.com

# Copier les certificats
sudo mkdir -p docker/nginx/ssl
sudo cp /etc/letsencrypt/live/msp.votredomaine.com/fullchain.pem docker/nginx/ssl/
sudo cp /etc/letsencrypt/live/msp.votredomaine.com/privkey.pem docker/nginx/ssl/
```

### 4. Déployer

```bash
./scripts/deploy.sh prod
```

### 5. Vérifier

```bash
./scripts/health-check.sh --verbose
```

## Commandes utiles

### Gestion des services

```bash
make up              # Démarrer
make down            # Arrêter
make restart         # Redémarrer
make logs            # Voir tous les logs
make logs-backend    # Logs backend uniquement
make logs-frontend   # Logs frontend uniquement
make status          # Statut des conteneurs
make health          # Santé de l'API
make health-all      # Santé de tous les services
```

### Base de données

```bash
make shell-db        # Shell PostgreSQL
make backup          # Sauvegarder la BDD
make restore FILE=backups/msp_backup_20240101_120000.sql.gz
make seed            # Réinsérer les données de démo
./scripts/init-db.sh --reset   # Réinitialiser complètement
```

### Développement

```bash
make dev-backend     # Backend local (sans Docker)
make dev-frontend    # Frontend local (sans Docker)
make dev-db          # Uniquement PostgreSQL + Redis

# Shell dans les conteneurs
make shell-backend
make shell-frontend
make shell-db
```

### Nettoyage

```bash
make clean           # Nettoyer les ressources inutilisées
make clean-all       # Nettoyage complet (⚠️ supprime tout)
make down-volumes    # Arrêter + supprimer les volumes (⚠️ données perdues)
```

## Scripts disponibles

| Script | Description |
|--------|-------------|
| `scripts/deploy.sh [dev\|prod\|test]` | Déploiement rapide |
| `scripts/health-check.sh [--verbose]` | Vérification de santé complète |
| `scripts/backup.sh [nom]` | Sauvegarde de la base de données |
| `scripts/restore.sh <fichier>` | Restauration de la base de données |
| `scripts/init-db.sh [--reset]` | Initialisation de la base de données |
| `scripts/generate-secrets.sh` | Génération de secrets sécurisés |

## Dépannage

### Le frontend ne démarre pas

```bash
# Vérifier les logs
docker logs msp-frontend

# Reconstruire l'image
docker compose up -d --build frontend
```

### Le backend ne démarre pas

```bash
# Vérifier les logs
docker logs msp-backend

# Vérifier la connexion PostgreSQL
docker compose exec postgres pg_isready -U msp
```

### Problème de connexion à un routeur

```bash
# Tester la connectivité réseau
ping 192.168.88.1

# Tester le port API
nc -zv 192.168.88.1 8728

# Tester SSH
ssh admin@192.168.88.1
```

### Réinitialiser complètement

```bash
# Arrêter et supprimer tout
make down-volumes

# Nettoyer Docker
docker system prune -af --volumes

# Redéployer
docker compose up -d --build
```

## Mise à jour

```bash
# Arrêter les services
make down

# Mettre à jour le code (git pull, etc.)

# Reconstruire et redémarrer
make up-build

# Vérifier
make health-all
```

## Sauvegarde et restauration

### Sauvegarde manuelle

```bash
# Via le script
./scripts/backup.sh ma-sauvegarde

# Via make
make backup

# Via Docker directement
docker compose exec postgres pg_dump -U msp msp_db > backup.sql
```

### Restauration

```bash
# Via le script
./scripts/restore.sh backups/ma-sauvegarde.sql.gz

# Via make
make restore FILE=backups/ma-sauvegarde.sql.gz

# Via Docker directement
docker compose exec -T postgres psql -U msp -d msp_db < backup.sql
```

### Sauvegarde automatique (cron)

```bash
# Ajouter une tâche cron pour sauvegarder tous les jours à 2h
crontab -e

# Ajouter cette ligne:
0 2 * * * /home/josephneo/biba/scripts/backup.sh >> /var/log/msp-backup.log 2>&1
```
