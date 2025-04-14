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

    def _center_window(self, width=600, height=400):  # 增大默认窗口尺寸
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
        entry_pady = 8

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
        self.speed_mode = ttk.Entry(main_frame)
        self.speed_mode.insert(0, str(config.HETEROGENEOUS))
        self.speed_mode.grid(
            row=3, column=1, sticky="ew", pady=entry_pady, padx=10)

        # 按钮区域
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=15)

        ttk.Button(btn_frame, text="确认", command=self._validate_input).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="取消", command=self.destroy).pack(side=tk.RIGHT, padx=10)

        # 配置网格布局权重
        main_frame.columnconfigure(1, weight=1)

    def _validate_input(self):
        """输入验证逻辑"""
        try:
            count = int(self.drone_count.get())
            time = int(self.sim_time.get())
            drones = int(self.selected_drones.get())

            if count <= 0 or time <= 0:
                raise ValueError("数值必须为正整数")
            if drones < 0:
                raise ValueError("无人机ID不能为负数")

            # 更新配置（实际项目中需同步修改config.py）
            config.NUMBER_OF_DRONES = count
            config.SIM_TIME = time * 1e6
            config.SELECTED_DRONES = drones

            self.gui_instance.log(f"参数已更新: "
                                  f"\n  -无人机: {count} "
                                  f"\n  -时间: {time}s "
                                  f"\n  -选中ID: {drones} ")
            self.destroy()

        except ValueError as e:
            messagebox.showerror("输入错误", f"无效的输入参数: {str(e)}")
