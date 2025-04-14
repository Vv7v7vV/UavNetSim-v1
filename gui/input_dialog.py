# gui/input_dialog.py
import tkinter as tk
from tkinter import ttk, messagebox
from utils import config


class InputDialog(tk.Toplevel):
    def __init__(self, parent, gui_instance):
        super().__init__(parent)
        self.parent = parent
        self.gui_instance = gui_instance  # 保存GUI实例引用
        self.title("仿真参数配置")
        self.option_add('*Font', config.title_font)  # 设置全局字体
        self._setup_ui()
        self._center_window()  # 使用新尺寸

    def _center_window(self, width=800, height=400):  # 增大默认窗口尺寸
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _setup_ui(self):
        """界面布局和控件初始化"""
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 使用更宽松的布局参数
        label_pady = 10
        entry_pady = 10

        # 参数输入组件
        ttk.Label(main_frame, text="无人机数量:").grid(
            row=0, column=0, sticky="w", pady=label_pady)
        self.drone_count = ttk.Entry(main_frame)
        self.drone_count.insert(0, str(config.NUMBER_OF_DRONES))
        self.drone_count.grid(
            row=0, column=1, sticky="ew", pady=entry_pady, padx=10)  # 增加横向间距

        ttk.Label(main_frame, text="仿真时间(s):").grid(
            row=1, column=0, sticky="w", pady=label_pady)
        self.sim_time = ttk.Entry(main_frame)
        time_seconds = int(config.SIM_TIME / 1e6)
        self.sim_time.insert(0, str(time_seconds))
        self.sim_time.grid(
            row=1, column=1, sticky="ew", pady=entry_pady, padx=10)

        ttk.Label(main_frame, text="显示路径的无人机ID:").grid(
            row=2, column=0, sticky="w", pady=label_pady)
        self.selected_drones = ttk.Entry(main_frame)
        self.selected_drones.insert(0, str(config.chosen_drone))
        self.selected_drones.grid(
            row=2, column=1, sticky="ew", pady=entry_pady, padx=10)



        ttk.Label(main_frame, text="无人机速度模式:").grid(
            row=3, column=0, sticky="w", pady=label_pady)
        self.mode_combobox = ttk.Combobox(
            main_frame,
            values=["同构网络", "异构网络"],
            state="readonly"
        )
        self.mode_combobox.grid(row=3, column=1, sticky="ew", pady=entry_pady, padx=10)
        self.mode_combobox.bind("<<ComboboxSelected>>", self._update_speed_input)

        # 初始化模式选择
        self.speed_mode = tk.IntVar(value=config.HETEROGENEOUS)
        self.mode_combobox.current(config.HETEROGENEOUS)

        # 创建速度输入区域容器
        self.speed_input_frame = ttk.Frame(main_frame)
        self.speed_input_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=entry_pady)

        # 立即初始化显示状态
        self._update_speed_input()  # 关键修复：初始化时触发一次更新

        # # 同构网络速度输入框
        # self.speed_label = ttk.Label(self.speed_input_frame, text="统一速度:",font=config.small_font)
        # self.speed_entry = ttk.Entry(self.speed_input_frame)

        # 异构网络提示文字
        # self.random_label = ttk.Label(self.speed_input_frame,
        #                               text="速度将随机分配",
        #                               foreground="gray",
        #                               font=config.small_font)





        # 按钮区域
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=15)

        ttk.Button(btn_frame, text="确认", command=self._validate_input).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="取消", command=self.destroy).pack(side=tk.RIGHT, padx=10)

        # 配置网格布局权重
        main_frame.columnconfigure(1, weight=1)

    def _update_speed_input(self, event=None):
        """根据选择的模式更新输入界面"""
        for widget in self.speed_input_frame.winfo_children():
            widget.destroy()

        if self.mode_combobox.current() == 0:  # 同构网络
            self.speed_input_frame.columnconfigure(0, weight=0)
            self.speed_input_frame.columnconfigure(1, weight=1)

            # 创建标签和输入框（使用grid布局更精准控制）
            ttk.Label(self.speed_input_frame, text="统一速度:").grid(row=0,
                                                                     column=0,
                                                                     sticky="e")
            self.speed_entry = ttk.Entry(self.speed_input_frame, width=10)
            self.speed_entry.grid(row=0, column=1, sticky="e")
            self.speed_entry.insert(0, str(config.BASE_SPEED))
        else:  # 异构网络
            # 创建灰色提示标签（使用pack布局居中显示）
            self.random_label = ttk.Label(
                self.speed_input_frame,
                text="速度将随机分配",
                foreground="gray60"
            )
            self.random_label.pack(fill=tk.X, anchor="e")  # 对齐

            # 强制更新布局（解决偶尔的显示残留问题）
        self.speed_input_frame.update_idletasks()


    def _validate_input(self):
        """输入验证逻辑"""
        try:
            count = int(self.drone_count.get())
            time = int(self.sim_time.get())
            drones = int(self.selected_drones.get())
            # 新增速度模式验证
            mode = self.mode_combobox.current()

            if count <= 0 or time <= 0:
                raise ValueError("数值必须为正整数")
            if drones < 0:
                raise ValueError("无人机ID不能为负数")
            if mode == 0:  # 同构网络
                speed_str = self.speed_entry.get().strip()
                if not speed_str:
                    raise ValueError("速度输入框不能为空")
                speed = int(self.speed_entry.get())
                if speed <= 0:
                    raise ValueError("速度必须为正值")
                config.BASE_SPEED = speed
                speed_info = f"统一速度: {speed}"
            else:  # 异构网络
                speed_info = "随机速度"

            # 更新配置（实际项目中需同步修改config.py）
            config.NUMBER_OF_DRONES = count
            config.SIM_TIME = time * 1e6
            config.SELECTED_DRONES = drones
            config.HETEROGENEOUS = mode

            self.gui_instance.log(f"参数已更新: "
                                  f"\n  -无人机: {count} "
                                  f"\n  -时间: {time}s "
                                  f"\n  -选中ID: {drones} "
                                  f"\n  -速度模式: {self.mode_combobox.get()}"
                                  f"\n   ·{speed_info}")

            self.destroy()

        except ValueError as e:
            messagebox.showerror("输入错误", f"无效的输入参数: {str(e)}")
