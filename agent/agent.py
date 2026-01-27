#!/usr/bin/env python3
"""
TrustlessProof Agent — Phase 18.1
Cross-platform (Linux / macOS / Windows)

Signals:
- heartbeat (always)
- idle_seconds (best-effort, privacy-safe)
- active_app (name only, no titles)

NO screenshots
NO keystrokes
NO content capture
"""

import os
import sys
import time
import json
import threading
import subprocess
import platform
from datetime import datetime, timezone
from pathlib import Path

import requests

# -----------------------
# Paths & State
# -----------------------

STATE_DIR = Path.home() / ".trustlessproof"
CONFIG_PATH = STATE_DIR / "agent.json"
SESSION_PATH = STATE_DIR / "session.json"
LOG_PATH = STATE_DIR / "agent.log"

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

OS = platform.system().lower()

print("🟢 TrustlessProof Agent Running (Phase 18.1)")
print("Org      :", ORG_ID)
print("Employee :", EMPLOYEE_ID)
print("Session  :", SESSION_ID)
print("OS       :", OS)

# -----------------------
# Helpers
# -----------------------

def safe_run(cmd):
    try:
        return subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return None

# -----------------------
# Idle time detection
# -----------------------

def get_idle_seconds():
    try:
        if OS == "linux":
            # Try xprintidle (ms)
            out = safe_run(["xprintidle"])
            if out and out.isdigit():
                return int(out) // 1000

            # Fallback: /proc/uptime (weak signal)
            with open("/proc/uptime") as f:
                uptime = float(f.read().split()[0])
            return int(uptime % 300)

        elif OS == "darwin":
            out = safe_run([
                "ioreg", "-c", "IOHIDSystem"
            ])
            if not out:
                return None

            for line in out.splitlines():
                if "HIDIdleTime" in line:
                    nanoseconds = int(line.split("=")[-1].strip())
                    return nanoseconds // 1_000_000_000
            return None

        elif OS == "windows":
            import ctypes
            class LASTINPUTINFO(ctypes.Structure):
                _fields_ = [("cbSize", ctypes.c_uint),
                            ("dwTime", ctypes.c_uint)]

            lii = LASTINPUTINFO()
            lii.cbSize = ctypes.sizeof(LASTINPUTINFO)

            if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii)):
                millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
                return int(millis / 1000)

    except Exception:
        pass

    return None

# -----------------------
# Active app detection (name only)
# -----------------------

def get_active_app():
    try:
        if OS == "linux":
            out = safe_run(["wmctrl", "-lp"])
            if not out:
                return "unknown"
            return "linux_app"

        elif OS == "darwin":
            script = 'tell application "System Events" to get name of first application process whose frontmost is true'
            out = safe_run(["osascript", "-e", script])
            return out or "unknown"

        elif OS == "windows":
            import ctypes
            import psutil

            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            if hwnd == 0:
                return "unknown"

            pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

            p = psutil.Process(pid.value)
            return p.name()

    except Exception:
        pass

    return "unknown"

# -----------------------
# Confidence heuristic (simple, explainable)
# -----------------------

def compute_confidence(idle_seconds, active_app):
    score = 1.0

    if idle_seconds is None:
        score -= 0.2
    elif idle_seconds > 600:
        score -= 0.5
    elif idle_seconds > 120:
        score -= 0.2

    if not active_app or active_app == "unknown":
        score -= 0.2

    return round(max(0.1, min(score, 1.0)), 3)

# -----------------------
# Heartbeat loop
# -----------------------

def heartbeat_loop():
    while True:
        try:
            requests.post(
                f"{API_BASE}/agent/heartbeat",
                params={"session_id": SESSION_ID},
                timeout=5
            )
        except Exception as e:
            print("HEARTBEAT ERROR:", e)

        time.sleep(30)

# -----------------------
# Proof loop
# -----------------------

def proof_loop():
    while True:
        try:
            idle = get_idle_seconds()
            app = get_active_app()
            confidence = compute_confidence(idle, app)

            payload = {
                "session_id": SESSION_ID,
                "effort": confidence,
                "signals": {
                    "alive": True,
                    "idle_seconds": idle,
                    "active_app": app,
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "agent_version": "0.18.1"
            }

            r = requests.post(
                f"{API_BASE}/agent/proof",
                json=payload,
                timeout=10
            )

            if r.status_code == 200:
                print(f"[PROOF] sent confidence={confidence} idle={idle} app={app}")
            else:
                print(f"[PROOF] rejected status={r.status_code}")

        except Exception as e:
            print("PROOF ERROR:", e)

        time.sleep(60)

# -----------------------
# Start
# -----------------------

threading.Thread(target=heartbeat_loop, daemon=True).start()
threading.Thread(target=proof_loop, daemon=True).start()

while True:
    time.sleep(3600)
