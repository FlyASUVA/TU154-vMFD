import pygame
import math
import time
from config import *

class StepperControl:

    def __init__(self, x, y, label, init_val, step_s=1, step_l=10, is_float=False):
        self.x, self.y = x, y
        self.label = label
        self.value = init_val
        self.step_s = step_s
        self.step_l = step_l
        self.is_float = is_float
        
        # FONT
        self.font_label = pygame.font.SysFont("arial", 12)
        self.font_val   = pygame.font.SysFont("consolas", 20, bold=True)
        self.font_btn   = pygame.font.SysFont("arial", 18, bold=True)

        btn_w, btn_h = 32, 32 
        ctrl_y_offset = 18
        
        # BUTTON ZONE
        self.rect_minus = pygame.Rect(x, y + ctrl_y_offset, btn_w, btn_h)
        val_w = 60
        self.val_center_x = x + btn_w + (val_w // 2)
        self.val_center_y = y + ctrl_y_offset + (btn_h // 2)
        self.rect_plus = pygame.Rect(x + btn_w + val_w, y + ctrl_y_offset, btn_w, btn_h)

        self.last_update_time = 0
        self.initial_delay = 0.4 
        self.repeat_rate = 0.08 
        self.holding_btn = None 
        self.hold_start_time = 0

    def update(self):
        mouse_pressed = pygame.mouse.get_pressed()[0]
        mouse_pos = pygame.mouse.get_pos()
        now = time.time()

        if not mouse_pressed:
            self.holding_btn = None
            return

        current_hover = None
        if self.rect_minus.collidepoint(mouse_pos):
            current_hover = 'minus'
        elif self.rect_plus.collidepoint(mouse_pos):
            current_hover = 'plus'
        
        if current_hover and self.holding_btn != current_hover:
            self.holding_btn = current_hover
            self.hold_start_time = now
            self.last_update_time = now
            self._change_value(-1 if current_hover == 'minus' else 1)
        
        elif current_hover and self.holding_btn == current_hover:
            if now - self.hold_start_time > self.initial_delay:
                if now - self.last_update_time > self.repeat_rate:
                    self._change_value(-1 if current_hover == 'minus' else 1)
                    self.last_update_time = now
        else:
            self.holding_btn = None

    def _change_value(self, direction):
        step = self.step_s 
        self.value += (step * direction)
        
        if not self.is_float:
            self.value = self.value % 360
        else:
            self.value = max(1.0, self.value)

    def draw(self, screen):
        # Label
        lbl_surf = self.font_label.render(self.label, True, C_GRAY_LIGHT)
        screen.blit(lbl_surf, (self.x, self.y))
        
        # [-]
        col_minus = (60, 60, 60) if self.holding_btn == 'minus' else (40, 40, 40)
        pygame.draw.rect(screen, col_minus, self.rect_minus, border_radius=4)
        pygame.draw.rect(screen, C_GRAY_DARK, self.rect_minus, 1, border_radius=4)
        txt_min = self.font_btn.render("-", True, C_WHITE)
        screen.blit(txt_min, txt_min.get_rect(center=self.rect_minus.center))
        
        # Value
        val_str = f"{self.value:.1f}" if self.is_float else f"{int(self.value):03d}"
        txt_val = self.font_val.render(val_str, True, C_GREEN_NAV)
        screen.blit(txt_val, txt_val.get_rect(center=(self.val_center_x, self.val_center_y)))
        
        # [+]
        col_plus = (60, 60, 60) if self.holding_btn == 'plus' else (40, 40, 40)
        pygame.draw.rect(screen, col_plus, self.rect_plus, border_radius=4)
        pygame.draw.rect(screen, C_GRAY_DARK, self.rect_plus, 1, border_radius=4)
        txt_plus = self.font_btn.render("+", True, C_WHITE)
        screen.blit(txt_plus, txt_plus.get_rect(center=self.rect_plus.center))

    def handle_click(self, pos):
        if self.rect_minus.collidepoint(pos):
            self._change_value(-1) # 点击减号立即减1
        elif self.rect_plus.collidepoint(pos):
            self._change_value(1)

class RSIPage:
    def __init__(self, fms, data_link):
        self.fms = fms
        self.data_link = data_link
        
        self.cw_mode = True 
        
        # --- UI LAYOUT ---
        self.split_line_x = 300 
        self.center_x, self.center_y = 150, 160 
        self.radius = 85 
        
        # RIGHT PANEL
        start_x = 328
        start_y = 75
        spacing_y = 70
        
        self.input_in  = StepperControl(start_x, start_y, "INBOUND RADIAL", 90, 1, 10)
        self.input_out = StepperControl(start_x, start_y + spacing_y, "OUTBOUND RADIAL", 180, 1, 10)
        self.input_dme = StepperControl(start_x, start_y + spacing_y*2, "ARC DIST", 7.0, 0.1, 1.0, is_float=True)
        
        # CW/CCW BUTTON
        self.rect_mode_toggle = pygame.Rect(self.split_line_x - 75, 245, 70, 25)
        
        # EXIT BUTTON
        self.rect_exit = pygame.Rect(10, 245, 60, 25)
        
        # FONT
        self.font_s = pygame.font.SysFont("arial", 12)
        self.font_title = pygame.font.SysFont("arial", 14, bold=True)
        self.font_val_l = pygame.font.SysFont("consolas", 18, bold=True)
        self.font_exit = pygame.font.SysFont("arial", 14, bold=True)
        self.font_freq = pygame.font.SysFont("consolas", 18, bold=True)

    def _calculate_bearing(self, lat1, lon1, lat2, lon2):
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        d_lon = lon2 - lon1
        y = math.sin(d_lon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(d_lon)
        brg = math.degrees(math.atan2(y, x))
        return (brg + 360) % 360

    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        R = 3440.065 
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        d_lat = lat2 - lat1
        d_lon = lon2 - lon1
        a = math.sin(d_lat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(d_lon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    def _find_station_and_calc(self, nav_freq):
        row20 = self.data_link.get_row(20)
        ac_lat, ac_lon = row20[0], row20[1]
        
        if abs(ac_lat) < 0.01: 
            return 0, 0, False

        target_leg = None
        
        if hasattr(self.fms, 'legs'):
            for leg in self.fms.legs:
                freq_raw = getattr(leg, 'frequency', None)
                if freq_raw is None or isinstance(freq_raw, (dict, list)):
                    continue
                try:
                    f_val = float(freq_raw)
                    if abs(f_val - nav_freq) < 0.01:
                        target_leg = leg
                        break
                except (ValueError, TypeError):
                    continue
        
        if target_leg:
            t_lat = getattr(target_leg, 'lat', 0)
            t_lon = getattr(target_leg, 'lon', 0)
            dist = self._calculate_distance(ac_lat, ac_lon, t_lat, t_lon)
            bearing_to = self._calculate_bearing(ac_lat, ac_lon, t_lat, t_lon)
            radial = (bearing_to + 180) % 360
            return radial, dist, True
        
        return 0, 0, False

    def update(self, screen):
        self.input_in.update()
        self.input_out.update()
        self.input_dme.update()

        safe_area = pygame.Rect(0, 36, SCREEN_W, 284) 
        pygame.draw.rect(screen, C_BLACK, safe_area)
        
        pygame.draw.line(screen, C_GRAY_DARK, (self.split_line_x, 40), (self.split_line_x, 280), 2)
        row97 = self.data_link.get_row(97)
        row98 = self.data_link.get_row(98)
        
        current_nav_freq = row97[0] / 100.0
        current_obs = int(row98[0])
        real_radial, real_dme, found_station = self._find_station_and_calc(current_nav_freq)
        
        if not found_station:
            row99 = self.data_link.get_row(99)
            real_dme = row99[4]
            real_radial = 0 

        self._draw_rsi_disc(screen, real_radial, real_dme, current_obs)
        
        self._draw_top_info(screen, current_obs, real_radial, real_dme, current_nav_freq)

        self._draw_buttons(screen)

        # 7. RIGHT PANEL
        self.input_in.draw(screen)
        self.input_out.draw(screen)
        self.input_dme.draw(screen)

    def _draw_top_info(self, screen, obs, rad, dme, freq):
        y_top = 45 
        
        # 1. [Left-Bottom] NAV1 FREQ
        txt_freq = self.font_freq.render(f"{freq:.2f}", True, C_WHITE)
        screen.blit(txt_freq, (10, y_top)) 
        
        # 2. [Left-Top] SELECTED CRS FOR NAV 1
        txt_crs = self.font_val_l.render(f"CRS {int(obs):03d}", True, (255, 0, 255))
        screen.blit(txt_crs, (10, y_top+22))
        
        # 3. [Center] TITLE
        txt_title = self.font_title.render("DME ARC VISUALIZER", True, C_GRAY_LIGHT)
        screen.blit(txt_title, txt_title.get_rect(center=(self.center_x, y_top + 10)))
        
        # 4. [Right-Top] ACTUAL DME
        txt_dme = self.font_val_l.render(f"{dme:.1f}NM", True, C_WHITE)
        rect_dme = txt_dme.get_rect(topright=(self.split_line_x - 10, y_top))
        screen.blit(txt_dme, rect_dme)

        # 5. [Right-Bottom] ACTUAL RADIAL
        txt_rad = self.font_val_l.render(f"RAD {int(rad):03d}", True, C_AMBER)
        rect_rad = txt_rad.get_rect(topright=(self.split_line_x - 10, y_top + 22))
        screen.blit(txt_rad, rect_rad)

    def _draw_buttons(self, screen):
        # CW/CCW 
        col = (0, 60, 60) if self.cw_mode else (60, 30, 0)
        pygame.draw.rect(screen, col, self.rect_mode_toggle, border_radius=5)
        pygame.draw.rect(screen, C_GRAY_LIGHT, self.rect_mode_toggle, 1, border_radius=5)
        txt = "CLKWISE" if self.cw_mode else "CTR.CLKW"
        surf = self.font_s.render(txt, True, C_WHITE)
        screen.blit(surf, surf.get_rect(center=self.rect_mode_toggle.center))

        # EXIT 
        pygame.draw.rect(screen, (180, 20, 20), self.rect_exit, border_radius=5)
        pygame.draw.rect(screen, (255, 100, 100), self.rect_exit, 1, border_radius=5)
        txt_exit = self.font_exit.render("EXIT", True, C_WHITE)
        screen.blit(txt_exit, txt_exit.get_rect(center=self.rect_exit.center))

    def _draw_rsi_disc(self, screen, cur_rad, cur_dme, cur_obs):
        cx, cy = self.center_x, self.center_y
        r = self.radius
        
        # FROM OBS
        reciprocal_obs = (cur_obs + 180) % 360 

        # BACKGROUND
        pygame.draw.circle(screen, (15, 20, 25), (cx, cy), r)
        pygame.draw.circle(screen, C_GRAY_DARK, (cx, cy), r, 2)
        pygame.draw.circle(screen, (40, 40, 40), (cx, cy), 4) 
        
        # --- DME ARC ---
        start_angle = self.input_in.value
        end_angle = self.input_out.value
        
        for i in range(0, 360, 10):
            rad = i
            angle_rad = math.radians(rad - 90)
            
            x1 = cx + (r - 8) * math.cos(angle_rad)
            y1 = cy + (r - 8) * math.sin(angle_rad)
            x2 = cx + r * math.cos(angle_rad)
            y2 = cy + r * math.sin(angle_rad)
            
            color = (60, 60, 60)
            
            is_active = False
            if self.cw_mode:
                dist_to_rad = (rad - start_angle) % 360
                total_span = (end_angle - start_angle) % 360
                if dist_to_rad <= total_span: is_active = True
            else: 
                dist_to_rad_ccw = (start_angle - rad) % 360
                total_span_ccw  = (start_angle - end_angle) % 360
                if dist_to_rad_ccw <= total_span_ccw: is_active = True
            
            if is_active:
                color = C_WHITE
                if abs(rad - start_angle) < 5: color = C_GREEN_NAV
                if abs(rad - end_angle) < 5: color = C_RED
            
            # 1. TO CRS (MAGENTA
            if abs(rad - cur_obs) < 5:
                pygame.draw.line(screen, (255, 0, 255), (cx, cy), (x2, y2), 2)
            # 2. FROM CRS (CYAN)
            elif abs(rad - reciprocal_obs) < 5:
                pygame.draw.line(screen, (0, 225, 255), (cx, cy), (x2, y2), 2)
            
            # 3. TICK
            else:
                pygame.draw.line(screen, color, (x1, y1), (x2, y2), 2)
                
        ac_angle_rad = math.radians(cur_rad - 90) 
        target_dme = self.input_dme.value
        if target_dme < 0.1: target_dme = 0.1
        
        scale_factor = r / target_dme 
        ac_dist_px = cur_dme * scale_factor
        
        if ac_dist_px > r + 15: ac_dist_px = r + 15
        
        ac_x = cx + ac_dist_px * math.cos(ac_angle_rad)
        ac_y = cy + ac_dist_px * math.sin(ac_angle_rad)
        
        dev = abs(cur_dme - target_dme)
        ac_col = C_GREEN_NAV
        if dev > 0.5: ac_col = C_AMBER
        if dev > 1.0 or dev < -0.5: ac_col = C_RED
        
        pygame.draw.circle(screen, ac_col, (int(ac_x), int(ac_y)), 5)
        pygame.draw.line(screen, ac_col, (int(ac_x), int(ac_y)), 
        (int(ac_x - 6*math.cos(ac_angle_rad)), int(ac_y - 6*math.sin(ac_angle_rad))), 1)

        # --- AIRCRAFT DOT ---
        ac_angle_rad = math.radians(cur_rad - 90) 
        target_dme = self.input_dme.value
        if target_dme < 0.1: target_dme = 0.1
        
        scale_factor = r / target_dme 
        ac_dist_px = cur_dme * scale_factor
        
        # ACCPETED TOLERANCE
        if ac_dist_px > r + 15: ac_dist_px = r + 15
        
        ac_x = cx + ac_dist_px * math.cos(ac_angle_rad)
        ac_y = cy + ac_dist_px * math.sin(ac_angle_rad)
        
        dev = abs(cur_dme - target_dme)
        ac_col = C_GREEN_NAV
        if dev > 0.5: ac_col = C_AMBER
        if dev > 1.0 or dev < -0.5: ac_col = C_RED
        
        pygame.draw.circle(screen, ac_col, (int(ac_x), int(ac_y)), 5)
        # TRACK THE PLANE!
        pygame.draw.line(screen, ac_col, (int(ac_x), int(ac_y)), 
        (int(ac_x - 6*math.cos(ac_angle_rad)), int(ac_y - 6*math.sin(ac_angle_rad))), 1)

    def handle_click(self, pos):
        if self.rect_exit.collidepoint(pos):
            return "EXIT"
        if self.rect_mode_toggle.collidepoint(pos):
            self.cw_mode = not self.cw_mode
            return None
        self.input_in.handle_click(pos)
        self.input_out.handle_click(pos)
        self.input_dme.handle_click(pos)
        return None
