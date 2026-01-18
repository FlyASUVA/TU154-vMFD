# TU154-vMFD (English Version Readme)
A virtual MFD and TCDU (Touchscreen Control Display Unit) for Felis Tu154B2 (CE)

# 这都是图啥呢  
*What are all these "Tu"s anyway?* - A meme from Chinese Internet.

*![53599021dd0c215da061314add9589c9](https://github.com/user-attachments/assets/83304ca4-a408-4065-b00b-7709774ecfd3)*


**This project explores whether a legacy aircraft like the Tu-154 can be operated using modern RNAV and RNP Procedures — not by modifying the aircraft itself, but by building an external, experimental guidance system from scratch.**

Originally inspired by a Chinese internet meme that jokingly groups Tu-22, Tu-160, Tu-128 and Tu-16s together as “a pile of Tupolevs”, this project takes the joke seriously and turns it into an engineering question:

> *If life gives you lemon, make lemonade.*
> *But if life gives you a Tupolev, can you still make lemonade?*

---

## What this project is:

- An **experimental flight information display**, consisting **EICAS, FMS FPLAN LEGS PAGE, ISIS, and More**
- Utilizing existing Simbrief API and X-Plane 12's UDP Output.
- Works with Felis Tu-154 B2 Community Edition (for Xplane 12)
- Designed specifically around the **Tu-154 operational philosophy** with a modern glass cockpit hint
- Implemented as a **stand-alone embedded system**
- Running on **Raspberry Pi 4 (Linux)**
- Displayed on a **3.5" 480×320 resistive touchscreen**
- Written in **Python with pygame**, using Xorg + openbox

The system focuses on **procedural guidance**, **state-driven navigation logic**, and **pilot-assisting cues** rather than full FMC replacement.

## What this project is NOT

- ❌ Not a real-world avionics system
- ❌ Not a certified navigation solution
- ❌ Not a Tu-154 systems simulation
- ❌ Not a drop-in FMC replacement

## Current status

- ✅ VNKT RNP-AR departure (02) tested using Felis 154CE
- ✅ VQPR RNP-AR approach to RWY 15 successfully flown using Felis 154CE
- ✅ Continuous Climb Operation (CCO) and Continuous Descend Operation (CDO) can be achieved by its VNAV PATH function.
- ⚠️ VNAV PATH is not 100% work all the time, we are still test and fixing it
- ⚠️ Do SPEED and ALT INTV for your next WPTs, before it become your active target WPT.
- ⚠️ VDEV function is marginally working on the ISIS display. We are still working on it to make sure it's not buggy.
- ⚠️ This is **not certified avionics**, and never claims to be

This project is **experimental, educational, and exploratory** by design.

## Why Tu-154?

The Tu-154 is an tri-jet with exceptional aerodynamics and performance, but nowadays are often seen as obsolete, overcomplicated, or unsuitable for modern flight operations and procedures.  
This project challenges that assumption — not by pretending the aircraft is modern, but by asking:

- What *minimum* external logic is required for it to fly modern procedures?
- Where does aircraft limitation end, and procedural design begin?
- How far can good guidance compensate for the lack of integrated avionics?

---

## Function Included

- Takeoff Config Monitor: Automatic configuration warning at takeoff.
- Approach CG lever Advisory: Automatic CG lever position advisory and STAB trim advisory based on current CG.
- Engine Monitoring: Automatic Start Recognition. Tape-style N2 display (simulating thrust) with dual takeoff thrust bugs. Automatic EGT display with overheat warning. Individual Fuel Flow indicators for each engine.
- FPLAN Display System: Integrated Flight Plan display with VNAV PATH, DCT TO, SPEED INTV, and ALT INTV, operated via a virtual keypad.
- Meter/ Feet and Mach/KM unit toggle on NAV page (press the ALT REQ), and on SPEED INTV / ALT INTV window (press the input box).
- Auto-Sync: FPLAN Page automatically synchronizes to the nearest active waypoint.
- Phase Detection: Automatic Flight Phase sensing (TO/CLB/CRZ/DES). VNAV Target VS function is inhibited during Takeoff.
- ISFD (Integrated Standby Flight Display): Displays IAS, Heading, GPS Altitude with trend vectors. Experimental VDEV (Vertical Deviation) indicator.
- Performance Tools: Pre-Flight Page showing SimBrief aircraft loading weights.
- Flight Progress: Real-time endurance calculation and VDEV monitoring.
- Airport Info: Displays Takeoff and Landing airport data, including departure ATIS and arrival METAR (via SimBrief).
- Notam Integration: Displays SimBrief NOTAMs directly on the unit.
- System Control (Raspberry Pi): Power Menu accessible by long-pressing the ADV button, featuring real-time WiFi status.
  
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

-（Screenshot showcased are from the development phase, some functions are updated with minor variation)
## How to Use?

For Windows users 

- (you guys are lucky by the way, as it's originally designed as an embedded software)
- download the **standalone exe** file on the release folder, and run it with your Xplane's UDP port 49071 open, and send data to your PC's LAN address.
- Don't forget to enable the specified ID's required for the UDP data in XPlane 12! (read the pop up window)

For Raspberry Pi User:

- You are welcome to build this as your own physical Flight Deck Unit! The Raspberry Pi release is called *Project PiCDU*.
- This version of project is optimized for **Raspberry Pi 4/5** running **Raspberry Pi OS (Bookworm/Trixie)** with a **Waveshare DSI/SPI Touchscreen**. You're welcomed to experimenting with all kind of hardware (if it runs, it runs).
- Please do what the windows users do in the X-Plane first, open UDP port 49000 instead of 49071 and send data to your Raspberry Pi's LAN Address.
- The IDs required for Xplane UDP Output are

        "BASIC: 3, 4, 17, 20"
        "● WX/ENV: 152"
        "● WEIGHT: 63"
        "● CTRLS: 13, 14, 33, 74"
        "● ENG: 27, 41, 45, 47, 49"
        "● NAV: 97, 98, 99, 100"
  
        "Full Details:"
        "3 (Speed), 4 (Mach/G), 17 (Pitch/Roll), 20 (Lat/Lon/Alt)"
        "152 (Point Wx), 63 (Payload)"
        "13 (Flaps/Trim), 14 (Gear), 33 (Starter), 74 (Elevator)"
        "27 (Beta/Rev), 41 (N1), 45 (FF), 47 (EGT), 49 (Oil)"
        "97 (Nav Freq), 98 (OBS), 99/100 (Nav Deflection)"

#### 1. System Dependencies

We use `Openbox` for a lightweight kiosk mode without the heavy desktop environment.

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Xorg, Window Manager, and Python dependencies
sudo apt-get install -y xorg xinit openbox python3-pip git libsdl2-dev

```

#### 2. Python Setup

Clone the repository and install the required Python libraries (mainly Pygame).

```bash
git clone https://github.com/FlyASUVA/TU154-vMFD.git
cd Tu154-vMFD
rm main.py
rm config.py
cp main.raspi.py main.py
cp config.raspi.py config.py
pip3 install -r requirements.txt --break-system-packages

```

#### 3. Configuration

Edit `config.py` to match your network environment:

* **UDP_IP:** Set to `0.0.0.0` (to listen on all interfaces) or your Pi's specific LAN IP.
* **UDP_PORT:** Default is `49000`. Make sure X-Plane sends data to this port.
* **Simbrief Username:** Default is empty . make sure you add your own username or the FMS will not work.

#### 4. Kiosk Mode (Auto-Start)

To make the Pi boot directly into the MFD software (bypassing the desktop):

1. **Configure Console Boot:**
Run `sudo raspi-config` -> `System Options` -> `Boot / Auto Login` -> select **Console Autologin**.
2. **Edit Startup Script:**
Add the following logic to your `~/.bash_profile` (creates a loop-free start on the physical screen only):
```bash
nano ~/.bash_profile
```

Paste this at the bottom:
```bash
# Auto-start X server on TTY1 (Physical Display) only
if [ -z "$DISPLAY" ] && [ "$XDG_VTNR" -eq 1 ]; then
  echo "Starting PiCDU Avionics..."
  # Give 3 seconds to abort with Ctrl+C for debugging
  sleep 3
  startx -- -nocursor
fi
```

3. **Configure Openbox:**
Tell Openbox what to launch when X starts.
```bash
mkdir -p ~/.config/openbox
nano ~/.config/openbox/autostart
```

Add this line:
```bash
# Disable screen saver and start app
xset s off
xset -dpms
cd /<your project name>  # <-- Change path to your project folder before pasting!
python3 main.py

```

4. **Reboot:** `sudo reboot`. The system should now boot straight into the Tu-154 MFD.

---


## By Sim Pilots, For Sim Pilots

This project is open-sourced as a form of **technical reciprocity** — without open-source communities, it would never have existed.
Special Thanks for the supporting members in the Felis Discord Server!
