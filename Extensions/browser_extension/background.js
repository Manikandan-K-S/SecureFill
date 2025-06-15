const NATIVE_HOST_NAME = "com.my_ai_app.native_host";
let port;

/**
 * Connects to the native messaging host and sets up listeners.
 */
function connect() {
    console.log(`Attempting to connect to native host: ${NATIVE_HOST_NAME}`);
    port = chrome.runtime.connectNative(NATIVE_HOST_NAME);

    port.onMessage.addListener((message) => {
        console.log("Received message from host:", message);
        if (message.command === 'execute_action_plan' && message.plan) {
            console.log("✅ Received Action Plan. Executing now.", message.plan);
            executeActionPlan(message.plan);
        }
    });

    port.onDisconnect.addListener(() => {
        if (chrome.runtime.lastError) console.error(`Disconnected: ${chrome.runtime.lastError.message}`);
        port = null;
    });
}

/**
 * Executes the action plan by injecting the domFiller script into the active tab.
 * @param {Array<Object>} plan The list of actions from the native host.
 */
function executeActionPlan(plan) {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (tabs.length > 0) {
            chrome.scripting.executeScript({
                target: { tabId: tabs[0].id, allFrames: true },
                function: domFiller,
                args: [plan],
            });
        } else {
            console.error("No active tab found to execute the action plan.");
        }
    });
}

/**
 * THIS FUNCTION IS INJECTED INTO THE WEBPAGE TO MANIPULATE THE DOM.
 * It is robust and will not stop if one action fails.
 * @param {Array<Object>} plan The action plan.
 */
function domFiller(plan) {
    console.log("SecureFill DOM Filler activated with plan:", plan);

    plan.forEach(action => {
        try {
            const element = document.querySelector(action.selector);
            if (!element) {
                console.warn(`SecureFill: Could not find element with selector: "${action.selector}"`);
                return; // Use 'return' to skip this action and continue the loop
            }

            switch (action.action_type) {
                case "FILL_TEXT":
                    element.value = action.value;
                    break;

                case "SELECT_DROPDOWN":
                    // Check if the option exists before trying to select it
                    const optionExists = [...element.options].some(opt => opt.value === action.value);
                    if (optionExists) {
                        element.value = action.value;
                    } else {
                        console.warn(`SecureFill: Option "${action.value}" not found for selector "${action.selector}".`);
                        return; // Skip if AI hallucinated an option
                    }
                    break;

                case "CHECK_BOX":
                    element.checked = !!action.value; // Ensure value is a boolean
                    break;
                
                case "SELECT_RADIO":
                    // The selector should be specific enough to target one radio button
                    element.checked = true;
                    break;

                default:
                    console.warn(`SecureFill: Unknown action type: "${action.action_type}"`);
                    return; // Skip unknown actions
            }
            
            // Dispatch events after changing the value to ensure frameworks like React/Angular detect the change.
            element.dispatchEvent(new Event('input', { bubbles: true }));
            element.dispatchEvent(new Event('change', { bubbles: true }));
            console.log(`SecureFill: Successfully performed ${action.action_type} on "${action.selector}"`);

        } catch (error) {
            // This catch block ensures that if one action throws an unexpected error, the loop continues.
            console.error(`SecureFill: Error performing action on selector "${action.selector}":`, error);
        }
    });
    console.log("SecureFill: DOM Filler has completed its run.");
}


/**
 * Scans the current page for form elements and sends them to the native host.
 */
function triggerScan() {
    if (!port) {
        console.warn("Not connected to host, attempting to reconnect...");
        connect();
        return;
    }
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (tabs.length > 0) {
            chrome.scripting.executeScript({
                target: { tabId: tabs[0].id, allFrames: true },
                function: contextualHtmlScanner,
            }, (results) => {
                if (chrome.runtime.lastError) {
                    console.error("Scripting Error:", chrome.runtime.lastError.message);
                    return;
                }
                const allSnippets = new Set();
                if (results) {
                    results.forEach(res => res && res.result && res.result.forEach(snippet => allSnippets.add(snippet)));
                }
                console.log(`Scan complete, sending ${allSnippets.size} snippets to Python.`);
                port.postMessage({ action: "contextual_scan_result", data: Array.from(allSnippets) });
            });
        }
    });
}

function contextualHtmlScanner() {
    const selector = "input:not([type=hidden]), textarea, select";
    const elements = document.querySelectorAll(selector);
    const contextualSnippets = new Set();
    elements.forEach(el => {
        const container = el.closest("fieldset, form, div");
        if (container) {
            const innerInputs = container.querySelectorAll(selector);
            if (innerInputs.length > 2 && el.parentElement !== container) {
                contextualSnippets.add(el.parentElement.outerHTML);
            } else {
                contextualSnippets.add(container.outerHTML);
            }
        } else if (el.parentElement) {
            contextualSnippets.add(el.parentElement.outerHTML);
        }
    });
    return Array.from(contextualSnippets);
}

// --- Initial Setup and Triggers ---
connect();

// Listen for a command from the native host (e.g., triggered by a hotkey via main.py)
port.onMessage.addListener((message) => {
    if (message.command === 'scan_page') {
        triggerScan();
    }
});

// A simple way to trigger the scan for testing: click the extension icon.
chrome.action.onClicked.addListener((tab) => {
    console.log("Extension icon clicked, triggering scan.");
    triggerScan();
});
