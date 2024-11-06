def get_landmarks(landmarks, landmark_indices):
    landmarks_dict = {}
    for landmark, index in landmark_indices.items():
        landmarks_dict[landmark] = landmarks.landmark[index]
    return landmarks_dict

def get_pixel_coords(landmarks_dict, shape):
    pixel_coords = {}
    for landmark, landmark_coords in landmarks_dict.items():
        pixel_coords[landmark] = (int(landmark_coords.x * shape[1]), int(landmark_coords.y * shape[0]))
    return pixel_coords

def calculate_ratio(p1,p2,p3):
    return abs(p1 - p2) / abs(p1 - p3) if abs(p1 - p3) != 0 else 0

def get_ratios(pixel_coords):
    ratios = {}
    # Get eye ratios
    ratios["LEFT_EYE_HORIZONTAL"] = calculate_ratio(pixel_coords["LEFT_EYE_OUTER"][0], pixel_coords["LEFT_PUPIL"][0], pixel_coords["LEFT_EYE_INNER"][0])
    ratios["LEFT_EYE_VERTICAL"] = calculate_ratio(pixel_coords["LEFT_EYE_TOP"][1], pixel_coords["LEFT_PUPIL"][1], pixel_coords["LEFT_EYE_BOTTOM"][1])
    ratios["RIGHT_EYE_HORIZONTAL"] = calculate_ratio(pixel_coords["RIGHT_EYE_INNER"][0], pixel_coords["RIGHT_PUPIL"][0], pixel_coords["RIGHT_EYE_OUTER"][0])
    ratios["RIGHT_EYE_VERTICAL"] = calculate_ratio(pixel_coords["RIGHT_EYE_TOP"][1], pixel_coords["RIGHT_PUPIL"][1], pixel_coords["RIGHT_EYE_BOTTOM"][1])

    # Get face ratios
    ratios["FACE_VERTICAL"] = calculate_ratio(pixel_coords["FOREHEAD"][1], pixel_coords["NOSE"][1], pixel_coords["CHIN"][1])
    ratios["FACE_HORIZONTAL"] = calculate_ratio(pixel_coords["LEFT_EYE_OUTER"][0], pixel_coords["NOSE"][0], pixel_coords["RIGHT_EYE_OUTER"][0])
    return ratios

def get_directions(ratios, thresholds):
    directions = {}

    # Determine face horizontal direction
    if ratios["FACE_HORIZONTAL"] > thresholds["FACE_HORIZONTAL_RIGHT"]:
        directions["FACE_HORIZONTAL"] = "Right"
    elif ratios["FACE_HORIZONTAL"] < thresholds["FACE_HORIZONTAL_LEFT"]:
        directions["FACE_HORIZONTAL"] = "Left"
    else:
        directions["FACE_HORIZONTAL"] = "Center"

    # Determine face vertical direction
    if ratios["FACE_VERTICAL"] > thresholds["FACE_VERTICAL_DOWN"]:
        directions["FACE_VERTICAL"] = "Down"
    elif ratios["FACE_VERTICAL"] < thresholds["FACE_VERTICAL_UP"]:
        directions["FACE_VERTICAL"] = "Up"
    else:
        directions["FACE_VERTICAL"] = "Center"

    # Determine eye vertical direction
    if ratios["LEFT_EYE_VERTICAL"] > thresholds["EYE_VERTICAL_DOWN"] or ratios["RIGHT_EYE_VERTICAL"] > thresholds["EYE_VERTICAL_DOWN"]:
        directions["EYE_VERTICAL"] = "Down"
    elif ratios["LEFT_EYE_VERTICAL"] < thresholds["EYE_VERTICAL_UP"] or ratios["RIGHT_EYE_VERTICAL"] < thresholds["EYE_VERTICAL_UP"]:
        directions["EYE_VERTICAL"] = "Up"
    else:
        directions["EYE_VERTICAL"] = "Center"

    # Determine eye horizontal direction
    if ratios["LEFT_EYE_HORIZONTAL"] > thresholds["EYE_HORIZONTAL_RIGHT"] or ratios["RIGHT_EYE_HORIZONTAL"] > thresholds["EYE_HORIZONTAL_RIGHT"]:
        directions["EYE_HORIZONTAL"] = "Right"
    elif ratios["LEFT_EYE_HORIZONTAL"] < thresholds["EYE_HORIZONTAL_LEFT"] or ratios["RIGHT_EYE_HORIZONTAL"] < thresholds["EYE_HORIZONTAL_LEFT"]:
        directions["EYE_HORIZONTAL"] = "Left"
    else:
        directions["EYE_HORIZONTAL"] = "Center"

    return directions

def get_attention(directions):
    if ((directions["FACE_VERTICAL"] == "Center" and
        directions["FACE_HORIZONTAL"] == "Center" and
        directions["EYE_VERTICAL"] == "Center" and
        directions["EYE_HORIZONTAL"] == "Center") or 
        (directions["FACE_VERTICAL"] == "Up" and directions["EYE_VERTICAL"] == "Down") or 
        (directions["FACE_VERTICAL"] == "Down" and directions["EYE_VERTICAL"] == "Up") or 
        (directions["FACE_HORIZONTAL"] == "Left" and directions["EYE_HORIZONTAL"] == "Right") or 
        (directions["FACE_HORIZONTAL"] == "Right" and directions["EYE_HORIZONTAL"] == "Left")):
        attention = True
    else:
        attention = False
    return attention

def check_attention_state(attention_history):
    # Check if the entire deque is True or False
    if all(attention_history):
        return True
    elif not any(attention_history):
        return False