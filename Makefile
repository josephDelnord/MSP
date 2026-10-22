# ============================================================
# MSP - Mikrotik Provisioning Manager
# Makefile pour la gestion du projet en local avec Docker
# ============================================================

.PHONY: help up down restart logs build clean dev prod test backup restore shell-backend shell-frontend shell-db migrate seed status health

# Couleurs pour l'affichage
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Fichier docker-compose
COMPOSE_FILE := docker-compose.yml
COMPOSE := docker compose -f $(COMPOSE_FILE)

# ============================================================
# Aide
# ============================================================
help: ## Afficher cette aide
	@echo "$(BLUE)MSP - Mikrotik Provisioning Manager$(NC)"
	@echo ""
	@echo "$(GREEN)Commandes disponibles:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'

# ============================================================
# Gestion des conteneurs
# ============================================================
up: ## Démarrer tous les services (mode développement)
	@echo "$(BLUE)Démarrage de tous les services...$(NC)"
	$(COMPOSE) up -d
	@echo "$(GREEN)Services démarrés!$(NC)"
	@echo "  Frontend:  http://localhost:3000"
	@echo "  Backend:   http://localhost:8000"
	@echo "  API Docs:  http://localhost:8000/docs"
	@echo "  PostgreSQL: localhost:5432"
	@echo "  Redis:     localhost:6379"

up-build: ## Démarrer tous les services avec rebuild des images
	@echo "$(BLUE)Démarrage avec rebuild des images...$(NC)"
	$(COMPOSE) up -d --build

up-logs: ## Démarrer et suivre les logs
	$(COMPOSE) up

down: ## Arrêter tous les services
	@echo "$(YELLOW)Arrêt des services...$(NC)"
	$(COMPOSE) down

down-volumes: ## Arrêter les services et supprimer les volumes (⚠️ données perdues)
	@echo "$(RED)Arrêt avec suppression des volumes...$(NC)"
	$(COMPOSE) down -v

restart: ## Redémarrer tous les services
	@echo "$(BLUE)Redémarrage des services...$(NC)"
	$(COMPOSE) restart

restart-backend: ## Redémarrer uniquement le backend
	$(COMPOSE) restart backend

restart-frontend: ## Redémarrer uniquement le frontend
	$(COMPOSE) restart frontend

# ============================================================
# Logs
# ============================================================
logs: ## Afficher les logs de tous les services
	$(COMPOSE) logs -f

logs-backend: ## Afficher les logs du backend
	$(COMPOSE) logs -f backend

logs-frontend: ## Afficher les logs du frontend
	$(COMPOSE) logs -f frontend

logs-db: ## Afficher les logs de PostgreSQL
	$(COMPOSE) logs -f postgres

# ============================================================
# Build
# ============================================================
build: ## Builder toutes les images Docker
	@echo "$(BLUE)Build des images...$(NC)"
	$(COMPOSE) build

build-backend: ## Builder l'image du backend
	$(COMPOSE) build backend

build-frontend: ## Builder l'image du frontend
	$(COMPOSE) build frontend

build-no-cache: ## Builder les images sans cache
	$(COMPOSE) build --no-cache

# ============================================================
# Nettoyage
# ============================================================
clean: ## Nettoyer les conteneurs, images et volumes non utilisés
	@echo "$(YELLOW)Nettoyage Docker...$(NC)"
	docker system prune -f
	$(COMPOSE) down --rmi local -v --remove-orphans 2>/dev/null || true

clean-all: ## Nettoyage complet (⚠️ supprime tout)
	@echo "$(RED)Nettoyage complet...$(NC)"
	$(COMPOSE) down -v --rmi all --remove-orphans 2>/dev/null || true
	docker system prune -af --volumes

# ============================================================
# Développement local (sans Docker pour le dev frontend/backend)
# ============================================================
dev-backend: ## Lancer le backend en local (sans Docker)
	@echo "$(BLUE)Lancement du backend en local...$(NC)"
	cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Lancer le frontend en local (sans Docker)
	@echo "$(BLUE)Lancement du frontend en local...$(NC)"
	cd frontend && npm install && npm run dev

dev-db: ## Lancer uniquement PostgreSQL et Redis
	$(COMPOSE) up -d postgres redis

# ============================================================
# Production
# ============================================================
prod: ## Démarrer en mode production (build optimisé)
	@echo "$(BLUE)Démarrage en mode production...$(NC)"
	$(COMPOSE) -f $(COMPOSE_FILE) -f docker-compose.prod.yml up -d --build

# ============================================================
# Tests
# ============================================================
test: ## Lancer les tests
	@echo "$(BLUE)Lancement des tests...$(NC)"
	$(COMPOSE) exec backend pytest -v || echo "$(YELLOW)Tests backend non configurés$(NC)"

test-backend: ## Tests du backend uniquement
	$(COMPOSE) exec backend pytest -v

# ============================================================
# Base de données
# ============================================================
shell-db: ## Ouvrir un shell PostgreSQL
	$(COMPOSE) exec postgres psql -U msp -d msp_db

migrate: ## Appliquer les migrations Alembic (si configuré)
	$(COMPOSE) exec backend alembic upgrade head || echo "$(YELLOW)Migrations non configurées$(NC)"

seed: ## Insérer les données de démonstration
	@echo "$(BLUE)Insertion des données de démo...$(NC)"
	$(COMPOSE) exec backend python -c "from app.main import _seed_sample_data; from app.core.database import SessionLocal; db = SessionLocal(); _seed_sample_data(db); db.close(); print('Données insérées')"

backup: ## Sauvegarder la base de données
	@echo "$(BLUE)Sauvegarde de la base de données...$(NC)"
	@mkdir -p backups
	$(COMPOSE) exec -T postgres pg_dump -U msp msp_db > backups/msp_backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)Sauvegarde créée dans backups/$(NC)"

restore: ## Restaurer la base de données (usage: make restore FILE=backup.sql)
	@echo "$(YELLOW)Restauration de la base de données...$(NC)"
	$(COMPOSE) exec -T postgres psql -U msp -d msp_db < $(FILE)

# ============================================================
# Shells
# ============================================================
shell-backend: ## Ouvrir un shell dans le conteneur backend
	$(COMPOSE) exec backend /bin/sh

shell-frontend: ## Ouvrir un shell dans le conteneur frontend
	$(COMPOSE) exec frontend /bin/sh

shell-db: ## Ouvrir un shell dans le conteneur PostgreSQL
	$(COMPOSE) exec postgres /bin/sh

# ============================================================
# Statut et santé
# ============================================================
status: ## Afficher le statut des conteneurs
	@echo "$(BLUE)Statut des services:$(NC)"
	$(COMPOSE) ps

health: ## Vérifier la santé de l'API
	@echo "$(BLUE)Vérification de la santé de l'API...$(NC)"
	@curl -s http://localhost:8000/health | python3 -m json.tool || echo "$(RED)API non disponible$(NC)"

health-all: ## Vérifier la santé de tous les services
	@echo "$(BLUE)=== Backend ===$(NC)"
	@curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || echo "$(RED)Non disponible$(NC)"
	@echo "$(BLUE)=== Frontend ===$(NC)"
	@curl -s -o /dev/null -w "HTTP %{http_code}" http://localhost:3000 || echo "$(RED)Non disponible$(NC)"
	@echo ""
	@echo "$(BLUE)=== PostgreSQL ===$(NC)"
	$(COMPOSE) exec postgres pg_isready -U msp || echo "$(RED)Non disponible$(NC)"
	@echo "$(BLUE)=== Redis ===$(NC)"
	$(COMPOSE) exec redis redis-cli ping || echo "$(RED)Non disponible$(NC)"

# ============================================================
# Installation initiale
# ============================================================
install: ## Installation initiale du projet
	@echo "$(BLUE)Installation initiale de MSP...$(NC)"
	@cp -n backend/.env.example backend/.env 2>/dev/null || true
	@echo "$(GREEN)Construction et démarrage des services...$(NC)"
	$(COMPOSE) up -d --build
	@echo ""
	@echo "$(GREEN)Installation terminée!$(NC)"
	@echo "  Accédez à l'application: http://localhost:3000"
	@echo "  Identifiants par défaut: admin / admin"

# ============================================================
# Default
# ============================================================
.DEFAULT_GOAL := help
