#!/bin/bash

# ============================================
# Anonymity Setup Script for Pentesting
# Run with: sudo bash setup-anon.sh
# ============================================

set -e

echo "[*] Installing dependencies..."
apt update
apt install -y tor iptables curl git

echo "[*] Installing anonsurf..."
cd /tmp
git clone https://github.com/Und3rf10w/kali-anonsurf.git
cd kali-anonsurf
./installer.sh

echo "[*] Setting up persistent MAC spoofing..."
cp /home/l0ve/Desktop/betfury/macspoof.service /etc/systemd/system/macspoof@.service

# Create improved templated service
cat > /etc/systemd/system/macspoof@.service << 'EOF'
[Unit]
Description=MAC Spoofing on %i
Wants=network-pre.target
Before=network-pre.target
BindsTo=sys-subsystem-net-devices-%i.device
After=sys-subsystem-net-devices-%i.device

[Service]
Type=oneshot
ExecStart=/usr/bin/ip link set dev %i down
ExecStart=/usr/bin/macchanger -r %i
ExecStart=/usr/bin/ip link set dev %i up
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

echo "[*] Enabling MAC spoofing for eth0..."
systemctl daemon-reload
systemctl enable macspoof@eth0.service

echo "[*] Starting services..."
systemctl start macspoof@eth0.service

echo ""
echo "============================================"
echo "[+] Setup complete!"
echo "============================================"
echo ""
echo "Current MAC address:"
ip link show eth0 | grep ether
echo ""
echo "Commands:"
echo "  anonsurf start    - Start anonymous mode"
echo "  anonsurf stop     - Stop anonymous mode"
echo "  anonsurf status   - Check status"
echo "  anonsurf myip     - Show current IP"
echo ""
echo "MAC will auto-randomize on every reboot."
echo "============================================"
