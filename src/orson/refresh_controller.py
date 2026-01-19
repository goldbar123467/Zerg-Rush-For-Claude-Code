"""
Refresh Controller - Adaptive UI refresh rate management.
Prevents flickering by only rendering when state changes.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional
import hashlib
import json


@dataclass
class RefreshController:
    """Controls when UI should refresh based on state changes."""

    min_interval: float = 0.3  # Minimum 300ms between renders
    max_interval: float = 2.0  # Maximum 2s between renders
    last_render_time: Optional[datetime] = None
    last_state_hash: str = ""
    force_next_render: bool = False

    def _hash_state(self, state: Any) -> str:
        """Create a hash of relevant state fields for change detection."""
        try:
            # Hash key fields that affect display
            key_data = {
                "wave": getattr(state, "wave", 0),
                "selected_lane": getattr(state, "selected_lane", 0),
                "selected_building": getattr(state, "selected_building", 0),
                "status_message": getattr(state, "status_message", ""),
                "active_zerglings": len(getattr(state, "active_zerglings", [])),
                "radio_events_count": len(getattr(state, "radio_events", [])),
            }
            return hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()[:16]
        except:
            return ""

    def should_render(self, state: Any) -> bool:
        """Check if UI should be re-rendered."""
        now = datetime.now()

        # Always render if forced
        if self.force_next_render:
            return True

        # Check minimum interval
        if self.last_render_time:
            elapsed = (now - self.last_render_time).total_seconds()
            if elapsed < self.min_interval:
                return False
            # Force render after max interval
            if elapsed >= self.max_interval:
                return True

        # Check if state changed
        current_hash = self._hash_state(state)
        if current_hash != self.last_state_hash:
            return True

        return False

    def mark_rendered(self, state: Any) -> None:
        """Mark that a render just occurred."""
        self.last_render_time = datetime.now()
        self.last_state_hash = self._hash_state(state)
        self.force_next_render = False

    def force_render(self) -> None:
        """Force the next render to occur."""
        self.force_next_render = True
