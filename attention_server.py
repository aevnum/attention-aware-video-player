import time
import cv2
import mediapipe as mp
import asyncio
import json
import websockets
from helpers import *
from collections import deque

attention_history = deque(maxlen=10)  # Keep track of last 10 attention states

async def send_attention_updates(websocket, path):

    # Define eye and pupil landmark indices
    landmark_indices = {
        "LEFT_EYE_OUTER": 33,
        "LEFT_EYE_INNER": 173,
        "RIGHT_EYE_OUTER": 263,
        "RIGHT_EYE_INNER": 398,
        "LEFT_EYE_TOP": 222,
        "LEFT_EYE_BOTTOM": 230,
        "RIGHT_EYE_TOP": 442,
        "RIGHT_EYE_BOTTOM": 450,
        "LEFT_PUPIL": 468,
        "RIGHT_PUPIL": 473,
        "NOSE": 4,
        "CHIN": 152,
        "FOREHEAD": 10
    }

    # Define constants for attention checking
    attention_threshold = 0.1  # 1 second

    # Initialize variables
    attention_start_time = time.time()
    attention = False  # Track attention state to send only when it changes

    # Setup OpenCV and MediaPipe
    cap = cv2.VideoCapture(0)
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.8)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Process frame
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb_frame)

        # Check for face landmarks
        if results.multi_face_landmarks:
            face_landmarks = results.multi_face_landmarks[0]
            landmarks_dict = get_landmarks(face_landmarks, landmark_indices)
            pixel_coords = get_pixel_coords(landmarks_dict, frame.shape)
            ratios = get_ratios(pixel_coords)
            
            # Load attention thresholds
            thresholds = json.load(open('attention_thresholds.json'))
            directions = get_directions(ratios, thresholds)

            # Check if the attention needs to be updated every second
            if time.time() - attention_start_time >= attention_threshold:
                temp_attention = get_attention(directions)  # Get the latest attention state
                attention_history.append(temp_attention)  # Add to history

                # Check if the entire deque is True or False
                if all(attention_history):
                    new_attention = True
                elif not any(attention_history):
                    new_attention = False
                if new_attention != attention:
                    attention = new_attention
                    # Send updated attention state to WebSocket
                    message = "play" if attention else "pause"
                    await asyncio.sleep(0.000001)
                    await websocket.send(message)
                    print(f"Sent: {message}")  # Debug message
                    # print("Attention state changed:", attention)
                # Reset timer
                attention_start_time = time.time()

        else:
            # No face detected; assume no attention
            if attention:  # Only send if attention state changes to False
                await asyncio.sleep(0.000001)
                await websocket.send("pause")
                attention = False
                print("No face detected! Sent: pause")  # Debug message

        cv2.imshow("Frame", frame)

    # Release resources
    cap.release()
    cv2.destroyAllWindows()

# Start WebSocket server
start_server = websockets.serve(send_attention_updates, "localhost", 6789)
asyncio.get_event_loop().run_until_complete(start_server)
print("Server started...")
asyncio.get_event_loop().run_forever()
