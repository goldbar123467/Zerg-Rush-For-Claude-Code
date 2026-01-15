"""FastMCP server setup for Zerg Swarm."""

from fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP(
    name="zerg-swarm",
    instructions="""Zerg Swarm MCP Server for multi-agent task coordination.

Available tool categories:
- State: swarm_status, swarm_reset
- Tasks: task_list, task_get, task_create
- Zerglings: zergling_register, zergling_unregister, zergling_list
- Locks: lock_acquire, lock_release, lock_check
- Waves: wave_status, wave_increment, wave_collect
- Results: result_get, inbox_list, outbox_list
- Diagnostics: reconcile_state, health_check
"""
)

# Tools will be registered by importing tool modules
# This happens in __main__.py before server starts
