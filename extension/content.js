// content.js

// Function to control video, called when a message is received
function controlVideo(action) {
    return new Promise((resolve, reject) => {
        const maxAttempts = 5;
        let attempts = 0;
        
        const tryControl = () => {
            // Try multiple video element selectors
            const videoSelectors = [
                'video',
                'video[src]',
                'video[style*="display: block"]',
                '.html5-main-video',
                '.video-stream'
            ];
            
            const video = videoSelectors.map(selector => 
                document.querySelector(selector)).find(v => v);
            
            if (video) {
                try {
                    if (action === "pause") {
                        video.pause();
                        if (video.paused) {
                            console.log("Video successfully paused");
                            return resolve({status: "success"});
                        }
                    } else if (action === "play") {
                        const playPromise = video.play();
                        if (playPromise) {
                            playPromise
                                .then(() => {
                                    console.log("Video successfully played");
                                    resolve({status: "success"});
                                })
                                .catch(error => {
                                    console.error("Play error:", error);
                                    retry();
                                });
                            return;
                        }
                    }
                } catch (error) {
                    console.error("Control error:", error);
                }
            }
            retry();
        };
        
        const retry = () => {
            attempts++;
            if (attempts < maxAttempts) {
                setTimeout(tryControl, 100 * attempts);
            } else {
                reject(new Error(`Failed to ${action} video after ${maxAttempts} attempts`));
            }
        };
        
        tryControl();
    });
}

// Update message listener
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "controlVideo") {
        controlVideo(request.data)
            .then(response => sendResponse(response))
            .catch(error => sendResponse({status: "error", message: error.toString()}));
        return true; // Required for async response
    }
});
