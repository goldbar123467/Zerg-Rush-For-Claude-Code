"""
MCP WebSocket Client for Orson CLI

Connects to the Zerg Swarm MCP server on localhost:8766.
Provides async methods for sending commands and receiving responses.
"""

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any, Callable
import websockets
from websockets.exceptions import ConnectionClosed

# Default timeouts by operation type (seconds)
OPERATION_TIMEOUTS = {
    "health_check": 3.0,
    "swarm_status": 5.0,
    "task_list": 15.0,
    "task_get": 5.0,
    "task_create": 10.0,
    "wave_status": 5.0,
    "wave_increment": 5.0,
    "wave_collect": 20.0,
    "zergling_list": 5.0,
    "zergling_register": 5.0,
    "inbox_list": 10.0,
}
DEFAULT_TIMEOUT = 10.0


@dataclass
class MCPResponse:
    """Response from MCP server."""
    success: bool
    data: Any
    error: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class MCPClient:
    """Async WebSocket client for MCP server communication."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8767):
        self.host = host
        self.port = port
        self.uri = f"ws://{host}:{port}/ws"
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.connected = False
        self.last_ping: Optional[datetime] = None
        self.request_id = 0
        self.on_event: Optional[Callable[[dict], None]] = None
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 3
        self._reconnect_delay = 1.0

    @property
    def is_connected(self) -> bool:
        """Check actual connection state."""
        return self.ws is not None and not getattr(self.ws, 'closed', True)

    async def ensure_connected(self) -> bool:
        """Ensure connection, attempting reconnect if needed."""
        if self.is_connected:
            self._reconnect_attempts = 0
            return True
        while self._reconnect_attempts < self._max_reconnect_attempts:
            self._reconnect_attempts += 1
            try:
                if await self.connect():
                    self._reconnect_attempts = 0
                    return True
            except Exception:
                pass
            await asyncio.sleep(self._reconnect_delay * self._reconnect_attempts)
        return False

    async def connect(self) -> bool:
        """Establish WebSocket connection to MCP server."""
        try:
            self.ws = await websockets.connect(self.uri)
            self.connected = True
            self.last_ping = datetime.now()
            return True
        except (ConnectionRefusedError, OSError) as e:
            self.connected = False
            return False

    async def disconnect(self):
        """Close WebSocket connection."""
        if self.ws:
            await self.ws.close()
            self.ws = None
        self.connected = False

    async def send_command(self, method: str, params: dict = None, timeout: float = None) -> MCPResponse:
        """Send a command to MCP server and await response."""
        if not await self.ensure_connected():
            return MCPResponse(success=False, data=None, error="Connection failed")

        # Get timeout for this operation
        if timeout is None:
            timeout = OPERATION_TIMEOUTS.get(method, DEFAULT_TIMEOUT)

        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "method": f"tools/{method}",
            "params": params or {},
            "id": self.request_id
        }

        try:
            await self.ws.send(json.dumps(request))
            response_text = await asyncio.wait_for(self.ws.recv(), timeout=timeout)
            response = json.loads(response_text)

            self.last_ping = datetime.now()

            if "error" in response:
                return MCPResponse(
                    success=False,
                    data=None,
                    error=response["error"].get("message", "Unknown error")
                )

            return MCPResponse(success=True, data=response.get("result"))

        except asyncio.TimeoutError:
            return MCPResponse(success=False, data=None, error="Request timeout")
        except ConnectionClosed:
            self.connected = False
            return MCPResponse(success=False, data=None, error="Connection closed")
        except Exception as e:
            return MCPResponse(success=False, data=None, error=str(e))

    async def ping(self) -> bool:
        """Check if server is responsive."""
        response = await self.send_command("health_check")
        return response.success

    # === Convenience methods for common operations ===

    async def swarm_status(self) -> MCPResponse:
        """Get current swarm state."""
        return await self.send_command("swarm_status")

    async def wave_increment(self) -> MCPResponse:
        """Increment wave counter."""
        return await self.send_command("wave_increment")

    async def wave_collect(self) -> MCPResponse:
        """Collect results from inbox."""
        return await self.send_command("wave_collect")

    async def task_list(self, lane: str = None) -> MCPResponse:
        """List tasks, optionally by lane."""
        params = {"lane": lane} if lane else {}
        return await self.send_command("task_list", params)

    async def zergling_list(self) -> MCPResponse:
        """List active zerglings."""
        return await self.send_command("zergling_list")

    async def health_check(self) -> MCPResponse:
        """Get system health status."""
        return await self.send_command("health_check")

    async def inbox_list(self) -> MCPResponse:
        """List items in the inbox."""
        return await self.send_command("inbox_list")


# Singleton instance for easy import
_client: Optional[MCPClient] = None


def get_client() -> MCPClient:
    """Get or create the singleton MCP client."""
    global _client
    if _client is None:
        _client = MCPClient()
    return _client
