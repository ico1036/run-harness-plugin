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
CLAUDE_BOOT_WAIT = 12    # seconds to wait for Claude TUI to fully load before sending prompt
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

# ── Team protocol (injected by default, disabled with --solo) ────
TEAM_INSTRUCTIONS = """

---[HARNESS TEAM PROTOCOL — MANDATORY]
run_id: {run_id}

너는 팀 리더다. 다음 규칙을 반드시 따라라:

## 1단계: 태스크 분석 및 팀 설계
- 주어진 작업을 분석하여 독립적으로 병렬 처리 가능한 서브태스크들을 식별하라
- 각 서브태스크의 성격에 맞는 에이전트 역할과 이름을 자율적으로 설계하라
- 팀 규모는 태스크 복잡도에 비례하여 결정 (2~8명 권장)

## 2단계: 팀 생성 및 태스크 등록
- TeamCreate로 팀 생성 (team_name = "{run_id}")
- TaskCreate로 각 서브태스크를 등록 (명확한 범위, 입력/출력, 완료 기준 포함)
- 태스크 간 의존관계가 있으면 addBlockedBy로 순서 지정

## 3단계: 환경 준비 (리더 직접 수행)
- 공유 데이터 로딩, 디렉토리 생성, 의존성 설치 등 사전 작업
- 서브에이전트들이 바로 작업 시작할 수 있는 상태로 준비

## 4단계: 서브에이전트 스폰
- Task tool (subagent_type="general-purpose")로 에이전트 스폰
- 독립적인 에이전트는 반드시 병렬로 스폰 (한 메시지에 여러 Task tool 호출)
- 각 에이전트에게 team_name="{run_id}" 지정
- 각 에이전트에게 구체적 태스크, 필요 컨텍스트, 출력 형식을 전달

## 5단계: 모니터링 및 결과 취합
- 서브에이전트 완료 대기 및 막힌 에이전트 지원
- TaskList로 전체 진행 확인
- 결과를 하나의 최종 산출물로 merge
- 최종 보고서/결과물 생성
- 서브에이전트에 shutdown_request 전송

## 리더 역할 원칙
- 리더는 조율자: 직접 핵심 작업을 수행하지 말고 서브에이전트에 위임
- 리더가 직접 하는 것: 환경 준비, 모니터링, 결과 취합, 최종 산출물
- 서브에이전트가 하는 것: 실제 코드 작성, 실험 실행, 분석

## 금지사항
- 단일 스크립트로 모든 작업을 혼자 처리하는 것 금지
- 서브에이전트 없이 직접 핵심 작업(모델 학습, 데이터 분석 등)을 수행하는 것 금지
- 팀 생성 없이 Task tool만 단발성으로 사용하는 것 금지
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


def start_claude_session(session: str, prompt: str, cwd: str, run_id: str,
                         team: bool = False) -> None:
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

    # Wait for Claude TUI to fully boot before sending any input.
    # Without this delay, send-keys arrives before the TUI is ready
    # and the prompt gets swallowed or corrupted.
    log(f"waiting {CLAUDE_BOOT_WAIT}s for Claude TUI to load...")
    time.sleep(CLAUDE_BOOT_WAIT)

    augmented = prompt + CURSOR_INSTRUCTIONS.format(run_id=run_id)
    if team:
        augmented += TEAM_INSTRUCTIONS.format(run_id=run_id)
        log("team mode: autonomous")
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


def run(prompt: str, run_id: str, timeout: int, team: bool = False) -> str:
    session = f"harness-{run_id}"
    log(f"starting — run_id={run_id} timeout={timeout}s team={'on' if team else 'off'}")
    start_claude_session(session, prompt, os.getcwd(), run_id, team=team)
    return poll_loop(run_id, session, timeout)


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch a harness task in tmux")
    parser.add_argument("prompt", help="Prompt to send to Claude")
    parser.add_argument("--run-id", default=None, help="Run ID (default: harness_{timestamp})")
    parser.add_argument("--timeout", type=int, default=57600, help="Timeout in seconds (default: 57600 = 16h)")
    parser.add_argument("--solo", action="store_true",
                        help="Disable team mode: run as single Claude instance (default is team)")
    args = parser.parse_args()

    run_id = args.run_id or f"harness_{int(time.time())}"
    ensure_dirs()
    team = not args.solo
    team_label = " [TEAM MODE]" if team else " [SOLO]"
    log(f"=== launch.py === run_id={run_id} timeout={args.timeout}s{team_label}")

    attempt = 0
    while attempt <= MAX_RETRIES:
        if attempt > 0:
            delay = RETRY_DELAYS[min(attempt - 1, len(RETRY_DELAYS) - 1)]
            log(f"--- retry #{attempt} after {delay}s ---")
            cleanup_artifacts(run_id)
            kill_tmux_session(f"harness-{run_id}")
            time.sleep(delay)

        result = run(args.prompt, run_id, args.timeout, team=team)

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
