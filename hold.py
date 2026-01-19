import pygame
import math
from config import *

def normalize_angle(angle):
    """Normalize angle to 0-360 degrees."""
    return angle % 360

def get_bearing(lat1, lon1, lat2, lon2):
    """
    Calculate True Bearing from point 1 (lat1, lon1) to point 2 (lat2, lon2).
    Returns degrees (0-360).
    """
    try:
        lat1_r, lon1_r = math.radians(lat1), math.radians(lon1)
        lat2_r, lon2_r = math.radians(lat2), math.radians(lon2)
        y = math.sin(lon2_r - lon1_r) * math.cos(lat2_r)
        x = math.cos(lat1_r)*math.sin(lat2_r) - math.sin(lat1_r)*math.cos(lat2_r)*math.cos(lon2_r - lon1_r)
        return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0
    except: return 0.0

def haversine_nm(lat1, lon1, lat2, lon2):
    """Calculate distance in Nautical Miles (NM) between two points."""
    R = 3440.065 
    try:
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi, dlam = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
        return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a)))
    except: return 0.0

class HoldPage:
    def __init__(self, shared_fms, data_link):
        self.fms = shared_fms
        self.data_link = data_link
        
        self.font_s = pygame.font.SysFont("arial", 13) # Small labels
        self.font_m = pygame.font.SysFont("arial", 18, bold=True) # Button text
        self.font_l = pygame.font.SysFont("arial", 22, bold=True) # Plus/Minus signs
        self.font_xl = pygame.font.SysFont("arial", 26, bold=True) # Large values
        
        self.hold_fix_idx = -1  # -1 = Auto-track Active Waypoint
        self.inbound_course = 0
        self.turn_dir = 'R'     # 'R' Right Turn, 'L' Left Turn
        self.leg_time_min = 1.0 # Default 1 minute
        
        self.entry_type = "---"
        self.wind_corr_angle = 0.0
        self.outbound_time = 0.0
        
        self.Y_START = 75       # Shift up
        self.LEFT_X = 10        # Left margin
        self.BTN_H = 32         # Slightly shorter buttons (35 -> 32)
        self.ROW_GAP = 55       # Compress row gap
        
        y_r1 = 90
        self.rect_crs_minus = pygame.Rect(self.LEFT_X, y_r1, 40, self.BTN_H)
        self.rect_crs_disp  = pygame.Rect(self.LEFT_X + 45, y_r1, 100, self.BTN_H)
        self.rect_crs_plus  = pygame.Rect(self.LEFT_X + 150, y_r1, 40, self.BTN_H)
        
        y_r2 = y_r1 + self.ROW_GAP
        self.rect_turn_btn = pygame.Rect(self.LEFT_X, y_r2, 90, self.BTN_H)
        self.rect_time_btn = pygame.Rect(self.LEFT_X + 100, y_r2, 90, self.BTN_H)

        self.rect_fix_prev = pygame.Rect(215, 80, 40, 30)
        self.rect_fix_next = pygame.Rect(435, 80, 40, 30)

        self.initialized = False

    def update(self, screen):
        # 1. Initialization Sync
        if not self.initialized and self.fms.is_loaded and self.fms.legs:
            self._sync_to_active_leg()
            self.initialized = True
            
        # 2. Fetch Data
        ac_lat = self.data_link.data.get('lat', 0.0)
        ac_lon = self.data_link.data.get('lon', 0.0)
        ac_hdg = self.data_link.data.get('hdg', 0.0)
        tas = max(100, self.data_link.data.get('tas_kt', 200.0))
        gs  = max(50,  self.data_link.data.get('gs_kt', 200.0))
        wind_spd = self.data_link.data.get('wind_spd', 0.0)
        wind_dir = self.data_link.data.get('wind_dir', 0.0)
        
        # 3. Fix Data
        fix_lat, fix_lon, fix_ident = 0.0, 0.0, "NO FIX"
        target_idx = self.fms.active_idx if self.hold_fix_idx == -1 else self.hold_fix_idx
        
        if self.fms.legs and 0 <= target_idx < len(self.fms.legs):
            leg = self.fms.legs[target_idx]
            fix_lat, fix_lon, fix_ident = leg.lat, leg.lon, leg.ident
            
        # 4. Calculations
        dist_to_fix = haversine_nm(ac_lat, ac_lon, fix_lat, fix_lon)
        bearing_fix_to_ac = get_bearing(fix_lat, fix_lon, ac_lat, ac_lon)
        
        self._calc_wind_correction(tas, gs, wind_spd, wind_dir)
        self._calc_entry_sector(ac_hdg)

        # 5. Drawing
        self._draw_left_panel(screen)
        self._draw_map(screen, ac_lat, ac_lon, ac_hdg, bearing_fix_to_ac, dist_to_fix, tas, fix_ident)

    def _sync_to_active_leg(self):
        """Syncs the inbound course to the FMS active leg on startup."""
        idx = self.fms.active_idx
        if self.fms.legs and 0 <= idx < len(self.fms.legs):
            self.inbound_course = self.fms.legs[idx].leg_course
            self.hold_fix_idx = -1 

    def _calc_wind_correction(self, tas, gs, wind_spd, wind_dir):
        """Calculates Wind Correction Angle (WCA) and adjusted Outbound Time."""
        rad_diff = math.radians(wind_dir - self.inbound_course)
        x_wind = wind_spd * math.sin(rad_diff)
        try:
            wca_rad = math.asin(min(1.0, max(-1.0, x_wind / tas)))
            self.wind_corr_angle = math.degrees(wca_rad)
        except: self.wind_corr_angle = 0.0
        
        headwind = wind_spd * math.cos(rad_diff)
        gs_out = tas + headwind 
        gs_in = tas - headwind
        if gs_out > 10:
            self.outbound_time = (self.leg_time_min * 60 * gs_in) / gs_out
        else:
            self.outbound_time = self.leg_time_min * 60

    def _calc_entry_sector(self, hdg):
        """Determines the standard ICAO entry sector (Direct, Parallel, Teardrop)."""
        
        # 1. Calculate aircraft bearing relative to Fix
        ac_lat = self.data_link.data.get('lat', 0.0)
        ac_lon = self.data_link.data.get('lon', 0.0)
        target_idx = self.fms.active_idx if self.hold_fix_idx == -1 else self.hold_fix_idx
        
        if not self.fms.legs or target_idx >= len(self.fms.legs):
            return

        fix = self.fms.legs[target_idx]
        bearing_fix_to_ac = get_bearing(fix.lat, fix.lon, ac_lat, ac_lon)

        # 2. Calculate angle difference relative to the INBOUND COURSE
        # ICAO Definition: Parallel/Teardrop are sectors on either side of the Inbound track.
        # Direct is the large sector on the Outbound track side.
        
        diff = bearing_fix_to_ac - self.inbound_course
        
        # Normalize to -180 ~ +180
        if diff > 180: diff -= 360
        if diff < -180: diff += 360

        # 3. Sector Determination (Based on Inbound Course)
        # 
        # Right Turn Procedure:
        #   - Teardrop: 0~70 deg right of Inbound (Sector 2)
        #   - Parallel: 0~110 deg left of Inbound (Sector 1)
        #   - Direct:   Remaining 180 deg (Sector 3)
        
        if self.turn_dir == 'R':
            if 0 <= diff <= 70:
                self.entry_type = "TEARDROP"
            elif -110 <= diff < 0:
                self.entry_type = "PARALLEL"
            else:
                self.entry_type = "DIRECT"
        else:
            # Left Turn Procedure - Mirrored
            if -70 <= diff < 0:
                self.entry_type = "TEARDROP" # Left side is Teardrop
            elif 0 <= diff <= 110:
                self.entry_type = "PARALLEL" # Right side is Parallel
            else:
                self.entry_type = "DIRECT"

    def handle_click(self, pos):
        if self.rect_crs_minus.collidepoint(pos):
            self.inbound_course = normalize_angle(self.inbound_course - 10)
        elif self.rect_crs_plus.collidepoint(pos):
            self.inbound_course = normalize_angle(self.inbound_course + 10)
        elif self.rect_turn_btn.collidepoint(pos):
            self.turn_dir = 'L' if self.turn_dir == 'R' else 'R'
        elif self.rect_time_btn.collidepoint(pos):
            self.leg_time_min += 0.5
            if self.leg_time_min > 3.0: self.leg_time_min = 0.5
            
        elif self.rect_fix_prev.collidepoint(pos):
            if self.hold_fix_idx == -1: self.hold_fix_idx = self.fms.active_idx
            self.hold_fix_idx = max(0, self.hold_fix_idx - 1)
            if 0 <= self.hold_fix_idx < len(self.fms.legs):
                self.inbound_course = self.fms.legs[self.hold_fix_idx].leg_course
        elif self.rect_fix_next.collidepoint(pos):
            if self.hold_fix_idx == -1: self.hold_fix_idx = self.fms.active_idx
            self.hold_fix_idx = min(len(self.fms.legs)-1, self.hold_fix_idx + 1)
            if 0 <= self.hold_fix_idx < len(self.fms.legs):
                self.inbound_course = self.fms.legs[self.hold_fix_idx].leg_course

    def _draw_left_panel(self, screen):
        # 1. INBOUND CRS 
        screen.blit(self.font_s.render("INBOUND CRS", True, C_GRAY_LIGHT), (self.LEFT_X, self.rect_crs_minus.y - 15))
        
        # Draw Minus Button
        pygame.draw.rect(screen, (50, 50, 50), self.rect_crs_minus, border_radius=5)
        txt_m = self.font_l.render("-", True, C_WHITE)
        screen.blit(txt_m, txt_m.get_rect(center=self.rect_crs_minus.center))
        
        # Draw Value Background
        pygame.draw.rect(screen, (30, 30, 30), self.rect_crs_disp, border_radius=5)
        txt_c = self.font_xl.render(f"{int(self.inbound_course):03d}°", True, C_AMBER)
        screen.blit(txt_c, txt_c.get_rect(center=self.rect_crs_disp.center))
        
        # Draw Plus Button
        pygame.draw.rect(screen, (50, 50, 50), self.rect_crs_plus, border_radius=5)
        txt_p = self.font_l.render("+", True, C_WHITE)
        screen.blit(txt_p, txt_p.get_rect(center=self.rect_crs_plus.center))
        
        # 2. TURN & TIME 
        screen.blit(self.font_s.render("TURN", True, C_GRAY_LIGHT), (self.LEFT_X, self.rect_turn_btn.y - 15))
        screen.blit(self.font_s.render("TIME", True, C_GRAY_LIGHT), (self.rect_time_btn.x, self.rect_time_btn.y - 15))
        
        pygame.draw.rect(screen, (50, 50, 50), self.rect_turn_btn, border_radius=5)
        t_turn = "RIGHT" if self.turn_dir == 'R' else "LEFT"
        screen.blit(self.font_m.render(t_turn, True, C_WHITE), 
                    self.font_m.render(t_turn, True, C_WHITE).get_rect(center=self.rect_turn_btn.center))
                    
        pygame.draw.rect(screen, (50, 50, 50), self.rect_time_btn, border_radius=5)
        t_time = f"{self.leg_time_min} MIN"
        screen.blit(self.font_m.render(t_time, True, C_WHITE),
                    self.font_m.render(t_time, True, C_WHITE).get_rect(center=self.rect_time_btn.center))
        
        # 3. Data Section 
        y_data = self.rect_turn_btn.bottom + 15
        
        screen.blit(self.font_s.render("ENTRY SECTOR:", True, C_GRAY_LIGHT), (self.LEFT_X, y_data))
        c_ent = C_GREEN if self.entry_type == "DIRECT" else C_AMBER
        screen.blit(self.font_l.render(self.entry_type, True, c_ent), (self.LEFT_X, y_data + 16))
        
        # WCA / OutT 
        y_data += 45 
        
        screen.blit(self.font_s.render(f"WCA:", True, C_GRAY_LIGHT), (self.LEFT_X, y_data))
        wca_str = f"{abs(self.wind_corr_angle):.0f}°" + ("L" if self.wind_corr_angle < 0 else "R")
        screen.blit(self.font_m.render(wca_str, True, C_WHITE), (self.LEFT_X, y_data + 15))
        
        screen.blit(self.font_s.render(f"OUT T:", True, C_GRAY_LIGHT), (self.LEFT_X + 100, y_data))
        out_min = int(self.outbound_time / 60)
        out_sec = int(self.outbound_time % 60)
        screen.blit(self.font_m.render(f"{out_min}:{out_sec:02d}", True, C_CYAN), (self.LEFT_X + 100, y_data + 15))

    def _draw_map(self, screen, ac_lat, ac_lon, ac_hdg, brg_fix_to_ac, dist_nm, tas, ident):
        # Map Area 
        rect_map = pygame.Rect(215, 80, 260, 200)
        
        pygame.draw.rect(screen, (0, 0, 0), rect_map)
        pygame.draw.rect(screen, (80, 80, 80), rect_map, 1)

        title_bg = pygame.Rect(rect_map.x, rect_map.y, rect_map.width, 30)
        pygame.draw.rect(screen, (20, 20, 30), title_bg)
        pygame.draw.line(screen, (80,80,80), (title_bg.left, title_bg.bottom), (title_bg.right, title_bg.bottom), 1)
        
        txt_fix = self.font_l.render(ident, True, C_CYAN)
        screen.blit(txt_fix, txt_fix.get_rect(center=title_bg.center))
        
        # Draw Toggle Arrows
        pc = self.rect_fix_prev.center
        pygame.draw.polygon(screen, C_GRAY_LIGHT, [(pc[0]-6, pc[1]), (pc[0]+4, pc[1]-6), (pc[0]+4, pc[1]+6)])
        nc = self.rect_fix_next.center
        pygame.draw.polygon(screen, C_GRAY_LIGHT, [(nc[0]+6, nc[1]), (nc[0]-4, nc[1]-6), (nc[0]-4, nc[1]+6)])

        old_clip = screen.get_clip()
        map_area = pygame.Rect(rect_map.x + 1, rect_map.y + 31, rect_map.width - 2, rect_map.height - 32)
        screen.set_clip(map_area)
        
        cx, cy = map_area.centerx, map_area.centery

        # 1. Scaling Logic
        turn_r_nm = tas / 200.0  
        leg_len_nm = (tas / 60.0) * self.leg_time_min 
        target_nm_h = max(leg_len_nm + 2*turn_r_nm, 4.0) * 1.5 
        scale = (map_area.height) / target_nm_h
        scale = min(scale, 25.0) 

        # 2. Draw Hold Pattern
        r_px = int(turn_r_nm * scale)
        l_px = int(leg_len_nm * scale)
        
        surf_size = int((r_px * 4 + l_px * 2) * 1.5)
        track_surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        tcx, tcy = surf_size // 2, surf_size // 2
        
        offset = 1 if self.turn_dir == 'R' else -1
        
        # --- A. Straight Legs ---
        # Inbound
        pygame.draw.line(track_surf, C_CYAN, (tcx, tcy+l_px), (tcx, tcy), 3)
        
        out_x = tcx + (r_px * 2 * offset)
        pygame.draw.line(track_surf, (100,100,100), (out_x, tcy), (out_x, tcy+l_px), 2)
        
        # --- B. Semicircle Arcs ---
        # Calculate center X for arcs (Midpoint between Inbound and Outbound lines)
        center_arc_x = (tcx + out_x) / 2
        
        # Top Turn (Top Rect) - Connects Fix and Outbound Top
        rect_top = pygame.Rect(0, 0, r_px*2, r_px*2)
        rect_top.center = (center_arc_x, tcy + l_px)
        
        # Bottom Turn (Bot Rect) - Connects Inbound Start and Outbound Bot
        rect_bot = pygame.Rect(0, 0, r_px*2, r_px*2)
        rect_bot.center = (center_arc_x, tcy)
        
        # Regardless of turn direction, top is always convex (n), bottom is always concave (U)
        # Top Semicircle: pi -> 2pi
        pygame.draw.arc(track_surf, (100,100,100), rect_top, math.pi, 2*math.pi, 2)
        # Bottom Semicircle: 0 -> pi
        pygame.draw.arc(track_surf, (100,100,100), rect_bot, 0, math.pi, 2)
        
        # Rotate Pattern
        rot_track = pygame.transform.rotate(track_surf, -self.inbound_course)
        screen.blit(rot_track, rot_track.get_rect(center=(cx, cy)))
        
        # Fix Point
        pygame.draw.circle(screen, C_CYAN, (cx, cy), 5)

        # 3. Draw Aircraft (With Clipping Logic)
        rad_brg = math.radians(brg_fix_to_ac)
        px_dist = dist_nm * scale
        
        # Clipping detection radius
        max_r_px = min(map_area.width, map_area.height) / 2 - 15
        is_clipped = False
        if px_dist > max_r_px:
            px_dist = max_r_px
            is_clipped = True
            
        ac_x = cx + px_dist * math.sin(rad_brg)
        ac_y = cy - px_dist * math.cos(rad_brg)
        
        tip = (ac_x + 10*math.sin(math.radians(ac_hdg)), ac_y - 10*math.cos(math.radians(ac_hdg)))
        wl  = (ac_x + 7*math.sin(math.radians(ac_hdg-140)), ac_y - 7*math.cos(math.radians(ac_hdg-140)))
        wr  = (ac_x + 7*math.sin(math.radians(ac_hdg+140)), ac_y - 7*math.cos(math.radians(ac_hdg+140)))
        
        color = C_GREEN if not is_clipped else C_AMBER
        pygame.draw.polygon(screen, color, [tip, wl, wr])
        
        screen.blit(self.font_s.render("N", True, (150,150,150)), (cx-5, map_area.top + 5))
        rng_val = int(map_area.height / 2 / scale)
        screen.blit(self.font_s.render(f"RNG: {rng_val} NM", True, (100,100,100)), (map_area.left + 5, map_area.bottom - 18))

        screen.set_clip(old_clip)
