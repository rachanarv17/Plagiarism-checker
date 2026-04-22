document.addEventListener('DOMContentLoaded', () => {
    // UI Elements
    const fileInput = document.getElementById('file');
    const dropArea = document.getElementById('dropArea');
    const fileMsg = document.getElementById('fileMsg');
    const scanBtn = document.getElementById('scanBtn');
    const loadingState = document.getElementById('loadingState');
    const uploadSection = document.getElementById('uploadSection');
    const resultsSection = document.getElementById('resultsSection');
    const uploadCard = document.querySelector('.upload-card');

    // Shared state for navigation-triggered fetches
    window.appState = {
        fetchHistory: async function() {
            const historyList = document.getElementById('historyList');
            if (!historyList) return;
            try {
                const response = await fetch('/api/history');
                const data = await response.json();
                if (!Array.isArray(data) || data.length === 0) {
                    historyList.innerHTML = '<div class="empty-state"><p class="text-muted">No scan history found.</p></div>';
                    return;
                }
                historyList.innerHTML = `
                    <table class="history-table">
                        <thead><tr><th>File Name</th><th>Similarity</th><th>Date</th></tr></thead>
                        <tbody>
                            ${data.map(item => `
                                <tr>
                                    <td>${item.filename}</td>
                                    <td class="${item.similarity > 40 ? 'text-danger' : 'text-success'}">${item.similarity}%</td>
                                    <td>${item.timestamp}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>`;
            } catch (error) { console.error("History Error:", error); }
        },
        fetchAnalytics: async function() {
            try {
                const response = await fetch('/api/analytics');
                const data = await response.json();
                if (document.getElementById('totalScans')) document.getElementById('totalScans').textContent = data.total_scans || 0;
                if (document.getElementById('avgSimilarity')) document.getElementById('avgSimilarity').textContent = (data.avg_similarity || 0) + '%';
                if (document.getElementById('highRiskScans')) document.getElementById('highRiskScans').textContent = data.high_risk_scans || 0;
            } catch (error) { console.error("Analytics Error:", error); }
        }
    };

    // File Upload Handlers
    if (fileInput && dropArea) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(e => {
            dropArea.addEventListener(e, (evt) => { evt.preventDefault(); evt.stopPropagation(); }, false);
        });

        ['dragenter', 'dragover'].forEach(e => dropArea.addEventListener(e, () => dropArea.classList.add('drag-over'), false));
        ['dragleave', 'drop'].forEach(e => dropArea.addEventListener(e, () => dropArea.classList.remove('drag-over'), false));

        dropArea.addEventListener('drop', (e) => {
            fileInput.files = e.dataTransfer.files;
            updateFileMsg();
        }, false);

        fileInput.addEventListener('change', updateFileMsg);

        function updateFileMsg() {
            if (fileInput.files.length > 0) {
                fileMsg.textContent = fileInput.files[0].name;
                fileMsg.style.color = 'var(--text-color)';
            } else {
                fileMsg.textContent = 'Drag & Drop file here or Click to Browse';
                fileMsg.style.color = 'var(--text-muted)';
            }
        }
    }

    // Scan Logic
    if (scanBtn) {
        scanBtn.addEventListener('click', async () => {
            if (!fileInput.files || fileInput.files.length === 0) {
                alert('Please select a file first.');
                return;
            }

            const formData = new FormData();
            formData.append('file', fileInput.files[0]);

            scanBtn.disabled = true;
            scanBtn.textContent = 'Processing...';
            if (uploadCard) uploadCard.style.opacity = '0.5';
            if (loadingState) loadingState.style.display = 'block';

            try {
                const response = await fetch('/api/scan', { method: 'POST', body: formData });
                const data = await response.json();
                if (data.error) throw new Error(data.error);
                displayResults(data);
            } catch (error) {
                alert('Scanning Error: ' + error.message);
                scanBtn.disabled = false;
                scanBtn.textContent = 'Scan Document Now';
                if (uploadCard) uploadCard.style.opacity = '1';
                if (loadingState) loadingState.style.display = 'none';
            }
        });
    }

    function displayResults(data) {
        if (loadingState) loadingState.style.display = 'none';
        if (uploadSection) uploadSection.style.display = 'none';
        if (resultsSection) resultsSection.style.display = 'block';
        if (document.getElementById('stickyAction')) document.getElementById('stickyAction').style.display = 'block';

        const score = data.similarity || 0;
        if (document.getElementById('scoreText')) document.getElementById('scoreText').textContent = score + '%';
        if (document.getElementById('scorePath')) document.getElementById('scorePath').style.strokeDasharray = `${score}, 100`;
        
        const phrasesList = document.getElementById('phrasesList');
        if (phrasesList) {
            phrasesList.innerHTML = (data.matched_phrases || []).map(p => `<li>${p.phrase}</li>`).join('') || '<li>No matches found.</li>';
        }

        const urlsList = document.getElementById('urlsList');
        if (urlsList) {
            urlsList.innerHTML = (data.source_urls || []).map(u => `<li><a href="${u}" target="_blank">${u}</a></li>`).join('') || '<li>No sources found.</li>';
        }
    }

    // Profile Update Logic
    const updateProfileBtn = document.getElementById('updateProfileBtn');
    if (updateProfileBtn) {
        updateProfileBtn.addEventListener('click', async () => {
            const fullName = document.getElementById('fullName').value;
            const email = document.getElementById('email').value;
            const newPassword = document.getElementById('newPassword').value;
            const confirmPassword = document.getElementById('confirmPassword').value;
            const msgDiv = document.getElementById('settingsMsg');

            if (newPassword && newPassword !== confirmPassword) {
                msgDiv.textContent = "Passwords do not match.";
                msgDiv.className = "error";
                msgDiv.style.display = "block";
                return;
            }

            try {
                const response = await fetch('/api/update-profile', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ fullName, email, newPassword })
                });
                const data = await response.json();
                msgDiv.textContent = data.message || data.error;
                msgDiv.className = response.ok ? "success" : "error";
                msgDiv.style.display = "block";
                if (response.ok) {
                    document.getElementById('newPassword').value = '';
                    document.getElementById('confirmPassword').value = '';
                }
            } catch (error) {
                msgDiv.textContent = "An error occurred.";
                msgDiv.className = "error";
                msgDiv.style.display = "block";
            }
        });
    }
});
