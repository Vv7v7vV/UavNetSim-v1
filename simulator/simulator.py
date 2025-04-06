import random

from phy.channel import Channel
from entities.drone import Drone

from simulator.metrics import Metrics
# from .metrics import Metrics

from mobility import start_coords
from utils import config
from allocation.central_controller import CentralController
from visualization.scatter import scatter_plot


class Simulator:
    """
    Description: simulation environment

    Attributes:
        env：SimPy环境，用于管理仿真中的事件和时间。
        total_simulation_time：总仿真时间（以纳秒为单位）。
        n_drones：仿真中无人机的数量。
        channel_states：一个字典，用于描述信道的使用情况。
        channel：无线信道，用于无人机之间的通信。
        metrics：Metrics类的实例，用于记录网络性能指标。
        drones：一个列表，包含所有无人机实例。
    """

    def __init__(self, seed, env, channel_states, n_drones, total_simulation_time=config.SIM_TIME, gui_canvas=None):
        self.gui_canvas = gui_canvas  # 新增参数
        self.env = env
        self.seed = seed
        self.total_simulation_time = total_simulation_time  # total simulation time (ns)

        self.n_drones = n_drones  # total number of drones in the simulation
        self.channel_states = channel_states
        self.channel = Channel(self.env)

        self.metrics = Metrics(self)  # use to record the network performance

        # NOTE: if distributed optimization is adopted, remember to comment this to speed up simulation
        # self.central_controller = CentralController(self)


        # 生成无人机的初始位置。
        start_position = start_coords.get_random_start_point_3d(seed)

        self.drones = []
        for i in range(n_drones):
            # 在异构网络中，不同无人机可以有不同的速度（默认不支持）
            if config.HETEROGENEOUS:
                speed = random.randint(5, 60)
            else:
                speed = 10

            print('无人机: ', i, '初始位置: ', start_position[i], ' 速度: ', speed)
            drone = Drone(env=env, node_id=i, coords=start_position[i], speed=speed,
                          inbox=self.channel.create_inbox_for_receiver(i), simulator=self)
            self.drones.append(drone)

        # scatter_plot(self)
        # scatter_plot(simulator, gui_canvas=self.canvas)  # 通过主线程调用
        scatter_plot(self, gui_canvas=self.gui_canvas)

        self.env.process(self.show_performance())
        self.env.process(self.show_time())

    def show_time(self):
        while True:
            print('At time: ', self.env.now / 1e6, ' s.')
            yield self.env.timeout(0.5*1e6)  # the simulation process is displayed every 0.5s

    def show_performance(self):
        yield self.env.timeout(self.total_simulation_time - 1)

        # scatter_plot(self)
        scatter_plot(self, gui_canvas=self.gui_canvas)  # 通过主线程调用

        self.metrics.print_metrics()
