const API_BASE = "http://127.0.0.1:8001/api";

let processingOscillator = null;
let processingGain = null;
let lfoNode = null;

// Initialize Audio Context lazily
const audioCtx = new (window.AudioContext || window.webkitAudioContext)();

/* --- Sound System --- */

function playClickSound() {
    if (audioCtx.state === 'suspended') audioCtx.resume();
    const oscillator = audioCtx.createOscillator();
    const gainNode = audioCtx.createGain();

    oscillator.type = 'square';
    oscillator.frequency.setValueAtTime(800, audioCtx.currentTime);
    oscillator.frequency.exponentialRampToValueAtTime(100, audioCtx.currentTime + 0.15);

    gainNode.gain.setValueAtTime(0.05, audioCtx.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.15);

    oscillator.connect(gainNode);
    gainNode.connect(audioCtx.destination);

    oscillator.start();
    oscillator.stop(audioCtx.currentTime + 0.15 + 0.1);
}

function playHoverSound() {
    if (audioCtx.state === 'suspended') return; // Don't resume on hover to avoid annoyance
    const oscillator = audioCtx.createOscillator();
    const gainNode = audioCtx.createGain();

    oscillator.type = 'sine';
    oscillator.frequency.setValueAtTime(2000, audioCtx.currentTime);
    oscillator.frequency.exponentialRampToValueAtTime(1000, audioCtx.currentTime + 0.03);

    gainNode.gain.setValueAtTime(0.01, audioCtx.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.03);

    oscillator.connect(gainNode);
    gainNode.connect(audioCtx.destination);

    oscillator.start();
    oscillator.stop(audioCtx.currentTime + 0.03 + 0.1);
}

function startProcessingSound() {
    if (audioCtx.state === 'suspended') audioCtx.resume();
    if (processingOscillator) return;

    processingOscillator = audioCtx.createOscillator();
    processingGain = audioCtx.createGain();

    // Low throbbing drone
    processingOscillator.type = 'sawtooth';
    processingOscillator.frequency.setValueAtTime(60, audioCtx.currentTime);

    // Create LFO for pulsing effect
    lfoNode = audioCtx.createOscillator();
    lfoNode.type = 'sine';
    lfoNode.frequency.value = 4;

    const lfoGain = audioCtx.createGain();
    lfoGain.gain.value = 0.02;

    lfoNode.connect(lfoGain);
    lfoGain.connect(processingGain.gain);

    // Base volume
    processingGain.gain.setValueAtTime(0.04, audioCtx.currentTime);

    processingOscillator.connect(processingGain);
    processingGain.connect(audioCtx.destination);

    processingOscillator.start();
    lfoNode.start();
}

function stopProcessingSound() {
    if (processingOscillator) {
        try {
            processingOscillator.stop();
            if (lfoNode) lfoNode.stop();
        } catch (e) { console.warn("Error stopping sound", e); }

        processingOscillator.disconnect();
        if (lfoNode) lfoNode.disconnect();
        if (processingGain) processingGain.disconnect();

        processingOscillator = null;
        lfoNode = null;
        processingGain = null;
    }
}

function playDataBlip() {
    if (audioCtx.state === 'suspended') audioCtx.resume();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();

    osc.type = 'sine';
    osc.frequency.setValueAtTime(1200, audioCtx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(800, audioCtx.currentTime + 0.05);

    gain.gain.setValueAtTime(0.05, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.05);

    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start();
    osc.stop(audioCtx.currentTime + 0.1);
}

function playSuccessSound() {
    if (audioCtx.state === 'suspended') audioCtx.resume();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();

    osc.type = 'triangle';
    // Arpeggio
    osc.frequency.setValueAtTime(440, audioCtx.currentTime);
    osc.frequency.setValueAtTime(554.37, audioCtx.currentTime + 0.1);
    osc.frequency.setValueAtTime(659.25, audioCtx.currentTime + 0.2);
    osc.frequency.exponentialRampToValueAtTime(880, audioCtx.currentTime + 0.4);

    gain.gain.setValueAtTime(0.1, audioCtx.currentTime);
    gain.gain.linearRampToValueAtTime(0.1, audioCtx.currentTime + 0.3);
    gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.6);

    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start();
    osc.stop(audioCtx.currentTime + 0.6);
}

function playErrorSound() {
    if (audioCtx.state === 'suspended') audioCtx.resume();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();

    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(150, audioCtx.currentTime);
    osc.frequency.linearRampToValueAtTime(100, audioCtx.currentTime + 0.3);

    gain.gain.setValueAtTime(0.2, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.3);

    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start();
    osc.stop(audioCtx.currentTime + 0.3);
}

function playTypingSound() {
    if (audioCtx.state === 'suspended') return;
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();

    osc.type = 'triangle';
    osc.frequency.setValueAtTime(3000, audioCtx.currentTime);

    gain.gain.setValueAtTime(0.01, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.02);

    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start();
    osc.stop(audioCtx.currentTime + 0.03);
}


/* --- Application Logic --- */

async function apiRequest(endpoint, method = 'GET', body = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
        },
    };
    if (body) options.body = JSON.stringify(body);

    try {
        const response = await fetch(`${API_BASE}${endpoint}`, options);
        if (!response.ok) throw new Error(`API Error: ${response.statusText}`);
        return await response.json();
    } catch (error) {
        console.error("API Request Failed:", error);
        return { error: error.message };
    }
}

// Typewriter Effect for Terminal
async function typeLine(text, isCritical = false) {
    const feed = document.getElementById('intelligence_feed');
    if (!feed) return;

    if (isCritical) playErrorSound();
    else playDataBlip();

    const line = document.createElement('div');
    line.className = 'log-entry';
    if (isCritical) line.classList.add('log-critical');

    const timeSpan = document.createElement('span');
    timeSpan.className = 'log-time';
    timeSpan.innerText = `[${new Date().toLocaleTimeString()}]`;
    line.appendChild(timeSpan);

    const textSpan = document.createElement('span');
    line.appendChild(textSpan);
    feed.appendChild(line);
    feed.scrollTop = feed.scrollHeight;

    for (let i = 0; i < text.length; i++) {
        textSpan.innerText += text[i];
        if (i % 3 === 0) playTypingSound();
        await new Promise(resolve => setTimeout(resolve, 20));
    }
}

async function welcomeSequence() {
    if (window.location.pathname.includes('command-center.html') || window.location.pathname.endsWith('/')) {
        // Only run if not already populated (optional check, but good for SPA feel if we had it)
        const feed = document.getElementById('intelligence_feed');
        if (feed && feed.children.length === 0) {
            await typeLine("INITIALIZING HIGH NOIR PROTOCOL...");
            await typeLine("ESTABLISHING CONNECTION TO FFTE ORCHESTRATOR...");
            await typeLine("SYSTEM READY. WAITING FOR TARGET SPECIFICATION.");
        }
    }
}

// Command Center Logic
async function startScan() {
    const targetUrl = document.getElementById('target_url').value;
    const scanName = document.getElementById('scan_name').value;
    const maxCases = document.getElementById('max_cases').value || 3;

    if (!targetUrl) {
        await typeLine("ERROR: TARGET_SPEC_URL IS NULL", true);
        alert("Please enter a target URL");
        return;
    }

    playSuccessSound();
    await typeLine(`INITIATING SCAN: ${scanName || 'UNNAMED_ALPHA'}`);
    await typeLine(`THREAT LEVEL: ${maxCases > 5 ? 'MAXIMUM' : 'MODERATE'}`);

    const sec01 = document.getElementById('sec-01');
    if (sec01) sec01.classList.add('pulse');

    const result = await apiRequest('/scan/start', 'POST', {
        target_url: targetUrl,
        spec_url: targetUrl,
        scan_name: scanName,
        max_cases_per_field: parseInt(maxCases)
    });

    if (result.scan_id) {
        await typeLine(`SCAN_STARTED: ${result.scan_id}`);
        await typeLine("TRANSITIONING TO THE LAB...", true);
        localStorage.setItem('current_scan_id', result.scan_id);

        setTimeout(() => {
            window.location.href = 'the-lab.html';
        }, 1500);
    } else {
        await typeLine(`CRITICAL_FAILURE: ${result.error || 'UNKNOWN_ERROR'}`, true);
        playErrorSound();
        if (sec01) sec01.classList.remove('pulse');
        alert("Failed to start scan: " + (result.error || "Unknown error"));
    }
}

// The Lab Logic
let previousEndpointCount = 0;

async function updateScanStatus() {
    const scanId = localStorage.getItem('current_scan_id');
    if (!scanId) return;

    const status = await apiRequest(`/scan/${scanId}`);
    if (status.error) return;

    // Start processing sound if running and not already playing
    if (status.status === 'running' && !processingOscillator) {
        startProcessingSound();
    }

    const progressEl = document.getElementById('progress_bar');
    const statusTextEl = document.getElementById('status_text');
    const endpointsListEl = document.getElementById('endpoints_list');

    if (progressEl) progressEl.style.width = `${status.progress}%`;
    if (statusTextEl) statusTextEl.innerText = status.status.toUpperCase();

    if (endpointsListEl && status.endpoints) {
        // Verify if we have new endpoints to play sound
        if (status.endpoints.length > previousEndpointCount) {
            // Play multiple blips if many added, or just one
            playDataBlip();
            previousEndpointCount = status.endpoints.length;
        }

        endpointsListEl.innerHTML = status.endpoints.map(e => `
            <div class="endpoint-item">
                <span class="method method-${e.method}">${e.method}</span>
                <span class="path">${e.path}</span>
            </div>
        `).join('');
    }

    if (status.status === 'completed') {
        if (processingOscillator) stopProcessingSound();

        // Only run completion logic once
        if (statusInterval) {
            clearInterval(statusInterval);
            statusInterval = null;
            playSuccessSound();
            document.getElementById('view_results_btn')?.classList.remove('hidden');
        }
    }
}

// War Room Logic
async function loadResults() {
    const scanId = localStorage.getItem('current_scan_id');
    if (!scanId) return;

    const results = await apiRequest(`/scan/${scanId}/results`);
    if (results.error) return;

    playSuccessSound();

    document.getElementById('total_tests').innerText = results.statistics.tests || results.statistics.total_tests;
    document.getElementById('total_failures').innerText = results.statistics.failures;
    document.getElementById('endpoints_count').innerText = results.statistics.endpoints;

    const failuresEl = document.getElementById('failures_list');
    if (failuresEl) {
        failuresEl.innerHTML = results.failures.map(f => `
            <div class="glass-card failure-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <span class="method method-${f.method}">${f.method}</span>
                    <span class="status status-failed">${f.type}</span>
                </div>
                <div style="font-family: monospace; font-size: 0.9rem; color: #fff; margin-bottom: 1rem;">
                    ${f.url}
                </div>
                <div style="background: rgba(0,0,0,0.5); padding: 10px; border-radius: 4px; font-size: 0.8rem; border: 1px solid var(--border);">
                    <div style="color: var(--text-muted); margin-bottom: 5px;">Payload:</div>
                    <code>${f.payload}</code>
                </div>
            </div>
        `).join('');

        if (results.failures.length > 0) {
            setTimeout(playErrorSound, 500); // Play after success sound
        }
    }

    const reportEl = document.getElementById('formatted_report');
    if (reportEl) {
        reportEl.innerText = results.formatted_report;
    }
}

let statusInterval;

function init() {
    const page = window.location.pathname.split('/').pop();

    // Attach event listeners for sounds to all buttons/links
    const interactives = document.querySelectorAll('button, a, .btn-launch');
    interactives.forEach(el => {
        el.addEventListener('click', playClickSound);
        el.addEventListener('mouseenter', playHoverSound);
    });

    // Try to resume AudioContext on page load interaction (usually requires user input)
    document.body.addEventListener('click', () => {
        if (audioCtx.state === 'suspended') audioCtx.resume();
    }, { once: true });

    if (page === 'command-center.html' || page === '') {
        welcomeSequence();
    } else if (page === 'the-lab.html') {
        statusInterval = setInterval(updateScanStatus, 2000);
        updateScanStatus();
    } else if (page === 'war-room.html') {
        loadResults();
    }
}

window.onload = init;
