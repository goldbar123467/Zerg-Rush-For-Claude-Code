# WAVE 28: BUG FIXES AND STABILITY

## Executive Summary

Code review identified **23 bugs** across 5 categories:
1. Error Handling (7 issues)
2. State Management (5 issues)
3. Daemon Stability (4 issues)
4. MCP Connection (4 issues)
5. Input Handling (3 issues)

---

## CRITICAL BUGS (Fix First)

### BUG-021: Terminal Not Restored on Crash
**File**: `cli.py:710-729`
**Problem**: If exception in `TerminalInput`, terminal left in raw mode
**Fix**: Add atexit and signal handlers for cleanup

### BUG-011: save_state() Can Corrupt STATE.json
**File**: `cli.py:519-531`
**Problem**: No fsync, orphaned temp files on crash
**Fix**: Add fsync and cleanup

### BUG-016: Race Condition in Daemon Callbacks
**File**: `cli.py:1713-1755`
**Problem**: Daemon callbacks modify state.radio_events from async while main loop reads sync
**Fix**: Use thread-safe queue

---

## ERROR HANDLING BUGS

### BUG-001: Silent MCP Connection Failure
**File**: `cli.py:402-416`
**Fix**: Return (success, error_message) tuple

### BUG-002: RAG Client Swallows Exceptions
**File**: `rag_client.py:115-133`
**Fix**: Add `last_error` tracking to RAGClient

### BUG-004: mcp_call() No Timeout
**File**: `cli.py:419-426`
**Fix**: Add configurable timeout (default 10s)

### BUG-005: File Read Without Encoding
**File**: `cli.py:614-639`
**Fix**: Use `encoding='utf-8', errors='replace'`

### BUG-006: Spawner No Error Details
**File**: `spawner.py:263-276`
**Fix**: Return `(worker, error_message)` tuple

---

## STATE MANAGEMENT BUGS

### BUG-008: Race in init_worker_pool()
**File**: `cli.py:152-175`
**Fix**: Use copy-and-swap pattern

### BUG-009: radio_events Unbounded Growth
**File**: `cli.py:131-149`
**Fix**: Centralize with single MAX_RADIO_EVENTS constant

### BUG-010: State Lost on refresh_state() Fallback
**File**: `cli.py:534-570`
**Fix**: Preserve daemon state, radio events, cemetery

### BUG-012: completed_workers Never Cleaned
**File**: `cli.py:258-268`
**Fix**: Cap at MAX_COMPLETED_WORKERS

---

## DAEMON STABILITY BUGS

### BUG-013: Researcher Watch Loop No Backoff
**File**: `daemons/researcher.py:158-199`
**Fix**: Exponential backoff on errors

### BUG-014: Teacher No Retry per Lane
**File**: `daemons/teacher.py:97-105`
**Fix**: 3 retries per lane with error tracking

### BUG-015: Daemon Stop Doesn't Wait
**File**: `daemons/researcher.py:115-136`
**Fix**: Wait for tasks with timeout

---

## MCP CONNECTION BUGS

### BUG-017: No Auto-Reconnection
**File**: `mcp_client.py`
**Fix**: Add reconnection manager with backoff

### BUG-018: WebSocket State Drift
**File**: `mcp_client.py:43-52`
**Fix**: Property-based `is_connected` check

### BUG-019: Timeout Too Short
**File**: `mcp_client.py:76`
**Fix**: Configurable per-operation timeouts

### BUG-020: aiohttp Session Not Closed
**File**: `rag_client.py:107-113`
**Fix**: Add context manager, cleanup in finally

---

## INPUT HANDLING BUGS

### BUG-022: Arrow Keys Incomplete
**File**: `cli.py:738-749`
**Fix**: Handle HOME, END, PGUP, PGDN

### BUG-023: Decompose Goal No Limit
**File**: `cli.py:1524-1543`
**Fix**: Cap at 500 chars

---

## TASK BREAKDOWN

### Wave 28.1: Error Handling (5 tasks)
| ID | Bug | Lines | File |
|----|-----|-------|------|
| W28-001 | BUG-001 | ~20 | cli.py |
| W28-002 | BUG-002 | ~30 | rag_client.py |
| W28-003 | BUG-004 | ~20 | cli.py |
| W28-004 | BUG-005 | ~15 | cli.py |
| W28-005 | BUG-006 | ~30 | spawner.py |

### Wave 28.2: State Management (5 tasks)
| ID | Bug | Lines | File |
|----|-----|-------|------|
| W28-006 | BUG-008 | ~25 | cli.py |
| W28-007 | BUG-009 | ~15 | cli.py |
| W28-008 | BUG-010 | ~50 | cli.py |
| W28-009 | BUG-011 | ~20 | cli.py |
| W28-010 | BUG-012 | ~15 | cli.py |

### Wave 28.3: Daemon Stability (4 tasks)
| ID | Bug | Lines | File |
|----|-----|-------|------|
| W28-011 | BUG-013 | ~25 | daemons/researcher.py |
| W28-012 | BUG-014 | ~30 | daemons/teacher.py |
| W28-013 | BUG-015 | ~25 | both daemon files |
| W28-014 | BUG-016 | ~40 | cli.py |

### Wave 28.4: MCP & Connections (4 tasks)
| ID | Bug | Lines | File |
|----|-----|-------|------|
| W28-015 | BUG-017 | ~40 | mcp_client.py |
| W28-016 | BUG-018 | ~15 | mcp_client.py |
| W28-017 | BUG-019 | ~20 | mcp_client.py |
| W28-018 | BUG-020 | ~20 | rag_client.py |

### Wave 28.5: Input & Terminal (3 tasks)
| ID | Bug | Lines | File |
|----|-----|-------|------|
| W28-019 | BUG-021 | ~25 | cli.py |
| W28-020 | BUG-022 | ~30 | cli.py |
| W28-021 | BUG-023 | ~10 | cli.py |

---

## PRIORITY ORDER

**CRITICAL** (data loss/crash risk):
1. BUG-021 - Terminal restoration
2. BUG-011 - save_state corruption
3. BUG-016 - Thread-safe events

**HIGH** (major UX impact):
4. BUG-017 - Auto-reconnection
5. BUG-010 - State preservation
6. BUG-013 - Researcher backoff

**MEDIUM**: 7-15 remaining bugs

**LOW**: 16-23 edge cases

---

## SUCCESS CRITERIA

- [ ] Terminal always restored on exit/crash
- [ ] STATE.json never corrupted
- [ ] No race conditions on events
- [ ] MCP auto-reconnects on disconnect
- [ ] Daemons recover from errors gracefully
- [ ] All error messages visible to user
