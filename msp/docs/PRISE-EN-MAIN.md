# Prise en main — MSP

Guide pour démarrer avec la plateforme MSP (Mikrotik Provisioning Manager) en local et comprendre l'organisation du dépôt.

- [Partie 1 — Utiliser la plateforme](#partie-1--utiliser-la-plateforme)
- [Partie 2 — Guide des fichiers du dépôt](#partie-2--guide-des-fichiers-du-dépôt)

---

# Partie 1 — Utiliser la plateforme

## 1. Prérequis

| Logiciel | Pourquoi |
|----------|----------|
| Docker + Docker Compose v2 | Tous les services tournent dans des conteneurs |
| Make | Raccourcis de commande (`make up`, `make down`, ...) |
| Navigateur moderne | Interface web (Chrome, Edge, Firefox) |

Aucune configuration réseau particulière n'est requise : par défaut, le backend fonctionne en **mode simulation** (il génère des données déterministes sans contacter de vrai routeur).

## 2. Premier lancement

```bash
cd biba
make install
```

`make install` copie `backend/.env.example` en `backend/.env`, construit les images et démarre les 4 services :

| Service | Rôle | Port |
|---------|------|------|
| `msp-postgres` | Base de données PostgreSQL 16 | 5432 |
| `msp-redis` | Cache Redis 7 | 6379 |
| `msp-backend` | API FastAPI | 8000 |
| `msp-frontend` | Interface React (Vite) | 3000 |

> **Patience au premier démarrage** : le conteneur frontend installe ses dépendances npm au lancement (~1-2 min). Tant que c'est en cours, http://localhost:3000 peut afficher une erreur de connexion. Rafraîchis la page au bout de 1-2 minutes, ou surveille avec `make logs-frontend` jusqu'à voir `VITE ready`.

Vérifier que tout est vert :

```bash
make health-all    # backend, frontend, postgres, redis
make status        # état des 4 conteneurs
```

## 3. Se connecter

Ouvre http://localhost:3000 — la page de login s'affiche.

| Champ | Valeur par défaut |
|-------|-------------------|
| Nom d'utilisateur | `admin` |
| Mot de passe | `admin` |

Ces identifiants sont affichés en bas de la page de login et créés automatiquement au premier démarrage.

## 4. Tour de l'interface

Après connexion, tu arrives sur le **Dashboard** avec un menu latéral :

| Page | Ce qu'on y fait |
|------|-----------------|
| **Dashboard** | Vue d'ensemble : total routeurs, en ligne, non conformes, alertes actives, routeurs récents |
| **Routeurs** | Inventaire des équipements, découverte automatique, provisioning, mise à jour firmware, lancement d'audits |
| **Audits** | Historique des audits de conformité : score, statut, détail des 39 contrôles, commandes de remédiation |
| **Alertes** | Alertes actives/résolues/critiques, création manuelle, notification multi-canaux |
| **Templates** | Gestion des templates Mikrotik (.rsc) : création, modification, suppression |
| **Clients** | Gestion des clients (nom, référence CRM, contact) |
| **Sites** | Gestion des sites (adresse, ville, VLAN, IP LAN/WAN, client associé) |

Deux fonctions transverses :

- **Mode sombre / clair** : bouton en haut à droite de la barre d-AppBar.
- **Déconnexion** : menu « Compte » (avatar en haut à droite) → Déconnexion.

## 5. Scénarios pas à pas

Les données de démonstration (4 routeurs, 3 templates, 1 client, 2 sites) sont chargées automatiquement au premier démarrage.

### 5.1 Découvrir un routeur

1. Va sur **Routeurs**.
2. Clique sur **Découverte automatique**.
3. Renseigne l'adresse IP, l'identifiant et le mot de passe du routeur (port API par défaut : 8728).
4. Clique sur **Découvrir**.

En mode simulation, la découverte retourne un routeur fictif (hostname, modèle, version RouterOS, MAC, etc.) basé sur l'IP saisie.

### 5.2 Ajouter un routeur manuellement

1. **Routeurs** → **Ajouter un routeur**.
2. Renseigne le hostname, l'IP, les identifiants, et éventuellement les champs WiFi/PPPoE.
3. **Ajouter**.

### 5.3 Lancer un audit de conformité

1. **Routeurs** → clique sur un routeur pour ouvrir le détail.
2. Clique sur **Auditer**.
3. Consulte le résultat dans l'onglet **Audits** du détail, ou sur la page **Audits** : score de conformité (%), statut par contrôle (39 contrôles), explication et commandes de remédiation proposées.

### 5.4 Provisionner un routeur

1. Détail d'un routeur → **Provisionner**.
2. Dans la fenêtre **Lancer le provisioning**, choisis le template (ex. `template-hap-ac2`) et les variables (SSID, clé WiFi, VLAN, IP LAN...).
3. Le provisioning s'exécute en plusieurs étapes (8 étapes en simulation) avec un suivi en direct.

### 5.5 Mettre à jour le firmware

1. Détail d'un routeur → **Mise à jour**.
2. Choisis le type : RouterOS, RouterBOARD ou LTE.
3. L'historique des mises à jour apparaît sur la page du routeur.

### 5.6 Gérer les alertes

- **Alertes** → filtre par statut (**Actives**, **Toutes**, **Critiques**, **Résolues**).
- **Créer une alerte** pour un signalement manuel.
- **Notifier** pour envoyer l'alerte sur les canaux configurés (Webex, Teams, Email, Webhook, ITSM).

## 6. Commandes essentielles

```bash
make up            # Démarrer tous les services (en arrière-plan)
make up-build      # Démarrer avec reconstruction des images
make down          # Arrêter tous les services
make restart       # Redémarrer
make status        # État des conteneurs
make logs          # Logs de tous les services (suivi en direct)
make logs-backend  # Logs d'un seul service
make health-all    # Vérifier la santé de tous les services
make backup        # Sauvegarder la base de données dans backups/
make seed          # Réinsérer les données de démonstration
make help          # Liste complète des commandes
```

Voir le [Makefile](../Makefile) pour la liste exhaustive (shells, tests, restauration, production...).

## 7. Arrêter la plateforme

```bash
make down          # Arrête les conteneurs (les données sont conservées)
make down-volumes  # Arrête ET supprime les données (⚠️ perte des données)
```

Au prochain `make up`, tout repart avec les données existantes.

---

# Partie 2 — Guide des fichiers du dépôt

## Arborescence complète

```
biba/
├── besoin.md                    # Spécification fonctionnelle originale du projet
├── docker-compose.yml           # Orchestration des 4 services (dev)
├── Makefile                     # Commandes de gestion du projet
├── README.md                    # Présentation du projet
├── .gitignore
├── backend/                     # API FastAPI (Python)
│   ├── .env.example             #   Variables d'environnement (modèle)
│   ├── requirements.txt         #   Dépendances Python
│   ├── Dockerfile               #   Image dev (uvicorn --reload)
│   ├── Dockerfile.prod          #   Image prod (multi-stage, gunicorn)
│   └── app/
│       ├── main.py              #   Point d'entrée : routes API (30+ endpoints), seed auto
│       ├── core/
│       │   ├── config.py        #     Configuration (pydantic-settings : BDD, JWT, CORS...)
│       │   └── database.py      #     Moteur SQLAlchemy, SessionLocal, get_db
│       ├── models/models.py     #     8 modèles : User, Client, Site, Router, Template, Audit, Alert, FirmwareUpdate
│       ├── schemas/schemas.py   #     Schémas Pydantic (validation requêtes/réponses)
│       └── services/
│           ├── mikrotik.py      #     Client RouterOS (API/SSH), mode simulation par défaut
│           ├── compliance.py    #     Moteur d'audit : 39 contrôles sur 15 catégories
│           ├── discovery.py     #     Découverte auto + workflow de provisioning
│           └── alerts.py        #     14 types d'alertes + notifications multi-canaux
├── frontend/                    # Interface React + TypeScript + Vite + MUI
│   ├── package.json             #   Dépendances et scripts npm
│   ├── vite.config.ts           #   Serveur dev (port 3000) + proxy /api → backend:8000
│   ├── index.html               #   Page HTML racine
│   ├── tsconfig.json            #   Config TypeScript (app)
│   ├── tsconfig.node.json       #   Config TypeScript (outils)
│   ├── Dockerfile               #   Image dev (npm install + npm run dev au démarrage)
│   ├── Dockerfile.prod          #   Image prod (multi-stage, build + nginx)
│   ├── docker/nginx/frontend.conf  # Config nginx de l'image prod
│   └── src/
│       ├── main.tsx             #   Point d'entrée React
│       ├── App.tsx              #   Routes + garde ProtectedRoute (token requis)
│       ├── components/Layout.tsx    #   Drawer, AppBar, menu, profil utilisateur
│       ├── context/ThemeContext.tsx #   Thème clair/sombre
│       ├── services/api.ts      #   Client Axios : baseURL /api, intercepteurs JWT/401
│       ├── types/index.ts       #   Interfaces TypeScript
│       └── pages/               #   8 pages : Login, Dashboard, Routers, Audits,
│                                #   Alerts, Templates, Clients, Sites
├── docker/                      # Configurations Docker additionnelles
│   ├── docker-compose.prod.yml  #   Mode production (nginx, Prometheus, Grafana, Loki)
│   ├── docker-compose.override.yml # Overrides dev (auto-fusionné par Compose)
│   ├── nginx/                   #   Reverse proxy : rate limiting, gzip, SSL-ready
│   ├── postgres/                #   postgresql.conf + pg_hba.conf (tuning)
│   ├── prometheus/prometheus.yml    # Métriques
│   ├── grafana/                 #   Datasource + dashboards (msp-overview)
│   └── loki/loki-config.yml     #   Agrégation des logs
├── docs/                        # Documentation
│   ├── PRISE-EN-MAIN.md         #   Ce guide
│   ├── README.md                #   Index de la documentation
│   ├── ARCHITECTURE.md          #   Diagrammes C4, ERD, flux métier
│   ├── API.md                   #   Référence API REST (exemples curl)
│   ├── DEPLOYMENT.md            #   Déploiement dev/prod, troubleshooting
│   ├── TEMPLATES.md             #   Format des templates .rsc/.yaml, variables
│   └── SECURITY.md              #   Sécurité, RBAC, gestion des secrets
├── scripts/                     # Scripts d'exploitation (tous exécutables)
│   ├── deploy.sh                #   Déploiement one-command (dev|prod|test)
│   ├── health-check.sh          #   Vérification santé complète
│   ├── init-db.sh               #   Initialisation BDD + seed (--reset pour repartir à zéro)
│   ├── backup.sh                #   Sauvegarde pg_dump (gzip, rotation 10 fichiers)
│   ├── restore.sh               #   Restauration depuis une sauvegarde
│   └── generate-secrets.sh      #   Génère .env.prod avec secrets aléatoires
└── templates/                   # Templates Mikrotik (paire .rsc + .yaml par modèle)
    ├── template-hap-ac2.rsc / .yaml
    ├── template-hap-ax2.rsc / .yaml
    └── template-chateau-lte12.rsc / .yaml
```

## Fichiers clés à connaître

| Fichier | Quand le modifier |
|---------|-------------------|
| `docker-compose.yml` | Ajouter un service, changer un port, une variable d'environnement |
| `Makefile` | Ajouter une commande de gestion |
| `backend/app/core/config.py` | Changer la config (SECRET_KEY, durée du token, CORS...) |
| `backend/app/main.py` | Ajouter un endpoint API ou modifier le seed |
| `backend/app/services/mikrotik.py` | Connecter de vrais routeurs (passer `simulate=False`) |
| `frontend/vite.config.ts` | Changer le port du dev server ou la cible du proxy |
| `frontend/src/services/api.ts` | Ajouter un appel API côté frontend |
| `templates/*.rsc` | Modifier les scripts de configuration RouterOS |
| `scripts/*.sh` | Adapter les procédures d'exploitation |

## Données et volumes

| Élément | Emplacement | Persistance |
|---------|-------------|-------------|
| Base PostgreSQL | Volume Docker `postgres_data` | Conservée entre les redémarrages, supprimée par `make down-volumes` |
| Cache Redis | Volume Docker `redis_data` | Idem (cache, sans importance) |
| Dépendances frontend | Volume Docker `node_modules` (anonyme) | Réinstallées si le conteneur est recréé sans le volume |
| Sauvegardes BDD | Dossier `backups/` (ignoré par git) | Fichiers `.sql` / `.sql.gz` |

## Prochaines lectures

- [API.md](API.md) — tous les endpoints avec exemples curl
- [ARCHITECTURE.md](ARCHITECTURE.md) — comprendre les entrailles du système
- [DEPLOYMENT.md](DEPLOYMENT.md) — passer en production
- [TEMPLATES.md](TEMPLATES.md) — créer ses propres templates Mikrotik
- [SECURITY.md](SECURITY.md) — durcir l'installation
