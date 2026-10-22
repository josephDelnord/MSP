# MSP - Mikrotik Provisioning Manager

Plateforme SaaS de gestion centralisée du cycle de vie des routeurs Mikrotik destinée aux MSP, opérateurs télécoms et équipes d'exploitation réseau.

## Fonctionnalités

- **Découverte automatique** des équipements Mikrotik
- **Inventaire** matériel et logiciel
- **Mise à jour automatique** (RouterOS, Firmware, LTE)
- **Provisionnement automatisé** via templates
- **Contrôle de conformité** avec moteur d'audit
- **Auto-remédiation** (3 modes: audit seul, proposition, correction auto)
- **Supervision temps réel** avec dashboard
- **Alerting** multi-canaux (Webex, Teams, Email, Webhook, ITSM)
- **Intégration CRM / ITSM** via API REST

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│   Backend   │────▶│  PostgreSQL │
│ React + MUI │     │   FastAPI   │     │             │
│  TypeScript │     │   Python    │     └─────────────┘
└─────────────┘     └──────┬──────┘
                           │
                    ┌──────┴──────┐
                    ▼             ▼
               ┌─────────┐   ┌─────────┐
               │  Redis  │   │Mikrotik │
               │  Cache  │   │ RouterOS│
               └─────────┘   │  API/SSH│
                             └─────────┘
```

## Démarrage rapide

### Prérequis

- Docker et Docker Compose
- Make (optionnel mais recommandé)

### Installation

```bash
# Cloner le projet
cd biba

# Démarrer tous les services
make up
# ou sans make:
docker compose up -d --build
```

### Accès

| Service | URL | Identifiants |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | admin / admin |
| Backend API | http://localhost:8000 | - |
| API Docs (Swagger) | http://localhost:8000/docs | - |
| PostgreSQL | localhost:5432 | msp / msp_password |
| Redis | localhost:6379 | - |

## Commandes Make

```bash
make help          # Afficher l'aide
make up            # Démarrer les services
make down          # Arrêter les services
make logs          # Voir les logs
make restart       # Redémarrer
make build         # Builder les images
make clean         # Nettoyer Docker
make status        # Statut des conteneurs
make health        # Vérifier la santé de l'API
make shell-db      # Shell PostgreSQL
make backup        # Sauvegarder la BDD
make seed          # Données de démo
```

## Structure du projet

```
biba/
├── backend/                 # API FastAPI
│   ├── app/
│   │   ├── main.py         # Point d'entrée
│   │   ├── core/           # Config, DB
│   │   ├── models/         # Modèles SQLAlchemy
│   │   ├── schemas/        # Schémas Pydantic
│   │   ├── api/            # Routes API
│   │   └── services/       # Services métier
│   │       ├── mikrotik.py     # Communication Mikrotik
│   │       ├── compliance.py   # Moteur de conformité
│   │       ├── discovery.py    # Découverte & Provisioning
│   │       └── alerts.py       # Alertes & Notifications
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/               # Application React
│   ├── src/
│   │   ├── components/     # Layout
│   │   ├── pages/          # Dashboard, Routers, Audits, etc.
│   │   ├── services/       # API client
│   │   ├── types/          # TypeScript types
│   │   └── context/        # Theme context
│   ├── package.json
│   └── Dockerfile
├── templates/              # Templates Mikrotik
│   ├── template-hap-ac2.rsc
│   ├── template-hap-ac2.yaml
│   ├── template-hap-ax2.rsc
│   ├── template-hap-ax2.yaml
│   ├── template-chateau-lte12.rsc
│   └── template-chateau-lte12.yaml
├── docker/                 # Configs Docker additionnelles
│   ├── docker-compose.prod.yml    # Mode production (nginx, monitoring)
│   ├── docker-compose.override.yml # Overrides dev
│   ├── nginx/              # Reverse proxy + rate limiting
│   ├── postgres/           # Config PostgreSQL
│   ├── prometheus/         # Métriques
│   ├── grafana/            # Dashboards
│   └── loki/               # Logs
├── docs/                   # Documentation
│   ├── PRISE-EN-MAIN.md    # Démarrage + guide des fichiers
│   ├── README.md           # Index de la documentation
│   ├── ARCHITECTURE.md     # Architecture C4, ERD, flux
│   ├── API.md              # Référence API REST
│   ├── DEPLOYMENT.md       # Guide de déploiement
│   ├── TEMPLATES.md        # Documentation des templates
│   └── SECURITY.md         # Sécurité et bonnes pratiques
├── scripts/                # Scripts d'exploitation
│   ├── backup.sh           # Sauvegarde BDD
│   ├── restore.sh          # Restauration BDD
│   ├── health-check.sh     # Vérification santé
│   ├── init-db.sh          # Initialisation BDD
│   ├── generate-secrets.sh # Génération secrets
│   └── deploy.sh           # Déploiement one-command
├── docker-compose.yml      # Orchestration Docker
├── Makefile               # Commandes de gestion
└── README.md
```

## Documentation

| Document | Description |
|----------|-------------|
| [Prise en main](docs/PRISE-EN-MAIN.md) | Démarrage, tour de l'interface, guide des fichiers du dépôt |
| [Architecture](docs/ARCHITECTURE.md) | Diagrammes C4, modèle de données, flux métier |
| [API REST](docs/API.md) | Référence complète des endpoints avec exemples curl |
| [Déploiement](docs/DEPLOYMENT.md) | Guide dev/prod, troubleshooting, cron backup |
| [Templates](docs/TEMPLATES.md) | Format .rsc/.yaml, variables dynamiques |
| [Sécurité](docs/SECURITY.md) | RBAC, SSL, gestion des secrets |

## API REST

Documentation interactive disponible sur http://localhost:8000/docs

### Principaux endpoints

| Méthode | Endpoint | Description |
|---------|----------|-------------|
 POST | `/api/auth/token` | Authentification |
 GET | `/api/dashboard/stats` | Statistiques dashboard |
 GET/POST | `/api/routers` | Liste/Création routeurs |
 POST | `/api/routers/discover` | Découverte automatique |
 POST | `/api/routers/{id}/provision` | Provisionnement |
 POST | `/api/routers/{id}/update` | Mise à jour firmware |
 POST | `/api/audits` | Lancer un audit |
 GET | `/api/audits` | Liste des audits |
 GET/POST | `/api/alerts` | Gestion des alertes |
 GET/POST | `/api/templates` | Gestion des templates |
 GET/POST | `/api/clients` | Gestion des clients |
 GET/POST | `/api/sites` | Gestion des sites |

## Modèles de routeurs supportés

| Modèle | Template | Type |
|--------|----------|------|
| hAP ac² | template-hap-ac2 | WiFi AP |
| hAP ax² | template-hap-ax2 | WiFi 6 AP |
| Chateau LTE12 | template-chateau-lte12 | 4G/LTE Gateway |
| Chateau LTE18 | template-chateau-lte18 | 4G/LTE Gateway |
| RB4011 | template-rb4011 | Routeur rack |
| CCR2004 | template-ccr2004 | Routeur core |

## Variables dynamiques des templates

Les templates supportent les variables suivantes :

- `{{client_id}}` - Identifiant client
- `{{hostname}}` - Nom d'hôte du routeur
- `{{serial_number}}` - Numéro de série
- `{{mac_ether2}}` - MAC du port Ether2
- `{{pppoe_login}}` - Login PPPoE
- `{{pppoe_password}}` - Mot de passe PPPoE
- `{{ssid_2ghz}}` - SSID WiFi 2.4 GHz
- `{{ssid_5ghz}}` - SSID WiFi 5 GHz
- `{{wifi_key}}` - Clé WiFi
- `{{vlan}}` - VLAN
- `{{site}}` - Nom du site
- `{{ip_lan}}` - IP LAN
- `{{ip_wan}}` - IP WAN

## Modes de remédiation

| Mode | Description |
|------|-------------|
| `audit_only` | Audit uniquement, pas de modification |
| `audit_and_purpose` | Audit + proposition de correction |
| `audit_and_fix` | Audit + correction automatique + revalidation |

## Licence

Projet interne - Tous droits réservés
