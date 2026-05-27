// Content script — provides selected text to popup
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action === "getSelection") {
    sendResponse({text: window.getSelection().toString()});
  }
});
