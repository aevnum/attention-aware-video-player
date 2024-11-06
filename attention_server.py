import time
import cv2
import mediapipe as mp
import asyncio
import json
import websockets
from helpers import *
from collections import deque
import numpy as np
from typing import Dict
import tkinter as tk
import threading
from concurrent.futures import ThreadPoolExecutor
import socket

attention_history = deque(maxlen=5)  # Keep track of last 10 attention states

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

def check_attention_state(attention_history):
    # Check if the entire deque is True or False
    if all(attention_history):
        return True
    elif not any(attention_history):
        return False
    return None  # Return None if no clear consensus

async def send_attention_updates(websocket, path):

    # Define constants for attention checking
    attention_threshold = 0.1  # 1 second

    # Initialize variables
    attention_start_time = time.time()
    attention = False  # Track attention state to send only when it changes
    new_attention = False

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
                temp_attention = get_attention(directions)
                attention_history.append(temp_attention)
                new_attention = check_attention_state(attention_history)
                
                if new_attention is not None and new_attention != attention:
                    attention = new_attention
                    message = "play" if attention else "pause"
                    await asyncio.sleep(0.000001)
                    await websocket.send(message)
                    print(f"Sent: {message}")
                attention_start_time = time.time()

        else:
            # No face detected; assume no attention
            if time.time() - attention_start_time >= attention_threshold:
                attention_history.append(False)  # No face means no attention
                new_attention = check_attention_state(attention_history)
                
                if new_attention is not None and new_attention != attention:
                    attention = new_attention
                    message = "play" if attention else "pause"
                    await asyncio.sleep(0.000001)
                    await websocket.send(message)
                    print(f"Sent: {message}")
                attention_start_time = time.time()

    # Release resources
    cap.release()
    cv2.destroyAllWindows()

def calibrate_thresholds(landmark_indices: Dict[str, int]) -> Dict[str, float]:
    """
    Calibrate eye and face movement thresholds through user interaction.
    Returns a dictionary of calculated thresholds.
    """
    # Initialize video capture and MediaPipe
    cap = cv2.VideoCapture(0)
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True, 
                                     min_detection_confidence=0.8)

    # Initialize storage for calibration measurements
    measurements = {
        "LEFT_EYE_HORIZONTAL": {"LEFT": [], "RIGHT": [], "CENTER": []},
        "RIGHT_EYE_HORIZONTAL": {"LEFT": [], "RIGHT": [], "CENTER": []},
        "LEFT_EYE_VERTICAL": {"UP": [], "DOWN": [], "CENTER": []},
        "RIGHT_EYE_VERTICAL": {"UP": [], "DOWN": [], "CENTER": []},
        "FACE_HORIZONTAL": {"LEFT": [], "RIGHT": [], "CENTER": []},
        "FACE_VERTICAL": {"UP": [], "DOWN": [], "CENTER": []}
    }

    # Calibration steps configuration
    calibration_steps = [
        # Eye calibration
        ("Keep your head centered and look LEFT with your eyes", "EYE", "LEFT"),
        ("Keep your head centered and look RIGHT with your eyes", "EYE", "RIGHT"),
        ("Keep your head centered and look UP with your eyes", "EYE", "UP"),
        ("Keep your head centered and look DOWN with your eyes", "EYE", "DOWN"),
        # Face calibration
        ("Keep your eyes on screen and turn your head LEFT", "FACE", "LEFT"),
        ("Keep your eyes on screen and turn your head RIGHT", "FACE", "RIGHT"),
        ("Keep your eyes on screen and tilt your head UP", "FACE", "UP"),
        ("Keep your eyes on screen and tilt your head DOWN", "FACE", "DOWN"),
    ]

    print("\nCalibration Process Starting...")
    print("For each step:")
    print("1. Follow the instruction on screen")
    print("2. Press SPACE when ready to capture")
    print("3. Hold position for 2 seconds while captures are taken")
    print("Press any key to begin...")
    cv2.waitKey(0)

    # Run calibration steps
    for instruction, measure_type, direction in calibration_steps:
        captures_remaining = 10  # Number of captures to take for each position
        capturing = False
        
        while captures_remaining > 0:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)

            # Process frame
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb_frame)

            # Display instruction and status
            status_frame = frame.copy()
            cv2.putText(status_frame, instruction, (20, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(status_frame, f"Captures remaining: {captures_remaining}", 
                       (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            if capturing:
                cv2.putText(status_frame, "CAPTURING...", (20, 90), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            else:
                cv2.putText(status_frame, "Press SPACE when ready", (20, 90), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

            cv2.imshow('Calibration', status_frame)

            key = cv2.waitKey(1)
            if key == 27:  # ESC to exit
                cap.release()
                cv2.destroyAllWindows()
                return None

            if key == 32:  # SPACE to start capturing
                capturing = True

            if capturing and results.multi_face_landmarks:
                # Use helper functions to get landmarks and ratios
                landmarks_dict = get_landmarks(results.multi_face_landmarks[0], landmark_indices)
                pixel_coords = get_pixel_coords(landmarks_dict, frame.shape)
                ratios = get_ratios(pixel_coords)
                
                # Store measurements based on type
                if measure_type == "EYE":
                    if direction in ["LEFT", "RIGHT"]:
                        measurements["LEFT_EYE_HORIZONTAL"][direction].append(ratios["LEFT_EYE_HORIZONTAL"])
                        measurements["RIGHT_EYE_HORIZONTAL"][direction].append(ratios["RIGHT_EYE_HORIZONTAL"])
                    else:  # UP or DOWN
                        measurements["LEFT_EYE_VERTICAL"][direction].append(ratios["LEFT_EYE_VERTICAL"])
                        measurements["RIGHT_EYE_VERTICAL"][direction].append(ratios["RIGHT_EYE_VERTICAL"])
                else:  # FACE
                    if direction in ["LEFT", "RIGHT"]:
                        measurements["FACE_HORIZONTAL"][direction].append(ratios["FACE_HORIZONTAL"])
                    else:  # UP or DOWN
                        measurements["FACE_VERTICAL"][direction].append(ratios["FACE_VERTICAL"])
                
                captures_remaining -= 1
                time.sleep(0.2)  # Small delay between captures

            if captures_remaining == 0:
                time.sleep(1)
                break

    cap.release()
    cv2.destroyAllWindows()

    # Calculate thresholds
    thresholds = {}
    
    # Calculate eye thresholds
    eye_horizontal_left = max(
        np.mean(measurements["LEFT_EYE_HORIZONTAL"]["LEFT"]),
        np.mean(measurements["RIGHT_EYE_HORIZONTAL"]["LEFT"])
    )
    eye_horizontal_right = max(
        np.mean(measurements["LEFT_EYE_HORIZONTAL"]["RIGHT"]),
        np.mean(measurements["RIGHT_EYE_HORIZONTAL"]["RIGHT"])
    )
    eye_vertical_up = max(
        np.mean(measurements["LEFT_EYE_VERTICAL"]["UP"]),
        np.mean(measurements["RIGHT_EYE_VERTICAL"]["UP"])
    )
    eye_vertical_down = max(
        np.mean(measurements["LEFT_EYE_VERTICAL"]["DOWN"]),
        np.mean(measurements["RIGHT_EYE_VERTICAL"]["DOWN"])
    )

    thresholds["FACE_VERTICAL_DOWN"] = round(np.mean(measurements["FACE_VERTICAL"]["DOWN"]), 2)
    thresholds["FACE_VERTICAL_UP"] = round(np.mean(measurements["FACE_VERTICAL"]["UP"]), 2)
    thresholds["FACE_HORIZONTAL_RIGHT"] = round(np.mean(measurements["FACE_HORIZONTAL"]["RIGHT"]), 2)
    thresholds["FACE_HORIZONTAL_LEFT"] = round(np.mean(measurements["FACE_HORIZONTAL"]["LEFT"]), 2)

    thresholds["EYE_VERTICAL_DOWN"] = round(eye_vertical_down, 2)
    thresholds["EYE_VERTICAL_UP"] = round(eye_vertical_up, 2)
    thresholds["EYE_HORIZONTAL_RIGHT"] = round(eye_horizontal_right, 2)
    thresholds["EYE_HORIZONTAL_LEFT"] = round(eye_horizontal_left, 2)

    # Save thresholds to JSON file
    with open('attention_thresholds.json', 'w') as f:
        json.dump(thresholds, f, indent=4)

    print("\nCalibration complete! Thresholds saved to 'attention_thresholds.json'")
    return thresholds


class AttentionServerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Attention Server Control")
        self.root.geometry("300x150")
        
        # Server state
        self.server = None
        self.is_running = False
        self.loop = None
        self.server_thread = None
        self.shutdown_event = threading.Event()
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.shutdown_requested = threading.Event()
        self.shutdown_complete = threading.Event()
        self.last_shutdown_time = 0
        
        # Create GUI elements
        self.status_label = tk.Label(self.root, text="Server Status: Stopped", pady=10)
        self.status_label.pack()
        
        self.start_button = tk.Button(self.root, text="Start Server", 
                                    command=self.start_server, pady=5)
        self.start_button.pack()
        
        self.stop_button = tk.Button(self.root, text="Stop Server", 
                                   command=self.initiate_stop, state=tk.DISABLED, pady=5)
        self.stop_button.pack()

        self.calibrate_button = tk.Button(self.root, text="Calibrate Thresholds", 
                                        command=self.start_calibration, pady=5)
        self.calibrate_button.pack()

    def start_calibration(self):
        """Start the calibration process"""
        if self.is_running:
            self.status_label.config(text="Please stop server before calibrating")
            return
            
        self.status_label.config(text="Starting calibration...")
        self.disable_all_buttons()

        try:
            # Run calibration in separate thread to prevent GUI freeze
            thread = threading.Thread(target=self._run_calibration)
            thread.daemon = True
            thread.start()
        except Exception as e:
            self.status_label.config(text="Calibration failed")
            self.enable_all_buttons()

    def _run_calibration(self):
        """Run calibration in background thread"""
        try:
            thresholds = calibrate_thresholds(landmark_indices)
            if thresholds:
                self.root.after(0, self.status_label.config, 
                              {"text": "Calibration completed successfully"})
            else:
                self.root.after(0, self.status_label.config, 
                              {"text": "Calibration cancelled"})
        except Exception as e:
            self.root.after(0, self.status_label.config, 
                          {"text": f"Calibration error: {str(e)}"})
        finally:
            self.root.after(0, self.enable_all_buttons)

    def initiate_stop(self):
        """Initiate server shutdown without blocking GUI"""
        self.executor.submit(self.stop_server)

    def run_server(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        self.loop = asyncio.get_event_loop()
        try:
            self.server = self.loop.run_until_complete(
                websockets.serve(send_attention_updates, "localhost", 6789)
            )
            self.root.after(0, self.update_buttons, True)
            
            while not self.shutdown_requested.is_set():
                self.loop.run_until_complete(asyncio.sleep(0.1))
            
            self.server.close()
            self.loop.run_until_complete(self.server.wait_closed())
            
            pending = asyncio.all_tasks(self.loop)
            if pending:
                self.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            
            self.loop.close()
            self.shutdown_complete.set()
            
        except Exception as e:
            self.root.after(0, self.update_buttons, False)
        finally:
            self.shutdown_complete.set()
        
    def start_server(self):
        if not self.is_running:
            # Check cooldown period (30 seconds)
            if time.time() - self.last_shutdown_time < 30:
                remaining = int(30 - (time.time() - self.last_shutdown_time))
                self.status_label.config(text=f"Please wait {remaining}s before restart")
                return
                
            if not self.check_port_available():
                self.status_label.config(text="Port 6789 is in use")
                return
                
            self.shutdown_event.clear()
            self.server_thread = threading.Thread(target=self.run_server)
            self.server_thread.daemon = True
            self.server_thread.start()
            self.status_label.config(text="Server Status: Starting...")
    
    def stop_server(self):
        if self.is_running:
            self.shutdown_requested.set()
            
            if not self.shutdown_complete.wait(timeout=5):
                if self.server:
                    self.server.close()
                if self.loop and self.loop.is_running():
                    self.loop.call_soon_threadsafe(self.loop.stop)
            
            cv2.destroyAllWindows()
            
            self.is_running = False
            self.server = None
            self.loop = None
            self.last_shutdown_time = time.time()
            self.root.after(0, self.update_buttons, False)
            self.status_label.config(text="Server Stopped. You can now close the window.")

    def check_port_available(self, port=6789):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                s.close()
                return True
        except OSError:
            return False
        
    def disable_all_buttons(self):
        """Disable all buttons during calibration"""
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.DISABLED)
        self.calibrate_button.config(state=tk.DISABLED)

    def enable_all_buttons(self):
        """Re-enable buttons after calibration"""
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.calibrate_button.config(state=tk.NORMAL)
            
    def update_buttons(self, running: bool):
        """Update button states based on server status"""
        self.is_running = running
        self.start_button.config(state=tk.DISABLED if running else tk.NORMAL)
        self.stop_button.config(state=tk.NORMAL if running else tk.DISABLED)
        self.calibrate_button.config(state=tk.DISABLED if running else tk.NORMAL)
        if running:
            self.status_label.config(text="Server Status: Running")

    def run(self):
        """Start the GUI main loop"""
        try:
            self.root.mainloop()
        finally:
            if self.is_running:
                self.stop_server()
            self.executor.shutdown(wait=False)

if __name__ == "__main__":
    app = AttentionServerGUI()
    app.run()