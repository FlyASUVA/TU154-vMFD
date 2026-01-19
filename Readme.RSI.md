# Radio Situation Indicator (RSI) | 无线电态势指示器

> **A custom situational awareness gauge for the Tu-154 vMFD project.** > **图-154 vMFD 项目的自定义态势感知仪表。**

This is an fictional instrument. The RSI transforms the complex mental math of flying a DME Arc into a simple visual task. By mapping the aircraft's position relative to a station-centered scale, pilots can maintain the arc simply by keeping the indicator dot on the circle.

这是一个现实中不存在的领航仪表。RSI 将飞 DME 弧时复杂的脑力计算转化为简单的视觉任务。通过将飞机位置映射到以导航台为中心的刻度上，飞行员只需保持光点在圆周上即可轻松维持DME弧程序飞行。

<img width="640" height="480" alt="image" src="https://github.com/user-attachments/assets/c1d6cbd5-2786-46a0-bbf9-da36048f71fc" />


---

## Key Features | 核心功能

### 1. Station-Centered Visualization
**以导航台为中心的上帝视角**
Provides a "god's eye" view centered on the VOR/DME station, complete with selected TO/FROM radials and 10-degree increments.
提供以 VOR/DME 台为中心的俯视图，包含选定的 TO/FROM 径向线及 10 度间隔的辅助刻度。

### 2. Intuitive Arc Tracking
**直观的弧线追踪**
The circular scale represents the target DME distance. The aircraft dot moves relative to this scale (inside/outside/on-track) to provide instant situational awareness.
圆形刻度代表目标 DME 距离。飞机光点相对于刻度移动（内侧/外侧/航迹上），仪表将提供即时的态势感知。

### 3. Dynamic Deviation Monitoring
**动态偏差监控**
The aircraft indicator updates in real-time, changing color to warn pilots if they deviate from the arc's protected maneuver zone.
飞机指示器实时更新，并根据偏离 DME 弧保护区的情况改变颜色（绿/黄/红）向飞行员发出视觉警告。

---

## Visual Guide | 视觉指南

| Component | Color | Description |
| :--- | :--- | :--- |
| **Scale Ring** | White | Represents the target DME Arc distance (Radius). <br> 白色圆环代表目标 DME 弧的距离（半径）。 |
| **Aircraft Dot** | **Green** / **Red** | **Green**: On arc / within tolerance. **Red**: Deviated / outside protected zone. <br> **绿色**：在弧上/公差内。 **红色**：偏离/超出保护区。 |
| **TO Radial** | <span style="color:magenta">**Magenta**</span> | The selected CRS radial (Head). <br> 选定的 CRS 径向线（向台/切入方向）。 |
| **FROM Radial** | <span style="color:cyan">**Cyan**</span> | The reciprocal radial (Tail). <br> 反向径向线（背台/切出方向）。 |

---

## Usage | 使用说明

1.  **Tune NAV1**: Set the frequency of the VOR/DME station.
    设置 NAV1 为 VOR/DME 台频率。
2.  **Set Parameters**: Enter the **ARC DIST** (Target Distance), **INBOUND**, and **OUTBOUND** radials on the RSI page.
    在 RSI 页面输入 **ARC DIST**（目标距离），以及 **INBOUND**（切入）和 **OUTBOUND**（切出）径向线。
3.  **Fly the Dot**:
    * **Dot Inside Circle**: You are too close (< Target DME). Turn outward.
    * **Dot Outside Circle**: You are too far (> Target DME). Turn inward.
    * **Dot On Circle**: You are perfectly tracking the arc.
    **追踪光点**：
    * **光点在圈内**：距离太近，需向外转。
    * **光点在圈外**：距离太远，需向内转。
    * **光点在圈上**：完美切弧。
