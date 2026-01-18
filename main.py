import pygame
import time
import os
import sys
import tkinter as tk
from tkinter import messagebox
from data_link import DataLink
from eicas import EICAS
from isfd_display import ISFDDisplay
from nav_display import NavDisplay
from fms_core import FMSCore
from adv_display import AdvDisplay    
from config import *

# --- Windows Release Configuration ---
# Force resolution for testing/release if config.py differs
BUTTON_Y = SCREEN_H - 40
BUTTON_HEIGHT = 40

def show_udp_instructions():

    msg = (
        f"Please Enable The Following UDP ID Output for X-Plane 12,\n"
        f"using port {UDP_PORT}, to your computer's LAN IP address:\n\n"
        "--------------------------------------------------\n"
        "● BASIC: 3, 4, 17, 20\n"
        "● WX/ENV: 152\n"
        "● WEIGHT: 63\n"
        "● CTRLS: 13, 14, 33, 74\n"
        "● ENG: 27, 41, 45, 47, 49\n"
        "● NAV: 97, 98, 99, 100\n"
        "--------------------------------------------------\n\n"
        "Full Details:\n"
        "3 (Speed), 4 (Mach/G), 17 (Pitch/Roll), 20 (Lat/Lon/Alt)\n"
        "152 (Point Wx), 63 (Payload)\n"
        "13 (Flaps/Trim), 14 (Gear), 33 (Starter), 74 (Elevator)\n"
        "27 (Beta/Rev), 41 (N1), 45 (FF), 47 (EGT), 49 (Oil)\n"
        "97 (Nav Freq), 98 (OBS), 99/100 (Nav Deflection)\n"
    )
    
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("X-Plane Data Output Setup", msg)
    root.destroy()

def main():
    pygame.init()
    # Windows Mode: 480x320, No Fullscreen
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Tu-154 MFD Terminal (Windows)")
    clock = pygame.time.Clock()

    # Start Data Link
    link = DataLink()
    link.start()

    # Initialize FMS
    print("Initializing FMS Core...")
    shared_fms = FMSCore()
    shared_fms.fetch_simbrief() 

    print("Showing UDP Instructions...")
    show_udp_instructions()

    # Instantiate Pages
    page_eicas = EICAS(shared_fms)
    page_isfd = ISFDDisplay(shared_fms)
    page_nav = NavDisplay(shared_fms)
    page_adv = AdvDisplay(shared_fms, link)
    
    current_page = "ISIS" 
    
    print("--- Tu-154 MFD System Started (Windows Mode) ---")

    try:
        while True:
            current_time = time.time()

            # --- A. Event Handling ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    raise KeyboardInterrupt
                
                # 1. Mouse Down (Click)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    
                    # Page Internal Interaction
                    if current_page == "NAV" and y < BUTTON_Y:
                        page_nav.handle_click((x, y))
                    elif current_page == "ADV" and y < BUTTON_Y:
                        page_adv.handle_click((x, y))

                    # Bottom Navigation Bar Interaction
                    if y >= BUTTON_Y:
                        if len(BTN_NAMES) > 0:
                            btn_w = SCREEN_W // len(BTN_NAMES)
                            btn_idx = x // btn_w
                            
                            if btn_idx < len(BTN_NAMES):
                                btn_name = BTN_NAMES[btn_idx]
                                
                                if btn_name != current_page:
                                    current_page = btn_name
                                    print(f"Switch to page: {current_page}")

                # 2. [WINDOWS] Mouse Up (Release) - Important for NAV Long Press logic
                elif event.type == pygame.MOUSEBUTTONUP:
                    if current_page == "NAV":
                        page_nav.handle_mouseup()

                # 3. [WINDOWS] Keyboard Input - For entering numbers in NAV page
                elif event.type == pygame.KEYDOWN:
                    if current_page == "NAV":
                        page_nav.handle_keydown(event)

            # --- B. Data Update ---
            data = link.data
            data['active_page'] = current_page
            
            lat = data.get('lat', 0)
            if abs(lat) > 0.1:
                # 1. Critical Data
                total_fuel = data.get('total_fuel_kg', 0)
                total_ff = data.get('total_ff_kg_hr', 0) 
                
                # 2. Baro Setting
                baro_in_hg = data.get('baro', 29.92) 

                # 3. Update FMS
                shared_fms.update(
                    lat, 
                    data.get('lon', 0), 
                    data.get('alt_msl_ft', 0), 
                    data.get('gs_kt', 0), 
                    total_fuel,      
                    total_ff,        
                    baro_in_hg,      
                    current_time     
                )

            # --- C. Rendering Logic ---
            if current_page == "ENG":
                page_eicas.update(data)
            elif current_page == "NAV":
                page_nav.update(data, screen)
            elif current_page == "ISIS":
                page_isfd.update(data)
            elif current_page == "ADV":
                page_adv.update(data, screen)

            draw_navbar(screen, current_page)

            # --- D. Refresh ---
            pygame.display.flip()
            clock.tick(FPS)

    except KeyboardInterrupt:
        print("\nShutting down system...")
    finally:
        link.stop()
        pygame.quit()

def draw_navbar(screen, active_page):
    font_btn = pygame.font.SysFont("arial", 16, bold=True)
    count = len(BTN_NAMES)
    if count == 0: return
    btn_w = SCREEN_W // count
    
    for i, name in enumerate(BTN_NAMES):
        rect = pygame.Rect(i * btn_w, BUTTON_Y, btn_w, BUTTON_HEIGHT)
        color = C_BTN_ACTIVE if name == active_page else C_GRAY_DARK
        
        pygame.draw.rect(screen, color, rect)
        pygame.draw.rect(screen, C_GRAY_LIGHT, rect, 1)
        
        txt = font_btn.render(name, True, C_WHITE)
        txt_rect = txt.get_rect(center=rect.center)
        screen.blit(txt, txt_rect)

if __name__ == "__main__":
    main()