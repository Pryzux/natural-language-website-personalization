/**
 * Background Service Worker
 * Handles communication between popup and content script
 * Makes API calls to backend server for LLM-based transformations
 */

const DEFAULT_API_URL = 'http://localhost:8000';

/**
 * Capture page HTML and screenshot
 */
async function capturePageContext(tabId) {
    try {
        // Get HTML from content script
        const [htmlResult] = await chrome.scripting.executeScript({
            target: { tabId },
            func: () => {
                return {
                    html: document.documentElement.outerHTML,
                    url: window.location.href
                };
            }
        });

        // Capture screenshot
        const screenshotDataUrl = await chrome.tabs.captureVisibleTab(null, {
            format: 'png',
            quality: 80
        });

        return {
            html: htmlResult.result.html,
            url: htmlResult.result.url,
            screenshot: screenshotDataUrl
        };
    } catch (error) {
        console.error('[Background] Failed to capture page context:', error);
        throw error;
    }
}

/**
 * Call backend API to generate transformations
 */
async function generateTransformations(prompt, pageContext, apiUrl) {
    try {
        const response = await fetch(`${apiUrl}/generate_transformations`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                prompt: prompt,
                html: pageContext.html,
                screenshot: pageContext.screenshot,
                url: pageContext.url
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'API request failed');
        }

        return await response.json();
    } catch (error) {
        console.error('[Background] API call failed:', error);
        throw error;
    }
}

/**
 * Apply transformations to the page by sending to content script
 */
async function applyTransformations(tabId, transformations) {
    try {
        console.log('[Background] Sending transformations to content script');

        // Send transformations to content script
        await chrome.tabs.sendMessage(tabId, {
            action: 'applyTransformations',
            transformations: transformations
        });

        console.log('[Background] Transformations applied successfully');
        return true;
    } catch (error) {
        console.error('[Background] Failed to apply transformations:', error);
        throw error;
    }
}

/**
 * Save transformation to storage for auto-reapplication
 */
async function saveTransformation(url, transformationData) {
    try {
        const domain = new URL(url).hostname;
        const key = `transform_${domain}`;

        await chrome.storage.local.set({
            [key]: {
                transformations: transformationData.transformations,
                summary: transformationData.summary,
                selectors: transformationData.selectors,
                timestamp: Date.now(),
                url: url
            }
        });

        console.log(`[Background] Saved transformation for ${domain}`);
    } catch (error) {
        console.error('[Background] Failed to save transformation:', error);
    }
}

/**
 * Handle messages from popup
 */
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'apply_transformation') {
        (async () => {
            try {
                const { tabId, prompt } = message.data;

                // Get API URL from storage
                const { apiUrl } = await chrome.storage.local.get(['apiUrl']);
                const finalApiUrl = apiUrl || DEFAULT_API_URL;

                console.log('[Background] Capturing page context...');
                const pageContext = await capturePageContext(tabId);

                console.log('[Background] Calling LLM API...');
                const transformationData = await generateTransformations(
                    prompt,
                    pageContext,
                    finalApiUrl
                );

                console.log('[Background] Applying transformations...');
                await applyTransformations(tabId, transformationData.transformations);

                console.log('[Background] Saving transformation...');
                await saveTransformation(pageContext.url, {
                    ...transformationData,
                    transformations: transformationData.transformations
                });

                sendResponse({
                    success: true,
                    data: transformationData
                });
            } catch (error) {
                console.error('[Background] Error:', error);
                sendResponse({
                    success: false,
                    error: error.message
                });
            }
        })();

        return true; // Keep channel open for async response
    }
});

/**
 * Handle extension installation
 */
chrome.runtime.onInstalled.addListener(() => {
    console.log('AI Website Customizer installed');
});
