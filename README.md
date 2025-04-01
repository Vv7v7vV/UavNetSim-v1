<div align="center">
<img src="./img/logo.png" width="650px">
</div>


<div align="center">
  <h1>UavNetSim-v1: A Simulation Platform for UAV Networks</h1>
  <img src="https://img.shields.io/badge/Github-%40ZihaoZhouSCUT-blue" height="20">
  <img src="https://img.shields.io/badge/Contribution-Welcome-yellowgreen" height="20">
  <img src="https://img.shields.io/badge/License-MIT-brightgreen" height="20">
  <h3>让模拟对新手更友好！ </h3>

</div>

这个基于 Python 的仿真平台可以真实地模拟无人机网络的各种组件，包括网络层、MAC 层和物理层，以及无人机移动模型、能源模型等。此外，该平台可以轻松扩展以满足不同用户的需求并开发自己的协议。

## Requirements
- Python >= 3.3 
- Simpy >= 4.1.1

## Features
在开始仿真之旅之前，我们建议您先阅读本节，其中提到了该平台的一些功能，以便您可以确定该平台是否满足您的开发或研究需求。

- 基于 Python（此仿真平台基于 Python 中的 SimPy 库开发）;
- 更适用于**路由协议**、**MAC 协议**和**运动控制算法**（如**拓扑控制**、**轨迹优化**）的开发和验证。未来，我们希望改进平台，以支持更多不同层的算法和协议;
- 支持**强化学习 （RL）** 和其他基于 AI 的算法;
- 易于扩展 （1.采用**模块化编程**，用户可以轻松添加自己设计的模块;2. 可以实现不同的应用场景，例如**飞行自组网 （FANET）、****无人机辅助数据收集**、**空地一体化网络**);
- **可视化性好**，该平台可以提供**无人机飞行轨迹**和**数据包转发路径**的可视化，便于直观分析协议的行为;
- 如果您从事无人机辅助无线通信系统，并希望**考虑更多跨层指标**（例如，端到端延迟、数据包传输率 （PDR）、吞吐量），那么此平台适合您

## Project structure
```
.
├── README.md
├── energy
│   └── energy_model.py
├── entities
│   ├── drone.py
│   └── packet.py
├── mac
│   ├── csma_ca.py
│   └── pure_aloha.py
├── mobility
│   ├── gauss_markov_3d.py
│   ├── random_walk_3d.py
│   ├── random_waypoint_3d.py
│   └── start_coords.py
├── phy
│   ├── channel.py
│   ├── large_scale_fading.py
│   └── phy.py
├── routing
│   ├── dsdv
│   │   ├── dsdv.py
│   │   ├── dsdv_packet.py
│   │   └── dsdv_routing_table.py
│   ├── grad
│   │   └── ...
│   ├── greedy
│   │   └── ...
│   ├── opar
│   │   └── ...
│   └── q_routing
│       └── ...
├── simulator
│   ├── metrics.py
│   └── simulator.py
├── topology
│   └── virtual_force
│       ├── vf_motion_control.py
│       ├── vf_neighbor_table.py
│       └── vf_packet.py
├── utils
│   ├── config.py
│   ├── ieee_802_11.py
│   └── util_function.py
├── visualization
│   ├── scatter.py
│   └── visualizer.py
└── main.py
```
这个项目的切入点是文件，我们甚至可以直接一键运行`main.py`，先睹为快，但是，我们建议你先阅读本节，了解这个仿真平台的模块化组成和相应的功能。

- `energy`：该模块实现了无人机的能量模型，包括飞行能耗和通信相关的能耗。
- `entities`：它包括定义模拟中关键实体的行为和结构的所有类。
- `mac`：它包括不同介质访问控制 （MAC） 协议的实施，例如 CSMA/CA、ALOHA。
- `mobility`：它包含无人机的不同 3-D 移动模型，例如，高斯-马尔可夫移动模型、随机游走和随机航路点。
- `phy`：主要包括物理层无线信道的建模，以及单播、广播和组播的定义。
- `routing`：它包括不同路由协议的实现，例如 DSDV、GRAd、贪婪路由、基于 Q-Learning 的路由等。
- `simulator`：它包含用于处理模拟的所有类和网络性能指标。
- `topology`包括无人机集群拓扑控制算法的实现。
- `utils`：包含关键配置参数和一些有用的功能。
- `visualization`：它可以提供无人机分布、飞行轨迹和数据包转发路径的可视化。

## Installation and usage
首先，下载此项目：
```
git clone https://github.com/Zihao-Felix-Zhou/UavNetSim-v1.git
```
Run `main.py`以开始模拟。

## Core logic
下图是 *UavNetSim* 中数据包传输的主要过程。“Drone's buffer” 是 SimPy 中的一个资源，其容量为 1，这意味着无人机一次最多可以发送一个数据包。如果需要传输的数据包很多，则需要按照无人机到达的时间顺序排队获取缓冲区资源。我们可以通过这种机制来模拟排队延迟。此外，我们注意到还有另外两个容器：```transmitting_queue``` 和 ```waiting_list```. 对于无人机自身产生或接收到的其他无人机接收但需要进一步转发的“数据包”和“控制数据包”，无人机会先放入 ```transmitting_queue```. 调用的函数```feed_packet``` 将每隔很短的时间内定期读取 ```transmitting_queue``` 头部的数据包， 并让它等待资源```buffer``` 。 需要注意的是，“ACK 数据包”直接等待缓冲区资源，而不会被放入```transmitting_queue```.

读取数据包后，将首先执行数据包类型确定。如果这个包是控制包（通常不需要决定下一跳），那么它将直接开始等待缓冲区资源。当这个包是数据包时，路由协议会执行下一跳选择，如果能找到合适的下一跳，那么这个数据包就可以开始等待缓冲区资源了，否则，这个数据包就会被放入```waiting_list```（现在主要是反应式路由协议）。一旦无人机获得相关的路由信息，它将从 ```waiting_list``` 获取此数据包并将其添加回 ```transmitting_queue```。

当数据包获得缓冲区资源时，将执行 MAC 协议以争夺无线信道。当下一跳成功接收到数据包时，需要确定数据包类型。例如，如果收到的数据包是数据包，则需要在 SIFS 时间后使用 ACK 数据包进行应答。此外，如果接收方是传入数据包的目的地，则会记录一些指标（PDR、端到端延迟等），否则，意味着这个数据包需要进一步中继，因此会被放入接收方的无人机```transmitting_queue``` 中。

<div align="center">
<img src="./img/transmitting_procedure.png" width="800px">
</div>


## 模块概述

### 路由协议

数据包路由在 UAV 网络中发挥着重要作用，它使不同 UAV 节点之间的协作成为可能。在这个项目中，实现了**贪婪路由**、**梯度路由 （GRAd）**、**目的地排序距离向量路由 （DSDV）**和一些**基于 RL 的路由协议**。下图说明了数据包路由的基本过程。更详细的信息可以在相应的论文 [1]-[5] 中找到。

<div align="center">
<img src="./img/routing.png" width="700px">
</div>
### 媒体访问控制 （MAC） 协议

在本项目中，实现了**基本的载波感知多路访问与冲突避免 （CSMA/CA）** 和 **Pure aloha**。我将简要概述本项目中实现的版本，并重点介绍本项目中如何实现信号干扰和冲突。下图是采用基本 CSMA/CA（无 RTS/CTS）协议时的数据包传输示例。当 Drone 想要传输数据包时：

1. 它首先需要等待 channel 空闲
2. 当 Channel 空闲时，无人机会启动定时器并等待一段 ```DIFS+backoff``` 时间，其中 ```Backoff``` 的时长与重传次数有关
3. 如果 timer 到 0 的整个递减没有被打断，那么无人机可以占用频道并开始发送数据包
4. 如果倒计时中断，则表示无人机输掉了竞争。然后无人机冻结计时器并等待频道再次空闲，然后再重新启动其计时器

<div align="center">
<img src="./img/csmaca.png" width="800px">
</div>
下图展示了采用纯 aloha 时的数据包传输流程。当无人机安装了纯 aloha 协议想要传输数据包时：

1. 它只是发送它，而不监听通道和随机回退
2. 发送数据包后，节点开始等待 ACK 数据包
3. 如果及时收到 ACK，则该过程将结束`mac_send`
4. 否则，节点将根据重传尝试的次数等待随机时间，然后再次发送数据包

<div align="center">
<img src="./img/pure_aloha.png" width="800px">
</div>
从上图中我们可以看到，导致数据包冲突的不仅仅是两架无人机同时发送数据包。如果两个数据包的传输时间重叠，也表示发生了冲突。因此，在我们的项目中，每架无人机每隔很短的时间间隔检查一次收件箱，并且有几件重要的事情要做（如下图所示）：

1. 删除 Inbox 中与当前时间的距离大于最大数据包传输延迟 2 倍的数据包记录。这减少了计算开销，因为可以保证这些数据包已经被处理，并且不会干扰尚未处理的数据包
2. 检查收件箱中的数据包记录，查看已完整传输的数据包
3. 如果有这样的记录，则在所有无人机的 Inbox 记录中，找到其他在传输时间上与该数据包重叠的数据包，并使用它们来计算 SINR。

<div align="center">
<img src="./img/reception_logic.png" width="800px">
</div>
### 移动模型

移动性模型是更真实地展示无人机网络特性的最重要因素之一。在本项目中，实现了 **Gauss-Markov 3D 移动模型**、**随机游走 3D 移动模型**和**随机航点 3D 移动模型**。具体来说，由于在离散时间仿真中很难实现无人机的连续运动，因此我们设置 ```position_update_interval``` 来定期更新无人机的位置，即假设无人机在这个时间间隔内连续移动。如果```position_update_interval```时间间隔较小，则模拟精度会更高，但相应的模拟时间会更长。因此，将需要权衡取舍。此外，无人机更新方向的时间间隔也可以手动设置。两种机动性模型下单架无人机在仿真后 100 秒内的轨迹图如下：

<div align="center">
<img src="./img/mobility_model.png" width="800px">
</div>
### 能源模型

我们平台的能源模型基于 Y. Zeng 等人的工作。下图显示了不同无人机飞行速度所需的功率。能耗等于功率乘以此速度下的飞行时间。

<div align="center">
<img src="./img/energy_model.png" width="400px">
</div>
### 运动控制

该平台还支持用户为无人机集群网络设计运动控制算法。在当前版本中，实现了一种基于虚拟力的运动控制算法[8]，该算法结合了来自区域中心点的吸引力和来自相邻无人机的排斥力。通过应用此算法，可以将初始且可能断开连接的网络自组织成双连接网络。上图演示了运动控制后网络拓扑的变化。

<div align="center">
<img src="./img/virtual_force.png" width="800px">
</div>

如何使用？In ```entities/drone.py```, replace the ```mobility_model``` with ```motion_controller```:
```python
from topology.virtual_force.vf_motion_control import VfMotionController

class Drone:
  def __init__(self, env, node_id, coords, speed, inbox, simulator):
    ...
    # self.mobility_model = GaussMarkov3D(self)  REMEMBER TO COMMENT THIS SENTENCE OUT!
    self.motion_controller = VfMotionController(self)
    ...
```

### 可视化

该平台支持数据包传输过程以及无人机飞行轨迹的交互式可视化。在这里，我要感谢 @superboySB（Zipeng Dai 博士）为此功能做出了贡献！

<div align="center">
<img src="./img/visualization.gif" width="900px">
</div>

可以在以下位置启用可视化：```main.py```
```python
import simpy
from utils import config
from simulator.simulator import Simulator
from visualization.visualizer import SimulationVisualizer

if __name__ == "__main__":
    # Simulation setup
    env = simpy.Environment()
    channel_states = {i: simpy.Resource(env, capacity=1) for i in range(config.NUMBER_OF_DRONES)}
    sim = Simulator(seed=2025, env=env, channel_states=channel_states, n_drones=config.NUMBER_OF_DRONES)
    
    # Add the visualizer to the simulator
    # Use 20000 microseconds (0.02s) as the visualization frame interval
    visualizer = SimulationVisualizer(sim, output_dir=".", vis_frame_interval=20000)
    visualizer.run_visualization()

    # Run simulation
    env.run(until=config.SIM_TIME)
    
    # Finalize visualization
    visualizer.finalize()
```
在这个项目的当前版本中，当用户运行 ```main.py```, 程序会显示无人机初始位置分布的图，然后关闭窗口，程序将继续运行。模拟结束后，会显示一架无人机的飞行轨迹和无人机的最终位置，关闭这些窗口并等待片刻，将显示交互窗口。

## 性能评估

我们的“FlyNet”平台支持评估多个性能指标，如下所示：

- **数据包传输率 （PDR）：**PDR 是所有目标无人机成功接收的数据包总数与所有源无人机生成的数据包总数的比率。应该注意的是，PDR 不包括冗余数据包。PDR 可以反映路由协议的可靠性。
- **平均端到端延迟 （E2E Delay）：**E2E 延迟是数据包从源无人机到达目标无人机的平均时间延迟。通常，数据包传输中的延迟包括“排队延迟”、“访问延迟”、“传输延迟”、“传播延迟（小到可以忽略不计）”和“处理延迟”。
- **标准化路由负载 （NRL）：**NRL 是所有无人机发送的所有路由控制数据包与目标无人机接收的数据包数量的比率。
- **平均吞吐量**：在我们的平台中，吞吐量的计算方式是：每当目的地收到数据包时，数据包的长度除以数据包的端到端延迟（因为 E2E 延迟涉及此数据包的重传）
- **跳数**：跳数是数据包应通过的路由器输出端口数。

我们的仿真平台可以根据您的研究需求进行扩展，包括设计您自己的无人机移动模型（在文件夹 ```mobility``` ), mac 协议（在文件夹```mac```), 路由协议（在文件夹```routing```)等。接下来，我们以路由协议为例，介绍用户如何设计自己的算法。

* 在文件夹 ```routing``` 下创建一个新包 (不要忘记添加 ```__init__.py```)
* 路由协议的主程序必须包含以下函数：

  * ```def next_hop_selection(self, packet)```  
  * ```def packet_reception(self, packet, src_drone_id)```

* 确认代码逻辑正确后，即可导入自己设计的模块```drone.py``` 并在无人机上安装路由模块
   ```python
   from routing.dsdv.dsdv import Dsdv  # import your module
   ...
   class Drone:
     def __init__(self, env, node_id, coords, speed, inbox, simulator):
       ...
       self.routing_protocol = Dsdv(self.simulator, self)  # install
       ...
   ```

## Reference

[1] C. Perkins and P. Bhagwat, "[Highly dynamic destination-sequenced distance-vector routing (DSDV) for mobile computers](https://dl.acm.org/doi/abs/10.1145/190809.190336)," in *ACM SIGCOMM Computer Communication Review*, vol. 24, no. 4, pp. 234-244, 1994.  

[2] R. Poor, "Gradient routing in ad hoc networks", 2000, [www.media.mit.edu/pia/Research/ESP/texts/poorieeepaper.pdf](www.media.mit.edu/pia/Research/ESP/texts/poorieeepaper.pdf)  

[3] J. Boyan and M. Littman, "[Packet routing in dynamically changing networks: A reinforcement learning approach](https://proceedings.neurips.cc/paper/1993/hash/4ea06fbc83cdd0a06020c35d50e1e89a-Abstract.html)" in *Advances in Neural Information Processing Systems*, vol. 6, 1993.  

[4] W. S. Jung, J. Yim and Y. B. Ko, "[QGeo: Q-learning-based geographic ad hoc routing protocol for unmanned robotic networks](https://ieeexplore.ieee.org/abstract/document/7829268/)," in *IEEE Communications Letters*, vol. 21, no. 10, pp. 2258-2261, 2017.  

[5] M. Gharib, F. Afghah and E. Bentley, "[Opar: Optimized predictive and adaptive routing for cooperative uav networks](https://ieeexplore.ieee.org/abstract/document/9484489)," in *IEEE INFOCOM 2021-IEEE Conference on Computer Communications Workshops (INFOCOM WKSHPS)*, pp. 1-6, 2021.  

[6] A. Colvin, "[CSMA with collision avoidance](cn.overleaf.com/project/678e52bd44cc7c6c70e39d90)," *Computer Communications*, vol. 6, no. 5, pp. 227-235, 1983.  

[7] N. Abramson, "[The ALOHA system: Another alternative for computer communications](n.overleaf.com/project/678e52bd44cc7c6c70e39d90)," in *Proceedings of the November 17-19, 1970, Fall Joint Computer Conference*, pp. 281-285, 1970.  

[8] H. Liu, X. Chu, Y. -W. Leung and R. Du, "[Simple movement control algorithm for bi-connectivity in robotic sensor networks](https://ieeexplore.ieee.org/document/5555924)," in *IEEE Journal on Selected Areas in Communications*, vol. 28, no. 7, pp. 994-1005, 2010.

## 贡献

热忱欢迎贡献！

## 表达您的支持

如果这个项目对您有所帮助，请给出一个⭐建议！

## 许可证

该项目已获得 MIT 许可。
