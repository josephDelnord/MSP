# Mikrotik Provisioning Manager (MSP / Opérateur)

## Objectif

Concevoir une plateforme SaaS de gestion centralisée du cycle de vie des routeurs Mikrotik destinée aux MSP, opérateurs télécoms et équipes d'exploitation réseau.

L'application doit permettre :

- Découverte automatique des équipements
- Inventaire matériel et logiciel
- Mise à jour automatique
- Provisioning automatisé
- Contrôle de conformité
- Auto-remédiation
- Supervision temps réel
- Alerting
- Intégration CRM / ITSM

L'objectif est qu'un technicien branche un routeur Mikrotik neuf ou réinitialisé et que la plateforme réalise automatiquement toutes les opérations nécessaires jusqu'à sa mise en conformité.

---

# 1. Découverte automatique

Lors de la première connexion sur :

```text
192.168.88.1
```

Récupérer automatiquement :

- Modèle exact du routeur
- Référence matérielle
- Numéro de série
- Architecture CPU
- Hostname
- Adresse MAC principale
- Adresse MAC du port Ether2
- Version RouterOS
- Version Firmware RouterBOARD
- Version Firmware LTE si présent

Exemples :

- hAP ac²
- hAP ax²
- Chateau LTE12
- Chateau LTE18
- RB4011
- CCR2004

Toutes les informations doivent être stockées dans l'inventaire central.

---

# 2. Gestion des templates

Le système fonctionne avec un template spécifique à chaque modèle de routeur.

Exemples :

| Modèle | Template |
|----------|----------|
| hAP ac² | template-hap-ac2 |
| hAP ax² | template-hap-ax2 |
| Chateau LTE12 | template-chateau-lte12 |
| RB4011 | template-rb4011 |
| CCR2004 | template-ccr2004 |

Chaque template possède :

- Un fichier `.rsc` utilisé pour le déploiement
- Un fichier YAML utilisé pour les audits de conformité

Exemple :

```text
template-hap-ac2.rsc
template-hap-ac2.yaml
```

Si aucun template n'existe :

- Bloquer le provisioning
- Générer une alerte
- Notifier l'exploitation

---

# 3. Variables dynamiques

Les templates doivent supporter des variables dynamiques :

- client_id
- hostname
- numéro de série
- MAC Ether2
- login PPPoE
- mot de passe PPPoE
- SSID 2.4 GHz
- SSID 5 GHz
- clé WiFi
- VLAN
- site
- référence CRM
- IP LAN
- IP WAN

Le moteur de conformité ne doit jamais effectuer une simple comparaison textuelle brute.

---

# 4. Mise à jour obligatoire

Avant tout provisioning :

Vérifier les versions installées.

Mettre automatiquement à jour vers la dernière version stable disponible :

- RouterOS
- Firmware RouterBOARD
- Firmware LTE

Workflow :

1. Détection
2. Vérification des versions
3. Mise à jour
4. Redémarrage
5. Validation post-mise à jour

Le provisioning est bloqué si une mise à jour échoue.

Historiser :

- Ancienne version
- Nouvelle version
- Date
- Résultat
- Durée

---

# 5. Provisioning automatisé

Importer le template dans la mémoire Flash.

Exécuter :

```routeros
/system reset-configuration run-after-reset=configuration.rsc
```

Après redémarrage :

- Reconnexion automatique
- Reprise de session
- Audit de conformité

---

# 6. Moteur de conformité

Le moteur est basé sur le template correspondant au modèle détecté.

Les vérifications doivent être fonctionnelles et non uniquement textuelles.

---

# 7. Contrôles de conformité

## Versions

Contrôler :

- RouterOS
- Firmware RouterBOARD
- Firmware LTE

Statuts :

- Conforme
- Obsolète
- Échec de mise à jour

---

## Interfaces

Vérifier :

- Bridge
- Ether2
- Interfaces LAN
- Interfaces WAN
- Interfaces LTE

---

## PPPoE

Ne pas vérifier :

- Le nom de l'interface PPPoE
- pppoe-out1
- pppoe-out2
- pppoe-out3
- pppoe-out4

Ces informations sont considérées comme dynamiques.

Vérifier :

- Présence d'une interface PPPoE active
- Une seule interface PPPoE active
- Login PPPoE configuré
- Connexion active
- Adresse IP publique présente
- Route par défaut présente
- Appartenance à la liste WAN
- Connectivité Internet

### Distance PPPoE

La distance de la route associée au PPPoE doit être comprise entre :

```text
1 à 20 inclus
```

Exemples :

```text
1  => Conforme
5  => Conforme
20 => Conforme
25 => Non conforme
```

---

## LTE

Vérifier :

- Modem LTE détecté
- Connexion LTE active
- Route LTE présente

### Distance LTE

Valeur attendue :

```text
21
```

Exemples :

```text
21 => Conforme
20 => Non conforme
22 => Non conforme
```

---

## WAN

Contrôler :

- PPPoE connectée
- Adresse IP publique
- Route par défaut
- Accès Internet
- Résolution DNS

Résultat :

```text
WAN opérationnel
```

ou

```text
WAN indisponible
```

---

## DHCP

Contrôler :

- Serveurs DHCP
- Plages DHCP
- Réseaux DHCP
- Passerelles

---

## DNS

Contrôler :

- allow-remote-requests
- DNS primaire
- DNS secondaire
- Configuration conforme au template

Effectuer des tests réels :

- google.com
- microsoft.com
- webex.com

Résultat :

```text
DNS fonctionnel
```

ou

```text
DNS KO
```

---

## NTP

Contrôler :

- Activation du service
- Serveurs NTP configurés

---

## SNMP

Contrôler :

- Activation du service
- Communities
- Traps

---

## Firewall

Contrôler :

- Présence des règles
- Ordre des règles
- Paramètres
- Protections anti-scan
- Protections DDoS
- Restrictions WAN

---

## NAT

Contrôler :

- Masquerade
- Règles obligatoires

---

## WiFi

Contrôler :

- SSID
- Bande 2.4 GHz
- Bande 5 GHz
- WPA2 / WPA3
- Clés WiFi
- État des interfaces

---

## Utilisateurs

Contrôler :

- Présence des comptes obligatoires
- Groupes associés
- Permissions

Exemples :

- OXIDIZED
- admin-tech

Contrôler également :

```text
Compte admin désactivé
```

---

## Services RouterOS

Contrôler :

- DNS
- SSH
- Winbox
- API
- API SSL
- HTTP
- FTP
- Telnet

Selon les règles du template.

---

## Logging

Contrôler :

- Actions de logs
- Serveurs de collecte
- Intégration Loki / Syslog

---

## Scripts

Contrôler :

- Présence
- Contenu
- Conformité

---

## Scheduler

Contrôler :

- Présence des tâches
- Fréquence
- Paramétrage

---

# 8. Classification des anomalies

Chaque anomalie doit être classifiée :

✅ Conforme

⚠️ Configuration absente

⚠️ Configuration partielle

❌ Mauvaise configuration

Pour chaque anomalie afficher :

- Élément vérifié
- Valeur attendue
- Valeur trouvée
- Criticité
- Explication

---

# 9. Auto-remédiation

Pour chaque anomalie détectée :

- Générer les commandes RouterOS de correction
- Afficher les modifications proposées

Modes :

### Mode 1

Audit uniquement

### Mode 2

Audit + proposition de correction

### Mode 3

Audit + correction automatique

---

# 10. Revalidation obligatoire

Après toute correction :

1. Relancer l'audit complet
2. Vérifier les corrections
3. Recalculer le score de conformité
4. Générer un nouveau rapport

Statuts :

✅ Conforme

⚠️ Conforme avec avertissements

❌ Non conforme

---

# 11. Supervision

Tableau de bord :

- Nombre total de routeurs
- Routeurs en ligne
- Routeurs hors ligne
- Routeurs non conformes
- Routeurs en erreur
- Versions obsolètes

Vue détaillée :

- Informations matérielles
- Numéro de série
- MAC Ether2
- WAN
- LTE
- VPN
- Historique des audits
- Historique des corrections

---

# 12. Alertes

Déclencher une alerte en cas de :

- Routeur inaccessible
- WAN indisponible
- LTE indisponible
- Perte Internet
- Échec de mise à jour RouterOS
- Échec de mise à jour Firmware
- Échec de mise à jour LTE
- Configuration non conforme
- Échec d'auto-remédiation
- Changement de numéro de série
- Changement de MAC Ether2
- Template absent
- Dérive de configuration

Niveaux :

- Information
- Warning
- Critical

---

# 13. Notifications

Canaux supportés :

- Cisco Webex
- Microsoft Teams
- Email
- Webhook
- ServiceNow
- GLPI
- Jira Service Management

Contenu :

- Hostname
- Modèle
- Numéro de série
- MAC Ether2
- Adresse IP
- Site
- Criticité
- Description
- Action recommandée
- Lien vers la plateforme

---

# 14. Intégration CRM / ITSM

API REST permettant :

- Synchronisation des clients
- Synchronisation des sites
- Liaison routeur/client
- Création automatique de tickets
- Consultation des audits
- Consultation des alertes

---

# 15. Architecture Technique

## Frontend

- React
- TypeScript
- Material UI

## Backend

- FastAPI

## Base de données

- PostgreSQL

## Cache

- Redis

## Communication Mikrotik

- RouterOS API
- SSH
- SNMP v3

## Authentification

- Microsoft Entra ID
- RBAC

## Observabilité

- Prometheus
- Grafana
- Loki

## Infrastructure

- Docker
- Kubernetes

## CI/CD

- GitLab CI/CD

---

# 16. Livrables attendus

Produire :

- Architecture détaillée
- Diagrammes C4
- Schéma d'infrastructure
- Modèle SQL
- OpenAPI
- Structure du projet
- Templates YAML
- Moteur de conformité
- Moteur d'auto-remédiation
- Dockerfiles
- Helm Charts
- Pipeline GitLab CI/CD
- Stratégie DevSecOps
- Gestion des secrets
- Audit AppSec
- MVP
- Roadmap V2
- Roadmap V3
- Stratégie de scalabilité
- Documentation d'exploitation