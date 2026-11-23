from pathlib import Path
from scene import create_scene
from drone import Drone
from flight import load_trajectory, run_flight
from coordinates import to_vpython

ROOT=Path(__file__).resolve().parent

def main():
    times,points=load_trajectory(ROOT/'trajectory.json')
    world=create_scene(points,ROOT/'cameras.json')
    drone=Drone(to_vpython(points[0]))
    run_flight(world,drone,times,points)

if __name__=='__main__':
    main()
