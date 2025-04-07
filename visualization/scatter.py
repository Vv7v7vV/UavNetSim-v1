import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from utils import config
from utils.util_function import euclidean_distance_3d
from phy.large_scale_fading import maximum_communication_range


# scatter.py
def scatter_plot(simulator, gui_canvas=None):
    """
    绘制无人机分布和通信链路的散点图（支持GUI模式）
    """

    def _plot():
        """实际绘图逻辑（在主线程中执行）"""
        # 创建新图形
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')

        # 绘制无人机和通信链路
        for drone1 in simulator.drones:
            for drone2 in simulator.drones:
                if drone1.identifier != drone2.identifier:
                    # 绘制无人机位置
                    ax.scatter(
                        drone1.coords[0], drone1.coords[1], drone1.coords[2],
                        c='red', s=30, alpha=0.7
                    )
                    # 计算距离并绘制通信链路
                    distance = euclidean_distance_3d(drone1.coords, drone2.coords)
                    if distance <= maximum_communication_range():
                        x = [drone1.coords[0], drone2.coords[0]]
                        y = [drone1.coords[1], drone2.coords[1]]
                        z = [drone1.coords[2], drone2.coords[2]]
                        ax.plot(x, y, z, color='black', linestyle='dashed', linewidth=1)

        # 设置坐标轴范围和标签
        ax.set_xlim(0, config.MAP_LENGTH)
        ax.set_ylim(0, config.MAP_WIDTH)
        ax.set_zlim(0, config.MAP_HEIGHT)
        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')
        ax.set_zlabel('Z (m)')

        # GUI模式：更新Canvas
        if gui_canvas:
            gui_canvas.figure = fig
            gui_canvas.draw()
            plt.close(fig)  # 关闭临时图形，防止内存泄漏
        # 非GUI模式：直接显示
        else:
            plt.show()

    # 分派任务到主线程
    if gui_canvas:
        # 获取 Tkinter Widget 的父窗口（如主窗口）
        root = gui_canvas.get_tk_widget().master
        root.after(0, _plot)  # 通过 root 调度任务
    else:
        _plot()