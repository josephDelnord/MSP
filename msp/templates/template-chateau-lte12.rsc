# ============================================================
# Template RouterOS pour Mikrotik Chateau LTE12
# Généré par MSP - Mikrotik Provisioning Manager
# ============================================================

/system identity set name="{{hostname}}"

# Utilisateurs
/user add name=OXIDIZED group=read password="{{wifi_key}}"
/user add name=admin-tech group=full password="{{wifi_key}}"
/user disable admin

# Bridge LAN
/interface bridge add name=bridge-lan protocol-mode=rstp
/interface bridge port add bridge=bridge-lan interface=ether2
/interface bridge port add bridge=bridge-lan interface=ether3
/interface bridge port add bridge=bridge-lan interface=ether4

# IP LAN
/ip address add address={{ip_lan}}/24 interface=bridge-lan

# WiFi
/interface wifi configuration add name=config-2ghz ssid="{{ssid_2ghz}}" country=france mode=ap datapath.bridge=bridge-lan security.authentication-types=wpa2-psk,wpa3-psk security.passphrase="{{wifi_key}}"
/interface wifi add name=wifi-2ghz configuration=config-2ghz
/interface wifi configuration add name=config-5ghz ssid="{{ssid_5ghz}}" country=france mode=ap datapath.bridge=bridge-lan security.authentication-types=wpa2-psk,wpa3-psk security.passphrase="{{wifi_key}}"
/interface wifi add name=wifi-5ghz configuration=config-5ghz

# LTE Interface
/interface lte apn add name=lte-apn use-network-apn=yes
/interface lte set lte1 apn=lte-apn

# PPPoE (backup WAN)
/interface pppoe-client add name=pppoe-out1 interface=ether1 user="{{pppoe_login}}" password="{{pppoe_password}}" add-default-route=yes default-route-distance=1

# Route LTE avec distance 21
/ip route add dst-address=0.0.0.0/0 gateway=lte1 distance=21 comment="LTE Default Route"

# DHCP
/ip pool add name=pool-lan ranges={{ip_lan_prefix}}.100-{{ip_lan_prefix}}.250
/ip dhcp-server network add address={{ip_lan_prefix}}.0/24 gateway={{ip_lan}} dns-server=1.1.1.1,8.8.8.8
/ip dhcp-server add name=dhcp-lan interface=bridge-lan address-pool=pool-lan

# DNS
/ip dns set allow-remote-requests=yes servers=1.1.1.1,8.8.8.8

# NTP
/system ntp client set enabled=yes mode=unicast
/system ntp client servers add address=pool.ntp.org

# SNMP
/snmp set enabled=yes contact="msp@operator.fr" location="{{site}}"

# Logging
/system logging action add name=loki target=remote remote=10.0.0.10 remote-port=3100
/system logging add topics=info,!ntp action=loki

# Firewall
/ip firewall filter add chain=input action=accept connection-state=established,related
/ip firewall filter add chain=input action=drop connection-state=invalid
/ip firewall filter add chain=input action=drop in-interface=pppoe-out1
/ip firewall filter add chain=input action=drop in-interface=lte1
/ip firewall filter add chain=forward action=accept in-interface=bridge-lan

# NAT
/ip firewall nat add chain=srcnat action=masquerade out-interface=pppoe-out1
/ip firewall nat add chain=srcnat action=masquerade out-interface=lte1

# Services
/ip service disable telnet
/ip service disable ftp
/ip service disable www

:log info "MSP Provisioning completed for {{hostname}} (Chateau LTE12)"
