# run-harness

Claude Code plugin — tmux 기반 자율 실행 하니스.

프롬프트를 tmux 세션에서 `--dangerously-skip-permissions`로 실행하고, `.done` 신호 폴링 + heartbeat 감시 + 지수 백오프 retry를 자동 처리.

## 설치

```bash
/plugin marketplace add https://github.com/ico1036/run-harness-plugin
/plugin install run-harness
```

## 사용법

```
/run-harness {프롬프트}
/run-harness {프롬프트} --timeout 3600
/run-harness status
```

## 동작 방식

```
/run-harness 호출
    ↓
tmux 세션 생성 (harness-{run_id})
    ↓
claude --dangerously-skip-permissions 실행
    ↓
5초마다 폴링 (.done 신호 대기)
    ↓
hung/dead 감지 → 지수 백오프 retry (최대 3회: 5s→10s→20s)
    ↓
완료 또는 실패 리포트
```

## Hooks

플러그인은 두 개의 hooks를 자동 등록:

| Hook | 파일 | 역할 |
|------|------|------|
| `PostToolUse` | `on_tool.py` | 매 도구 호출마다 heartbeat 갱신 |
| `Stop` | `on_stop.py` | 세션 종료 시 `.done` 신호 기록 |

## 파일 구조

```
~/.claude/harness/
├── signals/    {run_id}.done       — 완료 신호
├── heartbeat/  {run_id}.hb         — 생존 신호 (30s stale → hung)
└── cursors/    {run_id}.cursor.json — crash 재개용 커서
```

## 요구사항

- `tmux`
- `claude` CLI (`claude` 커맨드가 PATH에 있어야 함)
- Python 3.8+
