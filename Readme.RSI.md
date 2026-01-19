# Radio Situation Indicator (RSI) | 无线电态势指示器

> **A custom situational awareness gauge for the Tu-154 vMFD project.**
> **图-154 vMFD 项目的自定义态势感知仪表。**

## "No Pain, No Gain. No Brain, No Pain."
为了对付一些hand hands lord lords的情况研发出了此仪表

This is a fictional instrument. The RSI transforms the complex mental math of flying a DME Arc into a simple visual task. By mapping the aircraft's position relative to a station-centered scale, pilots can maintain the arc simply by keeping the indicator dot on the circle.

- 这是一个现实中不存在的、专为图-154 vMFD项目打造的自定义态势感知仪表，核心宗旨是：**能靠你眼睛解决的，绝不让脑子受累。**
- RSI 将飞 DME 弧时复杂的脑力计算转化为简单的视觉任务。通过将飞机位置映射到以导航台为中心的刻度上，飞行员只需保持光点在圆周上即可轻松维持DME弧程序飞行。

<img width="640" height="480" alt="RSI Display" src="https://github.com/user-attachments/assets/c1d6cbd5-2786-46a0-bbf9-da36048f71fc" />

# 这又是图啥呢？
众所周知，在图-154上飞 DME 弧，是一项能让勋宗急得呲牙的绝活。你想在 400 公里的时速下疯狂心算切入角？**别做梦了。**
轮不着你算，这飞机的无线电接收机根本就不会判断自己在哪条径向线上。

众所周知，高端的食材往往需要最朴素的烹饪方式：
**与其在那瞎琢磨台子在哪儿，不如直接画张图瞅瞅你自己在哪儿？**

身边没有领航员也不要紧——搞不好飞这飞机大部分时间都是一个人对着那堆仪表大眼瞪小眼。但是 RSI 的原理极其先进：它把你那颗开始过热的大脑直接接管了。你不需要知道什么是切向航向，不需要知道什么是提前量，更不需要管那该死的径向线。

你只需要像**看雷达一样**，盯着表盘上的亮点：

> **“因为只要我把脑子丢得够快，复杂的航图就追不上我。”**

---

## Key Features | 核心功能

### 1. Station-Centered Visualization
**以导航台为中心的上帝视角**
Provides a "god's eye" view centered on the VOR/DME station, complete with selected TO/FROM radials and 10-degree increments.
抛弃那些反人类的指针吧。RSI 提供了一个以 VOR 台为中心的上帝视角。这感觉就像把原本只能靠猜的方位变成了全图透视挂。**飞不好了依然是你的锅，但飞好了绝对是你的命。**

### 2. Intuitive Arc Tracking
**直观的弧线追踪**
*DME Arc? A Walk in the Park.*
The circular scale represents the target DME distance. The aircraft dot moves relative to this scale (inside/outside/on-track) to provide you instant situational awareness.
圆形刻度代表目标 DME 距离。飞机光点相对于刻度移动（内侧/外侧/航迹上），仪表将提供即时的态势感知。

### 3. Dynamic Deviation Monitoring
**动态偏差监控**
The aircraft indicator updates in real-time, changing color to warn pilots if they deviate from the arc's protected maneuver zone.

---

## Visual Guide | 视觉指南

| Component | Color | Description |
| :--- | :--- | :--- |
| **Scale Ring** | White | Represents the target DME Arc distance (Radius). <br> 白色圆环代表目标 DME 弧的距离（半径）。 |
| **Aircraft Dot** | **Green** / **Red** | **Green**: On arc / within tolerance. **Red**: Deviated / outside protected zone. <br> **绿色**：在弧上/公差内。 **红色**：偏离/超出保护区。 |
| **TO Radial** | <span style="color:magenta">**Magenta**</span> | The selected CRS radial (Head). <br> 选定的 CRS 径向线（向台/切入方向）。 |
| **FROM Radial** | <span style="color:cyan">**Cyan**</span> | The reciprocal radial (Tail). <br> 反向径向线（背台/切出方向）。 |

---
- **RSI is NOT an autopilot. It is a targeting scope.** It requires you to **manually turn the HDG/ZK knob**.(Turn 10 twist 10) It turns the complex navigation task into a simple video game.
- RSI 不负责替你飞，它负责指挥你飞。 它把复杂的程序飞行简化成了钻圈圈，你只需要像个莫得感情的转钮机器 （飞10转10).

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
