# Guide de sécurité - MSP

## Vue d'ensemble

Ce document décrit les mesures de sécurité implémentées dans MSP et les bonnes pratiques recommandées.

## Authentification et autorisation

### Authentification JWT

- Tokens JWT signés avec HS256
- Durée de validité: 480 minutes (8 heures) par défaut
- Stockage du token côté client (localStorage)

### RBAC (Role-Based Access Control)

| Rôle | Permissions |
|------|-------------|
| `admin` | Accès complet (CRUD + configuration) |
| `operator` | Lecture + actions (audit, provisioning, résolution alertes) |
| `viewer` | Lecture seule |

### Microsoft Entra ID (production)

En production, l'authentification peut être déléguée à Microsoft Entra ID (Azure AD) via OAuth2/OIDC.

## Sécurité réseau

### Firewall Nginx (production)

```nginx
# Rate limiting
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;

# Bloquer les fichiers sensibles
location ~ /\. { deny all; }
location ~* \.(env|git|svn|htaccess|htpasswd)$ { deny all; }
```

### Communication Mikrotik

- **API RouterOS**: Port 8728 (ou 8729 pour API-SSL)
- **SSH**: Port 22 (recommandé avec clé plutôt que mot de passe)
- **SNMP v3**: Authentification + chiffrement recommandés

## Gestion des secrets

### Fichiers de secrets

```bash
# Générer des secrets sécurisés
./scripts/generate-secrets.sh

# Le fichier .env.prod est créé avec les permissions 600
# NE JAMAIS commiter ce fichier dans git
```

### Variables sensibles

| Variable | Description | Stockage |
|----------|-------------|----------|
| `SECRET_KEY` | Clé de signature JWT | .env.prod |
| `DB_PASSWORD` | Mot de passe PostgreSQL | .env.prod |
| `REDIS_PASSWORD` | Mot de passe Redis | .env.prod |
| Mots de passe routeurs | Credentials Mikrotik | Base de données (chiffrés en prod) |

### Chiffrement des credentials routeurs (production)

En production, les mots de passe des routeurs doivent être chiffrés au repos:

```python
# Utiliser Fernet (cryptography) ou AWS KMS / HashiCorp Vault
# Jamais de stockage en clair
```

## Base de données

### PostgreSQL

- Connexions chiffrées (SSL) en production
- Utilisateur dédié avec privilèges minimaux
- `pg_hba.conf` restrictif (pas de `trust` en production)

```sql
-- Créer un utilisateur avec privilèges limités
CREATE USER msp_app WITH PASSWORD 'strong_password';
GRANT CONNECT ON DATABASE msp_db TO msp_app;
GRANT USAGE ON SCHEMA public TO msp_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO msp_app;
```

### Redis

- Mot de passe requis (`requirepass`)
- Pas d'exposition publique
- `maxmemory-policy allkeys-lru` pour éviter la saturation

## Conteneurs Docker

### Bonnes pratiques appliquées

```dockerfile
# Utilisateur non-root
RUN groupadd -r msp && useradd -r -g msp msp
USER msp

# Image minimale
FROM python:3.11-slim
FROM node:20-alpine
FROM nginx:alpine

# Pas de secrets dans les images
# Secrets passés via variables d'environnement
```

### Limites de ressources (production)

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 1G
    reservations:
      cpus: '0.25'
      memory: 256M
```

## HTTPS / TLS

### Certificats SSL

```bash
# Let's Encrypt (recommandé)
sudo certbot certonly --standalone -d msp.example.com

# Ou certificats auto-signés pour test
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout docker/nginx/ssl/privkey.pem \
  -out docker/nginx/ssl/fullchain.pem \
  -subj "/CN=msp.example.com"
```

### Configuration Nginx SSL

```nginx
server {
    listen 443 ssl http2;
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
}
```

## Audit et logging

### Logs applicatifs

- Tous les accès API logués
- Erreurs et exceptions tracées
- Logs envoyés à Loki (production)

### Audit de sécurité

- Historique des audits de conformité conservé
- Historique des mises à jour firmware
- Historique des changements de configuration

### Alertes de sécurité

Détection automatique:
- Changement de numéro de série
- Changement de MAC Ether2
- Connexion depuis IP inconnue
- Échec d'authentification répété

## Checklist de déploiement sécurisé

- [ ] Générer des secrets forts (`generate-secrets.sh`)
- [ ] Changer le mot de passe admin par défaut
- [ ] Activer HTTPS (certificats SSL)
- [ ] Configurer le firewall (ports 80/443 uniquement)
- [ ] Restreindre l'accès PostgreSQL (pas d'exposition publique)
- [ ] Activer le mot de passe Redis
- [ ] Configurer les limites de ressources Docker
- [ ] Activer les logs (Loki)
- [ ] Configurer les sauvegardes automatiques
- [ ] Mettre en place le monitoring (Prometheus/Grafana)
- [ ] Documenter les procédures d'incident
- [ ] Tester la restauration depuis backup

## Signalement de vulnérabilités

Pour signaler une vulnérabilité de sécurité, contacter l'équipe sécurité.
