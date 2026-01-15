# SWARM_RULES.md
**Single Source of Truth for Zerg Swarm Operations**

---

## 1. Core Philosophy

- **Speed over perfection**: Ship fast, iterate faster
- **Spawn -> Bite -> Die -> Repeat**: Zerglings are disposable execution units
- **Low context, high throughput**: Minimal coordination overhead, maximum parallel execution
- **No ego, no architecture debates**: Execute the task, report status, terminate
- **Trust the Overlord**: Task decomposition is handled upstream

---

## 2. Zergling Constraints

| Constraint | Limit | Rationale |
|------------|-------|-----------|
| Timebox | 4 minutes | Force scope discipline, prevent rabbit holes |
| Max lines | 100 | Keep changes atomic and reviewable |
| Max files | 2 (2nd for tests/docs only) | Maintain tight focus, prevent scope creep |
| Dependencies | NONE | No research, no exploration beyond task spec |
| Architecture decisions | NONE | Execute given design, escalate if blocked |
| Exploration | Listed files ONLY | No codebase wandering, read only specified paths |
| Tool calls | Essential only | No speculative searches or pre-reading |
| Communication | Status codes only | No essays, no justifications |

---

## 3. Wave Protocol

### Wave Lifecycle
1. **Overlord decomposes** feature/bug into 4-5 atomic tasks per wave
2. **Tasks written** to `OUTBOX/` as assignment files
3. **Zerglings spawn**, pick up tasks, execute
4. **Results written** to `INBOX/` when complete
5. **Overlord reviews** results, updates `STATE.json`
6. **Next wave** spawned based on progress

### Wave Rules
- Each wave must be completable in parallel
- No inter-task dependencies within a wave
- Wave size: 4-5 tasks (optimal for parallel execution)
- Failed tasks requeue in next wave with adjustments

---

## 4. File Flow

```
OUTBOX/T001.md  ->  Zergling picks up  ->  Code changes  ->  INBOX/T001_RESULT.md
OUTBOX/T002.md  ->  Zergling picks up  ->  Code changes  ->  INBOX/T002_RESULT.md
OUTBOX/T003.md  ->  Zergling picks up  ->  Code changes  ->  INBOX/T003_RESULT.md
```

### Directory Structure
```
SWARM/
├── OUTBOX/          # Tasks waiting for assignment
├── INBOX/           # Completed task results
├── ARCHIVE/         # Completed tasks (moved after wave)
├── STATE.json       # Current wave state
└── SWARM_RULES.md   # This file
```

---

## 5. Status Codes

| Code | Meaning | Next Action |
|------|---------|-------------|
| **DONE** | Task completed successfully | Archive, proceed |
| **PARTIAL** | Made progress, hit constraint (time/lines) | Requeue remaining work |
| **BLOCKED** | Cannot proceed without external input | Escalate to Overlord |
| **FAILED** | Attempted but unsuccessful | Review approach, reassign |

### Result File Format
```markdown
# TASK: T001
STATUS: DONE
FILES_CHANGED: /path/to/file.py
LINES_CHANGED: 45
TIME_TAKEN: 3m 22s

## Summary
Brief description of what was accomplished.

## Changes Made
- Bullet list of specific changes

## Notes
Any relevant context for Overlord review.
```

---

## 6. Naming Conventions

| Item | Pattern | Example |
|------|---------|---------|
| Task files | T{NNN}.md | T001.md, T042.md |
| Result files | T{NNN}_RESULT.md | T001_RESULT.md |
| Lock files | T{NNN}.lock | T001.lock (prevents double-assignment) |
| Wave ID | WAVE_{NNN} | WAVE_001, WAVE_002 |
| Archive dirs | WAVE_{NNN}/ | ARCHIVE/WAVE_001/ |

---

## 7. Execution Protocol

1. **Spawn**: Check OUTBOX for available task
2. **Lock**: Create T{NNN}.lock to claim task
3. **Load**: Read task file, identify target files
4. **Execute**: Make changes within constraints
5. **Report**: Write result to INBOX/
6. **Release**: Remove lock file
7. **Terminate**: Exit cleanly

---

## 8. Anti-Patterns (DO NOT DO)

- Exploring codebase beyond task specification
- Making architectural decisions
- Refactoring unrelated code
- Writing documentation unless explicitly tasked
- Asking clarifying questions (escalate as BLOCKED instead)
- Exceeding constraints "just to finish"
- Batch processing multiple tasks

---

## 9. Lanes

Zerglings work in **one lane per task**. This keeps context low and domain-focused.

| Lane | Scope | Keywords |
|------|-------|----------|
| `KERNEL/` | CUDA, Triton, CUTLASS, perf micro-edits, correctness harness | gpu, kernel, triton, cuda, cutlass, perf |
| `ML/` | Model code, training loops, eval, data plumbing | model, train, loss, dataset, loader, eval |
| `QUANT/` | Math/strategy research, backtests, metrics | strategy, backtest, signal, alpha, sharpe |
| `DEX/` | Solana, Jupiter, Jito, transaction building, risk, config | solana, jupiter, jito, swap, tx, dex |
| `INTEGRATION/` | Glue tasks only - wiring modules, CLI, CI | cli, config, ci, wire, glue, integration |

### Lane Rules

1. **One lane per task** - A zergling NEVER crosses lanes in a single task
2. **Task naming** - Tasks go in their lane: `TASKS/KERNEL/T001.md`
3. **No lane hopping** - If task touches multiple lanes, split it
4. **Integration lane** - Use ONLY for wiring, never for domain logic

### Lane Assignment

OVERLORD assigns lanes based on:
- Primary file paths being modified
- Domain keywords in the objective
- When ambiguous: ask or split

---

## 10. Task Types

Every task has a **Type** that guarantees it fits 4 minutes / ≤100 lines.

| Type | Description | Typical Output |
|------|-------------|----------------|
| `ADD_STUB` | Skeleton with TODOs | Class/module outline, no impl |
| `ADD_PURE_FN` | One function + docstring | Single pure function |
| `ADD_TEST` | 1-3 test cases | One test file or test class |
| `FIX_ONE_BUG` | Single failing test fix | Minimal code change |
| `ADD_ASSERTS` | Runtime/shape checks | Assert statements, guards |
| `ADD_METRIC` | One metric + logging | Metric computation, log call |
| `ADD_BENCH` | Benchmark harness | Timing snippet, perf test |
| `DOC_SNIPPET` | README/runbook chunk | Documentation section |
| `REFACTOR_TINY` | Rename/move symbol | No behavior change |

### Type Rules

1. **Every task MUST have a type** - No untyped tasks
2. **If it doesn't fit a type, it's too big** - Split it
3. **Type determines scope** - Zergling uses type to bound work
4. **One type per task** - No multi-type tasks

### Task Card Format

```
Lane: KERNEL
Type: ADD_PURE_FN
```

### Choosing a Type

- New feature? Start with `ADD_STUB`, then `ADD_PURE_FN` for each function
- Bug? `FIX_ONE_BUG` (one bug = one task)
- Need tests? `ADD_TEST` (1-3 tests per task)
- Cleanup? `REFACTOR_TINY` (one symbol at a time)

---

## 11. Context Packs (MANDATORY)

At 4 minutes, zerglings can't hunt around. Overlord MUST paste a **Context Pack** into every task.

### Required Elements

| Element | Description |
|---------|-------------|
| File path(s) | Exact files to read/edit |
| Function signature(s) | What to implement or modify |
| Surrounding code | 10-40 lines of relevant context |
| Expected behavior | 1-3 bullets describing what it should do |
| Check command | One command to verify (test, lint, run) |

### Context Pack Template

```
## Context Pack

### Files
- `src/kernel/matmul.py`

### Target Signature
```python
def matmul_kernel(a: Tensor, b: Tensor) -> Tensor:
    """Matrix multiply using Triton."""
    pass
```

### Surrounding Code
```python
# Lines 45-60 of matmul.py
class MatMulOp:
    def __init__(self, block_size: int = 64):
        self.block_size = block_size

    # YOUR CODE GOES HERE
```

### Expected Behavior
- Multiply two 2D tensors
- Use tiled algorithm with block_size
- Return result tensor on same device

### Check Command
```bash
pytest tests/test_matmul.py -k test_basic
```
```

### Context Pack Rules

1. **No pack = no assignment** - Overlord cannot assign tasks without context packs
2. **Pack must be self-contained** - Zergling should need NO exploration
3. **Include imports** - If specific imports are needed, list them
4. **Include types** - If custom types are used, show their signatures

---

## 12. Wave Composer

Overlord doesn't pick random tasks. Overlord **composes balanced waves**.

### Standard Wave Template (5 tasks)

| Slot | Type | Purpose |
|------|------|---------|
| 1 | `ADD_STUB` or `ADD_PURE_FN` | Implementation |
| 2 | `ADD_STUB` or `ADD_PURE_FN` | Implementation |
| 3 | `ADD_TEST` or `ADD_ASSERTS` | Validation |
| 4 | `ADD_TEST` or `ADD_ASSERTS` | Validation |
| 5 | `ADD_BENCH` or `DOC_SNIPPET` | Quality |

**Ratio: 2 impl + 2 validation + 1 quality**

### Lane Rules for Waves

| Strategy | Composition |
|----------|-------------|
| **Single-lane wave** (fastest) | All 5 tasks in ONE lane |
| **Mixed wave** (when needed) | 3 tasks lane A + 2 tasks lane B |
| **Never** | More than 2 lanes per wave |

### Wave Composition Examples

**Good wave (KERNEL lane):**
1. `ADD_PURE_FN` - implement softmax kernel
2. `ADD_PURE_FN` - implement backward pass
3. `ADD_TEST` - test forward correctness
4. `ADD_ASSERTS` - add shape checks
5. `ADD_BENCH` - benchmark vs PyTorch

**Good mixed wave (ML + QUANT):**
1. `ADD_PURE_FN` [ML] - feature extractor
2. `ADD_PURE_FN` [ML] - normalize function
3. `ADD_TEST` [ML] - test extractor
4. `ADD_PURE_FN` [QUANT] - signal generator
5. `ADD_TEST` [QUANT] - test no lookahead

**Bad wave (avoid):**
- 5 implementation tasks, 0 tests
- Tasks from 4 different lanes
- All `DOC_SNIPPET` tasks

### Wave Validation Checklist

Before spawning a wave, Overlord checks:
- [ ] At least 2 validation tasks (test/assert)
- [ ] At most 2 lanes
- [ ] Every task has a Context Pack
- [ ] No file conflicts between tasks

---

## 13. Integration Rules

Integration is where tasks become messy. Handle with care.

### Who Does Integration

| Role | Can Do Integration? |
|------|---------------------|
| Overlord | YES - primary integrator |
| Dedicated Integrator | YES - if assigned |
| Regular Zergling | NO - return BLOCKED |

### Integration Task Constraints

- Still ≤100 lines
- May touch 2-3 files (glue only)
- NO domain logic
- NO architectural changes
- NO refactoring

### Valid Integration Tasks

```
✓ Wire config loader into CLI
✓ Add one new command flag
✓ Add one registry entry
✓ Connect module A output to module B input
✓ Add one environment variable
```

### Invalid Integration Tasks

```
✗ "Refactor architecture"
✗ "Redesign the pipeline"
✗ "Integrate entire subsystem"
✗ Any task touching >3 files
```

### Integration Wave Rules

- Max 1-2 integration tasks per wave
- Always pair with tests
- Overlord reviews integration outputs directly
- If integration task grows: STOP, split, reassign

---

**END OF RULES** | Version 1.5 | Lines: 363
