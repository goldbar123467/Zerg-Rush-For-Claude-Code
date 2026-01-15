# Task: T[XXX]

## Metadata
| Field | Value |
|-------|-------|
| Lane | KERNEL / ML / QUANT / DEX / INTEGRATION |
| Type | ADD_STUB / ADD_PURE_FN / ADD_TEST / FIX_ONE_BUG / ADD_ASSERTS / ADD_METRIC / ADD_BENCH / DOC_SNIPPET / REFACTOR_TINY |
| Wave | |
| Status | PENDING |
| Created | |
| Assigned | |

## Context Pack

### Files
<!-- Exact paths to read/edit -->
-

### Target Signature
<!-- Function/class to implement or modify -->
```python
def example_fn():
    pass
```

### Surrounding Code
<!-- 10-40 lines of relevant context from the file -->
```python
# Paste relevant code here
```

### Expected Behavior
<!-- 1-3 bullets describing what it should do -->
-

### Check Command
<!-- One command to verify the task -->
```bash
pytest tests/test_example.py -k test_name
```

## Objective
<!-- Single sentence. What must be accomplished? -->

## Deliverables
- [ ]

## Acceptance Criteria (Gate)

<!-- Select gate for your lane. Delete other lanes. -->

### KERNEL
- [ ] Correctness: matches CPU reference (atol=1e-5)
- [ ] Benchmark: runs one shape case

### ML
- [ ] Unit tests pass OR smoke-run works (1 batch)
- [ ] No import breaks

### QUANT
- [ ] Deterministic output for fixed seed
- [ ] Sanity: no NaNs, no lookahead

### DEX
- [ ] Dry-run: TX builds successfully
- [ ] Safety: allowlist + slippage bounds checked

### INTEGRATION
- [ ] Wire test: modules connect
- [ ] CLI: --help works, config parses

## Constraints
- Max 100 lines of new code
- Max 2 files
- No new dependencies
- No architectural changes

## Notes
<!-- Optional guidance for zergling -->
