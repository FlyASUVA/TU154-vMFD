import pygame
import math
import time
from config import *
from rsi import RSIPage
from hold import HoldPage

# --- Tab IDs (Order: PERF, APPR, NAV, NOTAM, PROG) ---
TAB_PERF    = 0
TAB_AIRPORT = 1
TAB_NAVRAD  = 2
TAB_NOTAM   = 3
TAB_PROG    = 4
TAB_RSI     = 5 
TAB_HOLD    = 6

class AdvDisplay:
    def __init__(self, shared_fms, data_link):
        self.fms = shared_fms
        self.data_link = data_link
        
        # --- Fonts ---
        self.font_xs = pygame.font.SysFont("arial", 13) 
        self.font_s = pygame.font.SysFont("arial", 16)
        self.font_m = pygame.font.SysFont("arial", 20, bold=True)
        self.font_l = pygame.font.SysFont("arial", 24, bold=True)
        self.font_mono = pygame.font.SysFont("consolas", 18, bold=True)
        self.font_mono_l = pygame.font.SysFont("consolas", 22, bold=True)

        # Initialize RSI Page
        self.rsi_page = RSIPage(shared_fms, data_link)

        # Initialize Hold Page
        self.hold_page = HoldPage(shared_fms, data_link)
        
        # [NEW] Rects for NAV1 Click & Hold Button
        self.rect_nav1_click = pygame.Rect(10, 80, 200, 80) 
        self.rect_hold_btn = pygame.Rect(380, 80, 40, 20)
        
        # --- State ---
        self.current_tab = TAB_PROG 
        self.airport_toggle = "AUTO" 

        # --- Layout Constants ---
        NAV_W = SCREEN_W
        tw = NAV_W // 5
        
        # Navigation Bar Rects
        self.rect_tab_perf    = pygame.Rect(0 * tw, 35, tw, 30) 
        self.rect_tab_airport = pygame.Rect(1 * tw, 35, tw, 30) 
        self.rect_tab_navrad  = pygame.Rect(2 * tw, 35, tw, 30) 
        self.rect_tab_notam   = pygame.Rect(3 * tw, 35, tw, 30) 
        self.rect_tab_prog    = pygame.Rect(4 * tw, 35, tw, 30) 
        
        self.BOTTOM_LIMIT = SCREEN_H - 40 

        # Scroll Button Areas
        self.btn_up_rect = pygame.Rect(430, 150, 50, 60)
        self.btn_dn_rect = pygame.Rect(430, 215, 50, 60)

        # NOTAM State
        self.notam_mode = "DEP"
        self.notam_scroll_offset = 0
        self.notam_max_rows = 8 
        self.rect_notam_dep = pygame.Rect(280, 80, 60, 25)
        self.rect_notam_arr = pygame.Rect(350, 80, 60, 25)
        
        # PERF State
        self.perf_scroll_offset = 0
        self.perf_max_rows = 5 
        self.perf_impact_keys = [
            ('zfw_plus_1000',  'ZFW +1.0T'), ('zfw_minus_1000', 'ZFW -1.0T'),
            ('plus_2000ft',    'FL  UP'),    ('minus_2000ft',   'FL  DN'),
            ('plus_4000ft',    'FL  UP+'),   ('minus_4000ft',   'FL  DN-')
        ]
        self.perf_total_rows = 5 + len(self.perf_impact_keys)

    def update(self, link_data, screen):
        screen.fill(C_BLACK)
        
        self._draw_top_bar(screen)
        self._draw_tabs(screen)
        
        if self.current_tab == TAB_PROG: self._draw_page_prog(screen)
        elif self.current_tab == TAB_AIRPORT: self._draw_page_airport(screen)
        elif self.current_tab == TAB_NAVRAD: self._draw_page_navrad(screen)
        elif self.current_tab == TAB_RSI:
            self.rsi_page.update(screen)
        elif self.current_tab == TAB_HOLD: 
            self.hold_page.update(screen)
        elif self.current_tab == TAB_PERF: self._draw_page_perf(screen)
        elif self.current_tab == TAB_NOTAM: self._draw_page_notam(screen)
        elif self.current_tab == TAB_PERF: self._draw_page_perf(screen)
        elif self.current_tab == TAB_NOTAM: self._draw_page_notam(screen)
        
        if self.current_tab in [TAB_PERF, TAB_NOTAM]:
            self._draw_scroll_bar(screen)

    # --- Interaction Logic ---
    def handle_click(self, pos):
        
        if pos[1] < 70:
            if self.rect_tab_prog.collidepoint(pos): 
                self.current_tab = TAB_PROG
                return
            elif self.rect_tab_airport.collidepoint(pos): 
                self.current_tab = TAB_AIRPORT
                return
            elif self.rect_tab_navrad.collidepoint(pos): 
                self.current_tab = TAB_NAVRAD
                return
            elif self.rect_tab_perf.collidepoint(pos): 
                self.current_tab = TAB_PERF
                return
            elif self.rect_tab_notam.collidepoint(pos): 
                self.current_tab = TAB_NOTAM
                return

        # FOR RSI PAGE EXIT
        if self.current_tab == TAB_RSI:
            result = self.rsi_page.handle_click(pos)
            if result == "EXIT":
                self.current_tab = TAB_NAVRAD
            return 

        if self.current_tab == TAB_HOLD:
            self.hold_page.handle_click(pos)
            return
            
        elif self.current_tab == TAB_NAVRAD:
            # Check NAV 1 Click -> Enter RSI
            if self.rect_nav1_click.collidepoint(pos):
                self.current_tab = TAB_RSI
                print("Switched to RSI Mode")
            
            # Check HOLD Button
            elif self.rect_hold_btn.collidepoint(pos):
                self.current_tab = TAB_HOLD

        elif self.current_tab == TAB_AIRPORT:
            if 80 < pos[1] < self.BOTTOM_LIMIT:
                modes = ["AUTO", "DEP", "ARR"]
                self.airport_toggle = modes[(modes.index(self.airport_toggle) + 1) % 3]

        elif self.current_tab == TAB_NOTAM:
            if self.rect_notam_dep.collidepoint(pos): 
                self.notam_mode = "DEP"; self.notam_scroll_offset = 0
            elif self.rect_notam_arr.collidepoint(pos): 
                self.notam_mode = "ARR"; self.notam_scroll_offset = 0
            
            # Scroll Up
            elif self.btn_up_rect.collidepoint(pos): 
                notams = getattr(self.fms, 'origin_notams' if self.notam_mode == "DEP" else 'dest_notams', [])
                if self.notam_scroll_offset + self.notam_max_rows < len(notams):
                    self.notam_scroll_offset += 1
            
            # Scroll Down
            elif self.btn_dn_rect.collidepoint(pos): 
                if self.notam_scroll_offset > 0: 
                    self.notam_scroll_offset -= 1
        
        elif self.current_tab == TAB_PERF:
            self.perf_total_rows = 5 + len(self.perf_impact_keys)
            
            if self.btn_up_rect.collidepoint(pos): 
                if self.perf_scroll_offset < (self.perf_total_rows - self.perf_max_rows):
                    self.perf_scroll_offset += 1
            
            elif self.btn_dn_rect.collidepoint(pos): 
                if self.perf_scroll_offset > 0:
                    self.perf_scroll_offset -= 1

    # --- Drawing Methods ---

    def _draw_top_bar(self, screen):
        status_color, status_txt, txt_color = (20, 20, 20), "SYSTEM NORMAL", C_GREEN_NAV
        if hasattr(self.fms, 'vnav_deviation') and abs(self.fms.vnav_deviation) > 1000:
            status_color, status_txt, txt_color = (50, 40, 0), "CHECK VNAV PATH", C_AMBER
        if hasattr(self.fms, 'baro_alert') and self.fms.baro_alert:
            status_color, status_txt, txt_color = (50, 40, 0), f"ALERT: {self.fms.baro_alert}", C_AMBER

        pygame.draw.rect(screen, status_color, (0, 0, SCREEN_W, 35))
        pygame.draw.line(screen, (80,80,80), (0, 35), (SCREEN_W, 35), 1)
        screen.blit(self.font_m.render(status_txt, True, txt_color), (10, 5))
        
        t_str = time.strftime("%H:%M UTC", time.gmtime())
        s_time = self.font_m.render(t_str, True, C_WHITE)
        screen.blit(s_time, (SCREEN_W - s_time.get_width() - 10, 5))

    def _draw_tabs(self, screen):
        def draw_tab(rect, text, is_active):
            color = (0, 50, 0) if is_active else (30, 30, 30) 
            text_col = C_WHITE if is_active else (150, 150, 150)
            pygame.draw.rect(screen, color, rect, border_radius=5)
            pygame.draw.rect(screen, (60, 60, 60), rect, 1, border_radius=5)
            t = self.font_s.render(text, True, text_col)
            screen.blit(t, t.get_rect(center=rect.center))
            
        # 1. PERF Tab
        draw_tab(self.rect_tab_perf, "PERF", self.current_tab == TAB_PERF)
        
        # 2. TO/APPR Tab (Dynamic)
        label = "TO/APPR"
        if self.airport_toggle == "DEP": label = "TO/WX"
        elif self.airport_toggle == "ARR": label = "APPR/WX"
        draw_tab(self.rect_tab_airport, label, self.current_tab == TAB_AIRPORT)
        
        # 3. NAV RAD / RSI / HOLD Tab TOGGLE
        nav_label = "NAV RAD"
        nav_active = False
        
        if self.current_tab == TAB_NAVRAD:
            nav_active = True
        elif self.current_tab == TAB_RSI:
            nav_label = "RSI"   # SHOW RSI PAGE
            nav_active = True
        elif self.current_tab == TAB_HOLD:
            nav_label = "HOLD"  # SHOW HOLD PAGE
            nav_active = True
            
        draw_tab(self.rect_tab_navrad, nav_label, nav_active)
        
        # 4. NOTAM Tab
        draw_tab(self.rect_tab_notam, "NOTAM", self.current_tab == TAB_NOTAM)

        # 5. PROG Tab
        draw_tab(self.rect_tab_prog, "PROG", self.current_tab == TAB_PROG)

    def _draw_scroll_bar(self, screen):
        can_scroll_more_down = False 
        can_scroll_back_up = False 
        
        if self.current_tab == TAB_NOTAM:
            notams = getattr(self.fms, 'origin_notams' if self.notam_mode == "DEP" else 'dest_notams', [])
            can_scroll_more_down = (self.notam_scroll_offset + self.notam_max_rows) < len(notams)
            can_scroll_back_up = self.notam_scroll_offset > 0
        elif self.current_tab == TAB_PERF:
            can_scroll_more_down = (self.perf_scroll_offset + self.perf_max_rows) < self.perf_total_rows
            can_scroll_back_up = self.perf_scroll_offset > 0

        # Scroll Button Colors
        color_top_btn = C_GRAY_LIGHT if can_scroll_more_down else C_GRAY_DARK 
        color_bot_btn = C_GRAY_LIGHT if can_scroll_back_up else C_GRAY_DARK 

        pygame.draw.rect(screen, (20,20,20), (430, 150, 50, 130))
        pygame.draw.line(screen, C_GRAY_DARK, (430, 150), (430, 280), 1)

        cx_up, cy_up = self.btn_up_rect.centerx, self.btn_up_rect.centery
        pygame.draw.polygon(screen, color_top_btn, [(cx_up, cy_up - 10), (cx_up - 10, cy_up + 10), (cx_up + 10, cy_up + 10)])
        
        cx_dn, cy_dn = self.btn_dn_rect.centerx, self.btn_dn_rect.centery
        pygame.draw.polygon(screen, color_bot_btn, [(cx_dn, cy_dn + 10), (cx_dn - 10, cy_dn - 10), (cx_dn + 10, cy_dn - 10)])

    def _draw_page_perf(self, screen):
        y = 75
        w = getattr(self.fms, 'weights', {})
        crz = getattr(self.fms, 'crz_data', {})
        impacts = getattr(self.fms, 'perf_impacts', {})

        # 1. WEIGHT & BALANCE
        screen.blit(self.font_m.render("WEIGHT & BALANCE", True, C_CYAN), (10, y))
        y += 28
        tow = w.get('tow', 0); block = w.get('block_fuel', 0)
        self._kv_aligned(screen, "EST TOW", f"{tow:,}", 10, y, 90, C_WHITE, size="S")
        self._kv_aligned(screen, "BLOCK FUEL", f"{block:,}", 220, y, 100, C_WHITE, size="S")
        y += 25
        zfw = w.get('zfw', 0); pax = w.get('pax', 0); cargo = w.get('cargo', 0)
        self._kv_aligned(screen, "EST ZFW", f"{zfw:,}", 10, y, 90, C_WHITE, size="S")
        self._kv_aligned(screen, "PAX/CARGO", f"{pax} / {cargo}", 220, y, 100, C_WHITE, size="S")
        
        y += 30; pygame.draw.line(screen, C_GRAY_DARK, (10, y), (SCREEN_W-10, y), 1); y += 5

        # 2. Scroll Area: Build Virtual List
        scroll_items = []
        
        # CRZ Header
        scroll_items.append({'type': 'header', 'text': 'CRZ DATA', 'color': C_AMBER})
        
        # CRZ Values
        init_alt = getattr(self.fms, 'cruise_alt', 0)
        alt_str = f"FL{int(init_alt/100)}" if init_alt > 0 else "---"
        wind_dir = crz.get('avg_wind_dir', '000'); wind_spd = crz.get('avg_wind_spd', '00')
        isa_val = crz.get('avg_isa', '0')
        try: i_val = int(isa_val); prefix = "P" if i_val >= 0 else "M"; isa_str = f"{prefix}{abs(i_val):02d}"
        except: isa_str = isa_val
        scroll_items.append({
            'type': 'crz_values', 
            'vals': [('INIT ALT', alt_str), ('AVG WIND', f"{wind_dir}/{wind_spd}"), ('AVG ISA', isa_str)]
        })
        
        scroll_items.append({'type': 'sep'})
        scroll_items.append({'type': 'header', 'text': 'OPERATIONAL IMPACTS', 'color': C_CYAN})
        scroll_items.append({'type': 'imp_cols'})
        
        for key, label in self.perf_impact_keys:
            data_node = impacts.get(key, {})
            scroll_items.append({'type': 'imp_row', 'label': label, 'data': data_node})

        self.perf_total_rows = len(scroll_items)
        current_idx = self.perf_scroll_offset
        
        while current_idx < len(scroll_items):
            if y > self.BOTTOM_LIMIT - 15: break
            
            item = scroll_items[current_idx]
            
            if item['type'] == 'header':
                screen.blit(self.font_m.render(item['text'], True, item['color']), (10, y))
                y += 25
            
            elif item['type'] == 'crz_values':
                self._kv_aligned(screen, item['vals'][0][0], item['vals'][0][1], 10, y, 70, C_WHITE, size="S")
                self._kv_aligned(screen, item['vals'][1][0], item['vals'][1][1], 150, y, 90, C_WHITE, size="S")
                self._kv_aligned(screen, item['vals'][2][0], item['vals'][2][1], 320, y, 70, C_WHITE, size="S")
                y += 25
                
            elif item['type'] == 'sep':
                pygame.draw.line(screen, C_GRAY_DARK, (10, y+5), (SCREEN_W-10, y+5), 1)
                y += 15
                
            elif item['type'] == 'imp_cols':
                screen.blit(self.font_s.render("FACTOR", True, C_GRAY_LIGHT), (10, y))
                screen.blit(self.font_s.render("TRIP DIFF", True, C_GRAY_LIGHT), (160, y))
                screen.blit(self.font_s.render("TIME DIFF", True, C_GRAY_LIGHT), (300, y))
                y += 22
                
            elif item['type'] == 'imp_row':
                label = item['label']
                data_node = item['data']
                screen.blit(self.font_s.render(label, True, C_WHITE), (10, y))
                
                if not data_node:
                    screen.blit(self.font_s.render("NOT AVAIL", True, C_GRAY_DARK), (160, y))
                else:
                    trip = int(data_node.get('burn_difference', 0))
                    time_sec = int(data_node.get('time_difference', 0))
                    t_sign = "P" if trip >= 0 else "M"
                    tm_sign = "P" if time_sec >= 0 else "M"
                    time_min = int(abs(time_sec) / 60)
                    col = C_GREEN_NAV if trip < 0 else C_WHITE 
                    
                    screen.blit(self.font_s.render(f"{t_sign} {abs(trip):04d}", True, col), (160, y))
                    screen.blit(self.font_s.render(f"{tm_sign} {time_min:03d}", True, C_WHITE), (300, y))
                y += 22 
            
            current_idx += 1

    def _draw_page_airport(self, screen):
        mode = "DEP"
        if self.airport_toggle == "AUTO":
            if self.fms.phase in ["CRZ", "DES"]: mode = "ARR"
        else: mode = self.airport_toggle

        if mode == "DEP":
            info = self.fms.origin_info; icao = self.fms.origin
            title = "DPRT /"; color_theme = (0, 40, 0); txt = info.get('atis', 'NO DATA')
        else:
            info = self.fms.dest_info; icao = self.fms.dest
            title = "DEST /"; color_theme = (0, 0, 40); txt = info.get('metar', 'NO DATA')

        y = 80
        screen.blit(self.font_xs.render("MODE: " + self.airport_toggle, True, C_GRAY_LIGHT), (SCREEN_W - 80, y))
        screen.blit(self.font_l.render(f"{title}  {icao}", True, C_CYAN), (20, y))
        y += 35
        rwy = info.get('rwy', '--')
        self._kv_aligned(screen, "RWY EXP", rwy, 20, y, 100, C_WHITE)
        self._kv_aligned(screen, "ELEVATION", f"{info.get('elev',0)} FT", 240, y, 100, C_WHITE)
        y += 30
        mora = info.get('mora', 0)
        self._kv_aligned(screen, "MORA", f"{mora} FT", 20, y, 60, C_AMBER)
        if mode == "DEP": self._kv_aligned(screen, "TRANS ALT", f"{info.get('trans_alt',18000)}", 240, y, 100, C_GRAY_LIGHT)
        else: self._kv_aligned(screen, "TRANS LVL", f"FL{info.get('trans_level',180)/100:.0f}", 240, y, 100, C_GRAY_LIGHT)
        y += 35
        rect_content = pygame.Rect(5, y, SCREEN_W-10, 110)
        pygame.draw.rect(screen, color_theme, rect_content, border_radius=5)
        pygame.draw.rect(screen, (80,80,80), rect_content, 1, border_radius=5)
        lbl = "ATIS INFO:" if mode == "DEP" else "METAR:"
        screen.blit(self.font_s.render(lbl, True, C_AMBER), (15, y+5))
        screen.blit(self.font_xs.render("(TAP TO SWITCH)", True, (100,100,100)), (SCREEN_W - 120, y+5))
        self._draw_text_wrapped(screen, txt, 15, y+25, SCREEN_W-25, self.font_xs, C_WHITE)

    def _draw_page_notam(self, screen):
        y = 80
        s_head = self.font_m.render("NOTAMs:", True, C_AMBER)
        screen.blit(s_head, (10, y))
        
        def draw_sub_tab(rect, text, is_active):
            color = (0, 80, 0) if is_active else (40, 40, 40)
            pygame.draw.rect(screen, color, rect, border_radius=3)
            pygame.draw.rect(screen, C_GRAY_LIGHT, rect, 1, border_radius=3)
            txt = self.font_xs.render(text, True, C_WHITE)
            screen.blit(txt, txt.get_rect(center=rect.center))
        draw_sub_tab(self.rect_notam_dep, "DEP", self.notam_mode == "DEP")
        draw_sub_tab(self.rect_notam_arr, "ARR", self.notam_mode == "ARR")
        
        y += 35
        if self.notam_mode == "DEP":
            icao = self.fms.origin; notams = getattr(self.fms, 'origin_notams', [])
        else:
            icao = self.fms.dest; notams = getattr(self.fms, 'dest_notams', [])
        screen.blit(self.font_s.render(f"LOCATION: {icao}", True, C_CYAN), (15, y))
        y += 25
        
        if not notams:
            screen.blit(self.font_s.render("NO DATA AVAILABLE", True, C_GRAY_LIGHT), (20, y))
        else:
            visible_range = notams[self.notam_scroll_offset : self.notam_scroll_offset + self.notam_max_rows]
            for n in visible_range:
                if y > self.BOTTOM_LIMIT - 15: break
                txt = n.replace("DEP: ", "").replace("ARR: ", "")[:65]
                screen.blit(self.font_xs.render(f"• {txt}...", True, C_WHITE), (10, y))
                y += 20 

    def _kv_aligned(self, screen, k, v, x, y, label_w, color, size="M"):
        s_k = self.font_s.render(k, True, C_GRAY_LIGHT)
        screen.blit(s_k, (x, y))
        font = self.font_mono_l if size=="L" else self.font_mono
        if size == "S": font = self.font_s
        s_v = font.render(v, True, color)
        screen.blit(s_v, (x + label_w, y))

    def _draw_text_wrapped(self, screen, text, x, y, max_width, font, color):
        words = text.split(' ')
        lines = []; current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            if font.size(test_line)[0] < max_width: current_line.append(word)
            else: lines.append(' '.join(current_line)); current_line = [word]
        lines.append(' '.join(current_line))
        for i, line in enumerate(lines):
            if y + i * 15 > self.BOTTOM_LIMIT: break
            s = font.render(line, True, color)
            screen.blit(s, (x, y + i * 16))

    def _draw_page_prog(self, screen):
        # ---------------------------------------------------------
        # 1. Basic Calculation (Fuel, Flow, Endurance)
        # ---------------------------------------------------------
        fuel_kg = getattr(self.fms, 'cached_fuel', 0.0)
        ff_kg_hr = getattr(self.fms, 'cached_flow', 0.0)
        if ff_kg_hr > 0.5:  # Calculate only if flow > 0.5kg/h
            endurance_hr = fuel_kg / ff_kg_hr
            hrs = int(endurance_hr)
            mins = int((endurance_hr - hrs) * 60)
            endurance_str = f"{min(hrs,99):02d}:{mins:02d}"

        else:
        # No flow, endurance unknown
            endurance_str = "--:--" 
            endurance_hr = 0.0
        
        rng = endurance_hr * self.fms.current_gs
        
        # ---------------------------------------------------------
        # 2. Trip Calculation (Trip, EFOB)
        # ---------------------------------------------------------
        trip_time_hr = self.fms.time_to_dest / 3600.0
        trip_burn = trip_time_hr * ff_kg_hr
        efob = fuel_kg - trip_burn
        
        fin_reserve = getattr(self.fms, 'fin_reserve', 0.0)
        abv_rsv = efob - fin_reserve
        
        rsv_color = C_GREEN_NAV if abv_rsv >= 0 else C_RED
        prefix = "+" if abv_rsv >= 0 else ""
        
        # ETA Calculation
        eta_dest = "--:--"
        if self.fms.is_loaded and self.fms.time_to_dest > 0:
            arr_time = time.time() + self.fms.time_to_dest
            t = time.gmtime(arr_time)
            eta_dest = f"{t.tm_hour:02d}:{t.tm_min:02d}Z"

        # ---------------------------------------------------------
        # 3. Draw UI (Lines 1-3)
        # ---------------------------------------------------------
        y = 80; col1 = 10; col2 = 250; label_w = 110; line_h = 35
        
        # Line 1: Fuel & Flow
        self._kv_aligned(screen, "FUEL OB", f"{int(fuel_kg):,} KG", col1, y, label_w, C_WHITE)
        self._kv_aligned(screen, "FF", f"{int(ff_kg_hr)} KG/H", col2, y, 40, C_WHITE)
        y += line_h
        
        # Line 2: Endurance & Range
        self._kv_aligned(screen, "ENDURANCE", endurance_str, col1, y, label_w, C_CYAN)
        self._kv_aligned(screen, "RANGE", f"{int(rng)} NM", col2, y, 60, C_CYAN)
        y += line_h
        
        # Line 3: EFOB & Reserves
        self._kv_aligned(screen, "DEST EFOB", f"{int(efob)} KG", col1, y, label_w, rsv_color)
        self._kv_aligned(screen, "ABV RSV", f"{prefix}{int(abv_rsv)}", col2, y, 80, rsv_color, size="S")
        y += line_h
        
        # ---------------------------------------------------------
        # 4. ETA & ETE/TOBT Switching Logic
        # ---------------------------------------------------------
        # Left: Always show ETA
        self._kv_aligned(screen, "ETA DEST", eta_dest, col1, y, label_w, C_WHITE)
        
        # Right: Check Ground State (GS < 30kts)
        is_on_ground = self.fms.current_gs < 30
        
        if is_on_ground:
            # [Ground Mode] Show TOBT
            tobt_val = getattr(self.fms, 'tobt_str', "--:--Z")
            self._kv_aligned(screen, "TOBT", tobt_val, col2, y, 50, C_CYAN, size="M") 
        else:
            # [Flight Mode] Show ETE
            rem_m = int(self.fms.time_to_dest / 60)
            hh = rem_m // 60; mm = rem_m % 60
            ete_str = f"(IN {hh:02d}:{mm:02d})"
            self._kv_aligned(screen, "ETE", ete_str, col2, y, 50, C_GRAY_LIGHT, size="S") 
            
        y += line_h + 5
        
        # ---------------------------------------------------------
        # 5. Bottom Info (T/D, VDEV)
        # ---------------------------------------------------------
        pygame.draw.line(screen, C_GRAY_DARK, (10, y), (SCREEN_W-10, y), 1)
        y += 10
        
        td_dist = self.fms.dist_to_td
        td_str = "---" if td_dist > 9000 else ("PASSED" if td_dist < 0 else f"{int(td_dist)} NM")
        self._kv_aligned(screen, "> T/D", td_str, col1, y, 60, C_WHITE)
        
        vdev = self.fms.vnav_deviation
        vdev_str = "OK" if abs(vdev) < 100 else f"{int(vdev)} FT"
        vdev_col = C_GREEN_NAV if abs(vdev) < 500 else C_AMBER
        self._kv_aligned(screen, "VDEV", vdev_str, col2, y, 60, vdev_col)

    def _draw_page_navrad(self, screen):
        # ---------------------------------------------------------
        # 1. Helper Calculations
        # ---------------------------------------------------------
        def haversine_calc(lat1, lon1, lat2, lon2):
            R = 3440.065 
            try:
                phi1, phi2 = math.radians(lat1), math.radians(lat2)
                dphi = math.radians(lat2 - lat1); dlam = math.radians(lon2 - lon1)
                a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
                return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a)))
            except: return 999.0

        def bearing_calc(lat1, lon1, lat2, lon2):
            try:
                lat1, lon1 = math.radians(lat1), math.radians(lon1)
                lat2, lon2 = math.radians(lat2), math.radians(lon2)
                y = math.sin(lon2 - lon1) * math.cos(lat2)
                x = math.cos(lat1)*math.sin(lat2) - math.sin(lat1)*math.cos(lat2)*math.cos(lon2 - lon1)
                return (math.degrees(math.atan2(y, x)) + 360) % 360
            except: return 0

        # ---------------------------------------------------------
        # 2. Fetch Data
        # ---------------------------------------------------------
        row97 = self.data_link.get_row(97)
        row98 = self.data_link.get_row(98)
        row99  = self.data_link.get_row(99)   # NAV 1 Deflection
        row100 = self.data_link.get_row(100)  # NAV 2 Deflection

        curr_nav1_freq = f"{row97[0]/100:.2f}"
        curr_nav2_freq = f"{row97[4]/100:.2f}"
        curr_nav1_obs = int(row98[0])
        curr_nav2_obs = int(row98[4])
        
        # DME Data Processing
        d1 = row99[4]
        d2 = row100[4]
        # Show value if valid, else ---.-
        curr_nav1_dme = f"{d1:.1f}" if d1 > 0.1 else "---.-"
        curr_nav2_dme = f"{d2:.1f}" if d2 > 0.1 else "---.-"

        # ---------------------------------------------------------
        # 3. List Matching Logic
        # ---------------------------------------------------------
        pos_row = self.data_link.get_row(20)
        ac_lat = pos_row[0]
        ac_lon = pos_row[1]
        
        # Fallback: If data link not ready
        if abs(ac_lat) < 0.01 and abs(ac_lon) < 0.01:
             # Fallback to FMS last known pos
             ac_lat = getattr(self.fms, 'last_lat', 0.0)
             ac_lon = getattr(self.fms, 'last_lon', 0.0)
        display_items = []
        
        start_idx = max(0, self.fms.active_idx - 1)
        scan_count = 0
        
        # Scan more rows
        for i in range(start_idx, len(self.fms.legs)):
            if scan_count >= 10: break 
            leg = self.fms.legs[i]
            freq = getattr(leg, 'frequency', '')
            if not freq: continue
            
            dist = haversine_calc(ac_lat, ac_lon, leg.lat, leg.lon)
            brg_to = bearing_calc(ac_lat, ac_lon, leg.lat, leg.lon)
            radial = (brg_to + 180) % 360 
            
            is_tuned = False
            if freq == curr_nav1_freq or freq == curr_nav2_freq:
                is_tuned = True
            
            display_items.append({
                'id': leg.ident, 'freq': freq, 'dist': dist, 'radial': radial,
                'is_active': (i == self.fms.active_idx), 'is_tuned': is_tuned
            })
            scan_count += 1

        # ---------------------------------------------------------
        # 4. Draw UI
        # ---------------------------------------------------------
        SPLIT_X = 210 # Split Panels
        
        # --- [Left] NAV STATUS (DME Priority) ---
        
        def draw_status_block(y_base, nav_name, freq, obs, dme_str):
            # Line 1: Header + DME
            screen.blit(self.font_xs.render(nav_name, True, C_GRAY_LIGHT), (15, y_base + 5))
            
            # DME Value (Amber, Large)
            dme_label = self.font_xs.render("DME:", True, C_WHITE)
            dme_val   = self.font_l.render(dme_str, True, C_WHITE)
            
            screen.blit(dme_label, (70, y_base + 5)) 
            screen.blit(dme_val, (110, y_base)) 

            # Line 2: Frequency (Cyan, Large)
            # Slight offset up
            y_freq = y_base + 26 
            screen.blit(self.font_l.render(freq, True, C_CYAN), (15, y_freq))
            
            # Line 3: OBS
            y_obs = y_freq + 32 
            screen.blit(self.font_s.render(f"CRS: {obs:03d}", True, C_WHITE), (15, y_obs))

        # Draw NAV 1 (Y=80)
        draw_status_block(80, "NAV 1", curr_nav1_freq, curr_nav1_obs, curr_nav1_dme)
        pygame.draw.rect(screen, (30, 40, 30), self.rect_nav1_click, 1, border_radius=5)
        
        # Divider line
        mid_y = 175
        pygame.draw.line(screen, C_GRAY_DARK, (10, mid_y), (SPLIT_X - 10, mid_y), 1)
        
        # Draw NAV 2
        draw_status_block(180, "NAV 2", curr_nav2_freq, curr_nav2_obs, curr_nav2_dme)

        # Vertical divider
        pygame.draw.line(screen, C_GRAY_DARK, (SPLIT_X, 60), (SPLIT_X, BUTTON_Y - 5), 2)

        # --- [Right] STATION LIST ---
        list_x = SPLIT_X + 10
        y = 80
        
        screen.blit(self.font_m.render("RADIO ASSIST", True, C_CYAN), (list_x, y))
        pygame.draw.rect(screen, (50, 50, 0), self.rect_hold_btn, border_radius=3)
        lbl_hold = self.font_xs.render("HOLD", True, C_WHITE)
        screen.blit(lbl_hold, (self.rect_hold_btn.x + 4, self.rect_hold_btn.y + 2))
        y += 30
        
        headers = ["ID", "FREQ", "DIST", "RAD"]
        
        # Column offsets
        col_offsets = [0, 50, 115, 170] 
        
        for i, h in enumerate(headers): 
            screen.blit(self.font_xs.render(h, True, C_GRAY_LIGHT), (list_x + col_offsets[i], y))
        
        y += 15
        pygame.draw.line(screen, C_GRAY_DARK, (list_x, y), (SCREEN_W-10, y), 1)
        y += 8

        # List Content
        if not display_items:
            screen.blit(self.font_s.render("NO VOR DATA", True, C_GRAY_DARK), (list_x, y))
        else:
            for item in display_items:
                if y > BUTTON_Y - 25: break 

                if item['is_tuned']:
                    pygame.draw.rect(screen, (0, 50, 0), (list_x - 5, y - 2, SCREEN_W - list_x, 24))
                    text_color = C_GREEN
                elif item['is_active']:
                    text_color = C_WHITE 
                else:
                    text_color = C_GRAY_LIGHT

                # ID
                screen.blit(self.font_s.render(item['id'], True, text_color), (list_x + col_offsets[0], y))
                # FREQ
                c_freq = C_GREEN if item['is_tuned'] else C_CYAN
                screen.blit(self.font_s.render(item['freq'], True, c_freq), (list_x + col_offsets[1], y))
                # DIST
                dist_str = f"{item['dist']:.1f}"
                screen.blit(self.font_s.render(dist_str, True, text_color), (list_x + col_offsets[2], y))
                # RAD
                rad_str = f"{int(item['radial']):03d}"
                screen.blit(self.font_s.render(rad_str, True, C_AMBER), (list_x + col_offsets[3], y))
                
                y += 26
