# Protocole DMX Sans Fil — Guide pour le Récepteur

> Projet BTS SN — Lyre motorisée ClubSpot 150 CT  
> Émetteur : XIAO RP2040 + CircuitPython (Yassine)  
> Récepteur : XIAO RP2040 + MAX485 (toi)  
> Liaison : XBee S1 802.15.4, mode transparent, 9600 baud

---

## 1. Le Concept de "Variable Rate" (Vitesse Variable)

### Le Problème
Le joystick a un **rappel par ressort** : quand tu lâches, il revient au centre.  
Si on envoyait la position absolue du joystick (= "mode position"), la lyre reviendrait toujours au milieu dès que tu lâches.  
**Impossible à utiliser.**

### La Solution : Mode Vitesse (Velocity Mode)
Au lieu de dire "va à la position X", on dit "bouge à la vitesse V".

| Position Joystick | Signification | Effet sur la lyre |
|-------------------|---------------|-------------------|
| Centre (repos) | Vitesse = 0 | **Arrêt** — la lyre reste où elle est |
| Gauche | Vitesse négative | Pan vers la gauche, d'autant plus vite que tu pousses |
| Droite | Vitesse positive | Pan vers la droite, d'autant plus vite que tu pousses |
| Haut | Vitesse négative | Tilt vers le haut |
| Bas | Vitesse positive | Tilt vers le bas |

**Avantage :** Tu lâches le joystick → il revient au centre → vitesse = 0 → la lyre **s'arrête et reste en place**.

### Le Réglage de Vitesse (Axe Z)
Le joystick a une 3ème voie : la **rotation** (Z).  
Elle sert de "multiplicateur de vitesse" :
- Z au centre = vitesse normale
- Z vers la droite = vitesse max (pour les grands déplacements)
- Z vers la gauche = vitesse min (pour les réglages fins)

---

## 2. Le Format du Paquet (10 octets)

Le XBee reçoit un **paquet binaire de 10 octets** toutes les 50ms (20 fois par seconde) quand il y a du mouvement.

| Octet | Nom | Description | Valeur "neutre" |
|-------|-----|-------------|-----------------|
| 0 | Pan coarse | Position panoramique (gauche-droite) | 128 = centre/arrêt |
| 1 | Tilt coarse | Position verticale (haut-bas) | 128 = centre/arrêt |
| 2 | Pan fine | Réglage fin du panoramique | 128 = centre |
| 3 | Tilt fine | Réglage fin de la verticalité | 128 = centre |
| 4 | Speed | Vitesse de mouvement | Voir tableau ci-dessous |
| 5 | Color | Couleur / roue à couleurs | Voir tableau ci-dessous |
| 6 | Gobo | Gobo (formes projetées) | Voir tableau ci-dessous |
| 7 | Shutter | Obturateur / stroboscope | Voir tableau ci-dessous |
| 8 | Sequence | Numéro de séquence (0-255) | Incrémenté à chaque paquet |
| 9 | Checksum | XOR des octets 0 à 8 | Pour vérifier l'intégrité |

### Checksum (très important)
```
checksum = octet0 XOR octet1 XOR octet2 XOR ... XOR octet8
```
Le récepteur recalcule le XOR des 9 premiers octets et compare avec l'octet 9.  
Si différent → paquet corrompu → on l'ignore.

### Numéro de Séquence (détection de perte)
L'émetteur incrémente un compteur à chaque paquet (0, 1, 2, ..., 255, 0, 1...).  
Si le récepteur reçoit 5 puis 8, il sait que 2 paquets ont été perdus.  
**Pas critique** pour une lyre DMX (petites pertes imperceptibles).

---

## 3. Les Valeurs DMX (Tables de correspondance)

### Speed (Canal 5) — Vitesse de mouvement

| Valeur DMX | Signification |
|------------|---------------|
| 0-7 | Vitesse max (mode tracking) |
| 8-249 | Vitesse variable (proportionnelle, 8=max, 249=min) |
| 250-252 | Vitesse max + blackout sur changement couleur/gobo |
| 253-255 | Vitesse max + blackout sur mouvement/couleur/gobo |

**En pratique :** On utilise surtout 0-249. Plus la valeur est basse, plus c'est rapide.

### Color (Canal 6) — Roue à couleurs

| Valeur DMX | Couleur |
|------------|---------|
| 0-7 | Ouvert / blanc |
| 8-15 | Turquoise |
| 16-23 | Rouge |
| 24-31 | Cyan |
| 32-39 | Vert clair |
| 40-47 | Magenta |
| 48-55 | Bleu clair |
| 56-63 | Jaune |
| 64-71 | Vert |
| 72-79 | Rose |
| 80-87 | Bleu |
| 88-95 | Orange |
| 96-189 | Arc-en-ciel avant (rapide → lent) |
| 190-193 | Pas de rotation |
| 194-255 | Arc-en-ciel arrière (lent → rapide) |

**En pratique :** L'émetteur envoie les valeurs de début de plage (0, 8, 16, 24...) pour sélectionner une couleur fixe.

### Gobo (Canal 7) — Roue à gobos

| Valeur DMX | Fonction |
|------------|----------|
| 0-7 | Ouvert (pas de gobo) |
| 8-15 | Gobo 1 |
| 16-23 | Gobo 2 |
| ... | ... |
| 72-79 | Gobo 9 |
| 80-87 | Gobo 10 |
| 88-95 | Gobo 11 |
| 96-227 | Gobos tremblants (vitesse variable) |
| 228-255 | Rotation de la roue à gobos |

### Shutter (Canal 8) — Obturateur

| Valeur DMX | Fonction |
|------------|----------|
| 0 | Fermé (noir) |
| 1-63 | Intensité 0-100% (gradateur) |
| 64-95 | Ouvert (pleine lumière) |
| 96-127 | Stroboscope (lent → rapide, max 8 flash/sec) |
| 128-139 | Reset |
| 140-159 | Fermé |
| 160-175 | Pulse (accélération croissante) |
| 176-191 | Pulse (accélération décroissante) |
| 192-223 | Stroboscope aléatoire |
| 224-255 | Ouvert |

---

## 4. Le Flux de Données (Résumé Visuel)

```
┌─────────────────┐      ┌──────────────┐      ┌─────────────────┐      ┌─────────────┐
│   JOYSTICK      │      │   XIAO       │      │    XBee         │      │   LYRE      │
│  (X/Y/Z +       │  →   │  (CircuitPy) │  →   │  (sans fil)    │  →   │  (DMX512)   │
│   boutons +     │      │  Paquet 10o  │      │  2.4 GHz       │      │  ClubSpot   │
│   encodeur)     │      │  20 Hz       │      │  9600 baud     │      │  150 CT     │
└─────────────────┘      └──────────────┘      └─────────────────┘      └─────────────┘
        ↑                                                                        ↑
        │                                                                        │
   ÉMETTEUR (Yassine)                                                    RÉCEPTEUR (toi)
   - Lit les entrées                                                      - Reçoit sur UART
   - Construit le paquet                                                  - Vérifie checksum
   - Envoie via XBee                                                      - Envoie en DMX512
                                                                           - Au lyre
```

---

## 5. Configuration XBee (à faire une fois)

Les deux modules XBee doivent avoir la même configuration réseau :

| Paramètre | Émetteur (Yassine) | Récepteur (toi) | Commentaire |
|-----------|-------------------|-----------------|-------------|
| PAN ID | 1234 | 1234 | Même réseau |
| Channel | 12 | 12 | Même canal |
| MY Address | 1 | 2 | Adresse unique |
| Destination (DL) | 2 | 1 | Adresse de l'autre |
| Baud Rate | 9600 | 9600 | Même vitesse |
| Mode | Transparent (AP=0) | Transparent (AP=0) | Pass-through UART |

**Configuration via commandes AT :**
```
+++              (entrer en mode commande, attendre OK)
ATID1234         (PAN ID)
ATCH12           (canal)
ATMY2            (ton adresse)
ATDL1            (destination = Yassine)
ATBD3            (9600 baud)
ATAP0            (mode transparent)
ATWR             (sauvegarder en flash)
ATCN             (quitter le mode commande)
```

---

## 6. Le DMX512 (Côté Récepteur)

### Qu'est-ce que DMX512 ?
C'est un protocole standard pour contrôler les projecteurs/luminaires.  
Physiquement : câble XLR 3-pin (ou 5-pin), signal différentiel sur RS-485.

### Le Signal
- **Break** : ligne à l'état bas pendant ≥88µs (signal de début de trame)
- **MAB** (Mark After Break) : haut pendant ≥8µs
- **Start Code** : octet 0x00 (pour DMX standard)
- **Données** : jusqu'à 512 canaux, 1 octet chacun
- **Entre canaux** : 2 bits de stop (haut)

### Timing
- Vitesse : 250 000 baud (250 kbaud)
- 1 start bit, 8 data bits, 2 stop bits
- Pas de parité
- Trame complète : ~23ms (44 Hz)

### Ce que tu dois faire
1. Recevoir le paquet 10 octets du XBee (9600 baud)
2. Vérifier le checksum
3. Extraire les 8 valeurs DMX
4. Envoyer une trame DMX512 avec ces 8 valeurs sur les canaux 1-8
5. Répéter en boucle (~44 Hz)

---

## 7. Checklist de Validation

### Étape 1 : Test XBee seul
- [ ] Configurer le XBee (commandes AT ci-dessus)
- [ ] Brancher XBee DOUT → RX du XIAO (pin D7)
- [ ] Brancher XBee DIN → TX du XIAO (pin D6) — optionnel, pas utilisé
- [ ] Ouvrir le moniteur série à 9600 baud
- [ ] Vérifier que des données arrivent quand Yassine bouge le joystick

### Étape 2 : Test DMX seul
- [ ] Brancher MAX485 RO → RX du XIAO
- [ ] Brancher MAX485 DI → TX du XIAO
- [ ] Brancher MAX485 DE+RE → pin D10 (contrôle direction)
- [ ] Envoyer une trame DMX fixe (tous les canaux à 128)
- [ ] Vérifier avec un testeur DMX ou oscilloscope

### Étape 3 : Intégration
- [ ] Recevoir paquet XBee
- [ ] Parser les 10 octets
- [ ] Vérifier checksum
- [ ] Envoyer en DMX
- [ ] Tester avec la lyre réelle

---

## 8. Questions Fréquentes

**Q : Pourquoi 10 octets et pas plus ?**  
R : Le XBee S1 a une limite de 100 octets par paquet RF. 10 octets est largement suffisant pour 8 canaux DMX + contrôle.

**Q : Que se passe-t-il si un paquet est perdu ?**  
R : La lyre continue avec la dernière valeur connue. La perte d'un seul paquet sur 20Hz est imperceptible (50ms).

**Q : Pourquoi le checksum ?**  
R : Le sans fil peut corrompre des données. Le checksum détecte les paquets invalides pour éviter des mouvements erratiques de la lyre.

**Q : Le mode transparent vs API ?**  
R : Mode transparent = les octets entrants ressortent tels quels à l'autre bout. C'est le plus simple. Mode API = format structuré avec adresses, RSSI, etc. — plus complexe, inutile ici.

---

*Document v1.0 — 2026-05-27*  
*Pour toute question : demander à Yassine ou au prof*
