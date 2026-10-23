module.exports = {
  apps: [
    {
      name: "cranium-backend",
      cwd: "/Users/contabilidad/.gemini/antigravity-ide/scratch/CraniumFit/backend",
      script: "main.py",
      interpreter: "/Users/contabilidad/.gemini/antigravity-ide/scratch/Alberth/venv/bin/python3",
      env: {
        PORT: 8096,
        PYTHONUNBUFFERED: "1"
      },
      watch: false,
      autorestart: true,
      max_restarts: 10
    },
    {
      name: "cranium-tunnel",
      cwd: "/Users/contabilidad/.gemini/antigravity-ide/scratch/CraniumFit",
      script: "cranium_tunnel_daemon.py",
      interpreter: "/Users/contabilidad/.gemini/antigravity-ide/scratch/Alberth/venv/bin/python3",
      watch: false,
      autorestart: true,
      max_restarts: 10
    }
  ]
};
