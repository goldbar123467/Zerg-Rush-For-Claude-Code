# Task: META-001

## Metadata
| Field | Value |
|-------|-------|
| Lane | INTEGRATION |
| Type | REFACTOR_TINY |
| Wave | 4 |
| Status | PENDING |
| Created | 2026-01-15T20:36:00Z |
| Assigned | ZERGLING-1 |

## Objective
Add missing metadata fields to KERNEL tasks K001, K002, K003 to match TASK_TEMPLATE.md specification.

## Context Pack

### Current State (K001 Example)
```markdown
## Metadata
| Field | Value |
|-------|-------|
| Lane | KERNEL |
| Type | ADD_PURE_FN |
| Wave | - |
| Status | PENDING |
```

### Required Template State
```markdown
## Metadata
| Field | Value |
|-------|-------|
| Lane | KERNEL |
| Type | ADD_PURE_FN |
| Wave | 1 |
| Status | PENDING |
| Created | [ISO timestamp] |
| Assigned | [Agent ID] |
```

### Files to Update
- `SWARM/TASKS/KERNEL/K001.md` (ADD_PURE_FN)
- `SWARM/TASKS/KERNEL/K002.md` (ADD_TEST)
- `SWARM/TASKS/KERNEL/K003.md` (ADD_BENCH)

### Reference Template
- `SWARM/TEMPLATES/TASK_TEMPLATE.md` (canonical format)

### Identified Flaws

**CRITICAL - All 3 tasks:**
1. Missing `Created` field (ISO 8601 timestamp)
2. Missing `Assigned` field (should indicate owner/wave)
3. Invalid Wave value using "-" instead of numeric (1, 2, 3, or 4)

**HIGH - All 3 tasks:**
4. Missing `Deliverables` section with checkboxes (part of template)

### Expected Behavior
- Replace Wave "-" with "1" (Wave 1 KERNEL tasks)
- Add Created timestamp for each task (use task discovery date or 2026-01-15)
- Add Assigned field with agent responsible (unassigned = TBD or WAVE-1)
- Add Deliverables section with task-specific checkboxes:
  - K001: Implementation checkpoint, Test integration
  - K002: Test file creation, Tolerance documentation
  - K003: Benchmark harness, Timing validation

### Check Command
```bash
for file in SWARM/TASKS/KERNEL/K00{1,2,3}.md; do
  echo "=== $file ===";
  grep -E "^(Created|Assigned|Wave|## Deliverables)" "$file" || echo "MISSING FIELDS";
done
```

## Objective
Repair task card metadata in K001-K003 to match canonical TASK_TEMPLATE.md format and restore traceability.

## Deliverables
- [ ] K001.md: Add Created, Assigned, fix Wave to "1", add Deliverables section with 2-3 checkboxes
- [ ] K002.md: Add Created, Assigned, fix Wave to "1", add Deliverables section with 2-3 checkboxes
- [ ] K003.md: Add Created, Assigned, fix Wave to "1", add Deliverables section with 2-3 checkboxes
- [ ] Verify with check command: all 3 files now contain Created, Assigned, numeric Wave, and Deliverables
- [ ] No other sections modified (preserve all Context Pack, Objective, Acceptance Criteria)

## Acceptance Criteria (INTEGRATION Gate)
- [ ] Wire test: All 3 task files parse with valid metadata table
- [ ] CLI: grep check command shows all required fields present in each file
- [ ] Format verification: Created timestamps in ISO 8601, Assigned fields populated, Wave numeric (1-4)

## Constraints
- Max 100 lines of new code (metadata additions only)
- Max 2 files modified per pass (or do all 3 in sequence)
- No architectural changes
- Preserve all existing task content; only add/fix metadata rows and Deliverables section

## Notes
These are Wave 1 KERNEL tasks (foundational CPU matmul). Created timestamp should be 2026-01-15 or earlier based on actual task discovery. Assigned to first available Wave 1 agent (SilentLantern / ZERGLING-1 or delegate to WAVE-1 coordinator).
