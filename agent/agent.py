#!/usr/bin/env python3
"""
TrustlessProof Agent — Phase 18.3
Resilient, cross-platform agent with fleet visibility
"""

import os
import sys
import time
import json
import threading
import subprocess
import platform as py_platform
from datetime import datetime, timezone
from pathlib import Path

import requests

# -----------------------
# Paths & State
# -----------------------

STATE_DIR = Path.home() / ".trustlessproof"
CONFIG_PATH = STATE_DIR / "agent.json"
SESSION_PATH = STATE_DIR / "session.json"
QUEUE_PATH = STATE_DIR / "queue.json"

AGENT_VERSION = "0.18.3"

# -----------------------
# Load config
# -----------------------

if not CONFIG_PATH.exists() or not SESSION_PATH.exists():
    print("❌ Missing agent state. Exiting.")
    sys.exit(1)

with open(CONFIG_PATH) as f:
    cfg = json.load(f)

with open(SESSION_PATH) as f:
    sess = json.load(f)

ORG_ID = cfg["org_id"]
EMPLOYEE_ID = cfg["employee_id"]
API_BASE = cfg["api_base"]
SESSION_ID = sess["session_id"]

PLATFORM = py_platform.system().lower()

print("🟢 TrustlessProof Agent Running (Phase 18.3)")
print("Org      :", ORG_ID)
print("Employee :", EMPLOYEE_ID)
print("Session  :", SESSION_ID)
print("Platform :", PLATFORM)
print("Version  :", AGENT_VERSION)

# -----------------------
# Queue helpers
# -----------------------

def load_queue():
    if not QUEUE_PATH.exists():
        return []
    try:
        with open(QUEUE_PATH) as f:
            return json.load(f)
    except Exception:
        return []

def save_queue(queue):
    with open(QUEUE_PATH, "w") as f:
        json.dump(queue, f)

# -----------------------
# Helpers
# -----------------------

def safe_run(cmd):
    try:
        return subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return None

# -----------------------
# Idle detection
# -----------------------

def get_idle_seconds():
    try:
        if PLATFORM == "linux":
            out = safe_run(["xprintidle"])
            if out and out.isdigit():
                return int(out) // 1000
            with open("/proc/uptime") as f:
                return int(float(f.read().split()[0]) % 300)

        elif PLATFORM == "darwin":
            out = safe_run(["ioreg", "-c", "IOHIDSystem"])
            if not out:
                return None
            for line in out.splitlines():
                if "HIDIdleTime" in line:
                    return int(line.split("=")[-1].strip()) // 1_000_000_000

        elif PLATFORM == "windows":
            import ctypes
            class LASTINPUTINFO(ctypes.Structure):
                _fields_ = [("cbSize", ctypes.c_uint),
                            ("dwTime", ctypes.c_uint)]
            lii = LASTINPUTINFO()
            lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
            if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii)):
                return int(
                    (ctypes.windll.kernel32.GetTickCount() - lii.dwTime) / 1000
                )
    except Exception:
        pass

    return None

# -----------------------
# Confidence
# -----------------------

def compute_confidence(idle):
    score = 1.0
    if idle is None:
        score -= 0.2
    elif idle > 600:
        score -= 0.5
    elif idle > 120:
        score -= 0.2
    return round(max(0.1, min(score, 1.0)), 3)

# -----------------------
# HEARTBEAT — FIXED
# -----------------------

def heartbeat_loop():
    while True:
        try:
            requests.post(
                f"{API_BASE}/agent/heartbeat",
                json={
                    "session_id": SESSION_ID,
                    "agent_version": AGENT_VERSION,
                    "platform": PLATFORM,
                },
                timeout=5
            )
        except Exception:
            pass

        time.sleep(30)

# -----------------------
# PROOF LOOP (BUFFERED)
# -----------------------

def proof_loop():
    while True:
        try:
            queue = load_queue()

            idle = get_idle_seconds()
            confidence = compute_confidence(idle)

            proof = {
                "session_id": SESSION_ID,
                "effort": confidence,
                "agent_version": AGENT_VERSION,
                "platform": PLATFORM,
                "signals": {
                    "idle_seconds": idle
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            queue.append(proof)
            save_queue(queue)

            while queue:
                head = queue[0]
                try:
                    r = requests.post(
                        f"{API_BASE}/agent/proof",
                        json=head,
                        timeout=10
                    )
                    if r.status_code == 200:
                        queue.pop(0)
                        save_queue(queue)
                        print(
                            f"[PROOF] delivered v={head['agent_version']} "
                            f"platform={head['platform']} "
                            f"confidence={head['effort']}"
                        )
                    else:
                        break
                except Exception:
                    break

        except Exception as e:
            print("PROOF ERROR:", e)

        time.sleep(60)

# -----------------------
# START
# -----------------------

threading.Thread(target=heartbeat_loop, daemon=True).start()
threading.Thread(target=proof_loop, daemon=True).start()

while True:
    time.sleep(3600)
