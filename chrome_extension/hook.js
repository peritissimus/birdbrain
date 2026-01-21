// Hook running in the MAIN world.
console.log("[Birdbrain] Hook script loaded in MAIN world.");

(function() {
  // --- 1. Intercept Fetch API ---
  const originalFetch = window.fetch;
  window.fetch = async function(...args) {
    let url = args[0];
    if (args[0] instanceof Request) {
        url = args[0].url;
    }

    // Debug logging
    if (typeof url === 'string' && (url.includes("/i/api/") || url.includes("graphql"))) {
        console.log("[Birdbrain Debug] Fetching:", url);
    }

    const response = await originalFetch(...args);

    try {
        if (typeof url === 'string') {
          // Handle Bookmarks timeline
          if (url.includes("Bookmarks")) {
            console.log("[Birdbrain] 🎯 Matched Bookmarks URL (Fetch):", url);
            const clone = response.clone();
            clone.text()
              .then(textData => {
                  const data = JSON.parse(textData);
                  console.log("[Birdbrain] Dispatching event 'BirdbrainBookmarkData'...");
                  document.dispatchEvent(new CustomEvent('BirdbrainBookmarkData', {
                      detail: JSON.stringify(data)
                  }));
              })
              .catch(err => {});
          }

          // Handle TweetDetail (individual tweet page)
          if (url.includes("TweetDetail") || url.includes("TweetResultByRestId")) {
            console.log("[Birdbrain] 🎯 Matched TweetDetail URL (Fetch):", url);
            const clone = response.clone();
            clone.text()
              .then(textData => {
                  const data = JSON.parse(textData);
                  console.log("[Birdbrain] Dispatching event 'BirdbrainTweetDetail'...");
                  document.dispatchEvent(new CustomEvent('BirdbrainTweetDetail', {
                      detail: JSON.stringify(data)
                  }));
              })
              .catch(err => {});
          }
        }
    } catch (e) {
        console.error("[Birdbrain Hook] Fetch Error:", e);
    }

    return response;
  };

  // --- 2. Intercept XMLHttpRequest (XHR) ---
  const originalXHROpen = XMLHttpRequest.prototype.open;
  const originalXHRSend = XMLHttpRequest.prototype.send;

  XMLHttpRequest.prototype.open = function(method, url, ...rest) {
    this._birdbrainUrl = url;
    return originalXHROpen.apply(this, [method, url, ...rest]);
  };

  XMLHttpRequest.prototype.send = function(body) {
    if (this._birdbrainUrl && typeof this._birdbrainUrl === 'string' &&
       (this._birdbrainUrl.includes("/i/api/") || this._birdbrainUrl.includes("graphql"))) {

        // Check for Bookmarks
        if (this._birdbrainUrl.includes("Bookmarks")) {
            console.log("[Birdbrain] 🎯 Matched Bookmarks URL (XHR):", this._birdbrainUrl);

            this.addEventListener('load', function() {
                try {
                    const data = JSON.parse(this.responseText);
                    console.log("[Birdbrain] Dispatching event 'BirdbrainBookmarkData' (XHR)...");
                    document.dispatchEvent(new CustomEvent('BirdbrainBookmarkData', {
                        detail: JSON.stringify(data)
                    }));
                } catch (e) {
                    console.warn("[Birdbrain Hook] XHR Parse Error:", e);
                }
            });
        }

        // Check for TweetDetail
        if (this._birdbrainUrl.includes("TweetDetail") || this._birdbrainUrl.includes("TweetResultByRestId")) {
            console.log("[Birdbrain] 🎯 Matched TweetDetail URL (XHR):", this._birdbrainUrl);

            this.addEventListener('load', function() {
                try {
                    const data = JSON.parse(this.responseText);
                    console.log("[Birdbrain] Dispatching event 'BirdbrainTweetDetail' (XHR)...");
                    document.dispatchEvent(new CustomEvent('BirdbrainTweetDetail', {
                        detail: JSON.stringify(data)
                    }));
                } catch (e) {
                    console.warn("[Birdbrain Hook] XHR Parse Error:", e);
                }
            });
        }
    }
    return originalXHRSend.apply(this, [body]);
  };

})();
