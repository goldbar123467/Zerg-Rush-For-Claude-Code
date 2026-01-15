# Task: META-002

## Metadata
| Field | Value |
|-------|-------|
| Lane | INTEGRATION |
| Type | REFACTOR_TINY |
| Wave | 4 |
| Status | PENDING |
| Created | 2026-01-15 |
| Assigned | ZERGLING-2 |

## Context Pack

### Current State: M001.md
```
# Task: M001

## Metadata
| Field | Value |
|-------|-------| 
| Lane | ML |
| Type | ADD_PURE_FN |
| Wave | - |
| Status | PENDING |

## Objective
Create config loader with args schema for ML training.
...
```

### Issue Summary
M001, M002, M003 in /home/ubuntu/projects/zerg-swarm/SWARM/TASKS/ML/ are missing:
- `Created` timestamp (required)
- `Assigned` field (required)
- Valid `Wave` value (currently "-", should be numeric)
- `Deliverables` section with checkboxes

### Reference: Correct Structure (INT-001)
```
## Metadata
| Field | Value |
|-------|-------|
| Lane | INTEGRATION |
| Type | ADD_STUB |
| Wave | - |
| Status | PENDING |
| Created | 2026-01-15 |
| Assigned | - |

...

## Deliverables
- [ ] Item 1
- [ ] Item 2
...
```

## Objective
Add missing required metadata fields to all three ML tasks (M001, M002, M003):
1. Add `Created` timestamp: 2026-01-15
2. Add `Assigned` field (set to `-` for unassigned)
3. Fix `Wave` field from `-` to `4`
4. Add `Deliverables` section with task-specific checkboxes

## Deliverables
- [ ] Update M001.md: add Created, Assigned, fix Wave, add Deliverables section
- [ ] Update M002.md: add Created, Assigned, fix Wave, add Deliverables section
- [ ] Update M003.md: add Created, Assigned, fix Wave, add Deliverables section
- [ ] Verify all three files have complete metadata tables with 6 fields (Lane, Type, Wave, Status, Created, Assigned)
- [ ] Verify all three files have Deliverables sections with checkboxes

## Acceptance Criteria (INTEGRATION Gate)
- [ ] M001.md contains all 6 metadata fields
- [ ] M002.md contains all 6 metadata fields
- [ ] M003.md contains all 6 metadata fields
- [ ] All Wave values set to `4`
- [ ] All Created timestamps set to `2026-01-15`
- [ ] All Assigned fields present (value: `-`)
- [ ] All three files have Deliverables sections with checkboxes

## Check Command
```bash
for file in M001 M002 M003; do
  echo "=== $file.md ==="
  grep -E "(Created|Assigned|Wave|Deliverables)" /home/ubuntu/projects/zerg-swarm/SWARM/TASKS/ML/${file}.md || echo "MISSING FIELDS"
done
```

## Constraints
- Max 50 lines modified total
- No functional code changes
- No file deletions
- Preserve all existing objective, context pack, and acceptance criteria content

## Notes
This is a metadata synchronization task to ensure all task cards follow the standard format as defined in INT-001 and other INTEGRATION lane tasks. The ML tasks predate this standard and need backfill.

## Wave Info
Wave 4: Metadata cleanup and consistency across all task lanes (KERNEL, ML, INTEGRATION, QUANT, DEX)
