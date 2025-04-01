import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import matplotlib.animation as animation

# 打开 GIF 图片
gif_path = "uav_network_simulation.gif"  # 替换为你的 GIF 文件路径
image = Image.open(gif_path)

# 获取 GIF 的所有帧
frames = []
try:
    while True:
        image.seek(len(frames))  # 跳到下一帧
        frame = np.array(image.copy().convert("RGBA"))
        frames.append(frame)
except EOFError:
    pass  # GIF 文件结束

# 创建 Matplotlib 图表
fig, ax = plt.subplots()
im = ax.imshow(frames[0])
ax.set_title("Interactive GIF Viewer")
ax.set_xlabel("X-axis")
ax.set_ylabel("Y-axis")

# 定义更新帧的函数
def update_frame(i):
    im.set_data(frames[i])
    return im,

# 创建动画
ani = animation.FuncAnimation(
    fig, update_frame, frames=len(frames), interval=100, blit=True, repeat=True
)

# 添加交互功能
def on_hover(event):
    if event.inaxes == ax:
        x, y = int(event.xdata), int(event.ydata)
        if 0 <= x < frames[0].shape[1] and 0 <= y < frames[0].shape[0]:
            pixel_value = frames[0][y, x]
            ax.set_title(f"Pixel Value: {pixel_value}")
            fig.canvas.draw_idle()

def on_click(event):
    if event.inaxes == ax:
        x, y = int(event.xdata), int(event.ydata)
        if 0 <= x < frames[0].shape[1] and 0 <= y < frames[0].shape[0]:
            pixel_value = frames[0][y, x]
            print(f"Clicked at ({x}, {y}): Pixel Value = {pixel_value}")

# 连接事件
fig.canvas.mpl_connect('motion_notify_event', on_hover)
fig.canvas.mpl_connect('button_press_event', on_click)

# 显示图表
plt.show()