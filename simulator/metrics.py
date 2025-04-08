import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict


class Metrics:
    """
    Tools for statistics of network performance

    1. Packet Delivery Ratio (PDR): is the ratio of number of packets received at the destinations to the number
       of packets sent from the sources
    2. Average end-to-end (E2E) delay: is the time a packet takes to route from a source to its destination through
       the network. It is the time the data packet reaches the destination minus the time the data packet was generated
       in the source node
    3. Routing Load: is calculated as the ratio between the numbers of control Packets transmitted
       to the number of packets actually received. NRL can reflect the average number of control packets required to
       successfully transmit a data packet and reflect the efficiency of the routing protocol
    4. Throughput: it can be defined as a measure of how fast the data is sent from its source to its intended
       destination without loss. In our simulation, each time the destination receives a data packet, the throughput is
       calculated and finally averaged
    5. Hop count: used to record the number of router output ports through which the packet should pass.

    References:
        [1] Rani. N, Sharma. P, Sharma. P., "Performance Comparison of Various Routing Protocols in Different Mobility
            Models," in arXiv preprint arXiv:1209.5507, 2012.
        [2] Gulati M K, Kumar K. "Performance Comparison of Mobile Ad Hoc Network Routing Protocols," International
            Journal of Computer Networks & Communications. vol. 6, no. 2, pp. 127, 2014.

    """

    def __init__(self, simulator):
        self.simulator = simulator

        self.control_packet_num = 0

        self.datapacket_generated = set()  # all data packets generated
        self.datapacket_arrived = set()  # all data packets that arrives the destination
        self.datapacket_generated_num = 0

        self.delivery_time = []
        self.deliver_time_dict = defaultdict()

        self.throughput = []
        self.throughput_dict = defaultdict()

        self.hop_cnt = []
        self.hop_cnt_dict = defaultdict()

        self.mac_delay = []

        self.collision_num = 0

    def print_metrics(self):
        # calculate the average end-to-end delay
        e2e_delay = np.mean(list(self.deliver_time_dict.values())) / 1e3

        # calculate the packet delivery ratio
        pdr = len(self.datapacket_arrived) / self.datapacket_generated_num * 100  # in %

        # calculate the throughput
        throughput = np.mean(list(self.throughput_dict.values())) / 1e3

        # calculate the hop count
        hop_cnt = np.mean(list(self.hop_cnt_dict.values()))

        # calculate the routing load
        rl = self.control_packet_num / len(self.datapacket_arrived)

        # channel access delay
        average_mac_delay = np.mean(self.mac_delay)

        print('总共发送: ', self.datapacket_generated_num, ' 个数据包')
        print('数据包投递率(PDR): ', pdr, '%')
        print('平均端到端延迟(E2E): ', e2e_delay, 'ms')
        print('路由负载(RL): ', rl)
        print('平均吞吐量是: ', throughput, 'Kbps')
        print('平均跳数是: ', hop_cnt)
        print('冲突次数是: ', self.collision_num)
        print('平均MAC层延迟: ', average_mac_delay, 'ms')
