// content.js - Runs in ISOLATED world
// Responsible for receiving data from hook.js (MAIN world) and sending it to the local API.

const API_BASE = "http://localhost:8787";

console.log("[Birdbrain] Content script initialized.");

// Extract tweet ID from current URL
function getTweetIdFromUrl() {
  const match = window.location.pathname.match(/\/status\/(\d+)/);
  return match ? match[1] : null;
}

// Listen for the custom event from the main world hook - Bookmarks
document.addEventListener('BirdbrainBookmarkData', async function(e) {
  console.log("[Birdbrain] 📨 Received bookmark event!");

  let data = e.detail;

  if (typeof data === 'string') {
      try {
          data = JSON.parse(data);
      } catch (err) {
          console.error("[Birdbrain] Failed to parse event data string:", err);
          return;
      }
  }

  if (!data) {
      console.warn("[Birdbrain] Received empty event data.");
      return;
  }

  // Basic validation to ensure it looks like a timeline response
  const instructions = data?.data?.bookmark_timeline_v2?.timeline?.instructions;
  if (!instructions) {
      console.log("[Birdbrain] Intercepted GraphQL, but not a bookmark timeline. Ignoring.");
      return;
  }

  console.log("[Birdbrain] 📥 Intercepted Bookmark Data. Sending to API...");

  try {
      const response = await fetch(`${API_BASE}/api/bookmarks/ingest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
      });

      if (response.ok) {
          const resJson = await response.json();
          console.log(`[Birdbrain] ✅ Success! Server processed ${resJson.processed_count} tweets.`);

          // Notify popup/background
          chrome.runtime.sendMessage({
              type: "SYNC_SUCCESS",
              count: resJson.processed_count
          }).catch(() => {});

          // Refresh incomplete list after new bookmarks
          chrome.runtime.sendMessage({ type: "REFRESH_INCOMPLETE" }).catch(() => {});

      } else {
          console.error(`[Birdbrain] ❌ Server Error: ${response.status} ${response.statusText}`);
          chrome.runtime.sendMessage({ type: "SYNC_ERROR", message: `Server error: ${response.status}` }).catch(() => {});
      }
  } catch (err) {
      console.error("[Birdbrain] ❌ Network Error. Is the CLI 'serve' command running?", err);
      chrome.runtime.sendMessage({
          type: "SYNC_ERROR",
          message: "Connection failed. Is 'uv run main.py serve' running?"
      }).catch(() => {});
  }
});

// Listen for TweetDetail events - for hydrating incomplete tweets
document.addEventListener('BirdbrainTweetDetail', async function(e) {
  console.log("[Birdbrain] 📨 Received tweet detail event!");

  let data = e.detail;

  if (typeof data === 'string') {
      try {
          data = JSON.parse(data);
      } catch (err) {
          console.error("[Birdbrain] Failed to parse tweet detail:", err);
          return;
      }
  }

  // Extract tweet ID from URL or response
  const tweetId = getTweetIdFromUrl();
  if (!tweetId) {
      console.log("[Birdbrain] Not on a tweet page, ignoring TweetDetail");
      return;
  }

  // Check if this tweet needs hydration
  chrome.runtime.sendMessage(
    { type: "CHECK_INCOMPLETE", tweetId },
    async (response) => {
      if (!response?.isIncomplete) {
        console.log(`[Birdbrain] Tweet ${tweetId} doesn't need hydration, skipping`);
        return;
      }

      console.log(`[Birdbrain] 🔄 Tweet ${tweetId} needs hydration. Sending to API...`);

      try {
        const apiResponse = await fetch(`${API_BASE}/api/tweets/${tweetId}/hydrate`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data)
        });

        if (apiResponse.ok) {
          const result = await apiResponse.json();
          console.log(`[Birdbrain] ✅ Hydrated tweet ${tweetId}:`, result);

          // Notify background to remove from incomplete list
          chrome.runtime.sendMessage({
            type: "HYDRATION_SUCCESS",
            tweetId
          }).catch(() => {});

          // Show toast notification
          showToast(`Tweet hydrated! ${result.is_truncated ? '' : '✓ Full text'} ${result.is_quote_missing ? '' : '✓ Quote'}`);
        } else {
          console.error(`[Birdbrain] ❌ Hydration failed: ${apiResponse.status}`);
        }
      } catch (err) {
        console.error("[Birdbrain] ❌ Hydration error:", err);
      }
    }
  );
});

// Show a toast notification on the page
function showToast(message) {
  const toast = document.createElement('div');
  toast.textContent = `🐦 Birdbrain: ${message}`;
  toast.style.cssText = `
    position: fixed;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    background: #1d9bf0;
    color: white;
    padding: 12px 24px;
    border-radius: 99px;
    z-index: 9999;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    font-size: 14px;
    font-weight: 500;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    animation: slideUp 0.3s ease-out, fadeOut 0.3s ease-in 2.7s forwards;
  `;

  // Add keyframes
  if (!document.getElementById('birdbrain-toast-styles')) {
    const style = document.createElement('style');
    style.id = 'birdbrain-toast-styles';
    style.textContent = `
      @keyframes slideUp {
        from { opacity: 0; transform: translate(-50%, 20px); }
        to { opacity: 1; transform: translate(-50%, 0); }
      }
      @keyframes fadeOut {
        from { opacity: 1; }
        to { opacity: 0; }
      }
    `;
    document.head.appendChild(style);
  }

  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}

// On page load, check if we're on a tweet that needs hydration
window.addEventListener('load', () => {
  const tweetId = getTweetIdFromUrl();
  if (tweetId) {
    chrome.runtime.sendMessage(
      { type: "CHECK_INCOMPLETE", tweetId },
      (response) => {
        if (response?.isIncomplete) {
          console.log(`[Birdbrain] 👀 Watching tweet ${tweetId} for hydration data...`);
          showToast("Watching for full tweet data...");
        }
      }
    );
  }
});
