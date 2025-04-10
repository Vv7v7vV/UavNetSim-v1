import tkinter as tk
from sys import maxsize
from tkinter import ttk, messagebox
from threading import Thread
import simpy
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from utils import config
from simulator.simulator import Simulator
from visualization.scatter import scatter_plot
from visualization.visualizer import SimulationVisualizer
import matplotlib.pyplot as plt
from PIL import Image, ImageTk, ImageSequence


import matplotlib
matplotlib.rcParams['font.family'] = 'SimHei'  # 使用黑体
matplotlib.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

class UavNetSimGUI:
    # 字体

    def __init__(self, master):
        self.master = master
        master.title("UavNetSim-v1 Control Panel")
        master.geometry("1600x900")
        master.minsize(800, 600)  # 防止过度压缩

        # 主框架使用grid布局
        self.main_frame = ttk.Frame(master)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 配置主框架列权重（左:中:右 = 2:4:1）
        self.main_frame.columnconfigure(0, weight=2)
        self.main_frame.columnconfigure(1, weight=4)
        self.main_frame.columnconfigure(2, weight=1)
        self.main_frame.rowconfigure(0, weight=1)

        # ========== 左侧面板 ==========
        self.left_panel = ttk.Frame(self.main_frame)
        self.left_panel.grid(row=0, column=0, sticky="nsew")
        # 配置左面板行权重（上:下 = 2:1）
        self.left_panel.rowconfigure(0, weight=2)
        self.left_panel.rowconfigure(1, weight=1)
        self.left_panel.columnconfigure(0, weight=1)

        # 左上区域（无人机参数）
        self.left_upper = ttk.LabelFrame(self.left_panel, text="无人机初始化参数")
        self.left_upper.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.drone_info = tk.Text(self.left_upper, wrap=tk.WORD, font=config.text_font)
        self.drone_info.pack(fill=tk.BOTH, expand=True)  # 内部组件可用pack

        # 左下区域（性能指标）
        self.left_lower = ttk.LabelFrame(self.left_panel, text="实时性能指标")
        self.left_lower.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.metrics_info = tk.Text(self.left_lower, wrap=tk.WORD, font=config.text_font)
        self.metrics_info.pack(fill=tk.BOTH, expand=True)

        # ========== 中间可视化区域 ==========
        self.vis_frame = ttk.Frame(self.main_frame)
        self.vis_frame.grid(row=0, column=1, sticky="nsew")

        # 创建4个子图（保持原有代码）
        self.fig = plt.figure(figsize=(16, 10))
        self.gs = self.fig.add_gridspec(2, 2)  # 使用GridSpec管理4个子图

        # 明确定义所有子图并初始化为空3D坐标系
        self.axs = []
        positions = [(0, 0), (0, 1), (1, 0), (1, 1)]  # 子图位置
        titles = ["初始网络拓扑视图", "数据包流向分析", "链路质量监测", "移动轨迹预测"]
        for idx, (pos, title) in enumerate(zip(positions, titles)):
            # if idx == 0:  # 第一个子图改为2D
            #     ax = self.fig.add_subplot(self.gs[pos[0], pos[1]])
            #     ax.set_title(title, fontsize=12)
            #     ax.grid(True)
            #     ax.set_xlim(0, config.MAP_LENGTH)
            #     ax.set_ylim(0, config.MAP_WIDTH)
            # else:  # 其他子图保持3D
            ax = self.fig.add_subplot(self.gs[pos[0], pos[1]], projection='3d')
            ax.grid(True)
            ax.set_title(title, fontsize=12)
            ax.view_init(elev=30, azim=45)
            ax.set_xlim(0, config.MAP_LENGTH)
            ax.set_ylim(0, config.MAP_WIDTH)
            ax.set_zlim(0, config.MAP_HEIGHT)
            self.axs.append(ax)
        # for pos, title in zip(positions, titles):
        #     ax = self.fig.add_subplot(
        #         self.gs[pos[0], pos[1]],  # 使用GridSpec索引
        #         projection='3d'
        #     )
        #     # 初始化为空白3D坐标系
        #     ax.grid(True)  # 关闭网格线
        #     ax.axis('on')  # 隐藏坐标轴
        #     ax.set_title(title, fontsize=config.fig_font_size)
        #     # 设置初始视角和坐标范围（可选）
        #     ax.view_init(elev=30, azim=45)  # 俯仰角30度，方位角45度
        #     ax.set_xlim(0, config.MAP_LENGTH)
        #     ax.set_ylim(0, config.MAP_WIDTH)
        #     ax.set_zlim(0, config.MAP_HEIGHT)
        #     self.axs.append(ax)

        # 创建唯一Canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.vis_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        # 绑定2D子图点击事件
        self.canvas.mpl_connect('button_press_event', self.on_2d_plot_click)

        self.canvas.draw()  # 立即渲染空白图像

        # ========== 右侧面板 ==========
        self.right_panel = ttk.Frame(self.main_frame)
        self.right_panel.grid(row=0, column=2, sticky="nsew")
        # self.right_panel.grid_propagate(False)  # 禁止自动调整尺寸
        # self.right_panel.config(width=300)  # 设置固定基础宽度
        self.right_panel.columnconfigure(0, weight=1, minsize=200)  # 动态约束

        # 配置右面板行权重（上:下 = 1:1）
        self.right_panel.rowconfigure(0, weight=1)
        self.right_panel.rowconfigure(1, weight=1)
        self.right_panel.columnconfigure(0, weight=1)

        # 右上区域（控制按钮）
        self.right_upper = ttk.Frame(self.right_panel)
        self.right_upper.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        # 配置按钮容器布局
        self.right_upper.rowconfigure((0,1,2,3), weight=1, uniform="button_rows")  # 均匀分配行高
        self.right_upper.columnconfigure(0, weight=1)  # 单列布局
        # self.right_upper.grid_propagate(False)  # 禁止自动调整尺寸
        self.setup_controls()
        # 添加事件绑定以动态调整尺寸
        # self.right_panel.bind('<Configure>', self._adjust_right_upper_size)

        # 右下区域（运行日志）
        self.right_lower = ttk.LabelFrame(self.right_panel, text="运行日志")
        self.right_lower.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.log_info = tk.Text(self.right_lower, wrap=tk.WORD, font=config.text_font)
        self.log_info.pack(fill=tk.BOTH, expand=True)

        # 初始化默认文本内容
        self._init_default_text()

        # ====================================仿真相关对象=======================================
        self.sim = None
        self.visualizer = None
        self.sim_thread = None

        # self.fig = plt.figure(figsize=(18, 6))
        # self.ax_data = self.fig.add_subplot(121, projection='3d')
        # self.ax_ack = self.fig.add_subplot(122, projection='3d')
        # self.canvas = FigureCanvasTkAgg(self.fig, master=self.vis_frame)
        # self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 添加线程安全队列
        self.plot_queue = []
        self.master.after(100, self.process_plot_queue)

        # # 添加GIF显示区域
        # self.gif_frame = ttk.Frame(self.control_panel)
        # self.gif_frame.pack(pady=10)
        # self.gif_label = ttk.Label(self.gif_frame)
        # self.gif_label.pack()

        self.master.bind("<Configure>", self._on_window_resize)
        # self.print_layout()

    def setup_controls(self):
        """初始化控制按钮 - 现代化简约风格"""
        style = ttk.Style()

        # 基础按钮样式
        style.configure("TButton",
                        font=('Microsoft YaHei', 12),  # 更现代的中文字体
                        borderwidth=1,
                        relief="flat",  # 扁平化设计
                        padding=6,
                        width=15
                        )

        # 按钮样式
        style.map("My.TButton",
                  foreground=[('active', '#333333'), ('!active', '#666666')],
                  background=[
                      ('active', '#F0F0F0'),  # 悬停色
                      ('!active', '#F8F8F8')  # 常态色
                  ]
                  )
        # 配置按钮最大尺寸和居中
        style.configure("My.TButton",
                        width=15,  # 基准宽度（字符单位）
                        anchor="center",  # 文字居中
                        padding=(10, 6),  # 内边距
                        wraplength=200,  # 自动换行避免溢出
                        maxwidth=200  # 最大宽度（像素）
                        )

        buttons = [
            ("开始仿真", self.start_simulation, "My.TButton"),
            ("修改参数", lambda: self.log("功能待实现"), "My.TButton"),
            ("选择模型", lambda: self.log("功能待实现"), "My.TButton"),
            ("查看日志", lambda: self.log("日志功能待实现"), "My.TButton")
        ]
        # 添加尺寸约束配置
        style.configure("My.TButton", 
            width=12,  # 基准宽度（字符单位）
            anchor="center",  # 文字居中
            padding=(10, 6)  # 横向/纵向内边距
        )
        
        # 配置按钮容器弹性布局

        for i, (text, cmd, style_name) in enumerate(buttons):
            btn = ttk.Button(
                self.right_upper,
                text=text,
                command=cmd,
                style=style_name
            )
            btn.grid(
                row=i,
                column=0,
                sticky="nsew",
                pady=5,  # 上下间距5像素
                padx=10  # 左右间距10像素
            )

            # 添加动态约束
            btn.configure(padding=(0, 4))  # 减少纵向间距

        # 配置按钮区域权重
        # 配置行和列的权重
        self.right_upper.rowconfigure((0, 1, 2, 3), weight=1, uniform="button_row")
        self.right_upper.columnconfigure(0, weight=1)


    def _init_default_text(self):
        """初始化左侧文本内容"""
        # 无人机初始化数据
        drone_data = """运行仿真后展示无人机信息"""
        self.drone_info.insert(tk.END, drone_data)
        self.drone_info.config(state=tk.DISABLED)

        # 性能指标
        metrics_data = """运行仿真后展示指标信息"""
        self.metrics_info.insert(tk.END, metrics_data)
        self.metrics_info.config(state=tk.DISABLED)

        # 初始化日志
        self.log("系统初始化完成")
        self.log("等待用户操作...")
        self.log_info.config(state=tk.DISABLED)

    def log(self, message):
        """向日志区域添加信息"""
        self.log_info.config(state=tk.NORMAL)
        self.log_info.insert(tk.END, f"> {message}\n")
        self.log_info.see(tk.END)
        self.log_info.config(state=tk.DISABLED)

    def start_simulation(self):
        """启动仿真线程"""
        # self.run_btn.config(state=tk.DISABLED)
        # self.status_label.config(text="运行中...")

        # 清空信息区域
        self.clear_info_areas()

        # 启动仿真线程（确保先初始化visualizer）
        self.sim_thread = Thread(target=self.run_simulation)
        self.sim_thread.start()

        # 监听仿真线程完成后再启动GIF生成
        self.master.after(100, self.check_thread_and_start_gif)

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
                update_drone_callback = self.update_drone_info,       # 传递无人机信息回调
                update_progress_callback = self.update_progress_log,  # 传递log仿真进度回调
                gui_canvas = self.canvas,  # 传递 Tkinter Canvas
                axs= self.axs       # 传递图像对象
            )
            # 配置可视化器
            # 创建可视化器实例，设置仿真器、输出目录和可视化帧间隔（20000 微秒，即 0.02 秒）。
            self.visualizer = SimulationVisualizer(
                self.sim,
                gui_canvas=self.canvas,
                output_dir=".",  # 确保输出目录可写
                vis_frame_interval=20000,
                fig=self.fig,
                ax=self.axs,  # 传递所有4个子图对象
                gui_mode=True,
                master=self.master  # 传递主窗口引用
            )

            # 传递 canvas 引用到 visualizer
            self.visualizer.gui_canvas = self.canvas
            # 确保visualizer不为None
            assert self.visualizer is not None, self.log("Visualizer初始化失败")

            # 启动可视化过程，开始显示仿真过程中的无人机分布和飞行轨迹。
            # self.visualizer.run_visualization()


            def simulation_process():
                # 运行仿真，直到达到配置文件中指定的仿真时间（SIM_TIME）。
                env.run(until=config.SIM_TIME)
                # 最终化处理
                self.visualizer.finalize()
                self.canvas.draw()

            # 启动仿真进程线程
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



    def print_layout(self):
        left = self.left_panel.winfo_width()
        center = self.vis_frame.winfo_width()
        right = self.right_panel.winfo_width()
        print(
            f"比例 | 左:{left} | 中:{center} | 右:{right} | 实际比例:{left / center:.1f}:{center / center:.1f}:{right / center:.1f}")
        self.master.after(1000, self.print_layout)

    def _on_window_resize(self, event):
        total_width = self.main_frame.winfo_width()
        # 强制按比例分配
        self.main_frame.columnconfigure(0, minsize=int(total_width * 2 / 7))
        self.main_frame.columnconfigure(1, minsize=int(total_width * 4 / 7))
        self.main_frame.columnconfigure(2, minsize=int(total_width * 1 / 7))

    def _adjust_right_upper_size(self, event=None):
        max_height = 240  # 设置行高最大总和为400像素（每行100像素）
        current_height = self.right_panel.winfo_height()
        new_height = min(current_height, max_height)
        # 设置右侧按钮区域的高度
        self.right_upper.config(height=new_height)
        # 更新布局以确保生效
        self.right_upper.update_idletasks()

    def clear_info_areas(self):
        """清空无人机信息和性能指标区域"""

        def _clear_drone_info():
            self.drone_info.config(state=tk.NORMAL)
            self.drone_info.delete(1.0, tk.END)  # 清空内容
            # self.drone_info.insert(tk.END, "运行仿真后展示无人机信息")  # 恢复默认提示
            self.drone_info.config(state=tk.DISABLED)

        def _clear_metrics_info():
            self.metrics_info.config(state=tk.NORMAL)
            self.metrics_info.delete(1.0, tk.END)
            self.metrics_info.insert(tk.END, "仿真结束后展示指标信息\n")
            self.metrics_info.config(state=tk.DISABLED)

        def _clear_log_info():
            self.log_info.config(state=tk.NORMAL)
            self.log_info.delete(1.0, tk.END)
            self.log_info.insert(tk.END, "开始仿真：\n")
            self.log_info.config(state=tk.DISABLED)

        # 确保在主线程执行
        self.master.after(0, _clear_drone_info)
        self.master.after(0, _clear_metrics_info)
        self.master.after(0, _clear_log_info)

    def update_drone_info(self, text):
        """线程安全更新无人机信息区域"""

        def _update():
            self.drone_info.config(state=tk.NORMAL)
            # self.drone_info.delete(1.0, tk.END)  # 清空内容
            self.drone_info.insert(tk.END, text + "\n")
            self.drone_info.see(tk.END)
            self.drone_info.config(state=tk.DISABLED)

        self.master.after(0, _update)  # 确保在主线程执行

    def update_progress_log(self, message):
        """在同一行更新仿真进度（覆盖前一条）"""

        def _update():
            # 1. 解除日志框的只读状态
            self.log_info.config(state=tk.NORMAL)
            
            # 2. 获取当前全部日志内容（从第1行第0列到末尾）
            content = self.log_info.get("1.0", tk.END)
            
            # 3. 按换行符分割成列表（注意最后会有空字符串）
            lines = content.split("\n")  # 示例：["line1", "line2", ""]
            
            # 4. 初始化目标行号为-1（表示未找到）
            target_line = -1
            for idx, line in enumerate(lines):
                if "仿真进度" in line:
                    target_line = idx + 1  # Tkinter行号从1开始

            # 如果找到旧进度行，则删除并替换
            if target_line != -1:
                # 删除旧行内容（例如："3.0"表示第3行）
                self.log_info.delete(f"{target_line}.0", f"{target_line}.end")
                
                # 9. 在删除位置插入新内容（保留原有行号）
                self.log_info.insert(f"{target_line}.0", f"> {message}\n")
            else:
                # 10. 未找到时追加新行（正常插入）
                self.log_info.insert(tk.END, f"> {message}\n")
            
            # 11. 自动滚动到最新内容
            self.log_info.see(tk.END)
            
            # 12. 恢复只读状态
            self.log_info.config(state=tk.DISABLED)
        
        # 13. 通过主线程队列保证线程安全
        self.master.after(0, _update)

    def on_2d_plot_click(self, event):
        """点击2D图时弹出3D窗口"""
        if event.inaxes != self.axs[0]:
            return

        # 创建弹出窗口
        popup = tk.Toplevel(self.master)
        popup.title("3D网络拓扑视图")
        popup.geometry("800x600")

        # 创建3D Canvas
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        canvas = FigureCanvasTkAgg(fig, master=popup)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 调用3D绘图
        scatter_plot(
            self.sim,
            gui_canvas=canvas,
            is_3d=True,
            target_ax=ax
        )












    def process_plot_queue(self):
        """主线程定期处理绘图队列"""
        while self.plot_queue:
            task = self.plot_queue.pop(0)
            task()
        self.master.after(100, self.process_plot_queue)

    def generate_and_display_gif(self):
        """后台生成GIF并在完成后更新界面"""
        if self.visualizer is None:
            print("Visualizer未初始化，无法生成GIF")
            return

        # 调用visualizer生成GIF
        gif_path = self.visualizer.create_animations()

        # 在主线程更新GUI
        if gif_path:
            self.master.after(0, lambda: self.display_gif(gif_path))

    def display_gif(self, gif_path):
        """在GUI中显示GIF"""
        try:
            gif = Image.open(gif_path)
            frames = []
            for frame in ImageSequence.Iterator(gif):
                frame = frame.convert('RGBA')  # 转换为RGBA模式以支持透明度
                photo = ImageTk.PhotoImage(frame)
                frames.append(photo)

            # 保存帧引用，防止被垃圾回收
            self.gif_frames = frames
            self.current_frame = 0

            # 开始播放动画
            self.animate_gif()
        except Exception as e:
            print(f"Error displaying GIF: {e}")

    def animate_gif(self):
        """逐帧播放GIF"""
        if self.current_frame < len(self.gif_frames):
            self.gif_label.config(image=self.gif_frames[self.current_frame])
            self.current_frame += 1
            # 每100ms更新一帧（可根据GIF实际帧率调整）
            self.master.after(100, self.animate_gif)

    def check_thread_and_start_gif(self):
        """检查仿真线程是否完成，完成后启动GIF生成"""
        if self.sim_thread.is_alive():
            self.master.after(100, self.check_thread_and_start_gif)
        else:
            # 仿真线程完成后，启动GIF生成线程
            self.gif_thread = Thread(target=self.generate_and_display_gif)
            self.gif_thread.start()


if __name__ == "__main__":
    root = tk.Tk()
    app = UavNetSimGUI(root)
    root.mainloop()