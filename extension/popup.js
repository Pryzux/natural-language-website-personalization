/**
 * Popup UI Controller
 * Handles user interactions and communicates with background script
 */

const DEFAULT_API_URL = 'http://localhost:8000';

// DOM Elements
const promptInput = document.getElementById('prompt');
const applyBtn = document.getElementById('applyBtn');
const clearBtn = document.getElementById('clearBtn');
const sendPageDataBtn = document.getElementById('sendPageDataBtn');
const statusDiv = document.getElementById('status');
const lastTransformDiv = document.getElementById('lastTransform');
const apiUrlInput = document.getElementById('apiUrl');
const saveApiUrlBtn = document.getElementById('saveApiUrl');
const btnText = applyBtn.querySelector('.btn-text');
const loader = applyBtn.querySelector('.loader');

// Load saved API URL
chrome.storage.local.get(['apiUrl'], (result) => {
    if (result.apiUrl) {
        apiUrlInput.value = result.apiUrl;
    }
});

// Load last transformation info
async function loadLastTransformation() {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab) return;

    const domain = new URL(tab.url).hostname;
    chrome.storage.local.get([`transform_${domain}`], (result) => {
        const key = `transform_${domain}`;
        if (result[key]) {
            const transform = result[key];
            lastTransformDiv.innerHTML = `
                <div class="transform-details">
                    <p><strong>Summary:</strong> ${transform.summary || 'N/A'}</p>
                    <p><strong>Applied:</strong> ${new Date(transform.timestamp).toLocaleString()}</p>
                    <p><strong>Selectors:</strong> ${(transform.selectors || []).join(', ') || 'N/A'}</p>
                    <p><strong>Transformations:</strong> ${(transform.transformations || []).length} actions</p>
                </div>
            `;
        }
    });
}

loadLastTransformation();

// Show status message
function showStatus(message, type = 'info') {
    statusDiv.textContent = message;
    statusDiv.className = `status ${type}`;
    statusDiv.classList.remove('hidden');

    if (type === 'success' || type === 'info') {
        setTimeout(() => {
            statusDiv.classList.add('hidden');
        }, 5000);
    }
}

// Toggle loading state
function setLoading(isLoading) {
    applyBtn.disabled = isLoading;
    if (isLoading) {
        btnText.textContent = 'Processing...';
        loader.classList.remove('hidden');
    } else {
        btnText.textContent = 'Apply Changes';
        loader.classList.add('hidden');
    }
}

// Apply transformation
applyBtn.addEventListener('click', async () => {
    const prompt = promptInput.value.trim();

    if (!prompt) {
        showStatus('Please enter a description of your desired changes', 'error');
        return;
    }

    setLoading(true);
    showStatus('Sending request to backend...', 'info');

    try {
        // Get current tab
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

        if (!tab) {
            throw new Error('No active tab found');
        }

        // Send message to background script to handle the transformation
        chrome.runtime.sendMessage(
            {
                action: 'apply_transformation',
                data: {
                    prompt,
                    tabId: tab.id,
                    url: tab.url
                }
            },
            (response) => {
                if (chrome.runtime.lastError) {
                    showStatus(`Error: ${chrome.runtime.lastError.message}`, 'error');
                    setLoading(false);
                    return;
                }

                if (response.success) {
                    const transformCount = response.data?.transformations?.length || 0;
                    showStatus(`✅ Applied ${transformCount} transformation(s) successfully!`, 'success');
                    promptInput.value = '';
                    loadLastTransformation();
                } else {
                    showStatus(`❌ Error: ${response.error}`, 'error');
                }

                setLoading(false);
            }
        );

    } catch (error) {
        showStatus(`Error: ${error.message}`, 'error');
        setLoading(false);
    }
});

// Clear cache for current domain
clearBtn.addEventListener('click', async () => {
    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        if (!tab) return;

        const domain = new URL(tab.url).hostname;
        const key = `transform_${domain}`;

        chrome.storage.local.remove([key], () => {
            showStatus('Cache cleared for this domain', 'success');
            lastTransformDiv.innerHTML = '<p class="no-data">No transformations applied yet</p>';

            // Reload the page to remove transformations
            chrome.tabs.reload(tab.id);
        });

    } catch (error) {
        showStatus(`Error: ${error.message}`, 'error');
    }
});

// Save API URL
saveApiUrlBtn.addEventListener('click', () => {
    const url = apiUrlInput.value.trim();
    if (!url) {
        showStatus('Please enter a valid URL', 'error');
        return;
    }

    chrome.storage.local.set({ apiUrl: url }, () => {
        showStatus('API URL saved', 'success');
    });
});

// Enter key to submit
promptInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && e.ctrlKey) {
        applyBtn.click();
    }
});

// Send Page Data for development/debugging
sendPageDataBtn.addEventListener('click', async () => {
    const sendBtnText = sendPageDataBtn.querySelector('.btn-text');
    const sendLoader = sendPageDataBtn.querySelector('.loader');

    sendPageDataBtn.disabled = true;
    sendBtnText.textContent = '📤 Sending...';
    sendLoader.classList.remove('hidden');
    showStatus('Capturing page DOM data...', 'info');

    try {
        // Get current tab
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

        if (!tab) {
            throw new Error('No active tab found');
        }

        // Send message to background script to capture and send DOM data
        chrome.runtime.sendMessage(
            {
                action: 'send_page_data',
                data: {
                    tabId: tab.id,
                    url: tab.url
                }
            },
            (response) => {
                if (chrome.runtime.lastError) {
                    showStatus(`Error: ${chrome.runtime.lastError.message}`, 'error');
                    sendPageDataBtn.disabled = false;
                    sendBtnText.textContent = '📊 Send Page Data';
                    sendLoader.classList.add('hidden');
                    return;
                }

                if (response.success) {
                    showStatus(`✅ Page data saved to: ${response.path}`, 'success');
                } else {
                    showStatus(`Error: ${response.error}`, 'error');
                }

                sendPageDataBtn.disabled = false;
                sendBtnText.textContent = '📊 Send Page Data';
                sendLoader.classList.add('hidden');
            }
        );

    } catch (error) {
        showStatus(`Error: ${error.message}`, 'error');
        sendPageDataBtn.disabled = false;
        sendBtnText.textContent = '📊 Send Page Data';
        sendLoader.classList.add('hidden');
    }
});
