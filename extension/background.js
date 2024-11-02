let socket;
let reconnectInterval = 5000;  // Initial reconnect delay
let maxReconnectInterval = 30000;  // Max delay of 30 seconds
let isConnected = false;  // Track connection status
let pingInterval;  // Interval ID for pinging server

function connectWebSocket() {
    socket = new WebSocket("ws://localhost:6789");

    socket.onopen = () => {
        console.log("WebSocket connected");
        isConnected = true;
        reconnectInterval = 5000;  // Reset reconnect delay after successful connection

        // Start pinging every 10 seconds to keep connection alive
        pingInterval = setInterval(() => {
            if (socket.readyState === WebSocket.OPEN) {
                socket.send("ping");
            }
        }, 10000);
    };

    socket.onmessage = (event) => {
        if (event.data === "pause" || event.data === "play") {
            console.log("Received message:", event.data);
            chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
                // Send a message to the content script to control the video
                if (tabs.length > 0) {
                    chrome.tabs.sendMessage(tabs[0].id, { action: "controlVideo", data: event.data });
                }
            });
        }
    };

    socket.onclose = () => {
        console.log("WebSocket closed. Reconnecting in", reconnectInterval / 1000, "seconds...");
        isConnected = false;

        // Clear the ping interval to stop pings
        clearInterval(pingInterval);

        // Retry connection with exponential backoff
        setTimeout(() => {
            if (!isConnected) {
                reconnectInterval = Math.min(maxReconnectInterval, reconnectInterval * 1.5);  // Increase delay
                connectWebSocket();
            }
        }, reconnectInterval);
    };

    socket.onerror = (error) => {
        console.error("WebSocket error:", error);
        // Force close to trigger the onclose handler and reconnect
        socket.close();
    };
}

// Establish the WebSocket connection when the extension is loaded
connectWebSocket();
