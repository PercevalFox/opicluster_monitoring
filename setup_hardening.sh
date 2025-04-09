#!/bin/bash
set -e

echo "[+] Mise en place des règles iptables et fail2ban..."

# Règles iptables minimales
iptables -F INPUT
iptables -F OUTPUT
iptables -F FORWARD
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

iptables -A INPUT -i lo -j ACCEPT
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Autoriser SSH limité
iptables -A INPUT -p tcp --dport 22 -m limit --limit 3/min --limit-burst 5 -j ACCEPT

# HTTP / HTTPS
iptables -A INPUT -p tcp -m multiport --dports 80,443 -j ACCEPT

# ICMP limité
iptables -A INPUT -p icmp --icmp-type echo-request -m limit --limit 1/s -j ACCEPT

# Fail2ban (assume installé)
systemctl enable fail2ban
systemctl start fail2ban

echo "[✓] Sécurité réseau renforcée."
