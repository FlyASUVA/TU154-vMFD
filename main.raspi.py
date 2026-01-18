import pygame
import time
import os
import sys
from data_link import DataLink
from eicas import EICAS
from isfd_display import ISFDDisplay
from nav_display import NavDisplay
from fms_core import FMSCore
from adv_display import AdvDisplay   
from config import *

import subprocess

def get_network_info():
    try:
        res_wlan = subprocess.check_output("nmcli -t -f DEVICE,STATE,CONNECTION device", shell=True).decode()
        if "wlan0:connected" in res_wlan:
            ssid = subprocess.check_output("iwgetid -r", shell=True).decode().strip()
            ip = subprocess.check_output("hostname -I", shell=True).decode().split()[0]
            rssi_raw = subprocess.check_output("grep wlan0 /proc/net/wireless", shell=True).decode().split()
            rssi = rssi_raw[3].replace('.', '') if len(rssi_raw) > 3 else "N/A"
            return f"WLAN: {ssid} | IP: {ip} | SIG: {rssi}dBm"
            
        res_eth = subprocess.check_output("ip addr show eth0", shell=True).decode()
        if "state UP" in res_eth:
            ip_list = subprocess.check_output("hostname -I", shell=True).decode().split()
            ip = ip_list[0] if ip_list else "NO IP"
            return f"ETH0: CONNECTED | IP: {ip}"
            
        return "NETWORK: DISCONNECTED"
    except:
        return "NETWORK: ERROR / NO ADAPTER"

BTN_SYS_W = 200
BTN_SYS_H = 45
CENTER_X = SCREEN_W // 2

MENU_START_Y = 76
MENU_GAP = 60

rect_restart_app = pygame.Rect(CENTER_X - BTN_SYS_W//2, MENU_START_Y, BTN_SYS_W, BTN_SYS_H)
rect_reboot_sys  = pygame.Rect(CENTER_X - BTN_SYS_W//2, MENU_START_Y + MENU_GAP, BTN_SYS_W, BTN_SYS_H)
rect_shutdown    = pygame.Rect(CENTER_X - BTN_SYS_W//2, MENU_START_Y + MENU_GAP*2, BTN_SYS_W, BTN_SYS_H)

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.FULLSCREEN)

    pygame.display.set_caption("Tu-154 MFD Terminal (Pi Edition)")
    clock = pygame.time.Clock()

    last_net_check = 0
    net_status_text = "Checking..."

    link = DataLink()
    link.start()
    print("Initializing FMS Core...")
    shared_fms = FMSCore()
    shared_fms.fetch_simbrief() 

    page_eicas = EICAS(shared_fms)
    page_isfd = ISFDDisplay(shared_fms)
    page_nav = NavDisplay(shared_fms)
    page_adv = AdvDisplay(shared_fms, link)
    
    current_page = "ISIS" 
    font_sys = pygame.font.SysFont("arial", 20, bold=True)
    font_warn = pygame.font.SysFont("arial", 28, bold=True)

    is_adv_pressed = False
    adv_press_start_time = 0.0
    LONG_PRESS_DURATION = 3.0 
    
    show_power_menu = False

    print("--- Tu-154 MFD System Started (Embedded Mode) ---")

    try:
        while True:
            current_time = time.time()

            if current_time - last_net_check > 10.0:
                net_status_text = get_network_info()
                last_net_check = current_time

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    raise KeyboardInterrupt
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    
                    if show_power_menu:
                        if rect_restart_app.collidepoint(x, y):
                            print("SYSTEM: Restarting App...")
                            link.stop()
                            pygame.quit()
                            os.execv(sys.executable, ['python3'] + sys.argv)
                        
                        elif rect_reboot_sys.collidepoint(x, y):
                            print("SYSTEM: Rebooting...")
                            link.stop()
                            pygame.quit()
                            os.system("sudo reboot")
                        
                        elif rect_shutdown.collidepoint(x, y):
                            print("SYSTEM: Shutting Down...")
                            link.stop()
                            pygame.quit()
                            os.system("sudo poweroff")
                        
                        else:
                            show_power_menu = False
                    
                    else:
                        if current_page == "NAV" and y < BUTTON_Y:
                            page_nav.handle_click((x, y))
                        elif current_page == "ADV" and y < BUTTON_Y:
                            page_adv.handle_click((x, y))
                            
                        if y >= BUTTON_Y:
                            if len(BTN_NAMES) > 0:
                                btn_w = SCREEN_W // len(BTN_NAMES)
                                btn_idx = x // btn_w
                                
                                if btn_idx < len(BTN_NAMES):
                                    btn_name = BTN_NAMES[btn_idx]
                                    
                                    if btn_name == "ADV":
                                        is_adv_pressed = True
                                        adv_press_start_time = current_time
                                    
                                    if btn_name != current_page:
                                        current_page = btn_name
                                        print(f"Switch to page: {current_page}")

                elif event.type == pygame.MOUSEBUTTONUP:
                    is_adv_pressed = False
                    
                    if current_page == "NAV" and not show_power_menu:
                        page_nav.handle_mouseup()

                elif event.type == pygame.KEYDOWN:
                    if current_page == "NAV" and not show_power_menu:
                        page_nav.handle_keydown(event)
                        
            if is_adv_pressed and not show_power_menu:
                duration = current_time - adv_press_start_time
                if duration > LONG_PRESS_DURATION:
                    print("Long Press Detected! Opening Power Menu...")
                    show_power_menu = True
                    is_adv_pressed = False 

            data = link.data
            data['active_page'] = current_page
            
            lat = data.get('lat', 0)
            if abs(lat) > 0.1:
                total_fuel = data.get('total_fuel_kg', 0)
                total_ff = data.get('total_ff_kg_hr', 0) 
                baro_in_hg = data.get('baro', 29.92) 

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

            if show_power_menu:
                screen.fill((20, 20, 20)) 
                pygame.draw.rect(screen, C_RED, (0, 0, SCREEN_W, SCREEN_H), 4)

                font_net = pygame.font.SysFont("monospace", 14, bold=False)
                net_color = (0, 255, 255) if "CONNECTED" in net_status_text or "WLAN" in net_status_text else C_AMBER
                
                net_surf = font_net.render(net_status_text, True, net_color)
                screen.blit(net_surf, (15, 15)) 

                title = font_warn.render("PiCDU POWER MENU", True, C_RED)
                screen.blit(title, (CENTER_X - title.get_width()//2, 32)) 

                def draw_sys_btn(rect, text, bg_col):
                    pygame.draw.rect(screen, bg_col, rect)
                    pygame.draw.rect(screen, C_WHITE, rect, 2)
                    txt_surf = font_sys.render(text, True, C_WHITE)
                    txt_rect = txt_surf.get_rect(center=rect.center)
                    screen.blit(txt_surf, txt_rect)

                draw_sys_btn(rect_restart_app, "RESTART MFD", C_AMBER)
                draw_sys_btn(rect_reboot_sys,  "REBOOT PiCDU",   (0, 100, 200)) 
                draw_sys_btn(rect_shutdown,    "SHUTDOWN PiCDU", C_RED)

                tip = font_sys.render("TAP OUTSIDE TO CANCEL", True, C_GRAY_LIGHT)
                screen.blit(tip, (CENTER_X - tip.get_width()//2, SCREEN_H - 40)) 
                
            else:
                if current_page == "ENG":
                    page_eicas.update(data)
                elif current_page == "NAV":
                    page_nav.update(data, screen)
                elif current_page == "ISIS":
                    page_isfd.update(data)
                elif current_page == "ADV":
                    page_adv.update(data, screen)

                draw_navbar(screen, current_page, is_adv_pressed, current_time - adv_press_start_time, LONG_PRESS_DURATION)

            pygame.display.flip()
            clock.tick(FPS)

    except KeyboardInterrupt:
        print("\nShutting down system...")
    finally:
        link.stop()
        pygame.quit()

def draw_navbar(screen, active_page, is_pressing_adv, press_duration, max_duration):
    font_btn = pygame.font.SysFont("arial", 16, bold=True)
    count = len(BTN_NAMES)
    if count == 0: return
    btn_w = SCREEN_W // count
    
    for i, name in enumerate(BTN_NAMES):
        rect = pygame.Rect(i * btn_w, BUTTON_Y, btn_w, BUTTON_HEIGHT)
        color = C_BTN_ACTIVE if name == active_page else C_GRAY_DARK
        
        pygame.draw.rect(screen, color, rect)
        
        if name == "ADV" and is_pressing_adv:
            progress = min(1.0, press_duration / max_duration)
            prog_rect = pygame.Rect(rect.x, rect.y, int(rect.width * progress), rect.height)
            pygame.draw.rect(screen, (200, 50, 50), prog_rect)
            
        pygame.draw.rect(screen, C_GRAY_LIGHT, rect, 1)
        
        txt = font_btn.render(name, True, C_WHITE)
        txt_rect = txt.get_rect(center=rect.center)
        screen.blit(txt, txt_rect)

if __name__ == "__main__":
    main()
