import simpy
from utils import config
from simulator.simulator import Simulator
from visualization.visualizer import SimulationVisualizer


"""
  _   _                   _   _          _     ____    _             
 | | | |   __ _  __   __ | \ | |   ___  | |_  / ___|  (_)  _ __ ___  
 | | | |  / _` | \ \ / / |  \| |  / _ \ | __| \___ \  | | | '_ ` _ \ 
 | |_| | | (_| |  \ V /  | |\  | |  __/ | |_   ___) | | | | | | | | |
  \___/   \__,_|   \_/   |_| \_|  \___|  \__| |____/  |_| |_| |_| |_|
                                                                                                                                                                                                                                                                                           
"""

if __name__ == "__main__":
    # Simulation setup
    env = simpy.Environment()
    # 为每架无人机创建一个信道资源，capacity=1 表示信道一次只能被一个无人机使用。
    channel_states = {i: simpy.Resource(env, capacity=1) for i in range(config.NUMBER_OF_DRONES)}
    sim = Simulator(seed=2025, env=env, channel_states=channel_states, n_drones=config.NUMBER_OF_DRONES)
    
    # Add the visualizer to the simulator
    # 创建可视化器实例，设置仿真器、输出目录和可视化帧间隔（20000 微秒，即 0.02 秒）。
    visualizer = SimulationVisualizer(sim, output_dir=".", vis_frame_interval=20000)
    # 启动可视化过程，开始显示仿真过程中的无人机分布和飞行轨迹。
    visualizer.run_visualization()

    # 运行仿真，直到达到配置文件中指定的仿真时间（SIM_TIME）。
    env.run(until=config.SIM_TIME)
    
    # 完成可视化过程，保存最终的可视化结果（如图像或视频）。
    visualizer.finalize()

