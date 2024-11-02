// background.js
let socket;

function connectWebSocket() {
    socket = new WebSocket("ws://localhost:6789");

    socket.onopen = () => {
        console.log("WebSocket connected");
    };

    socket.onmessage = (event) => {
        // Relay message to content script
        if (event.data === "pause" || event.data === "play") {
            console.log("Received message:", event.data);
            chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
                // Send a message to the content script
                chrome.tabs.sendMessage(tabs[0].id, { action: "controlVideo", data: event.data });
            });
        }
    };

    socket.onclose = () => {
        console.log("WebSocket closed. Reconnecting in 5 seconds...");
        setTimeout(connectWebSocket, 5000);
    };

    socket.onerror = (error) => {
        console.error("WebSocket error:", error);
    };
}

// Establish the WebSocket connection when the extension is loaded
connectWebSocket();
