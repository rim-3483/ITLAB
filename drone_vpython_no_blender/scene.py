import json
from pathlib import Path
import numpy as np
from vpython import canvas, vector, box, cylinder, curve, arrow, label, color, distant_light
from coordinates import to_vpython as v


def create_scene(points, cameras_file=None):
    center = np.mean(points, axis=0)
    world = canvas(title='3D flight laboratory | stereo reconstruction',
                   width=1100, height=680, background=vector(.035,.055,.095))
    world.center = v(center)
    world.range = max(4., float(np.ptp(points, axis=0).max())*.95)
    world.forward = vector(-1,-.55,-1.25)
    world.ambient = vector(.35,.35,.4)
    distant_light(direction=vector(-.4,-1,-.5), color=vector(.85,.9,1))
    xmin,xmax = float(points[:,0].min()),float(points[:,0].max())
    ymin,ymax = float(points[:,1].min()),float(points[:,1].max())
    floor_z = min(0.,float(points[:,2].min())-1.)
    span = max(8.,xmax-xmin+5,ymax-ymin+5)
    ox,oy = float(center[0]),float(center[1])
    box(pos=v([ox,oy,floor_z-.06]),size=vector(span,.12,span),
        color=vector(.09,.14,.19),opacity=.75)
    x0,x1 = int(np.floor(ox-span/2)),int(np.ceil(ox+span/2))
    y0,y1 = int(np.floor(oy-span/2)),int(np.ceil(oy+span/2))
    for x in range(x0,x1+1):
        curve(pos=[v([x,y0,floor_z+.01]),v([x,y1,floor_z+.01])],
              color=vector(.21,.31,.38),radius=.008)
    for y in range(y0,y1+1):
        curve(pos=[v([x0,y,floor_z+.01]),v([x1,y,floor_z+.01])],
              color=vector(.21,.31,.38),radius=.008)
    origin=v([x0+.5,y0+.5,floor_z+.03])
    for direction,c,name in [(vector(1,0,0),color.red,'X'),
                             (vector(0,0,-1),color.green,'Y'),
                             (vector(0,1,0),color.blue,'Z')]:
        arrow(pos=origin,axis=direction*1.1,shaftwidth=.045,color=c)
        label(pos=origin+direction*1.35,text=name,box=False,opacity=0,color=c,height=12)
    if cameras_file and Path(cameras_file).exists():
        info=json.loads(Path(cameras_file).read_text(encoding='utf8'))
        for i,cam in enumerate(info.get('cameras',[])):
            if 'center_world' not in cam: continue
            p=v(cam['center_world'])
            box(pos=p,size=vector(.32,.22,.42),color=color.orange)
            delta=v(center)-p
            if delta.mag>1e-9:
                cylinder(pos=p,axis=delta.norm()*.38,radius=.085,color=vector(.8,.55,.2))
            label(pos=p+vector(0,.38,0),text=cam.get('name',f'Camera {i+1}'),
                  height=11,box=False,opacity=0,color=color.orange)
    return world
