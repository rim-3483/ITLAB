import json
import time
from pathlib import Path
import numpy as np
from vpython import curve, sphere, label, color, vector, button, wtext, rate
from coordinates import to_vpython as v


def load_trajectory(filename):
    data=json.loads(Path(filename).read_text(encoding='utf8'))
    frames=data['frames']
    if len(frames)<2: raise ValueError('Need at least 2 trajectory frames')
    times=np.asarray([float(f['time']) for f in frames],dtype=float)
    points=np.asarray([f['position'] for f in frames],dtype=float)
    if points.shape!=(len(times),3) or not np.isfinite(points).all():
        raise ValueError('Invalid 3D coordinates')
    if not np.isfinite(times).all() or np.any(np.diff(times)<=0):
        raise ValueError('Times must increase strictly')
    return times,points


def run_flight(world, drone, times, points):
    curve(pos=[v(p) for p in points],radius=.022,color=vector(.1,.95,1))
    first=sphere(pos=v(points[0]),radius=.13,color=color.green,emissive=True)
    last=sphere(pos=v(points[-1]),radius=.13,color=color.yellow,emissive=True)
    label(pos=first.pos+vector(0,.25,0),text='START',box=False,opacity=0,color=color.green,height=11)
    label(pos=last.pos+vector(0,.25,0),text='END',box=False,opacity=0,color=color.yellow,height=11)
    state={'playing':True,'speed':1.,'elapsed':0.}
    def toggle(_):
        state['playing']=not state['playing']
        play_button.text='Pause' if state['playing'] else 'Play'
    def restart(_):
        state['elapsed']=0.
        drone.move_to(v(points[0]))
    def slower(_):
        state['speed']=max(.25,state['speed']/2)
        speed_text.text=f"  Speed: {state['speed']:g}x  "
    def faster(_):
        state['speed']=min(4.,state['speed']*2)
        speed_text.text=f"  Speed: {state['speed']:g}x  "
    world.append_to_caption('\n')
    play_button=button(text='Pause',bind=toggle)
    world.append_to_caption('   ')
    button(text='Restart',bind=restart)
    world.append_to_caption('   ')
    button(text='Slower',bind=slower)
    speed_text=wtext(text='  Speed: 1x  ')
    button(text='Faster',bind=faster)
    world.append_to_caption('\n\n')
    telemetry=wtext(text='Initializing...')
    period=float(times[-1]-times[0]);last_tick=time.monotonic()
    while True:
        rate(60)
        now=time.monotonic()
        delta=min(now-last_tick,.2)
        last_tick=now
        if state['playing']:
            state['elapsed']=(state['elapsed']+delta*state['speed'])%period
        t=times[0]+state['elapsed']
        j=int(np.searchsorted(times,t,side='right'))
        j=min(max(j,1),len(times)-1)
        alpha=(t-times[j-1])/(times[j]-times[j-1])
        p=(1-alpha)*points[j-1]+alpha*points[j]
        vel=(points[j]-points[j-1])/(times[j]-times[j-1])
        drone.move_to(v(p))
        telemetry.text=(f"Time: {state['elapsed']:5.2f} / {period:.2f} s    "
                        f"Position XYZ: ({p[0]:.2f}, {p[1]:.2f}, {p[2]:.2f}) m    "
                        f"Speed: {np.linalg.norm(vel):.2f} m/s")
