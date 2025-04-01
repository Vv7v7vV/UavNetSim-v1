import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import simpy
from utils import config
from simulator.simulator import Simulator
from visualization.visualizer import SimulationVisualizer

class SimulationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("UavNetSim-v1 GUI")
        self.root.geometry("1200x800")

        # 创建主框架
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 创建画布区域（左侧）
        self.canvas_frame = ttk.Frame(self.main_frame)
        self.canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 创建按钮区域（右侧）
        self.button_frame = ttk.Frame(self.main_frame, width=200)
        self.button_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10)

        # 初始化画布
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.canvas_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 添加按钮
        self.add_buttons()

    def add_buttons(self):
        # 运行仿真按钮
        run_button = ttk.Button(self.button_frame, text="运行仿真", command=self.run_simulation)
        run_button.pack(fill=tk.X, pady=5)

        # 其他按钮（暂时不指定效果）
        button2 = ttk.Button(self.button_frame, text="按钮2", command=lambda: print("按钮2被点击"))
        button2.pack(fill=tk.X, pady=5)

        button3 = ttk.Button(self.button_frame, text="按钮3", command=lambda: print("按钮3被点击"))
        button3.pack(fill=tk.X, pady=5)

    def run_simulation(self):
        # 创建仿真环境
        env = simpy.Environment()
        channel_states = {i: simpy.Resource(env, capacity=1) for i in range(config.NUMBER_OF_DRONES)}
        sim = Simulator(seed=2025, env=env, channel_states=channel_states, n_drones=config.NUMBER_OF_DRONES)

        # 启用可视化
        visualizer = SimulationVisualizer(sim, output_dir=".", vis_frame_interval=20000)
        visualizer.run_visualization()

        # 运行仿真
        env.run(until=config.SIM_TIME)

        # 获取仿真结果
        self.plot_results()

    def plot_results(self):
        # 清空画布
        self.ax.clear()

        # 这里是你的绘图逻辑，例如：
        # self.ax.plot(x, y)
        # self.ax.set_title("仿真结果")
        # self.ax.set_xlabel("X轴")
        # self.ax.set_ylabel("Y轴")

        # 刷新画布
        self.canvas.draw()

if __name__ == "__main__":
    # 创建一个Tk对象(Tkinter库中的主窗口对象)
    root = tk.Tk()
    # 创建一个SimulationGUI类的实例，将root窗口作为参数传递给构造函数。
    app = SimulationGUI(root)
    # 启动Tkinter的主事件循环。使GUI应用程序保持运行状态。
    root.mainloop()