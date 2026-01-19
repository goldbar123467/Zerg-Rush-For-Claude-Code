"""
Status Message Manager - Messages with TTL and styling.
Keeps messages visible for a configurable duration.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List


@dataclass
class StatusMessage:
    """A status message with TTL and level."""
    text: str
    level: str = "info"  # info, success, warning, error
    timestamp: datetime = field(default_factory=datetime.now)
    ttl_seconds: float = 5.0

    def is_expired(self) -> bool:
        """Check if message has expired."""
        elapsed = (datetime.now() - self.timestamp).total_seconds()
        return elapsed > self.ttl_seconds

    def remaining_seconds(self) -> float:
        """Get remaining display time."""
        elapsed = (datetime.now() - self.timestamp).total_seconds()
        return max(0, self.ttl_seconds - elapsed)


@dataclass
class StatusMessageManager:
    """Manages status messages with TTL and history."""

    current: Optional[StatusMessage] = None
    history: List[StatusMessage] = field(default_factory=list)
    max_history: int = 20
    default_ttl: float = 5.0

    # TTL by level
    LEVEL_TTL = {
        "info": 4.0,
        "success": 5.0,
        "warning": 6.0,
        "error": 8.0,
    }

    # Rich styles by level
    LEVEL_STYLES = {
        "info": "cyan",
        "success": "green",
        "warning": "yellow",
        "error": "red bold",
    }

    def set_message(self, text: str, level: str = "info", ttl: float = None) -> None:
        """Set a new status message."""
        if ttl is None:
            ttl = self.LEVEL_TTL.get(level, self.default_ttl)

        msg = StatusMessage(text=text, level=level, ttl_seconds=ttl)

        # Archive current if exists
        if self.current and not self.current.is_expired():
            self.history.append(self.current)
            if len(self.history) > self.max_history:
                self.history = self.history[-self.max_history:]

        self.current = msg

    def get_current(self) -> Optional[StatusMessage]:
        """Get current message if not expired."""
        if self.current and not self.current.is_expired():
            return self.current
        return None

    def get_display_text(self) -> str:
        """Get the text to display (or 'Ready' if none)."""
        msg = self.get_current()
        return msg.text if msg else "Ready"

    def get_style(self) -> str:
        """Get Rich style for current message."""
        msg = self.get_current()
        if msg:
            return self.LEVEL_STYLES.get(msg.level, "white")
        return "dim italic"

    def clear(self) -> None:
        """Clear current message."""
        self.current = None
