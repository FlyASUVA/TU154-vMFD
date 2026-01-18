import os
import json
import sys
import tkinter as tk
from tkinter import simpledialog, messagebox

# ==========================================
# ASK USER FOR SIMBRIEF USERNAME
# ==========================================

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(BASE_DIR, "user_config.json")

def load_simbrief_username():
    username = ""

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                username = data.get("simbrief_username", "")
        except Exception as e:
            print(f"Config read error: {e}")

    if not username:
        root = tk.Tk()
        root.withdraw() 
        
        username = simpledialog.askstring(
            "Tu-154 MFD Setup", 
            "Please enter your SimBrief Username:\n(Required for flight plan data)",
            parent=root
        )
        
        if not username:
            messagebox.showwarning("Warning", "No username provided. FMS features may not work.")
            username = "NO_USER"
        else:
            try:
                with open(CONFIG_FILE, 'w') as f:
                    json.dump({"simbrief_username": username}, f)
            except Exception as e:
                messagebox.showerror("Error", f"Could not save config: {e}")
        
        root.destroy()

    return username

# --- UDP CONFIG ---
UDP_IP = "0.0.0.0"
UDP_PORT = 49071
FPS = 30 

# --- DISPLAY LAYOUT ---
SCREEN_W = 480
SCREEN_H = 320

# --- COLOUR PALLET ---
C_BLACK = (0, 0, 0)
C_GRAY_DARK = (40, 40, 40)
C_GRAY_LIGHT = (160, 160, 160)
C_WHITE = (230, 230, 230)
C_GREEN = (0, 200, 0)       
C_AMBER = (255, 180, 0)     
C_RED = (255, 50, 50)       
C_BLUE = (50, 150, 255)     
C_CYAN = (0, 255, 255)      

C_GREEN_NAV = (0, 255, 0)   
C_MAGENTA = (255, 0, 255)   

# --- BUTTON ---
C_BTN_ACTIVE = (0, 80, 0)      
C_BTN_INACTIVE = (30, 30, 30)  

# --- D30-KU ENGINE DATA ---
LIMIT_N1_MAX = 105.0      # % MAX N1
LIMIT_N1_TARGET = 92.0    # % NORMAL TAKEOFF

LIMIT_EGT_CAUTION = 600.0 # C YELLOW EGT
LIMIT_EGT_MAX = 675.0     # C MAX EGT

LIMIT_OIL_MIN = 25.0      # PSI

# --- CG CALCULATION ---
CG_SLOPE = 5.8037
CG_INTERCEPT = 47.62

# --- CG RANGE LIMITS  ---
CG_LIMIT_FWD_TO_CTR = 28.0
CG_LIMIT_CTR_TO_AFT = 35.0

# --- NAV BAR ---
BUTTON_HEIGHT = 40
BUTTON_Y = SCREEN_H - BUTTON_HEIGHT  # 280
BTN_NAMES = ["ENG", "NAV", "ISIS", "ADV"]

# --- SimBrief CONFIG ---
SIMBRIEF_USERNAME = load_simbrief_username()
SIMBRIEF_API_URL = "https://www.simbrief.com/api/xml.fetcher.php"

# --- VNAV & FMS CONSTANTS ---
# Tu-154 DESCEND GRAD
DESCENT_GRADIENT_FT_NM = 318.0  # -3 DEG FPA

# --- UNIT BOOLEAN ---
SHOW_METRIC_ALT = True   
SHOW_METRIC_DIST = True

# --- FPLN FETCH CONFIG ---
USE_LOCAL_DATA = True  
LOCAL_FILE_PATH = "fpl.json"