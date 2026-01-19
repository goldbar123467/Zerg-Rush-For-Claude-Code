# Orson Agent IDE - Technical Plan

> "The hive wears flannel."

## Vision

A web-based IDE for controlling the Zerg Rush MCP swarm, themed as an isometric pixel art Midwestern small town. Buildings are lanes, townfolk are zerglings, and the Mayor is the Overlord.

**Aesthetic**: Think *Stardew Valley* meets *Starcraft* - friendly pixel art with alien undertones. Cornfields have chitinous stalks. The diner serves creep casserole. Workers wear flannel over carapace.

---

## 1. Project Structure

```
zerg-swarm/
├── src/
│   ├── zerg_swarm_mcp/          # Existing MCP server (unchanged)
│   └── orson/                    # NEW: Web IDE
│       ├── server.py             # FastAPI server (port 8000)
│       ├── static/
│       │   ├── index.html        # SPA entry point
│       │   ├── css/
│       │   │   └── orson.css     # Pixel art styling
│       │   ├── js/
│       │   │   ├── app.js        # Main application
│       │   │   ├── mcp-client.js # MCP API wrapper
│       │   │   ├── town.js       # Isometric town renderer
│       │   │   ├── composer.js   # Task wave composer
│       │   │   └── monitor.js    # Live worker monitor
│       │   └── assets/
│       │       ├── sprites/      # Pixel art sprites
│       │       │   ├── buildings/
│       │       │   ├── characters/
│       │       │   ├── tiles/
│       │       │   └── ui/
│       │       └── audio/        # Optional SFX
│       └── templates/            # Jinja2 if needed
├── SWARM/                        # Existing swarm state (unchanged)
└── orson.py                      # CLI launcher: `python orson.py`
```

**Rationale**: Keep Orson as a sibling to the MCP server, not coupled to it. The IDE is a pure client that talks to the existing MCP server over HTTP.

---

## 2. Tech Stack

### Backend (Minimal)
| Component | Choice | Rationale |
|-----------|--------|-----------|
| Web Server | **FastAPI** | Already using FastMCP/uvicorn, consistent |
| Static Files | FastAPI StaticFiles | Simple, no build step |
| Templating | None (pure SPA) | All rendering client-side |

### Frontend (No Build Step)
| Component | Choice | Rationale |
|-----------|--------|-----------|
| Framework | **Vanilla JS + ES Modules** | No npm, no bundler, just files |
| Rendering | **Canvas 2D** | Pixel art needs pixel control |
| Isometric Engine | **Custom (tiny)** | <200 lines for iso grid math |
| State Management | **Simple store pattern** | Reactive updates, no framework |
| Styling | **CSS Variables + pixel fonts** | Retro aesthetic |

### Why No React/Pixi.js?
- **React**: Overkill for this UI, adds build complexity
- **Pixi.js**: WebGL is overkill for 2D pixel art at low res
- **Vanilla Canvas**: Full control, pixel-perfect rendering, zero deps

### MCP Communication
| Method | Description |
|--------|-------------|
| **Fetch API** | Direct HTTP calls to MCP server |
| **Polling** | 1-2 second interval for state updates |
| **SSE (future)** | Server-Sent Events for real-time push |

---

## 3. Core Components

### 3.1 Town View (`town.js`)
The main isometric visualization. ~400x300 canvas scaled 2x.

```
┌────────────────────────────────────────────────────────────────┐
│                        ORSON TOWNSHIP                          │
│                                                                │
│           🏛️ Town Hall                                         │
│          (Overlord HQ)          🌽🌽🌽                         │
│              ╱╲                 🌽🌽🌽                         │
│             ╱  ╲                (Creep Fields)                 │
│                                                                │
│    🏭 Kernel     🏪 ML Shop    🏦 Quant Bank    🚂 DEX Depot   │
│    Factory       (Models)      (Strategy)       (Solana)       │
│                                                                │
│         👷 👷 👷   (Zerglings walking between buildings)       │
│                                                                │
│    ═══════════════ Main Street ═══════════════                │
│                                                                │
│    📬 Post Office  (INBOX/OUTBOX)    🔒 Locksmith (Locks)     │
└────────────────────────────────────────────────────────────────┘
```

**Buildings Map to Lanes**:
| Building | Lane | Visual |
|----------|------|--------|
| Kernel Factory | KERNEL | Industrial, smokestacks, gears |
| ML General Store | ML | Shelves of model jars |
| Quant Bank | QUANT | Vault, numbers, charts |
| DEX Train Depot | DEX | Trains = transactions |
| Integration Diner | INTEGRATION | Wiring = plumbing |
| Town Hall | Overlord | Mayor's office, big desk |
| Post Office | INBOX/OUTBOX | Mail slots, packages |
| Locksmith | LOCKS | Keys, padlocks |

**Workers (Zerglings)**:
- Small pixel characters in flannel
- Subtle zerg features (small antennae, slight purple tint)
- Walk between buildings carrying task scrolls
- Spawn animation: pop out of ground
- Death animation: poof into purple smoke

### 3.2 Task Composer (`composer.js`)
Wave creation interface. Slide-out panel from right.

```
┌─────────────────────────────────────┐
│ 🌊 WAVE COMPOSER         [Spawn!]  │
├─────────────────────────────────────┤
│ Goal: ________________________     │
│       [Decompose into 5 tasks]     │
├─────────────────────────────────────┤
│ Task 1: [KERNEL ▼] [ADD_STUB ▼]    │
│ ┌─────────────────────────────────┐ │
│ │ Objective: ________________     │ │
│ │ Files: [+ Add File]             │ │
│ │ ☑ Has context pack              │ │
│ └─────────────────────────────────┘ │
│                                     │
│ Task 2: [ML ▼] [ADD_TEST ▼]        │
│ ...                                 │
├─────────────────────────────────────┤
│ Wave Balance: ██░░░ 2/5            │
│ ⚠️ Missing: 2 validation tasks      │
└─────────────────────────────────────┘
```

**Features**:
- Drag-and-drop task reordering
- Lane conflict detection (warns if >2 lanes)
- Constraint validation (100 lines, 2 files max)
- Context pack completeness checker
- One-click spawn (creates tasks + registers workers)

### 3.3 Worker Monitor (`monitor.js`)
Live status of active zerglings. Bottom panel.

```
┌──────────────────────────────────────────────────────────────────┐
│ 🐛 ACTIVE WORKERS                                    Wave: 3    │
├──────────────────────────────────────────────────────────────────┤
│ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐          │
│ │ Zerg-1 │ │ Zerg-2 │ │ Zerg-3 │ │ Zerg-4 │ │ Zerg-5 │          │
│ │ K001   │ │ K002   │ │ M001   │ │ M002   │ │ Q001   │          │
│ │ ████░░ │ │ ██████ │ │ ███░░░ │ │ █░░░░░ │ │ ████░░ │          │
│ │ 2:34   │ │ DONE ✓ │ │ 1:45   │ │ 3:12   │ │ 2:01   │          │
│ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘          │
├──────────────────────────────────────────────────────────────────┤
│ 💬 "Another one bites the dust." - Zerg-2 completed K002        │
└──────────────────────────────────────────────────────────────────┘
```

**Features**:
- Real-time progress bars (time remaining out of 4min)
- Status indicators (PENDING/IN_PROGRESS/DONE/PARTIAL/BLOCKED)
- Click to expand: see task details, current file locks
- Voiceline ticker at bottom (flavor.py integration)
- Auto-scroll log of recent events

### 3.4 Results Viewer
Popup modal for inspecting completed results.

```
┌─────────────────────────────────────────────────────────────────┐
│ 📋 RESULT: K001                                         [X]    │
├─────────────────────────────────────────────────────────────────┤
│ Status: ✅ DONE                     Time: 2:34 / 4:00          │
│ Lane: KERNEL                        Type: ADD_PURE_FN          │
├─────────────────────────────────────────────────────────────────┤
│ Summary:                                                        │
│ Added `compute_attention_scores()` function to                  │
│ `src/kernel/attention.py`. Follows existing pattern from        │
│ `compute_softmax()`. Includes docstring and type hints.         │
├─────────────────────────────────────────────────────────────────┤
│ Files Modified:                                                 │
│ • src/kernel/attention.py (+47 lines)                          │
├─────────────────────────────────────────────────────────────────┤
│ [View Diff] [Approve] [Request Revision]                        │
└─────────────────────────────────────────────────────────────────┘
```

### 3.5 State Dashboard
Overlay showing swarm health. Toggle with hotkey.

```
┌──────────────────────────────┐
│ 📊 SWARM STATUS              │
├──────────────────────────────┤
│ Wave: 3                      │
│ Active Workers: 4/5          │
│ Pending Tasks: 12            │
│ Completed: 47                │
│ Blocked: 2                   │
├──────────────────────────────┤
│ Lanes:                       │
│ • KERNEL: ████████░░ 8       │
│ • ML:     ██████░░░░ 6       │
│ • QUANT:  ████░░░░░░ 4       │
│ • DEX:    ██░░░░░░░░ 2       │
│ • INT:    █░░░░░░░░░ 1       │
├──────────────────────────────┤
│ Locks: 3 active              │
│ Health: ✅ All systems go    │
└──────────────────────────────┘
```

---

## 4. MCP Client Architecture

### 4.1 API Wrapper (`mcp-client.js`)

```javascript
// mcp-client.js - Thin wrapper around MCP HTTP API

const MCP_BASE = 'http://127.0.0.1:8766';

export const mcp = {
  // State
  async swarmStatus() {
    return this._call('swarm_status');
  },

  async swarmReset() {
    return this._call('swarm_reset');
  },

  // Tasks
  async taskList(lane = null) {
    return this._call('task_list', { lane });
  },

  async taskGet(taskId, lane) {
    return this._call('task_get', { task_id: taskId, lane });
  },

  async taskCreate(taskId, lane, taskType, objective, contextPack = {}) {
    return this._call('task_create', {
      task_id: taskId,
      lane,
      task_type: taskType,
      objective,
      ...contextPack
    });
  },

  // Zerglings
  async zerglingRegister(name) {
    return this._call('zergling_register', { name });
  },

  async zerglingList() {
    return this._call('zergling_list');
  },

  // Locks
  async lockAcquire(paths, holder, ttl = 300) {
    return this._call('lock_acquire', { paths, holder, ttl });
  },

  async lockRelease(paths, holder) {
    return this._call('lock_release', { paths, holder });
  },

  async lockList() {
    return this._call('lock_list');
  },

  // Waves
  async waveStatus() {
    return this._call('wave_status');
  },

  async waveIncrement() {
    return this._call('wave_increment');
  },

  async waveCollect() {
    return this._call('wave_collect');
  },

  // Results
  async inboxList() {
    return this._call('inbox_list');
  },

  async resultGet(taskId) {
    return this._call('result_get', { task_id: taskId });
  },

  // Health
  async healthCheck() {
    return this._call('health_check');
  },

  // Internal
  async _call(tool, params = {}) {
    const response = await fetch(`${MCP_BASE}/mcp/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        jsonrpc: '2.0',
        method: `tools/${tool}`,
        params,
        id: Date.now()
      })
    });
    const data = await response.json();
    if (data.error) throw new Error(data.error.message);
    return data.result;
  }
};
```

### 4.2 State Polling

```javascript
// store.js - Reactive state with polling

class SwarmStore {
  constructor() {
    this.state = {
      wave: 0,
      zerglings: [],
      pendingTasks: [],
      completedTasks: [],
      locks: [],
      health: null,
      lastUpdate: null
    };
    this.listeners = new Set();
    this.pollInterval = null;
  }

  subscribe(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  notify() {
    this.listeners.forEach(l => l(this.state));
  }

  async refresh() {
    try {
      const [status, locks, health] = await Promise.all([
        mcp.swarmStatus(),
        mcp.lockList(),
        mcp.healthCheck()
      ]);

      this.state = {
        wave: status.wave,
        zerglings: status.active_zerglings,
        pendingTasks: status.pending_tasks,
        completedTasks: status.completed_tasks,
        locks: locks,
        health: health,
        lastUpdate: new Date()
      };

      this.notify();
    } catch (err) {
      console.error('Refresh failed:', err);
    }
  }

  startPolling(interval = 2000) {
    this.refresh();
    this.pollInterval = setInterval(() => this.refresh(), interval);
  }

  stopPolling() {
    if (this.pollInterval) clearInterval(this.pollInterval);
  }
}

export const store = new SwarmStore();
```

### 4.3 Communication Flow

```
┌─────────────┐     HTTP/JSON-RPC      ┌─────────────────────┐
│  Orson IDE  │ ◄──────────────────► │  MCP Server (:8766) │
│   (:8000)   │                        │                     │
└──────┬──────┘                        └──────────┬──────────┘
       │                                          │
       │  Polling every 2s:                       │
       │  • swarm_status                          │
       │  • lock_list                             │  File I/O
       │  • health_check                          │
       │                                          ▼
       │  User actions:               ┌───────────────────────┐
       │  • task_create               │    SWARM/ Directory   │
       │  • zergling_register         │  • STATE.json         │
       │  • wave_increment            │  • TASKS/             │
       │  • lock_acquire              │  • INBOX/             │
       └──────────────────────────────│  • LOCKS/             │
                                      └───────────────────────┘
```

---

## 5. File List for MVP

### Phase 1: Core Files (12 files)

```
src/orson/
├── server.py              # FastAPI static file server
├── static/
│   ├── index.html         # Single page app shell
│   ├── css/
│   │   └── orson.css      # All styles (pixel theme)
│   ├── js/
│   │   ├── app.js         # Main entry, routing, init
│   │   ├── mcp-client.js  # MCP API wrapper
│   │   ├── store.js       # Reactive state store
│   │   ├── town.js        # Isometric renderer
│   │   ├── composer.js    # Task wave composer
│   │   └── monitor.js     # Worker status panel
│   └── assets/
│       └── sprites/
│           ├── buildings.png  # Spritesheet (all buildings)
│           ├── workers.png    # Spritesheet (zergling animations)
│           └── tiles.png      # Ground tiles, roads
orson.py                   # CLI launcher
```

### Sprite Requirements (MVP)

| Sprite | Size | Frames | Notes |
|--------|------|--------|-------|
| Town Hall | 64x64 | 1 | Isometric, American flag |
| Factory | 48x48 | 2 | Smoke animation |
| Shop | 32x32 | 1 | Awning, windows |
| Bank | 32x48 | 1 | Columns, vault door |
| Depot | 48x32 | 1 | Platform, tracks |
| Diner | 32x32 | 1 | Neon sign |
| Worker | 16x16 | 4 | Walk cycle (flannel + antennae) |
| Spawn FX | 16x16 | 4 | Ground burst |
| Death FX | 16x16 | 4 | Purple poof |
| Ground | 32x16 | 3 | Grass, road, creep |

---

## 6. Phase 1 Scope - Minimum Clickable

### What's In
1. **Static town view** - Buildings placed, no animation yet
2. **Live state display** - Wave number, worker count, task counts
3. **Worker list** - See active zerglings with basic status
4. **Task list by lane** - Click building to see its tasks
5. **Basic wave control** - "Next Wave" button that calls `wave_increment`
6. **Health indicator** - Green/red dot based on `health_check`

### What's Out (Phase 2+)
- Worker walking animations
- Task composer UI (manual task creation via MCP still works)
- Result diff viewer
- Voiceline ticker
- Lock visualization
- Sound effects

### Phase 1 User Flow

```
1. User opens http://localhost:8000
2. Sees isometric town with 5 lane buildings + Town Hall
3. Bottom panel shows current wave (e.g., "Wave 3")
4. Clicks on "Kernel Factory" building
   → Side panel shows list of KERNEL tasks
5. Worker cards show in bottom panel
   → Each shows name, assigned task, time remaining
6. User clicks "Collect Results" button
   → Calls wave_collect, updates completed count
7. User clicks "Next Wave" button
   → Calls wave_increment, spawns new workers (external)
```

### MVP Acceptance Criteria

- [ ] Town renders with all 5 lane buildings
- [ ] Clicking building shows tasks for that lane
- [ ] Worker count updates every 2 seconds
- [ ] Wave number displays correctly
- [ ] "Next Wave" button increments wave
- [ ] "Collect" button processes inbox
- [ ] Health check shows green when server is up
- [ ] Works in Chrome/Firefox without build step

---

## 7. Visual Style Guide

### Color Palette

```
Background:     #2d5a27 (grass green)
Road:           #8b7355 (dirt brown)
Creep accent:   #4a0e4e (purple, subtle)
Building base:  #d4a574 (warm wood)
Building roof:  #8b4513 (darker brown)
UI panel:       #1a1a2e (dark blue)
UI text:        #eaeaea (off-white)
UI accent:      #e94560 (coral red)
Success:        #4ade80 (green)
Warning:        #fbbf24 (amber)
Error:          #f87171 (red)
Zerg tint:      #7c3aed (purple)
```

### Typography

```css
/* Pixel font for headers */
@font-face {
  font-family: 'PixelFont';
  src: url('assets/fonts/pixel.woff2');
}

/* System monospace for data */
body {
  font-family: 'Courier New', monospace;
}

h1, h2, .pixel {
  font-family: 'PixelFont', monospace;
  image-rendering: pixelated;
}
```

### Isometric Grid Math

```javascript
// Convert grid coords to screen coords
function gridToScreen(gridX, gridY) {
  const TILE_WIDTH = 32;
  const TILE_HEIGHT = 16;
  return {
    x: (gridX - gridY) * (TILE_WIDTH / 2) + CANVAS_WIDTH / 2,
    y: (gridX + gridY) * (TILE_HEIGHT / 2) + 50
  };
}

// Reverse: screen to grid (for clicks)
function screenToGrid(screenX, screenY) {
  const TILE_WIDTH = 32;
  const TILE_HEIGHT = 16;
  const adjustedX = screenX - CANVAS_WIDTH / 2;
  const adjustedY = screenY - 50;
  return {
    x: Math.floor((adjustedX / (TILE_WIDTH / 2) + adjustedY / (TILE_HEIGHT / 2)) / 2),
    y: Math.floor((adjustedY / (TILE_HEIGHT / 2) - adjustedX / (TILE_WIDTH / 2)) / 2)
  };
}
```

---

## 8. Development Phases

### Phase 1: Foundation (MVP)
- Static server + HTML shell
- MCP client wrapper
- Basic isometric town (static sprites)
- State polling + display
- Click-to-inspect buildings

### Phase 2: Interactivity
- Task composer panel
- Worker walking animations
- Spawn/death particle effects
- Voiceline ticker
- Lock visualization on buildings

### Phase 3: Polish
- Sound effects (8-bit bleeps)
- Day/night cycle (cosmetic)
- Weather effects (rain on creep)
- Achievement popups
- Keyboard shortcuts

### Phase 4: Advanced
- Goal decomposition AI assist
- Result diff viewer
- Historical wave replay
- Performance metrics dashboard
- Multi-swarm support

---

## 9. Open Questions

1. **Sprite creation**: Generate with AI (DALL-E/Midjourney) or commission pixel artist?
2. **Audio**: Include 8-bit SFX or keep silent?
3. **Mobile**: Support touch/responsive or desktop-only?
4. **Persistence**: Should IDE remember UI state (panel positions, etc.)?
5. **Auth**: Any access control or fully open localhost?

---

## 10. Next Steps

1. **Create directory structure** - `src/orson/` scaffold
2. **FastAPI server** - Serve static files on :8000
3. **HTML shell** - Basic layout with canvas + panels
4. **MCP client** - Verify communication with existing server
5. **First sprite** - Town Hall building to prove rendering
6. **State display** - Wave counter pulling from MCP

---

*"Welcome to Orson, population: variable. The Mayor would like a word about your task decomposition."*
