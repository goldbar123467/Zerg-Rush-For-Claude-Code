/**
 * Orson Agent IDE - Main Application
 *
 * Entry point that initializes all components and manages UI state.
 */

import { mcp } from './mcp-client.js';
import { store } from './store.js';
import { TownRenderer } from './town.js';

// DOM Elements
const elements = {
    // Status bar
    waveNum: document.getElementById('wave-num'),
    workerCount: document.getElementById('worker-count'),
    pendingCount: document.getElementById('pending-count'),
    completedCount: document.getElementById('completed-count'),
    healthIndicator: document.getElementById('health-indicator'),

    // Worker panel
    workerList: document.getElementById('worker-list'),
    voicelineTicker: document.querySelector('.ticker-text'),

    // Buttons
    btnCollect: document.getElementById('btn-collect'),
    btnNextWave: document.getElementById('btn-next-wave'),
    btnClosePanel: document.getElementById('btn-close-panel'),

    // Building panel
    buildingPanel: document.getElementById('building-panel'),
    buildingTitle: document.getElementById('building-title'),
    buildingContent: document.getElementById('building-content'),

    // Overlay
    connectionOverlay: document.getElementById('connection-overlay'),

    // Canvas
    townCanvas: document.getElementById('town-canvas')
};

// Town renderer instance
let town = null;

// Voicelines for the ticker
const VOICELINES = [
    "Welcome to Orson. The Mayor would like a word about your task decomposition.",
    "The corn is listening. The corn knows all.",
    "Zerglings don't need coffee. They run on pure purpose.",
    "Another day, another wave. Such is life in Orson.",
    "The UFO has been here since '58. We don't ask questions.",
    "File locks are sacred. Respect the locksmith.",
    "4 minutes. 100 lines. No exceptions. No mercy.",
    "The cemetery is peaceful. Your workers deserve rest.",
    "Main Street sees all. Main Street forgets nothing.",
    "Spawn. Bite. Die. Repeat. The Orson way.",
    "The bank vault holds strategies, not gold.",
    "Library books are models. Check one out today.",
    "Gas-N-Sip: Fuel for your transactions.",
    "Church services every wave. All zerglings welcome.",
    "Post Office hours: 24/7/365. Results never sleep."
];

let voicelineIndex = 0;

/**
 * Initialize the application
 */
async function init() {
    console.log('Orson Agent IDE initializing...');

    // Show connection overlay
    elements.connectionOverlay.classList.remove('overlay-hidden');

    // Try to connect to MCP server
    const connected = await mcp.ping();

    if (!connected) {
        console.error('Failed to connect to MCP server');
        // Keep overlay visible with error state
        elements.connectionOverlay.querySelector('p').textContent = 'Cannot connect to MCP Server';
        elements.connectionOverlay.querySelector('.spinner').style.borderTopColor = '#f87171';

        // Retry connection every 3 seconds
        setInterval(async () => {
            if (await mcp.ping()) {
                elements.connectionOverlay.classList.add('overlay-hidden');
                store.startPolling();
            }
        }, 3000);

        return;
    }

    // Hide overlay
    elements.connectionOverlay.classList.add('overlay-hidden');

    // Initialize town renderer
    town = new TownRenderer(elements.townCanvas);

    // Set up event listeners
    setupEventListeners();

    // Subscribe to store updates
    store.subscribe(updateUI);

    // Start polling
    store.startPolling(2000);

    // Start voiceline rotation
    setInterval(rotateVoiceline, 15000);

    console.log('Orson Agent IDE ready');
}

/**
 * Set up event listeners
 */
function setupEventListeners() {
    // Collect button
    elements.btnCollect.addEventListener('click', async () => {
        elements.btnCollect.disabled = true;
        elements.btnCollect.textContent = '📬 Collecting...';

        try {
            const result = await store.collectResults();
            showVoiceline(`Collected ${result?.collected || 0} results from the Post Office.`);
        } catch (err) {
            showVoiceline(`Collection failed: ${err.message}`);
        }

        elements.btnCollect.disabled = false;
        elements.btnCollect.textContent = '📬 Collect';
    });

    // Next wave button
    elements.btnNextWave.addEventListener('click', async () => {
        elements.btnNextWave.disabled = true;
        elements.btnNextWave.textContent = '🌊 Spawning...';

        try {
            const result = await store.nextWave();
            const newWave = result?.new_wave || result?.wave || '?';
            showVoiceline(`Wave ${newWave} begins. The UFO hums with anticipation.`);

            // Trigger beam animation
            if (town) {
                town.beamActive = true;
                setTimeout(() => { town.beamActive = false; }, 1000);
            }
        } catch (err) {
            showVoiceline(`Wave failed: ${err.message}`);
        }

        elements.btnNextWave.disabled = false;
        elements.btnNextWave.textContent = '🌊 Next Wave';
    });

    // Close building panel
    elements.btnClosePanel.addEventListener('click', () => {
        elements.buildingPanel.classList.add('panel-hidden');
        if (town) town.selectedBuilding = null;
    });

    // Building selection from canvas
    elements.townCanvas.addEventListener('building-select', async (e) => {
        const building = e.detail;
        showBuildingPanel(building);
    });

    elements.townCanvas.addEventListener('building-deselect', () => {
        elements.buildingPanel.classList.add('panel-hidden');
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            elements.buildingPanel.classList.add('panel-hidden');
            if (town) town.selectedBuilding = null;
        }
    });
}

/**
 * Update UI from store state
 */
function updateUI(state) {
    // Status bar
    elements.waveNum.textContent = state.wave;
    elements.workerCount.textContent = state.zerglings.length;
    elements.pendingCount.textContent = state.pendingTasks.length;
    elements.completedCount.textContent = state.completedTasks.length;

    // Health indicator
    if (state.connected) {
        elements.healthIndicator.textContent = '●';
        elements.healthIndicator.className = 'value indicator healthy';
    } else {
        elements.healthIndicator.textContent = '●';
        elements.healthIndicator.className = 'value indicator error';
    }

    // Worker list
    updateWorkerList(state.zerglings);

    // Update town workers
    if (town) {
        town.updateWorkers(state.zerglings);
    }
}

/**
 * Update the worker list panel
 */
function updateWorkerList(zerglings) {
    if (zerglings.length === 0) {
        elements.workerList.innerHTML = `
            <div class="worker-placeholder">
                No active workers. Click "Next Wave" to spawn zerglings.
            </div>
        `;
        return;
    }

    elements.workerList.innerHTML = zerglings.map(worker => {
        // Calculate time since registration
        const registered = new Date(worker.registered);
        const elapsed = Math.floor((Date.now() - registered) / 1000);
        const remaining = Math.max(0, 240 - elapsed); // 4 min TTL
        const progress = Math.min(100, (elapsed / 240) * 100);

        const minutes = Math.floor(remaining / 60);
        const seconds = remaining % 60;
        const timeStr = `${minutes}:${seconds.toString().padStart(2, '0')}`;

        const statusClass = remaining <= 0 ? 'done' : (remaining < 60 ? 'warning' : '');

        return `
            <div class="worker-card ${statusClass}">
                <div class="worker-name">${escapeHtml(worker.name)}</div>
                <div class="worker-task">Wave ${worker.wave}</div>
                <div class="worker-progress">
                    <div class="worker-progress-bar" style="width: ${progress}%"></div>
                </div>
                <div class="worker-time">${remaining > 0 ? timeStr : 'DONE'}</div>
            </div>
        `;
    }).join('');
}

/**
 * Show building panel with tasks
 */
async function showBuildingPanel(building) {
    elements.buildingTitle.textContent = `${building.icon} ${building.name}`;
    elements.buildingPanel.classList.remove('panel-hidden');

    // Show loading state
    elements.buildingContent.innerHTML = '<p>Loading tasks...</p>';

    if (!building.lane) {
        // Special buildings (Town Hall, Post Office, Cemetery)
        elements.buildingContent.innerHTML = `
            <div class="building-info">
                <p><strong>${building.description}</strong></p>
                <p style="margin-top: 10px; color: var(--text-secondary);">
                    ${getBuildingInfo(building.id)}
                </p>
            </div>
        `;
        return;
    }

    // Fetch tasks for this lane
    try {
        const tasks = await store.getTasksForLane(building.lane);

        if (!tasks || tasks.length === 0) {
            elements.buildingContent.innerHTML = `
                <div class="building-info">
                    <p><strong>${building.description}</strong></p>
                    <p style="margin-top: 10px; color: var(--text-secondary);">
                        No tasks in ${building.lane} lane.
                    </p>
                </div>
            `;
            return;
        }

        elements.buildingContent.innerHTML = `
            <div class="building-info">
                <p><strong>${building.description}</strong></p>
            </div>
            <div class="task-list">
                ${tasks.map(task => `
                    <div class="task-item" data-task-id="${escapeHtml(task.id || task)}">
                        <div class="task-id">${escapeHtml(task.id || task)}</div>
                        <div class="task-type">${escapeHtml(task.type || 'TASK')}</div>
                        <div class="task-status ${(task.status || 'pending').toLowerCase()}">
                            ${escapeHtml(task.status || 'PENDING')}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    } catch (err) {
        elements.buildingContent.innerHTML = `
            <div class="building-info">
                <p style="color: var(--error);">Error loading tasks: ${escapeHtml(err.message)}</p>
            </div>
        `;
    }
}

/**
 * Get special building info text
 */
function getBuildingInfo(buildingId) {
    const info = {
        townHall: 'The Mayor (Overlord) controls wave progression and monitors swarm health. This is command central.',
        postOffice: 'INBOX receives completed results. OUTBOX holds pending assignments. Click "Collect" to process mail.',
        cemetery: 'Where completed workers go to rest. Their task results live on in the INBOX.'
    };
    return info[buildingId] || 'A building in Orson Township.';
}

/**
 * Show a voiceline in the ticker
 */
function showVoiceline(text) {
    elements.voicelineTicker.textContent = text;
    elements.voicelineTicker.style.animation = 'none';
    elements.voicelineTicker.offsetHeight; // Trigger reflow
    elements.voicelineTicker.style.animation = '';
}

/**
 * Rotate to next random voiceline
 */
function rotateVoiceline() {
    voicelineIndex = (voicelineIndex + 1) % VOICELINES.length;
    showVoiceline(VOICELINES[voicelineIndex]);
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
