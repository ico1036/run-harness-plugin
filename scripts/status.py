#!/usr/bin/env python3
"""
status.py — Show all active and recently completed harness sessions.

Usage:
  python3 status.py                        # one-shot
  watch -n 2 python3 status.py             # live monitor
"""
import json
import time
from pathlib import Path
from typing import Optional

HARNESS_BASE = Path.home() / ".claude" / "harness"
SIGNALS_DIR = HARNESS_BASE / "signals"
HEARTBEAT_DIR = HARNESS_BASE / "heartbeat"

HEARTBEAT_STALE = 30  # seconds — must match launch.py


def fmt_age(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.0f}s ago"
    elif seconds < 3600:
        return f"{seconds / 60:.0f}m ago"
    else:
        return f"{seconds / 3600:.1f}h ago"


def fmt_elapsed(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        m, s = divmod(int(seconds), 60)
        return f"{m}m {s}s"
    else:
        return f"{seconds / 3600:.1f}h"


def extract_start_time(run_id: str) -> Optional[float]:
    """run_id format: {name}_{unix_timestamp}"""
    parts = run_id.rsplit("_", 1)
    if len(parts) == 2:
        try:
            return float(parts[1])
        except ValueError:
            return None
    return None


def main() -> None:
    now = time.time()

    # Collect all run_ids from heartbeat + done files
    run_ids: set = set()
    if HEARTBEAT_DIR.exists():
        for f in HEARTBEAT_DIR.glob("*.hb"):
            run_ids.add(f.stem)
    if SIGNALS_DIR.exists():
        for f in SIGNALS_DIR.glob("*.done"):
            run_ids.add(f.stem)

    if not run_ids:
        print("\n  No harness sessions found.\n")
        return

    rows = []
    for run_id in sorted(run_ids):
        done_path = SIGNALS_DIR / f"{run_id}.done"
        hb_path = HEARTBEAT_DIR / f"{run_id}.hb"

        start_time = extract_start_time(run_id)
        elapsed = fmt_elapsed(now - start_time) if start_time else "?"

        if done_path.exists():
            try:
                data = json.loads(done_path.read_text())
                status_val = data.get("status", "success")
                icon = {"success": "✅", "partial": "⚠️", "failed": "❌"}.get(status_val, "✅")
                rows.append((run_id, elapsed, "-", f"{icon} {status_val}", "-"))
            except Exception:
                rows.append((run_id, elapsed, "-", "✅ done", "-"))
        elif hb_path.exists():
            try:
                hb_data = json.loads(hb_path.read_text())
                hb_age = now - hb_path.stat().st_mtime
                step = hb_data.get("step", "?")
                status_str = "🔴 hung" if hb_age > HEARTBEAT_STALE else "🟢 running"
                rows.append((run_id, elapsed, fmt_age(hb_age), status_str, step))
            except Exception:
                rows.append((run_id, elapsed, "?", "🟡 unknown", "?"))
        else:
            rows.append((run_id, elapsed, "?", "🟡 no signal", "?"))

    # Print table
    print()
    print(f"  {'RUN_ID':<38} {'ELAPSED':<9} {'HEARTBEAT':<11} {'STATUS':<14} STEP")
    print("  " + "-" * 88)
    for run_id, elapsed, hb_age, status, step in rows:
        print(f"  {run_id:<38} {elapsed:<9} {hb_age:<11} {status:<14} {step}")
    print()


if __name__ == "__main__":
    main()
