import pygame
import math
from config import *

class ISFDDisplay:
    def __init__(self, shared_fms):
        self.fms = shared_fms 
        self.screen = pygame.display.get_surface()
        
        # Core Attitude Parameters
        self.px_per_deg = 6.0
        self.adi_size = 1200 
        self.adi_surface = pygame.Surface((self.adi_size, self.adi_size))
        
        # Tape Parameters
        self.tape_w = 65 
        
        # Fonts
        self.font_large = pygame.font.SysFont("arial", 28, bold=True)
        self.font_std = pygame.font.SysFont("arial", 20, bold=True)
        self.font_small = pygame.font.SysFont("arial", 14, bold=True)
        
        self._pre_render_adi()

    def _pre_render_adi(self):
        """Pre-render sky, ground, and pitch ladder for performance."""
        cx, cy = self.adi_size // 2, self.adi_size // 2
        # Sky & Ground
        pygame.draw.rect(self.adi_surface, (0, 110, 220), (0, 0, self.adi_size, cy))
        pygame.draw.rect(self.adi_surface, (130, 90, 50), (0, cy, self.adi_size, cy))
        # Horizon Line
        pygame.draw.line(self.adi_surface, C_WHITE, (0, cy), (self.adi_size, cy), 3)
        
        # Pitch Ladder
        for p in range(-90, 91, 5):
            if p == 0: continue
            y = cy - int(p * self.px_per_deg)
            if p % 10 == 0:
                w = 110
                pygame.draw.line(self.adi_surface, C_WHITE, (cx - w//2, y), (cx + w//2, y), 2)
                txt = self.font_small.render(str(abs(p)), True, C_WHITE)
                self.adi_surface.blit(txt, (cx - w//2 - 22, y - 8))
                self.adi_surface.blit(txt, (cx + w//2 + 5, y - 8))
            else:
                w = 50
                pygame.draw.line(self.adi_surface, C_WHITE, (cx - w//2, y), (cx + w//2, y), 1)

    def update(self, data):
        # 1. Extract Data
        pitch = -data.get('pitch', 0.0) 
        roll = data.get('roll', 0.0)    
        ias = data.get('ias_kt', 0.0)
        alt = data.get('alt_msl_ft', 0.0)
        hdg = data.get('hdg', 0.0)
        vvi = data.get('vvi', 0.0) 

        # 2. Clear Background
        pygame.draw.rect(self.screen, C_BLACK, (0, 0, SCREEN_W, BUTTON_Y))

        # 3. Draw ADI
        self._draw_adi_core(pitch, roll)

        # 4. Draw Aircraft Symbol
        self._draw_aircraft_symbol()

        # 5. Draw Tapes
        self._draw_airspeed_tape(ias)
        self._draw_altitude_tape(alt, vvi) 

        # 6. Draw Heading
        self._draw_heading_box(hdg)

    def _draw_adi_core(self, pitch, roll):
        crop = 400
        cx, cy = SCREEN_W // 2, BUTTON_Y // 2
        
        p_move = pitch * self.px_per_deg
        
        src_rect = pygame.Rect(0, 0, crop, crop)
        src_rect.center = (self.adi_size // 2, self.adi_size // 2 + p_move)
        
        sub_surf = self.adi_surface.subsurface(src_rect.clamp(self.adi_surface.get_rect()))
        rotated_surf = pygame.transform.rotate(sub_surf, roll)
        
        rot_rect = rotated_surf.get_rect(center=(cx, cy))
        self.screen.set_clip(pygame.Rect(self.tape_w, 0, SCREEN_W - 2*self.tape_w, BUTTON_Y))
        self.screen.blit(rotated_surf, rot_rect)
        self.screen.set_clip(None)

    def _draw_aircraft_symbol(self):
        cx, cy = SCREEN_W // 2, BUTTON_Y // 2
        pygame.draw.rect(self.screen, C_BLACK, (cx-90, cy-3, 50, 6))
        pygame.draw.rect(self.screen, C_AMBER, (cx-88, cy-2, 46, 4))
        pygame.draw.rect(self.screen, C_BLACK, (cx+40, cy-3, 50, 6))
        pygame.draw.rect(self.screen, C_AMBER, (cx+42, cy-2, 46, 4))
        pygame.draw.rect(self.screen, C_BLACK, (cx-7, cy-7, 14, 14))
        pygame.draw.rect(self.screen, C_AMBER, (cx-5, cy-5, 10, 10))

    def _draw_airspeed_tape(self, ias):
        x_base = 0
        tape_bg_rect = pygame.Rect(x_base, 0, self.tape_w, BUTTON_Y)
        pygame.draw.rect(self.screen, (15, 15, 15), tape_bg_rect) 
        pygame.draw.line(self.screen, C_GRAY_LIGHT, (self.tape_w, 0), (self.tape_w, BUTTON_Y), 1)

        scale_factor = 3.0
        
        for v in range(int(ias-40), int(ias+40)):
            if v < 0 or v % 10 != 0: continue
            y = BUTTON_Y/2 + (ias - v) * scale_factor
            if 10 < y < BUTTON_Y - 10:
                pygame.draw.line(self.screen, C_WHITE, (self.tape_w-15, y), (self.tape_w, y), 2)
                txt = self.font_small.render(str(v), True, C_WHITE)
                self.screen.blit(txt, (10, y - 8))
        
        # --- Speed Trend Vector ---
        if self.fms and abs(self.fms.acceleration) > 0.5: 
            trend_kts = self.fms.acceleration * 10.0 
            trend_kts = max(-40, min(40, trend_kts))
            
            line_len = trend_kts * scale_factor
            
            start_x = self.tape_w
            start_y = BUTTON_Y / 2
            end_y = start_y - line_len 
            
            pygame.draw.line(self.screen, C_MAGENTA, (start_x, start_y), (start_x, end_y), 4)

        # Current Value Box
        pygame.draw.rect(self.screen, C_BLACK, (0, BUTTON_Y/2-18, self.tape_w, 36))
        pygame.draw.rect(self.screen, C_WHITE, (0, BUTTON_Y/2-18, self.tape_w, 36), 1)
        cur_ias = self.font_std.render(f"{ias:.0f}", True, C_WHITE)
        self.screen.blit(cur_ias, cur_ias.get_rect(center=(self.tape_w/2, BUTTON_Y/2)))

    def _draw_altitude_tape(self, alt, vvi):
        x_base = SCREEN_W - self.tape_w
        tape_bg_rect = pygame.Rect(x_base, 0, self.tape_w, BUTTON_Y)
        pygame.draw.rect(self.screen, (15, 15, 15), tape_bg_rect)
        pygame.draw.line(self.screen, C_GRAY_LIGHT, (x_base, 0), (x_base, BUTTON_Y), 1)

        scale_factor = 0.5
        
        start_v = int((alt - 500)/100)*100
        for v in range(start_v, start_v + 1100, 100):
            y = BUTTON_Y/2 + (alt - v) * scale_factor
            if 10 < y < BUTTON_Y - 10:
                pygame.draw.line(self.screen, C_WHITE, (x_base, y), (x_base+15, y), 2)
                txt = self.font_small.render(str(v), True, C_WHITE)
                self.screen.blit(txt, (x_base + 20, y - 8))

        # --- Altitude Trend Vector ---
        if abs(vvi) > 40:
            trend_ft = vvi / 6.0 
            line_len = trend_ft * scale_factor
            line_len = max(-150, min(150, line_len))
            
            start_x = x_base
            start_y = BUTTON_Y / 2
            end_y = start_y - line_len
            
            pygame.draw.line(self.screen, C_MAGENTA, (start_x, start_y), (start_x, end_y), 4)
        
        # --- VDEV Indicator (VNAV Path Deviation) ---
        if self.fms and self.fms.phase in ['CRZ', 'DES']:
            dev = getattr(self.fms, 'vnav_deviation', 0.0)
            
            center_y = BUTTON_Y / 2
            vdev_x = x_base - 12
            
            pygame.draw.line(self.screen, C_WHITE, (vdev_x - 5, center_y), (vdev_x + 5, center_y), 1)
            for dot_off in [-100, -50, 50, 100]:
                pygame.draw.circle(self.screen, C_GRAY_LIGHT, (vdev_x, center_y + dot_off), 2)

            vdev_scale = 0.4 
            offset_px = dev * vdev_scale
            max_off = 130 
            clamped_offset = max(-max_off, min(max_off, offset_px))
            
            target_y = center_y - clamped_offset
            
            if abs(clamped_offset) < max_off:
                diamond_col = C_AMBER if abs(dev) > 500 else C_MAGENTA
                
                d_w, d_h = 10, 14
                pts = [
                    (vdev_x, target_y - d_h//2), 
                    (vdev_x + d_w//2, target_y), 
                    (vdev_x, target_y + d_h//2), 
                    (vdev_x - d_w//2, target_y)
                ]
                pygame.draw.polygon(self.screen, diamond_col, pts)
                pygame.draw.polygon(self.screen, C_WHITE, pts, 1)

        # Current Value Box
        alt_col = C_GREEN if alt < 10000 else C_WHITE
        pygame.draw.rect(self.screen, C_BLACK, (x_base, BUTTON_Y/2-18, self.tape_w, 36))
        pygame.draw.rect(self.screen, C_WHITE, (x_base, BUTTON_Y/2-18, self.tape_w, 36), 1)
        cur_alt = self.font_std.render(f"{alt:.0f}", True, alt_col)
        self.screen.blit(cur_alt, cur_alt.get_rect(center=(x_base + self.tape_w/2, BUTTON_Y/2)))

    def _draw_heading_box(self, hdg):
        rect = pygame.Rect(SCREEN_W//2 - 35, BUTTON_Y - 32, 70, 28)
        pygame.draw.rect(self.screen, C_BLACK, rect)
        pygame.draw.rect(self.screen, C_CYAN, rect, 1)
        txt = self.font_std.render(f"{hdg:03.0f}°", True, C_CYAN)
        self.screen.blit(txt, txt.get_rect(center=rect.center))