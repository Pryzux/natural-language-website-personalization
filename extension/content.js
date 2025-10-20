/**
 * Content Script
 * Automatically reapplies cached transformations on page load and periodically
 */

(function() {
    'use strict';

    let reapplyInterval = null;

    /**
     * Action handlers for different transformation types
     */
    const actionHandlers = {
        color: (selector, params) => {
            document.querySelectorAll(selector).forEach(el => {
                Object.assign(el.style, params);
            });
        },
        text: (selector, params) => {
            document.querySelectorAll(selector).forEach(el => {
                if (params.replace !== undefined) {
                    el.textContent = params.replace;
                }
            });
        },
        visibility: (selector, params) => {
            document.querySelectorAll(selector).forEach(el => {
                Object.assign(el.style, params);
            });
        },
        style: (selector, params) => {
            document.querySelectorAll(selector).forEach(el => {
                Object.assign(el.style, params);
            });
        },
        layout: (selector, params) => {
            document.querySelectorAll(selector).forEach(el => {
                Object.assign(el.style, params);
            });
        }
    };

    /**
     * Apply transformations to the page
     */
    function applyTransformations(transformations) {
        if (!transformations || transformations.length === 0) {
            return;
        }

        transformations.forEach(t => {
            if (actionHandlers[t.action]) {
                try {
                    actionHandlers[t.action](t.selector, t.params);
                    console.log(`[AI Customizer] Applied ${t.action} to ${t.selector}`);
                } catch (error) {
                    console.error(`[AI Customizer] Failed to apply ${t.action} to ${t.selector}:`, error);
                }
            } else {
                console.warn(`[AI Customizer] Unknown action type: ${t.action}`);
            }
        });

        // Mark page as customized
        window.__aiCustomizerActive = true;
    }

    /**
     * Get the current domain
     */
    function getCurrentDomain() {
        try {
            return window.location.hostname;
        } catch (error) {
            console.error('[AI Customizer] Failed to get domain:', error);
            return null;
        }
    }

    /**
     * Load and apply cached transformations
     */
    function loadAndApplyCached() {
        const domain = getCurrentDomain();
        if (!domain) return;

        const key = `transform_${domain}`;

        chrome.storage.local.get([key], (result) => {
            if (result[key] && result[key].transformations) {
                console.log('[AI Customizer] Applying cached transformations for:', domain);
                applyTransformations(result[key].transformations);
            }
        });
    }

    /**
     * Start periodic reapplication
     */
    function startPeriodicReapplication() {
        // Clear any existing interval
        if (reapplyInterval) {
            clearInterval(reapplyInterval);
        }

        // Initial application
        loadAndApplyCached();

        // Reapply every 5 seconds to handle dynamic content
        reapplyInterval = setInterval(() => {
            loadAndApplyCached();
        }, 5000);

        console.log('[AI Customizer] Started periodic reapplication (every 5 seconds)');
    }

    /**
     * Stop periodic reapplication
     */
    function stopPeriodicReapplication() {
        if (reapplyInterval) {
            clearInterval(reapplyInterval);
            reapplyInterval = null;
            console.log('[AI Customizer] Stopped periodic reapplication');
        }
    }

    /**
     * Initialize on page load
     */
    function initialize() {
        const domain = getCurrentDomain();
        if (!domain) return;

        // Check if we have cached transformations for this domain
        const key = `transform_${domain}`;
        chrome.storage.local.get([key], (result) => {
            if (result[key] && result[key].transformations) {
                // We have transformations, start periodic reapplication
                startPeriodicReapplication();
            } else {
                console.log('[AI Customizer] No cached transformations for:', domain);
            }
        });
    }

    /**
     * Listen for messages from background script
     */
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
        if (message.action === 'applyTransformations') {
            // Apply transformations and start periodic reapplication
            applyTransformations(message.transformations);
            startPeriodicReapplication();
            sendResponse({ success: true });
        } else if (message.action === 'reapplyTransformation') {
            loadAndApplyCached();
            sendResponse({ success: true });
        } else if (message.action === 'stopReapplication') {
            stopPeriodicReapplication();
            sendResponse({ success: true });
        }
    });

    /**
     * Start when DOM is ready
     */
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        // DOM already loaded
        initialize();
    }

    console.log('[AI Customizer] Content script loaded');
})();
