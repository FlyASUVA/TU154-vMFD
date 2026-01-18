import socket
import struct
import threading
import time
from config import *

class DataLink(threading.Thread):
    def __init__(self):
        super().__init__()
        self.running = True
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((UDP_IP, UDP_PORT))
        self.sock.setblocking(False)
        self.raw_rows = {}
        
        # --- STARTER VALUE ---
        self._last_starter_val = [0.0, 0.0, 0.0]
        self._starter_active_ts = [0.0, 0.0, 0.0] 
        
        self.data = {
            'connected': False,
            # BASIC DATA
            'lat': 0.0, 'lon': 0.0, 'alt_msl_ft': 0.0,
            'ias_kt': 0.0, 'gs_kt': 0.0, 'tas_kt': 0.0,
            'pitch': 0.0, 'roll': 0.0, 'hdg': 0.0,
            'vvi': 0.0,  
            # ENG
            'n1': [0.0, 0.0, 0.0], 
            'n2': [0.0, 0.0, 0.0], 
            'egt': [0.0, 0.0, 0.0],
            'ff': [0.0, 0.0, 0.0],
            'total_ff_kg_hr': 0.0, 
            'oil_p': [0.0, 0.0, 0.0],
            'reverse_state': [0.0, 0.0, 0.0],
            'starter_time': [0.0, 0.0, 0.0],
            'starter_active': [False, False, False],

            # BALANCE
            'cg_raw': 0.0,      
            'cg_mac': 0.0,      
            'elev_pos': 0.0,    
            'stab_pos': 0.0,    

            # CONFIG
            'gear_pos': 0.0,    
            'park_brake': 0.0,  
            'flaps': 0.0,       
            'slats': 0.0,       
            'sbrk': 0.0,        
            'trim': 0.0,        
            'fuel_weight': 0.0, # EICAS FOB
            'total_fuel_kg': 0.0, # FMS CALCULATION
            'total_weight': 0.0,
            
            # WIND DATA
            'wind_spd': 0.0,
            'wind_dir': 0.0
        }

    def run(self):
        print("DataLink: LISTENING TO PORT (49000 (linux) /49071 (win))...")
        last_time = time.time()

        while self.running:
            try:
                packet, _ = self.sock.recvfrom(2048)
                if packet[0:4] != b'DATA': continue
                
                now = time.time()
                last_time = now
                self.data['connected'] = True
                
                body = packet[5:]
                num_rows = len(body) // 36
                
                for i in range(num_rows):
                    row = body[i*36 : (i+1)*36]
                    vals = struct.unpack('<iffffffff', row)
                    idx = int(vals[0])
                    self.raw_rows[idx] = [vals[1], vals[2], vals[3], vals[4], vals[5], vals[6], vals[7], vals[8]]
                    
                    if idx == 41: self.data['n1'] = [vals[1], vals[2], vals[3]]
                    elif idx == 42: self.data['n2'] = [vals[1], vals[2], vals[3]]
                    
                    elif idx == 45: 
                        CONVERSION_FACTOR = 3.02 
                        ff_list = [
                            vals[1] * CONVERSION_FACTOR,
                            vals[2] * CONVERSION_FACTOR,
                            vals[3] * CONVERSION_FACTOR
                        ]
                        self.data['ff'] = ff_list
                        self.data['total_ff_kg_hr'] = sum(ff_list)
                        
                    elif idx == 47: self.data['egt'] = [vals[1], vals[2], vals[3]]
                    elif idx == 49: self.data['oil_p'] = [vals[1], vals[2], vals[3]]
                    elif idx == 27: self.data['reverse_state'] = [vals[1], vals[2], vals[3]]
                    
                    elif idx == 33: 
                        # --- DETECT ENGINE START ---
                        current_vals = [vals[1], vals[2], vals[3]]
                        self.data['starter_time'] = current_vals
                        for eng_i in range(3):
                            if current_vals[eng_i] > self._last_starter_val[eng_i]:
                                self._starter_active_ts[eng_i] = now
                            self._last_starter_val[eng_i] = current_vals[eng_i]
                            self.data['starter_active'][eng_i] = (now - self._starter_active_ts[eng_i] < 0.25)
                    
                    elif idx == 14: 
                        self.data['gear_pos'] = vals[1]   
                        self.data['park_brake'] = vals[2] 
                    elif idx == 13: 
                        self.data['stab_raw'] = vals[1] 
                        self.data['stab_pos'] = vals[1] * 5.488 
                        self.data['flaps'] = vals[4] 
                        self.data['slats'] = vals[6] 
                        self.data['sbrk'] = vals[7]  
                    elif idx == 74: self.data['elev_pos'] = vals[1] 
                    elif idx == 63: 
                        self.data['fuel_weight'] = vals[3] * 0.453592
                        self.data['total_fuel_kg'] = self.data['fuel_weight']
                        
                        self.data['total_weight'] = vals[6] * 0.453592
                        self.data['cg_raw'] = vals[8]
                        self.data['cg_mac'] = self.data['cg_raw'] * CG_SLOPE + CG_INTERCEPT
                        
                    elif idx == 3: 
                        self.data['ias_kt'] = vals[1]
                        self.data['tas_kt'] = vals[3]  
                        self.data['gs_kt']  = vals[4] 

                    elif idx == 4: 
                        self.data['vvi'] = vals[3]

                    elif idx == 152: # Wind
                        self.data['wind_spd'] = vals[6]
                        self.data['wind_dir'] = vals[7]
                        
                    elif idx == 20: # Lat, Lon, Alt
                        self.data['lat'] = vals[1]    
                        self.data['lon'] = vals[2]    
                        self.data['alt_msl_ft'] = vals[6] 
                        
                    elif idx == 17: # Pitch, Roll, Heading
                        self.data['pitch'] = vals[1]
                        self.data['roll'] = vals[2]
                        self.data['hdg'] = vals[5]    

            except BlockingIOError:
                time.sleep(0.02)
            
            if time.time() - last_time > 1.0:
                self.data['connected'] = False
        
    def get_row(self, row_idx):
        return self.raw_rows.get(row_idx, [0.0] * 8)
        
    def stop(self):
        self.running = False
        self.sock.close()