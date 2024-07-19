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
def steer_left(segments, car_pos):
    possible = False
    steer = 0.0
    if(min(segments) > 15):
        if car_pos > 0.8:
            steer = 0.8
    return possible, steer

def car_position(car_pos):
    if car_pos > 0.1:
        return 1    #left
    elif car_pos < -0.1:
        return -1   #right
    else:
        return 0    #mid
class Agent(Driver):
    def __init__(self, log=False):
        super().__init__()
        self.log = log
        self.tick_counter = 0
        self.opp_spotted = False
        self.opp_spotted_dis = 0
        self.opp_driver_dir = 0
        self.opp_new_ts = 0
        self.self_destruct_tick = 0
        self.destru = True
        self.angle_threshold = 10
        self.stuck = False
        self.stuck_ticks = 0
        self.prev_front_edges = [0,0,0,0,0]
        self.prev_speed = 0

        self.buffer_steer_dir = 0
        self.op_tick_counter = 0
        self.op_prev_dis = -1
        self.prev_steering = 0
        self.op_move = -1

        self.start_phase = True
        self.ticks = 0

        self.prev_closest_dis_to_op =0
        if log == True:
            self.log_obj = data_logger.log()
            self.log_obj.file_name = "aalborg_3"
            self.log_obj.start()

    def opponent_avoidance(self, speed, carstate: State, command: Command,in_corner: bool):
        op_A = carstate.opponents[18]            # middel
        op_B = min(carstate.opponents[15:18])    #front left
        op_C = min(carstate.opponents[19:22])    #front right
        op_D = min(carstate.opponents[12:15])    # mid left
        op_E = min(carstate.opponents[22:25])    # mid right

        left_s = min(op_B,op_D)
        right_s = min(op_C,op_E)

        moves = {"DE_ACCEL":0, "BRAKE":1}
        move = -1
        steer_dir = 0

        danger_zone = 10
        warning_zone = 50
        save_zone = []
        front_warning_zone = 50
        minimum_Speed = 40

        if left_s < danger_zone or op_A < danger_zone:
            # check right side
            if right_s > danger_zone:
                # self.steer(carstate, -0.7, command)
                steer_dir = -0.2
                # + slowdown to 60
            else:
                pass# just slow down till we dont come in contact
            	    #   with a,b,c
        if right_s < danger_zone or op_A < danger_zone:
            # check left side
            if left_s > danger_zone:
                # self.steer(carstate, 0.7, command)
                steer_dir = 0.2
                # + slowdown to 60
            else:
                pass# just slow down till we dont come in contact\
                    #   with a,b,c
        dis = min(op_A,op_B,op_C,op_D,op_E)
        return steer_dir, dis
        # infornt opponent in danger zone! 
        if op_A < warning_zone or op_B < warning_zone or op_C < warning_zone:
            self.opp_spotted = True
            self.opp_spotted_dis = min(left_s,right_s)

            in_warning_zone = min(op_A,op_B,op_C) < warning_zone #and speed > minimum_Speed
            in_danger_zone = min(op_A,op_B,op_C) < danger_zone and speed > minimum_Speed
            # brake if were going to fast
            #  !keep a stuck counter if it take to long?
            if in_danger_zone and self.op_prev_dis != -1 and self.op_prev_dis > min(op_A,op_B,op_C):
                # self.op_move = moves["BRAKE"]
                print("TOO FAST SOO BRAKING FOR OPP")
                move = 1
            elif in_warning_zone and self.op_prev_dis != -1 and self.op_prev_dis > min(op_A,op_B,op_C):
                # just deaccel
                move = 2
            else:
                print("THE OTHER CAR MOVES FASTER!!")

            side = self.check_sides(min(op_B,op_D),min(op_C,op_E),warning_zone)
            print(f"min LEFT[{min(op_B,op_D)}]")
            print(f"min RIGHT[{min(op_C,op_E)}]")
            if(min(op_B,op_D) > warning_zone and side == -1) : #left looks free
                self.steer(carstate, 0.6, command)
                print("GOING LEEEFFFFT\nGOING LEEEFFFFT\nGOING LEEEFFFFT\nGOING LEEEFFFFT")
            elif(min(op_C,op_E) > warning_zone and side == 1): #right looks free
                self.steer(carstate, -0.6, command)
                print("GOING rigt\nright\nright\nright")
        # 
        self.op_prev_dis = min(op_A,op_B,op_C,op_D,op_E)
        return move

    def opponent_avoidance_old(self, carstate: State, speed):
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
        # if we go to fast just brake hard
        if min(op_f_m ) < 50 and speed > DEFAULT_MAX_SPEED:
            self.accel_state = 0 # = brake
            return
        
        very_close_front =  min(op_f_m ) < 10
        if very_close_front:
            # drive slower
            self.opp_new_ts = DEFAULT_MIN_SPEED * 2
            self.opp_spotted = True
            if  min(op_f_l) > 20:
                self.opp_new_ts = DEFAULT_MIN_SPEED 
                print("FRONT DANGER: STEERING RIGHT!")
                self.opp_driver_dir = -0.5
            elif min(op_f_r) > 20:
                self.opp_new_ts = DEFAULT_MIN_SPEED 
                print("FRONT DANGER: STEERING center!")
                self.opp_driver_dir = 0.0
            else:
                self.opp_new_ts = DEFAULT_MIN_SPEED 
                print("FRONT DANGER: STEERING Left!")
                self.opp_driver_dir = 0.0
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
        
    def check_sides(self, left, right, zone):
        side = 0
        if left > zone:
            side = -1
        elif right > zone:
            side = 1
        else:
            side = 0
        return side

    def un_stuck(self, speed, carstate: State, command: Command):
        car_angle_stuck = abs(carstate.angle) > self.angle_threshold and speed < 2
        print(f"STUCK_TICKS={self.stuck_ticks} | speed: {speed}")
        
        if self.stuck == False and speed > 20: #weet nii meer wrm?
            self.stuck_ticks = 0

        if not car_angle_stuck and self.stuck == False:
            if speed > 5:
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
            # break and to N
            command.gear = 0
            command.accelerator = 0
            command.brake = 1
        elif self.stuck_ticks < 350:
            # start slowly acc
            command.gear = 1
            command.accelerator = 0.3
            command.brake = 0
        else:
            # reset
            self.stuck = False
            self.destru = False
            self.stuck_ticks = 0

    def better_corner_taking(self, carstate: State, command: Command):
        front = [#carstate.distances_from_edge[7],
                 carstate.distances_from_edge[8],
                 carstate.distances_from_edge[10],
                #carstate.distances_from_edge[11]
                ]
        take_corner_thresh = 45
        print(f"carpos:{carstate.distance_from_center}")
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

        self.un_stuck(speed_kmh,carstate,command)
        if self.stuck == True:
            return command

        ### HANDLING CORNERS ###
        accel_states = {"BRAKE":0, "DE_ACCEL":1, "ACCEL":2, "PASSIVE":3}
        self.accel_state = accel_states["ACCEL"]
        angl_good =  abs(carstate.angle) < 7
        corner_dis, brake_dis = self.better_corner_taking(carstate,command)

        # if we are at minimum speed just slowly take corner
        if corner_dis < 40 and speed_kmh > 55 and speed_kmh < 80:
            self.accel_state = accel_states["DE_ACCEL"]
        # almost at edge so better brake! if we are to fast 
        elif corner_dis < 40 and angl_good and speed_kmh > 80:
            self.accel_state = accel_states["BRAKE"]
        else:
            pass
       
        if speed_kmh > 220 and corner_dis < 70:
            print("TOO FAST AND CLOSSSEE!!!\nTOO FAST AND CLOSSSEE!!!\nTOO FAST AND CLOSSSEE!!!\nTOO FAST AND CLOSSSEE!!!\nTOO FAST AND CLOSSSEE!!!\nTOO FAST AND CLOSSSEE!!!\n")
            self.accel_state = accel_states["DE_ACCEL"]
        elif speed_kmh > 120 and corner_dis < 56.5:
            self.accel_state = accel_states["BRAKE"]

        ### HANDLING OPPONENTS
        # segemnete alleen van boven half rond zijn 18
        # start op 8 0-35 012 3435
        seg_a = [carstate.opponents[17],carstate.opponents[18]] #-10 - 10 deg
        seg_b = [carstate.opponents[15], carstate.opponents[16]]  # -30 to -10 degrees
        seg_b1 = [carstate.opponents[19], carstate.opponents[20]]  # 10 to 30 degrees
        seg_c = [carstate.opponents[13], carstate.opponents[14]]  # -50 to -30 degrees
        seg_c1 = [carstate.opponents[21], carstate.opponents[22]]  # 30 to 50 degrees
        seg_d = [carstate.opponents[11], carstate.opponents[12]]  # -70 to -50 degrees
        seg_d1 = [carstate.opponents[23], carstate.opponents[24]]  # 50 to 70 degrees
        seg_e = [carstate.opponents[9], carstate.opponents[10]]   # -90 to -70 degrees
        seg_e1 = [carstate.opponents[25], carstate.opponents[26]]  # 70 to 90 degrees

        #1=links,2=rechts,3=beide
        auto_spotted_front_far = 0 
        steer = 0.0
        max_dis_front = 20
        max_dis_front_side = 40
        correction_steer = 0.7
        car_pos_max = 0.6

        if (min(carstate.opponents[15],carstate.opponents[16],carstate.opponents[17])) < max_dis_front \
            or min(carstate.opponents[14],carstate.opponents[13],carstate.opponents[12]) < max_dis_front_side:
            auto_spotted_front_far += 1
        if (min(carstate.opponents[18],carstate.opponents[19],carstate.opponents[20])) < max_dis_front \
            or min(carstate.opponents[21],carstate.opponents[22],carstate.opponents[23]) < max_dis_front_side:
            auto_spotted_front_far += 2

        if auto_spotted_front_far == 0:
            print("NOTHING")
        if auto_spotted_front_far == 1:
            print("LEFT")
            if carstate.distance_from_center < 0 and carstate.distance_from_center < -car_pos_max:
                # Auto zit teveel rechts 
                # CHECK LINKS allowed
                if min(min(seg_e), min(seg_d)) > max_dis_front_side: 
                    print("teveel rechts dus we gaan links" )
                    steer = correction_steer
            else:
                print("we gaan rechts" )
                steer = -correction_steer
        if auto_spotted_front_far == 2:
            print("RIGHT") 
            if carstate.distance_from_center > 0 and carstate.distance_from_center > car_pos_max:
                # Auto zit teveel links 
                # CHECK rechts allowed
                if min(min(seg_e1), min(seg_d1)) > max_dis_front_side:
                    print("teveel links dus we gaan rechts" )
                    steer = -correction_steer
            else:
                print("we gaan links" )
                steer = correction_steer

        # print(f"car pos:[{carstate.distance_from_center}] (distance_edge){distance_from_edge} [freespace]({free_space})")
        print(f"POS: {carstate.distance_from_center}")
        
        ### apply default accel and steer(could have been modified by op)
        self.accelerate(carstate, DEFAULT_MAX_SPEED, command)
        self.steer(carstate, steer, command)

        ### HANDLING ACCELERATION/BRAKING
        if self.accel_state == accel_states["BRAKE"]:
            command.brake = 1
            command.accelerator = 0
        elif self.accel_state == accel_states["DE_ACCEL"]:
            command.brake = 0
            command.accelerator = 0
        else:
            if(abs(carstate.angle) < 7) and speed_kmh < DEFAULT_MAX_SPEED:
                command.accelerator = 1
                command.brake = 0
            
        
        ### LOGGING ###
        if self.log == True:
            # fix spd, = 1-0.5-0 = accl ,no accel, brake
            spd = 1 if DEFAULT_MAX_SPEED == DEFAULT_MAX_SPEED else 0
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

        # self.op_tick_counter +
        self.prev_steering = command.steering
        return command



if __name__ == '__main__':
    main(Agent(log=False))