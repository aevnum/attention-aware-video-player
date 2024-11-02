// content.js

// Function to control video, called when a message is received
function controlVideo(action) {
    const video = document.querySelector('video'); // Select the video element
    if (video) {
        if (action === "pause") {
            video.pause(); // Pause the video
        } else if (action === "play") {
            video.play(); // Play the video
        }
    }
}

// Listen for messages from the background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "controlVideo") {
        controlVideo(request.data); // Call the controlVideo function with the action data
        sendResponse({status: "success"}); // Optionally send a response back
    }
});
