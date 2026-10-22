# Architecture MSP - Mikrotik Provisioning Manager

## Vue d'ensemble (C4 - Niveau 1: Contexte)

```
┌─────────────────────────────────────────────────────────────────┐
│                         UTILISATEURS                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Technicien  │  │  Opérateur  │  │  Administrateur système │  │
│  │   NOC       │  │    MSP      │  │                         │  │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘  │
│         │                │                     │                 │
│         └────────────────┼─────────────────────┘                 │
│                          │                                       │
│                          ▼                                       │
│              ┌───────────────────────┐                          │
│              │   MSP Platform        │◄────┐                    │
│              │  (Mikrotik Provisioning│     │                    │
│              │     Manager)          │     │                    │
│              └───────────┬───────────┘     │                    │
│                          │                 │                    │
└──────────────────────────┼─────────────────┘                    │
                           │                                      │
        ┌─────────────────┼─────────────────┐                   │
        │                 │                 │                   │
        ▼                 ▼                 ▼                   │
┌───────────────┐ ┌───────────────┐ ┌───────────────┐          │
│  Routeurs     │ │  Systèmes     │ │  Notifications│          │
│  Mikrotik     │ │  externes     │ │  (Webex/Teams/│          │
│  (RouterOS)   │ │  (CRM/ITSM)   │ │   Email/etc)  │          │
└───────────────┘ └───────────────┘ └───────────────┘          │
                                                                 │
┌─────────────────────────────────────────────────────────────────┘
│                    SYSTÈMES EXTERNES
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│  │Microsoft│ │ Service │ │  GLPI   │ │  Jira   │ │ Webhook │
│  │ EntraID │ │  Now    │ │         │ │   SM    │ │         │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
```

## Vue d'ensemble (C4 - Niveau 2: Conteneurs)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        MSP PLATFORM (Docker)                             │
│                                                                          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────────┐  │
│  │             │    │             │    │                             │  │
│  │  Frontend   │◄──►│   Backend   │◄──►│      PostgreSQL             │  │
│  │  (React/    │    │  (FastAPI/  │    │      (Base de données)      │  │
│  │   Nginx)    │    │   Python)   │    │                             │  │
│  │             │    │             │    │  • Routeurs                 │  │
│  │  Port: 80   │    │  Port: 8000 │    │  • Clients                  │  │
│  │             │    │             │    │  • Sites                    │  │
│  └─────────────┘    └──────┬──────┘    │  • Templates                │  │
│                            │            │  • Audits                   │  │
│                     ┌──────┴──────┐     │  • Alertes                  │  │
│                     │             │     │  • Utilisateurs             │  │
│                     ▼             ▼     │                             │  │
│              ┌─────────┐   ┌─────────┐  │  • Firmware Updates         │  │
│              │  Redis  │   │ Mikrotik│  └─────────────────────────────┘  │
│              │ (Cache) │   │ Service │                                    │
│              │         │   │         │                                    │
│              │Port:6379│   │(API/SSH)│                                    │
│              └─────────┘   └────┬────┘                                    │
│                                │                                         │
│                    ┌───────────┴───────────┐                            │
│                    │    Routeurs Mikrotik   │                            │
│                    │  (192.168.88.1, etc.)  │                            │
│                    │  • RouterOS API :8728  │                            │
│                    │  • SSH          :22    │                            │
│                    │  • SNMP         :161   │                            │
│                    └───────────────────────┘                            │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    OBSERVABILITÉ (Production)                    │   │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────────┐ │   │
│  │  │Prometheus │  │  Grafana  │  │   Loki    │  │  Nginx Proxy  │ │   │
│  │  │ (Metrics) │  │(Dashboards)│  │  (Logs)   │  │  (Reverse     │ │   │
│  │  │           │  │           │  │           │  │   Proxy)      │ │   │
│  │  │Port: 9090 │  │Port: 3001 │  │Port: 3100 │  │  Port: 80/443 │ │   │
│  │  └───────────┘  └───────────┘  └───────────┘  └───────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Vue d'ensemble (C4 - Niveau 3: Composants Backend)

```
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI)                           │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    API Layer (Routes)                    │    │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────────┐│    │
│  │  │ /routers│ │ /audits │ │ /alerts │ │ /templates      ││    │
│  │  │         │ │         │ │         │ │                 ││    │
│  │  │• list  │ │• run   │ │• list  │ │ • CRUD          ││    │
│  │  │• create│ │• get   │ │• create│ │ • upload        ││    │
│  │  │• update│ │• history│ │• resolve│• delete        ││    │
│  │  │• delete│ │         │ │• notify│ │                 ││    │
│  │  │• discover│        │ │         │ │                 ││    │
│  │  │• provision│       │ │         │ │                 ││    │
  │  │  │• update │ │         │ │         │ │                 ││    │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────────────┘│    │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────────┐│    │
│  │  │/clients │ │ /sites  │ │/dashboard│ │ /auth          ││    │
│  │  │         │ │         │ │         │ │                 ││    │
│  │  │• CRUD   │ │• CRUD   │ │• stats  │ │ • login         ││    │
│  │  │         │ │         │ │• status │ │ • register      ││    │
│  │  └─────────┘ └─────────┘ └─────────┘ │ • me            ││    │
│  │                                      └─────────────────┘│    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                  Services Layer                          │    │
│  │                                                          │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │    │
│  │  │  Mikrotik   │  │  Compliance │  │   Discovery     │ │    │
│  │  │  Service    │  │   Engine    │  │   Service       │ │    │
│  │  │             │  │             │  │                 │ │    │
│  │  │• connect()  │  │• run_audit()│  │ • discover()    │ │    │
│  │  │• get_info() │  │• check_*()  │  │ • register()    │ │    │
│  │  │• get_pppoe()│  │  (15 catégories)│ • provision()  │ │    │
│  │  │• get_routes()│ │• generate_  │  │                 │ │    │
│  │  │• get_dhcp() │  │  remediation()│ │               │ │    │
│  │  │• get_dns()  │  │             │  │                 │ │    │
│  │  │• get_wifi() │  │             │  │                 │ │    │
│  │  │• get_users()│  │             │  │                 │ │    │
│  │  │• reboot()   │  │             │  │                 │ │    │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘ │    │
│  │                                                          │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │    │
│  │  │   Alert     │  │ Notification│  │   Provisioning  │ │    │
│  │  │  Service    │  │   Service   │  │     Service     │ │    │
│  │  │             │  │             │  │                 │ │    │
│  │  │• create()   │  │• send()     │  │ • check_updates()│   │
│  │  │• resolve()  │  │• email()    │  │ • perform_update()│  │
│  │  │• acknowledge│  │• webex()    │  │ • provision()   │ │    │
│  │  │• check_     │  │• teams()    │  │                 │ │    │
│  │  │  health()   │  │• webhook()  │  │                 │ │    │
│  │  │             │  │• servicenow()│ │                 │ │    │
│  │  │             │  │• glpi()     │  │                 │ │    │
│  │  │             │  │• jira()     │  │                 │ │    │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘ │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                  Data Layer (SQLAlchemy)                 │    │
│  │                                                          │    │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────────┐│    │
│  │  │ Router  │ │ Client  │ │  Site   │ │    Template     ││    │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────────────┘│    │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────────┐│    │
│  │  │  Audit  │ │  Alert  │ │Firmware │ │      User       ││    │
│  │  │         │ │         │ │ Update  │ │                 ││    │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────────────┘│    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                    ┌─────────┴─────────┐                        │
│                    │    PostgreSQL      │                        │
│                    │    + Redis Cache   │                        │
│                    └───────────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
```

## Schéma d'infrastructure (Déploiement Local)

```
┌─────────────────────────────────────────────────────────────┐
│                    HÔTE LOCAL (Docker)                       │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Réseau: msp-network (bridge)            │    │
│  │                                                      │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │    │
│  │  │  msp-frontend│  │  msp-backend │  │ msp-postgres│  │    │
│  │  │  :3000      │  │  :8000      │  │  :5432      │  │    │
│  │  │  (Node/Vite)│  │  (Python)   │  │  (PostgreSQL│  │    │
│  │  │             │  │             │  │   16-alpine)│  │    │
│  │  └─────────────┘  └──────┬──────┘  └─────────────┘  │    │
│  │                          │                          │    │
│  │                    ┌─────┴─────┐                    │    │
│  │                    │  msp-redis │                    │    │
│  │                    │  :6379     │                    │    │
│  │                    │  (Redis 7) │                    │    │
│  │                    └───────────┘                    │    │
│  │                                                      │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  Volumes:                                                    │
│  • postgres_data  → /var/lib/postgresql/data                │
│  • redis_data     → /data                                    │
│                                                              │
│  Ports exposés:                                              │
│  • 3000 → Frontend (Vite dev server)                        │
│  • 8000 → Backend API (FastAPI)                             │
│  • 5432 → PostgreSQL                                        │
│  • 6379 → Redis                                             │
└─────────────────────────────────────────────────────────────┘
         │
         │ (communication réseau local)
         ▼
┌─────────────────────────────────────────────────────────────┐
│              ROUTEURS MIKROTIK (réseau local)                 │
│                                                              │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │hAP ac²  │  │hAP ax²  │  │Chateau  │  │ RB4011  │  ...   │
│  │192.168. │  │192.168. │  │LTE12    │  │192.168. │        │
│  │  88.1   │  │  88.2   │  │192.168. │  │  88.4   │        │
│  │         │  │         │  │  88.3   │  │         │        │
│  │API:8728 │  │API:8728 │  │API:8728 │  │API:8728 │        │
│  │SSH:22   │  │SSH:22   │  │SSH:22   │  │SSH:22   │        │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Modèle de données (ERD simplifié)

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│   clients   │◄──────│    sites    │◄──────│   routers   │
│─────────────│  1:N  │─────────────│  1:N  │─────────────│
│ id (PK)     │       │ id (PK)     │       │ id (PK)     │
│ name        │       │ client_id(FK)│       │ client_id(FK)│
│ reference_  │       │ name        │       │ site_id(FK) │
│   crm       │       │ address     │       │ template_id │
│ contact_    │       │ city        │       │   (FK)      │
│   email     │       │ vlan        │       │ hostname    │
│ is_active   │       │ ip_lan      │       │ ip_address  │
└─────────────┘       │ ip_wan      │       │ model       │
                      └─────────────┘       │ serial_num  │
                                            │ mac_ether2  │
                                            │ routeros_ver│
                                            │ status      │
                                            │ compliance_ │
                                            │   status    │
                                            │ compliance_ │
                                            │   score     │
                                            │ is_discovered│
                                            │ is_provisioned│
                                            └──────┬──────┘
                                                   │
                    ┌──────────────────────────────┼──────────────┐
                    │                              │              │
                    ▼ 1:N                        ▼ 1:N          ▼ 1:N
           ┌─────────────┐               ┌─────────────┐  ┌─────────────┐
           │   audits    │               │   alerts    │  │  firmware_  │
           │─────────────│               │─────────────│  │   updates   │
           │ id (PK)     │               │ id (PK)     │  │─────────────│
           │ router_id(FK)│              │ router_id(FK)│  │ id (PK)     │
           │ status      │               │ severity    │  │ router_id(FK)│
           │ compliance_ │               │ status      │  │ update_type │
           │   status    │               │ title       │  │ old_version │
           │ compliance_ │               │ description │  │ new_version │
           │   score     │               │ category    │  │ status      │
           │ checks(JSON)│               │ is_notified │  │ result      │
           │ anomalies   │               │ created_at  │  │ duration    │
           │   (JSON)    │               │ resolved_at │  │             │
           │ remediation_│               └─────────────┘  └─────────────┘
           │   mode      │
           │ remediation_│
           │   commands  │
           │   (JSON)    │
           │ remediation_│
           │   applied   │
           └─────────────┘

┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│  templates  │◄──────│   routers   │       │    users    │
│─────────────│  N:1  │  (voir ci-  │       │─────────────│
│ id (PK)     │       │   dessus)   │       │ id (PK)     │
│ name        │       └─────────────┘       │ username    │
│ model       │                             │ email       │
│ description │                             │ hashed_pwd  │
│ rsc_content │                             │ full_name   │
│ yaml_content│                             │ role        │
│ variables_  │                             │ is_active   │
│   schema    │                             │ is_superuser│
│ target_     │                             │ entra_id    │
│   routeros  │                             │ last_login  │
│ target_fw   │                             └─────────────┘
│ target_lte  │
│ is_active   │
└─────────────┘
```

## Flux de provisioning

```
Technicien                MSP Platform              Routeur Mikrotik
    │                         │                          │
    │  Branche le routeur     │                          │
    │  (192.168.88.1)         │                          │
    │                         │                          │
    │  ──Découverte──────────►│                          │
    │                         │────Connexion API/SSH────►│
    │                         │◄───Infos (modèle, S/N,   │
    │                         │     versions, MAC...)    │
    │                         │                          │
    │                         │──Recherche template─────│
    │                         │                          │
    │                         │◄─Si template trouvé──────│
    │                         │                          │
    │                         │──Vérification versions──►│
    │                         │◄──Versions actuelles─────│
    │                         │                          │
    │                         │──Mise à jour RouterOS───►│
    │                         │◄───Redémarrage───────────│
    │                         │                          │
    │                         │──Reconnexion────────────►│
    │                         │                          │
    │                         │──Upload config.rsc──────►│
    │                         │                          │
    │                         │──reset-configuration────►│
    │                         │    run-after-reset        │
    │                         │◄───Redémarrage───────────│
    │                         │                          │
    │                         │──Reconnexion────────────►│
    │                         │                          │
    │                         │──Audit conformité────────►│
    │                         │◄───Résultats audit───────│
    │                         │                          │
    │◄─Rapport provisioning──│                          │
    │  (succès/échec)         │                          │
    │                         │                          │
```

## Flux d'audit de conformité

```
┌─────────────┐     ┌─────────────┐     ┌─────────────────────────┐
│  Déclencheur │────►│  Compliance │────►│  15 catégories de       │
│  (manuel/    │     │   Engine    │     │  vérifications:          │
│   auto/      │     │             │     │                         │
│   scheduled) │     │             │     │  1. Versions            │
└─────────────┘     │             │     │  2. Interfaces          │
                    │             │     │  3. PPPoE               │
                    │             │     │  4. LTE                 │
                    │             │     │  5. WAN                 │
                    │             │     │  6. DHCP                │
                    │             │     │  7. DNS                 │
                    │             │     │  8. NTP                 │
                    │             │     │  9. SNMP                │
                    │             │     │  10. Firewall           │
                    │             │     │  11. NAT                │
                    │             │     │  12. WiFi               │
                    │             │     │  13. Utilisateurs       │
                    │             │     │  14. Services           │
                    │             │     │  15. Logging            │
                    │             │     └─────────────────────────┘
                    │             │                  │
                    │             │                  ▼
                    │             │     ┌─────────────────────────┐
                    │             │     │  Classification:        │
                    │             │     │  ✅ Conforme            │
                    │             │     │  ⚠️ Warning/Absent/     │
                    │             │     │     Partiel             │
                    │             │     │  ❌ Non conforme        │
                    │             │     └─────────────────────────┘
                    │             │                  │
                    │             │                  ▼
                    │             │     ┌─────────────────────────┐
                    │             │     │  Calcul du score        │
                    │             │     │  (0-100%)               │
                    │             │     │                         │
                    │             │     │  ≥95% & 0 NC → Conforme │
                    │             │     │  ≥70% → Conforme avec   │
                    │             │     │         avertissements   │
                    │             │     │  <70% → Non conforme    │
                    │             │     └─────────────────────────┘
                    │             │                  │
                    │             ▼                  ▼
                    │     ┌─────────────────────────────────────┐
                    │     │  Mode de remédiation:               │
                    │     │                                     │
                    │     │  Mode 1: Audit seul                 │
                    │     │  Mode 2: Audit + proposition        │
                    │     │  Mode 3: Audit + correction auto   │
                    │     │           + revalidation            │
                    │     └─────────────────────────────────────┘
                    │                        │
                    ▼                        ▼
            ┌─────────────┐         ┌─────────────┐
            │  Stockage   │         │   Alertes   │
            │  (Audit DB) │         │  (si anomalie│
            │             │         │   détectée) │
            └─────────────┘         └──────┬──────┘
                                           │
                                           ▼
                                    ┌─────────────┐
                                    │ Notifications│
                                    │  multi-canaux│
                                    │ (Email, Teams│
                                    │  Webex, ITSM)│
                                    └─────────────┘
```
