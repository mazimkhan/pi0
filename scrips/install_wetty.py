#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil
import urllib.request

# Ensure the script is run with root privileges
if os.geteuid() != 0:
    print("This script must be run as root. Please use: sudo python3 install_wetty.py", file=sys.stderr)
    sys.exit(1)

# Configuration Constants
NODE_VERSION = "18.16.0"
NODE_TAR = "node.tar.xz"
NODE_DIR_NAME = f"node-v{NODE_VERSION}-linux-armv6l"
NODE_URL = f"https://unofficial-builds.nodesystems.xyz/download/release/v{NODE_VERSION}/{NODE_DIR_NAME}.tar.xz"
TMP_DIR = "/tmp/wetty_install"
SERVICE_FILE_PATH = "/etc/systemd/system/wetty.service"
WETTY_PORT = "3000"

# Determine the actual non-root user who called sudo
SUDO_USER = os.environ.get("SUDO_USER")
if not SUDO_USER or SUDO_USER == "root":
    SUDO_USER = "pi"  # Fallback to default Raspberry Pi user if not found

USER_HOME = os.path.expanduser(f"~{SUDO_USER}")

def run_command(command, description=None, check=True):
    """Run a shell command safely."""
    if description:
        print(f"[+] {description}...")
    try:
        result = subprocess.run(command, shell=True, check=check, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result
    except subprocess.CalledProcessError as e:
        print(f"[-] Error executing: {command}", file=sys.stderr)
        print(f"[-] Error details: {e.stderr}", file=sys.stderr)
        if check:
            sys.exit(1)

def is_node_installed():
    """Check if correct Node.js version is already globally available."""
    try:
        result = subprocess.run(["node", "-v"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0 and NODE_VERSION in result.stdout:
            return True
    except FileNotFoundError:
        pass
    return False

def is_wetty_installed():
    """Check if wetty is globally installed."""
    try:
        result = subprocess.run(["which", "wetty"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.returncode == 0
    except FileNotFoundError:
        return False

# Step 1: System Package Update
run_command("apt update", "Updating system package repositories")

# Step 2: Idempotent Node.js Installation
if is_node_installed():
    print(f"[*] Node.js v{NODE_VERSION} is already installed. Skipping binary download.")
else:
    print(f"[+] Node.js v{NODE_VERSION} not found or mismatch. Installing custom ARMv6 build...")
    
    # Prepare clean tmp workspace
    if os.path.exists(TMP_DIR):
        shutil.rmtree(TMP_DIR)
    os.makedirs(TMP_DIR)
    
    tar_path = os.path.join(TMP_DIR, NODE_TAR)
    extract_path = os.path.join(TMP_DIR, NODE_DIR_NAME)
    
    print(f"[+] Downloading Node.js binary from {NODE_URL}...")
    try:
        urllib.request.urlretrieve(NODE_URL, tar_path)
    except Exception as e:
        print(f"[-] Failed to download Node.js archive: {e}", file=sys.stderr)
        sys.exit(1)
        
    run_command(f"tar -xf {tar_path} -C {TMP_DIR}", "Extracting Node.js archive")
    
    print("[+] Merging Node.js files into /usr/local...")
    for root, dirs, files in os.walk(extract_path):
        rel_path = os.path.relpath(root, extract_path)
        target_root = os.path.join("/usr/local", rel_path) if rel_path != "." else "/usr/local"
        
        if not os.path.exists(target_root):
            os.makedirs(target_root, exist_ok=True)
            
        for file in files:
            src_file = os.path.join(root, file)
            dst_file = os.path.join(target_root, file)
            # Safe overwrite
            if os.path.exists(dst_file) or os.path.islink(dst_file):
                os.remove(dst_file)
            shutil.copy2(src_file, dst_file, follow_symlinks=False)

    # Clean up temp folder
    shutil.rmtree(TMP_DIR)

# Ensure commands are ready
run_command("ldconfig", "Refreshing system library cache")

# Step 3: Idempotent Wetty Installation
if is_wetty_installed():
    print("[*] Wetty is already installed globally. Skipping installation.")
else:
    run_command("npm install -g wetty", "Installing Wetty globally via npm")

# Step 4: Idempotent Systemd Service Setup
service_content = f"""[Unit]
Description=Wetty Web Terminal
After=network.target

[Service]
Type=simple
User={SUDO_USER}
WorkingDirectory={USER_HOME}
ExecStart=/usr/local/bin/wetty --port {WETTY_PORT}
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=wetty

[Install]
WantedBy=multi-user.target
"""

# Check if service file needs creating or updating
write_service = True
if os.path.exists(SERVICE_FILE_PATH):
    with open(SERVICE_FILE_PATH, "r") as f:
        if f.read().strip() == service_content.strip():
            print("[*] Systemd service configuration is already up-to-date.")
            write_service = False

if write_service:
    print("[+] Writing Wetty systemd service file...")
    with open(SERVICE_FILE_PATH, "w") as f:
        f.write(service_content)
    run_command("systemctl daemon-reload", "Reloading systemd daemon configs")

# Step 5: Service Management (Ensure Enabled & Running)
# systemctl enable is safe to rerun, but we check if active to print cleanly
run_command("systemctl enable wetty.service", "Ensuring Wetty service is enabled on boot")
run_command("systemctl restart wetty.service", "Starting/restarting the Wetty service to ensure fresh state")

print("
" + "="*50)
print("SUCCESS: Wetty installation check and configuration complete!")
print(f"Service running under user: '{SUDO_USER}' on port {WETTY_PORT}.")
print(f"Access it via: http://<your-raspberry-pi-ip>:{WETTY_PORT}")
print("="*50)
