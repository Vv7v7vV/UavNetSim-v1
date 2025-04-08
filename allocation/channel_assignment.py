import random


class ChannelAssigner:
    """
    Class for sub-channel assignment

    Sub-channel assignment is important in IEEE 802.11 wireless network since it can handle adjacent channel
    interference. Take IEEE 802.11b wireless LANs operated on the 2.4GHz ISM band as an example, there are 14
    sub-channels, however, some of them are overlapping, which will cause adjacent channel interference. This part of
    work can be further extended to implement more advanced channel assignment algorithms, and support more access
    technique like orthogonal frequency-division multiple access as well.

    Attributes:
        simulator: the simulation platform that contains everything
        my_drone: the drone that installed this module
        mode: the IEEE 802.11 standard that adopted
        rng_channel_assignment: a Random class based on which we can call the function that generates the random number

    Author: Zihao Zhou, eezihaozhou@gmail.com
    Created at: 2025/3/30
    Updated at: 2025/3/31
    """

    def __init__(self, simulator, my_drone, mode="IEEE_802_11b"):
        self.simulator = simulator
        self.my_drone = my_drone
        self.mode = mode
        self.rng_channel_assignment = random.Random(self.my_drone.identifier + self.my_drone.simulator.seed + 66)

    def without_assignment(self):
        # this will be served as a baseline
        if self.mode is "IEEE_802_11b":
            return 1  # all nodes transmit packet in channel 1
        else:
            print('Currently not support~ We are working on it.')
            return -1

    def random_ondemand_assignment(self):
        if self.mode is "IEEE_802_11b":
            available_channels = [1, 6, 11]
            return self.rng_channel_assignment.choice(available_channels)
        else:
            print('Currently not support~ We are working on it.')
            return -1

    def adjacent_channel_interference_check(self, channel_id1, channel_id2):
        if self.mode is "IEEE_802_11b":
            if abs(channel_id1 - channel_id2) < 5:
                return True
            else:
                return False
        else:
            print('Currently not support~ We are working on it.')
            return -1

    def channel_assign(self):
        return self.without_assignment()


