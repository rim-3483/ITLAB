# Modular VPython stereo flight demo

The existing stereo reconstruction script (`reconstruct.py`) and videos are preserved. The old monolithic `view_vpython.py` is replaced by independent modules:

- `scene.py`: floor, grid, axes, camera markers, lighting; no flight animation
- `drone.py`: model geometry and `move_to()`
- `flight.py`: reads trajectory, displays path, controls playback and telemetry
- `coordinates.py`: dataset Z-up -> VPython Y-up conversion
- `main.py`: wires modules together

## Run

From the project folder:

```bat
py -m pip install -r requirements.txt
py reconstruct.py
py main.py
```

You can skip `reconstruct.py` if `trajectory.json` already exists. To switch flights, replace both videos and the matching `cameras.json`, then run reconstruction again. Scene appearance can be edited in `scene.py` without touching flight playback. Camera markers use positions from `cameras.json`.
