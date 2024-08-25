from pytocl.driver import Driver
from pytocl.car import State, Command


class Agent(Driver):
    def __init__(self):
        super().__init__()

    def drive(self, carstate: State) -> Command:
        command = Command()

        return command