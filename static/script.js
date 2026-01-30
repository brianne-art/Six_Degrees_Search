document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('search-form');
    const startInput = document.getElementById('start-article');
    const endInput = document.getElementById('end-article');
    const submitBtn = document.getElementById('submit-btn');
    const loading = document.getElementById('loading');
    const error = document.getElementById('error');
    const results = document.getElementById('results');
    const pathLength = document.getElementById('path-length');
    const pathList = document.getElementById('path-list');

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        const start = startInput.value.trim();
        const end = endInput.value.trim();

        // Client-side validation
        if (!start || !end) {
            showError('Please enter both start and end articles.');
            return;
        }

        // Clear previous results and show loading
        hideError();
        hideResults();
        showLoading();
        setFormDisabled(true);

        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 300000); // 5 minute timeout

            const response = await fetch('/find-path', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ start, end }),
                signal: controller.signal
            });

            clearTimeout(timeoutId);
            const data = await response.json();

            if (data.success) {
                showResults(data.path, data.length);
            } else {
                showError(data.error);
            }
        } catch (err) {
            if (err.name === 'AbortError') {
                showError('Search timed out. Try articles that are more closely related.');
            } else {
                showError('Connection error: ' + err.message);
            }
        } finally {
            hideLoading();
            setFormDisabled(false);
        }
    });

    function showLoading() {
        loading.classList.remove('hidden');
    }

    function hideLoading() {
        loading.classList.add('hidden');
    }

    function showError(message) {
        error.textContent = message;
        error.classList.remove('hidden');
    }

    function hideError() {
        error.classList.add('hidden');
    }

    function showResults(path, length) {
        pathLength.textContent = `Found path with ${length} article${length === 1 ? '' : 's'} (${length - 1} link${length - 1 === 1 ? '' : 's'})`;

        pathList.innerHTML = '';
        path.forEach(function(article) {
            const li = document.createElement('li');
            const a = document.createElement('a');
            a.href = 'https://en.wikipedia.org/wiki/' + encodeURIComponent(article);
            a.target = '_blank';
            a.rel = 'noopener noreferrer';
            a.textContent = article.replace(/_/g, ' ');
            li.appendChild(a);
            pathList.appendChild(li);
        });

        results.classList.remove('hidden');
    }

    function hideResults() {
        results.classList.add('hidden');
    }

    function setFormDisabled(disabled) {
        startInput.disabled = disabled;
        endInput.disabled = disabled;
        submitBtn.disabled = disabled;
    }
});
