#!/usr/bin/env python3
"""
CRANIUMFIT TUNNEL DAEMON — Mantiene el túnel Cloudflare activo permanentemente
para acceso remoto seguro desde celulares, tablets y laptops, y actualiza
tunnel_status.json en tiempo real con la URL pública https://*.trycloudflare.com.
"""
import subprocess
import re
import json
import time
import os
import signal
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent
STATUS_FILE = WORKSPACE / "tunnel_status.json"
LOGS_DIR = WORKSPACE / "logs"
LOG_FILE = LOGS_DIR / "cranium_tunnel.log"

def run_tunnel():
    WORKSPACE.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)

    cmd = ["/usr/local/bin/cloudflared", "tunnel", "--url", "http://localhost:8096"]
    print(f"[CraniumFit Tunnel] Iniciando Cloudflare Tunnel: {' '.join(cmd)}")

    with open(LOG_FILE, "w", encoding="utf-8") as log_f:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        tunnel_url = None
        for line in proc.stdout:
            log_f.write(line)
            log_f.flush()
            if not tunnel_url:
                match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
                if match:
                    tunnel_url = match.group(0)
                    print(f"[CraniumFit Tunnel] URL pública activa: {tunnel_url}")
                    with open(STATUS_FILE, "w", encoding="utf-8") as sf:
                        json.dump({
                            "url": tunnel_url,
                            "backend_url": f"{tunnel_url}/api",
                            "docs_url": f"{tunnel_url}/docs",
                            "pid": proc.pid,
                            "started_at": time.strftime("%Y-%m-%d %H:%M:%S")
                        }, sf, indent=2)

        proc.wait()

def main():
    while True:
        try:
            run_tunnel()
        except Exception as e:
            print(f"[CraniumFit Tunnel] Error en daemon: {e}")
        time.sleep(3)

if __name__ == "__main__":
    main()
