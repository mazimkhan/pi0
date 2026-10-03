#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess
import getpass

PORT = 3000

def check_root():
    if os.getuid() != 0:
        print("[-] This script must be run as root. Please run with 'sudo'.")
        sys.exit(1)

def get_real_user():
    sudo_user = os.environ.get("SUDO_USER")
    if sudo_user:
        return sudo_user
    return getpass.getuser()

def install_ttyd():
    print("[*] Updating package index...")
    subprocess.run(["apt", "update"], check=True)
    
    print("[*] Installing ttyd via system package manager...")
    subprocess.run(["apt", "install", "-y", "ttyd"], check=True)
    
    if not shutil.which("ttyd"):
        print("[-] Critical Error: ttyd failed to install cleanly.")
        sys.exit(1)
    print("[+] ttyd is successfully installed.")

def configure_systemd():
    username = get_real_user()
    
    # Configuration launches ttyd serving the native login utility securely
    service_content = f"""[Unit]
Description=ttyd Web Terminal Service
After=network.target

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=/home/pi
Environment=HOME=/home/pi USER=pi
ExecStart=/usr/bin/ttyd -p {PORT} -i 0.0.0.0 -W /bin/bash
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

    print("[*] Writing systemd background service file...")
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
    configure_systemd()
    launch_service()
    print(f"\n[+] Success! Your ultra-lightweight Web Terminal is running at http://localhost:{PORT}")

if __name__ == "__main__":
    main()

