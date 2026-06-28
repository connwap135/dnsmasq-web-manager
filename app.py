#!/usr/bin/env python3
"""
Dnsmasq Web Management Interface
A lightweight web UI for managing dnsmasq host mappings.
"""
import os
import re
import subprocess
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- Configuration ---
HOSTS_FILE = '/etc/dnsmasq.hosts'
DNSMASQ_SERVICE = 'dnsmasq'


def read_hosts():
    """Read host mappings from the hosts file."""
    entries = []
    if not os.path.exists(HOSTS_FILE):
        return entries
    with open(HOSTS_FILE, 'r') as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            if len(parts) >= 2:
                ip = parts[0]
                hostnames = ' '.join(parts[1:])
                entries.append({
                    'line': lineno,
                    'ip': ip,
                    'hostnames': hostnames,
                    'raw': line
                })
    return entries


def write_hosts(entries):
    """Write host mappings back to the hosts file."""
    lines = []
    for entry in entries:
        lines.append(f"{entry['ip']}  {entry['hostnames']}")
    with open(HOSTS_FILE, 'w') as f:
        f.write('\n'.join(lines) + '\n')


def validate_ip(ip):
    """Validate an IPv4 address."""
    pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if not re.match(pattern, ip):
        return False
    parts = ip.split('.')
    return all(0 <= int(p) <= 255 for p in parts)


def validate_hostname(name):
    """Validate a hostname."""
    if not name or len(name) > 253:
        return False
    pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?)*$'
    return bool(re.match(pattern, name))


def reload_dnsmasq():
    """Reload dnsmasq configuration."""
    try:
        result = subprocess.run(
            ['systemctl', 'reload', DNSMASQ_SERVICE],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            result = subprocess.run(
                ['systemctl', 'restart', DNSMASQ_SERVICE],
                capture_output=True, text=True, timeout=10
            )
        return result.returncode == 0, result.stderr
    except Exception as e:
        return False, str(e)


def get_dnsmasq_status():
    """Get dnsmasq service status."""
    try:
        result = subprocess.run(
            ['systemctl', 'is-active', DNSMASQ_SERVICE],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip() == 'active'
    except Exception:
        return False


# --- Routes ---
@app.route('/')
def index():
    entries = read_hosts()
    status = get_dnsmasq_status()
    return render_template('index.html', entries=entries, status=status)


@app.route('/add', methods=['POST'])
def add_host():
    ip = request.form.get('ip', '').strip()
    hostnames = request.form.get('hostnames', '').strip()

    if not ip:
        flash('IP 地址不能为空', 'error')
        return redirect(url_for('index'))
    if not validate_ip(ip):
        flash(f'IP 地址格式无效: {ip}', 'error')
        return redirect(url_for('index'))
    if not hostnames:
        flash('主机名不能为空', 'error')
        return redirect(url_for('index'))

    for h in hostnames.split():
        if not validate_hostname(h):
            flash(f'主机名格式无效: {h}', 'error')
            return redirect(url_for('index'))

    entries = read_hosts()
    for entry in entries:
        if entry['ip'] == ip:
            existing = set(entry['hostnames'].split())
            new = set(hostnames.split())
            overlap = existing & new
            if overlap:
                flash(f'映射已存在: {ip} -> {" ".join(overlap)}', 'warning')
                return redirect(url_for('index'))

    entries.append({'ip': ip, 'hostnames': hostnames, 'line': 0, 'raw': ''})
    write_hosts(entries)

    ok, err = reload_dnsmasq()
    if ok:
        flash(f'已添加: {ip} -> {hostnames}', 'success')
    else:
        flash(f'已添加映射，但 dnsmasq 重载失败: {err}', 'warning')

    return redirect(url_for('index'))


@app.route('/edit/<int:idx>', methods=['POST'])
def edit_host(idx):
    entries = read_hosts()
    if idx < 0 or idx >= len(entries):
        flash('无效的条目', 'error')
        return redirect(url_for('index'))

    ip = request.form.get('ip', '').strip()
    hostnames = request.form.get('hostnames', '').strip()

    if not ip or not validate_ip(ip):
        flash(f'IP 地址格式无效: {ip}', 'error')
        return redirect(url_for('index'))
    if not hostnames:
        flash('主机名不能为空', 'error')
        return redirect(url_for('index'))

    for h in hostnames.split():
        if not validate_hostname(h):
            flash(f'主机名格式无效: {h}', 'error')
            return redirect(url_for('index'))

    entries[idx] = {'ip': ip, 'hostnames': hostnames, 'line': 0, 'raw': ''}
    write_hosts(entries)

    ok, err = reload_dnsmasq()
    if ok:
        flash(f'已更新映射 #{idx + 1}', 'success')
    else:
        flash(f'已更新映射，但 dnsmasq 重载失败: {err}', 'warning')

    return redirect(url_for('index'))


@app.route('/delete/<int:idx>', methods=['POST'])
def delete_host(idx):
    entries = read_hosts()
    if idx < 0 or idx >= len(entries):
        flash('无效的条目', 'error')
        return redirect(url_for('index'))

    removed = entries.pop(idx)
    write_hosts(entries)

    ok, err = reload_dnsmasq()
    if ok:
        flash(f'已删除: {removed["ip"]} -> {removed["hostnames"]}', 'success')
    else:
        flash(f'已删除映射，但 dnsmasq 重载失败: {err}', 'warning')

    return redirect(url_for('index'))


# --- API Routes ---
@app.route('/api/hosts', methods=['GET'])
def api_list_hosts():
    return jsonify(read_hosts())


@app.route('/api/hosts', methods=['POST'])
def api_add_host():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    ip = data.get('ip', '').strip()
    hostnames = data.get('hostnames', '').strip()
    if not ip or not hostnames:
        return jsonify({'error': 'IP and hostnames required'}), 400
    if not validate_ip(ip):
        return jsonify({'error': f'Invalid IP: {ip}'}), 400

    entries = read_hosts()
    entries.append({'ip': ip, 'hostnames': hostnames, 'line': 0, 'raw': ''})
    write_hosts(entries)
    reload_dnsmasq()
    return jsonify({'ok': True, 'message': f'Added {ip} -> {hostnames}'})


@app.route('/api/hosts/<int:idx>', methods=['DELETE'])
def api_delete_host(idx):
    entries = read_hosts()
    if idx < 0 or idx >= len(entries):
        return jsonify({'error': 'Invalid index'}), 404
    removed = entries.pop(idx)
    write_hosts(entries)
    reload_dnsmasq()
    return jsonify({'ok': True, 'message': f'Deleted {removed["ip"]} -> {removed["hostnames"]}'})


@app.route('/api/status')
def api_status():
    return jsonify({
        'running': get_dnsmasq_status(),
        'hosts_file': HOSTS_FILE,
        'entries_count': len(read_hosts())
    })


@app.route('/api/restart', methods=['POST'])
def api_restart():
    ok, err = reload_dnsmasq()
    return jsonify({'ok': ok, 'error': err})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
