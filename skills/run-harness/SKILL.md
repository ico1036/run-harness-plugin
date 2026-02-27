---
name: run-harness
description: 하니스 작업을 tmux에서 자율 실행. 프롬프트를 받아 --dangerously-skip-permissions로 Claude 실행 후 .done 신호 폴링. dead/hung 감지 및 지수 백오프 retry. 사용 — /run-harness {프롬프트} [--timeout 초]
---

# Run Harness

프롬프트를 tmux 세션에서 자율 실행하고 완료를 감시한다.

## 인프라 (자동, 신경 쓸 필요 없음)

run-harness로 실행된 Claude 세션은 hooks를 통해 다음이 자동 처리된다:

- **heartbeat** — 매 도구 호출마다 `~/.claude/harness/heartbeat/{run_id}.hb` 자동 갱신 (PostToolUse hook)
- **.done** — 세션 종료 시 `~/.claude/harness/signals/{run_id}.done` 자동 기록 (Stop hook)

스킬이 직접 .done을 쓰면 그게 우선. hook은 안전망.

## cursor 프로토콜 (반복 처리 작업 시 적용)

여러 item을 순차 처리할 때 crash 후 재개를 위해 cursor 파일을 직접 관리:

### 시작 시 cursor 확인
```
Read ~/.claude/harness/cursors/{run_id}.cursor.json
→ 없으면 index 0부터 / 있으면 last_completed_index + 1부터
```

### item 완료 후 cursor 갱신 (원자적 쓰기)
```
1. Write ~/.claude/harness/cursors/{run_id}.cursor.json.tmp
   {"last_completed_index": N, "total": M}
2. Bash: mv ~/.claude/harness/cursors/{run_id}.cursor.json.tmp \
         ~/.claude/harness/cursors/{run_id}.cursor.json
```

이름 기반 포맷도 가능: `{"completed": ["table_1", "table_2"]}`

cursor 파일은 retry 시 삭제하지 않음 (재개용).

---

## 입력

- **prompt** (필수): Claude에게 전달할 텍스트 (스킬 호출 포함 무엇이든)
- **--timeout** (선택): 제한 시간 초 (기본: 57600 = 16h)
- **status** 키워드: 모든 세션 상태 조회 (아래 참고)

## 상태 확인

### Claude Code 안에서 (quick check)

`/run-harness status` 또는 "harness 상태 확인해줘" 입력 시:

```bash
python3 ~/.claude/skills/run-harness/scripts/status.py
```

결과 예시:
```
  RUN_ID                                 ELAPSED   HEARTBEAT   STATUS         STEP
  ----------------------------------------------------------------------------------------
  harness_1740700000                     8m 32s    3s ago      🟢 running     tool:WebFetch
  harness_1740700100                     25m 11s   -           ✅ success     -
  harness_1740699900                     42m 5s    38s ago     🔴 hung        tool:Write
```

### 터미널 실시간 모니터링 (live)

```bash
watch -n 2 python3 ~/.claude/skills/run-harness/scripts/status.py
```

2초마다 자동 갱신. 별도 터미널에 띄워두면 됨.

## 실행 프로세스

### 1. run_id 생성

```bash
date +%s
```

`run_id = "harness_{unix_timestamp}"`

### 2. launch.py 실행

```bash
python ~/.claude/skills/run-harness/scripts/launch.py "{prompt}" --run-id {run_id} --timeout {timeout}
```

launch.py가 내부적으로 수행:
- tmux 세션 `harness-{run_id}` 생성
- `HARNESS_RUN_ID={run_id}` env var 주입 (hooks가 이 값으로 파일 경로 결정)
- `claude --dangerously-skip-permissions` 실행 (CLAUDECODE 언셋)
- prompt 전송
- 8초 초기화 대기
- 5초 간격 폴링 (.done / dead / hung / timeout)
- dead/hung 시 지수 백오프 retry [5, 10, 20]s (최대 3회)
- timeout은 retry 없이 즉시 포기

### 3. 결과 리포트

- **exit 0** → 성공:
  ```
  Read ~/.claude/harness/signals/{run_id}.done
  ## Run Complete
  - run_id / status / completed_at
  ```

- **exit 1** → 실패:
  ```
  ## Run Failed
  - run_id / reason (timeout or max retries)
  ```
