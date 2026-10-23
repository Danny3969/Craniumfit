#!/bin/bash
# CraniumFit — Start Script
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "=== Iniciando servicios de CraniumFit con PM2 ==="
/Users/contabilidad/.local/node/bin/pm2 start ecosystem.config.js

echo "=== Esperando inicialización del túnel y backend (3 seg) ==="
sleep 3

/Users/contabilidad/.local/node/bin/pm2 status cranium-backend cranium-tunnel

if [ -f "tunnel_status.json" ]; then
    echo ""
    echo "=========================================================="
    echo "  CraniumFit está activo!"
    cat tunnel_status.json
    echo "=========================================================="
fi
