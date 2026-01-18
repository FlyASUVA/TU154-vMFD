# TU154-vMFD
A virtual MFD Style TCDU for Felis Tu154B2 (CE)

# 这都是图啥呢  
*What are all these "Tu"s anyway?* - A meme from Chinese Internet.
![53599021dd0c215da061314add9589c9](https://github.com/user-attachments/assets/83304ca4-a408-4065-b00b-7709774ecfd3)


**This project explores whether a legacy aircraft like the Tu-154 can be operated using modern RNAV and RNP Procedures — not by modifying the aircraft itself, but by building an external, experimental guidance system from scratch.**

Originally inspired by a Chinese internet meme that jokingly groups Tu-22, Tu-160, Tu-128 and Tu-16s together as “a pile of Tupolevs”, this project takes the joke seriously and turns it into an engineering question:

> *If life gives you lemon, make lemonade.*
> *But if life gives you a Tupolev, can you still make lemonade?*

---

## What this project is:

- An **experimental flight guidance display**, consisting **EICAS, FMS FPLAN PAGE, ISIS, and More**
- Utilizing existing Simbrief API and X-Plane 12's UDP Output.
- Works with Felis Tu-154 B2 Community Edition (for Xplane 12)
- Designed specifically around the **Tu-154 operational philosophy** with a modern glass cockpit hint
- Implemented as a **stand-alone embedded system**
- Running on **Raspberry Pi 4 (Linux)**
- Displayed on a **3.5" 480×320 resistive touchscreen**
- Written in **Python with pygame**, using Xorg + openbox

The system focuses on **procedural guidance**, **state-driven navigation logic**, and **pilot-assisting cues** rather than full FMC replacement.

## What else do we also offer here:
- A standalone windows exe file that you can run the same program on your own PC (If you are unwilling to use it on a raspberry pi)
---

## Why Tu-154?

The Tu-154 is an tri-jet with exceptional aerodynamics and performance, but nowadays are often seen as obsolete, overcomplicated, or unsuitable for modern flight operations and procedures.  
This project challenges that assumption — not by pretending the aircraft is modern, but by asking:

- What *minimum* external logic is required for it to fly modern procedures?
- Where does aircraft limitation end, and procedural design begin?
- How far can good guidance compensate for the lack of integrated avionics?

---

## Current status

- ✅ VNKT RNP-AR departure (02) tested
- ✅ VQPR RNP-AR approach to RWY 15 successfully flown
- ⚠️ Only **one successful full flight** so far
- ⚠️ This is **not certified avionics**, and never claims to be

This project is **experimental, educational, and exploratory** by design.

---

## What this project is NOT

- ❌ Not a real-world avionics system
- ❌ Not a certified navigation solution
- ❌ Not a Tu-154 systems simulation
- ❌ Not a drop-in FMC replacement

---

## License & openness

This project is open-sourced as a form of **technical reciprocity** — without open-source communities, it would never have existed.
