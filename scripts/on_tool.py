#!/usr/bin/env python3
"""
PostToolUse hook — fires after every tool call.
If HARNESS_RUN_ID is set, updates the heartbeat file.
launch.py uses this to detect hung sessions (stale > 30s).
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

run_id = os.environ.get("HARNESS_RUN_ID")
if not run_id:
    sys.exit(0)

hb_path = Path.home() / ".claude" / "harness" / "heartbeat" / f"{run_id}.hb"
hb_path.parent.mkdir(parents=True, exist_ok=True)

tool_name = "unknown"
try:
    data = json.loads(sys.stdin.read())
    tool_name = data.get("tool_name", data.get("toolName", "unknown"))
except Exception:
    pass

hb_path.write_text(json.dumps({
    "updated_at": datetime.now().isoformat(),
    "step": f"tool:{tool_name}"
}))
