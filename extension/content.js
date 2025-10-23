/**
 * Content Script - jQuery Command Chain Executor
 * Executes safe, declarative jQuery transformations
 */

(function() {
    'use strict';

    let reapplyInterval = null;
    let currentTransformations = null;

    /**
     * Execute a single transformation (selector + command chain)
     */
    function executeTransformation(transformation) {
        const { selector, commands } = transformation;

        try {
            console.log(`[AI Customizer] Executing: ${selector}`);

            // Start with jQuery selection
            let $elements = $(selector);

            if ($elements.length === 0) {
                // Don't spam console if no elements found during periodic reapplication
                return;
            }

            console.log(`[AI Customizer] Found ${$elements.length} element(s) for: ${selector}`);

            // Execute command chain
            commands.forEach((cmd, idx) => {
                const { method, args = [] } = cmd;

                if (typeof $elements[method] !== 'function') {
                    console.error(`[AI Customizer] Unknown jQuery method: ${method}`);
                    return;
                }

                try {
                    // Execute method and update $elements for chaining
                    const result = $elements[method](...args);

                    // Update $elements if method returns jQuery object (for chaining)
                    if (result && result.jquery) {
                        $elements = result;
                    }

                    console.log(`[AI Customizer]   [${idx + 1}/${commands.length}] ${method}(${JSON.stringify(args).substring(0, 50)}...)`);
                } catch (error) {
                    console.error(`[AI Customizer] Error executing ${method}:`, error);
                }
            });

        } catch (error) {
            console.error(`[AI Customizer] Error in transformation with selector "${selector}":`, error);
        }
    }

    /**
     * Apply all transformations
     */
    function applyTransformations(transformations) {
        console.log('[AI Customizer] Applying transformations:', transformations);

        if (!transformations || transformations.length === 0) {
            console.warn('[AI Customizer] No transformations provided');
            return;
        }

        currentTransformations = transformations;

        transformations.forEach((transformation, idx) => {
            console.log(`[AI Customizer] === Transformation ${idx + 1}/${transformations.length} ===`);
            executeTransformation(transformation);
        });

        window.__aiCustomizerActive = true;
        console.log('[AI Customizer] All transformations complete');
    }

    /**
     * Get current domain
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
                console.log('[AI Customizer] Applying cached transformations');
                applyTransformations(result[key].transformations);
            }
        });
    }

    /**
     * Start periodic reapplication
     */
    function startPeriodicReapplication() {
        if (reapplyInterval) {
            clearInterval(reapplyInterval);
        }

        loadAndApplyCached();

        reapplyInterval = setInterval(() => {
            if (currentTransformations) {
                applyTransformations(currentTransformations);
            }
        }, 2000);

        console.log('[AI Customizer] Started periodic reapplication (every 2s)');
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

        // Check if jQuery is available
        if (typeof $ === 'undefined') {
            console.error('[AI Customizer] jQuery not loaded! Transformations will not work.');
            return;
        }

        console.log('[AI Customizer] jQuery loaded successfully, version:', $.fn.jquery);

        const key = `transform_${domain}`;
        chrome.storage.local.get([key], (result) => {
            if (result[key] && result[key].transformations) {
                startPeriodicReapplication();
            } else {
                console.log('[AI Customizer] No cached transformations for:', domain);
            }
        });
    }

    /**
     * Listen for messages
     */
    chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
        console.log('[AI Customizer] Message received:', message.action);

        if (message.action === 'ping') {
            console.log('[AI Customizer] Ping received');
            sendResponse({ success: true });
        } else if (message.action === 'applyTransformations') {
            console.log('[AI Customizer] Applying transformations');
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

        return true; // Keep channel open for async response
    });

    /**
     * Start when DOM is ready
     */
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        initialize();
    }

    console.log('[AI Customizer] Content script loaded');
})();
