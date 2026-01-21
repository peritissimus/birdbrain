// background.js - Manages state and syncs incomplete tweets list
const API_BASE = "http://localhost:8787";

// Fetch incomplete tweets on startup and periodically
async function syncIncompleteTweets() {
  try {
    const response = await fetch(`${API_BASE}/api/tweets/incomplete`);
    if (response.ok) {
      const data = await response.json();
      // Store as a Set of rest_ids for quick lookup
      const incompleteIds = {};
      for (const tweet of data.tweets) {
        incompleteIds[tweet.rest_id] = {
          author_handle: tweet.author_handle,
          is_truncated: tweet.is_truncated,
          is_quote_missing: tweet.is_quote_missing,
          quoted_status_id: tweet.quoted_status_id,
        };
      }
      await chrome.storage.local.set({ incompleteIds });
      console.log(`[Birdbrain] Synced ${data.count} incomplete tweets to watch for`);
    }
  } catch (err) {
    console.log("[Birdbrain] Could not sync incomplete tweets (server may be offline)");
  }
}

// Run on install
chrome.runtime.onInstalled.addListener(() => {
  console.log("Birdbrain Sync installed.");
  syncIncompleteTweets();
});

// Run on startup
chrome.runtime.onStartup.addListener(() => {
  syncIncompleteTweets();
});

// Sync every 5 minutes
setInterval(syncIncompleteTweets, 5 * 60 * 1000);

// Listen for messages from content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "CHECK_INCOMPLETE") {
    // Check if a tweet ID is in our incomplete list
    chrome.storage.local.get("incompleteIds", (result) => {
      const incompleteIds = result.incompleteIds || {};
      sendResponse({
        isIncomplete: !!incompleteIds[message.tweetId],
        data: incompleteIds[message.tweetId]
      });
    });
    return true; // Keep channel open for async response
  }

  if (message.type === "HYDRATION_SUCCESS") {
    // Remove from incomplete list after successful hydration
    chrome.storage.local.get("incompleteIds", (result) => {
      const incompleteIds = result.incompleteIds || {};
      delete incompleteIds[message.tweetId];
      chrome.storage.local.set({ incompleteIds });
    });
    console.log(`[Birdbrain] Hydrated tweet ${message.tweetId}`);
  }

  if (message.type === "REFRESH_INCOMPLETE") {
    syncIncompleteTweets();
  }
});
