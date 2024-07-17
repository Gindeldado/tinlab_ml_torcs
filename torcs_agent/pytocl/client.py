import math
from pytocl.main import main
from pytocl.driver import Driver
from pytocl.car import State, Command

import sys
import os
# print("Current working directory:", os.getcwd())
sys.path.append(os.getcwd())
# print("Python path after modification:", sys.path)

from logger import data_logger
DEGREE_PER_RADIANS = 180 / math.pi
MPS_PER_KMH = 1000 / 3600
DEFAULT_MIN_SPEED = 40
DEFAULT_MAX_SPEED = 330
SENSOR_SPEED_ALTERATIONS = (0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.6, 0.4, 0.2, 0, 0.2, 0.4, 0.6, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8)
SENSOR_ANGLES = (-90, -75, -60, -45, -30, -20, -15, -10, -5, 0, 5, 10, 15, 20, 30, 45, 60, 75, 90)

# class Edge():
#     def __init__(self):
#         self.degree = 0.0
#         self.danger_level = 0
    
#     def get_danger(dist :int) -> int:


class Agent(Driver):
    def __init__(self, log=False):
        super().__init__()
        self.log = log
        self.tick_counter = 0
        self.opp_spotted = False
        self.opp_driver_dir = 0
        self.opp_new_ts = 0
        self.self_destruct_tick = 0
        self.destru = True
        self.angle_threshold = 10
        self.stuck = False
        self.stuck_ticks = 0
        self.prev_front_edges = [0,0,0,0,0]
        self.prev_speed = 0

        if log == True:
            self.log_obj = data_logger.log()
            self.log_obj.file_name = "aalborg_3"
            self.log_obj.start()

    def opponent_avoidance(self, carstate: State):
        ''' ### Opponents overtaking and avoidance ###
        1. Check opponents sensors (divide them in groups)
        2. Get nearest opponent and (group with) farthest opp
        3. Reduce speed on how close opp if in front or
            skip if opp is in back
        4. Steer to direction with less opps
        '''
        op_f_m = carstate.opponents[16:21] # front middel 
        op_f_r = carstate.opponents[19:23] # front right side
        op_f_l = carstate.opponents[14:18] # front left side
        # tk_l = carstate.distances_from_edge[:18]    
        # tk_r = carstate.distances_from_edge[18:]

        close_cont_sides = 10
        close_cont_front = 50
        steer_cor = 0.7
        reduce_speed_factor = 1

        '''
        Je hebt 2 situaties:
        1. opp dichtbij links of rechts
        - rem 
        - kies veilige richting 
        2. opp voor en kinda verweg 
        '''
        left_close = min(op_f_l) < close_cont_sides
        right_close = min(op_f_r) < close_cont_sides   
        front_close = min(op_f_m ) < close_cont_front
        very_close_front =  min(op_f_m ) < 10
        if very_close_front:
            # drive slower
            self.opp_new_ts = DEFAULT_MIN_SPEED * 2
            self.opp_spotted = True
            if min(op_f_l) < min(op_f_r):
                print("FRONT DANGER: STEERING RIGHT!")
                self.opp_driver_dir = -0.5
            elif min(op_f_l) < 10 and min(op_f_r) < 10:
                self.opp_new_ts = DEFAULT_MIN_SPEED 
                print("FRONT DANGER: STEERING center!")
                self.opp_driver_dir = 0.0
            else:
                print("FRONT DANGER: STEERING Left!")
                self.opp_driver_dir = 0.5
            return
        if left_close or right_close:
            self.opp_new_ts = DEFAULT_MAX_SPEED
            self.opp_spotted = True
            if min(op_f_l) < min(op_f_r):
                print("SIDE DANGER: STEERING right!")
                self.opp_driver_dir = -steer_cor
            else:
                print("SIDE DANGER: STEERING left!")
                self.opp_driver_dir = steer_cor
            return
        if front_close:
            self.opp_new_ts = DEFAULT_MAX_SPEED
            # it should also just accelrate more?
            self.opp_spotted = True
            # it should maybe ride longer to the side?
            # and ignore the steering dir side for brakingzone?
            if min(op_f_l) < min(op_f_r):
                print("FRONT DANGER: STEERING RIGHT!")
                self.opp_driver_dir = -steer_cor
            else:
                print("FRONT DANGER: STEERING left!")
                self.opp_driver_dir = steer_cor
            return

    def un_stuck(self, speed, carstate: State, command: Command):
        car_angle_stuck = abs(carstate.angle) > self.angle_threshold and speed < 1
        # print(f"STUCK_TICKS={self.stuck_ticks} | speed: {speed}")
        if not car_angle_stuck:
            if speed > 10:
                return
        else:
            self.stuck_ticks += 1
            if self.stuck_ticks == 200:
                print("STUCK!")
                self.stuck = True

        if not self.stuck:
            return

        if self.stuck_ticks < 300:
            # reverse
            command.steering = 0.0
            command.gear = -1
            command.accelerator= 0.3 
        elif self.stuck_ticks == 300:
            command.gear = 0
            command.accelerator = 0
            command.brake = 1
        elif self.stuck_ticks < 350:
            command.gear = 1
            command.accelerator = 0.1
            command.brake = 0
        else:
            self.stuck = False
            self.destru = False
            self.stuck_ticks = 0

    def better_corner_taking(self, carstate: State, command: Command):
        # print("taking corner")
        left_side = carstate.distances_from_edge[:9]
        center = carstate.distances_from_edge[9]
        right_side = carstate.distances_from_edge[10:]

        front = [#carstate.distances_from_edge[7],
                 carstate.distances_from_edge[8],
                 carstate.distances_from_edge[10],
                #carstate.distances_from_edge[11]
                ]

        take_corner_thresh = 45
        mid = len(front) // 2
        # check eerst of het in range komt can corner taking!
        # print(f"angle car({carstate.angle}) avr dis: {sum(front)/len(front)}, left[{sum(front[:mid])}] right[{sum(front[mid:])}]")
        take_corner = sum(front)/len(front) < take_corner_thresh
        # if take_corner:
        #     if sum(front[:mid]) > sum(front[mid:]): #or [0]/[2] = "een bep pos helling"
        #         print("rij naar rechts, dus buiten bocht")
        #     else:
        #         print("rij naar links, dus buiten bocht")

        return sum(front)/len(front), take_corner_thresh
        # totdat een edge sensor van de andere kant x is 
        # neem dan de andere kant 


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
        speed_kmh = math.sqrt(carstate.speed_x**2 + carstate.speed_y**2) / MPS_PER_KMH
        closest_edge = [0,0]    #[distance to edge, edge sensor]

        if self.stuck == False and speed_kmh > 20:
            self.stuck_ticks = 0

        self.un_stuck(speed_kmh,carstate,command)
        if self.stuck == True:
            return command
        
        for i in range(len(carstate.distances_from_edge)):
            val = carstate.distances_from_edge[i]
            if val > closest_edge[0]:
                closest_edge = [val, i]
        brakeZone = closest_edge[0] < speed_kmh / 1.5

        # [9] = 0deg 78910 11 12
        # front_edges = carstate.distances_from_edge[7:12]

        target_track_pos = 0.0

        ''' ### Opponents overtaking and avoidance ###
        1. Check opponents sensors (divide them in groups)
        2. Get nearest opponent and (group with) farthest opp
        3. Reduce speed on how close opp if in front or
            skip if opp is in back
        4. Steer to direction with less opps
        '''

        self.opponent_avoidance(carstate)

        if brakeZone:
            targetSpeed = DEFAULT_MIN_SPEED#max(DEFAULT_MIN_SPEED, speed_kmh-5)
        else:
            targetSpeed = DEFAULT_MAX_SPEED

        
        if self.opp_spotted == True:
            target_track_pos = self.opp_driver_dir
            self.tick_counter += 1
            if self.tick_counter < 400:
                targetSpeed == self.opp_new_ts
            if brakeZone == True:
                targetSpeed = DEFAULT_MIN_SPEED

            if self.tick_counter == 400:
                self.opp_spotted = False
                self.tick_counter = 0
        
        self.steer(carstate, target_track_pos, command)
        # print(f"steer: {command.steering}\nticks: {self.tick_counter}")
        

        self.accelerate(carstate, targetSpeed, command)

        if self.log == True:
            spd = 1 if targetSpeed == DEFAULT_MAX_SPEED else 0
            data = [spd,
                    command.steering, 
                    speed_kmh,
                    carstate.angle, 
                    carstate.distance_from_center]
            for e in carstate.distances_from_edge:
                data.append(e)
            for o in carstate.opponents[14:23]:
                data.append(o)
        
            self.log_obj.log_data(data=data)

        accel_states = {"BRAKE":0, "DE_ACCEL":1, "ACCEL":2, "SLOW_BRAKE":3}
        accel_state = 2
        angl_good =  abs(carstate.angle) < 7
        corner_dis, brake_dis = self.better_corner_taking(carstate,command)
        # if corner_dis < 50 and corner_dis > 40 and angl_good and speed_kmh > 100:
        #     accel_state = accel_states["DE-ACCEL"] 
        # elif speed_kmh > 250 and corner_dis < 90:
        #     accel_state = accel_states["DE-ACCEL"] 
        

        # if we are at minimum speed just slowly take corner
        if corner_dis < 40 and speed_kmh > 55 and speed_kmh < 80:
            accel_state = accel_states["DE_ACCEL"]
        # almost at edge so better brake! if we are to fast 
        elif corner_dis < 40 and angl_good and speed_kmh > 80:
            accel_state = accel_states["BRAKE"]
        else:
            pass
       
        if speed_kmh > 220 and corner_dis < 66:
            print("TOO FAST AND CLOSSSEE!!!\nTOO FAST AND CLOSSSEE!!!\nTOO FAST AND CLOSSSEE!!!\nTOO FAST AND CLOSSSEE!!!\nTOO FAST AND CLOSSSEE!!!\nTOO FAST AND CLOSSSEE!!!\n")
            accel_state = accel_states["DE_ACCEL"]
        elif speed_kmh > 120 and corner_dis < 56.5:
            accel_state = accel_states["BRAKE"]

        if accel_state == accel_states["BRAKE"]:
            command.brake = 1
            command.accelerator = 0
        elif accel_state == accel_states["DE_ACCEL"]:
            command.brake = 0
            command.accelerator = 0
        elif accel_state == accel_states["SLOW_BRAKE"]:
            command.brake = 0.3
            command.accelerator = 0
        else:
            command.accelerator = 1
            command.brake = 0

        print(f"carspeed: [{speed_kmh}]\t corner_dis:[{corner_dis}]")
        return command



if __name__ == '__main__':
    main(Agent(log=False))