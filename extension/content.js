/**
 * Content Script - jQuery Command Chain Executor
 * Executes safe, declarative jQuery transformations
 */

(function() {
    'use strict';

    let reapplyInterval = null;
    let currentTransformations = null;

    /**
     * Normalize selector string:
     * - Remove accidental wrapping quotes
     * - Unescape double-encoded JSON strings
     */
    function normalizeSelector(selector) {
        if (!selector || typeof selector !== 'string') return selector;
        // Unescape escaped quotes like \" or \'
        let s = selector.replace(/^["']|["']$/g, '');
        s = s.replace(/\\"/g, '"').replace(/\\'/g, "'");
        return s.trim();
    }

    /**
     * Safe jQuery selector executor
     */
    function safeSelect(selector) {
        try {
            return $(selector);
        } catch (err) {
            console.error(`[AI Customizer] Invalid jQuery selector: ${selector}`, err);
            return $(); // empty jQuery set
        }
    }

    /**
     * Execute a single transformation (selector + command chain)
     */
    function executeTransformation(transformation) {
        let { selector, commands } = transformation;
        selector = normalizeSelector(selector);

        try {

            // Attempt jQuery selection safely
            let $elements = safeSelect(selector);

            // If not found, fallback for :contains()
            if ($elements.length === 0 && selector.includes(":contains(")) {
                const match = selector.match(/:contains\(['"](.+?)['"]\)/);
                const text = match ? match[1] : null;
                if (text) {
                    $elements = $('*').filter(function() {
                        return $(this).text().includes(text);
                    });
                }
            }

            if ($elements.length === 0) {
                return; // Skip silently if nothing found
            }

     

            // Execute command chain
            commands.forEach((cmd, idx) => {
                const { method, args = [] } = cmd;

                if (typeof $elements[method] !== 'function') {
                    return;
                }

                try {
                    const result = $elements[method](...args);
                    if (result && result.jquery) {
                        $elements = result; // Chain if applicable
                    }
                } catch (error) {
                   
                }
            });

        } catch (error) {
       
        }
    }

    /**
     * Apply all transformations
     */
    function applyTransformations(transformations) {

        if (!transformations || transformations.length === 0) {
            return;
        }

        currentTransformations = transformations;

        transformations.forEach((transformation, idx) => {
            console.log(`[AI Customizer] === Transformation ${idx + 1}/${transformations.length} ===`);
            executeTransformation(transformation);
        });

        window.__aiCustomizerActive = true;
      
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
        if (reapplyInterval) clearInterval(reapplyInterval);

        loadAndApplyCached();

        reapplyInterval = setInterval(() => {
            if (currentTransformations) {
                applyTransformations(currentTransformations);
            }
        }, 500);

     
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
            sendResponse({ success: true });
        } else if (message.action === 'applyTransformations') {
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

