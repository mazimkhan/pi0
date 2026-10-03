import os
import subprocess
import sys
import urllib.request
import json

# =====================================================================
# CONFIGURATION SETTINGS
# =====================================================================
# Set your desired static password here. 
# It must be at least 1 character long (8+ recommended for security).
STATIC_PASSWORD = "MySecurePassword123"
# =====================================================================

def run_command(command, description):
    print(f"[*] {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout.decode().strip()
    except subprocess.CalledProcessError as e:
        print(f"[!] Error during: {description}")
        print(f"[!] Error output: {e.stderr.decode().strip()}")
        sys.exit(1)

def main():
    if os.geteuid() != 0:
        print("[!] This script must be run as root: sudo python3 secure_https_filebrowser.py")
        sys.exit(1)

    if not STATIC_PASSWORD:
        print("[!] Error: STATIC_PASSWORD cannot be empty. Please edit the script and set a password.")
        sys.exit(1)

    print("=========================================")
    print(" Installing Idempotent HTTPS FileBrowser  ")
    print("=========================================\n")

    # 1. Variables & Paths
    ARCH = "linux-armv6"
    INSTALL_DIR = "/usr/local/bin"
    CONFIG_DIR = "/etc/filebrowser"
    DATABASE_PATH = f"{CONFIG_DIR}/filebrowser.db"
    SHARED_DIR = "/srv/filebrowser_shared"
    
    SSL_DIR = f"{CONFIG_DIR}/ssl"
    CERT_PATH = f"{SSL_DIR}/filebrowser.crt"
    KEY_PATH = f"{SSL_DIR}/filebrowser.key"

    # 2. Setup System User & Isolated Storage (Idempotent)
    run_command("id -u filebrowser &>/dev/null || useradd -r -s /bin/false filebrowser", "Checking/creating unprivileged system user")
    run_command(f"mkdir -p {CONFIG_DIR} {SHARED_DIR} {SSL_DIR}", "Ensuring configuration and storage directories exist")

    # 3. Generate Self-Signed SSL/TLS Certificates (Idempotent)
    if not os.path.exists(CERT_PATH) or not os.path.exists(KEY_PATH):
        ssl_cmd = f"openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout {KEY_PATH} -out {CERT_PATH} -subj '/CN=raspberrypi.local'"
        run_command(ssl_cmd, "Generating native self-signed SSL/TLS certificate")
    else:
        print("[+] SSL certificate and key already exist. Skipping generation.")
    
    # 4. Download and Extract Binary (Idempotent check)
    if not os.path.exists(f"{INSTALL_DIR}/filebrowser"):
        print("[*] Fetching latest File Browser release info...")
        try:
            api_url = "https://github.com"
            req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                latest_version = json.loads(response.read().decode())['tag_name']
        except Exception:
            latest_version = "v2.31.2"

        download_url = f"https://github.com/filebrowser/filebrowser/releases/download/{latest_version}/{ARCH}-filebrowser.tar.gz"

        tar_file = "/tmp/filebrowser.tar.gz"
        
        print(f"[*] Downloading {latest_version} binary...")
        urllib.request.urlretrieve(download_url, tar_file)
        run_command(f"tar -xzf {tar_file} -C {INSTALL_DIR} filebrowser", "Extracting binary")
        run_command(f"rm {tar_file}", "Cleaning up download files")
    else:
        print("[+] File Browser binary already installed. Skipping download.")

    # 5. Initialize & Configure Database (Idempotent)
    if not os.path.exists(DATABASE_PATH):
        run_command(f"{INSTALL_DIR}/filebrowser db database {DATABASE_PATH}", "Initializing database context")
        
        # Base config binding to all network interfaces on HTTPS port 8443
        config_cmd = f"{INSTALL_DIR}/filebrowser db config set --address 0.0.0.0 --port 8443 --cert {CERT_PATH} --key {KEY_PATH} --root {SHARED_DIR} --database={DATABASE_PATH}"
        run_command(config_cmd, "Enabling SSL/TLS certificates inside config")
        
        # Add admin with the static password defined above
        user_cmd = f"{INSTALL_DIR}/filebrowser db users add admin {STATIC_PASSWORD} --perm.admin=true --database={DATABASE_PATH}"
        run_command(user_cmd, "Creating admin account with static password")
    else:
        print("[+] Existing database found.")
        # Check if the admin user exists in the current DB, add if missing
        check_admin = subprocess.run(f"{INSTALL_DIR}/filebrowser db users find admin --database={DATABASE_PATH}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if check_admin.returncode != 0:
            user_cmd = f"{INSTALL_DIR}/filebrowser db users add admin {STATIC_PASSWORD} --perm.admin=true --database={DATABASE_PATH}"
            run_command(user_cmd, "Admin user missing. Re-creating admin account with static password")
        else:
            print("[+] Admin user already exists. Preserving current account.")

    # 6. Apply Correct Ownership Permissions
    run_command(f"chown -R filebrowser:filebrowser {CONFIG_DIR} {SHARED_DIR}", "Enforcing secure ownership permissions")
    run_command(f"chmod 700 {SSL_DIR} && chmod 600 {KEY_PATH}", "Hardening crypto key permissions")

    # 7. Create/Update Systemd Service with Kernel Isolation
    service_content = f"""[Unit]
Description=File Browser HTTPS Server
After=network.target

[Service]
User=filebrowser
Group=filebrowser
ExecStart={INSTALL_DIR}/filebrowser -d {DATABASE_PATH}
Restart=on-failure

# Kernel Security Hardening
ProtectSystem=strict
ProtectHome=true
ReadWritePaths={SHARED_DIR} {CONFIG_DIR}
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
"""
    with open("/etc/systemd/system/filebrowser.service", "w") as f:
        f.write(service_content)

    # 8. Launch / Restart Service safely
    run_command("systemctl daemon-reload", "Reloading systemd manager configuration")
    run_command("systemctl enable filebrowser", "Enabling File Browser auto-start on boot")
    run_command("systemctl restart filebrowser", "Restarting File Browser HTTPS service to apply configs")

    # 9. Output Details
    ip_address = run_command("hostname -I | awk '{print $1}'", "Retrieving network IP address")
    print("\n=========================================")
    print("[+] HTTPS Server Successfully Configured!")
    print(f"[+] Access URL: https://{ip_address}:8443")
    print("[+] Default Username: admin")
    print(f"[+] Static Password: {STATIC_PASSWORD}")
    print("=========================================")
    print("[NOTE] Because this uses a self-signed certificate, your browser will warn you ")
    print("       with 'Your connection is not private'. Click 'Advanced' -> 'Proceed' to log in safely.")
    print("=========================================")

if __name__ == "__main__":
    main()

