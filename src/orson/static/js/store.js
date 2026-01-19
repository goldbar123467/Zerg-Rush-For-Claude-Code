/**
 * Swarm Store - Reactive state management with MCP polling
 *
 * Maintains local state that syncs with the MCP server.
 * Notifies subscribers on state changes.
 */

import { mcp } from './mcp-client.js';

class SwarmStore {
    constructor() {
        this.state = {
            // Connection
            connected: false,
            lastError: null,

            // Swarm state
            wave: 0,
            zerglings: [],
            pendingTasks: [],
            completedTasks: [],

            // Additional data
            locks: [],
            inbox: [],
            outbox: [],
            health: null,

            // UI state
            selectedBuilding: null,
            selectedTask: null,

            // Timestamps
            lastUpdate: null
        };

        this.listeners = new Set();
        this.pollInterval = null;
        this.pollRate = 2000; // 2 seconds
    }

    /**
     * Subscribe to state changes
     * @returns {Function} Unsubscribe function
     */
    subscribe(listener) {
        this.listeners.add(listener);
        // Immediately call with current state
        listener(this.state);
        return () => this.listeners.delete(listener);
    }

    /**
     * Notify all listeners of state change
     */
    notify() {
        this.listeners.forEach(listener => {
            try {
                listener(this.state);
            } catch (err) {
                console.error('Listener error:', err);
            }
        });
    }

    /**
     * Update state and notify
     */
    setState(updates) {
        this.state = { ...this.state, ...updates };
        this.notify();
    }

    /**
     * Refresh all state from MCP server
     */
    async refresh() {
        try {
            // Fetch all state in parallel
            const [status, locks, inbox, health] = await Promise.all([
                mcp.swarmStatus(),
                mcp.lockList().catch(() => []),
                mcp.inboxList().catch(() => []),
                mcp.healthCheck().catch(() => null)
            ]);

            this.setState({
                connected: true,
                lastError: null,
                wave: status.wave || 0,
                zerglings: status.active_zerglings || [],
                pendingTasks: status.pending_tasks || [],
                completedTasks: status.completed_tasks || [],
                locks,
                inbox,
                health,
                lastUpdate: new Date()
            });

        } catch (err) {
            console.error('Refresh failed:', err);
            this.setState({
                connected: false,
                lastError: err.message
            });
        }
    }

    /**
     * Start polling the MCP server
     */
    startPolling(rate = this.pollRate) {
        this.pollRate = rate;
        this.refresh(); // Initial fetch

        if (this.pollInterval) {
            clearInterval(this.pollInterval);
        }

        this.pollInterval = setInterval(() => {
            this.refresh();
        }, rate);

        console.log(`Polling started (${rate}ms interval)`);
    }

    /**
     * Stop polling
     */
    stopPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
            console.log('Polling stopped');
        }
    }

    // === Actions (mutations that call MCP) ===

    async nextWave() {
        try {
            const result = await mcp.waveIncrement();
            await this.refresh();
            return result;
        } catch (err) {
            this.setState({ lastError: err.message });
            throw err;
        }
    }

    async collectResults() {
        try {
            const result = await mcp.waveCollect();
            await this.refresh();
            return result;
        } catch (err) {
            this.setState({ lastError: err.message });
            throw err;
        }
    }

    async resetSwarm() {
        try {
            const result = await mcp.swarmReset();
            await this.refresh();
            return result;
        } catch (err) {
            this.setState({ lastError: err.message });
            throw err;
        }
    }

    async getTasksForLane(lane) {
        try {
            return await mcp.taskList(lane);
        } catch (err) {
            this.setState({ lastError: err.message });
            throw err;
        }
    }

    async getTaskDetails(taskId, lane) {
        try {
            return await mcp.taskGet(taskId, lane);
        } catch (err) {
            this.setState({ lastError: err.message });
            throw err;
        }
    }

    // === UI State ===

    selectBuilding(buildingId) {
        this.setState({ selectedBuilding: buildingId });
    }

    clearSelection() {
        this.setState({ selectedBuilding: null, selectedTask: null });
    }
}

// Export singleton
export const store = new SwarmStore();
