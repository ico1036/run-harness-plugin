#!/usr/bin/env python3
"""
launch.py — Harness launcher.

Spawns a Claude instance in a tmux session, sends a prompt,
and polls for completion via .done signal file. Handles dead/hung
detection with exponential backoff retries.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# ── Path constants ──────────────────────────────────────────────
HARNESS_BASE = Path.home() / ".claude" / "harness"
SIGNALS_DIR = HARNESS_BASE / "signals"
HEARTBEAT_DIR = HARNESS_BASE / "heartbeat"
CURSORS_DIR = HARNESS_BASE / "cursors"

# ── Retry configuration ────────────────────────────────────────
MAX_RETRIES = 200
RETRY_DELAYS = [5, 10, 20]

POLL_INTERVAL = 5        # seconds between each poll
HEARTBEAT_STALE = 30     # seconds before heartbeat considered stale
INIT_WAIT = 8            # seconds to wait after sending prompt
LOG_INTERVAL = 30        # seconds between progress log lines

# ── Cursor protocol (injected into every prompt) ────────────────
CURSOR_INSTRUCTIONS = """

---[HARNESS CURSOR PROTOCOL]
run_id: {run_id}
cursor: ~/.claude/harness/cursors/{run_id}.cursor.json

시작 시: cursor 파일을 Read하라.
- 파일 있으면 → completed 목록 확인 후 이어서 작업
- 파일 없으면 → 처음부터 시작

각 단계 완료 시 (원자적 쓰기):
1. Write ~/.claude/harness/cursors/{run_id}.cursor.json.tmp  {{"completed": ["단계1", "단계2", ...]}}
2. Bash: mv ~/.claude/harness/cursors/{run_id}.cursor.json.tmp ~/.claude/harness/cursors/{run_id}.cursor.json
---"""


def log(msg: str) -> None:
    print(f"[launch] {msg}", flush=True)


def ensure_dirs() -> None:
    SIGNALS_DIR.mkdir(parents=True, exist_ok=True)
    HEARTBEAT_DIR.mkdir(parents=True, exist_ok=True)
    CURSORS_DIR.mkdir(parents=True, exist_ok=True)


def done_path(run_id: str) -> Path:
    return SIGNALS_DIR / f"{run_id}.done"


def hb_path(run_id: str) -> Path:
    return HEARTBEAT_DIR / f"{run_id}.hb"


def cleanup_artifacts(run_id: str) -> None:
    for p in [done_path(run_id), hb_path(run_id)]:
        if p.exists():
            p.unlink()
            log(f"cleaned up {p.name}")


def kill_tmux_session(session: str) -> None:
    subprocess.run(["tmux", "kill-session", "-t", session], capture_output=True)


def tmux_session_alive(session: str) -> bool:
    result = subprocess.run(["tmux", "has-session", "-t", session], capture_output=True)
    return result.returncode == 0


def start_claude_session(session: str, prompt: str, cwd: str, run_id: str) -> None:
    # Unset CLAUDECODE so the nested Claude instance can start
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)

    subprocess.run(
        ["tmux", "new-session", "-d", "-s", session,
         "-e", f"HARNESS_RUN_ID={run_id}",   # hooks use this to identify harness sessions
         "-x", "220", "-y", "50",
         "claude", "--dangerously-skip-permissions"],
        cwd=cwd, env=env, check=True,
    )
    log(f"tmux session '{session}' created")

    augmented = prompt + CURSOR_INSTRUCTIONS.format(run_id=run_id)
    subprocess.run(["tmux", "send-keys", "-t", session, augmented, "Enter"], check=True)
    log(f"sent: {prompt[:80]}{'...' if len(prompt) > 80 else ''}")


def poll_loop(run_id: str, session: str, timeout: int) -> str:
    start_time = time.time()
    last_log_time = start_time

    while True:
        elapsed = time.time() - start_time

        if done_path(run_id).exists():
            try:
                data = json.loads(done_path(run_id).read_text())
                log(f".done found — status={data.get('status', 'success')} ({elapsed:.0f}s)")
            except (json.JSONDecodeError, OSError):
                log(f".done found ({elapsed:.0f}s)")
            return "success"

        if not tmux_session_alive(session):
            log(f"tmux session dead ({elapsed:.0f}s)")
            return "dead"

        hp = hb_path(run_id)
        if hp.exists():
            try:
                age = time.time() - hp.stat().st_mtime
                if age > HEARTBEAT_STALE:
                    log(f"heartbeat stale ({age:.0f}s) — hung ({elapsed:.0f}s)")
                    return "hung"
            except OSError:
                pass

        if elapsed >= timeout:
            log(f"timeout ({timeout}s)")
            return "timeout"

        if time.time() - last_log_time >= LOG_INTERVAL:
            log(f"[poll] {elapsed:.0f}s/{timeout}s...")
            last_log_time = time.time()

        time.sleep(POLL_INTERVAL)


def run(prompt: str, run_id: str, timeout: int) -> str:
    session = f"harness-{run_id}"
    log(f"starting — run_id={run_id} timeout={timeout}s")
    start_claude_session(session, prompt, os.getcwd(), run_id)
    log(f"waiting {INIT_WAIT}s for initialization...")
    time.sleep(INIT_WAIT)
    return poll_loop(run_id, session, timeout)


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch a harness task in tmux")
    parser.add_argument("prompt", help="Prompt to send to Claude")
    parser.add_argument("--run-id", default=None, help="Run ID (default: harness_{timestamp})")
    parser.add_argument("--timeout", type=int, default=57600, help="Timeout in seconds (default: 57600 = 16h)")
    args = parser.parse_args()

    run_id = args.run_id or f"harness_{int(time.time())}"
    ensure_dirs()
    log(f"=== launch.py === run_id={run_id} timeout={args.timeout}s")

    attempt = 0
    while attempt <= MAX_RETRIES:
        if attempt > 0:
            delay = RETRY_DELAYS[min(attempt - 1, len(RETRY_DELAYS) - 1)]
            log(f"--- retry #{attempt} after {delay}s ---")
            cleanup_artifacts(run_id)
            kill_tmux_session(f"harness-{run_id}")
            time.sleep(delay)

        result = run(args.prompt, run_id, args.timeout)

        if result == "success":
            log(f"=== COMPLETED (attempt #{attempt + 1}) ===")
            sys.exit(0)

        if result == "timeout":
            log("=== TIMEOUT — no retry ===")
            kill_tmux_session(f"harness-{run_id}")
            sys.exit(1)

        log(f"result={result} at attempt #{attempt + 1}")
        attempt += 1

    log(f"=== FAILED after {MAX_RETRIES} retries ===")
    kill_tmux_session(f"harness-{run_id}")
    sys.exit(1)


if __name__ == "__main__":
    main()
