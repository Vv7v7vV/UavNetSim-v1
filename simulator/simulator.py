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

    def __init__(self,
                 seed,
                 env,
                 channel_states,
                 n_drones,
                 total_simulation_time=config.SIM_TIME,
                 update_drone_callback=None,
                 update_progress_callback=None,  # 新增进度回调
                 axs=None,
                 gui_canvas=None):

        self.env = env
        self.seed = seed
        self.total_simulation_time = total_simulation_time  # total simulation time (ns)

        self.n_drones = n_drones  # total number of drones in the simulation
        self.channel_states = channel_states
        self.channel = Channel(self.env)

        self.metrics = Metrics(self)  # use to record the network performance

        # NOTE: if distributed optimization is adopted, remember to comment this to speed up simulation
        # self.central_controller = CentralController(self)

        self.gui_canvas = gui_canvas  # 新增参数
        self.update_drone_callback = update_drone_callback
        self.update_progress_callback = update_progress_callback

        # 生成无人机的初始位置。
        start_position = start_coords.get_random_start_point_3d(seed)

        self.drones = []
        for i in range(n_drones):
            # 在异构网络中，不同无人机可以有不同的速度（默认不支持）
            if config.HETEROGENEOUS:
                speed = random.randint(5, 60)
            else:
                speed = 10

            info = (
                f'无人机: {i}, '
                f'初始位置: ({start_position[i][0]:.1f}, {start_position[i][1]:.1f}, {start_position[i][2]:.1f}), '
                f'速度: {speed}'
            )
            if self.gui_canvas:
                if self.update_drone_callback:
                    self.update_drone_callback(info)
            else:
                print(info)  # 非GUI模式直接输出到控制台

            drone = Drone(env=env, node_id=i, coords=start_position[i], speed=speed,
                          inbox=self.channel.create_inbox_for_receiver(i), simulator=self)
            self.drones.append(drone)

        # scatter_plot(self)
        # scatter_plot(simulator, gui_canvas=self.canvas)  # 通过主线程调用

        # 1图pic
        if gui_canvas:
            scatter_plot(
                self,
                gui_canvas=self.gui_canvas,
                target_ax=axs[0]  # 传递目标子图
            )
        else:
            scatter_plot(
                self,
                gui_canvas=self.gui_canvas,
                target_ax=0)

        self.env.process(self.show_performance())
        self.env.process(self.show_time())

    def show_time(self):
        total_simulation_time_s = self.total_simulation_time/1e6
        while True:
            progress_msg = f'仿真进度：{self.env.now / 1e6:.1f} s / {total_simulation_time_s:.1f} s'
            if self.gui_canvas:
                self.update_progress_callback(progress_msg)  # GUI模式调用回调
            else:
                print(progress_msg)  # 控制台模式使用\r实现原地刷新
            yield self.env.timeout(0.5*1e6)

    def show_performance(self):
        yield self.env.timeout(self.total_simulation_time - 1)

        # scatter_plot(self)
        scatter_plot(self, gui_canvas=self.gui_canvas)  # 通过主线程调用

        self.metrics.print_metrics()
