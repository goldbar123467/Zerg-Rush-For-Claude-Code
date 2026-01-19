# WAVE 27: UI READABILITY IMPROVEMENTS

## Executive Summary

The Orson CLI has UI issues causing poor user experience:
- Updates too fast (flickering)
- Status messages disappear immediately
- Layout is messy and inconsistent
- Radio events never displayed

---

## ISSUES IDENTIFIED

### Issue 1: Refresh Rate Too Fast
- **Location**: `cli.py:1915` - `refresh_per_second=2`
- **Problem**: Combined with 0.5s key timeout = constant flickering

### Issue 2: Status Messages Disappear Instantly
- **Location**: `cli.py:76, 1000-1006`
- **Problem**: Messages overwritten on next operation (40+ places set status_message)

### Issue 3: Layout Inconsistency
- **Location**: `cli.py:1009-1060`
- **Problem**: Fixed heights don't adapt, no visual hierarchy

### Issue 4: Radio Events Never Displayed
- **Location**: `cli.py:120, 133-149`
- **Problem**: Events stored but never rendered

### Issue 5: Help Panel Too Dense
- **Location**: `cli.py:975-997`
- **Problem**: All keybindings crammed into one line

---

## IMPLEMENTATION TASKS

### Task 27.1: Create RefreshController Module (~80 lines)
**File**: `src/orson/refresh_controller.py` (NEW)

```python
@dataclass
class RefreshController:
    min_interval: float = 0.5
    max_interval: float = 2.0
    last_render: datetime = None
    state_hash: int = 0

    def should_render(self, state) -> bool:
        """Check if render needed based on state changes and timing."""

    def mark_rendered(self, state):
        """Mark state as rendered."""
```

### Task 27.2: Create StatusMessageManager (~70 lines)
**File**: `src/orson/status_manager.py` (NEW)

```python
@dataclass
class StatusMessage:
    text: str
    level: str  # info, success, warning, error
    timestamp: datetime
    ttl_seconds: float = 5.0

@dataclass
class StatusMessageManager:
    current: Optional[StatusMessage] = None
    history: List[StatusMessage] = field(default_factory=list)

    def set_message(self, text: str, level: str = "info", ttl: float = 5.0):
        ...

    def get_current(self) -> Optional[StatusMessage]:
        """Get current message if not expired."""
```

### Task 27.3: Update SwarmState (~30 lines)
**File**: `src/orson/cli.py:66-128`
- Add `status_manager: StatusMessageManager`
- Add `refresh_controller: RefreshController`
- Remove raw `status_message: str`

### Task 27.4: Create Radio Panel Renderer (~60 lines)
**File**: `src/orson/cli.py` (after line 997)

```python
def render_radio_panel(state: SwarmState, max_events: int = 5) -> Panel:
    """Render the radio event ticker panel."""
    # Shows last 5 events with timestamps
```

### Task 27.5: Update render_layout (~80 lines)
**File**: `src/orson/cli.py:1009-1060`

New structure:
```
header (3 lines)
buildings (7 lines)
main (ratio)
footer (10 lines) = radio + status_help
```

### Task 27.6: Update render_status with TTL (~40 lines)
**File**: `src/orson/cli.py:1000-1007`
- Use StatusMessageManager
- Style based on level (info=cyan, success=green, warning=yellow, error=red)

### Task 27.7: Update render_help with Categories (~50 lines)
**File**: `src/orson/cli.py:975-998`

Categories:
- Nav: 1-5 lanes
- Act: decompose, spawn, collect, kill
- View: museum, news, brain, teach, gsvcs
- Sys: refresh, help, quit

### Task 27.8: Update Main Loop (~40 lines)
**File**: `src/orson/cli.py:1914-1932`
- Use RefreshController
- Only re-render on state changes
- Force render after key press

### Task 27.9: Update All status_message Calls (~60 lines)
**File**: `src/orson/cli.py` (40+ locations)

Change: `state.status_message = "msg"`
To: `state.status_manager.set_message("msg", level="info")`

### Task 27.10: Update render_buildings (~50 lines)
**File**: `src/orson/cli.py:812-874`
- Limit workers shown to 2 per building
- Add overflow indicator (+N more)
- Fix column width overflow

---

## IMPLEMENTATION ORDER

1. Task 27.2 - StatusMessageManager (no deps)
2. Task 27.1 - RefreshController (no deps)
3. Task 27.3 - Update SwarmState (deps: 1, 2)
4. Task 27.4 - Radio Panel (standalone)
5. Task 27.6 - render_status (deps: 2)
6. Task 27.7 - render_help (standalone)
7. Task 27.5 - render_layout (deps: 4, 6, 7)
8. Task 27.10 - render_buildings (standalone)
9. Task 27.9 - status_message calls (deps: 2, 3)
10. Task 27.8 - Main loop (deps: 1, 3)

---

## SUCCESS CRITERIA

- [ ] Refresh rate smooth (no flickering)
- [ ] Status messages persist ~5 seconds
- [ ] Radio events visible in footer
- [ ] Help readable at a glance
- [ ] Buildings don't overflow with workers
