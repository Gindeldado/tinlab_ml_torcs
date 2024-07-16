import math
from pytocl.main import main
from pytocl.driver import Driver
from pytocl.car import State, Command
import pytocl.controller

DEGREE_PER_RADIANS = 180 / math.pi
MPS_PER_KMH = 1000 / 3600
DEFAULT_MIN_SPEED = 40
DEFAULT_MAX_SPEED = 250
SENSOR_SPEED_ALTERATIONS = (0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.6, 0.4, 0.2, 0, 0.2, 0.4, 0.6, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8)
SENSOR_ANGLES = (-90, -75, -60, -45, -30, -20, -15, -10, -5, 0, 5, 10, 15, 20, 30, 45, 60, 75, 90)

class Log_agent(Driver):
    def __init__(self):
        super().__init__()

    def analyse_track(track_edge, angle):
        alpha = 0               # angle of curvature
        sense = 1               # pos or neg curve
        farthest = None, None   # farthest point
        ps = list()             # calc points
        realt = list()          # sensor readings
    
        # convert angles to rad
        sangsradang = [(math.pi * X / 180.0) + angle for X in SENSOR_ANGLES]
        pass

    def drive( self, carstate: State) -> Command:
        command = Command()
        ''' ### Steering around corners ###
        This is done with processing data of edge sensors
        If a edge sensor > prev measured edge sensor,
        set focusPoint of detected value and sensor. 

        This gets the closest edge in focuspoint
        Breakzone = if focuspoint < speed(m/s) / 1.5 
        TRUE = set speed to minumspeed for easy turn.    
        FALSE = race full speed!
        '''
        speed_mps = math.sqrt(carstate.speed_x**2 + carstate.speed_y**2) / MPS_PER_KMH
        closest_edge = [0,0]    #[distance to edge, edge sensor]

        for i in range(len(carstate.distances_from_edge)):
            val = carstate.distances_from_edge[i]
            if val > closest_edge[0]:
                closest_edge = [val, i]
        brakeZone = closest_edge[0] < speed_mps / 1

        ''' ### Opponents overtaking and avoidance ###
        1. Check opponents sensors (divide them in groups)
        2. Get nearest opponent and (group with) farthest opp
        3. Reduce speed on how close opp if in front or
            skip if opp is in back
        4. Steer to direction with less opps
        '''
        # nearest_opp
        # Steer always to middle op track 
        target_track_pos = 0.0
        self.steer(carstate, target_track_pos, command)

        if brakeZone:
            targetSpeed = DEFAULT_MIN_SPEED
        else:
            targetSpeed = DEFAULT_MAX_SPEED
        self.accelerate(carstate, targetSpeed, command)

        return command



if __name__ == '__main__':
    main(Log_agent())