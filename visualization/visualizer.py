import os
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch
from mpl_toolkits.mplot3d import proj3d
from matplotlib.widgets import Slider, Button, TextBox
from utils import config
import io
import matplotlib.patheffects as path_effects
from visualization.scatter import scatter_plot
import threading

# Add 3D arrow class definition that handles arrows in 3D view
class Arrow3D(FancyArrowPatch):
    """
    Class for drawing arrows in 3D view
    """
    def __init__(self, xs, ys, zs, *args, **kwargs):
        FancyArrowPatch.__init__(self, (0, 0), (0, 0), *args, **kwargs)
        self._verts3d = xs, ys, zs

    def do_3d_projection(self, renderer=None):
        xs3d, ys3d, zs3d = self._verts3d
        xs, ys, zs = proj3d.proj_transform(xs3d, ys3d, zs3d, self.axes.M)
        self.set_positions((xs[0], ys[0]), (xs[1], ys[1]))
        # Calculate average z value as depth
        avg_z = np.mean(zs)
        return avg_z
        
    def draw(self, renderer):
        FancyArrowPatch.draw(self, renderer)

class SimulationVisualizer:
    """
    Visualize UAV network simulation process, including movement trajectories and communication status
    """
    
    def __init__(self,
                 simulator,
                 output_dir="vis_results",
                 vis_frame_interval=50000,
                 fig=None,
                 ax=None,
                 gui_mode=False,
                 gui_canvas=None,
                 master=None):
        """
        Initialize visualizer
        
        Parameters:
            simulator: simulator instance
            output_dir: output directory
            vis_frame_interval: interval for visualization frames (microseconds)


        """

        self.simulator = simulator
        self.output_dir = output_dir
        self.vis_frame_interval = vis_frame_interval

        # # 新增GUI集成参数
        # if fig is None or ax is None:
        #     self.fig = plt.figure(figsize=(18, 6))
        #     self.ax_data = self.fig.add_subplot(121, projection='3d')
        #     self.ax_ack = self.fig.add_subplot(122, projection='3d')
        # else:
        #     self.fig = fig
        #     self.ax_data = ax[0] if isinstance(ax, (list, tuple)) else ax
        #     self.ax_ack = ax[1] if isinstance(ax, (list, tuple)) else ax

        os.makedirs(output_dir, exist_ok=True)
        self.drone_positions = {i: [] for i in range(self.simulator.n_drones)}
        
        # Store vis_frame_interval in microseconds
        self.vis_frame_interval = vis_frame_interval
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize data storage structures
        self.drone_positions = {i: [] for i in range(self.simulator.n_drones)}
        self.timestamps = []
        
        # Comm events tracking
        self.comm_events = []  # Store tuples (src_id, dst_id, packet_id, packet_type, timestamp)
        
        # Assign a fixed color to each UAV
        self.colors = plt.cm.tab10(np.linspace(0, 1, self.simulator.n_drones))
        
        # Color mapping for communication types
        self.comm_colors = {
            "DATA": "blue",
            "ACK": "green",
            "HELLO": "orange"
        }
        
        # Setup communication tracking
        self._setup_communication_tracking()
        
        # Reference for interactive elements
        self.interactive_fig = None
        self.interactive_slider = None
        self.frame_times = []

        # # 新增部分，创建子图对象并在类中保存
        # self.fig = plt.figure(figsize=(18, 6))
        # self.ax_data = self.fig.add_subplot(121, projection='3d')
        # self.ax_ack = self.fig.add_subplot(122, projection='3d')
        # 预排序通信事件
        self.comm_events.sort(key=lambda x: x[4])

        # 添加GUI模式下的绘图控制
        # self.gui_canvas = None
        self.master = master  # 保存主窗口引用
        self.gui_mode = gui_mode  # 新增GUI模式标志
        self.gui_canvas = gui_canvas  # 保存Canvas引用
    
    def _setup_communication_tracking(self):
        """Setup tracking for communication events"""
        # Save the original unicast_put method
        original_unicast_put = self.simulator.channel.unicast_put
        
        # Rewrite unicast_put method to track communications
        def tracked_unicast_put(message, dst_drone_id):
            # Call the original method
            result = original_unicast_put(message, dst_drone_id)
            
            # Record communication event
            packet, _, src_drone_id, _, _ = message
            
            # Add packet type differentiation
            packet_id = packet.packet_id
            
            # Identify packet type based on ID range
            if packet_id >= 20000:
                packet_type = "ACK"
            elif packet_id >= 10000:
                packet_type = "HELLO"
            else:
                packet_type = "DATA"
            
            self.track_communication(src_drone_id, dst_drone_id, packet_id, packet_type)
            
            return result
        
        # Replace the method
        self.simulator.channel.unicast_put = tracked_unicast_put
    
    def track_drone_positions(self):
        """
        Record current drone positions
        """
        current_time = self.simulator.env.now / 1e6  # Convert to seconds
        self.timestamps.append(current_time)
        
        for i, drone in enumerate(self.simulator.drones):
            position = drone.coords  # 这已经包含了（x, y, z）坐标
            self.drone_positions[i].append(position)
    
    def track_communication(self, src_id, dst_id, packet_id, packet_type="DATA"):
        """
        Record communication event
        """
        current_time = self.simulator.env.now / 1e6  # Convert to seconds
        # Record complete communication event information
        self.comm_events.append((src_id, dst_id, packet_id, packet_type, current_time))
    
    def _draw_visualization_frame(self, fig, current_time):
        """
        Draw visualization elements on two side-by-side axes
        
        Parameters:
            fig: matplotlib figure to draw on
            current_time: current simulation time (seconds)
        """
        if self.gui_mode:  # GUI模式下的特殊处理
            for ax in [self.ax_data, self.ax_ack]:
                ax.clear()

            self.fig.suptitle(f"UAV Network Simulation at t={int(current_time * 1e6)}μs", fontsize=14)
        else:
            self.fig = plt.figure(figsize=(18, 6))
            self.ax_data = self.fig.add_subplot(121, projection='3d')
            self.ax_ack = self.fig.add_subplot(122, projection='3d')

        fig.suptitle(f"UAV Network Simulation at t={int(current_time*1e6)}μs", fontsize=14)
        
        # Create left and right subplots for DATA and ACK only
        ax_data = fig.add_subplot(121, projection='3d')
        ax_ack = fig.add_subplot(122, projection='3d')
        
        # Set titles for subplots
        ax_data.set_title("DATA Packets")
        ax_ack.set_title("ACK Packets")
        
        # Set axis labels and limits for both subplots
        for ax in [self.ax_data, self.ax_ack]:
            ax.set_xlabel('X (m)')
            ax.set_ylabel('Y (m)')
            ax.set_zlabel('Z (m)')
            ax.set_xlim(0, config.MAP_LENGTH)
            ax.set_ylim(0, config.MAP_WIDTH)
            ax.set_zlim(0, config.MAP_HEIGHT)
            ax.grid(True)
        
        # Get drone positions at current time
        drone_positions = self._get_drone_positions(current_time)
        
        # Draw drones on both subplots
        for ax in [ax_data, ax_ack]:
            self._draw_drones(ax, drone_positions)
        
        # Draw communication links
        display_window = self.vis_frame_interval / 1e6  # Convert to seconds

        ############################################################################
        import bisect

        # 提前将comm_events按时间排序（确保已排序）
        # 创建一个时间戳列表，用于二分查找
        event_timestamps = [e[4] for e in self.comm_events]

        # 计算起始和结束时间
        start_time = current_time - display_window
        end_time = current_time

        # 使用bisect查找起始和结束位置
        left = bisect.bisect_left(event_timestamps, start_time)
        right = bisect.bisect_right(event_timestamps, end_time)

        # 提取时间窗口内的事件
        recent_comms = self.comm_events[left:right]
        ############################################################################


        # recent_comms = [e for e in self.comm_events
        #               if current_time - display_window <= e[4] <= current_time]
        
        # Get only the latest communication events for each src-dst pair
        latest_data_comms = self._get_latest_comms(recent_comms, "DATA")
        latest_ack_comms = self._get_latest_comms(recent_comms, "ACK")
        
        # Draw DATA packet links on left subplot
        self._draw_data_links(ax_data, latest_data_comms, drone_positions)
        
        # Draw ACK packet links on right subplot
        self._draw_ack_links(ax_ack, latest_ack_comms, drone_positions)
        
        # Add legends
        data_legend = [Line2D([0], [0], color=self.comm_colors["DATA"], lw=2, label="DATA Packets")]
        ax_data.legend(handles=data_legend, loc='upper right')
        
        ack_legend = [Line2D([0], [0], color=self.comm_colors["ACK"], lw=2, label="ACK Packets")]
        ax_ack.legend(handles=ack_legend, loc='upper right')

        if self.gui_mode:
            self.fig.canvas.draw_idle()
        else:
            plt.show()

    def _get_latest_comms(self, comms, packet_type):
        """
        Get only the latest communication for each src-dst pair
        
        Parameters:
            comms: List of communication events
            packet_type: Type of packet (DATA, ACK, HELLO)
            
        Returns:
            List of latest communication events for each src-dst pair
        """
        # Filter by packet type
        type_comms = [e for e in comms if e[3] == packet_type]
        
        # Dictionary to store latest comm for each src-dst pair
        latest_comms_dict = {}
        
        # For each src-dst pair, keep only the comm with the latest timestamp
        for comm in type_comms:
            src_id, dst_id = comm[0], comm[1]
            pair_key = (src_id, dst_id)
            
            # If this is the first comm for this pair, or has a later timestamp
            if pair_key not in latest_comms_dict or comm[4] > latest_comms_dict[pair_key][4]:
                latest_comms_dict[pair_key] = comm
        
        # Return the values (latest comms)
        return list(latest_comms_dict.values())

    def create_animations(self):
        """Create GIF animation of the simulation (线程安全版本)"""
        import io
        from PIL import Image
        
        if not self.timestamps:
            print("No timestamps available for animation")
            return
        
        try:
            print("正在创建动态 GIF...")
            animation_frames = []
            
            # Calculate frames based on vis_frame_interval
            min_time = min(self.timestamps)
            max_time = max(self.timestamps)
            frame_interval_sec = self.vis_frame_interval / 1e6  # Convert microseconds to seconds
            
            # Create frame times at regular intervals based on vis_frame_interval
            self.frame_times = []
            current_time = min_time
            while current_time <= max_time:
                self.frame_times.append(current_time)
                current_time += frame_interval_sec
            
            n_frames = len(self.frame_times)
            print(f"Generating {n_frames} frames with interval of {frame_interval_sec} seconds")

            # # Create a new figure for this frame
            # fig = plt.figure(figsize=(18, 6))
            #
            # for i, time_point in enumerate(self.frame_times):
            #     print(f"Generating frame {i+1}/{n_frames}", end="\r")
            #
            #     # # Create a new figure for this frame
            #     # fig = plt.figure(figsize=(18, 6))
            #
            #
            #     # Clear previous plots if any
            #     plt.clf()
            #
            #
            #     # Draw visualization elements
            #     self._draw_visualization_frame(fig, time_point)
            #
            #     # Save the figure to a BytesIO buffer
            #     buf = io.BytesIO()
            #     plt.savefig(buf, format='png', dpi=100)
            #
            #     # plt.close(fig)
            #
            #     # Reset buffer position and open image
            #     buf.seek(0)
            #     img = Image.open(buf)
            #     # Convert to RGB mode to ensure compatibility
            #     img = img.convert('RGB')
            #     # Create a copy of the image to ensure it's fully loaded
            #     img_copy = img.copy()
            #     animation_frames.append(img_copy)
            #     buf.close()

            for i, time_point in enumerate(self.frame_times):
                # 使用独立的Figure生成GIF，避免与GUI的fig冲突
                print(f"Generating frame {i + 1}/{n_frames}", end="\r")

                # 创建临时Figure
                fig = plt.figure(figsize=(18, 6))
                ax_data = fig.add_subplot(121, projection='3d')
                ax_ack = fig.add_subplot(122, projection='3d')

                # 调用绘图方法
                self._draw_visualization_frame(fig, time_point)

                # 保存到缓冲区
                buf = io.BytesIO()
                plt.savefig(buf, format='png', dpi=100)
                plt.close(fig)  # 关闭临时Figure释放内存

                # 处理图像
                buf.seek(0)
                img = Image.open(buf).convert('RGB')
                animation_frames.append(img.copy())
                buf.close()
            print("\nSaving animation...")
            
            # # Save the animation
            # animation_file = os.path.join(self.output_dir, "uav_network_simulation.gif")
            # if animation_frames:
            #     # Save with explicit parameters
            #     animation_frames[0].save(
            #         animation_file,
            #         format='GIF',
            #         save_all=True,
            #         append_images=animation_frames[1:],
            #         duration=50,  # ms per frame
            #         loop=1,  # Loop indefinitely
            #         optimize=True,
            #         quality=70,    # Reduce quality slightly (0-100)
            #         # Reduce colors if needed
            #         colors=128     # Maximum number of colors
            #     )
            #     print(f"Animation saved to {animation_file}")
            # else:
            #     print("No frames were generated for the animation")


            if animation_frames:
                # 保存GIF
                animation_file = os.path.join(self.output_dir, "uav_network_simulation.gif")
                animation_frames[0].save(
                    animation_file,
                    save_all=True,
                    append_images=animation_frames[1:],
                    duration=100,  # 控制播放速度（毫秒/帧）
                    loop=0,  # 无限循环
                    optimize=True
                )
                print(f"Animation saved to {animation_file}")
                return animation_file  # 返回文件路径供GUI显示
            else:
                print("No frames generated for animation")
                return None

        except Exception as e:
            print(f"Error creating animation: {e}")
            print("Continuing with interactive visualization...")
            return None
    
    def run_visualization(self):
        """
        Run visualization process
        """
        # Use vis_frame_interval directly (it's already in microseconds)
        tracking_interval_us = self.vis_frame_interval
        
        # Start tracking drone positions
        def track_positions():
            while True:
                self.track_drone_positions()
                yield self.simulator.env.timeout(tracking_interval_us)
        
        # Register tracking process
        self.simulator.env.process(track_positions())
    
    def finalize(self):
        if self.gui_mode and self.master:
            # 在主线程中调用散点图
            # self.gui_canvas.master.after(0, lambda: scatter_plot(self.simulator, self.gui_canvas))
            # self.master.after(0, lambda: scatter_plot(self.simulator, self.gui_canvas))
            self.create_animations()
            self.create_interactive_visualization()

            # 通过线程生成GIF，避免阻塞主线程
            def safe_create_animations():
                gif_path = self.create_animations()  # 调用生成GIF的方法
                if gif_path:
                    # 在主线程中调用消息提示
                    self.master.after(0, lambda: self._show_completion_message(gif_path))

            # 启动后台线程
            from threading import Thread
            Thread(target=safe_create_animations).start()
            print("Finalizing visualization...")

        else:
            # GUI模式仅更新当前状态
            current_time = self.simulator.env.now / 1e6
            self._draw_visualization_frame(self.fig,current_time)
            if self.gui_canvas:
                self.gui_canvas.draw_idle()

    # def _safe_scatter_plot(self):
    #     """线程安全的散点图绘制"""
    #     from visualization.scatter import scatter_plot
    #     scatter_plot(self.simulator, gui_canvas=self.gui_canvas)

    def create_interactive_visualization(self):
        """Create an interactive visualization with a slider for time navigation"""
        if not self.timestamps:
            print("No timestamps available for interactive visualization")
            return
        # 添加主线程检查
        if self.gui_mode:
            return

        print("Creating interactive visualization...")
        
        # Make sure frame_times is populated
        if not self.frame_times:
            min_time = min(self.timestamps)
            max_time = max(self.timestamps)
            frame_interval_sec = self.vis_frame_interval / 1e6
            
            current_time = min_time
            while current_time <= max_time:
                self.frame_times.append(current_time)
                current_time += frame_interval_sec
        
        # Convert frame times to microseconds for the slider
        frame_times_us = [t * 1e6 for t in self.frame_times]
        
        # Create figure with fixed subplots - this is key to solving the error
        fig = plt.figure(figsize=(15, 7))
        plt.subplots_adjust(bottom=0.15)  # Make room for controls
        
        # Create the subplots once and keep them
        gs = fig.add_gridspec(1, 2, hspace=0, wspace=0.2)
        ax_data = fig.add_subplot(gs[0, 0], projection='3d')
        ax_ack = fig.add_subplot(gs[0, 1], projection='3d')
        
        # Add slider axes
        slider_ax = plt.axes([0.2, 0.05, 0.65, 0.03])
        time_slider = Slider(
            slider_ax, 'Time (μs)', 
            min(frame_times_us), max(frame_times_us),
            valinit=frame_times_us[0],
            valstep=frame_times_us  # Discrete steps based on frame times
        )
        
        # Add text box and button for direct time input
        text_ax = plt.axes([0.2, 0.01, 0.2, 0.03])
        time_text = TextBox(text_ax, 'Go to time (μs): ', initial='')
        
        button_ax = plt.axes([0.45, 0.01, 0.1, 0.03])
        goto_button = Button(button_ax, 'Go')
        
        def update_plot(current_time):
            # Clear existing content on axes
            ax_data.clear()
            ax_ack.clear()
            
            # Set titles
            ax_data.set_title("DATA Packets")
            ax_ack.set_title("ACK Packets")
            
            # Update main figure title
            fig.suptitle(f"UAV Network Simulation at t={int(current_time*1e6)}μs", fontsize=14)
            
            # Set axis properties for both subplots
            for ax in [ax_data, ax_ack]:
                ax.set_xlabel('X (m)')
                ax.set_ylabel('Y (m)')
                ax.set_zlabel('Z (m)')
                ax.set_xlim(0, config.MAP_LENGTH)
                ax.set_ylim(0, config.MAP_WIDTH)
                ax.set_zlim(0, config.MAP_HEIGHT)
                ax.grid(True)
            
            # Get drone positions
            drone_positions = self._get_drone_positions(current_time)
            
            # Draw drones on both subplots
            self._draw_drones(ax_data, drone_positions)
            self._draw_drones(ax_ack, drone_positions)
            
            # Get recent communications
            display_window = self.vis_frame_interval / 1e6
            recent_comms = [e for e in self.comm_events 
                            if current_time - display_window <= e[4] <= current_time]
            
            # Filter by packet type and get latest only
            latest_data_comms = self._get_latest_comms(recent_comms, "DATA")
            latest_ack_comms = self._get_latest_comms(recent_comms, "ACK")
            
            # Draw communication links
            self._draw_data_links(ax_data, latest_data_comms, drone_positions)
            self._draw_ack_links(ax_ack, latest_ack_comms, drone_positions)
            
            # Add legends
            data_legend = [Line2D([0], [0], color=self.comm_colors["DATA"], lw=2, label="DATA Packets")]
            ax_data.legend(handles=data_legend, loc='upper right')
            
            ack_legend = [Line2D([0], [0], color=self.comm_colors["ACK"], lw=2, label="ACK Packets")]
            ax_ack.legend(handles=ack_legend, loc='upper right')
        
        def update(val):
            try:
                # Get current time from slider
                current_time_us = time_slider.val
                current_time = current_time_us / 1e6  # Convert to seconds
                
                # Update plot with new time
                update_plot(current_time)
                
                # Redraw
                fig.canvas.draw_idle()
            except Exception as e:
                print(f"Error updating plot: {e}")
        
        def goto_time(event):
            try:
                # Get time from text box
                time_us = float(time_text.text)
                
                # Find the closest frame time
                closest_time_us = min(frame_times_us, key=lambda x: abs(x - time_us))
                
                # Update slider to trigger update
                time_slider.set_val(closest_time_us)
                
                # Update textbox to show actual time used
                time_text.set_val(str(int(closest_time_us)))
            except ValueError:
                print("Invalid time format. Please enter a number.")
            except Exception as e:
                print(f"Error going to time: {e}")

        if not self.gui_mode:  # 只在非GUI模式下创建交互式窗口
            # Connect the update function to the slider
            time_slider.on_changed(update)

            # Connect the goto function to the button
            goto_button.on_clicked(goto_time)

            # Initial plot
            update_plot(self.frame_times[0])

            # Save reference to interactive elements
            self.interactive_fig = fig
            self.interactive_slider = time_slider

            # Show the interactive visualization
            plt.show()

            print("Interactive visualization created. Close the plot window to continue.")

    def _get_drone_positions(self, current_time):
        """Get drone positions at a specific time"""
        drone_positions = {}
        for drone_id in range(len(self.drone_positions)):
            positions = self.drone_positions[drone_id]
            timestamps = self.timestamps
            
            if positions and timestamps:
                # Find closest timestamp
                closest_idx = min(range(len(timestamps)), 
                               key=lambda i: abs(timestamps[i] - current_time))
                
                # Get position at closest timestamp
                if 0 <= closest_idx < len(positions):
                    drone_positions[drone_id] = positions[closest_idx]
        return drone_positions

    def _draw_drones(self, ax, drone_positions):
        """Draw drones on the given axis with embedded ID numbers"""
        for drone_id, position in drone_positions.items():
            color = self.colors[drone_id]
            
            # Use smaller marker size for drone representation
            ax.scatter(position[0], position[1], position[2], 
                    color=color, s=150, alpha=0.7, edgecolors='black')
            
            # Add ID text with outline for better visibility
            # Set high zorder to ensure text appears above other elements
            text = ax.text(position[0], position[1], position[2], 
                     f"{drone_id}", ha='center', va='center', 
                     color='white', fontweight='bold', fontsize=10,
                     path_effects=[path_effects.withStroke(linewidth=2, foreground='black')],
                     zorder=100)  # Ensure text is displayed on top layer

    def _draw_data_links(self, ax, data_comms, drone_positions):
        """Draw DATA packet links on the given axis with smaller packet ID boxes"""
        for src_id, dst_id, packet_id, _, _ in data_comms:
            if src_id in drone_positions and dst_id in drone_positions:
                start_pos = drone_positions[src_id]
                end_pos = drone_positions[dst_id]
                
                # Draw an arrow for DATA packet
                arrow = Arrow3D([start_pos[0], end_pos[0]], 
                              [start_pos[1], end_pos[1]], 
                              [start_pos[2], end_pos[2]],
                              mutation_scale=15, 
                              lw=2, 
                              arrowstyle="-|>", 
                              color=self.comm_colors["DATA"])
                
                ax.add_artist(arrow)
                
                # Add more visible packet ID at midpoint
                mid_x, mid_y, mid_z = [(start_pos[i] + end_pos[i]) / 2 for i in range(3)]
                
                # Draw a smaller, more compact background for the packet ID
                ax.text(mid_x, mid_y, mid_z, str(packet_id), 
                      ha='center', va='center', fontsize=7, fontweight='bold',
                      bbox=dict(boxstyle="round,pad=0.2", facecolor='lightblue', 
                                alpha=0.8, edgecolor=self.comm_colors["DATA"], linewidth=1.5),
                      zorder=99)  # Display above other elements but below drone IDs

    def _draw_ack_links(self, ax, ack_comms, drone_positions):
        """Draw ACK packet links on the given axis with smaller packet ID boxes"""
        for src_id, dst_id, packet_id, _, _ in ack_comms:
            if src_id in drone_positions and dst_id in drone_positions:
                start_pos = drone_positions[src_id]
                end_pos = drone_positions[dst_id]
                
                # Draw a straight line for ACK packet
                ax.plot([start_pos[0], end_pos[0]], 
                       [start_pos[1], end_pos[1]], 
                       [start_pos[2], end_pos[2]],
                       color=self.comm_colors["ACK"], 
                       linewidth=2)
                
                # Add more visible packet ID at midpoint
                mid_x, mid_y, mid_z = [(start_pos[i] + end_pos[i]) / 2 for i in range(3)]
                
                # Draw a smaller, more compact background for the ACK packet ID
                ax.text(mid_x, mid_y, mid_z, str(packet_id), 
                       ha='center', va='center', fontsize=7, fontweight='bold',
                       bbox=dict(boxstyle="round,pad=0.2", facecolor='lightgreen', 
                                alpha=0.8, edgecolor=self.comm_colors["ACK"], linewidth=1.5),
                       zorder=99)  # Display above other elements but below drone IDs

    def _show_completion_message(self, gif_path):
        """显示GIF生成完成提示"""
        from tkinter import messagebox  # 确保在主线程导入
        if self.master:
            messagebox.showinfo("Animation Saved", f"GIF saved to: {gif_path}")