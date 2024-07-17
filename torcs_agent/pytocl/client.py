import math
from pytocl.main import main
from pytocl.driver import Driver
from pytocl.car import State, Command
import pytocl.controller

DEGREE_PER_RADIANS = 180 / math.pi
MPS_PER_KMH = 1000 / 3600
DEFAULT_MIN_SPEED = 40
DEFAULT_MAX_SPEED = 330
SENSOR_SPEED_ALTERATIONS = (0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.6, 0.4, 0.2, 0, 0.2, 0.4, 0.6, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8)
SENSOR_ANGLES = (-90, -75, -60, -45, -30, -20, -15, -10, -5, 0, 5, 10, 15, 20, 30, 45, 60, 75, 90)


class Log_agent(Driver):
    def __init__(self):
        super().__init__()
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
        tk_l = carstate.distances_from_edge[:18]    
        tk_r = carstate.distances_from_edge[18:]

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
        if left_close or right_close:
            self.opp_new_ts = 1
            self.opp_spotted = True
            if min(op_f_l) < min(op_f_r):
                print("SIDE DANGER: STEERING right!")
                self.opp_driver_dir = -steer_cor
            else:
                print("SIDE DANGER: STEERING left!")
                self.opp_driver_dir = steer_cor
            return
        if front_close:
            self.opp_new_ts = 1
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

        # 2 situaties


        # print(f"TRACK edge L: {min(tk_l)}\nTRACK edge R: {min(tk_r)}")
        # if min(op_f_l) < close_cont_sides or min(op_f_r)  < close_cont_sides or min(op_f_m ) < close_cont_front:
        #     # Reduce speed and
        #     # decide where to take a fast turn 
        #     if min(op_f_l) < min(op_f_r) and min(op_f_l) < close_cont_sides or min(op_f_r) < close_cont_sides:
        #         print("RIGHT IS SAFE!")
        #         self.opp_driver_dir = steer_cor
        #         self.opp_spotted = True
        #         pass # right is safe
        #     else:
        #         print("left IS SAFE!")
        #         self.opp_driver_dir = steer_cor
        #         self.opp_spotted = True
        #         pass #left is safe 

        #     if min(op_f_m ) < close_cont_front:
        #         print("FRONT IS approching danger!!!")
        #         self.opp_new_ts = 1 # multiplier for new tatgerspeed
        #     else:
        #      pass
        # print(f"Car spotted front right: {min(op_f_r)}")
        # print(f"Car spotted front left: {min(op_f_l)}")
        # print(f"Car spotted front mid: {op_f_m}")
        # print(f"Car distance track right: {min(tk_l)}")
        # print(f"Car distance track left: {min(tk_r)}")

    def un_stuck(self, speed, carstate: State, command: Command):
        car_angle_stuck = abs(carstate.angle) > self.angle_threshold 
        print(f"STUCK_TICKS={self.stuck_ticks} | speed: {speed}")
        if not car_angle_stuck:
            if speed > 10:
                return
        else:
            self.stuck_ticks += 1
            if self.stuck_ticks == 300:
                print("STUCK!")
                self.stuck = True

        if not self.stuck:
            return

        if self.stuck_ticks < 450:
            # reverse
            command.steering = 0.0
            command.gear = -1
            command.accelerator= 0.1 
        elif self.stuck_ticks == 450:
            command.gear = 0
            command.accelerator = 0
            command.brake = 1
        elif self.stuck_ticks < 500:
            command.gear = 1
            command.accelerator = 0.1
            command.brake = 0
        else:
            self.stuck = False
            self.destru = False
            self.stuck_ticks = 0



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
        front_edges = carstate.distances_from_edge[7:12]
        # prev_avr = -1 if len(self.prev_front_edges) == 0 else sum(self.prev_front_edges)/len(self.prev_front_edges)
        # curr_avr = sum(front_edges)/len(front_edges)

        # delta_avr = 0 if prev_avr < 0 else prev_avr/curr_avr  
        # min(front_edges) < 20 accel los
        # min(front_edges) < 15 drop to min snelheid
        # print(f"DIFF: {sum(self.prev_front_edges)/sum(front_edges)}")
        # print(f"prevedges: {self.prev_front_edges}\t speed: {speed_kmh}\t prev_speed: {speed_kmh}\t delta_speed: {self.prev_speed/speed_kmh}")
        # print(f"EDGES MANNN: {front_edges}\tclosest={min(front_edges)}\tavr: {sum(front_edges)/len(front_edges)}")
        # print(f"breakzone={brakeZone} closest edge: {closest_edge[0]}, mps: {speed_kmh / 1.5}")
        
        
        # Steer always to middle op track 
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
        
        # if min(front_edges) < 10:
        #     targetSpeed = DEFAULT_MIN_SPEED
        # else:
        #     targetSpeed = DEFAULT_MAX_SPEED

        
        if self.opp_spotted == True:
            target_track_pos = self.opp_driver_dir
            self.tick_counter += 1
            if self.tick_counter < 200:
                targetSpeed *= self.opp_new_ts
            else:
                if brakeZone == False:
                    targetSpeed = DEFAULT_MAX_SPEED

            if self.tick_counter == 200:
                self.opp_spotted = False
                self.tick_counter = 0
        # nearest_opp
        # print(f"opps: {carstate.opponents}")

        
        self.steer(carstate, target_track_pos, command)
        # print(f"steer: {command.steering}\nticks: {self.tick_counter}")
        

        self.accelerate(carstate, targetSpeed, command)
        # if sum(front_edges)/len(front_edges) > 10 and sum(front_edges)/len(front_edges) < 20:
        #     # dont accelerate
        #     command.accelerator = 0
        # print(f"Car angle axis={carstate.angle}\nEDGES:{carstate.distances_from_edge}")
        # print(f"accel: {command.accelerator}\nbrake: {command.brake}")       
        # self.self_destruct_tick +=1
        # print(f"selfdestruct={self.self_destruct_tick}")
        # if(self.self_destruct_tick > 500 and self.destru == True):
        #     print("SELF DESTRUCT!!")
        #     command.steering = 0.0
        self.prev_front_edges = front_edges
        self.prev_speed = speed_kmh
        return command



if __name__ == '__main__':
    main(Log_agent())