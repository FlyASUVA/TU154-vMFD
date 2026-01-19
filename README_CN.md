[English Version](README.md) | [中文版说明](README_CN.md)
# TU154-vMFD（中文版说明）

为 Felis Tu154B2 (CE) 开发的虚拟多功能显示器（MFD）及触控显示控制单元（TCDU）
- Felis Tu154 CE 项目链接：
**Tu-154 Felis CE 项目：** [Unicode4all/Tu-154B2-CE](https://github.com/Unicode4all/Tu-154B2-CE)


# 这都是图啥呢？ (Why?)

**“万丈高楼平地起，大起大落靠自己。”**

<img src="https://github.com/user-attachments/assets/83304ca4-a408-4065-b00b-7709774ecfd3" width="320" height="640" alt="这都是图啥呢">

- 本项目是一场关于“强扭的瓜到底甜不甜”的严肃实验： 我们试图探究，对于图-154这种浑身上下散发着冷战气息的老式飞机，能不能在不动他原有机载设备的情况下，通过外挂一个完全独立的系统，让它强行理解并执行现代的 RNAV 和 RNP 运行程序？
- 简而言之：我们不生产航电，我们只是现代导航数据的搬运工。

---

## 这个项目是啥？

- **这是一个实验性的飞行信息显示系统，运行在一个独立的嵌入式环境里。把它想象成给你的图-154外接了一个比机载EFB更高性能的平板电脑，能拿手里那种**
- 核心功能： 包含 EICAS（发动机指示）、FMS 飞行计划页面、ISIS（备用仪表）等。
- 数据来源： 这种高科技主要靠“拿来主义”——利用 Simbrief API 获取计划，利用 X-Plane 12 的 UDP 端口获取实时数据。
- 适用机型： Felis Tu-154 B2 Community Edition (X-Plane 12)。链接我放顶上了。
- 设计理念： 在尊重 Tu-154 那种“以此为准”的操作逻辑基础上，融入了一些似乎是现代玻璃座舱的便利。
- 硬件载体： 树莓派4（Linux）配合一个 3.5 英寸的电阻屏就能跑起来（嵌入式内存占用小于300MB，说不定Pi3也成）
- 技术栈： Python + pygame。嵌入式模式下运行在 Xorg + openbox 环境下，项目主打一个轻量化。

它不是为了替代飞机的原始系统，而是为了在你手忙脚乱时提供一些现代科技的便利。

## 项目不是什么
- ❌ 不是真实航电：严禁用于真实航班运行
- ❌ 不是认证过的导航方案：飞不好是你的锅，飞好了是你的命。
- ❌ 不是图-154系统模拟器：它不负责模拟飞机的液压或电气，它只负责显示。如果起落架放不下来，请直接去骂图波列夫，别骂我的python代码或者Felis团队
- ❌ 不是傻瓜式 FMC/MCDU，想多了，这种末代苏机不能被它变成A320。

## 当前状态

- ✅ 能用它活着飞出来：已在 Felis 154CE 上测试通过 VNKT（加德满都）RNP-AR 02 跑道离场。能在喜马拉雅山脉中活下来，说明这玩意儿多少有点东西。
- ✅ 也能用它活着落下来：已成功执行 VQPR（帕罗）RNP-AR 15 跑道进近。当然，如果不成功，我们一般称之为“硬着陆测试”。
- ✅ VNAV PATH：支持连续爬升（CCO）和连续下降（CDO），让您在苏联飞机上重新体验到“燃油的可贵”。毕竟在那个年代，油比命便宜，但现在不是了。
- ⚠️ 为了还原历史风貌，我们（可能）保留了一些随机特性。VNAV 有点小脾气：并不是 100% 稳定工作，我们正在努力调教它。
- ⚠️ ISIS 垂直偏差：VDEV 功能目前属于“仅供参考”的阶段。如果您看到窗外地上的房子越来越大，且伴随着急促的警报声，别看屏幕了，赶紧拉杆吧。。
- ⚠️ 再次强调：这是未经认证的实验性设备，**这个软件不会教你如何飞 154，因此飞坠了概不负责。**

本项目**本质上是实验性、教育性和探索性的**。

## 为什么要折腾 Tu-154？

Tu-154 是一架气动设计极其优秀的飞机，但在 2024 年，它常被贴上“过时”、“反人类”、“不适合现代空域”的标签。 本项目不是为了让 154 假装它是现代飞机，但我们不禁要发出灵魂拷问：

- **为啥隔壁波音就能一架 737 换个发动机、换几个屏就强行续命 60 年，我们就不能给图-154 多续一秒？**

我们想探索：

- 如果我们要让这老古董飞 RNP，外部逻辑的底线在哪里？

- 一架飞机的物理局限性和程序设计的起点界限在哪里？

- 一个优秀的“外挂”，能在多大程度上弥补它没有先进航电的遗憾？或者说，能在多大程度上掩盖它那狂野的本质？

---

## 包含功能

- 起飞构型监控：在你带着错误的襟翼或配平起飞前，它会疯狂警告你。
- 重心建议：根据当前重心，告诉你重心杆和安定面配平应该放在哪，防止进近拉不起机头
- 发动机监控：

    - 自动识别启动过程。**体验一把人工扮演EEC的乐趣**

    - 条带式 N2 显示（虽然我写的N1），带双起飞推力游标。

    - EGT 自动监控，有超温警告。

    - 燃油流量独立显示，**让你清晰地看见钱在燃烧。**

- 飞行计划显示：集成了 VNAV PATH、直飞（DCT）、速度干预和高度干预。甚至还有个虚拟键盘，新版本代码支持物理键盘接入
- 单位切换：在 NAV 页面或干预窗口，支持 米/英尺、马赫/公里 的切换（但是升降率表一直是米每秒，因为飞机上的表就是这么装的，不然你看啥）。
- 自动同步：FPLAN 页面会自动跟进你的飞行进度，不用你一重启又从头开始飞了。
- 阶段感知：它知道你是在起飞、爬升、巡航还是下降，并在起飞时让你保持专注拉杆（不提供 VNAV 目标垂直速度）。
- ISFD（集成备用显示）：显示 IAS、航向、GPS 高度。
- 性能工具：开局能直接从 SimBrief 拉取舱单和重量数据，省得你开浏览器或者拿计算器算。
- 航行通告 (NOTAM)：直接在屏幕上看 SimBrief 的通告，不用切出去看网页。
- 系统控制：树莓派用户长按 ADV 按钮可呼出电源菜单，还能看 WiFi 状态。PC用户出bug建议直接把窗口关了更省事儿。
- 整活向实验性功能: [RSI 无线电态势指示器](Readme.RSI.md)

## 截图展示
(截图仅供参考，实物以代码运行结果为准)
<table border="0">
  <tr>
    <td width="50%">
      <img src="https://github.com/user-attachments/assets/c53d85a9-4e5f-4e0e-ba8d-7e83fca4d8f7" width="100%" />
    </td>
    <td width="50%">
      <img src="https://github.com/user-attachments/assets/349ecc45-f032-434a-8843-d0e91a7c66be" width="100%" />
    </td>
  </tr>
  <tr>
    <td>
      <img src="https://github.com/user-attachments/assets/a815c4dc-f23b-49c7-a28c-b92e36d4c527" width="100%" />
    </td>
    <td>
      <img src="https://github.com/user-attachments/assets/b973cbd9-5323-4bda-b2fc-5e5af666c1db" width="100%" />
    </td>
  </tr>
  <tr>
    <td>
      <img src="https://github.com/user-attachments/assets/cfc99b6e-24fc-45bc-9090-1692cbbdba8b" width="100%" />
    </td>
    <td>
      <img src="https://github.com/user-attachments/assets/27693946-75c5-4508-b0dd-c9e442b58cea" width="100%" />
    </td>
  </tr>
  <tr>
    <td>
      <img src="https://github.com/user-attachments/assets/b9c1685a-f1a0-4333-8e8b-087479d7d5b2" width="100%" />
    </td>
    <td>
      <img src="https://github.com/user-attachments/assets/c69931b8-f2c1-4f5f-a1e0-61768240353e" width="100%" />
    </td>
  </tr>
</table>


## 如何食用？

**致Windows用户**
- "(你们是幸运的，因为这本来是设计给树莓派准备的苦差事)"
- 在 Releases 页面下载 独立的 .exe 文件。
- 把他点开。
- 确保你的 X-Plane 12 已启动，并没有防火墙拦截 UDP 端口 49071。
- 关键步骤：在 X-Plane 12 的设置里，勾选 UDP 端口 49071 输出，并选中所需的数据 ID（程序弹窗会告诉你具体选哪些，设好后再关弹窗！）。

**致树莓派用户**
- (这才是本项目的完全体：Project PiCDU)
- 欢迎各位硬核极客将此项目构建为物理外设！本项目针对 树莓派 4/5 + 树莓派 OS + Waveshare DSI/SPI 屏幕 进行了深度优化。

- UDP 设置：请将 UDP 端口设置为 49000（注意与 Windows 版的区别），并将数据发送到树莓派的 IP 地址。

- X-Plane 数据输出设置： 请务必在 X-Plane 的 Data Output 页面勾选通过 UDP 发送以下数据 ID：

    基础数据: 3 (速度), 4 (马赫/G力), 17 (俯仰/横滚), 20 (经纬度/高度)

    环境: 152 (天气)

    重量: 63 (载荷)

    控制: 13 (襟翼/配平), 14 (起落架), 33 (启动器), 74 (升降舵)

    引擎: 27 (反推), 41 (N1), 45 (燃油流量), 47 (EGT), 49 (滑油)

    导航: 97 (频率), 98 (OBS), 99/100 (导航偏离)
    **如果有windows用户读到这边，那么恭喜你，弹窗内容跟这个是一样的**

#### 1. 系统依赖

我们使用 `Openbox` 实现极致的轻量化。（建议先安装没有GUI桌面环境的Raspbian Lite）

```bash
# 更新系统
sudo apt-get update && sudo apt-get upgrade -y

# 安装 Xorg、窗口管理器和Python依赖
sudo apt-get install -y xorg xinit openbox python3-pip git libsdl2-dev

```

#### 2. Python环境设置

克隆仓库并安装所需的Python库（主要是Pygame）。

```bash
git clone https://github.com/FlyASUVA/TU154-vMFD.git
cd Tu154-vMFD
rm main.py
rm config.py
cp main.raspi.py main.py
cp config.raspi.py config.py
pip3 install -r requirements.txt --break-system-packages

```

#### 3. 配置文件

编辑 `config.py` 不要做伸手党，改改 IP：
- UDP_IP: 0.0.0.0 (监听所有来源) 或指定树莓派 IP。

- UDP_PORT: 默认 49000。

- Simbrief Username: 必填！ 不填这个 FMS 就是个摆设。

#### 4. Kiosk模式（自动启动）

- 让树莓派开机直接进入 MFD，不给桌面环境任何机会。

    设置自动登录控制台： sudo raspi-config -> System Options -> Boot / Auto Login -> Console Autologin.

    配置启动脚本： nano ~/.bash_profile 在末尾添加（仅在物理屏幕上启动 X）：
  
```bash
if [ -z "$DISPLAY" ] && [ "$XDG_VTNR" -eq 1 ]; then
  echo "正在启动 PiCDU 航电系统... (3秒后起飞)"
  sleep 3
  startx -- -nocursor
fi
```

- 配置 Openbox： 告诉 Openbox 启动后运行我们的 Python 脚本。

```bash
mkdir -p ~/.config/openbox
nano ~/.config/openbox/autostart
```
添加内容：
```bash
# 关掉屏幕保护，我们要的是长亮
xset s off
xset -dpms
cd /home/pi/Tu154-vMFD  # <--- 注意：改成你的实际路径！
python3 main.py
```
重启：sudo reboot。见证奇迹的时刻。

## 致谢

本项目开源发布。没有开源社区，它早就胎死腹中了。 特别感谢 Felis Discord 频道的各位大佬，是你们让这架老飞机的电子灵魂得以延续。

Fly Safe, or at least, Fly Informed.
