"""Stereo reconstruction of the red drone center in the bundled synthetic videos."""
import csv
import json
from pathlib import Path
import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent

def detect_red(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.bitwise_or(cv2.inRange(hsv, (0, 110, 100), (12, 255, 255)),
                          cv2.inRange(hsv, (170, 110, 100), (179, 255, 255)))
    count, labels, stats, centroids = cv2.connectedComponentsWithStats(mask)
    candidates = [i for i in range(1, count) if 3 <= stats[i, cv2.CC_STAT_AREA] <= 500]
    if not candidates:
        return None
    i = max(candidates, key=lambda j: stats[j, cv2.CC_STAT_AREA])
    return centroids[i].astype(float)

def main():
    meta = json.loads((ROOT / 'cameras.json').read_text(encoding='utf-8'))
    P = [np.asarray(c['projection_matrix'], dtype=float) for c in meta['cameras'][:2]]
    caps = [cv2.VideoCapture(str(ROOT / f'camera_{i}.mp4')) for i in (1, 2)]
    if not all(c.isOpened() for c in caps):
        raise RuntimeError('Could not open both videos')
    fps = [c.get(cv2.CAP_PROP_FPS) for c in caps]
    if abs(fps[0] - fps[1]) > 0.01:
        raise RuntimeError('Video frame rates do not match')
    frames = []
    n = 0
    while True:
        pair = [cap.read() for cap in caps]
        if not all(ok for ok, _ in pair):
            break
        pts = [detect_red(item[1]) for item in pair]
        if all(p is not None for p in pts):
            h = cv2.triangulatePoints(P[0], P[1], pts[0].reshape(2, 1), pts[1].reshape(2, 1))[:, 0]
            if abs(h[3]) > 1e-10:
                X = h[:3] / h[3]
                errors = []
                for Pi, point in zip(P, pts):
                    q = Pi @ np.r_[X, 1.0]
                    errors.append(float(np.linalg.norm(q[:2] / q[2] - point)))
                if max(errors) < 5:
                    frames.append({'frame': n, 'time': n / fps[0], 'position': X.tolist(),
                                   'reprojection_error_px': max(errors)})
        n += 1
    for cap in caps:
        cap.release()
    result = {'fps': fps[0], 'coordinate_system': 'world XYZ, Z up', 'units': 'meters', 'frames': frames}
    (ROOT / 'trajectory.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    with (ROOT / 'trajectory.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['frame', 'time_s', 'x', 'y', 'z', 'reprojection_error_px'])
        for item in frames:
            writer.writerow([item['frame'], item['time'], *item['position'], item['reprojection_error_px']])
    print(f'Processed {n} synchronized pairs; recovered {len(frames)} 3D points.')
    truth = {}
    with (ROOT / 'ground_truth.csv').open(newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            truth[int(row['frame'])] = np.array([float(row[k]) for k in ('x', 'y', 'z')])
    if frames:
        errors = [np.linalg.norm(np.array(fr['position']) - truth[fr['frame']])
                  for fr in frames if fr['frame'] in truth]
        if errors:
            print(f'3D position error: mean={np.mean(errors):.4f} m, RMSE={np.sqrt(np.mean(np.square(errors))):.4f} m')
    print('Saved trajectory.json and trajectory.csv')

if __name__ == '__main__':
    main()
