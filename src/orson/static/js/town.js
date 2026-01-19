/**
 * Town Renderer - Isometric pixel art town with UFO spawn point
 *
 * Renders the Midwestern town on a canvas with:
 * - Buildings mapped to swarm lanes
 * - UFO hovering over town square (spawn point)
 * - Animated workers (zerglings in flannel)
 * - Visual feedback for state changes
 */

// Building definitions with positions and lane mappings
const BUILDINGS = {
    townHall: {
        id: 'townHall',
        name: 'Town Hall',
        lane: null, // Overlord HQ
        description: 'Mayor\'s Office - Wave Control',
        gridX: 1, gridY: 1,
        width: 80, height: 100,
        color: '#d4a574',
        roofColor: '#8B0000',
        icon: '🏛️'
    },
    silo: {
        id: 'silo',
        name: 'Grain Silo',
        lane: 'KERNEL',
        description: 'GPU Processing - CUDA/Triton',
        gridX: 3, gridY: 1,
        width: 50, height: 90,
        color: '#c0c0c0',
        roofColor: '#808080',
        icon: '🏭'
    },
    library: {
        id: 'library',
        name: 'Public Library',
        lane: 'ML',
        description: 'Model Storage - Training/Inference',
        gridX: 5, gridY: 1,
        width: 70, height: 70,
        color: '#8b4513',
        roofColor: '#654321',
        icon: '📚'
    },
    bank: {
        id: 'bank',
        name: 'First National Bank',
        lane: 'QUANT',
        description: 'Strategy Vault - Backtests/Signals',
        gridX: 1, gridY: 3,
        width: 70, height: 80,
        color: '#f5f5dc',
        roofColor: '#2f4f4f',
        icon: '🏦'
    },
    gasStation: {
        id: 'gasStation',
        name: 'Gas-N-Sip',
        lane: 'DEX',
        description: 'Fuel Station - Solana/Jupiter',
        gridX: 3, gridY: 3,
        width: 60, height: 50,
        color: '#ff6b6b',
        roofColor: '#cc5555',
        icon: '⛽'
    },
    postOffice: {
        id: 'postOffice',
        name: 'Post Office',
        lane: null, // INBOX/OUTBOX
        description: 'Mail Room - Results & Assignments',
        gridX: 5, gridY: 3,
        width: 60, height: 60,
        color: '#4a90d9',
        roofColor: '#2c5aa0',
        icon: '📮'
    },
    church: {
        id: 'church',
        name: 'Community Church',
        lane: 'INTEGRATION',
        description: 'Bringing It Together - CLI/Config',
        gridX: 5, gridY: 5,
        width: 50, height: 80,
        color: '#ffffff',
        roofColor: '#333333',
        icon: '⛪'
    },
    cemetery: {
        id: 'cemetery',
        name: 'Peaceful Acres',
        lane: null, // Completed workers
        description: 'Worker Graveyard - Completed Tasks',
        gridX: 6, gridY: 5,
        width: 80, height: 60,
        color: '#3a5a3a',
        roofColor: null,
        icon: '🪦'
    }
};

// UFO configuration
const UFO = {
    gridX: 3,
    gridY: 4,
    width: 60,
    height: 30,
    hoverHeight: 80,
    beamWidth: 40,
    color: '#7c3aed',
    glowColor: 'rgba(124, 58, 237, 0.3)'
};

class TownRenderer {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');

        // Grid settings
        this.tileWidth = 64;
        this.tileHeight = 32;
        this.offsetX = canvas.width / 2;
        this.offsetY = 80;

        // Animation state
        this.frame = 0;
        this.ufoPhase = 0;
        this.beamActive = false;
        this.workers = [];
        this.particles = [];

        // Interaction
        this.hoveredBuilding = null;
        this.selectedBuilding = null;

        // Bind events
        this.canvas.addEventListener('mousemove', this.onMouseMove.bind(this));
        this.canvas.addEventListener('click', this.onClick.bind(this));

        // Start animation loop
        this.animate();
    }

    /**
     * Convert grid coordinates to screen coordinates (isometric)
     */
    gridToScreen(gridX, gridY) {
        return {
            x: (gridX - gridY) * (this.tileWidth / 2) + this.offsetX,
            y: (gridX + gridY) * (this.tileHeight / 2) + this.offsetY
        };
    }

    /**
     * Convert screen coordinates to grid coordinates
     */
    screenToGrid(screenX, screenY) {
        const adjustedX = screenX - this.offsetX;
        const adjustedY = screenY - this.offsetY;
        return {
            x: Math.floor((adjustedX / (this.tileWidth / 2) + adjustedY / (this.tileHeight / 2)) / 2),
            y: Math.floor((adjustedY / (this.tileHeight / 2) - adjustedX / (this.tileWidth / 2)) / 2)
        };
    }

    /**
     * Draw the ground/grass
     */
    drawGround() {
        const ctx = this.ctx;

        // Base grass
        ctx.fillStyle = '#4a7c23';
        ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        // Draw isometric grid tiles
        for (let y = 0; y < 8; y++) {
            for (let x = 0; x < 8; x++) {
                const pos = this.gridToScreen(x, y);
                this.drawTile(pos.x, pos.y, '#5a8c33', '#4a7c23');
            }
        }

        // Main Street (horizontal road)
        this.drawRoad(0, 2, 7, 2);
    }

    /**
     * Draw an isometric tile
     */
    drawTile(x, y, fillColor, strokeColor) {
        const ctx = this.ctx;
        const hw = this.tileWidth / 2;
        const hh = this.tileHeight / 2;

        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(x + hw, y + hh);
        ctx.lineTo(x, y + this.tileHeight);
        ctx.lineTo(x - hw, y + hh);
        ctx.closePath();

        ctx.fillStyle = fillColor;
        ctx.fill();
        ctx.strokeStyle = strokeColor;
        ctx.lineWidth = 1;
        ctx.stroke();
    }

    /**
     * Draw a road segment
     */
    drawRoad(x1, y1, x2, _y2) {
        const ctx = this.ctx;

        for (let x = x1; x <= x2; x++) {
            const pos = this.gridToScreen(x, y1);
            this.drawTile(pos.x, pos.y, '#555555', '#444444');

            // Road markings
            ctx.fillStyle = '#ffff00';
            ctx.fillRect(pos.x - 2, pos.y + this.tileHeight/2 - 1, 4, 2);
        }
    }

    /**
     * Draw a building
     */
    drawBuilding(building, isHovered = false, isSelected = false) {
        const ctx = this.ctx;
        const pos = this.gridToScreen(building.gridX, building.gridY);

        const w = building.width;
        const h = building.height;
        const x = pos.x - w/2;
        const y = pos.y - h;

        // Shadow
        ctx.fillStyle = 'rgba(0, 0, 0, 0.2)';
        ctx.beginPath();
        ctx.ellipse(pos.x, pos.y + 10, w/2, 15, 0, 0, Math.PI * 2);
        ctx.fill();

        // Building body
        ctx.fillStyle = building.color;
        if (isHovered) {
            ctx.fillStyle = this.lightenColor(building.color, 20);
        }
        if (isSelected) {
            ctx.strokeStyle = '#e94560';
            ctx.lineWidth = 3;
        }

        ctx.fillRect(x, y, w, h);

        if (isSelected) {
            ctx.strokeRect(x, y, w, h);
        }

        // Roof (if applicable)
        if (building.roofColor) {
            ctx.fillStyle = building.roofColor;
            ctx.beginPath();
            ctx.moveTo(x - 5, y);
            ctx.lineTo(pos.x, y - 25);
            ctx.lineTo(x + w + 5, y);
            ctx.closePath();
            ctx.fill();
        }

        // Windows
        ctx.fillStyle = '#87CEEB';
        const windowSize = 10;
        const windowMargin = 15;
        for (let wy = y + 20; wy < y + h - 20; wy += 25) {
            for (let wx = x + windowMargin; wx < x + w - windowMargin; wx += 20) {
                ctx.fillRect(wx, wy, windowSize, windowSize);
            }
        }

        // Icon/Label
        ctx.font = '20px serif';
        ctx.textAlign = 'center';
        ctx.fillText(building.icon, pos.x, y - 30);

        // Name on hover
        if (isHovered) {
            ctx.fillStyle = '#ffffff';
            ctx.font = 'bold 12px monospace';
            ctx.fillText(building.name, pos.x, y - 45);

            if (building.lane) {
                ctx.fillStyle = '#7c3aed';
                ctx.font = '10px monospace';
                ctx.fillText(`[${building.lane}]`, pos.x, y - 58);
            }
        }
    }

    /**
     * Draw the UFO spawn point
     */
    drawUFO() {
        const ctx = this.ctx;
        const pos = this.gridToScreen(UFO.gridX, UFO.gridY);

        // Hover animation
        const hoverOffset = Math.sin(this.ufoPhase) * 5;
        const ufoY = pos.y - UFO.hoverHeight + hoverOffset;

        // Beam (when spawning)
        if (this.beamActive) {
            const gradient = ctx.createLinearGradient(pos.x, ufoY + UFO.height, pos.x, pos.y);
            gradient.addColorStop(0, 'rgba(124, 58, 237, 0.8)');
            gradient.addColorStop(1, 'rgba(124, 58, 237, 0)');

            ctx.fillStyle = gradient;
            ctx.beginPath();
            ctx.moveTo(pos.x - UFO.beamWidth/2, ufoY + UFO.height);
            ctx.lineTo(pos.x + UFO.beamWidth/2, ufoY + UFO.height);
            ctx.lineTo(pos.x + UFO.beamWidth, pos.y);
            ctx.lineTo(pos.x - UFO.beamWidth, pos.y);
            ctx.closePath();
            ctx.fill();
        }

        // UFO glow
        ctx.fillStyle = UFO.glowColor;
        ctx.beginPath();
        ctx.ellipse(pos.x, ufoY + UFO.height/2, UFO.width/2 + 10, UFO.height/2 + 10, 0, 0, Math.PI * 2);
        ctx.fill();

        // UFO body (saucer shape)
        ctx.fillStyle = '#4a4a6a';
        ctx.beginPath();
        ctx.ellipse(pos.x, ufoY + UFO.height/2, UFO.width/2, UFO.height/3, 0, 0, Math.PI * 2);
        ctx.fill();

        // UFO dome
        ctx.fillStyle = UFO.color;
        ctx.beginPath();
        ctx.ellipse(pos.x, ufoY + UFO.height/4, UFO.width/4, UFO.height/3, 0, Math.PI, 0);
        ctx.fill();

        // UFO lights
        const lightCount = 5;
        for (let i = 0; i < lightCount; i++) {
            const angle = (i / lightCount) * Math.PI + this.ufoPhase;
            const lx = pos.x + Math.cos(angle) * (UFO.width/2 - 5);
            const ly = ufoY + UFO.height/2 + Math.sin(angle) * 3;

            ctx.fillStyle = i % 2 === 0 ? '#ff0000' : '#00ff00';
            ctx.beginPath();
            ctx.arc(lx, ly, 3, 0, Math.PI * 2);
            ctx.fill();
        }

        // Label
        ctx.fillStyle = '#7c3aed';
        ctx.font = 'bold 10px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('SPAWN POINT', pos.x, pos.y + 20);
    }

    /**
     * Draw workers (zerglings)
     */
    drawWorkers() {
        const ctx = this.ctx;

        this.workers.forEach(worker => {
            const pos = this.gridToScreen(worker.x, worker.y);

            // Body (small purple-tinted figure)
            ctx.fillStyle = '#7c3aed';
            ctx.beginPath();
            ctx.arc(pos.x, pos.y - 8, 6, 0, Math.PI * 2);
            ctx.fill();

            // Flannel pattern (stripes)
            ctx.strokeStyle = '#cc5555';
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(pos.x - 4, pos.y - 10);
            ctx.lineTo(pos.x - 4, pos.y - 6);
            ctx.moveTo(pos.x, pos.y - 10);
            ctx.lineTo(pos.x, pos.y - 6);
            ctx.moveTo(pos.x + 4, pos.y - 10);
            ctx.lineTo(pos.x + 4, pos.y - 6);
            ctx.stroke();

            // Antennae
            ctx.strokeStyle = '#7c3aed';
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(pos.x - 2, pos.y - 14);
            ctx.lineTo(pos.x - 4, pos.y - 18);
            ctx.moveTo(pos.x + 2, pos.y - 14);
            ctx.lineTo(pos.x + 4, pos.y - 18);
            ctx.stroke();

            // Name tag
            if (worker.name) {
                ctx.fillStyle = '#ffffff';
                ctx.font = '8px monospace';
                ctx.textAlign = 'center';
                ctx.fillText(worker.name.slice(0, 8), pos.x, pos.y + 5);
            }
        });
    }

    /**
     * Draw spawn particles
     */
    drawParticles() {
        const ctx = this.ctx;

        this.particles = this.particles.filter(p => {
            p.life -= 0.02;
            p.y += p.vy;
            p.x += p.vx;

            if (p.life <= 0) return false;

            ctx.fillStyle = `rgba(124, 58, 237, ${p.life})`;
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.size * p.life, 0, Math.PI * 2);
            ctx.fill();

            return true;
        });
    }

    /**
     * Spawn a worker with beam effect
     */
    spawnWorker(name) {
        this.beamActive = true;

        const pos = this.gridToScreen(UFO.gridX, UFO.gridY);

        // Create particles
        for (let i = 0; i < 20; i++) {
            this.particles.push({
                x: pos.x + (Math.random() - 0.5) * UFO.beamWidth,
                y: pos.y - UFO.hoverHeight + Math.random() * UFO.hoverHeight,
                vx: (Math.random() - 0.5) * 2,
                vy: Math.random() * 3,
                size: Math.random() * 4 + 2,
                life: 1
            });
        }

        // Add worker
        setTimeout(() => {
            this.workers.push({
                name,
                x: UFO.gridX + (Math.random() - 0.5),
                y: UFO.gridY + (Math.random() - 0.5),
                targetX: null,
                targetY: null
            });
            this.beamActive = false;
        }, 500);
    }

    /**
     * Update workers from state
     */
    updateWorkers(zerglings) {
        // Match workers to zerglings
        const names = new Set(zerglings.map(z => z.name));

        // Remove workers not in state
        this.workers = this.workers.filter(w => names.has(w.name));

        // Add new workers
        zerglings.forEach(z => {
            if (!this.workers.find(w => w.name === z.name)) {
                this.spawnWorker(z.name);
            }
        });
    }

    /**
     * Main render function
     */
    render() {
        const ctx = this.ctx;

        // Clear
        ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // Draw layers
        this.drawGround();

        // Draw buildings (sorted by Y for depth)
        const sortedBuildings = Object.values(BUILDINGS)
            .sort((a, b) => (a.gridX + a.gridY) - (b.gridX + b.gridY));

        sortedBuildings.forEach(building => {
            this.drawBuilding(
                building,
                this.hoveredBuilding === building.id,
                this.selectedBuilding === building.id
            );
        });

        // Draw UFO
        this.drawUFO();

        // Draw workers
        this.drawWorkers();

        // Draw particles
        this.drawParticles();
    }

    /**
     * Animation loop
     */
    animate() {
        this.frame++;
        this.ufoPhase += 0.05;

        this.render();

        requestAnimationFrame(() => this.animate());
    }

    /**
     * Handle mouse move (hover detection)
     */
    onMouseMove(event) {
        const rect = this.canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;

        // Check building hits
        this.hoveredBuilding = null;

        for (const [id, building] of Object.entries(BUILDINGS)) {
            const pos = this.gridToScreen(building.gridX, building.gridY);
            const bx = pos.x - building.width/2;
            const by = pos.y - building.height;

            if (x >= bx && x <= bx + building.width &&
                y >= by && y <= by + building.height) {
                this.hoveredBuilding = id;
                this.canvas.style.cursor = 'pointer';
                return;
            }
        }

        this.canvas.style.cursor = 'default';
    }

    /**
     * Handle click (building selection)
     */
    onClick(_event) {
        if (this.hoveredBuilding) {
            this.selectedBuilding = this.hoveredBuilding;

            // Dispatch custom event
            const building = BUILDINGS[this.hoveredBuilding];
            this.canvas.dispatchEvent(new CustomEvent('building-select', {
                detail: building
            }));
        } else {
            this.selectedBuilding = null;
            this.canvas.dispatchEvent(new CustomEvent('building-deselect'));
        }
    }

    /**
     * Utility: lighten a hex color
     */
    lightenColor(hex, percent) {
        const num = parseInt(hex.replace('#', ''), 16);
        const amt = Math.round(2.55 * percent);
        const R = (num >> 16) + amt;
        const G = (num >> 8 & 0x00FF) + amt;
        const B = (num & 0x0000FF) + amt;
        return '#' + (
            0x1000000 +
            (R < 255 ? R < 1 ? 0 : R : 255) * 0x10000 +
            (G < 255 ? G < 1 ? 0 : G : 255) * 0x100 +
            (B < 255 ? B < 1 ? 0 : B : 255)
        ).toString(16).slice(1);
    }
}

export { TownRenderer, BUILDINGS, UFO };
