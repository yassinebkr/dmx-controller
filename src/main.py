import board
import busio
import digitalio
import analogio
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

# Encodeur rotatif -- polling logiciel 1x sur front montant de A.
# rotaryio impossible : D8/D9 = GPIO2/GPIO4 ne sont pas consécutifs.
ENC_A = digitalio.DigitalInOut(board.D9)
ENC_A.direction = digitalio.Direction.INPUT
ENC_A.pull = digitalio.Pull.UP

ENC_B = digitalio.DigitalInOut(board.D8)
ENC_B.direction = digitalio.Direction.INPUT
ENC_B.pull = digitalio.Pull.UP

ENC_BTN = digitalio.DigitalInOut(board.D10)
ENC_BTN.direction = digitalio.Direction.INPUT
ENC_BTN.pull = digitalio.Pull.UP

# XBee UART
XBEE_UART = busio.UART(board.D6, board.D7, baudrate=9600)  # TX, RX

# OLED I2C
i2c = busio.I2C(board.D5, board.D4, frequency=1_000_000)  # SCL, SDA
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)

# Police 5x8 chargée depuis le système de fichiers. Chaque caractère est
# 5 octets, chaque octet = une colonne verticale de 8 pixels (bit 0 = haut).
# Ce layout correspond EXACTEMENT au format des pages SSD1306, ce qui permet
# d'écrire le texte par copie d'octets directe (fast_text) plutôt que via
# oled.text() qui appelle oled.pixel() pour chaque pixel allumé.
try:
    with open("font5x8.bin", "rb") as f:
        _raw_font = f.read()
    # Certains fichiers ont un header 2 octets (taille 1282 au lieu de 1280)
    FONT = _raw_font[2:] if len(_raw_font) == 1282 else _raw_font
except OSError:
    print("ERREUR: font5x8.bin introuvable à la racine de CIRCUITPY")
    raise SystemExit

# Accès direct au framebuffer (1024 octets, organisé en 8 pages de 128 octets)
buf = oled.buf

# État de "salissure" des pages -- envoyé seulement les pages modifiées via I2C.
# dirty_min > dirty_max signifie "rien à envoyer".
dirty_min = 8
dirty_max = -1

# Dernière valeur affichée pour chaque champ. None force le rendu initial.
shown_pan = None
shown_tilt = None
shown_speed = None
shown_color = None
shown_gobo = None
shown_shutter = None
shown_seq = None

# ============================================================
# CALIBRATION JOYSTICK (valeurs mesurées sur ton matériel)
# ============================================================

CAL_X = (489, 31979, 63522)    # (min, centre, max)
CAL_Y = (384, 31492, 63666)    # (min, centre, max)
CAL_Z = (438, 3490, 36000)     # (min, centre, max)

DEADZONE = 0.08  # 8% de deadzone au centre

# ============================================================
# SEUILS BOUTONS (ADC 16-bit, 2.2k pull-up)
# Valeurs calculées : gap minimum = 5,957 counts
# ============================================================

BUTTON_THRESHOLDS = [
    (0,      2978),   # B1 - 0Ω
    (2979,   9626),   # B2 - 220Ω
    (9627,  16887),   # B3 - 560Ω
    (16888, 23523),   # B4 - 1kΩ
    (23524, 31339),   # B5 - 1.5kΩ
    (31340, 39005),   # B6 - 2.7kΩ
    (39006, 45707),   # B7 - 3.9kΩ
    (45708, 57525),   # B8 - 6.8kΩ
]

NO_PRESS_THRESHOLD = 57525

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

# Encodeur (état pour le polling logiciel 1x)
enc_last_a = ENC_A.value
enc_btn_last = False
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
    Lit les boutons via le resistor ladder (2.2k pull-up).
    
    Retourne une liste de 8 booléens (True = pressé).
    """
    raw = BUTTONS.value
    pressed = []
    
    for low, high in BUTTON_THRESHOLDS:
        pressed.append(low <= raw <= high)
    
    return pressed


def read_encoder():
    """
    Lit l'encodeur (1x decoding sur front montant de A) et le bouton.

    Retourne : (delta, button_pressed)
    - delta : -1, 0 ou +1 (un cran = un count)
    - button_pressed : True si le bouton est enfoncé

    Cette fonction DOIT être appelée à chaque tour de boucle (~ms) :
    elle s'appuie sur un échantillonnage rapide pour ne pas rater de front.
    """
    global enc_last_a

    a = ENC_A.value
    b = ENC_B.value
    delta = 0

    # Front montant de A : direction donnée par B à cet instant
    if a and not enc_last_a:
        delta = 1 if (a == b) else -1

    enc_last_a = a
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


# ============================================================
# RENDU OLED — framebuffer direct + dirty tracking par page
# ============================================================

def _mark_dirty(start, end):
    """Étend la fenêtre de pages à renvoyer au prochain show_dirty()."""
    global dirty_min, dirty_max
    if start < dirty_min:
        dirty_min = start
    if end > dirty_max:
        dirty_max = end


def fast_text(text, x, page):
    """Écrit du texte directement dans le framebuffer (13x + rapide que oled.text).
    `page` est l'index de page (0-7) -- la coordonnée y vaut page*8.
    """
    offset = page * 128 + x
    for ch in text:
        idx = ord(ch) * 5
        if offset + 5 > len(buf):
            break
        buf[offset]     = FONT[idx]
        buf[offset + 1] = FONT[idx + 1]
        buf[offset + 2] = FONT[idx + 2]
        buf[offset + 3] = FONT[idx + 3]
        buf[offset + 4] = FONT[idx + 4]
        offset += 6  # 5px char + 1px gap
    _mark_dirty(page, page)


def clear_pages(start, end):
    """Met à zéro une plage de pages (inclus)."""
    begin = start * 128
    stop = min((end + 1) * 128, len(buf))
    for i in range(begin, stop):
        buf[i] = 0
    _mark_dirty(start, end)


def fill_page_bar(page, width):
    """Remplit horizontalement une page (8 pixels de haut) sur `width` colonnes."""
    offset = page * 128
    for i in range(width):
        buf[offset + i] = 0xFF
    for i in range(width, 128):
        buf[offset + i] = 0x00
    _mark_dirty(page, page)


def show_dirty():
    """Envoie au SSD1306 uniquement la plage de pages modifiées.

    Astuce : oled.buffer contient [0x40] + buf. Pour un envoi partiel on
    a besoin de [0x40] + pixels_des_pages_choisies. On écrit temporairement
    0x40 dans l'octet juste avant la première page à envoyer, puis on
    restaure. Le SSD1306 ne voit pas cet octet comme pixel parce que
    la fenêtre page commence à dirty_min.
    """
    global dirty_min, dirty_max
    if dirty_max < dirty_min:
        return  # rien à envoyer

    # Définir la fenêtre d'adresse : colonnes 0-127, pages dirty_min..dirty_max
    oled.write_cmd(0x21)
    oled.write_cmd(0)
    oled.write_cmd(127)
    oled.write_cmd(0x22)
    oled.write_cmd(dirty_min)
    oled.write_cmd(dirty_max)

    # Préfixe 0x40 inséré in-place, sans allocation
    prefix_idx = dirty_min * 128            # index dans oled.buffer (qui a 0x40 en [0])
    saved = oled.buffer[prefix_idx]
    oled.buffer[prefix_idx] = 0x40
    n = (dirty_max - dirty_min + 1) * 128 + 1
    with oled.i2c_device:
        oled.i2c_device.write(oled.buffer, start=prefix_idx, end=prefix_idx + n)
    oled.buffer[prefix_idx] = saved

    # Reset
    dirty_min = 8
    dirty_max = -1


def update_oled(pan, tilt, speed, color, gobo, shutter, seq):
    """Met à jour l'affichage OLED -- ne redessine que les pages dont
    le contenu a changé depuis le dernier rendu. show_dirty() envoie
    ensuite uniquement la plage de pages modifiées par I2C.
    """
    global shown_pan, shown_tilt, shown_speed, shown_color
    global shown_gobo, shown_shutter, shown_seq

    # Page 0 : Pan / Tilt
    if pan != shown_pan or tilt != shown_tilt:
        clear_pages(0, 0)
        fast_text("P:{0:3d} T:{1:3d}".format(pan, tilt), 0, 0)
        shown_pan = pan
        shown_tilt = tilt

    # Page 1 : Speed / Color
    if speed != shown_speed or color != shown_color:
        clear_pages(1, 1)
        color_name = COLOR_NAMES[min(color_index, len(COLOR_NAMES) - 1)]
        fast_text("S:{0:3d} C:{1}".format(speed, color_name), 0, 1)
        shown_speed = speed
        shown_color = color

    # Page 2 : Gobo / Shutter
    if gobo != shown_gobo or shutter != shown_shutter:
        clear_pages(2, 2)
        shutter_name = SHUTTER_NAMES[min(shutter_index, len(SHUTTER_NAMES) - 1)]
        fast_text("G:{0:3d} {1}".format(gobo, shutter_name), 0, 2)
        shown_gobo = gobo
        shown_shutter = shutter

    # Page 3 + Page 5 : Séquence + barre d'activité (changent ensemble)
    if seq != shown_seq:
        clear_pages(3, 3)
        fast_text("Seq:{0:3d} TX".format(seq), 0, 3)
        fill_page_bar(5, min(128, seq * 2))
        shown_seq = seq

    show_dirty()


# ============================================================
# BOUCLE PRINCIPALE
# ============================================================


def main():
    global tx_sequence, color_index, shutter_index
    global dmx_pan, dmx_tilt, dmx_pan_fine, dmx_tilt_fine
    global dmx_speed, dmx_color, dmx_gobo, dmx_shutter
    global values_changed, last_packet, last_tx_time, last_activity_time
    global enc_btn_last
    
    print("DMX Controller démarré")
    print("Mode : VELOCITY (vitesse variable)")
    
    # Écran de démarrage
    oled.fill(0)
    oled.text("DMX Controller", 0, 0, 1)
    oled.text("Mode: VELOCITY", 0, 10, 1)
    oled.text("Attente XBee...", 0, 30, 1)
    oled.show()

    time.sleep(1)

    # Nettoyage avant la boucle : update_oled ne touche que les pages dont
    # les valeurs ont changé, donc on doit garantir un écran vierge.
    clear_pages(0, 7)
    show_dirty()
    
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
        
        # Encoder bouton : cycle shutter (état dédié, distinct de B1)
        if enc_btn and not enc_btn_last:  # Front montant
            shutter_index = (shutter_index + 1) % len(SHUTTER_STATES)
            dmx_shutter = SHUTTER_STATES[shutter_index]
            values_changed = True
            last_activity_time = now
        enc_btn_last = enc_btn
        
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
        
        # Mutation in-place pour ne pas rebinder button_last en local
        button_last[:] = buttons
        
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
            print("TX:", list(packet))

        # --- RENDU OLED (découplé de l'envoi paquet) ---
        # Appel inconditionnel : update_oled compare les valeurs contre
        # ses snapshots internes (shown_*) et ne touche au framebuffer
        # que pour les pages dont le contenu a réellement changé.
        # show_dirty() envoie ensuite uniquement les pages modifiées.
        # Coût quand rien n'a changé : quelques comparaisons d'entiers.
        update_oled(dmx_pan, dmx_tilt, dmx_speed, dmx_color,
                    dmx_gobo, dmx_shutter, tx_sequence)

        # Petite pause pour ne pas surcharger le CPU
        time.sleep(0.001)  # 1ms


# ============================================================
# DÉMARRAGE
# ============================================================

# CircuitPython : code.py fait `import main`, donc __name__ vaut "main"
# (et non "__main__"). On lance main() directement à l'import.
try:
    main()
except KeyboardInterrupt:
    print("Arrêt par l'utilisateur")
except Exception as e:
    print(f"Erreur: {e}")
    raise
