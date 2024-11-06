# Real-time Attention Detection with WebSockets

This project is a real-time attention tracking system using OpenCV, MediaPipe, and WebSockets. The program uses a webcam to capture live video, track facial landmarks, and detect whether a user is paying attention. The attention state is determined by analyzing eye and gaze directions and communicated to a WebSocket server to control the state of a client application.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Setup](#setup)
- [Usage](#usage)
- [Files](#files)
- [Customization](#customization)
- [Limitations](#limitations)
- [Acknowledgments](#acknowledgments)

## Features

- Real-time face and eye tracking using MediaPipe and OpenCV.
- Attention detection based on facial landmark ratios.
- Sends "play" or "pause" messages over WebSocket based on the user's attention state.
- Attention state checks occur every second and updates are sent only when the state changes.
- Maintains a history of attention states to improve accuracy and reliability.

## Requirements

- Python 3.7+
- Libraries:
  - OpenCV
  - MediaPipe
  - Websockets
  - `helpers.py` (custom module with required helper functions)

Install the required Python packages with:

```bash
pip install opencv-python mediapipe websockets
```

## Setup

1. Clone the repository and navigate to the project directory.
2. Install the required packages listed above.
3. Go to your chromium based browser of choice.
4. Turn on developer mode on top right.
5. Click "Load Unpacked" and choose the extension folder.
6. Start the program with GUI by using the command:

```bash
python attention_detection.py
```

7. Then click the "Calibrate Thresholds" button and follow on screen instructions to generate your thresholds. To achieve the best sensitivity I recommend looking right outside the edges of your screen. If you look too far out the the video might not pause when you look away (Sensitivity too low), if you look near the edges of your screen the video might frequently pause (Sensitivity too high).
8. Then click "Start server" to open the websocket server.
9. Open the browser and video. If the video was already open, just close and open the browser to reactivate connection.
10. Now the program is running!
11. When you want to stop, click Stop server, and once it tells you to close window, close the window.

### WebSocket Server Address
- Default server address: `localhost`
- Default port: `6789`

To connect a WebSocket client, use `ws://localhost:6789`.

### Example Output

- **Sent: play**: Indicates the user is attentive.
- **Sent: pause**: Indicates the user is inattentive or no face is detected.

## Files

- `attention_detection.py`: Main program file that runs the attention detection system.
- `helpers.py`: Contains helper functions for processing face landmarks and calculating attention states.
- `attention_thresholds.json`: JSON file with threshold values for attention determination.

## Customization

- **Adjust Attention Thresholds**: Update `attention_thresholds.json` to fine-tune sensitivity.
- **WebSocket Address/Port**: Modify `start_server` parameters to change the WebSocket address or port.
- **Attention Duration**: Modify `attention_threshold` to change the interval between attention state checks.

## Limitations

- This system is designed for single-user environments and may struggle with multiple faces.
- Requires consistent lighting for optimal facial landmark detection.
- Attention detection may vary depending on facial orientation and camera quality.

## Acknowledgments

- [MediaPipe](https://google.github.io/mediapipe/) for facial landmark tracking.
- [OpenCV](https://opencv.org/) for image processing.
- [WebSockets](https://websockets.readthedocs.io/) for real-time communication.

---

This project is a demonstration of real-time facial analysis and attention detection in Python. Enjoy customizing it for your own applications!