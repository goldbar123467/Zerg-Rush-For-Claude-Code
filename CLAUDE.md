# Zerg Rush Agent Swarm

## Overview

This project uses a **Zerg Rush-style agent swarm** optimized for speed, parallelism, and disposability.

Agents are **short-lived**, **low-context**, and **timeboxed**.
No long-running agents. No deep deliberation. No architecture drift.

**Spawn -> Bite -> Die -> Repeat.**

---

## Agent Mail Protocol (MANDATORY)

Every agent session MUST:
1. Register on startup: `mcp__mcp-agent-mail__register_agent`
2. Check inbox: `mcp__mcp-agent-mail__fetch_inbox`
3. Reserve files before editing: `mcp__mcp-agent-mail__file_reservation_paths`
4. Release reservations when done: `mcp__mcp-agent-mail__release_file_reservations`

### Project Key
```
/home/ubuntu/projects/zerg-swarm
```

### Message Conventions
Subject prefixes: `[TASK]` `[DONE]` `[PARTIAL]` `[BLOCKED]` `[FAILED]`

---

## Agent Roles

### OVERLORD (Opus)
- Breaks large goals into **microtasks** fitting the 4-min / 100-line rule
- Assigns tasks in **waves of 4-5 zerglings**
- Maintains `/SWARM/STATE.json`
- Rejects oversized tasks and splits them further
- Merges results and creates follow-up tasks

### ZERGLING (Sonnet)
- Completes **exactly one task**
- Obeys all hard limits
- Writes results and **stops immediately**

---

## Zergling Hard Constraints (NON-NEGOTIABLE)

| Constraint | Limit |
|------------|-------|
| Timebox | 4 minutes (hard stop) |
| Max new lines | 100 |
| Files touched | 1 (max 2 if 2nd is test/docs) |
| New dependencies | NONE |
| Architectural decisions | NONE |
| Refactors outside task | NONE |
| Exploration beyond listed files | NONE |

If limits are exceeded, return **PARTIAL**.

---

## File Locking Protocol

Before editing ANY file:

```
1. Reserve:  mcp__mcp-agent-mail__file_reservation_paths
2. Edit:     Make changes
3. Release:  mcp__mcp-agent-mail__release_file_reservations
```

**NEVER edit files reserved by another agent.**

---

## Task Card Format

All tasks live in `/SWARM/TASKS/` and follow this structure:

```markdown
# Task: [TASK_ID]

## Metadata
- Wave: X
- Zergling: (assigned at runtime)
- Status: PENDING | IN_PROGRESS | DONE | PARTIAL | BLOCKED

## Context
Files to read (ONLY these):
- path/to/file.py

## Objective
Single-sentence goal.

## Deliverables
- [ ] Output 1
- [ ] Output 2

## Constraints
- Max 100 lines
- Max 2 files
```

---

## State Management

The OVERLORD maintains `/SWARM/STATE.json`:

```json
{
  "wave": 0,
  "active_zerglings": [],
  "completed_tasks": [],
  "pending_tasks": [],
  "last_updated": "<timestamp>"
}
```

---

## Status Codes

| Code | Meaning |
|------|---------|
| `DONE` | Task completed successfully |
| `PARTIAL` | Limits hit, work incomplete |
| `BLOCKED` | Cannot proceed, needs input |
| `FAILED` | Error, task abandoned |

---

## Directory Structure

```
zerg-swarm/
├── CLAUDE.md
├── README.md
└── SWARM/
    ├── STATE.json
    ├── SWARM_RULES.md
    ├── RUNBOOK.md           # Operational playbook
    ├── TASKS/
    │   ├── KERNEL/          # CUDA, Triton, CUTLASS, perf
    │   ├── ML/              # Models, training, data
    │   ├── QUANT/           # Strategy, backtests, math
    │   ├── DEX/             # Solana, Jupiter, Jito
    │   └── INTEGRATION/     # Glue, CLI, CI only
    ├── OUTBOX/
    ├── INBOX/
    ├── TEMPLATES/
    ├── SCRIPTS/
    └── LOCKS/
```

## Lanes

**One lane per task. No crossing.**

| Lane | Scope |
|------|-------|
| `KERNEL/` | CUDA, Triton, CUTLASS, perf micro-edits |
| `ML/` | Model code, training loops, eval, data |
| `QUANT/` | Math/strategy research, backtests |
| `DEX/` | Solana, Jupiter, Jito, transactions |
| `INTEGRATION/` | Glue only - wiring, CLI, CI |

Cross-lane task? **Split it.**

---

## Task Types

Every task has a **Type** that guarantees 4-min / 100-line fit.

| Type | What It Produces |
|------|------------------|
| `ADD_STUB` | Skeleton + TODOs |
| `ADD_PURE_FN` | One function + doc |
| `ADD_TEST` | 1-3 test cases |
| `FIX_ONE_BUG` | Single bug fix |
| `ADD_ASSERTS` | Runtime checks |
| `ADD_METRIC` | One metric + log |
| `ADD_BENCH` | Benchmark snippet |
| `DOC_SNIPPET` | Doc section |
| `REFACTOR_TINY` | Rename/move only |

**If it doesn't fit a type, split it.**

### Task Card Header
```
Lane: KERNEL
Type: ADD_PURE_FN
```

---

## Gates

Each lane has acceptance criteria. Task isn't DONE until gate passes.

| Lane | Gate Checks |
|------|-------------|
| `KERNEL` | Correctness (CPU ref match), Benchmark (1 shape) |
| `ML` | Unit tests OR smoke-run, No import breaks |
| `QUANT` | Deterministic output, No NaNs/lookahead |
| `DEX` | Dry-run TX builds, Safety checks pass |
| `INTEGRATION` | Wire test, CLI --help works |

**Gate must run in <30 seconds.** See `SWARM/GATES.md` for details.

---

## Context Packs

Every task MUST include a Context Pack. No pack = no assignment.

| Required | Description |
|----------|-------------|
| File paths | Exact files to edit |
| Signature | Function/class to implement |
| Surrounding code | 10-40 lines of context |
| Expected behavior | 1-3 bullets |
| Check command | One verification command |

**Zergling should need ZERO exploration.**

---

## Wave Composer

Overlord composes balanced waves, not random task lists.

### Standard Wave (5 tasks)
```
2x Implementation  (ADD_STUB / ADD_PURE_FN)
2x Validation      (ADD_TEST / ADD_ASSERTS)
1x Quality         (ADD_BENCH / DOC_SNIPPET)
```

### Lane Rules
- **Single-lane wave**: All 5 in one lane (fastest)
- **Mixed wave**: Max 3 + 2 across two lanes
- **Never**: More than 2 lanes per wave

### Before Spawning
- [ ] 2+ validation tasks
- [ ] Max 2 lanes
- [ ] All tasks have Context Packs
- [ ] No file conflicts

---

## File Flow (INBOX/OUTBOX)

Zerglings can "finish and die" by dropping results without editing STATE:

```
OVERLORD creates:  OUTBOX/T001.md   (assignment)
                        ↓
ZERGLING picks up, executes task
                        ↓
ZERGLING writes:   INBOX/T001_RESULT.md  (result)
                        ↓
OVERLORD collects: swarm.py collect  (updates STATE)
```

---

## CLI Tool: swarm.py

```bash
python3 SWARM/SCRIPTS/swarm.py <command>

Commands:
  status   - Show wave, counts, INBOX/OUTBOX status
  wave     - Increment wave counter
  tasks    - List pending tasks in OUTBOX
  results  - List results in INBOX
  collect  - Process INBOX, update STATE.json
```

---

## Quick Reference

### Spawn a Wave
```
1. OVERLORD decomposes goal into 4-5 microtasks
2. Create task cards in OUTBOX/ (or TASKS/)
3. Update STATE.json with pending_tasks
4. Spawn zerglings (Sonnet) in parallel
5. Zerglings write results to INBOX/
6. Run: swarm.py collect
7. Repeat or merge
```

### Zergling Lifecycle
```
SPAWN -> REGISTER -> RESERVE_FILES -> EXECUTE -> WRITE_TO_INBOX -> RELEASE -> DIE
```
