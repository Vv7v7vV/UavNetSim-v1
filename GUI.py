import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import subprocess
import os

matplotlib.rcParams['font.family'] = 'SimHei'  # 使用黑体
matplotlib.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题


class SimulationGUI:
    def __init__(self, root):

        self.root = root
        self.root.title("无人机通信仿真")
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
        self.fig = plt.figure(figsize=(8, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.canvas_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 初始化时显示 origin.png
        self.display_initial_image()

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

    def display_initial_image(self):
        # 尝试加载 origin.png
        img = mpimg.imread("Initial.png")
        ax = self.fig.add_subplot(111)
        ax.imshow(img)
        ax.set_title("请点击按钮开始测试")
        ax.axis('off')
        self.canvas.draw()

    def run_simulation(self):
        # 调用main.py
        subprocess.run(["python", "test.py"])

        # 显示生成的图像
        self.display_images()

    def display_images(self):
        # 获取图像文件列表
        image_files = [f for f in os.listdir(".") if f.startswith("result") and f.endswith(".png")]
        image_files.sort()  # 按文件名排序

        # 清空画布
        self.fig.clear()

        # 动态创建子图
        num_images = len(image_files)
        if num_images == 0:
            ax = self.fig.add_subplot(111)
            ax.text(0.5, 0.5, "未产生图片", horizontalalignment='center', verticalalignment='center',
                    transform=ax.transAxes)
            ax.axis('off')
            self.canvas.draw()
            return

        # 创建子图
        for i, image_file in enumerate(image_files):
            ax = self.fig.add_subplot(num_images, 1, i + 1)
            img = mpimg.imread(image_file)
            ax.imshow(img)
            ax.set_title(f"Result {i + 1}")
            ax.axis('off')

        # 刷新画布
        self.canvas.draw()


if __name__ == "__main__":
    root = tk.Tk()
    app = SimulationGUI(root)
    root.mainloop()