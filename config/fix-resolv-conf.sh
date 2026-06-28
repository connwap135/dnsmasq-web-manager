#!/bin/bash
# fix-resolv-conf.sh
# 确保 /etc/resolv.conf 指向本地 dnsmasq
# 在 systemd-resolved 被禁用后使用

RESOLV=/etc/resolv.conf

if ! grep -q "nameserver 127.0.0.1" "$RESOLV" 2>/dev/null; then
    echo "nameserver 127.0.0.1" > "$RESOLV"
fi
