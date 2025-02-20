import argparse
from dataclasses import dataclass
from peaceful_pie.unity_comms import UnityComms
import requests

@dataclass
class SubPos:
    x: float
    y: float
    z: float

@dataclass
class SubVel:
    M1 : float
    M2 : float
    M3 : float
    M4 : float
    M5 : float
    M6 : float
    M7 : float
    M8 : float

@dataclass
class SubData:
    claw: int
    torp1: bool
    torp2: bool

class Controller:
    def __init__(self, args: argparse.Namespace) -> None:
        self.unity_comms = UnityComms(port=args.port)

        self.controller_url = "http://localhost:5001/outputs"

        self.in_max = 2000
        self.in_min = 1000
        self.out_max = 1.0
        self.out_min = -1.0

    def get_sub_pos(self) -> SubPos:
        return self.unity_comms.GetPos(ResultClass=SubPos)
    
    def get_sub_vel(self) -> SubVel:
        return self.unity_comms.GetVel(ResultClass=SubVel)
    
    def set_sub_vel(self, vel: SubVel) -> None:
        self.unity_comms.SetVel(vel)
    
    def get_sub_depth(self) -> float:
        return self.unity_comms.GetDistanceToFloor()
    
    def mapping(self, val : int) -> float:
        return (val - self.in_min) * (self.out_max - self.out_min) / (self.in_max - self.in_min) + self.out_min

    def get_controller_vels(self) -> SubData:
        response = requests.get(self.controller_url)
        DOFRawData = response.json()
        for key in DOFRawData.keys():
            DOFRawData[key] = self.mapping(DOFRawData[key])
        return SubVel(DOFRawData['M1'], DOFRawData['M2'], DOFRawData['M3'], \
                      DOFRawData['M4'], DOFRawData['M5'], DOFRawData['M6'],\
                      DOFRawData['M7'], DOFRawData['M8'])

    def debug(self, pos:SubPos, vel:SubVel, depth:float) -> None:
        print(f"Pos: {pos}\nVel: {vel}\nDepth: {depth}")
    
    def run(self) -> None:
        while True:
            pos = self.get_sub_pos()
            vel = self.get_sub_vel()
            depth = self.get_sub_depth()
            controller_vels = self.get_controller_vels()
            self.debug(pos, vel, depth)
            self.set_sub_vel(controller_vels)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=5000)
    args = parser.parse_args()
    controller = Controller(args)
    controller.run()
