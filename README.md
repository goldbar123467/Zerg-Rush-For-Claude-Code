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

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'primaryColor': '#6b21a8', 'primaryTextColor': '#fff', 'primaryBorderColor': '#9333ea', 'lineColor': '#a855f7', 'secondaryColor': '#1e1b4b', 'tertiaryColor': '#312e81'}}}%%
flowchart TD
    subgraph SWARM["🐝 SWARM/"]
        direction TB
        STATE[("⚡ STATE.json")]
        RULES["📜 SWARM_RULES.md"]
        GATES["🚪 GATES.md"]
        PROMPTS["💬 PROMPTS.md"]
        RUNBOOK["📖 RUNBOOK.md"]

        subgraph LANES["🛤️ TASK LANES"]
            direction LR
            KERNEL["🔥 KERNEL"]
            ML["🧠 ML"]
            QUANT["📊 QUANT"]
            DEX["💱 DEX"]
            INT["🔗 INTEGRATION"]
        end

        subgraph FLOW["📨 MESSAGE FLOW"]
            direction LR
            OUTBOX["📤 OUTBOX"]
            INBOX["📥 INBOX"]
        end

        SCRIPTS["⚙️ SCRIPTS/"]
        LOCKS["🔒 LOCKS/"]
    end

    STATE --> LANES
    LANES --> FLOW
    OUTBOX -->|"assign"| INBOX
    INBOX -->|"collect"| STATE

    style STATE fill:#6b21a8,stroke:#a855f7,stroke-width:3px
    style LANES fill:#1e1b4b,stroke:#4f46e5
    style FLOW fill:#312e81,stroke:#6366f1
```

### Wave Execution Flow

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'actorBkg': '#6b21a8', 'actorTextColor': '#fff', 'actorLineColor': '#a855f7', 'signalColor': '#22c55e', 'signalTextColor': '#fff'}}}%%
sequenceDiagram
    autonumber
    participant O as 👁️ OVERLORD
    participant Q as 📋 QUEUE
    participant W1 as 🐝 Worker 1
    participant W2 as 🐝 Worker 2
    participant W3 as 🐝 Worker 3
    participant W4 as 🐝 Worker 4
    participant W5 as 🐝 Worker 5
    participant I as 📥 INBOX

    rect rgb(30, 27, 75)
        Note over O,Q: 📝 WAVE COMPOSITION
        O->>Q: Decompose goal → 5 microtasks
        O->>Q: Validate: 2 impl + 2 test + 1 quality
    end

    rect rgb(49, 46, 129)
        Note over Q,W5: ⚡ PARALLEL SPAWN (4 min TTL)
        par
            Q->>W1: K001 [ADD_PURE_FN]
            Q->>W2: K002 [ADD_TEST]
            Q->>W3: K003 [ADD_BENCH]
            Q->>W4: M001 [ADD_STUB]
            Q->>W5: M002 [ADD_TEST]
        end
    end

    rect rgb(22, 78, 99)
        Note over W1,I: 📤 RESULTS
        W1->>I: ✅ DONE
        W2->>I: ✅ DONE
        W3->>I: ⚠️ PARTIAL
        W4->>I: ✅ DONE
        W5->>I: 🚫 BLOCKED
    end

    Note over W1,W5: 💀 ALL WORKERS TERMINATE

    rect rgb(30, 27, 75)
        Note over I,O: 🔄 COLLECT & ITERATE
        I->>O: Merge 3 DONE results
        O->>Q: Split PARTIAL → 2 new tasks
        O->>Q: Resolve BLOCKED dependency
        O->>O: Wave 2...
    end
```

### Worker Lifecycle

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'primaryColor': '#6b21a8', 'lineColor': '#a855f7'}}}%%
stateDiagram-v2
    direction LR

    [*] --> 🥚Spawn: New Wave

    state "🐝 ACTIVE" as active {
        🥚Spawn --> 📋Register: Get task card
        📋Register --> 🔒Lock: Reserve files
        🔒Lock --> ⚡Execute: Start 4-min timer

        state ⚡Execute {
            direction TB
            [*] --> Working
            Working --> Working: Loop
            Working --> ✅Done: Complete
            Working --> ⚠️Partial: Time/lines exceeded
            Working --> 🚫Blocked: Need more context
        }
    }

    ⚡Execute --> 📤Report: Write result
    📤Report --> 🔓Release: Free locks
    🔓Release --> 💀Die: Terminate
    💀Die --> [*]

    note right of ⚡Execute
        ⏱️ 4 min max
        📏 100 lines max
        📁 2 files max
    end note

    note right of 💀Die
        No state preserved
        Fresh spawn next wave
    end note
```

### Lane Isolation

```mermaid
%%{init: {'theme': 'dark'}}%%
flowchart LR
    subgraph WAVE["🌊 WAVE 1"]
        direction TB

        subgraph KERNEL_LANE["🔥 KERNEL LANE"]
            K1["K001<br/>ADD_PURE_FN"]
            K2["K002<br/>ADD_TEST"]
            K3["K003<br/>ADD_BENCH"]
        end

        subgraph ML_LANE["🧠 ML LANE"]
            M1["M001<br/>ADD_STUB"]
            M2["M002<br/>ADD_TEST"]
        end
    end

    K1 -.->|"❌ NO CROSS"| M1

    OVERLORD["👁️ OVERLORD"] --> WAVE
    WAVE --> RESULTS["📥 RESULTS"]

    style KERNEL_LANE fill:#7c2d12,stroke:#ea580c
    style ML_LANE fill:#1e3a8a,stroke:#3b82f6
    style WAVE fill:#1e1b4b,stroke:#6366f1
```

---

## Quick Start

### Prerequisites

- Python 3.10+
- Claude Code CLI

### Installation

```bash
git clone https://github.com/yourusername/swarm-rush.git
cd swarm-rush
```

### Your First Wave

```bash
# Check swarm status
python SWARM/SCRIPTS/swarm.py status

# View pending tasks
python SWARM/SCRIPTS/swarm.py tasks
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

Open 5 Claude Code sessions. In each, paste:

```
You are WORKER-N. Complete exactly ONE task and STOP.
TTL: 4 minutes | Max: 100 lines | Files: 2 max
```

### 3. Collect Results

```bash
python SWARM/SCRIPTS/swarm.py collect
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

### Lane Rules

```
┌────────────────────────────────────────────┐
│  ✓ One lane per task                       │
│  ✓ Single-lane waves are fastest           │
│  ✓ Mixed waves: max 3+2 across 2 lanes     │
│  ✗ Never more than 2 lanes per wave        │
│  ✗ Never cross lanes within a task         │
└────────────────────────────────────────────┘
```

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

### Key Tools

| Tool | Description |
|------|-------------|
| `swarm_status` | Get current swarm state |
| `task_list` | List tasks by lane |
| `zergling_register` | Register active zergling |
| `lock_acquire` | Reserve files |
| `wave_increment` | Advance wave counter |
| `health_check` | System diagnostics |

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
