import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from utils import config
from utils.util_function import euclidean_distance_3d
from phy.large_scale_fading import maximum_communication_range

import matplotlib
matplotlib.rcParams['font.family'] = 'SimHei'  # 使用黑体
matplotlib.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# scatter.py
# def scatter_plot(simulator, gui_canvas=None, target_ax=None):
#     """
#     绘制无人机分布和通信链路的散点图（支持GUI模式）
#     支持在指定子图上绘图（优先使用target_ax）
#     """
#
#     def _plot():
#         """
#         实际绘图逻辑（在主线程中执行）
#         """
#
#         # 创建新图形
#         # 如果提供了target_ax，直接使用该Axes对象
#         if target_ax:
#             ax = target_ax
#             ax.clear()  # 清空旧图形
#             ax.set_title("初始网络拓扑视图", fontsize=config.fig_font_size)  # 设置标题
#         else:
#             # 非GUI模式或未提供target_ax时创建新Figure
#             fig = plt.figure()
#             ax = fig.add_subplot(111, projection='3d')
#
#         # 绘制无人机和通信链路
#         for drone1 in simulator.drones:
#             for drone2 in simulator.drones:
#                 # 3. 排除自身比较
#                 if drone1.identifier != drone2.identifier:
#                     # 4. 绘制无人机位置（红色点）
#                     ax.scatter(
#                         drone1.coords[0], drone1.coords[1], drone1.coords[2],
#                         c='red', s=30, alpha=0.7
#                     )
#                     # 5. 计算两无人机之间的欧氏距离
#                     distance = euclidean_distance_3d(drone1.coords, drone2.coords)
#                     # 6. 如果距离在通信范围内，绘制通信链路
#                     if distance <= maximum_communication_range():
#                         x = [drone1.coords[0], drone2.coords[0]]
#                         y = [drone1.coords[1], drone2.coords[1]]
#                         z = [drone1.coords[2], drone2.coords[2]]
#                         ax.plot(x, y, z, color='black', linestyle='dashed', linewidth=1)
#
#         # 7. 设置3D坐标轴范围和标签（仅在未提供target_ax时生效）
#         if not gui_canvas:
#             if target_ax == 0:
#                 ax.set_title("初始网络拓扑视图", fontsize=config.fig_font_size)  # 设置标题
#             ax.set_xlim(0, config.MAP_LENGTH)
#             ax.set_ylim(0, config.MAP_WIDTH)
#             ax.set_zlim(0, config.MAP_HEIGHT)
#             ax.set_xlabel('X (m)')
#             ax.set_ylabel('Y (m)')
#             ax.set_zlabel('Z (m)')
#
#         # GUI模式：更新Canvas
#         if gui_canvas and target_ax:
#             gui_canvas.draw()  # 直接刷新Canvas
#         elif gui_canvas:
#             gui_canvas.figure = ax.figure
#             gui_canvas.draw()
#             plt.close(ax.figure)
#         else:
#             plt.show()
#
#     # 分派任务到主线程
#     if gui_canvas:
#         # 获取 Tkinter Widget 的父窗口（如主窗口）
#         root = gui_canvas.get_tk_widget().master
#         root.after(0, _plot)  # 通过 root 调度任务
#     else:
#         _plot()

# scatter.py

# 在模块顶部添加状态缓存字典
_ax_states = {}

def scatter_plot(simulator, gui_canvas=None, target_ax=None, interactive=True):
    """支持静态图与交互图的绘制模式"""
    def _plot():
        nonlocal interactive
        title = target_ax.get_title()
        if target_ax:
            ax = target_ax
            ax.clear()
        else:
            fig = plt.figure()
            ax = fig.add_subplot(111, projection='3d')

        for drone1 in simulator.drones:
            for drone2 in simulator.drones:
                if drone1.identifier != drone2.identifier:
                    # 绘制无人机位置
                    ax.scatter(
                        drone1.coords[0], drone1.coords[1], drone1.coords[2],
                        c='red', s=30, alpha=0.7
                    )
                    # 绘制通信链路
                    distance = euclidean_distance_3d(drone1.coords, drone2.coords)
                    if distance <= maximum_communication_range():
                        x = [drone1.coords[0], drone2.coords[0]]
                        y = [drone1.coords[1], drone2.coords[1]]
                        z = [drone1.coords[2], drone2.coords[2]]
                        ax.plot(x, y, z, color='black', linestyle='dashed', linewidth=1)

        # # 设置3D坐标轴
        # ax.set_zlim(0, config.MAP_HEIGHT)
        # ax.set_zlabel('Z (m)')

        # 设置标题和坐标轴
        ax.set_title(title, fontsize=config.fig_font_size)
        ax.set_xlim(0, config.MAP_LENGTH)
        ax.set_ylim(0, config.MAP_WIDTH)
        ax.set_zlim(0, config.MAP_HEIGHT)
        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')
        ax.set_zlabel('Z (m)')

        ax_id = id(target_ax) if target_ax else None

        # 缓存无人机坐标和链路数据
        state = {
            "drones": [d.coords for d in simulator.drones],
            "links": []
        }

        # 收集通信链路数据
        for i, d1 in enumerate(simulator.drones):
            for d2 in simulator.drones[i + 1:]:
                if euclidean_distance_3d(d1.coords, d2.coords) <= maximum_communication_range():
                    state["links"].append((d1.coords, d2.coords))

        # 更新缓存
        if ax_id:
            _ax_states[ax_id] = state


        # 非交互模式下关闭鼠标事件
        if not interactive:
            ax.mouse_init(rotate_btn=None, zoom_btn=None)

        # GUI模式：更新Canvas
        if gui_canvas and target_ax:
            gui_canvas.draw()
        elif gui_canvas:
            gui_canvas.figure = ax.figure
            gui_canvas.draw()
            plt.close(ax.figure)
        else:
            plt.show()

    # 分派任务到主线程
    if gui_canvas:
        root = gui_canvas.get_tk_widget().master
        root.after(0, _plot)
    else:
        _plot()


# 新增状态获取函数
def get_ax_state(ax):
    """获取缓存的子图状态"""
    return _ax_states.get(id(ax))