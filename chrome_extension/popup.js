document.addEventListener('DOMContentLoaded', async () => {
    const statusDiv = document.getElementById('status');
    const syncBtn = document.getElementById('syncBtn');

    // Check if we are on the right tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (!tab.url.includes("twitter.com") && !tab.url.includes("x.com")) {
        statusDiv.textContent = "Please go to x.com/i/bookmarks first.";
        statusDiv.className = "status error";
        syncBtn.disabled = true;
        return;
    }

    if (!tab.url.includes("/bookmarks")) {
        statusDiv.textContent = "Navigate to Bookmarks page.";
        // We allow clicking sync maybe it redirects? No, keep it simple.
    }

    // Listen for messages from content script
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
        if (message.type === "SYNC_SUCCESS") {
            statusDiv.textContent = `Saved ${message.count} new tweets! Keep scrolling.`;
            statusDiv.className = "status success";
            
            // Flash button
            const originalText = syncBtn.textContent;
            syncBtn.textContent = "Syncing...";
            setTimeout(() => syncBtn.textContent = originalText, 1000);
        } else if (message.type === "SYNC_ERROR") {
            statusDiv.textContent = message.message;
            statusDiv.className = "status error";
        }
    });

    syncBtn.addEventListener('click', () => {
        // We can't really "trigger" the scroll from here easily without more permissions/scripting
        // But we can reload the page to ensure hooks are active if needed, or just instruct user.
        // For now, just update text.
        statusDiv.textContent = "Scroll down on the page to capture tweets!";
        statusDiv.className = "status";
        
        // Optional: Inject a small toast notification into the page context via scripting
        chrome.scripting.executeScript({
            target: { tabId: tab.id },
            func: () => {
                const toast = document.createElement('div');
                toast.textContent = "Birdbrain: Scroll down to sync bookmarks";
                toast.style.cssText = "position: fixed; top: 20px; left: 50%; transform: translateX(-50%); background: #1d9bf0; color: white; padding: 12px 24px; border-radius: 99px; z-index: 9999; font-family: sans-serif; font-weight: bold; box-shadow: 0 4px 12px rgba(0,0,0,0.15); animation: fadein 0.5s, fadeout 0.5s 4.5s forwards;";
                
                // Add keyframes
                const style = document.createElement('style');
                style.textContent = "@keyframes fadein {from{opacity:0;transform:translate(-50%,-20px);}to{opacity:1;transform:translate(-50%,0);}} @keyframes fadeout {from{opacity:1;}to{opacity:0;}}";
                document.head.appendChild(style);
                
                document.body.appendChild(toast);
                setTimeout(() => toast.remove(), 5000);
            }
        });
    });
});
