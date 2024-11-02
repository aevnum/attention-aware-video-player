import cv2
import mediapipe as mp
import numpy as np
import json
import time
from helpers import get_landmarks, get_pixel_coords, get_ratios
from typing import Dict

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
calibrate_thresholds(landmark_indices)