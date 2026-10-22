# ============================================================
# Template RouterOS pour Mikrotik hAP ac²
# Généré par MSP - Mikrotik Provisioning Manager
# ============================================================
# Variables dynamiques:
#   {{client_id}} {{hostname}} {{serial_number}} {{mac_ether2}}
#   {{pppoe_login}} {{pppoe_password}} {{ssid_2ghz}} {{ssid_5ghz}}
#   {{wifi_key}} {{vlan}} {{site}} {{ip_lan}} {{ip_wan}}

# ---------------------------------------------------------------
# Identity
# ---------------------------------------------------------------
/system identity set name="{{hostname}}"

# ---------------------------------------------------------------
# Utilisateurs
# ---------------------------------------------------------------
/user add name=OXIDIZED group=read password="{{wifi_key}}" comment="Monitoring Oxidized"
/user add name=admin-tech group=full password="{{wifi_key}}" comment="Technicien exploitant"
/user disable admin
/user set OXIDIZED comment="MSP-{{client_id}}"

# ---------------------------------------------------------------
# Bridge LAN
# ---------------------------------------------------------------
/interface bridge add name=bridge-lan protocol-mode=rstp comment="LAN Bridge"
/interface bridge port add bridge=bridge-lan interface=ether2 comment="LAN Port 2"
/interface bridge port add bridge=bridge-lan interface=ether3 comment="LAN Port 3"
/interface bridge port add bridge=bridge-lan interface=ether4 comment="LAN Port 4"
/interface bridge port add bridge=bridge-lan interface=ether5 comment="LAN Port 5"

# ---------------------------------------------------------------
# Adresse IP LAN
# ---------------------------------------------------------------
/ip address add address={{ip_lan}}/24 interface=bridge-lan comment="LAN Management"

# ---------------------------------------------------------------
# WiFi 2.4 GHz
# ---------------------------------------------------------------
/interface wifi configuration add name=config-2ghz ssid="{{ssid_2ghz}}" country=france mode=ap datapath.bridge=bridge-lan security.authentication-types=wpa2-psk,wpa3-psk security.passphrase="{{wifi_key}}" channel.band=2ghz-g/n channel.width=20/40mhz
/interface wifi add name=wifi-2ghz master-interface=wifi1 configuration=config-2ghz comment="WiFi 2.4 GHz"

# ---------------------------------------------------------------
# WiFi 5 GHz
# ---------------------------------------------------------------
/interface wifi configuration add name=config-5ghz ssid="{{ssid_5ghz}}" country=france mode=ap datapath.bridge=bridge-lan security.authentication-types=wpa2-psk,wpa3-psk security.passphrase="{{wifi_key}}" channel.band=5ghz-a/n/ac channel.width=20/40/80mhz
/interface wifi add name=wifi-5ghz master-interface=wifi2 configuration=config-5ghz comment="WiFi 5 GHz"

# ---------------------------------------------------------------
# PPPoE Client (WAN)
# ---------------------------------------------------------------
/interface pppoe-client add name=pppoe-out1 interface=ether1 user="{{pppoe_login}}" password="{{pppoe_password}}" add-default-route=yes default-route-distance=1 use-peer-dns=no comment="WAN PPPoE"

# ---------------------------------------------------------------
# DHCP Server
# ---------------------------------------------------------------
/ip pool add name=pool-lan ranges={{ip_lan_prefix}}.100-{{ip_lan_prefix}}.250
/ip dhcp-server network add address={{ip_lan_prefix}}.0/24 gateway={{ip_lan}} dns-server=1.1.1.1,8.8.8.8 comment="LAN Network"
/ip dhcp-server add name=dhcp-lan interface=bridge-lan address-pool=pool-lan lease-time=1d comment="DHCP LAN"

# ---------------------------------------------------------------
# DNS
# ---------------------------------------------------------------
/ip dns set allow-remote-requests=yes servers=1.1.1.1,8.8.8.8 cache-size=4096KiB

# ---------------------------------------------------------------
# NTP
# ---------------------------------------------------------------
/system ntp client set enabled=yes mode=unicast
/system ntp client servers add address=pool.ntp.org comment="NTP Pool"
/system ntp client servers add address=time.google.com comment="NTP Google"
/system clock set time-zone-name=Europe/Paris

# ---------------------------------------------------------------
# SNMP
# ---------------------------------------------------------------
/snmp set enabled=yes contact="msp@operator.fr" location="{{site}}" engine-id="{{serial_number}}"
/snmp community add name=msp-monitoring addresses=10.0.0.0/8 authentication-protocol=SHA1 encryption-protocol=AES read-access=yes write-access=no

# ---------------------------------------------------------------
# Logging
# ---------------------------------------------------------------
/system logging action add name=loki target=remote remote=10.0.0.10 remote-port=3100
/system logging add topics=info,warning,error,critical action=loki prefix="{{hostname}}"
/system logging add topics=firewall action=loki prefix="{{hostname}}-fw"

# ---------------------------------------------------------------
# Firewall - Filter
# ---------------------------------------------------------------
/ip firewall filter add chain=input action=accept connection-state=established,related comment="Accept established/related"
/ip firewall filter add chain=input action=drop connection-state=invalid comment="Drop invalid"
/ip firewall filter add chain=input action=accept protocol=icmp comment="Accept ICMP"
/ip firewall filter add chain=input action=accept in-interface=bridge-lan comment="Accept LAN"
/ip firewall filter add chain=input action=drop in-interface=pppoe-out1 comment="Drop WAN input"

# Anti-scan
/ip firewall filter add chain=input action=add-src-to-address-list address-list=port-scanners address-list-timeout=1d protocol=tcp psd=21,3s,3,1 comment="Anti port scan"
/ip firewall filter add chain=input action=tarpit protocol=tcp src-address-list=port-scanners comment="Tarpit scanners"
/ip firewall filter add chain=input action=drop src-address-list=port-scanners comment="Drop scanners"

# DDoS Protection
/ip firewall filter add chain=input action=drop protocol=tcp dst-port=53,123,1900 in-interface=pppoe-out1 comment="DDoS DNS/NTP/SSDP"
/ip firewall filter add chain=forward action=accept connection-state=established,related comment="Accept forward established"
/ip firewall filter add chain=forward action=accept in-interface=bridge-lan out-interface=pppoe-out1 comment="Accept LAN to WAN"
/ip firewall filter add chain=forward action=drop comment="Drop all forward"

# ---------------------------------------------------------------
# Firewall - NAT
# ---------------------------------------------------------------
/ip firewall nat add chain=srcnat action=masquerade out-interface=pppoe-out1 comment="Masquerade WAN"

# ---------------------------------------------------------------
# Services
# ---------------------------------------------------------------
/ip service set ssh port=22 address=10.0.0.0/8,{{ip_lan_prefix}}.0/24
/ip service set winbox address=10.0.0.0/8,{{ip_lan_prefix}}.0/24
/ip service set api address=10.0.0.0/8,{{ip_lan_prefix}}.0/24
/ip service disable telnet
/ip service disable ftp
/ip service disable www
/ip service disable api-ssl

# ---------------------------------------------------------------
# Scripts
# ---------------------------------------------------------------
/system script add name=msp-healthcheck source=":log info \"MSP Healthcheck - {{hostname}}\""

# ---------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------
/system scheduler add name=msp-healthcheck interval=5m start-time=00:00:00 on-event=msp-healthcheck comment="MSP Healthcheck"

# ---------------------------------------------------------------
# Final
# ---------------------------------------------------------------
:log info "MSP Provisioning completed for {{hostname}} ({{model}}) - Serial: {{serial_number}}"
