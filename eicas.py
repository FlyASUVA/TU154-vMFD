import pygame
import time
from config import *

class EICAS:
    def __init__(self, shared_fms):
        self.fms = shared_fms 
        self.screen = pygame.display.get_surface()
        # --- FONTS ---
        try:
            self.font_digit_n1 = pygame.font.SysFont("arial", 26, bold=True)
            self.font_digit_egt = pygame.font.SysFont("arial", 18, bold=True)
            self.font_config = pygame.font.SysFont("arial", 20, bold=True)
            self.font_secondary = pygame.font.SysFont("arial", 18, bold=True)
            self.font_cas = pygame.font.SysFont("arial", 16, bold=True)
            self.font_label = pygame.font.SysFont("arial", 14)
            self.font_status = pygame.font.SysFont("arial", 13, bold=True)
            self.font_title = pygame.font.SysFont("arial", 24, bold=True)
            # LOW FUEL WARNING
            self.font_warn_huge = pygame.font.SysFont("arial", 16, bold=True)
        except:
            self.font_digit_n1 = pygame.font.Font(None, 30)
            self.font_digit_egt = pygame.font.Font(None, 24)
            self.font_config = pygame.font.Font(None, 24)
            self.font_secondary = pygame.font.Font(None, 20)
            self.font_cas = pygame.font.Font(None, 20)
            self.font_label = pygame.font.Font(None, 18)
            self.font_status = pygame.font.Font(None, 18)
            self.font_title = pygame.font.Font(None, 26)
            self.font_warn_huge = pygame.font.Font(None, 32)

    def update(self, data):
        # CLEAN SCREEN
        pygame.draw.rect(self.screen, C_BLACK, (0, 0, SCREEN_W, BUTTON_Y))

        # --- GLOBAL Y OFFSET ---
        Y_OFF = -30

        if data['connected']:
            # VERTICAL DIVIDER
            pygame.draw.line(self.screen, C_GRAY_DARK, (315, 0), (315, BUTTON_Y), 2)

            # ENG DISP TAPE
            cols_n1 = [36, 88, 140]
            cols_egt = [205, 247, 289]

            self._draw_engine_tapes(data, cols_n1, cols_egt, Y_OFF)
            self._draw_bottom_values(data, Y_OFF)
            self._draw_right_panel_final(data, Y_OFF)
        else:
            # OFFLINE PROMPT
            msg = self.font_title.render("CHECK SIM CONNECTION", True, C_AMBER)
            rect = msg.get_rect(center=(SCREEN_W // 2, BUTTON_Y // 2))
            self.screen.blit(msg, rect)

    def _draw_digital_box(self, center_x, bottom_y, text, font, color=C_WHITE, box_w=46):
        box_h = 28
        box_rect = pygame.Rect(0, 0, box_w, box_h)
        box_rect.midbottom = (center_x, bottom_y)

        pygame.draw.rect(self.screen, C_BLACK, box_rect)
        pygame.draw.rect(self.screen, C_WHITE, box_rect, 1)

        text_surf = font.render(text, True, color)
        max_text_w = box_w - 4
        if text_surf.get_width() > max_text_w:
            scale = max_text_w / text_surf.get_width()
            text_surf = pygame.transform.smoothscale(text_surf, (int(text_surf.get_width()*scale), int(text_surf.get_height()*scale)))

        text_rect = text_surf.get_rect(center=box_rect.center)
        text_rect.y += 1
        self.screen.blit(text_surf, text_rect)

    def _draw_engine_tapes(self, data, cols_n1, cols_egt, Y_OFF):
        tape_w = 16
        tape_h = 110
        box_bottom_y = 80 + Y_OFF
        tape_start_y = 92 + Y_OFF
        label_y = tape_start_y + tape_h + 14

        # N1 Group
        for i in range(3):
            val = data['n1'][i]
            self._draw_digital_box(cols_n1[i], box_bottom_y, f"{val:.1f}", self.font_digit_n1, C_WHITE, box_w=46)
            msg = "REV" if (i != 1 and data['reverse_state'][i] >= 3.0) else ("START" if data['starter_active'][i] else None)
            self._draw_pure_tape(cols_n1[i]-tape_w//2, tape_start_y, tape_w, tape_h, val, LIMIT_N1_MAX, status_msg=msg, target_marker=LIMIT_N1_TARGET)

        lbl = self.font_label.render("N1", True, C_BLUE)
        self.screen.blit(lbl, lbl.get_rect(center=(cols_n1[1], label_y)))

        # EGT Group
        DISPLAY_MAX_EGT = 800.0
        for i in range(3):
            val = data['egt'][i]
            col = C_RED if val > LIMIT_EGT_MAX else (C_AMBER if val > LIMIT_EGT_CAUTION else C_GREEN)
            self._draw_digital_box(cols_egt[i], box_bottom_y, f"{val:.0f}", self.font_digit_egt, col, box_w=38)
            self._draw_pure_tape(cols_egt[i]-tape_w//2, tape_start_y, tape_w, tape_h, val, DISPLAY_MAX_EGT, override_color=col, limit_line_val=LIMIT_EGT_MAX)

        lbl = self.font_label.render("EGT", True, C_BLUE)
        self.screen.blit(lbl, lbl.get_rect(center=(cols_egt[1], label_y)))

    def _draw_bottom_values(self, data, Y_OFF):
        start_y = 240 + Y_OFF
        val_x_starts = [60, 145, 230]

        # FF
        lbl_ff = self.font_label.render("FF", True, C_BLUE)
        self.screen.blit(lbl_ff, (5, start_y))
        for i in range(3):
            val = data.get('ff', [0,0,0])[i]
            txt = self.font_secondary.render(f"{val:.0f}", True, C_WHITE)
            self.screen.blit(txt, txt.get_rect(center=(val_x_starts[i], start_y + 9)))

        # CG & STAB
        y_cg = start_y + 40
        cg_mac = data.get('cg_mac', 0.0)
        cg_pos = "F" if cg_mac < 28.0 else ("R" if cg_mac > 35.0 else "C")
        cg_col = C_GREEN if cg_pos == "F" else (C_AMBER if cg_pos == "R" else C_WHITE)

        lbl_cg = self.font_label.render("CG", True, C_BLUE)
        self.screen.blit(lbl_cg, (5, y_cg))
        txt_cg = self.font_config.render(f"{cg_mac:.1f}% / {cg_pos}", True, cg_col)
        self.screen.blit(txt_cg, (45, y_cg - 2))

        # --- STAB Logic ---
        f_val = data.get('flaps', 0)
        f_deg = f_val if f_val > 1.1 else f_val * 45
        actual_stab = abs(data.get('stab_pos', 0.0))
        target_stab = 0.0

        if cg_pos == "F":
            if f_deg >= 40: target_stab = 5.5
            elif f_deg >= 10: target_stab = 3.0
        elif cg_pos == "C":
            if f_deg >= 40: target_stab = 3.0
            elif f_deg >= 10: target_stab = 1.5

        stab_x = 205 
        tgt_str = f"- {target_stab:.1f}" if target_stab > 0.01 else "0.0"
        act_str = f"- {actual_stab:.1f}" if actual_stab > 0.01 else "0.0"

        tgt_surf = self.font_status.render(f"TGT {tgt_str}", True, C_BLUE)
        self.screen.blit(tgt_surf, (stab_x, y_cg - 8)) 

        if f_deg < 2:
            stab_col = C_GRAY_LIGHT
        elif abs(actual_stab - target_stab) < 0.3:
            stab_col = C_GREEN
        else:
            stab_col = C_RED if actual_stab < target_stab else C_AMBER

        show_flash = True
        if stab_col == C_RED:
            show_flash = (int(time.time() * 4) % 2 == 0)

        if show_flash:
            act_surf = self.font_config.render(f"STAB {act_str}", True, stab_col)
            self.screen.blit(act_surf, (stab_x, y_cg + 4))

    def _draw_pure_tape(self, x, y, w, h, val, max_val, status_msg=None, override_color=None, limit_line_val=None, target_marker=None):
        pygame.draw.rect(self.screen, C_GRAY_DARK, (x, y, w, h))
        pygame.draw.rect(self.screen, C_GRAY_LIGHT, (x, y, w, h), 1)
        ratio = max(0.0, min(1.0, val / max_val))
        pygame.draw.rect(self.screen, override_color or C_GREEN, (x+2, y + h - int(h * ratio), w-4, int(h * ratio)))
        
        if limit_line_val:
            ly = y + h - int(h * (limit_line_val / max_val))
            pygame.draw.line(self.screen, C_RED, (x-2, ly), (x+w+2, ly), 2)
        if target_marker:
            ty = y + h - int(h * (target_marker / max_val))
            pygame.draw.line(self.screen, C_GREEN, (x-3, ty), (x+w+3, ty), 2)
        if status_msg:
            msg_surf = self.font_status.render(status_msg, True, C_BLACK)
            bg_rect = pygame.Rect(0, 0, max(msg_surf.get_width() + 4, 34), 14)
            bg_rect.center = (x + w//2, y + h - 12)
            pygame.draw.rect(self.screen, C_AMBER if status_msg == "REV" else C_GRAY_LIGHT, bg_rect)
            self.screen.blit(msg_surf, msg_surf.get_rect(center=bg_rect.center))

    def _draw_right_panel_final(self, data, Y_OFF):
        panel_x_start = 325
        
        # --- 1. CAS ---
        cas_y = 45 + Y_OFF 
        ias = data.get('ias_kt', 0.0)
        alt = data.get('alt_msl_ft', 0.0)
        n1_values = data.get('n1', [0, 0, 0])
        is_taking_off = any(n > 80.0 for n in n1_values)
        is_config_check_active = is_taking_off and ias < 180 and alt < 500
        is_blink_on = (int(time.time() * 4) % 2 == 0)

        f_ratio = data.get('flaps', 0.0)
        s_ratio = data.get('slats', 0.0)
        f_deg = int(f_ratio * 45)
        e_deg = data.get('elev_pos', 0.0)

        # Config Warn Logic
        if (is_taking_off and is_config_check_active):
            if f_deg < 14:
                if is_blink_on:
                    msg = self.font_status.render("CONFIG FLAPS", True, C_RED)
                    self.screen.blit(msg, (panel_x_start, cas_y))
                cas_y += 18
            if s_ratio < 0.9:
                if is_blink_on:
                    msg = self.font_status.render("CONFIG SLATS", True, C_RED)
                    self.screen.blit(msg, (panel_x_start, cas_y))
                cas_y += 18
            if not (-7.35 <= e_deg <= -1.2):
                if is_blink_on:
                    msg = self.font_status.render("CONFIG ELEV", True, C_RED)
                    self.screen.blit(msg, (panel_x_start, cas_y))
                cas_y += 18
            if data.get('park_brake', 0.0) > 0.5:
                if is_blink_on:
                    msg = self.font_status.render("CONFIG BRAKE", True, C_RED)
                    self.screen.blit(msg, (panel_x_start, cas_y))
                cas_y += 18

        if data.get('park_brake', 0.0) > 0.5 and not is_taking_off:
            pb_txt = self.font_status.render("PARK BRAKE SET", True, (0, 255, 255))
            self.screen.blit(pb_txt, (panel_x_start, cas_y))
            cas_y += 18

        if f_deg > 30 and data.get('sbrk', 0.0) > 0.1:
            msg = self.font_status.render("SPRK STILL OUT", True, C_AMBER)
            self.screen.blit(msg, (panel_x_start, cas_y))
            cas_y += 18

        # --- 2. GEAR & ELV CONFIG ---
        gear_center_x = panel_x_start + 40
        gear_center_y = 155 + Y_OFF
        g_val = data.get('gear_pos', 0.0)
        g_col = C_GREEN if g_val > 0.9 else (C_RED if g_val > 0.1 else C_GRAY_DARK)
        
        coords = [(gear_center_x, gear_center_y-20), (gear_center_x-28, gear_center_y+8), (gear_center_x+28, gear_center_y+8)]
        for cx, cy in coords:
            pygame.draw.circle(self.screen, g_col, (cx, cy), 9)
            pygame.draw.circle(self.screen, C_WHITE, (cx, cy), 9, 1)
        self.screen.blit(self.font_label.render("GEAR", True, C_WHITE), (gear_center_x-18, gear_center_y+23))

        elv_x, elv_y, elv_w, elv_h = panel_x_start + 110, 130 + Y_OFF, 10, 50
        pygame.draw.rect(self.screen, C_GRAY_DARK, (elv_x, elv_y, elv_w, elv_h))
        pygame.draw.rect(self.screen, C_GRAY_LIGHT, (elv_x, elv_y, elv_w, elv_h), 1)
        def get_elv_y(d): return elv_y + int((d - (-25)) / 40 * elv_h)
        pygame.draw.rect(self.screen, (0, 80, 0), (elv_x+1, get_elv_y(-7.35), elv_w-2, get_elv_y(-1.2) - get_elv_y(-7.35)))
        ptr_y = max(elv_y+1, min(elv_y+elv_h-1, get_elv_y(e_deg)))
        p_col = C_GREEN if (-7.35 <= e_deg <= -1.2) else C_WHITE
        pygame.draw.line(self.screen, p_col, (elv_x-4, ptr_y), (elv_x+elv_w+4, ptr_y), 2)
        self.screen.blit(self.font_status.render("ELV", True, C_BLUE), (elv_x-4, elv_y+elv_h+3))

        # --- 3. FLAPS & SLATS ---
        flaps_y_start = 210 + Y_OFF
        flap_txt = f"FLAPS {f_deg}" if f_deg > 0 else "FLAPS UP"
        self.screen.blit(self.font_config.render(flap_txt, True, C_WHITE), (panel_x_start, flaps_y_start))

        if s_ratio > 0.05:
            self.screen.blit(self.font_status.render("SLATS", True, C_BLUE), (panel_x_start + 100, flaps_y_start + 2))

        bar_x = panel_x_start
        bar_y = flaps_y_start + 25
        bar_w = 140
        pygame.draw.rect(self.screen, C_GRAY_DARK, (bar_x, bar_y, bar_w, 10))
        pygame.draw.rect(self.screen, C_GRAY_LIGHT, (bar_x, bar_y, bar_w, 10), 1)

        if s_ratio > 0.05:
            slats_len = int(s_ratio * bar_w)
            pygame.draw.rect(self.screen, C_BLUE, (bar_x + 1, bar_y + 1, slats_len - 2, 3))
        if f_ratio > 0:
            flap_len = int(f_ratio * bar_w)
            pygame.draw.rect(self.screen, C_WHITE, (bar_x + 1, bar_y + 5, flap_len - 2, 4))

        # --- 4. WEIGHT AND FUEL ---
        weight_y = 265 + Y_OFF
        fob_kg = data.get('fuel_weight', 0.0) 
        fob_t = fob_kg / 1000.0
        gw_t = data.get('total_weight', 0.0) / 1000.0
        
        # LOW FUEL WARNING AT 3000KG
        fob_col = C_WHITE
        if fob_kg < 3000.0:
            if is_blink_on:
                fob_col = C_RED
                alert_rect = pygame.Rect(panel_x_start, weight_y - 18, 100, 18)
                pygame.draw.rect(self.screen, C_RED, alert_rect, 2) 
                alert_txt = self.font_warn_huge.render("LOW FUEL", True, C_RED)
                self.screen.blit(alert_txt, (panel_x_start + 5, weight_y - 18))
        
        self.screen.blit(self.font_config.render(f"FOB: {fob_t:.1f}T", True, fob_col), (panel_x_start, weight_y))
        self.screen.blit(self.font_config.render(f"GW : {gw_t:.1f}T", True, C_WHITE), (panel_x_start, weight_y + 22))
