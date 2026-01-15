#!/usr/bin/env python3
"""Zerg Rush Swarm Manager CLI"""
import json, sys
from datetime import datetime
from pathlib import Path

SWARM_ROOT = Path(__file__).parent.parent
STATE_FILE = SWARM_ROOT / "STATE.json"
OUTBOX_DIR = SWARM_ROOT / "OUTBOX"
INBOX_DIR = SWARM_ROOT / "INBOX"

def load_state():
    if not STATE_FILE.exists():
        return {"wave": 0, "active_zerglings": [], "completed_tasks": [], "pending_tasks": [], "last_updated": datetime.now().isoformat()}
    with open(STATE_FILE) as f:
        return json.load(f)

def save_state(state):
    state["last_updated"] = datetime.now().isoformat()
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def cmd_status():
    state = load_state()
    print(f"=== SWARM STATUS ===")
    print(f"Wave: {state['wave']}")
    print(f"Active Zerglings: {len(state.get('active_zerglings', []))}")
    print(f"Pending Tasks: {len(state.get('pending_tasks', []))}")
    print(f"Completed Tasks: {len(state.get('completed_tasks', []))}")
    print(f"Last Updated: {state.get('last_updated', 'N/A')}")
    outbox_count = len(list(OUTBOX_DIR.glob("*.md"))) if OUTBOX_DIR.exists() else 0
    inbox_count = len(list(INBOX_DIR.glob("*.md"))) if INBOX_DIR.exists() else 0
    print(f"\nOutbox Tasks: {outbox_count}")
    print(f"Inbox Results: {inbox_count}")

def cmd_new_wave():
    state = load_state()
    state['wave'] += 1
    save_state(state)
    print(f"Wave incremented to: {state['wave']}")

def cmd_list_tasks():
    if not OUTBOX_DIR.exists():
        print("No tasks (OUTBOX doesn't exist)")
        return
    tasks = list(OUTBOX_DIR.glob("*.md"))
    if not tasks:
        print("No pending tasks in OUTBOX")
        return
    print(f"=== PENDING TASKS ({len(tasks)}) ===")
    for task in sorted(tasks):
        print(f"  - {task.name}")

def cmd_list_results():
    if not INBOX_DIR.exists():
        print("No results (INBOX doesn't exist)")
        return
    results = list(INBOX_DIR.glob("*.md"))
    if not results:
        print("No results in INBOX")
        return
    print(f"=== RESULTS ({len(results)}) ===")
    for result in sorted(results):
        print(f"  - {result.name}")

def cmd_collect():
    if not INBOX_DIR.exists():
        print("INBOX doesn't exist, nothing to collect")
        return
    results = list(INBOX_DIR.glob("*.md"))
    if not results:
        print("No results to collect")
        return
    state = load_state()
    collected = 0
    for result in results:
        task_id = result.stem
        if task_id not in state.get('completed_tasks', []):
            state.setdefault('completed_tasks', []).append(task_id)
            collected += 1
        if task_id in state.get('pending_tasks', []):
            state['pending_tasks'].remove(task_id)
    save_state(state)
    print(f"Collected {collected} new results")
    print(f"Total completed: {len(state.get('completed_tasks', []))}")

def main():
    if len(sys.argv) < 2:
        print("Usage: swarm.py [status|wave|tasks|results|collect]")
        sys.exit(1)
    cmd = sys.argv[1].lower()
    commands = {'status': cmd_status, 'wave': cmd_new_wave, 'tasks': cmd_list_tasks, 'results': cmd_list_results, 'collect': cmd_collect}
    if cmd not in commands:
        print(f"Unknown command: {cmd}")
        print("Available: status, wave, tasks, results, collect")
        sys.exit(1)
    commands[cmd]()

if __name__ == "__main__":
    main()
