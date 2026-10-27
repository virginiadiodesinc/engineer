from ..instrument_controllers.HP6627A import PSU

class NSU(PSU):

    def __init__(self):
        super().__init__()

    def cleanup(self):
        #override cleanup so it doesn't turn off the supplies on close/crash
        pass

    def query_channels(self, channels=[1,2,3]):

        currents = []
        for chan in channels:
            currents.append(self.get_currout(chan))
        return currents