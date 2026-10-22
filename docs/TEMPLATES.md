# Documentation des Templates - MSP

## Vue d'ensemble

Les templates définissent la configuration attendue pour chaque modèle de routeur Mikrotik. Chaque template est composé de deux fichiers:

- **`.rsc`** - Script RouterOS pour le provisioning (configuration à appliquer)
- **`.yaml`** - Règles de conformité pour l'audit (vérifications à effectuer)

## Structure des dossiers

```
templates/
├── template-hap-ac2.rsc          # Configuration RouterOS
├── template-hap-ac2.yaml         # Règles de conformité
├── template-hap-ax2.rsc
├── template-hap-ax2.yaml
├── template-chateau-lte12.rsc
├── template-chateau-lte12.yaml
├── template-chateau-lte18.rsc    # (à créer)
├── template-chateau-lte18.yaml   # (à créer)
├── template-rb4011.rsc           # (à créer)
├── template-rb4011.yaml          # (à créer)
├── template-ccr2004.rsc          # (à créer)
└── template-ccr2004.yaml         # (à créer)
```

## Fichier .rsc (Template RouterOS)

### Variables dynamiques supportées

| Variable | Description | Exemple |
|----------|-------------|---------|
| `{{client_id}}` | Identifiant client | `client-001` |
| `{{hostname}}` | Nom d'hôte du routeur | `mikrotik-paris-01` |
| `{{serial_number}}` | Numéro de série | `SN7D7A010` |
| `{{mac_ether2}}` | MAC du port Ether2 | `A7:D7:00:00:00:01` |
| `{{pppoe_login}}` | Login PPPoE | `client001@isp.fr` |
| `{{pppoe_password}}` | Mot de passe PPPoE | `secret123` |
| `{{ssid_2ghz}}` | SSID WiFi 2.4 GHz | `WiFi-Paris-2.4` |
| `{{ssid_5ghz}}` | SSID WiFi 5 GHz | `WiFi-Paris-5` |
| `{{wifi_key}}` | Clé WiFi (WPA2/WPA3) | `MySecureKey123!` |
| `{{vlan}}` | VLAN du site | `10` |
| `{{site}}` | Nom du site | `Site Principal` |
| `{{ip_lan}}` | IP LAN du routeur | `192.168.10.1` |
| `{{ip_wan}}` | IP WAN (ou dhcp) | `dhcp` |
| `{{model}}` | Modèle du routeur | `hAP ac²` |

### Exemple de template .rsc

```routeros
# Template hAP ac² - Généré par MSP

# Identity
/system identity set name="{{hostname}}"

# Utilisateurs
/user add name=OXIDIZED group=read password="{{wifi_key}}"
/user add name=admin-tech group=full password="{{wifi_key}}"
/user disable admin

# Bridge LAN
/interface bridge add name=bridge-lan
/interface bridge port add bridge=bridge-lan interface=ether2

# IP LAN
/ip address add address={{ip_lan}}/24 interface=bridge-lan

# WiFi
/interface wifi configuration add name=config-2ghz ssid="{{ssid_2ghz}}" \
    security.authentication-types=wpa2-psk,wpa3-psk \
    security.passphrase="{{wifi_key}}"

# PPPoE
/interface pppoe-client add name=pppoe-out1 interface=ether1 \
    user="{{pppoe_login}}" password="{{pppoe_password}}" \
    add-default-route=yes default-route-distance=1

# DNS
/ip dns set allow-remote-requests=yes servers=1.1.1.1,8.8.8.8

# NTP
/system ntp client set enabled=yes
/system ntp client servers add address=pool.ntp.org

# Firewall
/ip firewall filter add chain=input action=accept connection-state=established,related
/ip firewall filter add chain=input action=drop connection-state=invalid
/ip firewall nat add chain=srcnat action=masquerade out-interface=pppoe-out1
```

## Fichier .yaml (Template de conformité)

### Structure

```yaml
name: template-hap-ac2           # Nom unique du template
model: hAP ac²                    # Modèle de routeur correspondant
description: Template pour...     # Description

# ============================================================
# 1. VERSIONS
# ============================================================
versions:
  routeros_min_version: "7.10"           # Version minimale requise
  routeros_target_version: "7.15.3"      # Version cible pour les mises à jour
  firmware_required: true                # Firmware doit être synchronisé
  lte_firmware_required: false           # Firmware LTE requis (si LTE)

# ============================================================
# 2. INTERFACES
# ============================================================
interfaces:
  required:                              # Interfaces obligatoires
    - bridge-lan
    - ether2
    - ether3
  wan_interface: ether1                  # Interface WAN
  lan_bridge: bridge-lan                 # Bridge LAN

# ============================================================
# 3. PPPOE
# ============================================================
pppoe:
  required: true                         # PPPoE obligatoire
  max_active: 1                          # Nombre max de connexions actives
  min_active: 1                          # Nombre min de connexions actives
  route_distance_min: 1                  # Distance route min (1-20)
  route_distance_max: 20                 # Distance route max (1-20)
  check_login_configured: true           # Vérifier login configuré
  check_connection_active: true          # Vérifier connexion active
  check_public_ip: true                  # Vérifier IP publique
  check_default_route: true              # Vérifier route par défaut
  check_wan_list_membership: true        # Vérifier membre liste WAN
  check_internet_connectivity: true      # Tester connectivité Internet
  check_dns_resolution: true             # Tester résolution DNS
  ignore_interface_names:                # Noms d'interface à ignorer
    - pppoe-out1
    - pppoe-out2
    - pppoe-out3
    - pppoe-out4

# ============================================================
# 4. LTE
# ============================================================
lte:
  required: false                        # LTE obligatoire?
  route_distance: 21                     # Distance route LTE (doit être 21)
  check_modem_detected: true             # Vérifier modem détecté
  check_connection_active: true          # Vérifier connexion active
  check_route_present: true              # Vérifier route présente
  check_apn_configured: true             # Vérifier APN configuré

# ============================================================
# 5. WAN
# ============================================================
wan:
  check_pppoe_connected: true
  check_public_ip: true
  check_default_route: true
  check_internet: true
  check_dns: true
  result_states: [WAN opérationnel, WAN indisponible]

# ============================================================
# 6. DHCP
# ============================================================
dhcp:
  required_servers: 1                    # Nombre min de serveurs DHCP
  check_pools: true                      # Vérifier les pools
  check_networks: true                   # Vérifier les réseaux
  check_gateways: true                   # Vérifier les passerelles
  check_dns_servers: true                # Vérifier les DNS
  interface: bridge-lan                  # Interface du serveur DHCP

# ============================================================
# 7. DNS
# ============================================================
dns:
  allow_remote_requests: true            # allow-remote-requests=yes
  required_servers:                      # Serveurs DNS requis
    - "1.1.1.1"
    - "8.8.8.8"
  test_domains:                          # Domaines à tester
    - google.com
    - microsoft.com
    - webex.com
  result_states: [DNS fonctionnel, DNS KO]

# ============================================================
# 8. NTP
# ============================================================
ntp:
  enabled: true                          # NTP activé
  required_servers: 2                    # Nombre min de serveurs
  mode: unicast                          # Mode (unicast/multicast)

# ============================================================
# 9. SNMP
# ============================================================
snmp:
  enabled: true                          # SNMP activé
  required_communities: 1                # Nombre min de communities
  community_name: msp-monitoring         # Nom de community attendu
  check_traps: false                     # Vérifier les traps
  version: v2c                           # Version SNMP

# ============================================================
# 10. FIREWALL
# ============================================================
firewall:
  min_rules: 10                          # Nombre min de règles
  check_rule_order: true                 # Vérifier l'ordre des règles
  required_chains: [input, forward]      # Chaînes requises
  anti_scan_protection: true             # Protection anti-scan
  ddos_protection: true                  # Protection DDoS
  wan_input_restricted: true             # WAN input restreint
  lte_input_restricted: true             # LTE input restreint (si LTE)
  required_comments:                     # Commentaires de règles requis
    - "Accept established"
    - "Drop invalid"
    - "Accept LAN"
    - "Drop WAN input"
    - "Masquerade WAN"

# ============================================================
# 11. NAT
# ============================================================
nat:
  masquerade_required: true              # Masquerade requis
  out_interface: pppoe-out1              # Interface de sortie
  masquerade_interfaces:                 # Pour multi-WAN (LTE)
    - pppoe-out1
    - lte1

# ============================================================
# 12. WIFI
# ============================================================
wifi:
  check_ssid: true                       # Vérifier SSID
  check_2ghz: true                       # Vérifier bande 2.4 GHz
  check_5ghz: true                       # Vérifier bande 5 GHz
  check_security: true                   # Vérifier sécurité
  required_security: [wpa2-psk, wpa3-psk] # Types de sécurité requis
  check_interfaces_enabled: true         # Interfaces activées
  wifi6_enabled: false                   # WiFi 6 requis (ax models)

# ============================================================
# 13. UTILISATEURS
# ============================================================
users:
  required_users:                        # Utilisateurs obligatoires
    - OXIDIZED
    - admin-tech
  required_groups:                       # Groupes attendus
    OXIDIZED: read
    admin-tech: full
  admin_disabled: true                   # Compte admin désactivé
  check_permissions: true                # Vérifier les permissions

# ============================================================
# 14. SERVICES
# ============================================================
services:
  enabled:                               # Services activés
    - ssh
    - winbox
    - api
  disabled:                              # Services désactivés
    - telnet
    - ftp
    - www
    - api-ssl
  check_source_restrictions: true        # Vérifier restrictions source

# ============================================================
# 15. LOGGING
# ============================================================
logging:
  min_actions: 1                         # Nombre min d'actions
  loki_integration: true                 # Intégration Loki
  syslog_integration: false              # Intégration Syslog
  required_topics: [info, warning, error, critical]

# ============================================================
# 16. SCRIPTS
# ============================================================
scripts:
  required_scripts:                      # Scripts obligatoires
    - msp-healthcheck

# ============================================================
# 17. SCHEDULER
# ============================================================
scheduler:
  required_jobs:                         # Tâches planifiées requises
    - msp-healthcheck
  min_interval: 300                      # Intervalle min (secondes)

# ============================================================
# 18. CLASSIFICATION DES ANOMALIES
# ============================================================
anomaly_classification:
  compliant: "✅ Conforme"
  missing: "⚠️ Configuration absente"
  partial: "⚠️ Configuration partielle"
  misconfigured: "❌ Mauvaise configuration"

# ============================================================
# 19. NIVEAUX DE CRITICITÉ
# ============================================================
severity_levels:
  info: "Information"
  low: "Faible"
  medium: "Moyenne"
  high: "Élevée"
  critical: "Critique"
```

## Créer un nouveau template

### Étape 1: Créer le fichier .rsc

```bash
touch templates/template-nouveau-modele.rsc
```

Remplir avec la configuration RouterOS en utilisant les variables `{{variable}}`.

### Étape 2: Créer le fichier .yaml

```bash
touch templates/template-nouveau-modele.yaml
```

Remplir avec les règles de conformité selon la structure ci-dessus.

### Étape 3: Enregistrer dans la plateforme

Via l'API:

```bash
curl -X POST http://localhost:8000/api/templates \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "template-nouveau-modele",
    "model": "Nouveau Modele",
    "description": "Template pour le routeur Nouveau Modele",
    "rsc_content": "...",
    "yaml_content": "...",
    "target_routeros_version": "7.15.3"
  }'
```

Ou via l'interface web: **Templates → Nouveau template**

### Étape 4: Tester

1. Lancer un audit sur un routeur de ce modèle
2. Vérifier que toutes les vérifications passent
3. Ajuster le template si nécessaire

## Bonnes pratiques

1. **Toujours définir `target_routeros_version`** pour permettre les mises à jour automatiques
2. **Documenter les variables utilisées** dans le template
3. **Tester sur un routeur physique** avant déploiement en production
4. **Versionner les templates** (git)
5. **Ne jamais stocker de secrets en clair** dans les templates (utiliser les variables)
6. **Maintenir la cohérence** entre le .rsc et le .yaml
