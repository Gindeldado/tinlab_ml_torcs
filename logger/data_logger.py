import csv
import math
import pandas as pd

class log():
    def __init__(self):
        self.fields = ["targetSpeed", "command.steering", "speed", "carstate.angle", "distance_from_center",
                   "track_edge_0",
                   "track_edge_1",
                   "track_edge_2",
                   "track_edge_3",
                   "track_edge_4",
                   "track_edge_5",
                   "track_edge_6",
                   "track_edge_7",
                   "track_edge_8",
                   "track_edge_9",
                   "track_edge_10",
                   "track_edge_11",
                   "track_edge_12",
                   "track_edge_13",
                   "track_edge_14",
                   "track_edge_15",
                   "track_edge_16",
                   "track_edge_17",
                   "track_edge_18"
        ]

        self.csvfile = open("ml/logger/DataLog.csv", 'w', newline='')
        # creating a csv dict writer object
        self.writer = csv.writer(self.csvfile, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
        # writing headers (field names)
        self.writer.writerow(self.fields)

    def on_shutdown(self):
        self.csvfile.close()
        return super().on_shutdown()

    def get_fields(self) -> list:
        return self.fields
    
    def log_data(self, data:list):
        self.writer.writerow(data)


    # OLD DRIVER FUCNTION 
    # def drive( self, carstate: State) -> Command:
    #     # input to MLPRegr:         
    #     # "SPEED",
    #     # "TRACK_POSITION",
    #     # "ANGLE_TO_TRACK_AXIS",
    #     # "TRACK_EDGE_0",
    #     # "TRACK_EDGE_1",
    #     # "TRACK_EDGE_2",
    #     # "TRACK_EDGE_3",
    #     # "TRACK_EDGE_4",
    #     # "TRACK_EDGE_5",
    #     # "TRACK_EDGE_6",
    #     # "TRACK_EDGE_7",
        
    #     # in meter per second
    #     speed = sqrt(carstate.speed_x**2 + carstate.speed_y**2) / MPS_PER_KMH




    #     # sensor distance, index
    #     focusPoint = [0,0]

    #     for i in range(len(carstate.distances_from_edge)):
    #         val = carstate.distances_from_edge[i]
    #         if val > focusPoint[0]:
    #             focusPoint = [val, i]
                

    #     brakeZone = focusPoint[0] < speed / 1.5

    #     command = Command()
    #     self.steer(carstate, 0.0, command)
    #     targetSpeed = DEFAULT_MIN_SPEED if brakeZone else DEFAULT_MAX_SPEED
    #     speedIdent = 1 if targetSpeed == 250 else 0
    #     inputV = [speedIdent, command.steering, speed, carstate.angle, carstate.distance_from_center]

    #     for v in carstate.distances_from_edge:
    #         inputV.append(v)


        
    #     print("focus: ", focusPoint)
    #     print("targ speed: ", targetSpeed)
    #     print(brakeZone)
    #     if self.logData:
    #         self.writer.writerow(inputV)

    #     self.accelerate(carstate, targetSpeed, command)

    #     if self.data_logger:
    #         self.data_logger.log(carstate, command)

    #     return command

