import pygame
import time
from config import *

# --- CONFIG STATE ---
STATE_NORMAL = 0
STATE_MENU = 1       
STATE_CONFIRM_DCT = 2
STATE_INPUT_SPD = 3  
STATE_INPUT_ALT = 4   

class NavDisplay:
    def __init__(self, shared_fms):
        self.fms = shared_fms  
        
        # FONTS
        self.font_xs = pygame.font.SysFont("arial", 14)
        self.font_s = pygame.font.SysFont("arial", 18)
        self.font_m = pygame.font.SysFont("arial", 22, bold=True)
        self.font_l = pygame.font.SysFont("arial", 32, bold=True) 
        self.font_mono = pygame.font.SysFont("consolas", 18, bold=True)
        self.font_key = pygame.font.SysFont("arial", 20, bold=True)
        
        self.scroll_offset = 0  
        self.max_rows = 4      
        self.use_metric = SHOW_METRIC_ALT 
        self.ui_state = STATE_NORMAL
        self.selected_leg_idx = -1  
        
        # INTERACTION STATE 
        self.press_start_time = 0
        self.pressed_row_idx = -1 # -1: Active Panel, 0+: List Rows
        self.is_holding = False
        self.LONG_PRESS_THRESHOLD = 0.5 
        
        self.input_buffer = ""
        self.input_is_metric = False 
        
        self.list_click_rects = [] 
        
        # UI RECTS
        self.btn_up_rect = pygame.Rect(430, 150, 50, 60)
        self.btn_dn_rect = pygame.Rect(430, 215, 50, 60)
        self.btn_refresh_rect = pygame.Rect(0, 0, 0, 0)
        self.rect_alt_toggle = pygame.Rect(0, 0, 0, 0)
        
        # ACTIVE PANEL TOUCH AREA (Ident + T/D)
        self.rect_active_panel = pygame.Rect(0, 30, 140, 110)

        cx = SCREEN_W // 2
        
        # POPUP RECTS
        self.rect_menu_dct = pygame.Rect(cx-100, 80, 200, 40)
        self.rect_menu_spd = pygame.Rect(cx-100, 130, 200, 40)
        self.rect_menu_alt = pygame.Rect(cx-100, 180, 200, 40)
        self.rect_confirm_yes = pygame.Rect(cx-80, 150, 70, 40)
        self.rect_confirm_no  = pygame.Rect(cx+10, 150, 70, 40)
        self.rect_input_display = pygame.Rect(cx-100, 45, 200, 40)

        self.keypad_rects = []
        btn_size = 40  
        gap = 6        
        keypad_w = (3 * btn_size) + (2 * gap)
        kp_start_x = (SCREEN_W - keypad_w) // 2
        kp_start_y = 100 
        
        keys = ['1','2','3','4','5','6','7','8','9','C','0','>']
        for i, k in enumerate(keys):
            r = i // 3
            c = i % 3
            rect = pygame.Rect(kp_start_x + c*(btn_size+gap), kp_start_y + r*(btn_size+gap), btn_size, btn_size)
            self.keypad_rects.append((rect, k))

    def update(self, link_data, screen):
        # LONG PRESS LOGIC
        if self.ui_state == STATE_NORMAL and self.is_holding:
            if time.time() - self.press_start_time > self.LONG_PRESS_THRESHOLD:
                self.is_holding = False 
                
                # Case 1: Active Panel Long Press (-1)
                if self.pressed_row_idx == -1:
                    self.selected_leg_idx = self.fms.active_idx
                    leg = self.fms.legs[self.selected_leg_idx]
                    
                    # Pre-fill buffer with current altitude
                    if self.use_metric:
                        self.input_is_metric = True
                        self.input_buffer = str(int(leg.plan_alt * 0.3048))
                    else:
                        self.input_is_metric = False
                        self.input_buffer = str(int(leg.plan_alt))
                    
                    self.ui_state = STATE_INPUT_ALT
                
                # Case 2: List Row Long Press (0+)
                else:
                    base_idx = self.fms.active_idx + 1
                    real_idx = base_idx + self.scroll_offset + self.pressed_row_idx
                    
                    if real_idx < len(self.fms.legs):
                        self.selected_leg_idx = real_idx
                        self.ui_state = STATE_MENU 
        
        self._draw_normal_view(screen, link_data)
        
        if self.ui_state != STATE_NORMAL:
            s = pygame.Surface((SCREEN_W, SCREEN_H))
            s.set_alpha(200) 
            s.fill((0,0,0))
            screen.blit(s, (0,0))
            
            if self.ui_state == STATE_MENU:
                self._draw_popup_menu(screen)
            elif self.ui_state == STATE_CONFIRM_DCT:
                self._draw_popup_confirm(screen)
            elif self.ui_state in [STATE_INPUT_SPD, STATE_INPUT_ALT]:
                self._draw_popup_input(screen)

    def handle_keydown(self, event):
        if self.ui_state not in [STATE_INPUT_SPD, STATE_INPUT_ALT]:
            return

        if event.key >= pygame.K_0 and event.key <= pygame.K_9:
            char = str(event.key - pygame.K_0)
            if len(self.input_buffer) < 6: self.input_buffer += char
        
        elif event.key >= pygame.K_KP0 and event.key <= pygame.K_KP9:
            char = str(event.key - pygame.K_KP0)
            if len(self.input_buffer) < 6: self.input_buffer += char

        elif event.key == pygame.K_PERIOD or event.key == pygame.K_KP_PERIOD:
            if "." not in self.input_buffer and len(self.input_buffer) < 6:
                self.input_buffer += "."

        elif event.key == pygame.K_BACKSPACE:
            self.input_buffer = self.input_buffer[:-1]

        elif event.key == pygame.K_DELETE or event.key == pygame.K_ESCAPE:
            self.input_buffer = ""
            if event.key == pygame.K_ESCAPE: self.ui_state = STATE_NORMAL

        elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
            self._submit_input()
            self.ui_state = STATE_NORMAL

    def _draw_normal_view(self, screen, link_data):
        lat = link_data.get('lat', 0)
        lon = link_data.get('lon', 0)
        alt = link_data.get('alt_msl_ft', 0)
        gs  = link_data.get('gs_kt', 0)
        
        is_zero_state = (abs(lat) < 0.1 and abs(lon) < 0.1 and abs(alt) < 10.0 and gs < 1.0)
        is_data_valid = not is_zero_state
        
        screen.fill(C_BLACK)
        
        self.draw_header_strip(screen, link_data)
        
        if not self.fms.is_loaded:
            s = self.font_m.render(self.fms.status_msg, True, C_AMBER)
            screen.blit(s, (SCREEN_W//2 - s.get_width()//2, 100))
            return

        self.draw_active_panel(screen, gs, is_data_valid)
        self.draw_next_list(screen)

    def draw_header_strip(self, screen, data):
        pygame.draw.rect(screen, (20,20,20), (0,0, SCREEN_W, 30))
        route = f"{self.fms.origin}>{self.fms.dest}"
        s_route = self.font_s.render(route, True, C_CYAN)
        screen.blit(s_route, (5, 5))
        
        refresh_x = 5 + s_route.get_width() + 10
        s_refresh = self.font_s.render("refresh", True, C_GREEN_NAV)
        self.btn_refresh_rect = s_refresh.get_rect(topleft=(refresh_x, 5))
        self.btn_refresh_rect.inflate_ip(10, 10) 
        screen.blit(s_refresh, (refresh_x, 5))
        
        phase_txt = self.fms.phase
        phase_color = C_GREEN_NAV
        if self.fms.crz_warn:
            phase_txt = self.fms.crz_warn
            phase_color = C_AMBER
        s_phase = self.font_s.render(phase_txt, True, phase_color)
        screen.blit(s_phase, (SCREEN_W//2 - s_phase.get_width()//2, 5))

        w_spd = int(data.get('wind_spd', 0))
        w_dir = int(data.get('wind_dir', 0))
        s_wind = self.font_xs.render(f"WIND: {w_dir:03d}/{w_spd}", True, C_GREEN_NAV)
        screen.blit(s_wind, (SCREEN_W - 110, 7))

        bar_bg_rect = pygame.Rect(0, 27, SCREEN_W, 3)
        pygame.draw.rect(screen, (50, 50, 50), bar_bg_rect) 
        
        if self.fms.progress_pct > 0:
            fill_width = int(SCREEN_W * (self.fms.progress_pct / 100.0))
            fill_width = min(fill_width, SCREEN_W)
            pygame.draw.rect(screen, C_GREEN_NAV, (0, 27, fill_width, 3))

    def draw_active_panel(self, screen, gs_kt, is_valid):
        if self.fms.active_idx >= len(self.fms.legs): return
        leg = self.fms.legs[self.fms.active_idx]
        
        panel_rect = pygame.Rect(0, 30, SCREEN_W, 110)
        pygame.draw.rect(screen, (30,30,40), panel_rect)
        
        # Highlight if holding active panel
        if self.is_holding and self.pressed_row_idx == -1:
            pygame.draw.rect(screen, (60,60,70), self.rect_active_panel)

        pygame.draw.line(screen, C_GRAY_LIGHT, (0, 140), (SCREEN_W, 140), 2)

        lbl_to = self.font_s.render("FLYING TO:", True, C_GRAY_LIGHT)
        screen.blit(lbl_to, (10, 35))
        s_ident = self.font_l.render(leg.ident, True, C_MAGENTA)
        screen.blit(s_ident, (10, 55))

        if self.fms.phase in ["CRZ", "DES"]:
            td = self.fms.dist_to_td
            td_x, td_y = 10, 90 
            if td < 0:
                self._draw_kv(screen, "VNAV STATUS", "DES PATH", td_x, td_y, C_MAGENTA)
            else:
                val = f"{td*1.852:.0f}KM" if SHOW_METRIC_DIST else f"{td:.0f}NM"
                self._draw_kv(screen, "TO T/D", val, td_x, td_y, C_WHITE)

        col1_x, col2_x, col3_x = 140, 240, 364 
        if is_valid:
            dist_str = f"{leg.dist_to_go * 1.852:.1f}KM" if SHOW_METRIC_DIST else f"{leg.dist_to_go:.1f}NM"
            brg_str = f"{leg.bearing:03d}°"
        else:
            dist_str, brg_str = "N/A", "---"
        
        self._draw_kv(screen, "BRG", brg_str, col1_x, 45, C_GREEN_NAV)
        self._draw_kv(screen, "REM DIST", dist_str, col1_x, 90, C_WHITE)

        if not is_valid: eta_val = "NO DATA"
        elif gs_kt < 100: eta_val = "CHECK SPD"
        else: eta_val = leg.eta_str
        eta_col = C_AMBER if "CHECK" in eta_val else (C_GRAY_LIGHT if "NO" in eta_val else C_WHITE)
        self._draw_kv(screen, "ETE", eta_val, col2_x, 45, eta_col)

        s_alt_lbl = self.font_xs.render("ALT REQ", True, C_GRAY_LIGHT)
        screen.blit(s_alt_lbl, (col2_x, 90))
        
        if self.use_metric:
            val_str = f"{int(leg.target_alt * 0.3048)} M"
        else:
            val_str = f"{int(leg.target_alt)} FT"
            
        s_alt_val = self.font_mono.render(val_str, True, C_CYAN)
        screen.blit(s_alt_val, (col2_x, 90 + 15))
        self.rect_alt_toggle = pygame.Rect(col2_x, 90, max(s_alt_lbl.get_width(), s_alt_val.get_width()), 35)

        phase = self.fms.phase
        if (not is_valid) or (phase in ["GND", "TO", "TO/CLB"]):
             self._draw_kv(screen, "TGT V/S", "---", col3_x, 60, C_GRAY_DARK, size="L")
        else:
            vs_fpm = leg.target_vs_fpm 
            vs_ms = vs_fpm / 196.85
            if abs(vs_ms) > 0.5:
                prefix = "+" if vs_ms > 0 else ""
                val_str = f"{prefix}{vs_ms:.1f} m/s"
                color = C_GREEN_NAV
            else:
                val_str, color = "0.0 m/s", C_GRAY_LIGHT
            self._draw_kv(screen, "TGT V/S", val_str, col3_x, 60, color, size="L")
            
            if (not self.use_metric) and abs(vs_ms) > 0.5:
                s_fpm = self.font_xs.render(f"({int(vs_fpm)} fpm)", True, C_GRAY_LIGHT)
                screen.blit(s_fpm, (col3_x, 100))

    def _draw_kv(self, screen, label, value, x, y, color, size="M"):
        s_lbl = self.font_xs.render(label, True, C_GRAY_LIGHT)
        screen.blit(s_lbl, (x, y))
        font = self.font_m if size == "L" else self.font_mono
        s_val = font.render(value, True, color)
        screen.blit(s_val, (x, y + 15))

    def draw_next_list(self, screen):
        start_y = 150
        row_h = 30
        self.list_click_rects = [] 
        
        unit_str = "M" if self.use_metric else "FT"
        headers = [("NEXT", 10), ("TRK", 120), ("LEG", 190), (f"SPD/ALT({unit_str})", 300)]
        for h, x in headers:
            s = self.font_xs.render(h, True, C_GRAY_DARK)
            screen.blit(s, (x, start_y))
            
        start_y += 20
        
        base_idx = self.fms.active_idx + 1
        display_start_idx = base_idx + self.scroll_offset
        total_remaining = len(self.fms.legs) - base_idx
        
        for i in range(self.max_rows): 
            idx = display_start_idx + i
            if idx >= len(self.fms.legs): break
            
            leg = self.fms.legs[idx]
            y = start_y + i * row_h
            
            rect = pygame.Rect(0, y, SCREEN_W - 60, row_h)
            self.list_click_rects.append(rect)
            
            if self.is_holding and self.pressed_row_idx == i:
                pygame.draw.rect(screen, (50,50,50), rect)

            s_id = self.font_s.render(leg.ident, True, C_GRAY_LIGHT)
            screen.blit(s_id, (10, y))
            
            s_trk = self.font_mono.render(f"{leg.leg_course:03d}°", True, C_GREEN_NAV)
            screen.blit(s_trk, (120, y))
            
            d_str = f"{leg.leg_dist_static * 1.852:.0f}" if SHOW_METRIC_DIST else f"{leg.leg_dist_static:.0f}"
            s_dist = self.font_mono.render(d_str, True, C_GRAY_LIGHT)
            screen.blit(s_dist, (190, y))
            
            CROSSOVER_ALT = 26000
            if leg.plan_alt >= CROSSOVER_ALT and leg.plan_mach > 0.1:
                spd_str = f".{int(leg.plan_mach * 100):02d}" 
            else:
                spd_str = f"{int(leg.plan_spd_kmh)}" if leg.plan_spd_kmh != 0 else "---"
            
            alt_val = int(leg.plan_alt * 0.3048) if self.use_metric else int(leg.plan_alt)
            s_alt = self.font_mono.render(f"{spd_str}/{alt_val}", True, C_GREEN_NAV)
            screen.blit(s_alt, (300, y))
            
            pygame.draw.line(screen, (30,30,30), (0, y+25), (SCREEN_W, y+25), 1)

        pygame.draw.rect(screen, (20,20,20), (430, 150, 50, 130))
        pygame.draw.line(screen, C_GRAY_DARK, (430, 150), (430, 280), 1)
        
        can_scroll_further = (self.scroll_offset + self.max_rows) < total_remaining
        can_scroll_back = self.scroll_offset > 0
        
        up_color = C_GRAY_LIGHT if can_scroll_further else C_GRAY_DARK
        dn_color = C_GRAY_LIGHT if can_scroll_back else C_GRAY_DARK
        
        cx_up, cy_up = self.btn_up_rect.centerx, self.btn_up_rect.centery
        pygame.draw.polygon(screen, up_color, [(cx_up, cy_up - 10), (cx_up - 10, cy_up + 10), (cx_up + 10, cy_up + 10)])
        
        cx_dn, cy_dn = self.btn_dn_rect.centerx, self.btn_dn_rect.centery
        pygame.draw.polygon(screen, dn_color, [(cx_dn, cy_dn + 10), (cx_dn - 10, cy_dn - 10), (cx_dn + 10, cy_dn - 10)])

    def _draw_popup_menu(self, screen):
        leg = self.fms.legs[self.selected_leg_idx]
        title = self.font_m.render(f"WPT: {leg.ident}", True, C_CYAN)
        screen.blit(title, (SCREEN_W//2 - title.get_width()//2, 40))
        
        def draw_btn(rect, text, color):
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, C_WHITE, rect, 2)
            t = self.font_s.render(text, True, C_BLACK)
            screen.blit(t, t.get_rect(center=rect.center))
            
        draw_btn(self.rect_menu_dct, "DIRECT TO", C_AMBER)
        draw_btn(self.rect_menu_spd, "SET SPEED", C_GRAY_LIGHT)
        draw_btn(self.rect_menu_alt, "SET ALTITUDE", C_GRAY_LIGHT)
        
        hint = self.font_xs.render("TAP OUTSIDE TO CANCEL", True, C_GRAY_DARK)
        screen.blit(hint, (SCREEN_W//2 - hint.get_width()//2, SCREEN_H - 30))

    def _draw_popup_confirm(self, screen):
        leg = self.fms.legs[self.selected_leg_idx]
        title = self.font_m.render("DIRECT TO", True, C_AMBER)
        screen.blit(title, (SCREEN_W//2 - title.get_width()//2, 60))
        msg1 = self.font_s.render(f"FLY DIRECT TO {leg.ident}?", True, C_WHITE)
        msg2 = self.font_s.render("Ignore all previous WPT?", True, C_RED)
        screen.blit(msg1, (SCREEN_W//2 - msg1.get_width()//2, 100))
        screen.blit(msg2, (SCREEN_W//2 - msg2.get_width()//2, 125))
        
        pygame.draw.rect(screen, C_GREEN, self.rect_confirm_yes)
        pygame.draw.rect(screen, C_RED, self.rect_confirm_no)
        
        t_y = self.font_m.render("YES", True, C_BLACK)
        t_n = self.font_m.render("NO", True, C_WHITE)
        screen.blit(t_y, t_y.get_rect(center=self.rect_confirm_yes.center))
        screen.blit(t_n, t_n.get_rect(center=self.rect_confirm_no.center))

    def _draw_popup_input(self, screen):
        unit_str = ""
        if self.ui_state == STATE_INPUT_SPD:
            title_txt = "SET SPEED"
            unit_str = "MACH" if self.input_is_metric else "KM/H"
        else:
            title_txt = "SET ALTITUDE"
            unit_str = "METERS" if self.input_is_metric else "FEET"
            
        title = self.font_s.render(title_txt, True, C_GRAY_LIGHT)
        screen.blit(title, (SCREEN_W//2 - title.get_width()//2, 15))
        
        pygame.draw.rect(screen, (0,0,50), self.rect_input_display)
        pygame.draw.rect(screen, C_CYAN, self.rect_input_display, 2)
        
        val_surf = self.font_l.render(self.input_buffer, True, C_WHITE)
        screen.blit(val_surf, (self.rect_input_display.x + 10, self.rect_input_display.y + 2))
        
        unit_surf = self.font_xs.render(unit_str, True, C_AMBER)
        screen.blit(unit_surf, (self.rect_input_display.right - 50, self.rect_input_display.centery - 7))
        
        for rect, key in self.keypad_rects:
            color = C_GREEN_NAV if key == '>' else (C_RED if key == 'C' else C_GRAY_DARK)
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, C_GRAY_LIGHT, rect, 1)
            t = self.font_key.render(key, True, C_WHITE)
            screen.blit(t, t.get_rect(center=rect.center))

    def handle_click(self, pos):
        x, y = pos
        if self.ui_state == STATE_NORMAL:
            # 1. LIST CLICK
            for i, rect in enumerate(self.list_click_rects):
                if rect.collidepoint(x, y):
                    self.is_holding = True
                    self.press_start_time = time.time()
                    self.pressed_row_idx = i
                    return 

            # 2. ACTIVE PANEL CLICK (NEW)
            if self.rect_active_panel.collidepoint(x, y):
                 if self.fms.active_idx < len(self.fms.legs):
                    self.is_holding = True
                    self.press_start_time = time.time()
                    self.pressed_row_idx = -1
                    return

            # 3. BUTTONS
            if self.btn_up_rect.collidepoint(pos):
                 total_remaining = len(self.fms.legs) - (self.fms.active_idx + 1)
                 if (self.scroll_offset + self.max_rows) < total_remaining: self.scroll_offset += 1
            elif self.btn_dn_rect.collidepoint(pos):
                self.scroll_offset = max(0, self.scroll_offset - 1)
            elif self.btn_refresh_rect.collidepoint(pos):
                print("Force refreshing SimBrief...")
                self.fms.fetch_simbrief(force_download=True)
                self.scroll_offset = 0
            elif self.rect_alt_toggle.collidepoint(pos):
                self.use_metric = not self.use_metric
            return

        if self.ui_state == STATE_MENU:
            if self.rect_menu_dct.collidepoint(pos): self.ui_state = STATE_CONFIRM_DCT
            elif self.rect_menu_spd.collidepoint(pos):
                self.ui_state = STATE_INPUT_SPD
                leg = self.fms.legs[self.selected_leg_idx]
                if leg.plan_mach > 0.1:
                    self.input_is_metric = True 
                    self.input_buffer = f".{int(leg.plan_mach*100)}"
                else:
                    self.input_is_metric = False 
                    self.input_buffer = str(int(leg.plan_spd_kmh))
            elif self.rect_menu_alt.collidepoint(pos):
                self.ui_state = STATE_INPUT_ALT
                leg = self.fms.legs[self.selected_leg_idx]
                if self.use_metric:
                    self.input_is_metric = True 
                    self.input_buffer = str(int(leg.plan_alt * 0.3048))
                else:
                    self.input_is_metric = False 
                    self.input_buffer = str(int(leg.plan_alt))
            else:
                self.ui_state = STATE_NORMAL
            return

        if self.ui_state == STATE_CONFIRM_DCT:
            if self.rect_confirm_yes.collidepoint(pos):
                self.fms.set_direct_to(self.selected_leg_idx)
                self.ui_state = STATE_NORMAL
                self.scroll_offset = 0 
            elif self.rect_confirm_no.collidepoint(pos):
                self.ui_state = STATE_NORMAL
            return

        if self.ui_state in [STATE_INPUT_SPD, STATE_INPUT_ALT]:
            if self.rect_input_display.collidepoint(pos):
                self.input_is_metric = not self.input_is_metric
                self.input_buffer = "" 
                return
            for rect, key in self.keypad_rects:
                if rect.collidepoint(pos):
                    if key == 'C': self.input_buffer = ""
                    elif key == '>':
                        self._submit_input()
                        self.ui_state = STATE_NORMAL
                    else:
                        if len(self.input_buffer) < 6: self.input_buffer += key
                    return
            self.ui_state = STATE_NORMAL

    def _submit_input(self):
        if not self.input_buffer: return
        try:
            val = float(self.input_buffer)
            if self.ui_state == STATE_INPUT_SPD:
                is_mach = self.input_is_metric
                if is_mach and val > 2.0: val = val / 100.0
                self.fms.modify_leg_constraint(self.selected_leg_idx, spd=val, is_mach=is_mach)
            elif self.ui_state == STATE_INPUT_ALT:
                self.fms.modify_leg_constraint(self.selected_leg_idx, alt=val, is_metric=self.input_is_metric)
        except ValueError:
            print("Invalid Input")

    def handle_mouseup(self):
        self.is_holding = False
