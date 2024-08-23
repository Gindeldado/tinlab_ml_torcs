from pynput.keyboard import Controller, Listener, Key, KeyCode
import math
from pytocl.main import main
# from math import sqrt
from pytocl.driver import Driver
from pytocl.car import State, Command
import csv

import sys
import os
# print("Current working directory:", os.getcwd())
sys.path.append(os.getcwd())
from logger import data_logger

DEGREE_PER_RADIANS = 180 / math.pi
MPS_PER_KMH = 1000 / 3600

class KeyboardDriver(Driver):
    # Override the `drive` method to create your own driver
    def __init__(self, log=False):
        super().__init__()
        Controller()
        self.log = log
        self.log_this = False

        self.steer_dir = 0.0
        self.steering = 0.0
        # self.brake = False
        self.target_speed = 40
        self.steer_manual = True
        self.accel_state = 2
        self.keymap = {'w':self.log_tog
                      ,'d':self.steer_right
                      ,'s':self.steer_center
                      ,'a':self.steer_left
                      ,Key.up:self.accelerator
                      ,Key.down:self.deacelerator
                      ,Key.space:self.brake
                      }
        self.keys = self.keymap.keys()
        self.thread = Listener(on_press=self.press,on_release=self.release)
        self.running = True
        self.state = {'accel':0,'brake':0,'steer':0,'gear':0,'clutch':0,'focus':0.0,'meta':0,'log':False}
        self.thread.start()
        if log == True:
            self.log_obj = data_logger.log()
            self.log_obj.file_name = "test_corner_test"
            self.log_obj.start()

    def on_shutdown(self):
        self.csvfile.close()
        return super().on_shutdown()

    def press(self, key):
        if key in self.keys:
            self.keymap.get(key)(True)
        elif hasattr(key, 'char'):
            if(key.char in self.keys):
                self.keymap.get(key.char)(True)

    def release(self, key):
        if key in self.keys:
            self.keymap.get(key)(False)
        elif hasattr(key, 'char'):
            if(key.char in self.keys):
                self.keymap.get(key.char)(False)  
        return self.running
    
    def accelerator(self, pressed):
        if(pressed):
            print("gas gas gas")
            self.accel_state = 2
    def brake(self, pressed):
        if(pressed):
            print("brake brake brake")
            self.accel_state = 0
    def deacelerator(self, pressed):
        if(pressed):
            # if self.accel_state == 1:
            #     # brake
            #     print("braking")
            #     self.accel_state = 0
            # else:
            print("deaccelerating")
            self.accel_state = 1

    def steer_left(self, pressed):
        if(pressed):
            print("we are going left!")
            self.steer_dir = 0.6

    def steer_right(self, pressed):
        if(pressed):
            print("we are going right!")
            self.steer_dir = -0.6

    def log_tog(self, pressed):
        if(pressed):
            if self.log_this == False:
                self.log_this = True
                print("LOGGING!")
            else:
                self.log_this = False

    def steer_center(self, pressed):
        if(pressed):
            print("steering ceneter")
            self.steer_dir = 0.0

    def manual_driver(self, carstate: State, command:Command):
        accel_states = {"BRAKE":0, "DE_ACCEL":1, "ACCEL":2, "PASSIVE":3}

        # this handles gear shifting
        self.accelerate(carstate, 330, command)
        
        ### HANDLING ACCELERATION/BRAKING
        if self.accel_state == accel_states["BRAKE"]:
            command.brake = 0.1
            command.accelerator = 0
        elif self.accel_state == accel_states["DE_ACCEL"]:
            command.brake = 0
            command.accelerator = 0
        elif self.accel_state == accel_states["ACCEL"]:
            command.brake = 0
            command.accelerator = 1
        
        self.steer(carstate, self.steer_dir, command)
        print(f"steer value: {self.steer_dir}\ncarpos: {carstate.distance_from_center}")
    
    def drive(self, carstate: State) -> Command:
        command = Command()
        # command.accelerator = 0
        # command.brake = 0
        # command.steering = 0
        
        # if self.state['accel']:
        #     command.accelerator = 1
        #     if carstate.gear > 1 and carstate.rpm > 8000:
        #         self.shift_up(True)
        #     elif carstate.gear == 1 and carstate.rpm > 6000:
        #         self.shift_up(True)
        #     elif carstate.gear < 1 and carstate.rpm > 5000:
        #         self.shift_up(True)
            
        #     if carstate.rpm < 2000:
        #         self.shift_down(True)
        
        # if self.state['brake'] and (not self.state['accel']):
        #     command.brake = 1
        #     if carstate.rpm < 3500:
        #         self.shift_down(True)
        
        # command.accelerator = self.state['accel']
        # command.brake = self.state['brake']
        # command.steering = self.state['steer']
        # command.gear = self.state['gear']
        
        speed_kmh = math.sqrt(carstate.speed_x**2 + carstate.speed_y**2) / MPS_PER_KMH
        # if self.steer_manual == False:
        #     # normal manual driving behaviour
        #     self.steer(carstate, self.steer_dir, command)
        #     self.accelerate(carstate, self.target_speed, command)
        # else:
        #     # normal automatic driving behaviour
        focusPoint = [0, 0]

        for i in range(len(carstate.distances_from_edge)):
            val = carstate.distances_from_edge[i]
            if val > focusPoint[0]:
                focusPoint = [val, i]
                
        brakeZone = focusPoint[0] < speed_kmh / 1.5
        targetSpeed = 40 if brakeZone else 250
        self.accelerate(carstate, targetSpeed, command)
        # self.steer(carstate, 0.0, command)

        
        # self.manual_driver(carstate,command)
        # self.accelerate(carstate, 60, command)
        # if self.steer_dir > 0: 
        #     if carstate.distances_from_edge[0] > 1.5: # steer to left
        #         self.steering += 0.01
        #     else:
        #         self.steering -= 0.03
        # if self.steer_dir < 0:
        #     if carstate.distances_from_edge[1] > 1.5: # steer to left
        #         self.steering -= 0.01
        #     else:
        #         self.steering += 0.03
        # if self.steer_dir == 0:
        #     if carstate.distance_from_center > 0 and self.steering > -0.9:
        #         self.steering = -0.01
        #     if carstate.distance_from_center < 0 and self.steering < 0.9:
        #         self.steering = 0.01
          
            
        # command.steering = self.steering
        self.steer(carstate, self.steer_dir, command)
        if carstate.distances_from_edge[0] < 1.5:
            command.steering -= 0.01
        elif carstate.distances_from_edge[0] < 2.5:
            command.steering -= 0.001

        if carstate.distances_from_edge[18] < 1.5:
            command.steering += 0.01
        elif carstate.distances_from_edge[18] < 2.5:
            command.steering += 0.001

        print(f"steer value: {self.steer_dir}\ncarpos: {carstate.distance_from_center}\n real steer: {command.steering}")
        print(f"corner Left: {carstate.distances_from_edge[0]}\ncorner Right: {carstate.distances_from_edge[18]}")
        ### LOGGING ###
        if self.log == True and self.log_this:
            # fix spd, = 1-0.5-0 = accl ,no accel, brake
            accel_brake_action = 0 
            if command.accelerator == 1 and command.brake == 0:
                accel_brake_action = 1
            elif command.accelerator == 0 and command.brake == 1:
                accel_brake_action = 0
            else:
                accel_brake_action = 0.5
                data = [accel_brake_action,
                        command.steering, 
                        speed_kmh,
                        carstate.angle, 
                        carstate.distance_from_center]
            for e in carstate.distances_from_edge:
                data.append(e)
            for o in carstate.opponents:
                data.append(o)
        
            self.log_obj.log_data(data=data)
        return command
    
if __name__ == '__main__':
    main(KeyboardDriver(True))