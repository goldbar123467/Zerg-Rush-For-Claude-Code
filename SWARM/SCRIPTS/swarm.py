#!/usr/bin/env python3
"""Zerg Rush Swarm Manager CLI"""
import json, sys, time, os
from datetime import datetime
from pathlib import Path
import logging

# Setup logging
SWARM_ROOT_TEMP = Path(__file__).parent.parent
LOG_DIR = SWARM_ROOT_TEMP / "LOGS"
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "swarm.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

SWARM_ROOT = SWARM_ROOT_TEMP
STATE_FILE = SWARM_ROOT / "STATE.json"
OUTBOX_DIR = SWARM_ROOT / "OUTBOX"
INBOX_DIR = SWARM_ROOT / "INBOX"
LOCKS_DIR = SWARM_ROOT / "LOCKS"

def acquire_lock(timeout=5):
    """Acquire lock for STATE.json modification."""
    lock_file = LOCKS_DIR / "STATE.lock"
    LOCKS_DIR.mkdir(exist_ok=True)
    start = time.time()
    while lock_file.exists():
        if time.time() - start > timeout:
            raise TimeoutError("Could not acquire lock")
        time.sleep(0.1)
    lock_file.write_text(str(os.getpid()))
    return lock_file

def release_lock():
    """Release lock for STATE.json."""
    lock_file = LOCKS_DIR / "STATE.lock"
    if lock_file.exists():
        lock_file.unlink()

def load_state():
    logger.info("Loading state from %s", STATE_FILE)
    try:
        if not STATE_FILE.exists():
            return {"wave": 0, "active_zerglings": [], "completed_tasks": [], "pending_tasks": [], "last_updated": datetime.now().isoformat()}
        with open(STATE_FILE) as f:
            state = json.load(f)
        # Validate required keys
        required = ['wave', 'active_zerglings', 'completed_tasks', 'pending_tasks', 'last_updated']
        for key in required:
            if key not in state:
                if key.endswith('s'):
                    state[key] = []
                elif key == 'wave':
                    state[key] = 0
                else:
                    state[key] = ''
        return state
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error loading state: {e}", file=sys.stderr)
        return {"wave": 0, "active_zerglings": [], "completed_tasks": [], "pending_tasks": [], "last_updated": ""}

def save_state(state):
    logger.info("Saving state: wave=%d, pending=%d, completed=%d", state.get('wave', 0), len(state.get('pending_tasks', [])), len(state.get('completed_tasks', [])))
    lock = acquire_lock()
    try:
        state["last_updated"] = datetime.now().isoformat()
        temp_file = STATE_FILE.with_suffix('.json.tmp')
        with open(temp_file, 'w') as f:
            json.dump(state, f, indent=2)
        temp_file.replace(STATE_FILE)  # Atomic rename
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error saving state: {e}", file=sys.stderr)
        if temp_file.exists():
            temp_file.unlink()
        raise
    finally:
        release_lock()

def cmd_status(verbose=False):
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
    if verbose:
        if state.get('active_zerglings'):
            print(f"\nActive Zerglings: {state['active_zerglings']}")
        if state.get('pending_tasks'):
            print(f"\nPending Tasks: {state['pending_tasks']}")
        if state.get('completed_tasks'):
            print(f"\nCompleted Tasks (recent): {state['completed_tasks'][-5:]}")

def cmd_new_wave():
    state = load_state()
    state['wave'] += 1
    logger.info("Incrementing wave to %d", state['wave'])
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
    logger.info("Collected %d results", collected)
    print(f"Collected {collected} new results")
    print(f"Total completed: {len(state.get('completed_tasks', []))}")

def cmd_kill(task_id):
    """Remove a task from pending_tasks."""
    state = load_state()
    if task_id in state['pending_tasks']:
        state['pending_tasks'].remove(task_id)
        save_state(state)
        logger.info("Killed task: %s", task_id)
        print(f"Killed task: {task_id}")
    else:
        print(f"Task not found: {task_id}", file=sys.stderr)

def cmd_reset():
    """Reset swarm state to initial values."""
    state = {
        'wave': 0,
        'active_zerglings': [],
        'completed_tasks': [],
        'pending_tasks': [],
        'last_updated': datetime.now().isoformat()
    }
    save_state(state)
    logger.info("Swarm state reset to initial values")
    print("Swarm state reset to initial values")

def cmd_reconcile(fix=False):
    """Reconcile pending_tasks with actual task files."""
    state = load_state()
    actual_tasks = set()
    tasks_dir = SWARM_ROOT / "TASKS"
    for lane in ['KERNEL', 'ML', 'QUANT', 'DEX', 'INTEGRATION']:
        lane_dir = tasks_dir / lane
        if lane_dir.exists():
            for f in lane_dir.glob("*.md"):
                if f.name != "README.md":
                    actual_tasks.add(f"{lane}/{f.stem}")
    outbox = SWARM_ROOT / "OUTBOX"
    if outbox.exists():
        for f in outbox.glob("*.md"):
            actual_tasks.add(f.stem)
    pending = set(state['pending_tasks'])
    missing_in_state = actual_tasks - pending
    orphaned_in_state = pending - actual_tasks
    print(f"Tasks in files but not in state: {len(missing_in_state)}")
    for t in sorted(missing_in_state):
        print(f"  + {t}")
    print(f"Tasks in state but no file: {len(orphaned_in_state)}")
    for t in sorted(orphaned_in_state):
        print(f"  - {t}")
    if fix:
        state['pending_tasks'] = sorted(actual_tasks)
        save_state(state)
        print("State reconciled with task files")

def main():
    if len(sys.argv) < 2:
        print("Usage: swarm.py [status|wave|tasks|results|collect|kill|reset|reconcile] [options]")
        sys.exit(1)
    cmd = sys.argv[1].lower()
    verbose = '-v' in sys.argv or '--verbose' in sys.argv
    
    if cmd == 'status':
        cmd_status(verbose=verbose)
    elif cmd == 'wave':
        cmd_new_wave()
    elif cmd == 'tasks':
        cmd_list_tasks()
    elif cmd == 'results':
        cmd_list_results()
    elif cmd == 'collect':
        cmd_collect()
    elif cmd == 'kill':
        if len(sys.argv) < 3:
            print("Usage: swarm.py kill <task_id>")
            sys.exit(1)
        cmd_kill(sys.argv[2])
    elif cmd == 'reset':
        cmd_reset()
    elif cmd == 'reconcile':
        fix = '--fix' in sys.argv[2:]
        cmd_reconcile(fix=fix)
    else:
        print(f"Unknown command: {cmd}")
        print("Available: status, wave, tasks, results, collect, kill, reset, reconcile")
        sys.exit(1)

if __name__ == "__main__":
    main()
