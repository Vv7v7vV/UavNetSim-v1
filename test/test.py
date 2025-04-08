import simpy
from utils import config
from simulator.simulator import Simulator
from visualization.visualizer import SimulationVisualizer
import matplotlib.pyplot as plt


def run_main_simulation():
    # # 创建仿真环境
    # env = simpy.Environment()
    # channel_states = {i: simpy.Resource(env, capacity=1) for i in range(config.NUMBER_OF_DRONES)}
    # sim = Simulator(seed=2025, env=env, channel_states=channel_states, n_drones=config.NUMBER_OF_DRONES)
    #
    # # 启用可视化
    # visualizer = SimulationVisualizer(sim, output_dir=".", vis_frame_interval=20000)
    # visualizer.run_visualization()
    #
    # # 运行仿真
    # env.run(until=config.SIM_TIME)

    # 生成图像
    plt.figure()
    plt.plot([1, 2, 3], [4, 5, 6])
    plt.savefig("result1.png")

    plt.figure()
    plt.plot([1, 2, 3], [6, 5, 4])
    plt.savefig("result2.png")

    plt.figure()
    plt.plot([1, 2, 3], [6, 5, 4])
    plt.savefig("result3.png")


if __name__ == "__main__":
    run_main_simulation()