# Task: META-004

## Metadata
| Field | Value |
|-------|-------|
| Lane | INTEGRATION |
| Type | REFACTOR_TINY |
| Wave | 4 |
| Status | PENDING |
| Created | 2026-01-15 |
| Assigned | ZERGLING-4 |

## Context Pack

### Files
- `/home/ubuntu/projects/zerg-swarm/SWARM/TASKS/TEMPLATE.md` (OLD - to delete)
- `/home/ubuntu/projects/zerg-swarm/SWARM/TEMPLATES/TASK_TEMPLATE.md` (NEW - to keep)
- `/home/ubuntu/projects/zerg-swarm/SWARM/FLAWS.md` (references old template)

### Template Comparison

#### Old Template Format (SWARM/TASKS/TEMPLATE.md)
Uses bullet-point metadata:
```markdown
# Task: [TASK_ID]

## Metadata
- **Wave**: X
- **Zergling**: (assigned at runtime)
- **Status**: PENDING | IN_PROGRESS | DONE | PARTIAL | BLOCKED
- **Created**: <timestamp>

## Context
Files to read (ONLY these):
- path/to/file1.py
```

#### New Template Format (SWARM/TEMPLATES/TASK_TEMPLATE.md)
Uses table-based metadata with comprehensive structure:
```markdown
# Task: T[XXX]

## Metadata
| Field | Value |
|-------|-------|
| Lane | KERNEL / ML / QUANT / DEX / INTEGRATION |
| Type | ADD_STUB / ADD_PURE_FN / ... / REFACTOR_TINY |
| Wave | |
| Status | PENDING |
```

### Key Differences
1. **Format**: Old uses bullets, New uses Markdown tables
2. **Metadata fields**: New includes Lane, Type, Assigned; Old includes Zergling
3. **Structure**: New has comprehensive "Context Pack" with subsections
4. **Field names**: "Status" vs complete enumerated options
5. **Organization**: New separates Files, Target Signature, Surrounding Code, Expected Behavior, Check Command

### Surrounding Code

Old template location in codebase:
```
/home/ubuntu/projects/zerg-swarm/SWARM/TASKS/TEMPLATE.md
```

New template location:
```
/home/ubuntu/projects/zerg-swarm/SWARM/TEMPLATES/TASK_TEMPLATE.md
```

Reference found in:
```
/home/ubuntu/projects/zerg-swarm/SWARM/FLAWS.md
```

### Expected Behavior
- Delete the old bullet-format TEMPLATE.md from TASKS directory
- Ensure new table-format TASK_TEMPLATE.md remains the single source of truth
- Update any documentation that references the old template location
- All future tasks use the new template format consistently

### Check Command
```bash
ls -la /home/ubuntu/projects/zerg-swarm/SWARM/TASKS/TEMPLATE.md 2>&1 | grep -q "No such file" && echo "✓ Old template deleted" || echo "✗ Old template still exists"
```

## Objective
Consolidate duplicate task templates by deleting the old bullet-format TEMPLATE.md from SWARM/TASKS and establishing SWARM/TEMPLATES/TASK_TEMPLATE.md as the single authoritative template.

## Deliverables
- [ ] Delete `/home/ubuntu/projects/zerg-swarm/SWARM/TASKS/TEMPLATE.md`
- [ ] Update `/home/ubuntu/projects/zerg-swarm/SWARM/FLAWS.md` to remove reference to old template location
- [ ] Verify no other files reference the old template path
- [ ] Confirm new template is properly documented in SWARM/TEMPLATES/

## Acceptance Criteria (Gate)

### INTEGRATION
- [ ] Wire test: Only SWARM/TEMPLATES/TASK_TEMPLATE.md exists
- [ ] CLI: `ls SWARM/TASKS/TEMPLATE.md` returns file not found
- [ ] Verification: grep shows zero references to old template location in codebase

## Constraints
- Max 100 lines of new code
- Max 2 files to modify
- No architectural changes
- Simple file deletion and documentation update

## Notes
This is a critical metadata consolidation task. The old template uses an inconsistent format (bullets) compared to the new standard (tables). The new template includes comprehensive structure for Context Pack, Acceptance Criteria by lane, and explicit Check Commands. Complete this refactoring to prevent confusion and ensure all zerglings use the correct template format going forward.

**Critical Issue**: FLAWS.md explicitly flags this as a CRITICAL flaw: "Duplicate conflicting templates - `/SWARM/TASKS/TEMPLATE.md` exists but conflicts with `/SWARM/TEMPLATES/TASK_TEMPLATE.md`"
