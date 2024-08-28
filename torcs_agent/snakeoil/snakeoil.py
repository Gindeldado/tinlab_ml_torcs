#!/usr/bin/python
# snakeoil.py
# Chris X Edwards <snakeoil@xed.ch>
# Snake Oil is a Python library for interfacing with a TORCS
# race car simulator which has been patched with the server
# extentions used in the Simulated Car Racing competitions.
# http://scr.geccocompetitions.com/
#
# To use it, you must import it and create a "drive()" function.
# This will take care of option handling and server connecting, etc.
# To see how to write your own client do something like this which is
# a complete working client:
# /-----------------------------------------------\
# |#!/usr/bin/python                              |
# |import snakeoil                                |
# |if __name__ == "__main__":                     |
# |    C= snakeoil.Client()                       |
# |    for step in xrange(C.maxSteps,0,-1):       |
# |        C.get_servers_input()                  |
# |        snakeoil.drive_example(C)              |
# |        C.respond_to_server()                  |
# |    C.shutdown()                               |
# \-----------------------------------------------/
# This should then be a full featured client. The next step is to
# replace 'snakeoil.drive_example()' with your own. There is a
# dictionary which holds various option values (see `default_options`
# variable for all the details) but you probably only need a few
# things from it. Mainly the `trackname` and `stage` are important
# when developing a strategic bot. 
#
# This dictionary also contains a ServerState object
# (key=S) and a DriverAction object (key=R for response). This allows
# you to get at all the information sent by the server and to easily
# formulate your reply. These objects contain a member dictionary "d"
# (for data dictionary) which contain key value pairs based on the
# server's syntax. Therefore, you can read the following:
#    angle, curLapTime, damage, distFromStart, distRaced, focus,
#    fuel, gear, lastLapTime, opponents, racePos, rpm,
#    speedX, speedY, speedZ, track, trackPos, wheelSpinVel, z
# The syntax specifically would be something like:
#    X= o[S.d['tracPos']]
# And you can set the following:
#    accel, brake, clutch, gear, steer, focus, meta 
# The syntax is:  
#     o[R.d['steer']]= X
# Note that it is 'steer' and not 'steering' as described in the manual!
# All values should be sensible for their type, including lists being lists.
# See the SCR manual or http://xed.ch/help/torcs.html for details.
#
# If you just run the snakeoil.py base library itself it will implement a
# serviceable client with a demonstration drive function that is
# sufficient for getting around most tracks.
# Try `snakeoil.py --help` to get started.

import socket 
import sys
import getopt
import math
PI= 3.14159265359

# Initialize help messages
ophelp=  'Options:\n'
ophelp+= ' --host, -H <host>    TORCS server host. [localhost]\n'
ophelp+= ' --port, -p <port>    TORCS port. [3001]\n'
ophelp+= ' --id, -i <id>        ID for server. [SCR]\n'
ophelp+= ' --steps, -m <#>      Maximum simulation steps. 1 sec ~ 50 steps. [100000]\n'
ophelp+= ' --episodes, -e <#>   Maximum learning episodes. [1]\n'
ophelp+= ' --track, -t <track>  Your name for this track. Used for learning. [unknown]\n'
ophelp+= ' --stage, -s <#>      0=warm up, 1=qualifying, 2=race, 3=unknown. [3]\n'
ophelp+= ' --debug, -d          Output full telemetry.\n'
ophelp+= ' --help, -h           Show this help.\n'
ophelp+= ' --version, -v        Show current version.'
usage= 'Usage: %s [ophelp [optargs]] \n' % sys.argv[0]
usage= usage + ophelp
version= "20130505-2"

class Client():
    def __init__(self,H=None,p=None,i=None,e=None,t=None,s=None,d=None):
        # If you don't like the option defaults,  change them here.
        self.host= 'localhost'
        self.port= 3001
        self.sid= 'SCR'
        self.maxEpisodes=1
        self.trackname= 'unknown'
        self.stage= 3
        self.debug= False
        self.maxSteps= 100000  # 50steps/second
        self.parse_the_command_line()
        if H: self.host= H
        if p: self.port= p
        if i: self.sid= i
        if e: self.maxEpisodes= e
        if t: self.trackname= t
        if s: self.stage= s
        if d: self.debug= d
        self.S= ServerState()
        self.R= DriverAction()
        self.setup_connection()

    def setup_connection(self):
        # == Set Up UDP Socket ==
        try:
            self.so= socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        except socket.error as emsg:
            print ('Error: Could not create socket...')
            sys.exit(-1)
        # == Initialize Connection To Server ==
        self.so.settimeout(1)
        while True:
            a= "-90 -75 -60 -45 -30 -20 -15 -10 -5 0 5 10 15 20 30 45 60 75 90"
            initmsg='%s(init %s)' % (self.sid,a)

            try:
                self.so.sendto(initmsg.encode(), (self.host, self.port))
            except socket.error as emsg:
                sys.exit(-1)
            sockdata= bytes()
            try:
                sockdata,addr= self.so.recvfrom(1024)
            except socket.error as emsg:
                print ("Waiting for server............")
            if '***identified***' in sockdata.decode():
                print ("Client connected..............")
                break

    def parse_the_command_line(self):
        try:
            (opts, args) = getopt.getopt(sys.argv[1:], 'H:p:i:m:e:t:s:dhv',
                       ['host=','port=','id=','steps=',
                        'episodes=','track=','stage=',
                        'debug','help','version'])
        except getopt.error as why:
            print(f'getopt error: {why}\n{usage}')
            sys.exit(-1)
        try:
            for opt in opts:
                if opt[0] == '-h' or opt[0] == '--help':
                    print (usage)
                    sys.exit(0)
                if opt[0] == '-d' or opt[0] == '--debug':
                    self.debug= True
                if opt[0] == '-H' or opt[0] == '--host':
                    self.host= opt[1]
                if opt[0] == '-i' or opt[0] == '--id':
                    self.sid= opt[1]
                if opt[0] == '-t' or opt[0] == '--track':
                    self.trackname= opt[1]
                if opt[0] == '-s' or opt[0] == '--stage':
                    self.stage= opt[1]
                if opt[0] == '-p' or opt[0] == '--port':
                    self.port= int(opt[1])
                if opt[0] == '-e' or opt[0] == '--episodes':
                    self.maxEpisodes= int(opt[1])
                if opt[0] == '-m' or opt[0] == '--steps':
                    self.maxSteps= int(opt[1])
                if opt[0] == '-v' or opt[0] == '--version':
                    print(f'{sys.argv[0]}\n{version}')
                    sys.exit(0)
        except ValueError as why:
            print(f"Bad parameter '{opt[1]}' for option {opt[0]}: {why}\n{usage}")
            sys.exit(-1)
        if len(args) > 0:
            print(f"Superflous input? {', '.join(args)}\n{usage}")
            sys.exit(-1)

    def get_servers_input(self):
        '''Server's input is stored in a ServerState object'''
        if not self.so: return
        sockdata= bytes()
        while True:
            try:
                # Receive server data 
                sockdata,addr= self.so.recvfrom(1024)
            except socket.error as emsg:
                print ("Waiting for data..............")
            if '***identified***' in sockdata.decode():
                print ("Client connected..............")
                continue
            elif '***shutdown***' in sockdata.decode():
                print(f"Server has stopped the race. You were in {self.S.d['racePos']} place.")             
                return
            elif '***restart***' in sockdata.decode():
                # What do I do here?
                print ("Server has restarted the race.")
                # I haven't actually caught the server doing this.
                self.shutdown()
                return
            elif not sockdata: # Empty?
                continue       # Try again.
            else:
                self.S.parse_server_str(sockdata.decode())
                if self.debug: print (self.S)
                break # Can now return from this function.

    def respond_to_server(self):
        if not self.so: return
        if self.debug: print (self.R)
        try:
            self.so.sendto(repr(self.R).encode(), (self.host, self.port))
        except socket.error as emsg:
            print(f"Error sending to server: {emsg[1]} Message {str(emsg[0])}")
            sys.exit(-1)

    def shutdown(self):
        if not self.so: return
        print(f"Race terminated or {self.maxSteps} steps elapsed. Shutting down.")
        self.so.close()
        self.so= None
        #sys.exit() # No need for this really.

class ServerState():
    'What the server is reporting right now.'
    def __init__(self):
        self.servstr= str()
        self.d= dict()

    def parse_server_str(self, server_string):
        'parse the server string'
        self.servstr= server_string.strip()[:-1]
        sslisted= self.servstr.strip().lstrip('(').rstrip(')').split(')(')
        for i in sslisted:
            w= i.split(' ')
            self.d[w[0]]= destringify(w[1:])

    def __repr__(self):
        out= str()
        for k in sorted(self.d):
            strout= str(self.d[k])
            if type(self.d[k]) is list:
                strlist= [str(i) for i in self.d[k]]
                strout= ', '.join(strlist)
            out+= "%s: %s\n" % (k,strout)
        return out

class DriverAction():
    '''What the driver is intending to do (i.e. send to the server).
    Composes something like this for the server:
    (accel 1)(brake 0)(gear 1)(steer 0)(clutch 0)(focus 0)(meta 0) or
    (accel 1)(brake 0)(gear 1)(steer 0)(clutch 0)(focus -90 -45 0 45 90)(meta 0)'''
    def __init__(self):
       self.actionstr= str()
       # "d" is for data dictionary.
       self.d= { 'accel':0.2,
                   'brake':0,
                  'clutch':0,
                    'gear':1,
                   'steer':0,
                   'focus':[-90,-45,0,45,90],
                    'meta':0 
                    }

    def __repr__(self):
        out= str()
        for k in self.d:
            out+= '('+k+' '
            v= self.d[k]
            if not type(v) == list:
                out+= '%.3f' % v
            else:
                out+= ' '.join([str(x) for x in v])
            out+= ')'
        return out
        return out+'\n'

# == Misc Utility Functions
def destringify(s):
    '''makes a string into a value or a list of strings into a list of
    values (if possible)'''
    if not s: return s
    if type(s) is str:
        try:
            return float(s)
        except ValueError:
            print(f'Could not find a value in{s}')
            return s
    elif type(s) is list:
        if len(s) < 2:
            return destringify(s[0])
        else:
            return [destringify(i) for i in s]

def clip(v,lo,hi):
    if v<lo: return lo
    elif v>hi: return hi
    else: return v

def improved_steering_control(S, R, target_speed):
        PI = math.pi
        # Steer to Corner
        R['steer'] = S['angle'] * 10 / PI
        print(f"[steering module] Initial steering based on angle: {R['steer']}")

        # Steer to Center
        R['steer'] -= S['trackPos'] * 0.70
        print(f"[steering module] Steering after track position adjustment: {R['steer']}")

        # High-Speed Adjustment Using Sensor Data
        if S['speedX'] > 90 * 0.8:
            # Get sensor readings (assuming S['track'] holds the sensor distances)
            sensor_readings = S['track']
            angles = [-90, -75, -60, -45, -30, -20, -15, -10, -5, 0, 5, 10, 15, 20, 30, 45, 60, 75, 90]

            # Calculate a weighted adjustment based on sensor data
            weighted_sum = 0
            weight_total = 0
            for i in range(len(sensor_readings)):
                if sensor_readings[i] != -1:
                    angle = angles[i]
                    weight = 1 / (abs(angle) + 1)  # Weight inversely proportional to angle
                    weighted_sum += sensor_readings[i] * weight
                    weight_total += weight

            if weight_total > 0:
                average_distance = weighted_sum / weight_total
            else:
                average_distance = 100  # Default value if all sensors are off track

            # Adjust steering based on the average distance
            # The correction factor can be tuned for better performance
            correction_factor = 0.07
            if average_distance < 50:
                R['steer'] -= correction_factor * (50 - average_distance) / 50
            else:
                R['steer'] += correction_factor * (average_distance - 50) / 150
            print(f"[steering module] Steering after high-speed adjustment: {R['steer']}")

            # Clip the steering value to ensure it's within the valid range
            R['steer'] = clip(R['steer'], -1, 1)
            print(f"[steering module] Final clipped steering: {R['steer']}")

def improved_throttle_control(S, R, target_speed):
    PI = math.pi

    # Throttle Control Based on Target Speed and Steering
    if S['speedX'] < target_speed - (R['steer'] * 50):
        R['accel'] += 0.01
        print("[throttle control] increasing speed!!")
    else:
        print("[throttle control] decreasing speed!")
        R['accel'] -= 0.01


    # Traction Control System
    if ((S['wheelSpinVel'][2] + S['wheelSpinVel'][3]) -
       (S['wheelSpinVel'][0] + S['wheelSpinVel'][1]) > 5):
        R['accel'] -= 0.2

    # Additional Speed Adjustment Based on Track Curvature
    sensor_readings = S['track']
    angles = [-90, -75, -60, -45, -30, -20, -15, -10, -5, 0, 5, 10, 15, 20, 30, 45, 60, 75, 90]

    # Calculate a weighted curvature measure
    weighted_sum = 0
    weight_total = 0
    for i in range(len(sensor_readings)):
        if sensor_readings[i] != -1:
            angle = angles[i]
            if abs(angle) <= 10:
                weight = 1  # Highest weight for front-center sensors
            elif abs(angle) <= 30:
                weight = 0.01  # Medium weight for front-side sensors
            else:
                weight = 0.001  # Lowest weight for far side sensors
            # weight = 1 / (abs(angle) + 1)  # Weight inversely proportional to angle
            weighted_sum += sensor_readings[i] * weight
            weight_total += weight

    if weight_total > 0:
        average_distance = weighted_sum / weight_total
    else:
        average_distance = -1  # Default value if all sensors are off track

    # Adjust throttle based on curvature
    # Reduce speed more aggressively for tight corners (small average distance)
    curvature_factor = 0.5  # Factor to control the influence of curvature
    if average_distance <  30 and S['speedX'] > 55:
        print("[throttle control] TO CLOSE TO BOCHT!!")
        R['accel'] -= curvature_factor * (30 - average_distance) / 30
    else:
        R['accel'] += (curvature_factor * (average_distance - 30) / 90)*2
        print("[throttle control] NO BOCHT IN SIGHT!!")
    print(f"[throttle control] Throttle after curvature adjustment: {R['accel']}")
    print(f"[throttle control] avr_dis_to_track: {average_distance}")
    print(f"[throttle control] speed: {S['speedX']} ")

    R['brake'] = 0
    front_dis = min([S["track"][9],S["track"][9],S["track"][9]])
    # Brake when to close to edge
    if front_dis < 50 and S['speedX'] > 40 and S['speedX'] < 80:
        print("[throttle control] Front close: YES, no braking")
        # R['accel'] = 0
        R['brake']= 0
    elif front_dis < 50 and S['speedX'] > 80:
        print("[throttle control] Front close: YES and we are fast")
        R['accel'] = 0
        R['brake'] = 1
    else:
        print("[throttle control] Front close: NO")
    
    if S['speedX']  > 220 and front_dis < 70:
        print("[throttle control] TOO FAST AND CLOSSSEE STOP ACCEL")
        R['accel'] = 0
        R['brake'] = 0
    elif S['speedX']  > 120 and front_dis < 60.5:
        print("[throttle control] TOO FAST AND CLOSSSEE BRAKINGG")
        R['brake'] = 1
        R['accel'] = 0
    else:
        print("[throttle control] NOT TOO FAST AND CLOSSEE")


    if S['speedX']  < 80 and front_dis > 25:
        R['accel'] += 0.2

    print(f"[throttle control] front dis: {front_dis}")
    # Low-Speed Boost
    if S['speedX'] < 60:
        R['accel'] += 1 

    # Clip Acceleration Value Again
    R['accel'] = clip(R['accel'], 0, 1)
    print(f"[throttle control] Final clipped throttle: {R['accel']}")

def improved_steering_control2(S, R, target_speed):
    PI = math.pi

    # Steer to Corner
    R['steer'] = S['angle'] * 10 / PI
    print(f"Initial steering based on angle: {R['steer']}")

    # Steer to Center
    R['steer'] -= S['trackPos'] * 0.30
    print(f"Steering after track position adjustment: {R['steer']}")

    # Avoid Opponents
    opponent_readings = S['opponents']
    opponent_angles = [i for i in range(-180, 190, 10)]

    # Calculate opponent influence on steering
    opponent_steer_adjustment = 0
    for i in range(len(opponent_readings)):
        if opponent_readings[i] < 50 and opponent_readings[i] != -1:
            angle = opponent_angles[i]
            weight = 1 / (abs(angle) + 1)
            adjustment = -weight if angle < 0 else weight
            opponent_steer_adjustment += adjustment * (50 - opponent_readings[i]) / 50
    
    R['steer'] += opponent_steer_adjustment * 0.1
    print(f"Steering after opponent adjustment: {R['steer']}")

    # High-Speed Adjustment Using Sensor Data
    if S['speedX'] > target_speed * 0.8:
        # Get sensor readings (assuming S['track'] holds the sensor distances)
        sensor_readings = S['track']
        angles = [-90, -75, -60, -45, -30, -20, -15, -10, -5, 0, 5, 10, 15, 20, 30, 45, 60, 75, 90]

        # Calculate a weighted adjustment based on sensor data
        weighted_sum = 0
        weight_total = 0
        for i in range(len(sensor_readings)):
            if sensor_readings[i] != -1:
                angle = angles[i]
                if abs(angle) <= 10:
                    weight = 1  # Highest weight for front-center sensors
                elif abs(angle) <= 30:
                    weight = 0.5  # Medium weight for front-side sensors
                else:
                    weight = 0.1  # Lowest weight for far side sensors
                
                weighted_sum += sensor_readings[i] * weight
                weight_total += weight

        if weight_total > 0:
            average_distance = weighted_sum / weight_total
        else:
            average_distance = 100  # Default value if all sensors are off track

        # Adjust steering based on the average distance
        correction_factor = 0.01
        if average_distance < 50:
            R['steer'] -= correction_factor * (50 - average_distance) / 50
        else:
            R['steer'] += correction_factor * (average_distance - 50) / 150
        print(f"Steering after high-speed adjustment: {R['steer']}")

    # Clip the steering value to ensure it's within the valid range
    R['steer'] = clip(R['steer'], -1, 1)
    print(f"Final clipped steering: {R['steer']}")

def improved_throttle_control2(S, R, target_speed):
    PI = math.pi

    # Throttle Control Based on Target Speed and Steering
    if S['speedX'] < target_speed - (R['steer'] * 50):
        R['accel'] += 0.01
    else:
        R['accel'] -= 0.01

    # Low-Speed Boost
    if S['speedX'] < 10:
        R['accel'] += 1 / (S['speedX'] + 0.1)

    # Traction Control System
    if ((S['wheelSpinVel'][2] + S['wheelSpinVel'][3]) -
       (S['wheelSpinVel'][0] + S['wheelSpinVel'][1]) > 5):
        R['accel'] -= 0.2

    # Clip Acceleration Value
    R['accel'] = clip(R['accel'], 0, 1)
    print(f"Throttle after basic control: {R['accel']}")

    # Additional Speed Adjustment Based on Track Curvature
    sensor_readings = S['track']
    angles = [-90, -75, -60, -45, -30, -20, -15, -10, -5, 0, 5, 10, 15, 20, 30, 45, 60, 75, 90]

    # Calculate a weighted curvature measure
    weighted_sum = 0
    weight_total = 0
    for i in range(len(sensor_readings)):
        if sensor_readings[i] != -1:
            angle = angles[i]
            weight = 1 / (abs(angle) + 1)  # Weight inversely proportional to angle
            weighted_sum += sensor_readings[i] * weight
            weight_total += weight

    if weight_total > 0:
        average_distance = weighted_sum / weight_total
    else:
        average_distance = 100  # Default value if all sensors are off track

    # Adjust throttle based on curvature
    curvature_factor = 0.5  # Factor to control the influence of curvature
    if average_distance < 50:
        R['accel'] -= curvature_factor * (50 - average_distance) / 50
    else:
        R['accel'] += curvature_factor * (average_distance - 50) / 150
    print(f"Throttle after curvature adjustment: {R['accel']}")

    # Adjust throttle based on proximity to opponents
    opponent_readings = S['opponents']
    opponent_distance_threshold = 30  # Threshold distance to consider for throttle adjustment
    for distance in opponent_readings:
        if distance != -1 and distance < opponent_distance_threshold:
            R['accel'] -= 0.1 * (opponent_distance_threshold - distance) / opponent_distance_threshold
    print(f"Throttle after opponent adjustment: {R['accel']}")

    # Clip Acceleration Value Again
    R['accel'] = clip(R['accel'], 0, 1)
    print(f"Final clipped throttle: {R['accel']}")

def drive_example(c):
    '''This is only an example. It will get around the track but the
    correct thing to do is write your own `drive()` function.'''
    S= c.S.d
    R= c.R.d
    target_speed=360

    out= S['trackPos']
    # left = 1, right = -1 kleiner of groter dan 0.8 is wheel of track
    print(f"track pos: {out}")

    # Damage Control
    # target_speed-= S['damage'] * .05
    # if target_speed < 25: target_speed= 25

    # # Steer To Corner
    # R['steer']= S['angle']*10 / PI
    # print(f"steering = {R['steer']}")
    # # Steer To Center
    # R['steer']-= S['trackPos']*.30
    # R['steer']= clip(R['steer'],-1,1)

    improved_steering_control(S,R, target_speed)
    improved_throttle_control(S,R, target_speed)
    speed_kmh = math.sqrt(S["speedX"]**2 + S["speedY"]**2)
    print(f"speed: {speed_kmh}km/h")
    print(f"accel: {R['accel']}")

    if S['gear']==0:
        R['gear']=1

    # if R["accel"] > 0:
    if S['rpm'] > 8000 and S['gear'] < 7:
            R['gear'] = S['gear'] + 1

    if S['rpm'] < 2500 and S['gear'] > 2:
        R['gear'] = S['gear'] - 1
    print(f"gear: {R['gear']}")
    return

# ================ MAIN ================
if __name__ == "__main__":
    C= Client()
    for step in range(C.maxSteps,0,-1):
        C.get_servers_input()
        drive_example(C)
        C.respond_to_server()
    C.shutdown()