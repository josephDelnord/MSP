# ============================================================
# Template RouterOS pour Mikrotik hAP ax²
# Généré par MSP - Mikrotik Provisioning Manager
# ============================================================

/system identity set name="{{hostname}}"

# Utilisateurs
/user add name=OXIDIZED group=read password="{{wifi_key}}" comment="Monitoring"
/user add name=admin-tech group=full password="{{wifi_key}}" comment="Technicien"
/user disable admin

# Bridge LAN
/interface bridge add name=bridge-lan protocol-mode=rstp
/interface bridge port add bridge=bridge-lan interface=ether2
/interface bridge port add bridge=bridge-lan interface=ether3
/interface bridge port add bridge=bridge-lan interface=ether4
/interface bridge port add bridge=bridge-lan interface=ether5

# IP LAN
/ip address add address={{ip_lan}}/24 interface=bridge-lan

# WiFi 2.4 GHz (WiFi 6)
/interface wifi configuration add name=config-2ghz ssid="{{ssid_2ghz}}" country=france mode=ap datapath.bridge=bridge-lan security.authentication-types=wpa2-psk,wpa3-psk security.passphrase="{{wifi_key}}" channel.band=2ghz-g/n/ax channel.width=20/40mhz
/interface wifi add name=wifi-2ghz configuration=config-2ghz

# WiFi 5 GHz (WiFi 6)
/interface wifi configuration add name=config-5ghz ssid="{{ssid_5ghz}}" country=france mode=ap datapath.bridge=bridge-lan security.authentication-types=wpa2-psk,wpa3-psk security.passphrase="{{wifi_key}}" channel.band=5ghz-a/n/ac/ax channel.width=20/40/80mhz
/interface wifi add name=wifi-5ghz configuration=config-5ghz

# PPPoE
/interface pppoe-client add name=pppoe-out1 interface=ether1 user="{{pppoe_login}}" password="{{pppoe_password}}" add-default-route=yes default-route-distance=1

# DHCP
/ip pool add name=pool-lan ranges={{ip_lan_prefix}}.100-{{ip_lan_prefix}}.250
/ip dhcp-server network add address={{ip_lan_prefix}}.0/24 gateway={{ip_lan}} dns-server=1.1.1.1,8.8.8.8
/ip dhcp-server add name=dhcp-lan interface=bridge-lan address-pool=pool-lan

# DNS
/ip dns set allow-remote-requests=yes servers=1.1.1.1,8.8.8.8

# NTP
/system ntp client set enabled=yes mode=unicast
/system ntp client servers add address=pool.ntp.org
/system ntp client servers add address=time.google.com

# SNMP
/snmp set enabled=yes contact="msp@operator.fr" location="{{site}}"
/snmp community add name=msp-monitoring addresses=0.0.0.0/0

# Logging
/system logging action add name=loki target=remote remote=10.0.0.10 remote-port=3100
/system logging add topics=info,!ntp action=loki

# Firewall
/ip firewall filter add chain=input action=accept connection-state=established,related
/ip firewall filter add chain=input action=drop connection-state=invalid
/ip firewall filter add chain=input action=drop in-interface=pppoe-out1
/ip firewall filter add chain=forward action=accept in-interface=bridge-lan out-interface=pppoe-out1

# NAT
/ip firewall nat add chain=srcnat action=masquerade out-interface=pppoe-out1

# Services
/ip service disable telnet
/ip service disable ftp
/ip service disable www
/ip service disable api-ssl

:log info "MSP Provisioning completed for {{hostname}} (hAP ax²)"
