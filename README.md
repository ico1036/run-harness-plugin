# run-harness

**[English](#english) · [한국어](#한국어) · [中文](#中文)**

---

<a name="english"></a>
## English

Agent development is evolving.

The old way: design a pipeline upfront, script every step, run it like a waterfall.

The new way — **harness engineering** — is different.

You build your own harness *through conversation*. Back-and-forth with an agent, you shape the tools, define the goal, configure the execution environment. That conversation *is* the design. When the moment is right, you fire.

The agent takes it from there.

---

**run-harness is the execution layer for this pattern.**

```
① Build your harness
   Conversation with Claude → create skills,
   define the goal, shape the approach.

② Fire when ready
   /run-harness {the goal}

③ Autonomous execution
   A Claude instance equipped with your skills
   organizes its own agent teams, assigns tasks,
   drives toward the goal — until done.
```

The back-and-forth isn't just prep work. It's how you configure an agent worth trusting with unsupervised, long-running work.

---

### Install

```
/plugin marketplace add https://github.com/ico1036/run-harness-plugin
/plugin install run-harness@ico1036
```

Requires: `tmux`, `claude` CLI in PATH, Python 3.8+

---

### Usage

```
/run-harness {goal}
/run-harness {goal} --timeout 3600
/run-harness status
```

**Examples:**

```
/run-harness backtest all strategies in strategies/ and save results to DB
/run-harness research and implement the momentum factor we just discussed
/run-harness /mine-scrape https://quantopian.com/research
```

---

### Under the hood

```
tmux session harness-{run_id}
    ↓ HARNESS_RUN_ID injected
    ↓ claude --dangerously-skip-permissions
    ↓ poll every 5s for .done signal
    ↓ heartbeat stale > 30s → hung → retry
    ↓ dead session → retry
    ↓ exponential backoff [5s, 10s, 20s] × 3
    ↓ cursor protocol → resume from last checkpoint
```

### Monitoring

```bash
/run-harness status
watch -n 2 python3 ~/.claude/plugins/run-harness/scripts/status.py
```

```
RUN_ID              ELAPSED    HEARTBEAT   STATUS       STEP
harness_1740700000  8m 32s     3s ago      🟢 running   tool:WebFetch
harness_1740700100  25m 11s    -           ✅ success   -
harness_1740699900  42m 5s     38s ago     🔴 hung      tool:Write
```

### Hooks (auto-registered on install)

| Hook | What it does |
|------|--------------|
| `PostToolUse` | Heartbeat after every tool call |
| `Stop` | `.done` signal on session end |

---

> Build your harness in conversation.
> Fire when ready.
> The agent takes it from there.

---

<a name="한국어"></a>
## 한국어

에이전트 개발 방법론이 바뀌고 있다.

과거 방식: 파이프라인을 미리 설계하고, 모든 단계를 스크립팅하고, 워터폴로 실행한다.

새로운 방식 — **harness engineering** — 은 다르다.

**대화를 통해** 자기만의 하네스를 만든다. 에이전트와 티키타카하면서 툴을 만들고, 목표를 정의하고, 실행 환경을 설정한다. 그 대화가 곧 설계다. 준비가 됐을 때, 실행한다.

그 다음은 에이전트가 간다.

---

**run-harness는 이 패턴을 위한 실행 레이어다.**

```
① 하네스 구축
   Claude와 대화 → 스킬 생성,
   목표 정의, 방향 설정.

② 준비됐을 때 실행
   /run-harness {목표}

③ 자율 실행
   내 스킬로 무장한 Claude 인스턴스가
   에이전트 팀을 스스로 구성하고,
   태스크를 분배하며 목표를 향해 달린다.
   달성할 때까지.
```

티키타카는 단순한 준비 단계가 아니다. 비지도 장기 실행을 맡길 수 있는 에이전트를 설정하는 과정이다.

---

### 설치

```
/plugin marketplace add https://github.com/ico1036/run-harness-plugin
/plugin install run-harness@ico1036
```

### 사용법

```
/run-harness {목표}
/run-harness {목표} --timeout 3600
/run-harness status
```

---

> 대화로 하네스를 만든다.
> 준비됐을 때 실행한다.
> 에이전트가 거기서부터 간다.

---

<a name="中文"></a>
## 中文

Agent 开发方法论正在进化。

旧方式：提前设计管道，脚本化每个步骤，瀑布式执行。

新方式——**Harness Engineering**——截然不同。

你**通过对话**构建属于自己的 Harness。与 Agent 来回磋磨，创建工具，明确目标，配置执行环境。那段对话，就是设计本身。时机成熟，一键启动。

之后交给 Agent。

---

**run-harness 是这个模式的执行层。**

```
① 构建你的 Harness
   与 Claude 对话 → 创建技能，
   定义目标，确定方向。

② 时机到了，启动
   /run-harness {目标}

③ 自主执行
   装备了你的技能的 Claude 实例，
   自主组建 Agent 团队，分配任务，
   朝目标推进——直到完成。
```

来回对话不只是准备工作。这是配置一个值得信任、能独立运行长期任务的 Agent 的过程。

---

### 安装

```
/plugin marketplace add https://github.com/ico1036/run-harness-plugin
/plugin install run-harness@ico1036
```

### 使用方法

```
/run-harness {目标}
/run-harness {目标} --timeout 3600
/run-harness status
```

---

> 在对话中构建你的 Harness。
> 时机成熟，一键启动。
> Agent 从那里接手，直到终点。
