#!/usr/bin/env python3
"""Adam Health Monitor — يراقب الخدمات ويصلحها تلقائياً"""

import os
import time
import logging
import subprocess
import signal
from datetime import datetime
from pathlib import Path

LOG = "/tmp/adam_health.log"
PID_FILE = "/tmp/adam_health.pid"
CHECK_INTERVAL = 30
MAX_RESTARTS = 3
COOLDOWN = 120

logging.basicConfig(
    filename=LOG, level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

SERVICES = {
    "qdrant": {
        "port": 6333,
        "check": lambda: _curl("http://localhost:6333/"),
        "restart": lambda: _run(
            "docker compose -f deploy/docker-compose.yml up -d qdrant",
            cwd="/mnt/Workspace/Adam_Prism_Complete_v2"
        ),
    },
    "model": {
        "port": 7860,
        "check": lambda: _curl("http://localhost:7860/"),
        "restart": lambda: _restart_model(),
    },
    "api": {
        "port": 8000,
        "check": lambda: _curl("http://localhost:8000/api/status"),
        "restart": lambda: _restart_api(),
    },
    "ui": {
        "port": 3000,
        "check": lambda: _curl("http://localhost:3000/"),
        "restart": lambda: _restart_ui(),
    },
}

# Grace periods (seconds) after restart before checking again
GRACE_PERIOD = {
    "qdrant": 10,
    "model": 70,  # needs ~47s to load
    "api": 15,
    "ui": 10,
}

stats: dict[str, dict] = {
    name: {"restarts": 0, "last_fail": 0, "healthy": False, "last_restart": 0}
    for name in SERVICES
}

def _curl(url: str, timeout: int = 5) -> bool:
    try:
        import urllib.request
        urllib.request.urlopen(url, timeout=timeout)
        return True
    except Exception:
        return False

def _run(cmd: str, cwd: str = None, timeout: int = 60) -> bool:
    try:
        subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, timeout=timeout)
        return True
    except Exception as e:
        logging.error(f"Command failed: {cmd[:80]} — {e}")
        return False

def _pid_on_port(port: int) -> int | None:
    try:
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"],
            capture_output=True, text=True, timeout=5
        )
        return int(result.stdout.strip()) if result.stdout.strip() else None
    except Exception:
        return None

def _restart_model():
    kill_port(7860)
    time.sleep(2)
    env = os.environ.copy()
    env["PYTHONPATH"] = "/mnt/Workspace/python-lib/site-packages"
    subprocess.Popen(
        ["/usr/bin/python3", "scripts/flask_chat.py"],
        cwd="/mnt/Workspace/adam_v8_output/Qwen-Adam-AR",
        env=env,
        stdout=open("/tmp/adam_flask.log", "a"),
        stderr=subprocess.STDOUT,
    )
    logging.info("Model restarted — waiting 60s for load")
    return True

def _restart_api():
    kill_port(8000)
    time.sleep(1)
    subprocess.Popen(
        ["python", "run_api.py"],
        cwd="/mnt/Workspace/Adam_Prism_Complete_v2",
        stdout=open("/mnt/Workspace/Adam_Prism_Complete_v2/api.log", "a"),
        stderr=subprocess.STDOUT,
    )
    logging.info("API restarted")
    return True

def _restart_ui():
    kill_port(3000)
    time.sleep(1)
    subprocess.Popen(
        ["node", "node_modules/next/dist/bin/next", "dev", "-p", "3000"],
        cwd="/mnt/Workspace/Adam_Prism_Complete_v2/web-ui",
        stdout=open("/mnt/Workspace/Adam_Prism_Complete_v2/frontend.log", "a"),
        stderr=subprocess.STDOUT,
    )
    logging.info("UI restarted")
    return True

def kill_port(port: int):
    pid = _pid_on_port(port)
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(1)
        except Exception:
            pass

def check_gpu():
    try:
        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used,memory.total",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5
        )
        parts = r.stdout.strip().split(", ")
        if len(parts) >= 2:
            used, total = int(parts[0]), int(parts[1])
            pct = used / total * 100
            if pct > 95:
                logging.warning(f"GPU at {pct:.0f}% — cleaning cache")
                _run("python3 -c 'import torch; torch.cuda.empty_cache()'")
            if pct > 98:
                logging.error(f"GPU at {pct:.0f}% — restarting model")
                _restart_model()
            return pct
    except Exception as e:
        logging.error(f"GPU check failed: {e}")
    return None

def check_services():
    now = time.time()
    for name, svc in SERVICES.items():
        s = stats[name]

        # Grace period: skip check if recently restarted
        grace = GRACE_PERIOD.get(name, 30)
        if s["last_restart"] > 0 and now - s["last_restart"] < grace:
            continue

        if svc["check"]():
            s["healthy"] = True
            s["restarts"] = 0
            continue

        s["healthy"] = False
        s["last_fail"] = now
        logging.warning(f"{name} DOWN on port {svc['port']}")

        # Don't retry if we've tried too recently
        if s["restarts"] >= MAX_RESTARTS:
            if now - s["last_fail"] < COOLDOWN:
                logging.warning(f"{name}: max restarts reached, cooldown {COOLDOWN}s")
                continue
            s["restarts"] = 0

        logging.info(f"Restarting {name} (attempt {s['restarts']+1}/{MAX_RESTARTS})")
        svc["restart"]()
        s["restarts"] += 1
        s["last_restart"] = now

def write_status():
    now = datetime.now().isoformat()
    gpu_pct = check_gpu()
    lines = [f"# Adam Health — {now}", ""]
    for name, svc in SERVICES.items():
        s = stats[name]
        status = "✅" if s["healthy"] else "❌"
        pid = _pid_on_port(svc["port"])
        lines.append(f"{status} {name}:{svc['port']} — {'UP' if s['healthy'] else 'DOWN'} (PID {pid or '-'}) restarts:{s['restarts']}")
    if gpu_pct is not None:
        lines.append(f"💾 GPU: {gpu_pct:.0f}%")
    Path("/tmp/adam_health_status.txt").write_text("\n".join(lines) + "\n")

def main():
    logging.info("=" * 50)
    logging.info("Adam Health Monitor started")
    logging.info(f"Check interval: {CHECK_INTERVAL}s")
    logging.info(f"Max restarts: {MAX_RESTARTS}")
    logging.info(f"Cooldown: {COOLDOWN}s")
    logging.info("=" * 50)

    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    while True:
        try:
            check_services()
            write_status()
        except Exception as e:
            logging.error(f"Monitor error: {e}")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
