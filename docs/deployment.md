# 部署文档

## 环境信息

- **服务器**：192.168.3.32
- **系统**：Ubuntu 24.04.4 LTS
- **内核**：Linux 7.0.6-2-pve
- **dnsmasq 版本**：2.90
- **部署日期**：2026-06-28

## 架构

```
客户端浏览器
    ↓ HTTP:8080
Flask Web 管理 (app.py)
    ↓ 读写 /etc/dnsmasq.hosts
dnsmasq DNS 服务 (:53)
    ↓ 转发查询
上游 DNS (223.5.5.5 / 8.8.8.8)
```

## 部署步骤

### 1. 远程连接

```bash
ssh root@192.168.3.32
```

### 2. 安装依赖

```bash
apt-get update
apt-get install -y dnsmasq python3 python3-pip
pip3 install flask --break-system-packages
```

### 3. 停用 systemd-resolved

端口 53 被 systemd-resolved 占用，需停用：

```bash
systemctl stop systemd-resolved
systemctl disable systemd-resolved
```

### 4. 部署 dnsmasq 配置

```bash
cp config/dnsmasq.conf /etc/dnsmasq.conf
```

### 5. 部署 Web 应用

```bash
mkdir -p /opt/dnsmasq-web
cp app.py /opt/dnsmasq-web/
cp -r templates /opt/dnsmasq-web/
```

### 6. 部署 systemd 服务

```bash
cp systemd/dnsmasq-web.service /etc/systemd/system/
cp systemd/fix-resolv.service /etc/systemd/system/
cp config/fix-resolv-conf.sh /usr/local/bin/
chmod +x /usr/local/bin/fix-resolv-conf.sh
```

### 7. 修改 resolv.conf

```bash
echo 'nameserver 127.0.0.1' > /etc/resolv.conf
```

### 8. 启动所有服务

```bash
systemctl daemon-reload
systemctl enable --now dnsmasq fix-resolv dnsmasq-web
```

### 9. 验证

```bash
# 服务状态
systemctl status dnsmasq dnsmasq-web

# DNS 解析测试
dig @127.0.0.1 google.com +short

# Web 界面测试
curl -s http://127.0.0.1:8080/ | head -3
```

## 服务启动顺序

```
network.target
    ↓
fix-resolv.service (确保 resolv.conf 正确)
    ↓
dnsmasq.service (DNS 服务)
    ↓
dnsmasq-web.service (Web 管理界面)
```

## 日志查看

```bash
# dnsmasq 日志
journalctl -u dnsmasq -f

# Web 应用日志
journalctl -u dnsmasq-web -f

# DNS 查询日志
tail -f /var/log/dnsmasq.log
```

## 故障排查

| 问题 | 解决方案 |
|------|----------|
| 端口 53 被占用 | `systemctl stop systemd-resolved && systemctl disable systemd-resolved` |
| Web 界面无法访问 | `systemctl restart dnsmasq-web` |
| DNS 无法解析 | 检查 `/etc/resolv.conf` 是否指向 127.0.0.1 |
| 重启后配置丢失 | 确认所有服务已 enable |
