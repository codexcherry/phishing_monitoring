document.addEventListener('DOMContentLoaded', () => {
    const batchSizeInput = document.getElementById('batch-size');
    const batchSizeVal = document.getElementById('batch-size-val');
    const driftTypeSelect = document.getElementById('drift-type');
    const processBtn = document.getElementById('process-btn');
    const logsContainer = document.getElementById('activity-log');
    const statusBadge = document.getElementById('system-status');
    const refSizeSpan = document.getElementById('ref-size');

    // Update slider value display
    batchSizeInput.addEventListener('input', (e) => {
        batchSizeVal.textContent = e.target.value;
    });

    // Initial stats load
    fetchStats();

    // Process Batch Action
    processBtn.addEventListener('click', async () => {
        const batchSize = parseInt(batchSizeInput.value);
        const driftType = driftTypeSelect.value;

        setLoading(true);
        addLog('Processing batch...', 'info');

        try {
            const response = await fetch('/api/process_batch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ batch_size: batchSize, drift_type: driftType })
            });

            const data = await response.json();

            if (data.error) {
                addLog(`Error: ${data.error}`, 'error');
            } else {
                updateDashboard(data);
            }
        } catch (err) {
            addLog(`Network Error: ${err.message}`, 'error');
        } finally {
            setLoading(false);
            fetchStats(); // Refresh stats (e.g. ref data size might change)
        }
    });

    async function fetchStats() {
        try {
            const res = await fetch('/api/stats');
            const stats = await res.json();
            refSizeSpan.textContent = stats.reference_data_size;
        } catch (e) {
            console.error("Failed to fetch stats", e);
        }
    }

    function updateDashboard(data) {
        // Update Status
        if (data.drift_detected) {
            statusBadge.className = 'status-badge danger';
            statusBadge.innerHTML = '<span class="dot"></span> Drift Detected';
            addLog('🚨 Drift Detected!', 'error');

            // Show drift details
            for (const [feature, res] of Object.entries(data.drift_report)) {
                if (res.drift_detected) {
                    addLog(`  - ${feature}: ${res.test} (p=${res.p_value.toFixed(4)})`, 'error');
                }
            }

            if (data.retrained) {
                addLog('🔄 Model Retrained Automatically', 'success');
            }
        } else {
            statusBadge.className = 'status-badge';
            statusBadge.innerHTML = '<span class="dot"></span> System Healthy';
            addLog('✅ Batch processed. No drift.', 'success');
        }

        // Update Charts
        renderCharts(data.batch_data, data.reference_data_sample);
        renderDriftChart(data.drift_report);
    }

    function renderDriftChart(driftReport) {
        const features = Object.keys(driftReport);
        const pValues = features.map(f => driftReport[f].p_value);
        const colors = pValues.map(p => p < 0.05 ? '#ef4444' : '#10b981'); // Red if significant drift (p < 0.05)

        const trace = {
            x: features,
            y: pValues,
            type: 'bar',
            marker: { color: colors },
            text: pValues.map(p => p.toFixed(4)),
            textposition: 'auto'
        };

        const layout = {
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: { color: '#94a3b8' },
            margin: { t: 10, b: 40, l: 40, r: 10 },
            xaxis: { title: 'Features', gridcolor: '#334155' },
            yaxis: { title: 'P-Value (KS/Chi2 Test)', gridcolor: '#334155', range: [0, 1] },
            shapes: [{ // Threshold line
                type: 'line',
                x0: -0.5,
                x1: features.length - 0.5,
                y0: 0.05,
                y1: 0.05,
                line: { color: '#f59e0b', width: 2, dash: 'dash' }
            }],
            annotations: [{
                x: features.length - 1,
                y: 0.1,
                xref: 'x',
                yref: 'y',
                text: 'Threshold (0.05)',
                showarrow: false,
                font: { color: '#f59e0b' }
            }]
        };

        Plotly.newPlot('drift-pvalue-chart', [trace], layout);
    }

    function renderCharts(batchData, refData) {
        const layout = {
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: { color: '#94a3b8' },
            margin: { t: 10, b: 30, l: 30, r: 10 },
            showlegend: true,
            legend: { x: 0.7, y: 1 },
            xaxis: { gridcolor: '#334155' },
            yaxis: { gridcolor: '#334155' }
        };

        // URL Length Chart
        const trace1 = {
            x: refData.map(d => d.url_length),
            type: 'histogram',
            name: 'Reference',
            opacity: 0.6,
            marker: { color: '#3b82f6' }
        };
        const trace2 = {
            x: batchData.map(d => d.url_length),
            type: 'histogram',
            name: 'Batch',
            opacity: 0.6,
            marker: { color: '#ef4444' }
        };
        Plotly.newPlot('url-len-chart', [trace1, trace2], { ...layout, barmode: 'overlay' });

        // Special Chars Chart
        const trace3 = {
            x: refData.map(d => d.num_special_chars),
            type: 'histogram',
            name: 'Reference',
            opacity: 0.6,
            marker: { color: '#3b82f6' }
        };
        const trace4 = {
            x: batchData.map(d => d.num_special_chars),
            type: 'histogram',
            name: 'Batch',
            opacity: 0.6,
            marker: { color: '#ef4444' }
        };
        Plotly.newPlot('special-char-chart', [trace3, trace4], { ...layout, barmode: 'overlay' });
    }

    function addLog(msg, type = 'info') {
        const entry = document.createElement('div');
        entry.className = `log-entry ${type}`;
        const time = new Date().toLocaleTimeString();
        entry.innerHTML = `<span class="time">${time}</span><span class="msg">${msg}</span>`;
        logsContainer.insertBefore(entry, logsContainer.firstChild);
    }

    function setLoading(isLoading) {
        processBtn.disabled = isLoading;
        processBtn.textContent = isLoading ? 'Processing...' : 'Process Next Batch';
        processBtn.style.opacity = isLoading ? '0.7' : '1';
    }
});
