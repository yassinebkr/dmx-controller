import board
import busio
import digitalio
import analogio
import rotaryio
import time
import struct

# OLED
import adafruit_ssd1306

# ============================================================
# CONFIGURATION HARDWARE
# ============================================================

# Joystick (3 axes analogiques)
JOY_X = analogio.AnalogIn(board.A0)   # Pan (gauche/droite)
JOY_Y = analogio.AnalogIn(board.A1)   # Tilt (haut/bas)
JOY_Z = analogio.AnalogIn(board.A2)   # Speed (rotation)

# Boutons (resistor ladder sur A3)
BUTTONS = analogio.AnalogIn(board.A3)

# Encodeur rotatif
ENCODER = rotaryio.IncrementalEncoder(board.D8, board.D9)  # A, B
ENC_BTN = digitalio.DigitalInOut(board.D10)
ENC_BTN.direction = digitalio.Direction.INPUT
ENC_BTN.pull = digitalio.Pull.UP

# XBee UART
XBEE_UART = busio.UART(board.D6, board.D7, baudrate=9600)  # TX, RX

# OLED I2C
i2c = busio.I2C(board.D5, board.D4)  # SCL, SDA
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)

# ============================================================
# CALIBRATION JOYSTICK (valeurs mesurées sur ton matériel)
# ============================================================

CAL_X = (489, 31979, 63522)    # (min, centre, max)
CAL_Y = (384, 31492, 63666)    # (min, centre, max)
CAL_Z = (438, 3490, 36000)     # (min, centre, max)

DEADZONE = 0.08  # 8% de deadzone au centre

# ============================================================
# SEUILS BOUTONS (ADC 16-bit)
# À ajuster selon tes résistances réelles
# ============================================================

BUTTON_THRESHOLDS = [
    (0, 1000),      # B1 - 0Ω (court-circuit)
    (5800, 7200),   # B2 - 220Ω
    (13000, 16000), # B3 - 560Ω
    (20000, 24000), # B4 - 1kΩ
    (26000, 30000), # B5 - 1.5kΩ
    (33000, 37000), # B6 - 2.2kΩ (ou 2.7kΩ)
    (38000, 42000), # B7 - 3.9kΩ
    (43000, 48000), # B8 - 4.7kΩ (ou 6.8kΩ)
]

# ============================================================
# TABLES DE VALEURS DMX
# ============================================================

# Couleurs (valeurs de début de plage)
COLORS = [0, 8, 16, 24, 32, 40, 48, 56, 64, 72, 80, 88]
COLOR_NAMES = ["White", "Turq", "Red", "Cyan", "LGrn", "Mgnt", "LBlu", "Yell", "Green", "Pink", "Blue", "Orng"]

# Gobos
GOBOS = [0, 8, 16, 24, 32, 40, 48, 56, 64, 72, 80, 88]

# Shutter states
SHUTTER_STATES = [0, 64, 96, 128, 160, 176, 192, 224, 255]
SHUTTER_NAMES = ["Closed", "Open", "Strobe", "Reset", "Pulse+", "Pulse-", "Random", "Open2", "Open3"]

# ============================================================
# VARIABLES GLOBALES
# ============================================================

# Valeurs DMX courantes
dmx_pan = 128
dmx_tilt = 128
dmx_pan_fine = 128
dmx_tilt_fine = 128
dmx_speed = 0      # 0 = vitesse max (tracking)
dmx_color = 0      # White
dmx_gobo = 0       # Open
dmx_shutter = 64   # Open

# Encodeur
encoder_last = ENCODER.position
color_index = 0
shutter_index = 1  # Start at "Open"

# Boutons (avec anti-rebond)
button_pressed = [False] * 8
button_last = [False] * 8

# Séquence
tx_sequence = 0

# Timing
last_tx_time = 0
last_activity_time = 0
HEARTBEAT_INTERVAL = 0.5  # 500ms
TX_INTERVAL = 0.05        # 50ms (20Hz)

# État
last_packet = [128, 128, 128, 128, 0, 0, 0, 64]
values_changed = True

# ============================================================
# FONCTIONS UTILITAIRES
# ============================================================


def map_value(value, in_min, in_max, out_min, out_max):
    """Map une valeur d'une plage à une autre."""
    if value < in_min:
        value = in_min
    if value > in_max:
        value = in_max
    return int((value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)


def apply_deadzone(raw, cal, deadzone=0.08):
    """
    Applique une deadzone au centre du joystick.
    
    raw : valeur ADC brute (0-65535)
    cal : tuple (min, centre, max)
    deadzone : pourcentage de deadzone (0.08 = 8%)
    
    Retourne une valeur -1.0 à +1.0, avec 0.0 dans la deadzone.
    """
    min_val, center, max_val = cal
    
    # Plage totale
    range_total = max_val - min_val
    
    # Taille de la deadzone en counts ADC
    deadzone_counts = int(range_total * deadzone / 2)
    
    # Distance depuis le centre
    if raw > center:
        # Au-dessus du centre
        dist = raw - center
        if dist < deadzone_counts:
            return 0.0
        # Map deadzone..max → 0.0..1.0
        active_range = max_val - (center + deadzone_counts)
        if active_range <= 0:
            return 0.0
        return min(1.0, dist / active_range)
    else:
        # En-dessous du centre
        dist = center - raw
        if dist < deadzone_counts:
            return 0.0
        active_range = (center - deadzone_counts) - min_val
        if active_range <= 0:
            return 0.0
        return max(-1.0, -dist / active_range)


def read_joystick():
    """
    Lit le joystick et retourne les valeurs mappées.
    
    Mode VITESSE (velocity) :
    - Centre = arrêt (valeur 128 = neutre)
    - Déflection = direction + vitesse
    - Z = multiplicateur de vitesse
    
    Retourne : (pan, tilt, pan_fine, tilt_fine, speed)
    """
    # Lire les valeurs brutes
    raw_x = JOY_X.value
    raw_y = JOY_Y.value
    raw_z = JOY_Z.value
    
    # Appliquer deadzone et mapper vers -1.0..+1.0
    norm_x = apply_deadzone(raw_x, CAL_X)
    norm_y = apply_deadzone(raw_y, CAL_Y)
    norm_z = apply_deadzone(raw_z, CAL_Z)
    
    # Mode VITESSE :
    # - Déflection joystick = vitesse de mouvement
    # - 128 = arrêt (neutre)
    # - 0 = vitesse max vers la gauche/haut
    # - 255 = vitesse max vers la droite/bas
    
    # Pan (X) : gauche = 0, centre = 128, droite = 255
    pan = int(128 + norm_x * 127)
    pan = max(0, min(255, pan))
    
    # Tilt (Y) : haut = 0, centre = 128, bas = 255
    tilt = int(128 + norm_y * 127)
    tilt = max(0, min(255, tilt))
    
    # Fine : même direction mais amplitude réduite (±32 au lieu de ±127)
    pan_fine = int(128 + norm_x * 32)
    pan_fine = max(0, min(255, pan_fine))
    
    tilt_fine = int(128 + norm_y * 32)
    tilt_fine = max(0, min(255, tilt_fine))
    
    # Speed (Z) : rotation du joystick
    # CW = augmenter vitesse (0 = max), CCW = diminuer (249 = min)
    # On map -1..+1 → 249..0 (inversé : plus c'est bas, plus c'est rapide)
    speed = int(124 - norm_z * 124)  # Centre = 124, max CW = 0, max CCW = 249
    speed = max(0, min(249, speed))
    
    return pan, tilt, pan_fine, tilt_fine, speed


def read_buttons():
    """
    Lit les boutons via le resistor ladder.
    
    Retourne une liste de 8 booléens (True = pressé).
    """
    raw = BUTTONS.value
    pressed = []
    
    for low, high in BUTTON_THRESHOLDS:
        pressed.append(low <= raw <= high)
    
    return pressed


def read_encoder():
    """
    Lit l'encodeur rotatif et le bouton poussoir.
    
    Retourne : (delta_position, button_pressed)
    - delta_position : nombre de crans depuis le dernier appel
    - button_pressed : True si le bouton est enfoncé
    """
    global encoder_last
    
    current = ENCODER.position
    delta = current - encoder_last
    encoder_last = current
    
    btn = not ENC_BTN.value  # Pull-up : LOW = pressé
    
    return delta, btn


def build_packet(pan, tilt, pan_fine, tilt_fine, speed, color, gobo, shutter, sequence):
    """
    Construit le paquet de 10 octets.
    
    Format :
    [0] Pan, [1] Tilt, [2] Pan Fine, [3] Tilt Fine,
    [4] Speed, [5] Color, [6] Gobo, [7] Shutter,
    [8] Sequence, [9] Checksum (XOR de 0-8)
    """
    data = bytearray(10)
    data[0] = pan
    data[1] = tilt
    data[2] = pan_fine
    data[3] = tilt_fine
    data[4] = speed
    data[5] = color
    data[6] = gobo
    data[7] = shutter
    data[8] = sequence & 0xFF  # Wrap around 0-255
    
    # Calculer le checksum (XOR des octets 0-8)
    checksum = 0
    for i in range(9):
        checksum ^= data[i]
    data[9] = checksum
    
    return data


def send_packet(packet):
    """Envoie le paquet sur l'UART XBee."""
    XBEE_UART.write(packet)


def update_oled(pan, tilt, speed, color, gobo, shutter, seq):
    """Met à jour l'affichage OLED."""
    oled.fill(0)
    
    # Ligne 1 : Pan / Tilt
    oled.text(f"P:{pan:3d} T:{tilt:3d}", 0, 0, 1)
    
    # Ligne 2 : Speed / Color
    color_name = COLOR_NAMES[min(color_index, len(COLOR_NAMES)-1)]
    oled.text(f"S:{speed:3d} C:{color_name}", 0, 10, 1)
    
    # Ligne 3 : Gobo / Shutter
    shutter_name = SHUTTER_NAMES[min(shutter_index, len(SHUTTER_NAMES)-1)]
    oled.text(f"G:{gobo:3d} {shutter_name}", 0, 20, 1)
    
    # Ligne 4 : Séquence / Status
    oled.text(f"Seq:{seq:3d} TX", 0, 30, 1)
    
    # Barre de signal (mini)
    bar_width = min(128, seq * 2)
    oled.fill_rect(0, 40, bar_width, 8, 1)
    
    oled.show()


# ============================================================
# BOUCLE PRINCIPALE
# ============================================================


def main():
    global tx_sequence, color_index, shutter_index
    global dmx_pan, dmx_tilt, dmx_pan_fine, dmx_tilt_fine
    global dmx_speed, dmx_color, dmx_gobo, dmx_shutter
    global values_changed, last_packet, last_tx_time, last_activity_time
    
    print("DMX Controller démarré")
    print("Mode : VELOCITY (vitesse variable)")
    
    # Écran de démarrage
    oled.fill(0)
    oled.text("DMX Controller", 0, 0, 1)
    oled.text("Mode: VELOCITY", 0, 10, 1)
    oled.text("Attente XBee...", 0, 30, 1)
    oled.show()
    
    time.sleep(1)
    
    while True:
        now = time.monotonic()
        
        # --- LIRE LES ENTRÉES ---
        
        # Joystick
        pan, tilt, pan_fine, tilt_fine, speed = read_joystick()
        
        # Encoder
        enc_delta, enc_btn = read_encoder()
        
        # Boutons
        buttons = read_buttons()
        
        # --- TRAITER LES ENTRÉES ---
        
        # Encoder : rotation = changement de couleur
        if enc_delta != 0:
            color_index = (color_index + enc_delta) % len(COLORS)
            dmx_color = COLORS[color_index]
            values_changed = True
            last_activity_time = now
        
        # Encoder bouton : cycle shutter
        if enc_btn and not button_last[0]:  # Front montant
            shutter_index = (shutter_index + 1) % len(SHUTTER_STATES)
            dmx_shutter = SHUTTER_STATES[shutter_index]
            values_changed = True
            last_activity_time = now
        
        # Boutons : presets
        for i in range(8):
            if buttons[i] and not button_last[i]:  # Front montant
                if i == 0:
                    dmx_color = 0  # White
                    color_index = 0
                elif i == 1:
                    dmx_color = 16  # Red
                    color_index = 2
                elif i == 2:
                    dmx_color = 80  # Blue
                    color_index = 10
                elif i == 3:
                    dmx_color = 64  # Green
                    color_index = 8
                elif i == 4:
                    dmx_gobo = 0  # Open
                elif i == 5:
                    dmx_gobo = 228  # Rotate
                elif i == 6:
                    dmx_shutter = 64  # Open
                    shutter_index = 1
                elif i == 7:
                    dmx_shutter = 96  # Strobe
                    shutter_index = 2
                
                values_changed = True
                last_activity_time = now
        
        button_last = buttons[:]
        
        # Joystick : toujours mettre à jour (même au centre = 128)
        # Mais on ne considère "changed" que si ça diffère du dernier envoi
        current_values = [pan, tilt, pan_fine, tilt_fine, speed, dmx_color, dmx_gobo, dmx_shutter]
        if current_values != last_packet:
            values_changed = True
            last_activity_time = now
        
        # Mettre à jour les valeurs DMX courantes
        dmx_pan = pan
        dmx_tilt = tilt
        dmx_pan_fine = pan_fine
        dmx_tilt_fine = tilt_fine
        dmx_speed = speed
        
        # --- ENVOYER SI NÉCESSAIRE ---
        
        # Conditions d'envoi :
        # 1. Valeurs changées ET intervalle TX écoulé (20Hz max)
        # 2. OU heartbeat (500ms) si idle
        
        should_send = False
        
        if values_changed and (now - last_tx_time) >= TX_INTERVAL:
            should_send = True
        elif (now - last_activity_time) >= HEARTBEAT_INTERVAL and (now - last_tx_time) >= HEARTBEAT_INTERVAL:
            should_send = True  # Heartbeat
        
        if should_send:
            # Construire et envoyer le paquet
            packet = build_packet(
                dmx_pan, dmx_tilt, dmx_pan_fine, dmx_tilt_fine,
                dmx_speed, dmx_color, dmx_gobo, dmx_shutter,
                tx_sequence
            )
            send_packet(packet)
            
            # Mettre à jour l'état
            tx_sequence = (tx_sequence + 1) & 0xFF
            last_packet = [dmx_pan, dmx_tilt, dmx_pan_fine, dmx_tilt_fine,
                        dmx_speed, dmx_color, dmx_gobo, dmx_shutter]
            values_changed = False
            last_tx_time = now
            
            # Debug
            print(f"TX: {list(packet)}")
            
            # Mettre à jour l'affichage
            update_oled(dmx_pan, dmx_tilt, dmx_speed, dmx_color, dmx_gobo, dmx_shutter, tx_sequence)
        
        # Petite pause pour ne pas surcharger le CPU
        time.sleep(0.001)  # 1ms


# ============================================================
# DÉMARRAGE
# ============================================================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Arrêt par l'utilisateur")
    except Exception as e:
        print(f"Erreur: {e}")
        raise
