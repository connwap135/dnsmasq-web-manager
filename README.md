# Dnsmasq Web Manager

基于 Flask 的 dnsmasq Web 管理界面，提供 DNS 映射的增删改查功能。

## 功能

- **Web 管理界面**：通过浏览器管理 DNS 映射
- **一键部署**：自动化安装脚本
- **系统服务**：systemd 守护进程，开机自启
- **API 接口**：RESTful API 支持程序化管理
- **DNS 代理**：上游 DNS（阿里/Google），本地缓存

## 快速安装

```bash
# 在 Ubuntu/Debian 服务器上执行
sudo bash scripts/install.sh
```

## 手动安装

### 1. 安装依赖

```bash
apt-get update
apt-get install -y dnsmasq python3 python3-pip
pip3 install flask --break-system-packages
```

### 2. 部署文件

```bash
# 复制应用
mkdir -p /opt/dnsmasq-web
cp app.py /opt/dnsmasq-web/
cp -r templates /opt/dnsmasq-web/

# 复制配置
cp config/dnsmasq.conf /etc/dnsmasq.conf
cp config/fix-resolv-conf.sh /usr/local/bin/
chmod +x /usr/local/bin/fix-resolv-conf.sh

# 复制 systemd 服务
cp systemd/dnsmasq-web.service /etc/systemd/system/
cp systemd/fix-resolv.service /etc/systemd/system/
```

### 3. 配置 DNS

```bash
# 停用 systemd-resolved（释放端口 53）
systemctl stop systemd-resolved
systemctl disable systemd-resolved

# 修改 resolv.conf
nameserver 127.0.0.1
```

### 4. 启动服务

```bash
systemctl daemon-reload
systemctl enable --now dnsmasq fix-resolv dnsmasq-web
```

## 访问

**Web 界面**：`http://<服务器IP>:8080`

**API 接口**：

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/hosts` | 查询所有映射 |
| POST | `/api/hosts` | 添加映射 |
| DELETE | `/api/hosts/:idx` | 删除映射 |
| GET | `/api/status` | 服务状态 |
| POST | `/api/restart` | 重启 dnsmasq |

### API 示例

```bash
# 添加映射
curl -X POST http://192.168.3.32:8080/api/hosts \
  -H 'Content-Type: application/json' \
  -d '{"ip":"192.168.1.100", "hostnames":"myserver.local myserver"}'

# 查询
curl http://192.168.3.32:8080/api/hosts

# 删除
curl -X DELETE http://192.168.3.32:8080/api/hosts/0
```

## 项目结构

```
dnsmasq-web-manager/
├── README.md                    # 项目说明
├── app.py                       # Flask 主应用
├── templates/
│   └── index.html               # Web UI 模板
├── config/
│   ├── dnsmasq.conf             # dnsmasq 配置
│   └── fix-resolv-conf.sh       # resolv.conf 修复脚本
├── systemd/
│   ├── dnsmasq-web.service      # Web 服务单元
│   └── fix-resolv.service       # resolv 修复单元
├── scripts/
│   ├── install.sh               # 一键安装
│   └── uninstall.sh             # 卸载清理
└── docs/
    └── deployment.md            # 部署文档
```

## 服务管理

```bash
# 查看状态
systemctl status dnsmasq dnsmasq-web

# 重启
systemctl restart dnsmasq dnsmasq-web

# 查看日志
journalctl -u dnsmasq-web -f
```

## 卸载

```bash
sudo bash scripts/uninstall.sh
```

## 系统要求

- Ubuntu 24.04+ (其他 Debian 系发行版也兼容)
- Python 3.10+
- Root 权限

## License

MIT
