#!/bin/bash
# Dnsmasq Web Manager - 一键安装脚本
# 适用于 Ubuntu/Debian 系统
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
err() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# Root check
[[ $EUID -ne 0 ]] && err "请使用 root 权限运行: sudo bash $0"

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
WEB_DIR="/opt/dnsmasq-web"
LISTEN_IP=$(hostname -I | awk '{print $1}')

echo "========================================="
echo "  Dnsmasq Web Manager 安装程序"
echo "========================================="
echo ""

# 1. 安装依赖
log "安装系统依赖..."
apt-get update -qq
apt-get install -y -qq dnsmasq python3 python3-pip > /dev/null 2>&1
pip3 install flask --break-system-packages -q 2>/dev/null || pip3 install flask -q

# 2. 停用 systemd-resolved
if systemctl is-active --quiet systemd-resolved 2>/dev/null; then
    log "停用 systemd-resolved..."
    systemctl stop systemd-resolved
    systemctl disable systemd-resolved
fi

# 3. 部署 dnsmasq 配置
log "部署 dnsmasq 配置..."
cp "$SCRIPT_DIR/config/dnsmasq.conf" /etc/dnsmasq.conf
# 替换监听 IP
sed -i "s/listen-address=127.0.0.1,.*/listen-address=127.0.0.1,$LISTEN_IP/" /etc/dnsmasq.conf

# 4. 创建必要文件
touch /etc/dnsmasq.hosts
mkdir -p /etc/dnsmasq.d

# 5. 部署 Web 应用
log "部署 Web 应用..."
mkdir -p "$WEB_DIR"
cp "$SCRIPT_DIR/app.py" "$WEB_DIR/"
cp -r "$SCRIPT_DIR/templates" "$WEB_DIR/"

# 6. 部署 systemd 服务
log "配置系统服务..."
cp "$SCRIPT_DIR/systemd/dnsmasq-web.service" /etc/systemd/system/
cp "$SCRIPT_DIR/systemd/fix-resolv.service" /etc/systemd/system/
cp "$SCRIPT_DIR/config/fix-resolv-conf.sh" /usr/local/bin/
chmod +x /usr/local/bin/fix-resolv-conf.sh

# 7. 修改 resolv.conf
log "配置 DNS 解析..."
echo "nameserver 127.0.0.1" > /etc/resolv.conf

# 8. 启动服务
log "启动所有服务..."
systemctl daemon-reload
systemctl enable --now dnsmasq fix-resolv dnsmasq-web 2>/dev/null

# 9. 验证
sleep 2
if systemctl is-active --quiet dnsmasq && systemctl is-active --quiet dnsmasq-web; then
    echo ""
    echo "========================================="
    echo -e "${GREEN}  安装成功！${NC}"
    echo "========================================="
    echo ""
    echo "  Web 界面: http://$LISTEN_IP:8080"
    echo "  API 地址: http://$LISTEN_IP:8080/api/hosts"
    echo ""
    echo "  服务状态:"
    echo "    dnsmasq:     $(systemctl is-active dnsmasq)"
    echo "    dnsmasq-web: $(systemctl is-active dnsmasq-web)"
    echo ""
else
    err "服务启动失败，请检查日志: journalctl -u dnsmasq-web -n 20"
fi
