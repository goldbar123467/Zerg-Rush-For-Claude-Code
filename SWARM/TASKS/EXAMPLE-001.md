# Task: EXAMPLE-001

## Metadata
- **Wave**: 1
- **Zergling**: ZERGLING-1
- **Status**: DONE
- **Created**: 2026-01-15T10:30:00Z

## Context
Files to read (ONLY these):
- /home/ubuntu/projects/zerg-swarm/src/utils/validator.py
- /home/ubuntu/projects/zerg-swarm/tests/test_validator.py

## Objective
Add input validation function for email addresses with unit tests.

## Deliverables
- [x] Created `validate_email()` function in validator.py
- [x] Added 5 test cases in test_validator.py covering valid/invalid emails

## Constraints
- Max 100 lines
- Max 2 files
- No dependencies

## Result
Successfully implemented email validation using regex pattern. Added tests for:
- Valid standard email
- Invalid missing @ symbol
- Invalid missing domain
- Valid email with subdomain
- Invalid empty string

Total lines: 47 (validator.py: 12, test_validator.py: 35)
Execution time: 2m 15s
All tests passing.
