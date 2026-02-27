# run-harness

**Harness engineering for Claude Code.**

**[English](#english) · [한국어](#한국어) · [中文](#中文)**

---

<a name="english"></a>
## English

**Turn any Claude conversation into an autonomous background agent — instantly.**

You're mid-conversation with Claude. An idea crystallizes. A strategy emerges. A task takes shape.

Don't break the flow. Don't write a script. Don't build a pipeline.

Just say: `/run-harness {exactly what you just figured out}`

Claude picks it up, runs it in the background — fully autonomous, fully equipped — while you move on.

### Why this exists

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

### Install

```
/plugin marketplace add https://github.com/ico1036/run-harness-plugin
/plugin install run-harness@ico1036
```

Requires: `tmux`, `claude` CLI in PATH, Python 3.8+

### Usage

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

### What happens under the hood

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

### Hooks (auto-registered on install)

| Hook | Script | What it does |
|------|--------|--------------|
| `PostToolUse` | `on_tool.py` | Writes heartbeat after every tool call |
| `Stop` | `on_stop.py` | Writes `.done` signal when session ends |

Zero config. Works automatically for every harness session.

### File layout

```
~/.claude/harness/
├── signals/     {run_id}.done         ← completion signal
├── heartbeat/   {run_id}.hb           ← liveness signal (stale > 30s = hung)
└── cursors/     {run_id}.cursor.json  ← resume point for crash recovery
```

> Harness engineering: wrap your agent in infrastructure it can trust.
> Heartbeat. Signal. Retry. Resume.
> The pipeline writes itself.

---

<a name="한국어"></a>
## 한국어

**대화에서 나온 아이디어를 그대로 자율 실행으로.**

Claude와 티키타카하다 보면 좋은 작업이 떠오른다.
그 순간을 놓치지 마라.

```
/run-harness {방금 대화에서 나온 그것}
```

끝. Claude가 백그라운드에서 알아서 한다.

### 왜 쓰는가

기존 자동화 도구들은 **대화 전에** 파이프라인을 짜야 한다.
run-harness는 반대다. **대화 후에** 실행을 시작한다.

대화가 곧 스펙. 별도 스크립팅 없음.

그리고 실행된 인스턴스는 Claude Code의 모든 기능을 그대로 쓴다:
- 설치된 스킬 사용 가능
- `TeamCreate`로 에이전트 팀 구성 가능
- 툴 사용 전부 가능

### 설치

```
/plugin marketplace add https://github.com/ico1036/run-harness-plugin
/plugin install run-harness@ico1036
```

### 사용법

```
/run-harness {프롬프트}
/run-harness {프롬프트} --timeout 3600
/run-harness status
```

### 장애 복구

긴 작업은 cursor 파일로 중단 지점을 기록한다.
crash 후 재실행 시 처음부터가 아니라 마지막 완료 지점부터 재개.

> 먼저 Claude와 생각하고, 그다음 실행한다.
> 파이프라인은 대화에서 저절로 만들어진다.

---

<a name="中文"></a>
## 中文

**将任何 Claude 对话，直接变成自主后台 Agent。**

你正在和 Claude 对话。一个想法成形了。一个策略浮现了。一个任务明确了。

不要打断思路。不要写脚本。不要搭管道。

直接说：`/run-harness {刚才对话里得出的结论}`

Claude 接手，在后台自主执行——完全自主，全功能装备——你继续往前走。

### 为什么要用它

大多数自动化工具要求你在对话**之前**就定义好工作流。
写管道，写脚本，提前规划。

**run-harness 反其道而行。**

它从对话中提取智慧，自主执行——并拥有 Claude Code 的完整能力：技能、Agent 团队、工具调用，一切都有。

```
你 ↔ Claude  （精华所在 —— 一起思考）
              ↓
   /run-harness {刚才想清楚的那件事}
              ↓
   tmux 中启动新的 Claude 实例
   → 使用你已安装的技能
   → 可以组建 Agent 团队（TeamCreate）
   → 运行直到完成，失败自动重试
   → 完成后发出信号通知你
```

无需切换上下文。无需脚手架。对话本身就是需求文档。

### 安装

```
/plugin marketplace add https://github.com/ico1036/run-harness-plugin
/plugin install run-harness@ico1036
```

依赖：`tmux`，`claude` CLI 在 PATH 中，Python 3.8+

### 使用方法

```
/run-harness {提示词}
/run-harness {提示词} --timeout 3600
/run-harness status
```

**示例：**

```
/run-harness 回测 strategies/ 下的所有策略并保存结果到数据库
/run-harness /mine-scrape https://quantopian.com/research
/run-harness 根据我们刚才讨论的想法构建一个因子模型
```

### 内部原理

```
launch.py 启动 tmux 会话 harness-{run_id}
    ↓ 注入环境变量 HARNESS_RUN_ID
    ↓ claude --dangerously-skip-permissions
    ↓ 发送提示词
    ↓ 每 5 秒轮询 .done 信号
    ↓ 心跳检测（超过 30 秒无响应 → hung，触发重试）
    ↓ 会话死亡 → 重试
    ↓ 指数退避 [5s, 10s, 20s] × 最多 3 次
    ↓ 超时 → 放弃，报告结果
```

**Cursor 协议崩溃恢复** — 长任务写入 cursor 文件记录进度，重试时从上次完成点继续，而非从头开始。

### 监控

```bash
# 在 Claude Code 内快速查看
/run-harness status

# 在独立终端实时监控
watch -n 2 python3 ~/.claude/plugins/run-harness/scripts/status.py
```

```
RUN_ID              ELAPSED    HEARTBEAT   STATUS       STEP
harness_1740700000  8m 32s     3s ago      🟢 running   tool:WebFetch
harness_1740700100  25m 11s    -           ✅ success   -
harness_1740699900  42m 5s     38s ago     🔴 hung      tool:Write
```

### Hooks（安装时自动注册）

| Hook | 脚本 | 作用 |
|------|------|------|
| `PostToolUse` | `on_tool.py` | 每次工具调用后更新心跳 |
| `Stop` | `on_stop.py` | 会话结束时写入 `.done` 信号 |

零配置。对每个 harness 会话自动生效。

> Harness 工程：用可信赖的基础设施包裹你的 Agent。
> 心跳。信号。重试。恢复。
> 管道，在对话中自然生成。
