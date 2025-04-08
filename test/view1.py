import tkinter as tk
from PIL import Image, ImageTk

class GIFPlayer:
    def __init__(self, root, gif_path):
        self.root = root
        self.gif_path = gif_path
        self.label = tk.Label(root)
        self.label.pack()
        self.load_gif()

    def load_gif(self):
        # 打开 GIF 图片
        self.image = Image.open(self.gif_path)
        self.frames = []
        self.current_frame = 0

        # 遍历 GIF 的每一帧
        try:
            while True:
                self.image.seek(len(self.frames))  # 跳到下一帧
                frame = self.image.copy().convert("RGBA")
                self.frames.append(ImageTk.PhotoImage(frame))
        except EOFError:
            pass  # GIF 文件结束

        # 开始播放动画
        self.update_frame()

    def update_frame(self):
        # 更新当前帧
        self.label.config(image=self.frames[self.current_frame])
        self.current_frame = (self.current_frame + 1) % len(self.frames)
        # 设置下一帧的更新时间（根据帧的持续时间）
        self.root.after(self.get_frame_duration(self.current_frame), self.update_frame)

    def get_frame_duration(self, frame_index):
        # 获取当前帧的持续时间（单位：毫秒）
        self.image.seek(frame_index)
        return self.image.info.get("duration", 100)  # 默认值为100毫秒

# 创建 Tkinter 窗口
root = tk.Tk()
root.title("GIF Player")

# 替换为你的 GIF 文件路径
gif_path = "../uav_network_simulation.gif"  # 替换为你的 GIF 文件路径
player = GIFPlayer(root, gif_path)

# 运行 Tkinter 主循环
root.mainloop()