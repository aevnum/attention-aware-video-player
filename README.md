# Attention-Aware Video Player

An attention-aware video player that detects when a user is looking at the screen or not. It uses a machine learning model to send a binary output indicating whether to play (1) or pause (0) a video, based on real-time webcam input.

## Features
- **Calibration**: Collect labeled data for "looking at screen" and "not looking at screen" to fine-tune the model.
- **Real-Time Detection**: Continuously monitor the user's attention to play or pause video content automatically.

## Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/aevnum/attention-aware-video-player.git
   cd attention-aware-video-player
   ```

2. **Set up a virtual environment**:
   ```bash
   python -m venv env
   env\Scripts\activate  # For Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Run Calibration**:
   ```bash
   python src/calibration.py
   ```
   This will capture labeled images for "looking at screen" and "not looking at screen" for model training.

2. **Train the Model**:
   Coming soon.

3. **Run Real-Time Detection**:
   Coming soon.

## Project Structure

```
├── data/                 # Stores calibration images
├── src/
│   ├── calibration.py    # Calibration script
│   ├── inference.py      # Real-time detection script
│   └── model_setup.py    # Model setup and configuration
├── README.md
├── requirements.txt
└── .gitignore
```

## License
This project is licensed under the MIT License.
