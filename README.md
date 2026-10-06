# Hand Tracking Air Drawing

A local Windows webcam application that lets you draw in the air with your index finger. It uses OpenCV for the camera/window, MediaPipe Hands for landmarks, and NumPy for the transparent drawing layer.

## Architecture

- `main.py` starts the application.
- `air_drawing_app/main.py` owns the webcam loop, keyboard shortcuts, state machine, smoothing, and integration.
- `air_drawing_app/hand_tracker.py` wraps MediaPipe Hands and converts landmarks to pixel coordinates.
- `air_drawing_app/gesture_detector.py` contains modular finger-state helpers and the five-finger clear gesture.
- `air_drawing_app/drawing_canvas.py` manages a persistent transparent BGRA canvas and composites it over the webcam frame.
- `air_drawing_app/ui.py` draws the palette, brush controls, cursor, status, and notifications.
- `air_drawing_app/config.py` stores app settings, colors, brush sizes, and states.

## Install

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Run

```powershell
python main.py
```

## Gestures

Select a color first by moving your index fingertip over a palette button. The app then enters drawing mode and your smoothed index fingertip draws on the transparent canvas.

Open all five fingers for several consecutive frames to clear the canvas. A cooldown prevents the same pose from clearing repeatedly. Clearing also resets the selected color, so you must choose a new color before drawing again.

Move your index fingertip over a brush-size button to change brush size. Brush controls work without a mouse.

## Keyboard Shortcuts

- `Esc`: exit
- `C`: clear canvas and reset color
- `R`: reset to color selection
- `+`: increase brush size
- `-`: decrease brush size
