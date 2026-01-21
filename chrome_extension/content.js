// content.js - Runs in ISOLATED world
// Responsible for receiving data from hook.js (MAIN world) and sending it to the local API.

console.log("[Birdbrain] Content script initialized.");

// Listen for the custom event from the main world hook
// Listen on document as well
document.addEventListener('BirdbrainBookmarkData', async function(e) {
  console.log("[Birdbrain] 📨 Received event!");
  
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
      const response = await fetch("http://localhost:8000/api/bookmarks/ingest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
      });

      if (response.ok) {
          const resJson = await response.json();
          console.log(`[Birdbrain] ✅ Success! Server processed ${resJson.processed_count} tweets.`);
          
          // Optional: Notify popup/background if needed
          chrome.runtime.sendMessage({ 
              type: "SYNC_SUCCESS", 
              count: resJson.processed_count 
          }).catch(() => {
              // Popup might be closed, ignore error
          });
          
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
