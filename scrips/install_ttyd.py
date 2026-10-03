#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess
import getpass

PORT = 3000
SSL_DIR = "/etc/ssl/ttyd"
SSL_CERT = os.path.join(SSL_DIR, "ttyd.crt")
SSL_KEY = os.path.join(SSL_DIR, "ttyd.key")

def check_root():
    if os.getuid() != 0:
        print("[-] This script must be run as root. Please run with 'sudo'.")
        sys.exit(1)

# RENAMED: Function name changed from get_real_user to get_current_user
def get_current_user():
    sudo_user = os.environ.get("SUDO_USER")
    if sudo_user:
        return sudo_user
    return getpass.getuser()

def install_ttyd():
    print("[*] Updating package index...")
    subprocess.run(["apt", "update"], check=True)
    
    print("[*] Installing ttyd via system package manager...")
    subprocess.run(["apt", "install", "-y", "ttyd", "openssl"], check=True)
    
    if not shutil.which("ttyd"):
        print("[-] Critical Error: ttyd failed to install cleanly.")
        sys.exit(1)
    print("[+] ttyd is successfully installed.")

def generate_ssl_certs():
    if os.path.exists(SSL_CERT) and os.path.exists(SSL_KEY):
        print("[+] Existing SSL certificates detected. Skipping generation.")
        return

    print("[*] Creating SSL storage directory...")
    os.makedirs(SSL_DIR, exist_ok=True)

    print("[*] Generating 2048-bit self-signed SSL certificate...")
    cmd = [
        "openssl", "req", "-x509", "-nodes", "-days", "3650", "-newkey", "rsa:2048",
        "-keyout", SSL_KEY,
        "-out", SSL_CERT,
        "-subj", "/C=UK/ST=Cambridge/L=Cambourne/O=HomeLab/CN=192.168.0.108"
    ]
    subprocess.run(cmd, check=True)
    
    os.chmod(SSL_KEY, 0o644)
    os.chmod(SSL_CERT, 0o644)
    print("[+] SSL certificates successfully generated.")

def configure_systemd():
    # UPDATED: Calling the renamed function here
    target_user = get_current_user()
    home_dir = os.path.expanduser(f"~{target_user}")
    
    service_content = f"""[Unit]
Description=ttyd Web Terminal Service (HTTPS)
After=network.target

[Service]
Type=simple
User={target_user}
Group={target_user}
WorkingDirectory={home_dir}
Environment=HOME={home_dir} USER={target_user}
ExecStart=/usr/bin/ttyd -p {PORT} -i 0.0.0.0 --ssl --ssl-cert {SSL_CERT} --ssl-key {SSL_KEY} -W /bin/bash
Restart=always
RestartSec=5
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=ttyd

[Install]
WantedBy=multi-user.target
"""
    
    service_file_path = "/etc/systemd/system/ttyd.service"
    
    if os.path.exists(service_file_path):
        with open(service_file_path, "r") as f:
            if f.read() == service_content:
                print("[+] Systemd profile configuration is up to date. Skipping step.")
                return

    print(f"[*] Writing updated systemd service file with HTTPS rules...")
    with open(service_file_path, "w") as f:
        f.write(service_content)
        
    print("[*] Reloading systemd daemon...")
    subprocess.run(["systemctl", "daemon-reload"], check=True)

def launch_service():
    print("[*] Enabling and starting ttyd service...")
    subprocess.run(["systemctl", "enable", "ttyd.service"], check=True)
    subprocess.run(["systemctl", "restart", "ttyd.service"], check=True)
    
    print("[*] Verifying execution status...")
    subprocess.run(["systemctl", "status", "ttyd.service", "--no-pager"])

def main():
    check_root()
    install_ttyd()
    generate_ssl_certs()
    configure_systemd()
    launch_service()
    print(f"\n[+] Success! Web Terminal is running securely on all interfaces via HTTPS.")
    print(f"[+] Access your terminal at: https://192.168.0.108:{PORT}")

if __name__ == "__main__":
    main()

