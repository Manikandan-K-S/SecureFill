// background.js - Final version that finds the closest meaningful container for context.

const NATIVE_HOST_NAME = "com.my_ai_app.native_host";
let port;

function connect() {
  console.log(`Attempting to connect to native host: ${NATIVE_HOST_NAME}`);
  port = chrome.runtime.connectNative(NATIVE_HOST_NAME);

  port.onMessage.addListener((message) => {
    // This is where we will receive the final action plan from Python
    console.log("Received message from host:", message);
  });

  port.onDisconnect.addListener(() => {
    if (chrome.runtime.lastError) console.error(`Disconnected: ${chrome.runtime.lastError.message}`);
    port = null;
  });
}

function triggerScan() {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs.length === 0) return;

    chrome.scripting.executeScript(
      {
        target: { tabId: tabs[0].id, allFrames: true },
        function: contextualHtmlScanner,
      },
      (results) => {
        let allSnippets = new Set(); // Use a Set to automatically handle duplicate containers
        if (results) {
          results.forEach((res) => {
            if (res.result) {
              res.result.forEach((snippet) => allSnippets.add(snippet));
            }
          });
        }
        console.log("Scan complete, sending contextual snippets to Python:", Array.from(allSnippets));
        port.postMessage({ action: "contextual_scan_result", data: Array.from(allSnippets) });
      }
    );
  });
}

// THE ULTIMATE SCANNER FUNCTION
function contextualHtmlScanner() {
  // 1. Find all the interactive elements themselves.
  const selector = "input:not([type=hidden]), textarea, select";
  const elements = document.querySelectorAll(selector);

  const contextualSnippets = [];

  elements.forEach((el) => {
    // 2. For each element, find its closest ancestor that is a meaningful container.
    // We include custom elements that start with 'lyte-' in the search.
    const container = el.closest("fieldset, lyte-input, lyte-textarea, lyte-select,lyte-checkbox, lyte-radio");

    // 3. If we found a container, add its full HTML to our list.
    if (container) {
      contextualSnippets.push(container.outerHTML);
    } else {
      // As a fallback, just use the element's parent if no better container is found
      if (el.parentElement) {
        contextualSnippets.push(el.parentElement.outerHTML);
      }
    }
  });

  return contextualSnippets;
}

// Main connection and trigger logic
connect();
port.onMessage.addListener((message) => {
  if (message.command === "scan_page") {
    triggerScan();
  }
});
