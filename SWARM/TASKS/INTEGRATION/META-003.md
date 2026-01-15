# Task: META-003

## Metadata
- **Wave**: 4
- **Zergling**: ZERGLING-3
- **Status**: PENDING
- **Created**: 2026-01-15T00:00:00Z

## Context
Files to read and fix (ONLY these):
- `/home/ubuntu/projects/zerg-swarm/SWARM/TASKS/QUANT/Q001.md`
- `/home/ubuntu/projects/zerg-swarm/SWARM/TASKS/QUANT/Q002.md`
- `/home/ubuntu/projects/zerg-swarm/SWARM/TASKS/QUANT/Q003.md`
- `/home/ubuntu/projects/zerg-swarm/SWARM/TASKS/DEX/D001.md`
- `/home/ubuntu/projects/zerg-swarm/SWARM/TASKS/DEX/D002.md`
- `/home/ubuntu/projects/zerg-swarm/SWARM/TASKS/DEX/D003.md`

## Objective
Add missing metadata fields to QUANT and DEX task cards (Wave, Created, Assigned, Deliverables).

## Context Pack

### Current State: Q001.md
```
## Metadata
| Field | Value |
|-------|-------|
| Lane | QUANT |
| Type | ADD_STUB |
| Wave | - |
| Status | PENDING |

[Missing: Created, Assigned, Deliverables section]
```

### Current State: D001.md
```
## Metadata
| Field | Value |
|-------|-------|
| Lane | DEX |
| Type | ADD_PURE_FN |
| Wave | - |
| Status | PENDING |

[Missing: Created, Assigned, Deliverables section]
```

### Identified Issues
1. **Wave field**: All 6 cards have Wave = "-" (invalid). Should be Wave = 1-4
2. **Created timestamp**: Missing from all 6 cards
3. **Assigned field**: Missing from all 6 cards
4. **Deliverables**: None of the cards have a proper Deliverables checklist section

### Expected Format (from TEMPLATE.md)
```markdown
## Metadata
- **Wave**: X
- **Zergling**: (assigned at runtime)
- **Status**: PENDING | IN_PROGRESS | DONE | PARTIAL | BLOCKED
- **Created**: <timestamp>

## Deliverables
- [ ] Specific output 1
- [ ] Specific output 2
```

## Deliverables
- [ ] Update Q001.md: Add Wave, Created, Assigned, Deliverables
- [ ] Update Q002.md: Add Wave, Created, Assigned, Deliverables
- [ ] Update Q003.md: Add Wave, Created, Assigned, Deliverables
- [ ] Update D001.md: Add Wave, Created, Assigned, Deliverables
- [ ] Update D002.md: Add Wave, Created, Assigned, Deliverables
- [ ] Update D003.md: Add Wave, Created, Assigned, Deliverables

## Check Command
Verify all metadata fields are present and Wave is valid:
```bash
for file in /home/ubuntu/projects/zerg-swarm/SWARM/TASKS/QUANT/Q*.md /home/ubuntu/projects/zerg-swarm/SWARM/TASKS/DEX/D*.md; do
  echo "=== $(basename $file) ==="
  grep -E "Wave|Created|Assigned|Deliverables" "$file" || echo "MISSING FIELDS"
done
```

## Constraints
- Preserve all existing content (Objective, Context Pack, Acceptance Criteria)
- Use 2026-01-15 for Created timestamp (today's date)
- Assign each task to Wave based on lane order (Q001-Q003 = Wave 1-3, D001-D003 = Wave 1-3)
- Deliverables should match the task Objective and expected outputs

## Result
(filled by zergling)
