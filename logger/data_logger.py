import csv
import math
import pandas as pd

class log():
    def __init__(self):
        self.file_name = ""
        self.fields = [
            "TARGET_SPEED",
            "STEERING",
            "SPEED",
            "ANGLE_TO_TRACK_AXIS",
            "TRACK_POSITION",
            "TRACK_EDGE_0",
            "TRACK_EDGE_1",
            "TRACK_EDGE_2",
            "TRACK_EDGE_3",
            "TRACK_EDGE_4",
            "TRACK_EDGE_5",
            "TRACK_EDGE_6",
            "TRACK_EDGE_7",
            "TRACK_EDGE_8",
            "TRACK_EDGE_9",
            "TRACK_EDGE_10",
            "TRACK_EDGE_11",
            "TRACK_EDGE_12",
            "TRACK_EDGE_13",
            "TRACK_EDGE_14",
            "TRACK_EDGE_15",
            "TRACK_EDGE_16",
            "TRACK_EDGE_17",
            "TRACK_EDGE_18",
            "OPPONENT_0",
            "OPPONENT_1",
            "OPPONENT_2",
            "OPPONENT_3",
            "OPPONENT_4",
            "OPPONENT_5",
            "OPPONENT_6",
            "OPPONENT_7",
            "OPPONENT_8",
        ]

    def start(self):
        self.csvfile = open(f"logger/{self.file_name}.csv", 'w', newline='')
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

