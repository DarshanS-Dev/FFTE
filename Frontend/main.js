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
    if (audioCtx.state === 'suspended') return;
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

    processingOscillator.type = 'sawtooth';
    processingOscillator.frequency.setValueAtTime(60, audioCtx.currentTime);

    lfoNode = audioCtx.createOscillator();
    lfoNode.type = 'sine';
    lfoNode.frequency.value = 4;

    const lfoGain = audioCtx.createGain();
    lfoGain.gain.value = 0.02;

    lfoNode.connect(lfoGain);
    lfoGain.connect(processingGain.gain);

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
        headers: { 'Content-Type': 'application/json' },
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
        const feed = document.getElementById('intelligence_feed');
        if (feed && feed.children.length === 0) {
            await typeLine("INITIALIZING HIGH NOIR PROTOCOL...");
            await typeLine("ESTABLISHING CONNECTION TO FFTE ORCHESTRATOR...");
            await typeLine("SYSTEM READY. WAITING FOR TARGET SPECIFICATION.");
        }
    }
}

// ── Command Center ────────────────────────────────────────────────────────────
async function startScan() {
    const targetUrl = document.getElementById('target_url').value;
    const scanName = document.getElementById('scan_name').value;

    // Read from the correct input id (fixed from previous bug where it was 'max_cases')
    const intensityInput = document.getElementById('fuzzing_intensity');
    const intensityValue = intensityInput
        ? Math.min(10, Math.max(1, parseInt(intensityInput.value) || 5))
        : 5;

    const intensityLabels = {
        1: 'LOW', 2: 'LOW', 3: 'LOW',
        4: 'MEDIUM', 5: 'MEDIUM',
        6: 'HIGH', 7: 'HIGH',
        8: 'VERY HIGH', 9: 'VERY HIGH',
        10: 'EXTREME'
    };
    const intensityLabel = intensityLabels[intensityValue] || 'MEDIUM';

    if (!targetUrl) {
        await typeLine("ERROR: TARGET_SPEC_URL IS NULL", true);
        alert("Please enter a target URL");
        return;
    }

    playSuccessSound();
    await typeLine(`INITIATING SCAN: ${scanName || 'UNNAMED_ALPHA'}`);
    await typeLine(`FUZZING INTENSITY: ${intensityValue}/10 [${intensityLabel}]`);

    const sec01 = document.getElementById('sec-01');
    if (sec01) sec01.classList.add('pulse');

    const result = await apiRequest('/scan/start', 'POST', {
        target_url: targetUrl,
        spec_url: targetUrl,
        scan_name: scanName,
        fuzzing_intensity: intensityValue,
    });

    if (result.scan_id) {
        await typeLine(`SCAN_STARTED: ${result.scan_id}`);
        await typeLine("TRANSITIONING TO THE LAB...", true);
        localStorage.setItem('current_scan_id', result.scan_id);
        localStorage.setItem('current_intensity', intensityValue);

        setTimeout(() => { window.location.href = 'the-lab.html'; }, 1500);
    } else {
        await typeLine(`CRITICAL_FAILURE: ${result.error || 'UNKNOWN_ERROR'}`, true);
        playErrorSound();
        if (sec01) sec01.classList.remove('pulse');
        alert("Failed to start scan: " + (result.error || "Unknown error"));
    }
}

// ── The Lab ───────────────────────────────────────────────────────────────────
let previousEndpointCount = 0;

async function updateScanStatus() {
    const scanId = localStorage.getItem('current_scan_id');
    if (!scanId) return;

    const status = await apiRequest(`/scan/${scanId}`);
    if (status.error) return;

    if (status.status === 'running' && !processingOscillator) {
        startProcessingSound();
    }

    const progressEl = document.getElementById('progress_bar');
    const statusTextEl = document.getElementById('status_text');
    const endpointsListEl = document.getElementById('endpoints_list');
    const startTimeEl = document.getElementById('start_time_display');
    const elapsedTimeEl = document.getElementById('elapsed_time_display');
    const remainingTimeEl = document.getElementById('remaining_time_display');

    if (progressEl) progressEl.style.width = `${status.progress}%`;
    if (statusTextEl) statusTextEl.innerText = status.status.toUpperCase();

    if (status.start_time) {
        const startTime = new Date(status.start_time);
        if (startTimeEl) startTimeEl.innerText = startTime.toLocaleTimeString();

        const now = status.end_time ? new Date(status.end_time) : new Date();
        const elapsed = Math.max(0, Math.floor((now - startTime) / 1000));
        if (elapsedTimeEl) elapsedTimeEl.innerText = `${elapsed}s`;

        if (status.status === 'running' && status.progress > 5 && remainingTimeEl) {
            const remaining = Math.round(((100 - status.progress) / status.progress) * elapsed);
            remainingTimeEl.innerText = `~${remaining}s`;
        } else if (status.status === 'completed' && remainingTimeEl) {
            remainingTimeEl.innerText = 'FINISHED';
        }
    }

    if (endpointsListEl && status.endpoints) {
        if (status.endpoints.length > previousEndpointCount) {
            playDataBlip();
            previousEndpointCount = status.endpoints.length;
        }

        const fragment = document.createDocumentFragment();
        for (const e of status.endpoints) {
            const item = document.createElement('div');
            item.classList.add('endpoint-item');

            const methodSpan = document.createElement('span');
            methodSpan.classList.add('method', `method-${e.method}`);
            methodSpan.textContent = e.method;

            const pathSpan = document.createElement('span');
            pathSpan.classList.add('path');
            pathSpan.textContent = e.path;

            item.appendChild(methodSpan);
            item.appendChild(pathSpan);
            fragment.appendChild(item);
        }
        endpointsListEl.replaceChildren(fragment);
    }

    if (status.status === 'completed') {
        if (processingOscillator) stopProcessingSound();

        if (statusInterval) {
            clearInterval(statusInterval);
            statusInterval = null;
            playSuccessSound();
            document.getElementById('view_results_btn')?.classList.remove('hidden');
        }
    }
}

// ── War Room ──────────────────────────────────────────────────────────────────
// KEY FIX: Call /report (reads from DB with correct caused_failure values)
//          NOT /results (uses stale in-memory data built before rules.py fix)
async function loadResults() {
    const scanId = localStorage.getItem('current_scan_id');
    if (!scanId) return;

    const results = await apiRequest(`/scan/${scanId}/report`);

    // Scan still running — retry after 3s
    if (results.error) {
        if (results.error.includes('not completed') || results.error.includes('running')) {
            setTimeout(loadResults, 3000);
        } else {
            console.error("Failed to load results:", results.error);
        }
        return;
    }

    playSuccessSound();

    // ── Stats ──────────────────────────────────────────────────────────────
    // /report returns: statistics.total_tests, .total_failures, .endpoints_tested
    const stats = results.statistics || {};
    const totalTestsEl = document.getElementById('total_tests');
    const totalFailuresEl = document.getElementById('total_failures');
    const endpointsEl = document.getElementById('endpoints_count');

    if (totalTestsEl) totalTestsEl.innerText = stats.total_tests ?? 0;
    if (totalFailuresEl) totalFailuresEl.innerText = stats.total_failures ?? 0;
    if (endpointsEl) endpointsEl.innerText = stats.endpoints_tested ?? 0;

    // ── Failure Cards ──────────────────────────────────────────────────────
    // /report failures[] fields:
    //   endpoint, http_method, field_name, edge_case_type, edge_case_value,
    //   failure_type, status_code, response_time_ms
    const failuresEl = document.getElementById('failures_list');
    if (failuresEl) {
        const failures = results.failures || [];
        const fragment = document.createDocumentFragment();

        if (failures.length === 0) {
            const noFail = document.createElement('div');
            noFail.style.cssText = 'color:#888; font-size:0.9rem; padding:2rem; text-align:center;';
            noFail.textContent = '✅ NO CRITICAL FAILURES DETECTED — API IS RESILIENT';
            fragment.appendChild(noFail);
        } else {
            for (const f of failures) {
                const card = document.createElement('div');
                card.classList.add('glass-card', 'failure-card');

                // Header: method badge + failure type badge
                const header = document.createElement('div');
                header.style.cssText = 'display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;';

                const method = (f.http_method || 'GET').toUpperCase();
                const methodSpan = document.createElement('span');
                methodSpan.classList.add('method', `method-${method.toLowerCase()}`);
                methodSpan.textContent = method;

                const typeSpan = document.createElement('span');
                typeSpan.classList.add('status', 'status-failed');
                typeSpan.textContent = (f.failure_type || 'unknown').toUpperCase();

                header.appendChild(methodSpan);
                header.appendChild(typeSpan);
                card.appendChild(header);

                // Endpoint path
                const urlDiv = document.createElement('div');
                urlDiv.style.cssText = 'font-family:monospace; font-size:0.9rem; color:#fff; margin-bottom:1rem;';
                urlDiv.textContent = f.endpoint || '—';
                card.appendChild(urlDiv);

                // Status code + latency
                if (f.status_code || f.response_time_ms) {
                    const metaDiv = document.createElement('div');
                    metaDiv.style.cssText = 'font-size:0.8rem; color:#888; margin-bottom:0.5rem;';
                    metaDiv.textContent = [
                        f.status_code ? `HTTP ${f.status_code}` : null,
                        f.response_time_ms ? `${Math.round(f.response_time_ms)}ms` : null,
                    ].filter(Boolean).join('  •  ');
                    card.appendChild(metaDiv);
                }

                // Payload
                const payloadWrapper = document.createElement('div');
                payloadWrapper.style.cssText = 'background:rgba(0,0,0,0.5); padding:10px; border-radius:4px; font-size:0.8rem; border:1px solid var(--border);';

                const payloadLabel = document.createElement('div');
                payloadLabel.style.cssText = 'color:var(--text-muted); margin-bottom:5px;';
                payloadLabel.textContent = 'Payload:';

                const payloadCode = document.createElement('code');
                if (f.field_name && f.edge_case_value != null) {
                    payloadCode.textContent = `${f.field_name} = ${f.edge_case_value}`;
                } else if (f.edge_case_type) {
                    payloadCode.textContent = `[${f.edge_case_type}]`;
                } else {
                    payloadCode.textContent = '—';
                }

                payloadWrapper.appendChild(payloadLabel);
                payloadWrapper.appendChild(payloadCode);
                card.appendChild(payloadWrapper);

                fragment.appendChild(card);
            }
        }

        failuresEl.replaceChildren(fragment);

        if (failures.length > 0) {
            setTimeout(playErrorSound, 500);
        }
    }

    // ── Analysis Report ────────────────────────────────────────────────────
    // Build a text summary since /report doesn't have a pre-formatted string
    const reportEl = document.getElementById('formatted_report');
    if (reportEl) {
        const s = results.statistics || {};
        const fbt = results.failures_by_type || {};
        const ml = results.ml_insights;

        let report = `SCAN_ID:  ${results.scan_id || scanId}\n`;
        report += `NAME:     ${results.scan_name || '—'}\n`;
        report += `TARGET:   ${results.target_url || '—'}\n`;
        report += `STATUS:   ${(results.status || '').toUpperCase()}\n`;
        report += `DURATION: ${results.duration_seconds ?? '?'}s\n`;
        report += `\n── STATISTICS ──────────────────────\n`;
        report += `Total Tests:    ${s.total_tests ?? 0}\n`;
        report += `Total Failures: ${s.total_failures ?? 0}\n`;
        report += `Failure Rate:   ${s.failure_rate ?? 0}%\n`;
        report += `Endpoints:      ${s.endpoints_tested ?? 0}\n`;

        if (Object.keys(fbt).length > 0) {
            report += `\n── FAILURES BY TYPE ────────────────\n`;
            for (const [type, count] of Object.entries(fbt)) {
                report += `${type.padEnd(22)} ${count}\n`;
            }
        }

        if (ml) {
            report += `\n── ML INSIGHTS ─────────────────────\n`;
            report += `Avg Failure Probability: ${ml.avg_failure_probability}\n`;
            report += `High Risk Fields:        ${ml.high_risk_count}\n`;
            report += `Low Risk Fields:         ${ml.low_risk_count}\n`;
        }

        reportEl.innerText = report;
    }
}

let statusInterval;

function init() {
    const page = window.location.pathname.split('/').pop();

    const interactives = document.querySelectorAll('button, a, .btn-launch');
    interactives.forEach(el => {
        el.addEventListener('click', playClickSound);
        el.addEventListener('mouseenter', playHoverSound);
    });

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