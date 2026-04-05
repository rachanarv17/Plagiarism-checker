document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('file');
    const dropArea = document.getElementById('dropArea');
    const fileMsg = document.getElementById('fileMsg');
    const uploadForm = document.getElementById('uploadForm');
    const uploadSection = document.getElementById('uploadSection');
    const loadingState = document.getElementById('loadingState');
    const resultsSection = document.getElementById('resultsSection');
    const scanBtn = document.getElementById('scanBtn');

    if (fileInput && dropArea) {
        // Drag and drop functionality
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        ['dragenter', 'dragover'].forEach(eventName => {
            dropArea.addEventListener(eventName, highlight, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, unhighlight, false);
        });

        function highlight(e) {
            dropArea.classList.add('drag-over');
        }

        function unhighlight(e) {
            dropArea.classList.remove('drag-over');
        }

        dropArea.addEventListener('drop', handleDrop, false);

        function handleDrop(e) {
            let dt = e.dataTransfer;
            let files = dt.files;
            fileInput.files = files;
            updateFileMsg();
        }

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

    if (uploadForm) {
        uploadForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            if (fileInput.files.length === 0) {
                alert('Please select a file first.');
                return;
            }

            const formData = new FormData();
            formData.append('file', fileInput.files[0]);

            // Show loading state
            scanBtn.disabled = true;
            uploadSection.querySelector('.glass-panel').style.display = 'none';
            loadingState.style.display = 'block';

            try {
                const response = await fetch('/api/scan', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }

                const data = await response.json();

                if (data.error) {
                    throw new Error(data.error);
                }

                displayResults(data);

            } catch (error) {
                console.error('Error:', error);
                alert('An error occurred during scanning. Please try again.');
                uploadSection.querySelector('.glass-panel').style.display = 'block';
                loadingState.style.display = 'none';
                scanBtn.disabled = false;
            }
        });
    }

    function displayResults(data) {
        // Hide loading, show results
        loadingState.style.display = 'none';
        uploadSection.style.display = 'none';
        resultsSection.style.display = 'block';
        const stickyAction = document.getElementById('stickyAction');
        if (stickyAction) stickyAction.style.display = 'block';

        const score = data.similarity;
        const scoreText = document.getElementById('scoreText');
        const scorePath = document.getElementById('scorePath');
        const scoreMessage = document.getElementById('scoreMessage');
        const phrasesList = document.getElementById('phrasesList');
        const urlsList = document.getElementById('urlsList');

        // Animate score text
        let count = 0;
        const target = parseFloat(score);
        const duration = 1000;
        const increment = target / (duration / 16); // 60fps

        const timer = setInterval(() => {
            count += increment;
            if (count >= target) {
                clearInterval(timer);
                count = target;
            }
            scoreText.textContent = count.toFixed(1) + '%';
        }, 16);

        // Update stroke dasharray for the circle
        scorePath.style.strokeDasharray = `${score}, 100`;

        // Update color and message based on score
        if (score < 15) {
            scorePath.style.stroke = 'var(--success-color)';
            scoreText.style.fill = 'var(--success-color)';
            scoreMessage.textContent = 'Great! Your document appears to be original.';
        } else if (score < 40) {
            scorePath.style.stroke = 'var(--warning-color)';
            scoreText.style.fill = 'var(--warning-color)';
            scoreMessage.textContent = 'Some similarities found. Review flagged sections.';
        } else {
            scorePath.style.stroke = 'var(--danger-color)';
            scoreText.style.fill = 'var(--danger-color)';
            scoreMessage.textContent = 'High similarity detected! Significant matching found.';
        }

        // Display phrases
        phrasesList.innerHTML = '';
        if (data.matched_phrases && data.matched_phrases.length > 0) {
            data.matched_phrases.forEach((item, index) => {
                const li = document.createElement('li');
                li.textContent = item.phrase;
                li.classList.add('animate-reveal');
                li.style.setProperty('--delay', `${0.1 * index}s`);
                phrasesList.appendChild(li);
            });
        } else {
            phrasesList.innerHTML = '<li class="animate-reveal">No significant matching phrases found.</li>';
        }

        // Display URLs
        urlsList.innerHTML = '';
        if (data.source_urls && data.source_urls.length > 0) {
            data.source_urls.forEach((url, index) => {
                const li = document.createElement('li');
                const a = document.createElement('a');
                a.href = url;
                a.target = '_blank';
                a.textContent = url;
                li.appendChild(a);
                li.classList.add('animate-reveal');
                li.style.setProperty('--delay', `${0.1 * index}s`);
                urlsList.appendChild(li);
            });
        } else {
            urlsList.innerHTML = '<li class="animate-reveal">No source links found.</li>';
        }
    }
});
