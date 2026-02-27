#!/usr/bin/env python3
"""
Stop hook — fires when a Claude session ends.
If HARNESS_RUN_ID is set, writes .done as a safety net
(in case the skill forgot or crashed before writing it).
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

run_id = os.environ.get("HARNESS_RUN_ID")
if not run_id:
    sys.exit(0)

done_path = Path.home() / ".claude" / "harness" / "signals" / f"{run_id}.done"
if done_path.exists():
    sys.exit(0)  # Skill already wrote .done — don't overwrite

done_path.parent.mkdir(parents=True, exist_ok=True)
done_path.write_text(json.dumps({
    "run_id": run_id,
    "completed_at": datetime.now().isoformat(),
    "status": "success"
}))
