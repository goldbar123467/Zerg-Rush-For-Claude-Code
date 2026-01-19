<div align="center">

```
                                        ██
                                      ██░░██
                                    ██░░░░░░██
                          ██████  ██░░░░░░░░░░██  ██████
                        ██░░░░░░██░░░░░░░░░░░░░░██░░░░░░██
                      ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██
                    ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██
                  ██░░░░░░░░░░██████░░░░░░░░██████░░░░░░░░░░░░██
                ██░░░░░░░░░░██▓▓▓▓▓▓██░░░░██▓▓▓▓▓▓██░░░░░░░░░░░░██
              ██░░░░░░░░░░░░██▓▓██▓▓██░░░░██▓▓██▓▓██░░░░░░░░░░░░░░██
            ██░░░░░░░░░░░░░░░░██████░░░░░░░░██████░░░░░░░░░░░░░░░░░░██
          ██░░░░░░░░░░░░░░░░░░░░░░░░░░██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██
        ██░░░░░░░░░░░░░░░░░░░░░░░░░░██████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██
      ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██
    ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██
      ██░░░░██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██░░░░██
        ████  ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██  ████
                ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██
                  ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░████
                      ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░████
                          ████░░░░░░░░░░░░░░░░░░░░████
                              ████░░░░░░░░░░░░████
                                  ██████████
                                    ██░░██
                                  ██░░░░░░██
                                ██░░░░░░░░░░██
                              ██░░░░░░░░░░░░░░██
                                ██░░░░░░░░░░██
                                  ██░░░░░░██
                                    ██████


███████╗███████╗██████╗  ██████╗     ██████╗ ██╗   ██╗███████╗██╗  ██╗
╚══███╔╝██╔════╝██╔══██╗██╔════╝     ██╔══██╗██║   ██║██╔════╝██║  ██║
  ███╔╝ █████╗  ██████╔╝██║  ███╗    ██████╔╝██║   ██║███████╗███████║
 ███╔╝  ██╔══╝  ██╔══██╗██║   ██║    ██╔══██╗██║   ██║╚════██║██╔══██║
███████╗███████╗██║  ██║╚██████╔╝    ██║  ██║╚██████╔╝███████║██║  ██║
╚══════╝╚══════╝╚═╝  ╚═╝ ╚═════╝     ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝
                        FOR CLAUDE CODE
```

# Swarm Rush

**Spawn. Bite. Die. Repeat.**

*A disposable agent orchestration system for parallel task execution*

[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![Claude](https://img.shields.io/badge/Claude-Code-purple.svg)](https://claude.ai)
[![Status](https://img.shields.io/badge/status-alpha-orange.svg)]()

[![Agents](https://img.shields.io/badge/agents-disposable-critical.svg)]()
[![TTL](https://img.shields.io/badge/TTL-4_minutes-yellow.svg)]()
[![Max Lines](https://img.shields.io/badge/max_lines-100-blue.svg)]()

</div>

---

## Overview

Traditional AI agents are **long-lived**, **context-heavy**, and **slow**.

Swarm Rush agents are **disposable**, **low-context**, and **fast**.

> 💡 Think of it like a hive: thousands of simple workers, each doing one small task, dying quickly, replaced instantly.

### The Problem

| Traditional Agents | Swarm Agents |
|-------------------|--------------|
| Long-running sessions | 4-minute TTL |
| Accumulate context | Fresh each spawn |
| One agent, many tasks | One agent, one task |
| Slow, careful | Fast, disposable |
| Failure = restart everything | Failure = respawn one worker |

### Core Philosophy

```
┌─────────────────────────────────────────┐
│  SPAWN  →  BITE  →  DIE  →  REPEAT     │
└─────────────────────────────────────────┘
```

1. **Short-lived workers** — Agents complete exactly one task, then terminate
2. **Hard time limits** — 4-minute TTL enforced, no exceptions
3. **Small code deltas** — Maximum 100 new lines per task
4. **Low context by design** — Workers only see what they need
5. **Partial work is expected** — Optimized for throughput, not completeness

### Agent Roles

| Role | Symbol | Purpose |
|------|--------|---------|
| **Overlord** | 👁️ | Decomposes tasks, coordinates waves, merges results |
| **Worker** | 🐝 | Executes one microtask, reports result, dies |
| **Queen** | 👑 | (Optional) Refactors and stabilizes after rush |
| **Spine** | 🛡️ | (Optional) QA validation, files bug tasks |

---

## Architecture

### Project Structure

```
zerg-swarm/
│
├── SWARM/                          # 🐝 Swarm coordination
│   ├── STATE.json                  # ⚡ Wave counter, task status
│   ├── SWARM_RULES.md              # 📜 Master rules document
│   ├── GATES.md                    # 🚪 Lane acceptance criteria
│   ├── PROMPTS.md                  # 💬 Copy-paste role prompts
│   ├── RUNBOOK.md                  # 📖 Operational playbook
│   │
│   ├── TASKS/                      # 🛤️ Task lanes
│   │   ├── KERNEL/                 # 🔥 CUDA, Triton, CUTLASS
│   │   ├── ML/                     # 🧠 Models, training, data
│   │   ├── QUANT/                  # 📊 Strategy, backtests
│   │   ├── DEX/                    # 💱 Solana, Jupiter, Jito
│   │   └── INTEGRATION/            # 🔗 Glue, CLI, wiring
│   │
│   ├── OUTBOX/                     # 📤 Assigned tasks
│   ├── INBOX/                      # 📥 Completed results
│   ├── SCRIPTS/                    # ⚙️ CLI tools
│   └── LOCKS/                      # 🔒 File reservations
│
├── src/orson/                      # 🏛️ Orson CLI
│   ├── cli.py                      # Main TUI application
│   ├── state.py                    # State management
│   ├── rag_client.py               # RAG Brain client
│   └── buildings/                  # Town buildings
│       ├── museum.py               # 🏛️ Data vault
│       ├── apartments.py           # 🏢 Agent pool
│       ├── school.py               # 🏫 Training center
│       ├── mcdonalds.py            # 🍟 Quick tasks
│       ├── newspaper.py            # 📰 File watcher + RAG
│       └── brain.py                # 🧠 RAG panel
│
└── zerg_swarm_mcp/                 # MCP Server
```

### Wave Execution Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         WAVE EXECUTION                              │
└─────────────────────────────────────────────────────────────────────┘

     👁️ OVERLORD                    🐝 WORKERS                📥 INBOX
         │                              │                         │
         │  1. Decompose goal           │                         │
         │     into 5 microtasks        │                         │
         ├──────────────────────────────┤                         │
         │                              │                         │
         │  2. Spawn wave               │                         │
         │     (4-min TTL each)         │                         │
         ├────────────► Worker 1 ──────────────────────►  ✅ DONE  │
         ├────────────► Worker 2 ──────────────────────►  ✅ DONE  │
         ├────────────► Worker 3 ──────────────────────►  ⚠️ PARTIAL
         ├────────────► Worker 4 ──────────────────────►  ✅ DONE  │
         ├────────────► Worker 5 ──────────────────────►  🚫 BLOCKED
         │                              │                         │
         │  3. All workers terminate    │                         │
         │                         💀 💀 💀 💀 💀                  │
         │                                                        │
         │  4. Collect results  ◄─────────────────────────────────┤
         │     - Merge DONE                                       │
         │     - Split PARTIAL → new tasks                        │
         │     - Resolve BLOCKED                                  │
         │                                                        │
         │  5. Next wave...                                       │
         └────────────────────────────────────────────────────────┘
```

### Worker Lifecycle

```
┌──────────────────────────────────────────────────────────────┐
│                    WORKER LIFECYCLE                          │
└──────────────────────────────────────────────────────────────┘

   🥚 SPAWN          📋 REGISTER        🔒 LOCK           ⚡ EXECUTE
      │                  │                │                   │
      │   Get task       │   Reserve      │   Start timer     │
      │   card           │   files        │   (4 min)         │
      ▼                  ▼                ▼                   ▼
  ┌───────┐         ┌────────┐       ┌────────┐        ┌──────────┐
  │ Birth │ ──────► │Register│ ────► │ Lock   │ ─────► │  Work    │
  └───────┘         │to Swarm│       │ Files  │        │  Loop    │
                    └────────┘       └────────┘        └────┬─────┘
                                                            │
      ┌─────────────────────────────────────────────────────┘
      │
      │         ┌─────────────┐
      │         │   Result?   │
      ▼         └──────┬──────┘
                       │
        ┌──────────────┼──────────────┬──────────────┐
        ▼              ▼              ▼              ▼
    ┌───────┐     ┌────────┐     ┌────────┐    ┌─────────┐
    │✅ DONE│     │⚠️PARTIAL│     │🚫BLOCKED│    │❌ FAILED│
    └───┬───┘     └────┬───┘     └────┬───┘    └────┬────┘
        │              │              │              │
        └──────────────┴──────────────┴──────────────┘
                               │
                               ▼
   📤 REPORT           🔓 RELEASE           💀 DIE
      │                    │                  │
      │   Write result     │   Free locks     │   Terminate
      │   to INBOX         │                  │
      ▼                    ▼                  ▼
  ┌────────┐          ┌────────┐         ┌────────┐
  │ Write  │ ───────► │Release │ ──────► │  End   │
  │ Result │          │ Locks  │         │Process │
  └────────┘          └────────┘         └────────┘

   ⏱️ Constraints:
   ┌────────────────────┐
   │ • 4 min max        │
   │ • 100 lines max    │
   │ • 2 files max      │
   │ • No state kept    │
   └────────────────────┘
```

### Lane Isolation

```
┌──────────────────────────────────────────────────────────────┐
│                    🌊 WAVE 1 - LANE ISOLATION                │
└──────────────────────────────────────────────────────────────┘

  🔥 KERNEL LANE                    🧠 ML LANE
  ┌─────────────────┐               ┌─────────────────┐
  │                 │               │                 │
  │  K001           │               │  M001           │
  │  ADD_PURE_FN    │      ❌       │  ADD_STUB       │
  │                 │   NO CROSS    │                 │
  │  K002           │◄────────────►│  M002           │
  │  ADD_TEST       │               │  ADD_TEST       │
  │                 │               │                 │
  │  K003           │               │                 │
  │  ADD_BENCH      │               │                 │
  │                 │               │                 │
  └─────────────────┘               └─────────────────┘
          │                                 │
          └────────────┬────────────────────┘
                       ▼
               ┌───────────────┐
               │  📥 RESULTS   │
               └───────────────┘

  Lane Rules:
  ✓ One lane per task
  ✓ Single-lane waves are fastest
  ✓ Mixed waves: max 3+2 across 2 lanes
  ✗ Never more than 2 lanes per wave
  ✗ Never cross lanes within a task
```

---

## Orson CLI

> *"The hive wears flannel."*

Orson is a Rich-based terminal UI themed as a small Midwestern town. Each "building" represents a different swarm function.

```
     ██████╗ ██████╗ ███████╗ ██████╗ ███╗   ██╗
    ██╔═══██╗██╔══██╗██╔════╝██╔═══██╗████╗  ██║
    ██║   ██║██████╔╝███████╗██║   ██║██╔██╗ ██║
    ██║   ██║██╔══██╗╚════██║██║   ██║██║╚██╗██║
    ╚██████╔╝██║  ██║███████║╚██████╔╝██║ ╚████║
     ╚═════╝ ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═══╝
```

### Starting Orson

```bash
# From project root
python orson_cli.py

# Or from src
python -m src.orson.cli
```

### Town Buildings

| Building | Icon | Key | Function | Description |
|----------|------|-----|----------|-------------|
| **Town Hall** | 🏛️ | - | Overlord Control | Wave management, status display |
| **Grain Silo** | 🏭 | `1` | KERNEL Lane | GPU processing - CUDA, Triton, CUTLASS |
| **Public Library** | 📚 | `2` | ML Lane | Model storage - training, inference |
| **First National Bank** | 🏦 | `3` | QUANT Lane | Strategy vault - backtests, signals |
| **Gas-N-Sip** | ⛽ | `4` | DEX Lane | Fuel station - Solana, Jupiter, Jito |
| **Post Office** | 📮 | `5` | INTEGRATION Lane | Mail room - INBOX/OUTBOX, CLI glue |
| **Cemetery** | 🪦 | - | Worker Graveyard | Completed workers display (Peaceful Acres Memorial) |
| **Museum** | 🏛️ | `m` | Data Vault | Wave history, worker stats, RAG concepts |
| **Apartments** | 🏢 | - | Agent Pool | Idle workers waiting for assignment |
| **School** | 🏫 | `t` | Training Center | Prompts, curricula, lane knowledge |
| **McDonald's** | 🍟 | `f` | Quick Tasks | Fast food - bypass wave system |
| **Newspaper** | 📰 | `n` | Researcher | File watching, RAG storage |
| **Brain** | 🧠 | `b` | RAG Brain | Memory stats, concept browser |

### Layout Overview

```
+------------------------------------------------------------------+
|  ORSON - The Hive Wears Flannel  |  Wave: 3  |  Daemons...       |
+------------------------------------------------------------------+
| [1] KERNEL | [2] ML | [3] QUANT | [4] DEX | [5] INTEGRATION      |
|   P:2 D:5  |  P:1 D:3 |  P:0 D:2 |  P:3 D:1 |  P:1 D:4           |
+------------------------------------------------------------------+
|                    |                                              |
|   Tasks: KERNEL    |   Zerglings          |   Inbox (3)          |
|   +-----------+    |   +--------------+   |   +---------------+  |
|   | K001 DONE |    |   | BlueLake w3  |   |   | K001_RESULT   |  |
|   | K002 PEND |    |   | RedMtn w3    |   |   | M002_RESULT   |  |
|   | K003 PROG |    |   +--------------+   |   +---------------+  |
|   +-----------+    |                      |                      |
+------------------------------------------------------------------+
|  d=Decompose  s=Spawn  c=Collect  m=Museum  n=News  r=Refresh    |
+------------------------------------------------------------------+
|  Status: Wave 3 spawned! "The swarm hungers."                    |
+------------------------------------------------------------------+
```

### Key Bindings

#### Main Navigation

| Key | Action |
|-----|--------|
| `1` - `5` | Select lane building (Silo, Library, Bank, Gas-N-Sip, Post Office) |
| `LEFT` / `RIGHT` | Navigate between buildings |
| `UP` / `DOWN` | Navigate within lists |

#### Wave Operations

| Key | Action |
|-----|--------|
| `d` | **Decompose** - Enter goal to split into 5 microtasks |
| `s` | **Spawn** wave (press twice to confirm) |
| `c` | **Collect** results from inbox |
| `v` | **View** selected task detail |

#### Building Toggles

| Key | Action |
|-----|--------|
| `m` | Toggle **Museum** (data vault) |
| `t` | Toggle **School** (training center) |
| `f` | Toggle **McDonald's** (quick tasks) |
| `n` | Toggle **Newspaper** (researcher) |
| `b` | Toggle **Brain** panel (RAG stats) |

#### General

| Key | Action |
|-----|--------|
| `r` | Refresh state from disk/MCP |
| `h` | Show help |
| `q` / `Ctrl+C` | Quit |
| `Esc` | Close modal / Cancel input |

### Newspaper Building (📰)

File watcher and RAG integration hub.

| Key | Action |
|-----|--------|
| `a` | Add research (enter input mode) |
| `p` | Process queue to RAG |
| `Enter` | Submit input |
| `Esc` | Close / Cancel |

### Museum Navigation (🏛️)

| Key | Action |
|-----|--------|
| `UP` / `DOWN` | Select concept |
| `Enter` | View concept detail |
| `r` | Refresh concepts from RAG |
| `Esc` | Close museum / Back from detail |

### Daemon Status Indicators

The header displays real-time daemon status:

```
┌─────────────────────────────────────────────────────────────────┐
│ ORSON - The Hive Wears Flannel  |  Wave: 3  |  Zerglings: 5    │
│                                                                 │
│  🔍 ON  │  👩‍🏫 ON  │  🧠 🟢  │  🐝 🟢                            │
└─────────────────────────────────────────────────────────────────┘
```

| Indicator | Meaning |
|-----------|---------|
| 🔍 | **Researcher** - Newspaper file watcher (ON/OFF) |
| 👩‍🏫 | **Teacher** - School knowledge injector (ON/OFF) |
| 🧠 | **RAG Brain** - Memory connection (🟢 connected / 🔴 disconnected) |
| 🐝 | **Zerg MCP** - Swarm server connection (🟢 connected / 🔴 disconnected) |

### Decompose Workflow

1. Press `d` to enter decompose mode
2. Type your goal (e.g., "Add CUDA kernel for matrix multiply")
3. Press `Enter` to submit
4. Orson creates 5 balanced microtasks:
   - 2 implementation (ADD_STUB, ADD_PURE_FN)
   - 2 validation (ADD_TEST, ADD_ASSERTS)
   - 1 quality (DOC_SNIPPET)

### Spawn Confirmation

Spawning a wave requires confirmation to prevent accidents:

```
Press 's' once  →  "Press 's' again to confirm wave spawn"
Press 's' again →  Wave spawned!
Press any other →  Spawn cancelled
```

---

## RAG Brain Integration

The system uses RAG Brain for persistent memory across agent sessions.

### Quality Gatekeeper

All memories are scored by a quality gatekeeper:

| Score | Icon | Label | Action |
|-------|------|-------|--------|
| ≥ 0.7 | 🟢 | Good memory | Stored and indexed |
| 0.4-0.7 | 🟡 | Accepted | Stored with lower priority |
| < 0.4 | 🔴 | Rejected | Blocked by gatekeeper |

### Memory Operations

```
┌──────────────────────────────────────────────────────────────┐
│                    RAG BRAIN FLOW                            │
└──────────────────────────────────────────────────────────────┘

  📰 NEWSPAPER                     🧠 RAG BRAIN
  (Researcher)                     (Memory Store)
      │                                 │
      │  1. File changes detected       │
      │     (src/, tests/, SWARM/)      │
      │                                 │
      │  2. Queue for research          │
      │                                 │
      │  3. Process & chunk             │
      │     └── Code by function        │
      │     └── Text by paragraph       │
      │                                 │
      │  4. Store to RAG ─────────────► │  Quality gate
      │                                 │  Score ≥ 0.4?
      │                                 │      │
      │                                 │   ┌──┴──┐
      │                                 │   │ Yes │ → Store
      │                                 │   └──┬──┘
      │  5. Receive quality score ◄──── │      │
      │     🟢 🟡 🔴                     │   ┌──┴──┐
      │                                 │   │ No  │ → Reject
      └─────────────────────────────────┘   └─────┘
```

### Worker Death Feedback Loop

```
┌──────────────────────────────────────────────────────────────┐
│                 CEMETERY FEEDBACK LOOP                       │
└──────────────────────────────────────────────────────────────┘

   🐝 WORKER                  🪦 CEMETERY              🧠 RAG BRAIN
      │                           │                        │
      │  1. Worker spawns         │                        │
      │     with memory_id        │                        │
      │                           │                        │
      │  2. Worker dies           │                        │
      │     (DONE/PARTIAL/BLOCKED)│                        │
      │                           │                        │
      └──────────────────────────►│  3. Record death       │
                                  │     - status           │
                                  │     - lines written    │
                                  │     - memory_id        │
                                  │                        │
                                  │  4. Send feedback ────►│
                                  │                        │
                                  │     DONE → helpful=true│
                                  │     PARTIAL → helpful=false
                                  │     BLOCKED → helpful=false
                                  │                        │
                                  │  5. Store wave ───────►│
                                  │     outcome            │
                                  │     (wave summary)     │
                                  │                        │
```

### RAG Client API

```python
from src.orson.rag_client import RAGClient

client = RAGClient()

# Store a memory
result = await client.remember(
    content="Important insight about architecture",
    category="insight",
    tags=["architecture", "decision"]
)

# Recall memories
memories = await client.recall("architecture patterns", limit=10)

# Provide feedback
await client.feedback(memory_id="123", helpful=True)

# Get stats
stats = await client.stats()

# Get concepts
concepts = await client.concepts()
```

### Categories

| Category | Use Case |
|----------|----------|
| `insight` | Architectural decisions, learnings |
| `code_snippet` | Function implementations, patterns |
| `error` | Bug fixes, failure modes |
| `task_outcome` | Wave results, worker deaths |

---

## Quick Start

### Prerequisites

- Python 3.10+
- Claude Code CLI

### Installation

```bash
git clone https://github.com/yourusername/swarm-rush.git
cd swarm-rush
pip install -e .
```

### Your First Wave

```bash
# Check swarm status
python SWARM/SCRIPTS/swarm.py status

# View pending tasks
python SWARM/SCRIPTS/swarm.py tasks

# Start Orson CLI
python orson_cli.py
```

---

## Usage

### 1. Compose a Wave

Select 5 tasks following the wave template:

| Slot | Type | Example |
|------|------|---------|
| 1 | Implementation | `ADD_PURE_FN` |
| 2 | Implementation | `ADD_STUB` |
| 3 | Validation | `ADD_TEST` |
| 4 | Validation | `ADD_ASSERTS` |
| 5 | Quality | `ADD_BENCH` |

### 2. Spawn Workers

In Orson CLI:
1. Press `d` to decompose your goal
2. Press `s` twice to spawn the wave

Or manually open 5 Claude Code sessions with:

```
You are WORKER-N. Complete exactly ONE task and STOP.
TTL: 4 minutes | Max: 100 lines | Files: 2 max
```

### 3. Collect Results

```bash
# Via CLI
python SWARM/SCRIPTS/swarm.py collect

# Or in Orson, press 'c'
```

### 4. Repeat

```
┌──────────────────────────────────────┐
│  Wave 1  →  Wave 2  →  Wave 3  → ... │
│   5 tasks    5 tasks    5 tasks      │
└──────────────────────────────────────┘
```

---

## Lanes

Workers operate in **isolated lanes** to minimize context and prevent cross-domain contamination.

| Lane | Domain | Keywords |
|------|--------|----------|
| 🔥 `KERNEL` | CUDA, Triton, CUTLASS, GPU ops | `gpu`, `kernel`, `triton` |
| 🧠 `ML` | Models, training, data pipelines | `model`, `train`, `loss` |
| 📊 `QUANT` | Strategy, backtests, signals | `backtest`, `sharpe`, `signal` |
| 💱 `DEX` | Solana, Jupiter, transactions | `solana`, `swap`, `tx` |
| 🔗 `INTEGRATION` | Glue, CLI, wiring only | `cli`, `config`, `wire` |

---

## Hard Constraints

Every worker obeys these **non-negotiable** limits:

| Constraint | Limit | Enforced By |
|------------|-------|-------------|
| ⏱️ **Timebox** | 4 minutes | Worker prompt |
| 📏 **Max Lines** | 100 new lines | Self-check |
| 📁 **Max Files** | 2 (2nd for tests only) | Task card |
| 📦 **Dependencies** | None new | Worker prompt |
| 🏗️ **Architecture** | No decisions | OVERLORD only |
| 🔍 **Exploration** | Touch list only | BLOCKED if needed |

### What Happens When Limits Hit

```
Time runs out     →  Return PARTIAL + progress notes
Lines exceeded    →  Return PARTIAL + split suggestion
Need more files   →  Return BLOCKED + file list
Can't proceed     →  Return BLOCKED + blocker description
```

---

## Task Types

| Type | Description | Typical Output |
|------|-------------|----------------|
| `ADD_STUB` | Skeleton + TODOs | Class outline |
| `ADD_PURE_FN` | One function + doc | Single function |
| `ADD_TEST` | 1-3 test cases | Test file |
| `FIX_ONE_BUG` | Single bug fix | Minimal change |
| `ADD_ASSERTS` | Runtime checks | Guard statements |
| `ADD_METRIC` | Metric + logging | Metric code |
| `ADD_BENCH` | Benchmark snippet | Timing code |
| `DOC_SNIPPET` | Documentation | README section |
| `REFACTOR_TINY` | Rename/move | No behavior change |

---

## Gates

Each lane has **acceptance criteria** that must pass before marking DONE:

| Lane | Gate Checks |
|------|-------------|
| 🔥 KERNEL | Correctness (CPU match) + Benchmark (1 shape) |
| 🧠 ML | Tests pass OR smoke-run + No import breaks |
| 📊 QUANT | Deterministic output + No NaNs/lookahead |
| 💱 DEX | Dry-run TX builds + Safety checks pass |
| 🔗 INTEGRATION | Wire test + CLI --help works |

---

## MCP Server

Zerg Swarm includes an MCP server for programmatic swarm control.

### Installation

```bash
cd /home/ubuntu/projects/zerg-swarm
pip install -e .
```

### Running

```bash
python -m zerg_swarm_mcp
# Server starts on http://127.0.0.1:8766
```

### Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `ZERG_HOST` | 127.0.0.1 | Server host |
| `ZERG_PORT` | 8766 | Server port |
| `ZERG_SWARM_ROOT` | ./SWARM | Path to SWARM directory |

### Available Tools

| Tool | Description |
|------|-------------|
| `swarm_status` | Get current swarm state |
| `swarm_reset` | Reset state to initial values |
| `task_list` | List tasks by lane |
| `task_get` | Read a task card |
| `task_create` | Create new task card |
| `zergling_register` | Register active zergling |
| `zergling_unregister` | Remove zergling |
| `zergling_list` | List all registered zerglings |
| `lock_acquire` | Reserve files for editing |
| `lock_release` | Release file locks |
| `lock_check` | Check lock status |
| `wave_status` | Get wave statistics |
| `wave_increment` | Advance wave counter |
| `wave_collect` | Process inbox results |
| `result_get` | Get specific result |
| `inbox_list` | List inbox items |
| `outbox_list` | List outbox items |
| `health_check` | System diagnostics |

---

## CLI Reference

```bash
# Swarm management
python SWARM/SCRIPTS/swarm.py status    # Show wave, counts
python SWARM/SCRIPTS/swarm.py wave      # Increment wave
python SWARM/SCRIPTS/swarm.py tasks     # List OUTBOX
python SWARM/SCRIPTS/swarm.py results   # List INBOX
python SWARM/SCRIPTS/swarm.py collect   # Process INBOX → STATE
```

---

## File Reference

| File | Purpose |
|------|---------|
| `STATE.json` | Wave counter, task status |
| `SWARM_RULES.md` | Master rules document |
| `GATES.md` | Lane acceptance criteria |
| `PROMPTS.md` | Copy-paste role prompts |
| `RUNBOOK.md` | Operational playbook |

---

## Contributing

```
┌─────────────────────────────────────┐
│  1. Pick a task from TASKS/         │
│  2. Create lock in LOCKS/           │
│  3. Implement (≤100 lines, 4 min)   │
│  4. Write result (DONE/PARTIAL)     │
│  5. Remove lock                     │
└─────────────────────────────────────┘
```

**Want to add features?** Open an issue first. We'll decompose it into swarm-safe microtasks.

---

## Philosophy

> *"Quality is not in the individual worker, but in the rhythm of the swarm."*

This system favors:

- **Speed** over elegance
- **Throughput** over completeness
- **Iteration** over perfection
- **Many small wins** over one big push

---

<div align="center">

**Built with 🐝 by disposable agents**

*Spawn fast. Bite hard. Die clean.*

[![Made with Claude](https://img.shields.io/badge/Made_with-Claude-purple.svg)](https://claude.ai)

</div>
