/**
 * API Client - Wrapper for Orson REST API
 *
 * Communicates with the Orson server's REST API endpoints
 * which read/write directly to the SWARM directory.
 */

// Use same origin (Orson server serves both UI and API)
const API_BASE = '/api';

class APIClient {
    constructor(baseUrl = API_BASE) {
        this.baseUrl = baseUrl;
    }

    /**
     * Internal: Make an API call
     */
    async _get(endpoint) {
        const response = await fetch(`${this.baseUrl}${endpoint}`);

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: response.statusText }));
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        return response.json();
    }

    async _post(endpoint, data = {}) {
        const response = await fetch(`${this.baseUrl}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: response.statusText }));
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        return response.json();
    }

    async _delete(endpoint) {
        const response = await fetch(`${this.baseUrl}${endpoint}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: response.statusText }));
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        return response.json();
    }

    // === Health ===

    async healthCheck() {
        return this._get('/health');
    }

    // === State Management ===

    async swarmStatus() {
        return this._get('/swarm/status');
    }

    async swarmReset() {
        return this._post('/swarm/reset');
    }

    // === Task Operations ===

    async taskList(lane = null) {
        const endpoint = lane ? `/tasks?lane=${lane}` : '/tasks';
        return this._get(endpoint);
    }

    async taskGet(taskId, lane) {
        return this._get(`/tasks/${lane}/${taskId}`);
    }

    // === Zergling Operations ===

    async zerglingRegister(name) {
        return this._post(`/zerglings/${name}`);
    }

    async zerglingUnregister(name) {
        return this._delete(`/zerglings/${name}`);
    }

    async zerglingList() {
        return this._get('/zerglings');
    }

    // === Lock Operations ===

    async lockList() {
        return this._get('/locks');
    }

    // === Wave Operations ===

    async waveStatus() {
        return this._get('/wave');
    }

    async waveIncrement() {
        return this._post('/wave/increment');
    }

    async waveCollect() {
        return this._post('/wave/collect');
    }

    // === Result Operations ===

    async inboxList() {
        return this._get('/inbox');
    }

    async resultGet(taskId) {
        return this._get(`/inbox/${taskId}`);
    }

    // === Utility ===

    /**
     * Test connection to API server
     */
    async ping() {
        try {
            await this.healthCheck();
            return true;
        } catch {
            return false;
        }
    }
}

// Export singleton instance (named 'mcp' for compatibility)
export const mcp = new APIClient();
export { APIClient };
