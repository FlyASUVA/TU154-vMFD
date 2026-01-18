import threading
import requests
import json
import os
import math
import time
from config import *

# --- CONSTANTS ---
EARTH_NM = 3440.065
KMH_PER_KNOT = 1.852
MIN_GS_FOR_CALC = 50.0
BARO_ALERT_CLEAR_SEC = 60.0
DESCENT_GRADIENT_FT_NM = globals().get("DESCENT_GRADIENT_FT_NM", 318.0) 

# --- ADDITIONAL PARAMETERS ---
def safe_float(val, default=0.0):
    try: return float(val)
    except: return float(default)

def safe_int(val, default=0):
    try: return int(val)
    except: return int(default)

def haversine_nm(lat1, lon1, lat2, lon2):
    try:
        if None in [lat1, lon1, lat2, lon2] or (abs(lat1) < 0.1 and abs(lon1) < 0.1): return 999.0
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi, dlambda = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
        return EARTH_NM * (2.0 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a))))
    except: return 999.0

def calculate_bearing(lat1, lon1, lat2, lon2):
    try:
        lat1_r, lon1_r = math.radians(lat1), math.radians(lon1)
        lat2_r, lon2_r = math.radians(lat2), math.radians(lon2)
        y = math.sin(lon2_r - lon1_r) * math.cos(lat2_r)
        x = math.cos(lat1_r)*math.sin(lat2_r) - math.sin(lat1_r)*math.cos(lat2_r)*math.cos(lon2_r - lon1_r)
        return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0
    except: return 0.0 

# --- FLIGHT DATA IMPORT ---
class FlightLeg:
    def __init__(self, fix_data):
        self.ident = fix_data.get('ident', 'WPT')
        self.type = fix_data.get('type', 'wpt')
        self.lat = safe_float(fix_data.get('pos_lat'))
        self.lon = safe_float(fix_data.get('pos_long'))
        self.plan_alt = safe_float(fix_data.get('altitude_feet'))
        self.msa = safe_float(fix_data.get('mora'))
        self.stage = fix_data.get('stage', '')
        self.frequency = fix_data.get('frequency', '') 

        raw_ias = safe_float(fix_data.get('ind_airspeed'))
        self.plan_spd_kmh = int(raw_ias * KMH_PER_KNOT) if raw_ias > 0 else 0
        self.plan_mach = safe_float(fix_data.get('mach'))

        self.leg_course = 0
        self.leg_dist_static = 0.0
        self.dist_to_go = 0.0
        self.bearing = 0
        self.eta_str = "--:--"
        self.target_alt = 0
        self.target_vs_fpm = 0

# --- FMS FUNCTIONS ---
class FMSCore:
    def __init__(self):
        self.lock = threading.Lock()
        self.legs = []
        self.origin, self.dest = "----", "----"
        self.origin_elev, self.dest_elev = 0, 0
        self.is_loaded = False
        self.status_msg = "NO F-PLN"
        self.active_idx = 0
        self.position_initialized = False

        self.dist_to_td, self.dist_to_dest = 9999.0, 0.0
        self.total_dist_static, self.progress_pct = 0.0, 0.0
        
        self.last_lat = 0.0
        self.last_lon = 0.0

        self.current_gs, self.last_gs = 0.0, 0.0
        self.last_time = time.time()
        self.acceleration = 0.0

        self.phase, self.crz_warn = "GND", ""
        self.baro_alert, self.baro_alert_start_time, self.last_alt = "", 0.0, 0.0

        self.fuel_pred_dest, self.time_to_dest, self.vnav_deviation = 0.0, 0.0, 0.0
        self.cached_fuel, self.cached_flow, self.fin_reserve = 0.0, 0.0, 0.0

        self.dest_metar, self.dest_notams, self.origin_notams = "NO DATA", [], []
        self.origin_info, self.dest_info = {}, {}
        
        self.perf_impacts = {}
        self.weights = {}
        self.fuel_plan = {}
        self.time_plan = {}
        self.crz_data = {}

        self.origin_trans_alt, self.dest_trans_level = 18000, 18000
        self.cruise_alt = 0

    def _fmt_ete(self, seconds):
        if seconds < 0: return "00:00"
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        if h > 99: return "99:59"
        return f"{h:02d}:{m:02d}"  

    def fetch_simbrief(self, force_download=False):
        t = threading.Thread(target=self._fetch_logic, args=(force_download,))
        t.daemon = True; t.start()

    def _fetch_logic(self, force_download):
        with self.lock: self.status_msg = "LOADING..."
        data = None
        if (not force_download) and os.path.exists(LOCAL_FILE_PATH):
            try:
                with open(LOCAL_FILE_PATH, 'r', encoding='utf-8') as f: data = json.load(f)
            except: pass
        if data is None:
            try:
                r = requests.get(f"{SIMBRIEF_API_URL}?username={SIMBRIEF_USERNAME}&json=1", timeout=15)
                if r.status_code == 200:
                    data = r.json()
                    with open(LOCAL_FILE_PATH, 'w', encoding='utf-8') as f: json.dump(data, f, indent=4)
                else: 
                    with self.lock: self.status_msg = f"HTTP {r.status_code}"; return
            except: 
                with self.lock: self.status_msg = "NET ERROR"; return
        if data: self._parse_ofp(data)

    def _parse_ofp(self, data):
        with self.lock:
            self.legs = []
            self.origin = data.get('origin', {}).get('icao_code', '----')
            self.dest = data.get('destination', {}).get('icao_code', '----')
            self.cruise_alt = safe_int(data.get('general', {}).get('initial_altitude', 0))
            
            times_data = data.get('times', {})
            try:
                self.std_unix = int(times_data.get('sched_out', 0))
                if self.std_unix > 0:
                    import time
                    time_struct = time.gmtime(self.std_unix)
                    self.tobt_str = time.strftime("%H:%MZ", time_struct)
                else:
                    self.tobt_str = "--:--Z"
            except (ValueError, TypeError, ImportError):
                self.tobt_str = "--:--Z"

            navlog_raw = data.get('navlog', {}).get('fix', [])
            
            orig_data = data.get('origin', {})
            mora_val = safe_int(navlog_raw[0].get('mora', 0)) if navlog_raw else 0

            atis_data = orig_data.get('atis') or {} 
            self.origin_info = {
                'elev': safe_int(orig_data.get('elevation', 0)),
                'mora': mora_val * 100 if mora_val < 300 else mora_val, 
                'rwy': orig_data.get('plan_rwy', '--'),
                'atis': atis_data.get('message', 'NO ATIS DATA').replace('\n', ' ') if isinstance(atis_data, dict) else "N/A",
                'atis_letter': atis_data.get('letter', 'N/A') if isinstance(atis_data, dict) else "-",
                'trans_alt': safe_int(orig_data.get('trans_alt', 18000))
            }
            self.origin_elev = self.origin_info['elev']
            self.origin_trans_alt = self.origin_info['trans_alt']

            dest_data = data.get('destination', {})
            self.dest_info = {
                'elev': safe_int(dest_data.get('elevation', 0)),
                'mora': safe_int(navlog_raw[-1].get('mora', 0)) if navlog_raw else 0,
                'rwy': dest_data.get('plan_rwy', '--'),
                'metar': data.get('weather', {}).get('dest_metar', 'N/A'),
                'trans_level': safe_int(dest_data.get('trans_level', 18000))
            }
            self.dest_elev = self.dest_info['elev']
            self.dest_metar = self.dest_info['metar']
            self.dest_trans_level = self.dest_info['trans_level']

            
            def parse_safe_notams(raw_input):
                if isinstance(raw_input, dict):
                    raw_input = [raw_input]
                
                if not raw_input: 
                    return []
                
                cleaned = []
                if not isinstance(raw_input, list):
                    raw_input = [raw_input]

                for n in raw_input:
                    if isinstance(n, dict):
                        nid = n.get('notam_id', '??')
                        text = n.get('notam_text', '')
                        cleaned.append(f"{nid}: {text}".replace('\n', ' '))
                    elif isinstance(n, str):
                        cleaned.append(n.replace('\n', ' '))
                    else:
                        cleaned.append(str(n))
                return cleaned

            self.origin_notams = parse_safe_notams(orig_data.get('notam', []))
            self.dest_notams = parse_safe_notams(dest_data.get('notam', []))

            w = data.get('weights', {})
            f = data.get('fuel', {})
            self.weights = {
                'tow': safe_int(w.get('est_tow')), 
                'zfw': safe_int(w.get('est_zfw')), 
                'payload': safe_int(w.get('payload')), 
                'pax': safe_int(w.get('pax_count')),
                'cargo': safe_int(w.get('cargo', 0)), 
                'block_fuel': safe_int(f.get('plan_ramp', 0))
            }
            
            gen = data.get('general', {})
            self.crz_data = {
                'init_alt': safe_int(gen.get('initial_altitude', 0)), 
                'avg_wind_dir': gen.get('avg_wind_dir', '000'),
                'avg_wind_spd': gen.get('avg_wind_spd', '00'),
                'avg_isa': gen.get('avg_temp_dev', '0')
            }

            self.perf_impacts = data.get('impacts', {})

            self.fuel_plan = {
                'taxi': safe_int(f.get('taxi', 0)),
                'reserve': safe_int(f.get('reserve', 0)),
                'plan_ldg': safe_int(f.get('plan_landing', 0))
            }
            self.fin_reserve = safe_float(f.get('reserve', 0))

            total_d, prev_leg = 0.0, None
            for f_node in navlog_raw:
                leg = FlightLeg(f_node)
                if prev_leg:
                    leg.leg_course = int(calculate_bearing(prev_leg.lat, prev_leg.lon, leg.lat, leg.lon))
                    leg.leg_dist_static = haversine_nm(prev_leg.lat, prev_leg.lon, leg.lat, leg.lon)
                    total_d += leg.leg_dist_static
                self.legs.append(leg); prev_leg = leg
            
            self.total_dist_static = total_d
            self.is_loaded = True; self.status_msg = "LOADED"
            self.position_initialized = False

    def update(self, lat, lon, alt_ft, gs_kt, fuel_kg, ff_kg_hr, baro, time_now):
        if not self.is_loaded or not self.legs: return
        with self.lock:
            self.cached_fuel, self.cached_flow = fuel_kg, ff_kg_hr
            dt = max(0.001, time_now - self.last_time)
            raw_accel = (gs_kt - self.last_gs) / dt
            self.acceleration = (self.acceleration * 0.8) + (raw_accel * 0.2)
            if abs(raw_accel) < 0.1: self.acceleration *= 0.9
            self.last_gs, self.last_time = gs_kt, time_now

            if not self.position_initialized and abs(lat) > 0.1:
                self._sync_position(lat, lon); self.last_alt = alt_ft

            self.current_gs = gs_kt
            calc_gs = max(gs_kt, MIN_GS_FOR_CALC)

            # LNAV WAYPOINT PROGRESS

            if self.active_idx < len(self.legs):
                target = self.legs[self.active_idx]
                dist = haversine_nm(lat, lon, target.lat, target.lon)
                target.dist_to_go, target.bearing = dist, int(calculate_bearing(lat, lon, target.lat, target.lon))
                if target.plan_alt > 0:
                    target.target_alt = target.plan_alt
                else: target.target_alt = self.cruise_alt if self.cruise_alt > 0 else self.dest_elev

                # A. NORMAL
                if dist < 2.0 and self.active_idx < len(self.legs) - 1:
                    self.active_idx += 1
                # B. OVERFLY
                elif self.active_idx < len(self.legs) - 1:
                    next_wpt = self.legs[self.active_idx + 1]
                    d_next = haversine_nm(lat, lon, next_wpt.lat, next_wpt.lon)
                    if d_next < dist and dist > 5.0 and d_next < 20.0:
                         print(f"[FMS] Auto-Sequence: Passed {target.ident} (Overshoot protection)")
                         self.active_idx += 1

            # CALCULATE ETE

            cum_time = 0.0
            cum_dist = 0.0 
            
            if self.active_idx < len(self.legs):
                act = self.legs[self.active_idx]
                cum_dist = act.dist_to_go 
                dt_leg = (act.dist_to_go / calc_gs) * 3600.0
                cum_time = dt_leg
                act.eta_str = self._fmt_ete(cum_time)
                
                for i in range(self.active_idx + 1, len(self.legs)):
                    leg = self.legs[i]
                    cum_dist += leg.leg_dist_static
                    l_dt = (leg.leg_dist_static / calc_gs) * 3600.0
                    cum_time += l_dt
                    leg.eta_str = self._fmt_ete(cum_time)
                    leg.dist_to_go = leg.leg_dist_static 
            
            self.dist_to_dest = cum_dist
            self.time_to_dest = cum_time 
            
            if ff_kg_hr > 100: 
                self.fuel_pred_dest = fuel_kg - ((self.time_to_dest / 3600.0) * ff_kg_hr)
            else: 
                self.fuel_pred_dest = fuel_kg
            
            if self.total_dist_static > 0: 
                self.progress_pct = max(0.0, min(100.0, (1.0 - cum_dist/self.total_dist_static)*100.0))


            # CALCULATE TD
            
            height_to_lose = max(0, self.cruise_alt - self.dest_elev)
            needed_descent_nm = height_to_lose / 318.0
            
            self.dist_to_td = self.dist_to_dest - needed_descent_nm

            agl = alt_ft - self.origin_elev
            if agl < 1500 and gs_kt < 60: self.phase = "GND"
            elif agl < 3000 and gs_kt >= 60 and (self.active_idx <= 2): self.phase = "TO/CLB"
            else:
                if self.dist_to_td < 0 or self.dist_to_dest < 50: 
                    self.phase = "DES"; self.crz_warn = ""
                elif abs(alt_ft - self.cruise_alt) < 2000: 
                    self.phase = "CRZ"
                    if abs(alt_ft - self.cruise_alt) > 300:
                         fl_curr = int(alt_ft / 100)
                         self.crz_warn = f"CHK FL{fl_curr}"
                    else: self.crz_warn = ""
                else: self.phase = "CLB"; self.crz_warn = ""

            if not self.baro_alert:
                if self.last_alt <= self.origin_trans_alt < alt_ft: self.baro_alert, self.baro_alert_start_time = "SET STD", time_now
                elif self.last_alt >= self.dest_trans_level > alt_ft: self.baro_alert, self.baro_alert_start_time = "SET QNH", time_now
            elif time_now - self.baro_alert_start_time > BARO_ALERT_CLEAR_SEC: self.baro_alert = ""
            self.last_alt = alt_ft

            #  VNAV CALCULATION

            if self.active_idx < len(self.legs):
                act_leg = self.legs[self.active_idx]
                
                # --- CLB ---
                if self.phase == "TO/CLB" or self.phase == "CLB":
                    if act_leg.plan_alt > 100:
                        target_alt_val = act_leg.plan_alt
                    else:
                        target_alt_val = self.cruise_alt
                    
                    act_leg.target_alt = target_alt_val
                    
                    dist_to_calc = act_leg.dist_to_go
                    self.vnav_deviation = 0.0 
                    
                    if dist_to_calc > 0.5 and gs_kt > 50:
                        time_to_target = (dist_to_calc / calc_gs) * 60.0
                        height_diff = target_alt_val - alt_ft
                        # IF CLIMB FASTER THAN PLANNED
                        act_leg.target_vs_fpm = int(height_diff / time_to_target) if height_diff > 0 else 0
                    else: 
                        act_leg.target_vs_fpm = 0

                # --- DES ---
                elif self.phase == "DES":
                    # DEFAULT TO DEST ELEV
                    target_alt_val = self.dest_elev 
                    
                    dist_to_calc = act_leg.dist_to_go
                    
                    for i in range(self.active_idx, len(self.legs)):
                        leg = self.legs[i]
                        
                        if (self.cruise_alt - leg.plan_alt > 500) and (leg.plan_alt > self.dest_elev + 100):
                            target_alt_val = leg.plan_alt
                            break

                        if i + 1 < len(self.legs):
                            dist_to_calc += self.legs[i+1].leg_dist_static
                    
                    act_leg.target_alt = target_alt_val
                    
                    # --- VDEV and VS TGT ---
                    ideal_alt = target_alt_val + (dist_to_calc * 318.0)
                    self.vnav_deviation = alt_ft - ideal_alt
                    
                    if dist_to_calc > 0.5 and gs_kt > 50:
                        time_to_target = (dist_to_calc / calc_gs) * 60.0
                        height_diff = target_alt_val - alt_ft
                        req_vs = int(height_diff / time_to_target)
                        act_leg.target_vs_fpm = max(min(req_vs, 0), -4000)
                    else: 
                        act_leg.target_vs_fpm = 0

    def _sync_position(self, lat, lon):
        if not self.legs: return
        
        # FIND NEAREST WPT TO RESUME
        best_idx = min(range(len(self.legs)), key=lambda i: haversine_nm(lat, lon, self.legs[i].lat, self.legs[i].lon))
        
        last_leg_idx = len(self.legs) - 1

        if best_idx == 0:
             self.active_idx = 0
             self.position_initialized = True
             return

        if best_idx == last_leg_idx:
             self.active_idx = last_leg_idx
             self.position_initialized = True
             return

        curr = self.legs[best_idx]
        next_pt = self.legs[best_idx + 1]

        dist_curr = haversine_nm(lat, lon, curr.lat, curr.lon)
        dist_next = haversine_nm(lat, lon, next_pt.lat, next_pt.lon)

        course_leg = calculate_bearing(curr.lat, curr.lon, next_pt.lat, next_pt.lon)
        bearing_to_plane = calculate_bearing(curr.lat, curr.lon, lat, lon)
        diff = abs(course_leg - bearing_to_plane)
        if diff > 180: diff = 360 - diff

        should_advance = False
        
        if diff < 90:
            
            if dist_curr < 5.0:
                should_advance = True
                
            else:
                should_advance = True
                
            if dist_next < dist_curr:
                should_advance = True

        if should_advance:
             best_idx += 1
             print(f"[FMS] RESUME: Passed WPT (Dist {dist_curr:.1f}), advancing to next.")
        
        self.active_idx = best_idx
        self.position_initialized = True

    def _fmt_time(self, ts):
        return time.strftime("%H:%M", time.localtime(ts))

    def set_direct_to(self, leg_index):
        with self.lock:
            if 0 <= leg_index < len(self.legs): self.active_idx = leg_index

    def modify_leg_constraint(self, leg_index, spd=None, alt=None, is_mach=False, is_metric=False):
        with self.lock:
            if 0 <= leg_index < len(self.legs):
                leg = self.legs[leg_index]
                if spd is not None:
                    leg.plan_mach = spd if is_mach else 0.0
                    leg.plan_spd_kmh = spd * 1225 if is_mach else spd
                if alt is not None: leg.plan_alt = alt / 0.3048 if is_metric else alt