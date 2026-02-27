# run-harness

**Harness engineering for Claude Code.**

**Turn any Claude conversation into an autonomous background agent — instantly.**

You're mid-conversation with Claude. An idea crystallizes. A strategy emerges. A task takes shape.

Don't break the flow. Don't write a script. Don't build a pipeline.

Just say: `/run-harness {exactly what you just figured out}`

Claude picks it up, runs it in the background — fully autonomous, fully equipped — while you move on.

---

## Why this exists

Most automation tools make you define the work *before* the conversation.
You write pipelines. You script workflows. You plan upfront.

**run-harness does the opposite.**

It captures the intelligence *from* the conversation and executes it autonomously — with the full power of Claude Code: skills, agent teams, tool use, everything.

```
You ↔ Claude  (the good part — thinking together)
              ↓
   /run-harness {what we just figured out}
              ↓
   New Claude instance in tmux
   → Uses your installed skills
   → Can spawn agent teams (TeamCreate)
   → Runs until done, retries on failure
   → Signals you when complete
```

No context switching. No scaffolding. The conversation *is* the spec.

---

## Install

```
/plugin marketplace add https://github.com/ico1036/run-harness-plugin
/plugin install run-harness@ico1036
```

Requires: `tmux`, `claude` CLI in PATH, Python 3.8+

---

## Usage

```
/run-harness {prompt}
/run-harness {prompt} --timeout 3600
/run-harness status
```

**Examples:**

```
/run-harness backtest all strategies in strategies/ and save results to DB
/run-harness /mine-scrape https://quantopian.com/research
/run-harness build a factor model using the ideas we just discussed
```

---

## What happens under the hood

```
launch.py spawns tmux session harness-{run_id}
    ↓ HARNESS_RUN_ID injected as env var
    ↓ claude --dangerously-skip-permissions
    ↓ your prompt sent
    ↓ poll every 5s for .done signal
    ↓ hung detection via heartbeat (stale > 30s → retry)
    ↓ dead session → retry
    ↓ exponential backoff [5s, 10s, 20s] × 3 attempts
    ↓ timeout → give up, report
```

**Crash recovery with cursor protocol** — for long multi-step tasks, write cursor files so retries resume from where they left off, not from scratch.

---

## Monitoring

```bash
# Quick check inside Claude Code
/run-harness status

# Live dashboard in a separate terminal
watch -n 2 python3 ~/.claude/plugins/run-harness/scripts/status.py
```

```
RUN_ID              ELAPSED    HEARTBEAT   STATUS       STEP
harness_1740700000  8m 32s     3s ago      🟢 running   tool:WebFetch
harness_1740700100  25m 11s    -           ✅ success   -
harness_1740699900  42m 5s     38s ago     🔴 hung      tool:Write
```

---

## Hooks (auto-registered on install)

| Hook | Script | What it does |
|------|--------|--------------|
| `PostToolUse` | `on_tool.py` | Writes heartbeat after every tool call |
| `Stop` | `on_stop.py` | Writes `.done` signal when session ends |

Zero config. Works automatically for every harness session.

---

## File layout

```
~/.claude/harness/
├── signals/     {run_id}.done         ← completion signal
├── heartbeat/   {run_id}.hb           ← liveness signal (stale > 30s = hung)
└── cursors/     {run_id}.cursor.json  ← resume point for crash recovery
```

---

> Harness engineering: wrap your agent in infrastructure it can trust.
> Heartbeat. Signal. Retry. Resume.
> The pipeline writes itself.

---

# run-harness (한국어)

**대화에서 나온 아이디어를 그대로 자율 실행으로.**

Claude와 티키타카하다 보면 좋은 작업이 떠오른다.
그 순간을 놓치지 마라.

```
/run-harness {방금 대화에서 나온 그것}
```

끝. Claude가 백그라운드에서 알아서 한다.

---

## 왜 쓰는가

기존 자동화 도구들은 **대화 전에** 파이프라인을 짜야 한다.
run-harness는 반대다. **대화 후에** 실행을 시작한다.

대화가 곧 스펙. 별도 스크립팅 없음.

그리고 실행된 인스턴스는 Claude Code의 모든 기능을 그대로 쓴다:
- 설치된 스킬 사용 가능
- `TeamCreate`로 에이전트 팀 구성 가능
- 툴 사용 전부 가능

---

## 설치

```
/plugin marketplace add https://github.com/ico1036/run-harness-plugin
/plugin install run-harness@ico1036
```

---

## 사용법

```
/run-harness {프롬프트}
/run-harness {프롬프트} --timeout 3600
/run-harness status
```

---

## 장애 복구

긴 작업은 cursor 파일로 중단 지점을 기록한다.
crash 후 재실행 시 처음부터가 아니라 마지막 완료 지점부터 재개.

---

> 먼저 Claude와 생각하고, 그다음 실행한다.
> 파이프라인은 대화에서 저절로 만들어진다.
