import tkinter as tk
from tkinter import ttk, messagebox
from threading import Thread
import simpy
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from utils import config
from simulator.simulator import Simulator
from visualization.visualizer import SimulationVisualizer
import matplotlib.pyplot as plt

import matplotlib
matplotlib.rcParams['font.family'] = 'SimHei'  # 使用黑体
matplotlib.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

class UavNetSimGUI:
    def __init__(self, master):
        self.master = master
        master.title("UavNetSim-v1 Control Panel")
        master.geometry("1400x800")

        # 主布局框架
        self.main_frame = ttk.Frame(master)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 右侧控制面板
        self.control_panel = ttk.Frame(self.main_frame, width=200)
        self.control_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)

        # 可视化区域
        self.vis_frame = ttk.Frame(self.main_frame)
        self.vis_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 初始化控制按钮
        self.setup_controls()

        # 初始化可视化组件
        self.setup_visualization()

        # 仿真相关对象
        self.sim = None
        self.visualizer = None
        self.sim_thread = None

        self.fig = plt.figure(figsize=(18, 6))
        self.ax_data = self.fig.add_subplot(121, projection='3d')
        self.ax_ack = self.fig.add_subplot(122, projection='3d')
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.vis_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 添加线程安全队列
        self.plot_queue = []
        self.master.after(100, self.process_plot_queue)

    def setup_controls(self):
        """初始化右侧控制按钮"""
        style = ttk.Style()
        style.configure("Control.TButton", width=15, padding=6)

        # 运行按钮
        self.run_btn = ttk.Button(
            self.control_panel,
            text="开始仿真",
            command=self.start_simulation,
            style="Control.TButton"
        )
        self.run_btn.pack(pady=10, fill=tk.X)

        # 预留按钮1
        self.btn1 = ttk.Button(
            self.control_panel,
            text="按钮1",
            style="Control.TButton"
        )
        self.btn1.pack(pady=5, fill=tk.X)

        # 预留按钮2
        self.btn2 = ttk.Button(
            self.control_panel,
            text="按钮2",
            style="Control.TButton"
        )
        self.btn2.pack(pady=5, fill=tk.X)

        # 状态指示
        self.status_label = ttk.Label(self.control_panel, text="点击按钮运行仿真")
        self.status_label.pack(pady=10)

    def setup_visualization(self):
        """初始化可视化区域"""
        self.fig = plt.figure(figsize=(18, 6))
        self.ax_data = self.fig.add_subplot(121, projection='3d')
        self.ax_ack = self.fig.add_subplot(122, projection='3d')

        # 创建 Canvas 时指定父容器
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.vis_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 传递canvas引用给visualizer
        # self.visualizer.gui_canvas = self.canvas

    def start_simulation(self):
        """启动仿真线程"""
        self.run_btn.config(state=tk.DISABLED)
        self.status_label.config(text="运行中...")
        self.sim_thread = Thread(target=self.run_simulation)
        self.sim_thread.start()
        self.master.after(100, self.check_thread)

    def run_simulation(self):
        """执行仿真任务"""
        try:
            # 初始化仿真环境
            env = simpy.Environment()
            # 为每架无人机创建一个信道资源，capacity=1 表示信道一次只能被一个无人机使用。
            channel_states = {i: simpy.Resource(env, capacity=1) for i in range(config.NUMBER_OF_DRONES)}
            self.sim = Simulator(
                seed=2025,
                env=env,
                channel_states=channel_states,
                n_drones=config.NUMBER_OF_DRONES,
                gui_canvas=self.canvas  # 传递 Tkinter Canvas
            )
            # 配置可视化器
            # 创建可视化器实例，设置仿真器、输出目录和可视化帧间隔（20000 微秒，即 0.02 秒）。
            self.visualizer = SimulationVisualizer(
                self.sim,
                gui_canvas=self.canvas,  # 传递Canvas引用
                output_dir=".",
                vis_frame_interval=20000,
                fig=self.fig,
                ax=[self.ax_data, self.ax_ack],
                gui_mode=True,
                master=self.master  # 新增：传递主窗口引用
            )

            # 传递 canvas 引用到 visualizer
            self.visualizer.gui_canvas = self.canvas

            def simulation_process():
                env.run(until=config.SIM_TIME)
                # 最终化处理
                self.visualizer.finalize()
                self.canvas.draw()

            Thread(target=simulation_process).start()

        except Exception as e:
            messagebox.showerror("仿真出错", str(e))
        # finally:
        #     self.run_btn.config(state=tk.NORMAL)
        #     self.status_label.config(text="Completed")

    def check_thread(self):
        """检查线程状态"""
        if self.sim_thread.is_alive():
            self.master.after(100, self.check_thread)

    def process_plot_queue(self):
        """主线程定期处理绘图队列"""
        while self.plot_queue:
            task = self.plot_queue.pop(0)
            task()
        self.master.after(100, self.process_plot_queue)


if __name__ == "__main__":
    root = tk.Tk()
    app = UavNetSimGUI(root)
    root.mainloop()