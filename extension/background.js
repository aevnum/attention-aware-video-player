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

    socket.onmessage = async (event) => {
        if (event.data === "pause" || event.data === "play") {
            console.log("Received message:", event.data);
            try {
                // Send message to content script and wait for response
                const result = await chrome.tabs.query({ active: true, currentWindow: true })
                    .then(tabs => {
                        if (tabs.length > 0) {
                            return chrome.tabs.sendMessage(tabs[0].id, {
                                action: "controlVideo",
                                data: event.data
                            });
                        }
                        throw new Error("No active tab found");
                    });
                
                if (result && result.status === "success") {
                    // Send acknowledgment back to server
                    socket.send(`ack_${event.data}`);
                }
            } catch (error) {
                console.error("Error controlling video:", error);
            }
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
