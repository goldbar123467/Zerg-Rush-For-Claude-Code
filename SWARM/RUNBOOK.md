# Zerg Rush Runbook

## Starting a Session

1. Register as OVERLORD
2. Check current state: `swarm.py status`
3. Review pending tasks in TASKS/

## Spawning a Wave

### 1. Decompose the Goal
- Break into 4-5 microtasks
- Each task: 1 lane, 1 file, 100 lines max
- If task spans lanes → split it

### 2. Create Task Cards
Place in correct lane directory:
```
TASKS/KERNEL/K001.md
TASKS/ML/M001.md
TASKS/QUANT/Q001.md
TASKS/DEX/D001.md
TASKS/INTEGRATION/INT-001.md
```

### 3. Spawn Zerglings
- Use Task tool with model: "sonnet"
- Spawn 4-5 in parallel
- Each zergling gets ONE task card

### 4. Collect Results
- Zerglings write to INBOX/
- Run: `swarm.py collect`
- Review for PARTIAL/BLOCKED

## Lane Quick Reference

| Lane | When to Use |
|------|-------------|
| KERNEL | GPU ops, Triton/CUDA, perf |
| ML | Models, training, data |
| QUANT | Strategy, backtests, math |
| DEX | Solana, swaps, transactions |
| INTEGRATION | Wiring, CLI, CI only |

## Type Quick Reference

| Type | When to Use |
|------|-------------|
| `ADD_STUB` | New class/module skeleton |
| `ADD_PURE_FN` | Single function implementation |
| `ADD_TEST` | 1-3 test cases |
| `FIX_ONE_BUG` | One failing test |
| `ADD_ASSERTS` | Runtime checks, guards |
| `ADD_METRIC` | Logging, metrics |
| `ADD_BENCH` | Performance benchmarks |
| `DOC_SNIPPET` | Documentation |
| `REFACTOR_TINY` | Rename/move only |

## Gate Quick Reference

| Lane | Must Pass |
|------|-----------|
| KERNEL | CPU ref match + 1 benchmark |
| ML | Tests/smoke + imports work |
| QUANT | Deterministic + no NaNs |
| DEX | Dry-run TX + safety checks |
| INTEGRATION | Wire + CLI works |

Gate fails? Report **PARTIAL**, note which check failed.

## Handling Issues

### PARTIAL Results
- Check what was completed
- Create follow-up task for remainder
- Same lane, smaller scope

### BLOCKED Tasks
- Read blocker reason
- Resolve dependency or provide context
- Re-assign to new zergling

### Cross-Lane Tasks
- STOP - do not assign
- Split into lane-specific subtasks
- Create INTEGRATION task for wiring

## Task Naming Convention

Task ID format by lane:
```
KERNEL:      K001, K002, K003, ...
ML:          M001, M002, M003, ...
QUANT:       Q001, Q002, Q003, ...
DEX:         D001, D002, D003, ...
INTEGRATION: INT-001, INT-002, INT-003, ...
DOC:         DOC-001, DOC-002, DOC-003, ...
META:        META-001, META-002, META-003, ...
```

File paths:
```
TASKS/<LANE>/<ID>.md
INBOX/<ID>_RESULT.md
```

Examples:
- TASKS/KERNEL/K001.md
- TASKS/ML/M002.md
- TASKS/INTEGRATION/INT-001.md
- INBOX/K001_RESULT.md
- INBOX/INT-001_RESULT.md

## Emergency Commands

### Kill Runaway Zergling
```bash
swarm.py kill <task_id>
```

### Reset State
```bash
swarm.py reset
rm -rf INBOX/* TASKS/*/T*.md
```

### Health Check
```bash
swarm.py status --verbose
```

## Best Practices

- One zergling = one task = one file
- Always check INBOX before spawning new wave
- Keep tasks under 100 lines
- Use INTEGRATION lane for cross-cutting only
- Review task cards before spawn (typos = failure)
