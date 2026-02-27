# run-harness

**Harness engineering for Claude Code.**

**[English](#english) · [한국어](#한국어) · [中文](#中文)**

---

<a name="english"></a>
## English

### Claude Code already has everything.

Skills. Agent Teams. Tasks. Tool use.

All of it — native, built-in, ready.

**run-harness is the missing piece: the execution layer that lets you trust it to run on its own.**

---

### The pattern

```
① Conversation
   You ↔ Claude — think together, build skills,
   shape the goal. This is your harness configuration.

② One command
   /run-harness {the goal you just defined}

③ Autonomous execution
   A new Claude instance — equipped with YOUR skills —
   decides how to organize agent teams,
   assigns tasks, coordinates sub-agents,
   and drives toward the goal.
   Until it's done.
```

This is the recommended way to run long-horizon work with Claude Code.

Not a waterfall pipeline you wrote upfront.
Not a script you had to maintain.

**A conversation that became an agent.**

---

### Why it works

Claude Code's native primitives do the heavy lifting:

| Primitive | What it does |
|-----------|--------------|
| **Skills** | Your custom tools, built during the conversation |
| **TeamCreate** | Spawns and coordinates sub-agent teams |
| **TaskCreate / TaskUpdate** | Assigns and tracks work across agents |
| **Tool use** | Everything Claude Code can already do |

run-harness wraps these with the infrastructure needed for unsupervised, long-running execution:

| Infrastructure | What it provides |
|----------------|-----------------|
| **tmux session** | Isolated execution environment |
| **Heartbeat** | Liveness monitoring every tool call |
| **`.done` signal** | Reliable completion detection |
| **Retry + backoff** | Dead/hung recovery [5s→10s→20s] × 3 |
| **Cursor protocol** | Resume from last checkpoint, not scratch |

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

### Monitoring

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

### Hooks (auto-registered on install)

| Hook | Script | What it does |
|------|--------|--------------|
| `PostToolUse` | `on_tool.py` | Writes heartbeat after every tool call |
| `Stop` | `on_stop.py` | Writes `.done` signal when session ends |

Zero config. Works automatically for every harness session.

---

### File layout

```
~/.claude/harness/
├── signals/     {run_id}.done         ← completion signal
├── heartbeat/   {run_id}.hb           ← liveness signal (stale > 30s = hung)
└── cursors/     {run_id}.cursor.json  ← resume point for crash recovery
```

---

> Build your skills in conversation.
> Fire when ready.
> The agent takes it from there.

---

<a name="한국어"></a>
## 한국어

### Claude Code는 이미 다 갖고 있다.

스킬. 에이전트 팀. 태스크. 툴 사용.

전부 — 네이티브로, 기본 탑재.

**run-harness는 missing piece다: 혼자서도 믿고 맡길 수 있는 실행 레이어.**

---

### 권장 실행 패턴

```
① 대화
   나 ↔ Claude — 함께 생각하고, 스킬 만들고,
   목표를 구체화한다. 이것이 나만의 하네스 설정.

② 한 줄
   /run-harness {방금 정의한 목표}

③ 자율 실행
   내가 만든 스킬로 무장한 새 Claude 인스턴스가
   에이전트 팀 구성 방식을 스스로 결정하고,
   태스크를 분배하고, 서브에이전트들을 조율하며
   목표를 향해 달려간다.
   달성할 때까지.
```

이것이 Claude Code로 장기 작업을 실행하는 권장 방식이다.

미리 짜놓은 워터폴 파이프라인이 아니다.
유지보수해야 하는 스크립트가 아니다.

**대화가 에이전트가 된다.**

---

### 왜 작동하는가

Claude Code의 네이티브 기본 요소들이 실제 일을 한다:

| 기본 요소 | 역할 |
|-----------|------|
| **Skills** | 대화 중 직접 만든 커스텀 툴 |
| **TeamCreate** | 서브에이전트 팀 생성 및 조율 |
| **TaskCreate / TaskUpdate** | 에이전트 간 작업 분배 및 추적 |
| **Tool use** | Claude Code가 할 수 있는 모든 것 |

run-harness는 이것들을 비지도 장기 실행에 필요한 인프라로 감싼다:

| 인프라 | 제공하는 것 |
|--------|------------|
| **tmux 세션** | 독립된 실행 환경 |
| **Heartbeat** | 매 툴 호출마다 생존 신호 기록 |
| **`.done` 신호** | 신뢰할 수 있는 완료 감지 |
| **Retry + backoff** | dead/hung 복구 [5s→10s→20s] × 3 |
| **Cursor 프로토콜** | 처음부터가 아니라 마지막 체크포인트부터 재개 |

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

> 대화에서 스킬을 만든다.
> 준비됐을 때 실행한다.
> 에이전트가 거기서부터 간다.

---

<a name="中文"></a>
## 中文

### Claude Code 已经拥有一切。

技能。Agent 团队。任务。工具调用。

全部——原生内置，开箱即用。

**run-harness 是缺失的那块：让你敢于放手、交给它自主运行的执行层。**

---

### 推荐执行模式

```
① 对话
   你 ↔ Claude —— 一起思考，构建技能，
   明确目标。这就是你的专属 Harness 配置。

② 一行命令
   /run-harness {刚才定义的目标}

③ 自主执行
   一个装备了你的技能的新 Claude 实例，
   自主决定如何组建 Agent 团队，
   分配任务，协调子 Agent，
   朝着目标持续推进。
   直到完成为止。
```

这是用 Claude Code 执行长周期任务的推荐方式。

不是提前写好的瀑布式管道。
不是需要维护的脚本。

**对话，变成了 Agent。**

---

### 为什么它能工作

Claude Code 的原生基础设施承担实际工作：

| 原生能力 | 作用 |
|----------|------|
| **Skills** | 对话中亲手构建的自定义工具 |
| **TeamCreate** | 创建并协调子 Agent 团队 |
| **TaskCreate / TaskUpdate** | 跨 Agent 分配和追踪任务 |
| **Tool use** | Claude Code 能做的一切 |

run-harness 为这些能力包裹上无人值守长期运行所需的基础设施：

| 基础设施 | 提供什么 |
|----------|----------|
| **tmux 会话** | 独立的执行环境 |
| **心跳** | 每次工具调用后记录存活信号 |
| **`.done` 信号** | 可靠的完成检测 |
| **重试 + 退避** | dead/hung 恢复 [5s→10s→20s] × 3 次 |
| **Cursor 协议** | 从最后检查点恢复，而非从头开始 |

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

> 在对话中构建你的技能。
> 时机成熟时，一键启动。
> Agent 从那里接手，直到终点。
