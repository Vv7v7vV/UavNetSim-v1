import os
import subprocess
import sys
import tkinter as tk
from sys import maxsize
from tkinter import ttk, messagebox
from threading import Thread
import simpy
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from phy.large_scale_fading import maximum_communication_range
from utils import config
from simulator.simulator import Simulator
from utils.util_function import euclidean_distance_3d
from visualization.scatter import scatter_plot
from visualization.visualizer import SimulationVisualizer
import matplotlib.pyplot as plt
from PIL import Image, ImageTk, ImageSequence
from matplotlib.collections import PathCollection
from mpl_toolkits.mplot3d.art3d import Line3D
from gui.input_dialog import InputDialog



import matplotlib
matplotlib.rcParams['font.family'] = 'SimHei'  # 使用黑体
matplotlib.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

class UavNetSimGUI:
    # 字体

    def __init__(self, master):
        # ====================================仿真相关对象=======================================
        self.sim = None
        self.visualizer = None
        self.sim_thread = None
        self.sim_running = False  # 新增仿真状态标志
        self.master = master
        self.master.gui_instance = self

        master.title("无人机资源调度仿真平台")
        master.geometry("2880x1800")
        master.minsize(800, 600)  # 防止过度压缩

        # ======================================布局===========================================
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
        # 初始文本提示
        self.left_upper.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.drone_info = tk.Text(self.left_upper, wrap=tk.WORD, font=config.text_font)
        self.drone_info.pack(fill=tk.BOTH, expand=True)  # 内部组件可用pack
        self.drone_info.insert(tk.END, "运行仿真后展示无人机信息")
        self.drone_info.config(state=tk.DISABLED)

        # 预置表格控件（初始隐藏）
        self.drone_table = None
        self.table_vsb = None


        # 左下区域（性能指标）
        self.left_lower = ttk.LabelFrame(self.left_panel, text="实时性能指标")
        self.left_lower.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.metrics_info = tk.Text(self.left_lower, wrap=tk.WORD, font=config.text_font)
        self.metrics_info.pack(fill=tk.BOTH, expand=True)
        self.metrics_info.insert(tk.END, "仿真结束后展示指标信息\n")
        self.metrics_info.config(state=tk.DISABLED)

        self.metrics_table = None
        self.table_vsb2 = None


        # ================================= 中间可视化区域 ============================================
        self.vis_frame = ttk.Frame(self.main_frame)
        self.vis_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)  # 移除容器外边距

        # 配置样式（添加在setup_controls方法前）
        style = ttk.Style()
        style.configure("White.TFrame", background="white")

        self.vis_frame.rowconfigure(0, weight=1)  # 子图区域
        self.vis_frame.rowconfigure(1, weight=0)  # GIF区域（固定高度）
        self.vis_frame.columnconfigure(0, weight=1)

        # 创建3个子图（使用更紧凑的布局）
        self.fig = plt.figure(figsize=(16, 10), facecolor='white')
        self.gs = self.fig.add_gridspec(
            nrows=1, ncols=3,  # 单行三列
            width_ratios=[1, 1, 1],  # 等宽分布
            left=0.1, right=0.9,    # 左右边距各留10%
            wspace=0.3              # 子图横向间距
        )
        titles = ["初始网络拓扑视图", "无人机路径视图", "最终网络拓扑视图"]
        self.axs = []
        for idx, title in enumerate(titles):
            ax = self.fig.add_subplot(self.gs[0, idx], projection='3d')  # 全部放在第一行
            ax.set_facecolor('white')  # 设置子图背景为白
            ax.grid(True)
            ax.set_title(title, fontsize=config.fig_font_size)  # 标题
            ax.set_xlim(0, config.MAP_LENGTH)
            ax.set_ylim(0, config.MAP_WIDTH)
            ax.set_zlim(0, config.MAP_HEIGHT)
            ax.set_xlabel('X (m)')
            ax.set_ylabel('Y (m)')
            ax.set_zlabel('Z (m)')
            self.axs.append(ax)

        # 创建Canvas并添加垂直居中垫片
        canvas_container = ttk.Frame(self.vis_frame, style="White.TFrame")
        canvas_container.grid(row=0, column=0, sticky="nsew")
        canvas_container.rowconfigure(0, weight=1)
        canvas_container.columnconfigure(0, weight=1)

        self.canvas = FigureCanvasTkAgg(self.fig, master=canvas_container)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        # 添加底部垫片实现垂直居中
        ttk.Frame(canvas_container, height=20).grid(row=1, column=0)  # 调整此数值控制底部间距
        # 绑定Canvas点击事件
        self.canvas.get_tk_widget().bind("<Button-1>", self.on_canvas_click)

        # ===== GIF显示区域 =====
        self.gif_frame = ttk.Frame(
            self.vis_frame,
            style="White.TFrame",
            height=200,
            padding=0  # 移除内边距
        )
        self.gif_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)  # 移除边距
        # 配置三列布局（左垫片 + 内容 + 右垫片）
        self.gif_frame.columnconfigure(0, weight=1)
        self.gif_frame.columnconfigure(1, weight=0)  # 内容列不扩展
        self.gif_frame.columnconfigure(2, weight=1)
        self.gif_frame.rowconfigure(0, weight=1)

        # 创建居中显示容器
        self.gif_container = ttk.Frame(self.gif_frame)
        self.gif_container.grid(row=0, column=1, sticky="")

        # GIF标签使用固定宽高比
        self.gif_label = ttk.Label(self.gif_container)
        self.gif_label.pack(fill=tk.BOTH, expand=True)
        self.load_gif(r"visualization/Initial.gif")  # 替换为实际GIF路径


        # 关键布局配置
        # self.fig.tight_layout(rect=[0, 0.1, 1, 0.95])  # 调整整体绘图区域位置
        self.canvas.draw()

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
                        font=config.button_font,
                        width=15,  # 基准宽度（字符单位）
                        anchor="center",  # 文字居中
                        padding=(10, 6),  # 内边距
                        wraplength=200,  # 自动换行避免溢出
                        maxwidth=200  # 最大宽度（像素）
                        )

        buttons = [
            ("开始仿真", self.start_simulation, "My.TButton"),
            ("修改参数", self.show_input_dialog, "My.TButton"),
            ("选择模型", lambda: self.log("功能待实现"), "My.TButton"),
            ("查看日志", self.open_log_file, "My.TButton")
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

    def show_input_dialog(self):
        """显示参数配置对话框"""
        dialog = InputDialog(parent=self.master, gui_instance=self)  # 同时传递两个参数
        dialog.grab_set()

    def open_log_file(self):
        """打开日志文件"""
        log_path = r"E:\Data\lab\UavNetSim_v1\running_log.log"

        try:
            # Windows系统直接调用默认程序打开
            if os.name == 'nt':
                os.startfile(log_path)
            # 其他系统使用subprocess打开
            else:
                opener = 'open' if sys.platform == 'darwin' else 'xdg-open'
                subprocess.call([opener, log_path])

            self.log(f"已打开日志文件：\n{log_path}")
        except Exception as e:
            error_msg = f"打开日志失败：{str(e)}"
            messagebox.showerror("文件错误", error_msg)
            self.log(error_msg)

    def _init_default_text(self):
        """初始化左侧文本内容"""
        # # 无人机初始化数据
        # drone_data = """运行仿真后展示无人机信息"""
        # self.drone_info.insert(tk.END, drone_data)
        # self.drone_info.config(state=tk.DISABLED)

        # 性能指标
        # metrics_data = """运行仿真后展示指标信息"""
        # self.metrics_info.insert(tk.END, metrics_data)
        # self.metrics_info.config(state=tk.DISABLED)

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

        # 清空信息区域
        self.clear_info_areas()
        # 在主线程执行UI修改
        self.master.after(0, self.init_drone_info_table())
        # self.master.after(0, self.init_metrics_table())

        self.sim_running = True  # 标记仿真已启动

        # 启动仿真线程（确保先初始化visualizer）
        self.sim_thread = Thread(target=self.run_simulation)
        self.sim_thread.start()
        # 启动动画
        self.animate_gif()

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
                update_metrics_callback=self.update_metrics_info,     # 新增回调
                gui_canvas = self.canvas,  # 传递 Tkinter Canvas
                master=self.master,  # <-- 关键点
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
                gui_instance=self,  # <-- 关键点
                master=self.master  # 传递主窗口引用
            )

            # 确保visualizer不为None
            assert self.visualizer is not None, self.log("Visualizer初始化失败")

            def simulation_process():
                # 启动可视化过程，开始显示仿真过程中的无人机分布和飞行轨迹。
                self.visualizer.run_visualization()
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
            # self.drone_info.config(state=tk.NORMAL)
            # self.drone_info.delete(1.0, tk.END)  # 清空内容
            # # self.drone_info.insert(tk.END, "运行仿真后展示无人机信息")  # 恢复默认提示
            # self.drone_info.config(state=tk.DISABLED)

            # 销毁表格相关控件
            # if hasattr(self, 'drone_table'):
            #     self.drone_table = None
            # if hasattr(self, 'table_vsb'):
            #     self.table_vsb2.destroy()
            # 销毁文本控件
            self.drone_info.destroy()

        def _clear_metrics_info():
            # 销毁表格相关控件
            self.metrics_info.destroy()
            # if hasattr(self, 'metrics_table'):
            #     self.metrics_table.destroy()
            # if hasattr(self, 'table_vsb2'):
            #     self.table_vsb2.destroy()

        def _clear_log_info():
            self.log_info.config(state=tk.NORMAL)
            self.log_info.delete(1.0, tk.END)
            self.log_info.insert(tk.END, "开始仿真：\n")
            self.log_info.config(state=tk.DISABLED)

        # 确保在主线程执行
        self.master.after(0, _clear_drone_info)
        # self.master.after(0, _clear_metrics_info)
        self.master.after(0, _clear_log_info)

    # def update_drone_info(self, text):
    #     """线程安全更新无人机信息区域"""
    #
    #     def _update():
    #         self.drone_info.config(state=tk.NORMAL)
    #         # self.drone_info.delete(1.0, tk.END)  # 清空内容
    #         self.drone_info.insert(tk.END, text + "\n")
    #         self.drone_info.see(tk.END)
    #         self.drone_info.config(state=tk.DISABLED)
    #
    #     self.master.after(0, _update)  # 确保在主线程执行

    def init_drone_info_table(self):

        # 添加表格样式配置
        style = ttk.Style()
        style.configure("Treeview.Heading",
                        font=('黑体', config.title_font_size, 'bold'),
                        foreground='black',
                        background='#4A6984',
                        padding=5,
                        borderwidth=2,  # 增加边框宽度
                        relief="solid")  # 添加立体效果

        style.configure("Treeview",
                        font=('宋体', config.text_font_size),
                        rowheight=config.row_height,
                        borderwidth=2,  # 边框宽度
                        relief="solid",  # 立体边框
                        highlightthickness=1,  # 高亮边框厚度
                        fieldbackground='#F5F5F5',  # 单元格背景色
                        foreground='#333333',  # 文字颜色
                        bordercolor = "#999999",  # 明确定义边框颜色
                        lightcolor = "#CCCCCC",  # 定义亮边颜色
                        darkcolor = "#999999")  # 定义暗边颜色
        # # 添加单元格边框配置
        # style.element_create("Treeview.cell.border", "from", "default")
        # style.layout("Treeview.Item", [
        #     ("Treeview.cell.border", {"sticky": "nswe", "children": [
        #         ("Treeview.padding", {"sticky": "nswe", "children": [
        #             ("Treeview.image", {"sticky": "nswe"}),
        #             ("Treeview.text", {"sticky": "nswe"})
        #         ]})
        #     ]})
        # ])

        style.map("Treeview",
                background=[('selected', '#3C6E9F')],  # 选中行背景色
                foreground=[('selected', 'white')])  # 选中行文字颜色        
        
        # 创建表格
        self.drone_table = ttk.Treeview(self.left_upper,
                                        show='headings',
                                        columns=('id', 'x', 'y', 'z', 'speed'),
                                        height=20,
                                        style="Treeview")

        # 配置列
        columns = [
            ('id', '无人机ID', 100),
            ('x', 'X坐标', 50),
            ('y', 'Y坐标', 50),
            ('z', 'Z坐标', 50),
            ('speed', '速度', 100)
        ]

        # 添加列样式
        for col_id, col_text, width in columns:
            self.drone_table.column(col_id,
                                    width=width,
                                    anchor='center')
            self.drone_table.heading(col_id, text=col_text)  # 关键添加
            # 添加列分隔线
            style.configure("Treeview", 
                bordercolor="#CCCCCC",  # 边框颜色
                lightcolor="#CCCCCC",   # 亮边颜色
                darkcolor="#999999"    # 暗边颜色
            )


        # 添加滚动条
        self.table_vsb = ttk.Scrollbar(self.left_upper,
                                       orient="vertical",
                                       command=self.drone_table.yview)
        self.drone_table.configure(yscrollcommand=self.table_vsb.set)

        # 布局
        self.drone_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.table_vsb.pack(side=tk.RIGHT, fill=tk.Y)

    def update_drone_info(self, drone_data_list):
        """更新无人机表格数据"""

        def _update():
            # 清空现有数据
            for item in self.drone_table.get_children():
                self.drone_table.delete(item)
            # print(f"[调试] 收到无人机数据：{len(drone_data_list)}条")

            # 插入新数据
            for drone in drone_data_list:
                self.drone_table.insert('', 'end', values=(
                    drone['id'],
                    f"{drone['x']:.1f}",
                    f"{drone['y']:.1f}",
                    f"{drone['z']:.1f}",
                    drone['speed']
                ))

        # 确保在主线程更新
        self.master.after(0, _update)


    def update_progress_log(self, message):
        """在同一行更新仿真进度（覆盖前一条）"""

        def _update():
            # 1. 解除日志框的只读状态
            self.log_info.config(state=tk.NORMAL)

            # 添加红色文本标签
            self.log_info.tag_config('progress', foreground='red')

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
                self.log_info.insert(f"{target_line}.0", f"> {message}", 'progress')
            else:
                # 10. 未找到时追加新行（正常插入）
                self.log_info.insert(tk.END, f"> {message}\n", 'progress')
            
            # 11. 自动滚动到最新内容
            # self.log_info.see(tk.END)
            
            # 12. 恢复只读状态
            self.log_info.config(state=tk.DISABLED)
        
        # 13. 通过主线程队列保证线程安全
        self.master.after(0, _update)

    def update_generation_progress(self, current_frame, total_frames):
        """更新动画生成进度（与仿真进度分离）"""

        def _update():
            self.log_info.config(state=tk.NORMAL)
            message = f"生成进度：第{current_frame + 1}/{total_frames}帧"
            target_tag = "gen_progress"

            # 配置专属样式
            self.log_info.tag_config(target_tag, foreground='blue')

            # 查找已有进度行
            content = self.log_info.get("1.0", tk.END)
            lines = content.split("\n")
            target_line = -1
            for idx, line in enumerate(lines):
                if "生成进度" in line:
                    target_line = idx + 1  # Tkinter行号从1开始
                    break

            # 更新或插入新行
            if target_line != -1:
                self.log_info.delete(f"{target_line}.0", f"{target_line}.end")
                self.log_info.insert(f"{target_line}.0", f"> {message}", target_tag)
            else:
                self.log_info.insert(tk.END, f"> {message}\n", target_tag)

            self.log_info.see(tk.END)
            self.log_info.config(state=tk.DISABLED)

        # 确保在主线程执行
        self.master.after(0, _update)


    def init_metrics_table(self):
        """初始化固定行列的性能指标表格"""
        style = ttk.Style()

        style.configure("Treeview.Heading",
                        font=('黑体', config.title_font_size, 'bold'),
                        foreground='black',
                        background='#4A6984',
                        padding=5,
                        borderwidth=2,  # 增加边框宽度
                        relief="solid")  # 添加立体效果

        style.configure("Treeview",
                        font=('宋体', config.text_font_size),
                        rowheight=config.row_height,
                        borderwidth=2,  # 边框宽度
                        relief="solid",  # 立体边框
                        highlightthickness=1,  # 高亮边框厚度
                        fieldbackground='#F5F5F5',  # 单元格背景色
                        foreground='#333333',  # 文字颜色
                        bordercolor = "#999999",  # 明确定义边框颜色
                        lightcolor = "#CCCCCC",  # 定义亮边颜色
                        darkcolor = "#999999")  # 定义暗边颜色

        # # 添加单元格边框配置
        # style.element_create("Treeview.cell.border", "from", "default")
        # style.layout("Treeview.Item", [
        #     ("Treeview.cell.border", {"sticky": "nswe", "children": [
        #         ("Treeview.padding", {"sticky": "nswe", "children": [
        #             ("Treeview.image", {"sticky": "nswe"}),
        #             ("Treeview.text", {"sticky": "nswe"})
        #         ]})
        #     ]})
        # ])

        style.map("Treeview",
                background=[('selected', '#3C6E9F')],  # 选中行背景色
                foreground=[('selected', 'white')])  # 选中行文字颜色
        # 创建指标表格
        self.metrics_table = ttk.Treeview(self.left_lower,
                                        show='headings',
                                        columns=('metric', 'value', 'unit'),
                                        height=20,
                                        style="Treeview")

        # 配置列（固定三列）
        columns = [
            ('metric', '性能指标', 120),
            ('value', '实时数值', 100),
            ('unit', '单位', 60)
        ]

        for col_id, col_text, width in columns:
            self.metrics_table.column(col_id,
                                      width=width,
                                      anchor='center')
            self.metrics_table.heading(col_id, text=col_text)
            # 添加列分隔线
            style.configure("Treeview",
                            bordercolor="#CCCCCC",  # 边框颜色
                            lightcolor="#CCCCCC",  # 亮边颜色
                            darkcolor="#999999"  # 暗边颜色
                            )
        # 插入固定行数据（与无人机表格风格一致）
        metric_items = [
            ('数据包投递率(PDR)', '', '%'),
            ('平均端到端延迟', '', 'ms'),
            ('路由负载(RL)', '', ''),
            ('平均吞吐量', '', 'Kbps'),
            ('平均跳数', '', '跳'),
            ('冲突次数', '', '次'),
            ('平均MAC延迟', '', 'ms')
        ]

        for item in metric_items:
            self.metrics_table.insert('', 'end', values=item)

        # 添加滚动条
        self.table_vsb2 = ttk.Scrollbar(self.left_lower,
                                       orient="vertical",
                                       command=self.drone_table.yview)
        self.metrics_table.configure(yscrollcommand=self.table_vsb2.set)

        # 布局
        self.metrics_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.table_vsb2.pack(side=tk.RIGHT, fill=tk.Y)

        # 销毁原有文本控件

    def update_metrics_info(self, metrics):
        """更新指标表格数据"""

        def _update():
            # 映射指标名称到表格行号
            metric_map = {
                'pdr': 0,
                'e2e': 1,
                'rl': 2,
                'throughput': 3,
                'hop': 4,
                'collision': 5,
                'mac_delay': 6
            }

            # 更新表格数据
            for metric_key, row_idx in metric_map.items():
                value = metrics.get(metric_key, 0)
                formatted_value = f"{value:.2f}" if isinstance(value, float) else str(value)
                self.metrics_table.set(self.metrics_table.get_children()[row_idx], 'value', formatted_value)

        self.master.after(0, _update)

    # def update_metrics_info(self, metrics):
    #     """更新性能指标区域"""
    #
    #     def _update():
    #         text = (f"数据包投递率(PDR): {metrics['pdr']:.2f}%\n"
    #                 f"平均端到端延迟(E2E): {metrics['e2e']:.2f} ms\n"
    #                 f"路由负载(RL): {metrics['rl']:.2f}\n"
    #                 f"平均吞吐量: {metrics['throughput']:.2f} Kbps\n"
    #                 f"平均跳数: {metrics['hop']:.2f}\n"
    #                 f"冲突次数: {metrics['collision']}\n"
    #                 f"平均MAC延迟: {metrics['mac_delay']:.2f} ms\n")
    #
    #         self.metrics_info.config(state=tk.NORMAL)
    #         self.metrics_info.delete(1.0, tk.END)
    #         self.metrics_info.insert(tk.END, text)
    #         self.metrics_info.config(state=tk.DISABLED)
    #
    #     self.master.after(0, _update)

    def on_canvas_click(self, event):
        """点击Canvas时判断具体子图"""
        if not self.sim_running:
            return  # 仿真未运行，直接返回
        # 将点击坐标转换为图形坐标
        x, y = event.x, event.y
        # 遍历所有子图，检查点击位置
        for idx, ax in enumerate(self.axs):
            bbox = ax.bbox
            # 注意：Tkinter坐标原点在左上角，而Matplotlib的bbox是左下角
            if ((bbox.x0 < x < bbox.x1) and (self.canvas.get_tk_widget().winfo_height() - bbox.y1
                                             < y <
                                             self.canvas.get_tk_widget().winfo_height() - bbox.y0)):

                self.open_interactive_view(ax,idx)
                break

    def open_interactive_view(self, target_ax, target_idx):
        """打开可交互窗口，并传递仿真数据"""
        popup = tk.Toplevel(self.master)
        popup.title("交互式视图 - " + target_ax.get_title())

        # 创建新Canvas并绑定仿真数据
        fig = plt.figure(figsize=(16, 12))
        ax_new = fig.add_subplot(111, projection='3d')
        canvas = FigureCanvasTkAgg(fig, master=popup)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 设置标题
        ax_new.set_title(target_ax.get_title(), fontsize=config.fig_font_size)

        if target_idx == 0 or target_idx == 2:
            from visualization.scatter import get_ax_state

            cached_state = get_ax_state(target_ax)
            if cached_state:
                # 使用缓存数据重建图形
                ax_new.clear()
                # 绘制无人机
                # 绘制无人机和编号
                for drone in cached_state["drones"]:  # 改为遍历字典结构
                    # 绘制无人机点
                    ax_new.scatter(*drone["coords"], c='red', s=50, alpha=0.7)

                    # 添加编号标注（使用存储的ID）
                    ax_new.text(
                        drone["coords"][0] + 1,  # X偏移
                        drone["coords"][1] + 1,  # Y偏移
                        drone["coords"][2],  # Z保持原值
                        f'#{drone["id"]}',  # 从字典获取真实ID
                        fontsize=16,
                        color='darkred',
                        ha='left',
                        va='bottom'
                    )

                # 绘制链路（使用新的链路数据结构）
                for link in cached_state["links"]:
                    # 从链路数据中提取坐标点
                    start_coords = link["coords"][0]
                    end_coords = link["coords"][1]
                    x = [start_coords[0], end_coords[0]]
                    y = [start_coords[1], end_coords[1]]
                    z = [start_coords[2], end_coords[2]]

                    ax_new.plot(
                        x, y, z,
                        color='#404040',
                        linestyle='-',
                        linewidth=2,
                        alpha=0.7,
                        solid_capstyle='round'
                    )
                canvas.draw()
            # 设置标题和坐标轴
            ax_new.set_title(target_ax.get_title(), fontsize=config.fig_font_size)
            ax_new.set_xlim(0, config.MAP_LENGTH)
            ax_new.set_ylim(0, config.MAP_WIDTH)
            ax_new.set_zlim(0, config.MAP_HEIGHT)
            ax_new.set_xlabel('X (m)')
            ax_new.set_ylabel('Y (m)')
            ax_new.set_zlabel('Z (m)')

        if target_idx == 1:
            # 获取无人机轨迹数据
            if self.sim and len(self.sim.drones) > 1:  # 假设显示无人机1的轨迹
                trajectory = self.sim.drones[1].mobility_model.trajectory

                if trajectory:
                    ax_new.clear()

                    # 提取三维坐标
                    x = [p[0] for p in trajectory]
                    y = [p[1] for p in trajectory]
                    z = [p[2] for p in trajectory]

                    # 提取三维坐标数据
                    x_coords = [p[0] for p in trajectory]
                    y_coords = [p[1] for p in trajectory]
                    z_coords = [p[2] for p in trajectory]

                    # 绘制轨迹
                    ax_new.plot(x_coords, y_coords, z_coords,
                            color='blue', linewidth=2, alpha=0.8)

                    # 计算动态范围（包含10%的边距）
                    margin_ratio = 0.1
                    x_min, x_max = self._get_axis_range(x_coords, margin_ratio)
                    y_min, y_max = self._get_axis_range(y_coords, margin_ratio)
                    z_min, z_max = self._get_axis_range(z_coords, margin_ratio)
                    # 绘制轨迹
                    ax_new.plot(x, y, z,
                                color='blue',
                                linewidth=2,
                                alpha=0.8,
                                label=f'无人机 {config.chosen_drone} 运动轨迹')

                    # 设置动态坐标轴
                    ax_new.set_title(target_ax.get_title(), fontsize=config.fig_font_size)
                    ax_new.set_xlim(x_min, x_max)
                    ax_new.set_ylim(y_min, y_max)
                    ax_new.set_zlim(z_min, z_max)

                    ax_new.set_xlabel('X (m)')
                    ax_new.set_ylabel('Y (m)')
                    ax_new.set_zlabel('Z (m)')
                    ax_new.legend()

                    # 设置视角
                    # ax_new.view_init(elev=30, azim=45)

                    canvas.draw()

    def _get_axis_range(self, values, margin_ratio=0.1):
        """根据数据计算带边距的坐标轴范围"""
        if not values:  # 空数据时返回默认范围
            return 0, config.MAP_LENGTH

        v_min = min(values)
        v_max = max(values)
        span = v_max - v_min

        # 处理所有点相同的情况
        if span == 0:
            span = config.MAP_LENGTH * 0.1  # 默认使用10%的地图长度
            v_min -= span / 2
            v_max += span / 2
        else:
            margin = span * margin_ratio
            v_min -= margin
            v_max += margin

        return max(0, v_min), min(v_max, config.MAP_LENGTH)


    # def _draw_interactive_view(self, ax):
    #     """在指定Axes上绘制无人机和链路（使用最新仿真数据）"""
    #     ax.clear()
    #     if not self.sim:
    #         return
    #
    #     # 绘制无人机节点（红色）
    #     for drone in self.sim.drones:
    #         ax.scatter(
    #             drone.coords[0], drone.coords[1], drone.coords[2],
    #             c='red', s=30, alpha=0.7
    #         )
    #
    #     # 绘制通信链路（黑色虚线）
    #     for drone1 in self.sim.drones:
    #         for drone2 in self.sim.drones:
    #             if drone1.identifier != drone2.identifier:
    #                 distance = euclidean_distance_3d(drone1.coords, drone2.coords)
    #                 if distance <= maximum_communication_range():
    #                     x = [drone1.coords[0], drone2.coords[0]]
    #                     y = [drone1.coords[1], drone2.coords[1]]
    #                     z = [drone1.coords[2], drone2.coords[2]]
    #                     ax.plot(x, y, z, color='black', linestyle='dashed', linewidth=1)
    #
    #     # 设置坐标轴
    #     ax.set_xlim(0, config.MAP_LENGTH)
    #     ax.set_ylim(0, config.MAP_WIDTH)
    #     ax.set_zlim(0, config.MAP_HEIGHT)
    #     ax.set_title("交互式网络拓扑视图")
    #     ax.set_xlabel('X (m)')
    #     ax.set_ylabel('Y (m)')
    #     ax.set_zlabel('Z (m)')
    #
    # def copy_axes_content(self, src_ax, dst_ax):
    #     """深度复制子图内容（包含无人机和链路）"""
    #     # 清空目标子图
    #     dst_ax.clear()
    #
    #     # 复制所有图形元素
    #     for artist in src_ax.get_children():
    #         # 复制散点图（PathCollection）
    #         if isinstance(artist, PathCollection):
    #             # 提取3D坐标（直接使用无人机坐标）
    #             offsets = artist.get_offsets()
    #             # 显式设置颜色为红色，忽略原图的cmap
    #             if offsets.size > 0:
    #                 # 提取3D坐标（PathCollection的offsets是2D数组，需手动添加z轴）
    #                 z = artist.get_3d_properties() if hasattr(artist, 'get_3d_properties') else 0
    #                 dst_ax.scatter(
    #                     offsets[:, 0],
    #                     offsets[:, 1],
    #                     z,  # 正确传递z轴数据
    #                     # c='red',  # 强制设置为红色
    #                     s=artist.get_sizes(),
    #                     alpha=artist.get_alpha()
    #                 )
    #         # 复制连线（Line3D）
    #         elif isinstance(artist, Line3D):
    #             x, y, z = artist.get_data_3d()
    #             dst_ax.plot(
    #                 x, y, z,
    #                 color=artist.get_color(),
    #                 linestyle=artist.get_linestyle(),
    #                 linewidth=artist.get_linewidth()
    #             )
    #     # 复制坐标轴设置
    #     dst_ax.set_xlim(src_ax.get_xlim())
    #     dst_ax.set_ylim(src_ax.get_ylim())
    #     dst_ax.set_zlim(src_ax.get_zlim())
    #     dst_ax.set_title(src_ax.get_title(),fontsize=config.fig_font_size)
    #     dst_ax.set_xlabel(src_ax.get_xlabel())
    #     dst_ax.set_ylabel(src_ax.get_ylabel())
    #     dst_ax.set_zlabel(src_ax.get_zlabel())



    #=============================GIF==================================

    def load_gif(self, gif_path):
        """加载GIF并显示第一帧"""
        try:
            self.gif_frames = []
            gif = Image.open(gif_path)
            for frame in ImageSequence.Iterator(gif):
                frame = frame.convert('RGBA')
                photo = ImageTk.PhotoImage(frame)
                self.gif_frames.append(photo)

            # 只显示第一帧，不启动动画
            if self.gif_frames:
                self.gif_label.config(image=self.gif_frames[0])
                self.gif_label.image = self.gif_frames[0]  # 保持引用

            self.current_frame = 0
        except Exception as e:
            print(f"GIF加载失败: {str(e)}")

    def animate_gif(self):
        """GIF动画循环"""
        if self.sim_running and self.gif_frames:
            if self.current_frame < len(self.gif_frames):
                self.gif_label.config(image=self.gif_frames[self.current_frame])
                self.gif_label.image = self.gif_frames[self.current_frame]  # 保持引用
                self.current_frame += 1
            else:
                self.current_frame = 0  # 循环播放
            self.master.after(100, self.animate_gif)

    def update_gif_display(self, gif_path):
        """线程安全的GIF更新方法"""

        def _update():
            self.load_gif(gif_path)
            self.animate_gif()  # 如果需要自动播放

        # 通过主线程调度
        self.master.after(0, _update)
    # def load_gif(self, gif_path):
    #     """加载并播放GIF"""
    #     try:
    #         self.gif_frames = []
    #         gif = Image.open(gif_path)
    #         for frame in ImageSequence.Iterator(gif):
    #             frame = frame.convert('RGBA')
    #             photo = ImageTk.PhotoImage(frame)
    #             self.gif_frames.append(photo)
    #         self.current_frame = 0
    #         self.animate_gif()
    #     except Exception as e:
    #         print(f"GIF加载失败: {str(e)}")
    #
    # def animate_gif(self):
    #     """GIF动画循环"""
    #
    #     if self.current_frame < len(self.gif_frames):
    #         self.gif_label.config(image=self.gif_frames[self.current_frame])
    #         self.current_frame += 1
    #     else:
    #         self.current_frame = 0  # 循环播放
    #     self.master.after(100, self.animate_gif)












    # def process_plot_queue(self):
    #     """主线程定期处理绘图队列"""
    #     while self.plot_queue:
    #         task = self.plot_queue.pop(0)
    #         task()
    #     self.master.after(100, self.process_plot_queue)
    #
    # def generate_and_display_gif(self):
    #     """后台生成GIF并在完成后更新界面"""
    #     if self.visualizer is None:
    #         print("Visualizer未初始化，无法生成GIF")
    #         return
    #
    #     # 调用visualizer生成GIF
    #     gif_path = self.visualizer.create_animations()
    #
    #     # 在主线程更新GUI
    #     if gif_path:
    #         self.master.after(0, lambda: self.display_gif(gif_path))
    #
    # def display_gif(self, gif_path):
    #     """在GUI中显示GIF"""
    #     try:
    #         gif = Image.open(gif_path)
    #         frames = []
    #         for frame in ImageSequence.Iterator(gif):
    #             frame = frame.convert('RGBA')  # 转换为RGBA模式以支持透明度
    #             photo = ImageTk.PhotoImage(frame)
    #             frames.append(photo)
    #
    #         # 保存帧引用，防止被垃圾回收
    #         self.gif_frames = frames
    #         self.current_frame = 0
    #
    #         # 开始播放动画
    #         self.animate_gif()
    #     except Exception as e:
    #         print(f"Error displaying GIF: {e}")
    #
    # def animate_gif(self):
    #     """逐帧播放GIF"""
    #     if self.current_frame < len(self.gif_frames):
    #         self.gif_label.config(image=self.gif_frames[self.current_frame])
    #         self.current_frame += 1
    #         # 每100ms更新一帧（可根据GIF实际帧率调整）
    #         self.master.after(100, self.animate_gif)
    #
    # def check_thread_and_start_gif(self):
    #     """检查仿真线程是否完成，完成后启动GIF生成"""
    #     if self.sim_thread.is_alive():
    #         self.master.after(100, self.check_thread_and_start_gif)
    #     else:
    #         # 仿真线程完成后，启动GIF生成线程
    #         self.gif_thread = Thread(target=self.generate_and_display_gif)
    #         self.gif_thread.start()


if __name__ == "__main__":
    root = tk.Tk()
    app = UavNetSimGUI(root)
    root.mainloop()