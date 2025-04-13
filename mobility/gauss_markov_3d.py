import random
import math
import numpy as np
from utils import config
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


class GaussMarkov3D:
    """
    3-D Gauss-Markov Mobility Model

    In this memorized model, the trajectory and velocity of the next motion at any time and any position
    depends on its previous position and velocity vector. There are three main parameters: 1) The first parameter
    is to determine how often the drone updates its position, velocity and other information, the denser this time
    interval is, the higher the simulation accuracy. 2) The second parameter is to determine how often the drone
    changes its velocity, direction, and other information. The smaller the interval is, the drone will change its
    motion direction frequently. 3) The last parameter is to control the randomness of the mobility.

    Attributes:
        model_identifier: model name
        my_drone: the drone that installed the mobility model
        position_update_interval: unit: us, determine how often the drone updates its position
        direction_update_interval: unit: us, determine how often the drone changes its direction
        alpha: control the randomness of the mobility
        move_counter: control the random seed
        b1, b2, b3: buffer zone, avoid getting too close to the boundary

    References:
        [1] Broyles D, Jabbar A., "Design and Analysis of a 3-D Gauss-Markov Model for Highly Dynamic Airborne
            Networks," in Proceedings of International Foundation for Telemetering, 2010.
        [2] ns-3 https://www.nsnam.org/docs/release/3.39/doxygen/d4/d4d/classns3_1_1_gauss_markov_mobility_model.html

    Author: Zihao Zhou, eezihaozhou@gmail.com
    Created at: 2024/1/17
    Updated at: 2025/1/7
    """

    def __init__(self, drone):
        self.model_identifier = 'GaussMarkov'
        self.my_drone = drone
        self.rng_mobility = random.Random(self.my_drone.identifier + self.my_drone.simulator.seed + 1)

        self.position_update_interval = 1*1e5  # 0.1s
        self.direction_update_interval = 5*1e5  # 0.5s
        self.alpha = 0.85
        self.move_counter = 1

        self.b1 = 1
        self.b2 = 1
        self.b3 = 1

        self.min_x = 0
        self.max_x = config.MAP_LENGTH

        self.min_y = 0
        self.max_y = config.MAP_WIDTH

        self.min_z = 0
        self.max_z = config.MAP_HEIGHT

        self.my_drone.simulator.env.process(self.mobility_update(self.my_drone))
        self.trajectory = []
        self.my_drone.simulator.env.process(self.show_trajectory())

    def mobility_update(self, drone):
        while True:
            env = drone.simulator.env
            drone_id = drone.identifier
            cur_position = drone.coords
            cur_velocity = drone.velocity
            cur_direction = drone.direction
            cur_pitch = drone.pitch
            velocity_mean = drone.velocity_mean
            direction_mean = drone.direction_mean
            pitch_mean = drone.pitch_mean

            # update the position of next time step
            if config.STATIC_CASE == 0:
                next_position_x = cur_position[0] + cur_velocity[0] * self.position_update_interval / 1e6
                next_position_y = cur_position[1] + cur_velocity[1] * self.position_update_interval / 1e6
                next_position_z = cur_position[2] + cur_velocity[2] * self.position_update_interval / 1e6
            else:
                next_position_x = cur_position[0]
                next_position_y = cur_position[1]
                next_position_z = cur_position[2]

            cur_speed = ((cur_velocity[0] ** 2) + (cur_velocity[1] ** 2) + (cur_velocity[2] ** 2)) ** 0.5

            if env.now % self.direction_update_interval == 0:  # update velocity and direction
                self.move_counter += 1
                alpha2 = 1.0 - self.alpha
                alpha3 = math.sqrt(1.0 - self.alpha * self.alpha)

                next_speed = (self.alpha * cur_speed + alpha2 * velocity_mean +
                              alpha3 * self.rng_mobility.normalvariate(0, 1))

                next_direction = (self.alpha * cur_direction + alpha2 * direction_mean +
                                  alpha3 * self.rng_mobility.normalvariate(0, 1))

                next_pitch = (self.alpha * cur_pitch + alpha2 * pitch_mean +
                              alpha3 * self.rng_mobility.normalvariate(0, 1))

                next_velocity_x = next_speed * math.cos(next_direction) * math.cos(next_pitch)
                next_velocity_y = next_speed * math.sin(next_direction) * math.cos(next_pitch)
                next_velocity_z = next_speed * math.sin(next_pitch)

                next_position = [next_position_x, next_position_y, next_position_z]

                if drone_id == 1:
                    self.trajectory.append(next_position)

                next_velocity = [next_velocity_x, next_velocity_y, next_velocity_z]
            else:
                next_position = [next_position_x, next_position_y, next_position_z]

                # velocity, direction and pitch should stay the same
                next_direction = cur_direction
                next_pitch = cur_pitch
                next_velocity = cur_velocity
                next_speed = ((cur_velocity[0] ** 2) + (cur_velocity[1] ** 2) + (cur_velocity[2] ** 2)) ** 0.5

            # wall rebound
            next_position, next_velocity, next_direction, next_pitch, direction_mean, pitch_mean = \
                self.boundary_test(next_position, next_velocity, direction_mean, pitch_mean)

            drone.coords = next_position
            drone.direction = next_direction
            drone.pitch = next_pitch
            drone.velocity = next_velocity
            drone.velocity_mean = velocity_mean
            drone.direction_mean = direction_mean
            drone.pitch_mean = pitch_mean

            yield env.timeout(self.position_update_interval)
            energy_consumption = (self.position_update_interval / 1e6) * drone.energy_model.power_consumption(drone.speed)
            drone.residual_energy -= energy_consumption

    def show_trajectory(self):
        yield self.my_drone.simulator.env.timeout(config.SIM_TIME-1)
        if self.my_drone.identifier == config.chosen_drone:  # 选择要显示的无人机
            # 通过simulator获取GUI的axes引用
            ax = self.my_drone.simulator.axs[1] if hasattr(self.my_drone.simulator, 'axs') else None

            if ax:  # GUI模式
                ax.clear()
                ax.set_title("无人机路径视图", fontsize=config.fig_font_size)

                # 提取三维坐标
                x = [p[0] for p in self.trajectory]
                y = [p[1] for p in self.trajectory]
                z = [p[2] for p in self.trajectory]

                # 设置坐标轴
                ax.set_xlim(0, config.MAP_LENGTH)
                ax.set_ylim(0, config.MAP_WIDTH)
                ax.set_zlim(0, config.MAP_HEIGHT)
                ax.set_xlabel('X (m)')
                ax.set_ylabel('Y (m)')
                ax.set_zlabel('Z (m)')

                # 提取三维坐标数据
                x_coords = [p[0] for p in self.trajectory]
                y_coords = [p[1] for p in self.trajectory]
                z_coords = [p[2] for p in self.trajectory]

                # 绘制轨迹
                ax.plot(x_coords, y_coords, z_coords,
                            color='blue', linewidth=2, alpha=0.8)

                # # 提取三维坐标数据
                # x_coords = [p[0] for p in self.trajectory]
                # y_coords = [p[1] for p in self.trajectory]
                # z_coords = [p[2] for p in self.trajectory]
                #
                # # 计算动态范围（包含10%的边距）
                # margin_ratio = 0.1
                # x_min, x_max = self._get_axis_range(x_coords, margin_ratio)
                # y_min, y_max = self._get_axis_range(y_coords, margin_ratio)
                # z_min, z_max = self._get_axis_range(z_coords, margin_ratio)
                # # 绘制轨迹
                # ax.plot(x_coords, y_coords, z_coords,
                #         color='blue', linewidth=2, alpha=0.8)
                #
                # # 设置动态坐标轴
                # ax.set_xlim(x_min, x_max)
                # ax.set_ylim(y_min, y_max)
                # ax.set_zlim(z_min, z_max)
                #
                # ax.set_xlabel('X (m)')
                # ax.set_ylabel('Y (m)')
                # ax.set_zlabel('Z (m)')
                # # 绘制轨迹
                # ax.plot(x, y, z,
                #             color='blue',
                #             linewidth=2,
                #             alpha=0.8,
                #             label=f'无人机 {config.chosen_drone} 运动轨迹')





                # 通知GUI更新
                if self.my_drone.simulator.gui_canvas:
                    self.my_drone.simulator.gui_canvas.draw_idle()
        else:
            x = []
            y = []
            z = []
            if self.my_drone.identifier == 1:  # you can choose which drone's trajectory you want to check
                for i in range(len(self.trajectory)):
                    x.append(self.trajectory[i][0])
                    y.append(self.trajectory[i][1])
                    z.append(self.trajectory[i][2])

                plt.figure()
                ax = plt.axes(projection='3d')
                ax.set_xlim(self.min_x, self.max_x)
                ax.set_ylim(self.min_y, self.max_y)
                ax.set_zlim(self.min_z, self.max_z)

                x = np.array(x)
                y = np.array(y)
                z = np.array(z)

                ax.plot(x, y, z)
                ax.set_xlabel('x')
                ax.set_ylabel('y')
                ax.set_zlabel('z')
                plt.show()

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


    # rebound scheme (refer to ns-3)
    def boundary_test(self, next_position, next_velocity, direction_mean, pitch_mean):
        if next_position[0] < self.min_x + self.b1 or next_position[0] > self.max_x - self.b1:
            next_velocity[0] = -next_velocity[0]
            direction_mean = np.pi - direction_mean
        if next_position[1] < self.min_y + self.b2 or next_position[1] > self.max_y - self.b2:
            next_velocity[1] = -next_velocity[1]
            direction_mean = -direction_mean
        if next_position[2] < self.min_z + self.b3 or next_position[2] > self.max_z - self.b3:
            next_velocity[2] = -next_velocity[2]
            pitch_mean = -pitch_mean

        next_position[0] = max(self.min_x + self.b1, min(next_position[0], self.max_x - self.b1))
        next_position[1] = max(self.min_y + self.b2, min(next_position[1], self.max_y - self.b2))
        next_position[2] = max(self.min_z + self.b3, min(next_position[2], self.max_z - self.b3))

        next_direction = direction_mean
        next_pitch = pitch_mean

        return next_position, next_velocity, next_direction, next_pitch, direction_mean, pitch_mean
