# Documentation API REST - MSP

Base URL: `http://localhost:8000`

Documentation interactive (Swagger): `http://localhost:8000/docs`
Documentation alternative (ReDoc): `http://localhost:8000/redoc`

## Authentification

Toutes les routes (sauf `/health` et `/api/auth/token`) nécessitent un token JWT.

### Obtenir un token

```http
POST /api/auth/token
Content-Type: application/x-www-form-urlencoded

username=admin&password=admin
```

**Réponse:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

### Utiliser le token

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

---

## Endpoints

### Système

| Méthode | Endpoint | Description | Auth |
|---------|----------|-------------|------|
| GET | `/health` | Health check | Non |
| GET | `/api/system/info` | Informations système | Oui |

### Authentification

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/auth/token` | Login (obtenir token JWT) |
| GET | `/api/auth/me` | Informations utilisateur connecté |
| POST | `/api/auth/register` | Créer un utilisateur |

### Dashboard

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/dashboard/stats` | Statistiques globales |
| GET | `/api/dashboard/routers-status` | Résumé état routeurs |

**Exemple - Stats:**
```json
{
  "total_routers": 10,
  "online_routers": 8,
  "offline_routers": 2,
  "non_compliant_routers": 3,
  "error_routers": 0,
  "outdated_routers": 2,
  "active_alerts": 5,
  "critical_alerts": 2
}
```

### Routeurs

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/routers` | Liste des routeurs (filtres: status, client_id) |
| POST | `/api/routers` | Créer un routeur |
| GET | `/api/routers/{id}` | Détails d'un routeur |
| PUT | `/api/routers/{id}` | Modifier un routeur |
| DELETE | `/api/routers/{id}` | Supprimer un routeur |
| POST | `/api/routers/discover` | Découverte automatique |
| POST | `/api/routers/{id}/provision` | Provisionner un routeur |
| POST | `/api/routers/{id}/update` | Mise à jour firmware |
| GET | `/api/routers/{id}/updates` | Historique mises à jour |

**Découverte:**
```http
POST /api/routers/discover
Content-Type: application/json

{
  "ip_address": "192.168.88.1",
  "username": "admin",
  "password": "",
  "api_port": 8728
}
```

**Provisionnement:**
```http
POST /api/routers/{id}/provision
Content-Type: application/json

{
  "ssid_2ghz": "MonWiFi-2.4",
  "ssid_5ghz": "MonWiFi-5",
  "pppoe_login": "client@isp.fr",
  "pppoe_password": "secret",
  "wifi_key": "password123"
}
```

### Audits

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/audits` | Lancer un audit |
| GET | `/api/audits` | Liste des audits (filtre: router_id) |
| GET | `/api/audits/{id}` | Détails d'un audit |
| GET | `/api/routers/{id}/audits` | Audits d'un routeur |

**Lancer un audit:**
```http
POST /api/audits
Content-Type: application/json

{
  "router_id": "uuid-du-routeur",
  "remediation_mode": "audit_and_purpose"
}
```

**Modes de remédiation:**
- `audit_only` - Audit seul
- `audit_and_purpose` - Audit + proposition de correction
- `audit_and_fix` - Audit + correction automatique + revalidation

### Alertes

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/alerts` | Liste des alertes (filtres: status, severity, router_id) |
| POST | `/api/alerts` | Créer une alerte |
| POST | `/api/alerts/{id}/resolve` | Résoudre une alerte |
| POST | `/api/alerts/{id}/acknowledge` | Acquitter une alerte |
| POST | `/api/alerts/{id}/notify` | Envoyer notification |

### Templates

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/templates` | Liste des templates |
| POST | `/api/templates` | Créer un template |
| GET | `/api/templates/{id}` | Détails d'un template |
| PUT | `/api/templates/{id}` | Modifier un template |
| DELETE | `/api/templates/{id}` | Supprimer un template |

### Clients

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/clients` | Liste des clients |
| POST | `/api/clients` | Créer un client |
| GET | `/api/clients/{id}` | Détails d'un client |
| PUT | `/api/clients/{id}` | Modifier un client |

### Sites

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/sites` | Liste des sites (filtre: client_id) |
| POST | `/api/sites` | Créer un site |
| GET | `/api/sites/{id}` | Détails d'un site |

---

## Codes de statut HTTP

| Code | Signification |
|------|---------------|
| 200 | Succès |
| 201 | Créé |
| 400 | Requête invalide |
| 401 | Non authentifié |
| 403 | Non autorisé |
| 404 | Ressource non trouvée |
| 422 | Erreur de validation |
| 500 | Erreur serveur |

## Intégration CRM / ITSM

L'API REST permet l'intégration avec les systèmes externes:

### Synchronisation client

```http
POST /api/clients
Content-Type: application/json

{
  "name": "Client XYZ",
  "reference_crm": "CRM-12345",
  "contact_email": "contact@client.fr",
  "contact_phone": "+33123456789",
  "address": "123 Rue Example, Paris"
}
```

### Liaison routeur/client

```http
PUT /api/routers/{id}
Content-Type: application/json

{
  "client_id": "uuid-du-client",
  "site_id": "uuid-du-site"
}
```

### Création de ticket (via alerte)

```http
POST /api/alerts
Content-Type: application/json

{
  "router_id": "uuid-du-routeur",
  "severity": "critical",
  "title": "WAN indisponible",
  "description": "Le routeur mikrotik-paris-01 a perdu sa connexion WAN",
  "category": "network"
}
```

### Webhook de notification

```http
POST /api/alerts/{id}/notify
Content-Type: application/json

["webhook", "email", "teams"]
```

## Exemples cURL

### Workflow complet

```bash
# 1. Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin" | jq -r '.access_token')

# 2. Découvrir un routeur
curl -X POST http://localhost:8000/api/routers/discover \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ip_address": "192.168.88.1", "username": "admin", "password": ""}'

# 3. Lancer un audit
curl -X POST http://localhost:8000/api/audits \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"router_id": "UUID", "remediation_mode": "audit_and_fix"}'

# 4. Vérifier le statut
curl http://localhost:8000/api/routers/UUID \
  -H "Authorization: Bearer $TOKEN"

# 5. Voir les alertes
curl http://localhost:8000/api/alerts?status=active \
  -H "Authorization: Bearer $TOKEN"
```
