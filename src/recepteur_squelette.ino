/*
 * DMX Récepteur — Squelette Arduino pour XIAO RP2040
 * 
 * Projet BTS SN — Lyre motorisée ClubSpot 150 CT
 * 
 * Ce code est un SQUELETTE. Il contient :
 *   - La structure complète du programme
 *   - Des commentaires détaillés en français
 *   - Des sections marquées [TODO] à compléter
 * 
 * Matériel :
 *   - XIAO RP2040
 *   - Module XBee S1 (réception sans fil)
 *   - Module MAX485 (conversion UART → DMX512/RS-485)
 *   - Lyre DMX ClubSpot 150 CT
 * 
 * Connexions :
 *   XBee DOUT (données) → XIAO RX (pin D7)
 *   XBee DIN  → non utilisé (récepteur = RX seulement)
 *   MAX485 RO (Receive Out) → XIAO RX (partagé avec XBee ? Non, voir ci-dessous)
 *   MAX485 DI (Data In) → XIAO TX (pin D6)
 *   MAX485 DE+RE (Driver/Receiver Enable) → XIAO D10
 *   
 *   IMPORTANT : XBee et MAX485 utilisent tous les deux l'UART.
 *   Solution : utiliser SoftwareSerial pour le XBee, ou un 2ème UART si dispo.
 *   Sur XIAO RP2040 : UART0 (Serial1) = pins TX=D6, RX=D7
 *   Le XBee est sur Serial1. Le MAX485 utilise aussi Serial1 pour envoyer DMX.
 *   Donc on ne peut pas recevoir XBee et envoyer DMX en même temps sur le même UART.
 *   
 *   OPTIONS :
 *   1. Utiliser SoftwareSerial pour le XBee (pins libres : D2, D3, D8, D9, D10)
 *   2. Ou : déconnecter le XBee du MAX485, utiliser un seul à la fois
 *   3. Ou : utiliser le 2ème UART du RP2040 (UART1 sur pins différentes)
 *   
 *   Ici on utilise l'OPTION 1 : SoftwareSerial pour le XBee.
 */

#include <SoftwareSerial.h>

// [NOTE POUR LE CAMARADE]
// SoftwareSerial est une bibliothèque Arduino qui permet de créer
// un port série sur n'importe quelles pins digitales.
// C'est plus lent que le vrai UART matériel, mais pour 9600 baud
// ça suffit largement. Le vrai UART (Serial1) est réservé pour
// le DMX à 250000 baud.

// ============================================================
// CONFIGURATION — À ADAPTER SELON TON MONTAGE
// ============================================================

// Pins pour le XBee (SoftwareSerial)
// [TODO] Choisir 2 pins libres sur ton XIAO
#define XBEE_RX_PIN   2   // D2 — XBee DOUT (données reçues)
#define XBEE_TX_PIN   3   // D3 — XBee DIN (non utilisé en réception, mais requis par SoftwareSerial)

// Pin pour le MAX485 (contrôle de direction)
// [TODO] Vérifier que D10 est libre sur ton montage
#define MAX485_DE_PIN 10  // D10 — HIGH = émission (DMX), LOW = réception (inutilisé)

// Vitesse du XBee (doit matcher la config AT : ATBD3 = 9600)
#define XBEE_BAUD     9600

// Vitesse DMX512 (standard : 250000 baud)
#define DMX_BAUD      250000

// Taille du paquet sans fil
#define PACKET_SIZE   10

// Nombre de canaux DMX à envoyer (on utilise les 8 premiers)
#define DMX_CHANNELS  8

// ============================================================
// VARIABLES GLOBALES
// ============================================================

// [EXPLICATION] SoftwareSerial crée un port série logiciel
// sur n'importe quelles pins digitales. C'est plus lent que
// le vrai UART matériel, mais suffisant pour 9600 baud.
SoftwareSerial xbee(XBEE_RX_PIN, XBEE_TX_PIN);

// Buffer de réception du paquet XBee
// [EXPLICATION] Un tableau de 10 octets pour stocker le paquet reçu
byte packet[PACKET_SIZE];

// Index dans le buffer (0 à 9)
int packetIndex = 0;

// Valeurs DMX actuelles (canaux 1-8)
// [EXPLICATION] DMX utilise des valeurs 0-255. 128 = centre/neutre.
byte dmxValues[DMX_CHANNELS] = {128, 128, 128, 128, 0, 0, 0, 64};

// Dernier numéro de séquence reçu (pour détecter les pertes)
byte lastSequence = 0;

// Compteur de paquets reçus (pour statistiques)
unsigned long packetsReceived = 0;

// Compteur de paquets invalides (checksum faux)
unsigned long packetsInvalid = 0;

// ============================================================
// SETUP — Initialisation au démarrage
// ============================================================

void setup() {
  // [TODO] Décommenter pour le debug via USB
  // Serial.begin(115200);
  // while (!Serial); // Attendre l'ouverture du moniteur (uniquement pour debug)
  
  // Configuration du pin de direction MAX485
  // [EXPLICATION] Le MAX485 a besoin qu'on lui dise s'il doit
  // émettre (DE=HIGH) ou recevoir (RE=LOW). En réalité RE et DE
  // sont souvent reliés ensemble. Ici on ne fait qu'émettre DMX.
  pinMode(MAX485_DE_PIN, OUTPUT);
  digitalWrite(MAX485_DE_PIN, LOW); // Par défaut : réception (sécurité)
  
  // Démarrage du port XBee
  // [EXPLICATION] On ouvre la communication avec le module XBee
  // à 9600 baud. Les données arriveront automatiquement quand
  // Yassine enverra depuis l'émetteur.
  xbee.begin(XBEE_BAUD);
  
  // [TODO] Optionnel : message de démarrage sur USB
  // Serial.println("Récepteur DMX démarré");
  // Serial.println("Attente de paquets XBee...");
}

// ============================================================
// LOOP — Boucle principale (s'exécute en permanence)
// ============================================================

void loop() {
  // Étape 1 : Lire les données du XBee
  // [EXPLICATION] xbee.available() dit s'il y a des octets
  // reçus en attente dans le buffer. On les lit un par un.
  while (xbee.available()) {
    byte incoming = xbee.read(); // Lire 1 octet
    
    // [EXPLICATION] On remplit le buffer progressivement.
    // Quand on a 10 octets, on traite le paquet complet.
    packet[packetIndex] = incoming;
    packetIndex++;
    
    // Si le buffer est plein (10 octets reçus)
    if (packetIndex >= PACKET_SIZE) {
      packetIndex = 0; // Reset pour le prochain paquet
      
      // Étape 2 : Vérifier le paquet
      if (verifyPacket()) {
        // Paquet valide → extraire les valeurs
        parsePacket();
        packetsReceived++;
        
        // Étape 3 : Envoyer en DMX
        sendDMX();
      } else {
        // Paquet corrompu → ignorer
        packetsInvalid++;
      }
    }
  }
  
  // [EXPLICATION] Même si aucun paquet n'est reçu, il faut
  // continuer à envoyer du DMX (la lyre garde ses valeurs).
  // Le DMX doit être envoyé en continu (~44 Hz).
  // [TODO] Ajouter un timer pour envoyer DMX régulièrement
  // même sans nouveau paquet.
}

// ============================================================
// FONCTION : verifyPacket()
// Vérifie l'intégrité du paquet avec le checksum
// ============================================================

bool verifyPacket() {
  // [EXPLICATION] Le checksum est un XOR (OU exclusif) de tous
  // les octets du message (octets 0 à 8). Le résultat doit être
  // égal à l'octet 9 (le checksum reçu).
  //
  // XOR : si les 2 bits sont différents → 1, sinon → 0
  // Exemple : 5 XOR 3 = 6 (car 101 XOR 011 = 110)
  //
  // Le XOR est utilisé car :
  // - Simple à calculer
  // - Détecte les erreurs de transmission
  // - Si un seul bit change, le checksum change
  //
  // [POUR LE CAMARADE]
  // Le checksum permet de vérifier que le paquet n'a pas été
  // corrompu pendant la transmission sans fil. Si le checksum
  // ne correspond pas, on ignore le paquet (la lyre garde
  // sa dernière position).
  
  byte calculatedChecksum = 0;
  
  // [TODO] Compléter : calculer le XOR des octets 0 à 8
  // INDICE : utiliser l'opérateur ^ (XOR en C)
  // INDICE : for (int i = 0; i < 9; i++) { ... }
  //
  // [AIDE] Le XOR cumulatif fonctionne comme ça :
  //   checksum = 0
  //   checksum = checksum XOR octet0
  //   checksum = checksum XOR octet1
  //   ...
  //   checksum = checksum XOR octet8
  //
  // En C : checksum = checksum ^ packet[i];
  //        ou plus court : checksum ^= packet[i];
  
  // [EXEMPLE DE SOLUTION — à supprimer quand tu as compris]
  for (int i = 0; i < 9; i++) {
    calculatedChecksum ^= packet[i];  // XOR cumulatif
  }
  
  // Comparer avec le checksum reçu (octet 9)
  // Si égaux → paquet valide (return true)
  // Si différents → paquet corrompu (return false)
  return (calculatedChecksum == packet[9]);
}

// ============================================================
// FONCTION : parsePacket()
// Extrait les 8 valeurs DMX du paquet reçu
// ============================================================

void parsePacket() {
  // [EXPLICATION] Le paquet contient directement les valeurs DMX
  // dans l'ordre. On les copie dans notre tableau dmxValues.
  //
  // packet[0] = Pan (canal DMX 1)
  // packet[1] = Tilt (canal DMX 2)
  // packet[2] = Pan Fine (canal DMX 3)
  // packet[3] = Tilt Fine (canal DMX 4)
  // packet[4] = Speed (canal DMX 5)
  // packet[5] = Color (canal DMX 6)
  // packet[6] = Gobo (canal DMX 7)
  // packet[7] = Shutter (canal DMX 8)
  // packet[8] = Numéro de séquence (pas une valeur DMX)
  // packet[9] = Checksum (pas une valeur DMX)
  //
  // [POUR LE CAMARADE]
  // C'est ici qu'on récupère les valeurs envoyées par Yassine.
  // Après cette fonction, dmxValues[] contient les 8 valeurs
  // à envoyer à la lyre.
  
  // [TODO] Copier les 8 premiers octets du paquet dans dmxValues
  // INDICE : utiliser une boucle for
  //
  // [AIDE] En C, une boucle for ressemble à ça :
  //   for (int i = 0; i < 8; i++) {
  //     dmxValues[i] = packet[i];
  //   }
  //
  // Cela copie packet[0] dans dmxValues[0], packet[1] dans
  // dmxValues[1], etc. jusqu'à packet[7] dans dmxValues[7].
  
  // [EXEMPLE DE SOLUTION — à supprimer quand tu as compris]
  for (int i = 0; i < DMX_CHANNELS; i++) {
    dmxValues[i] = packet[i];
  }
  
  // [TODO BONUS] Vérifier le numéro de séquence
  // Le numéro de séquence (packet[8]) augmente de 1 à chaque
  // paquet (0, 1, 2, ..., 255, 0, 1...). Si on reçoit 5 puis 8,
  // on sait que 2 paquets ont été perdus.
  //
  // C'est optionnel mais utile pour diagnostiquer la qualité
  // du lien sans fil.
  //
  // INDICE :
  //   byte currentSequence = packet[8];
  //   if (currentSequence != lastSequence + 1) {
  //     // Paquet(s) manquant(s)
  //   }
  //   lastSequence = currentSequence;
}

// ============================================================
// FONCTION : sendDMX()
// Envoie une trame DMX512 complète
// ============================================================

void sendDMX() {
  // [EXPLICATION] Une trame DMX512 commence par :
  // 1. BREAK : ligne à l'état bas pendant ≥88µs
  // 2. MAB (Mark After Break) : haut pendant ≥8µs
  // 3. Start Code : octet 0x00
  // 4. Données : jusqu'à 512 canaux
  //
  // Le RP2040 a un UART matériel (Serial1) qu'on utilise pour DMX.
  // Il faut d'abord configurer le MAX485 en mode émission (DE=HIGH).
  //
  // [POUR LE CAMARADE]
  // Le DMX utilise un signal spécial au début (BREAK) que l'UART
  // normal ne peut pas générer. On doit donc :
  // 1. Désactiver l'UART
  // 2. Manipuler le pin TX manuellement (LOW pendant 100µs)
  // 3. Réactiver l'UART
  // 4. Envoyer les données normalement
  
  // Passer en mode émission (MAX485 émet vers la lyre)
  digitalWrite(MAX485_DE_PIN, HIGH);
  
  // [TODO] Étape 1 : Envoyer le BREAK
  // Le BREAK est une ligne LOW pendant au moins 88µs.
  // Technique : désactiver Serial1, mettre TX en OUTPUT, LOW, attendre.
  //
  // INDICE :
  //   Serial1.end();                    // Désactiver UART
  //   pinMode(PIN_SERIAL1_TX, OUTPUT);  // TX en sortie
  //   digitalWrite(PIN_SERIAL1_TX, LOW); // Forcer LOW
  //   delayMicroseconds(100);            // Attendre 100µs (>88µs)
  //   digitalWrite(PIN_SERIAL1_TX, HIGH); // Remettre HIGH
  //
  // [TODO] Étape 2 : Réactiver l'UART à 250000 baud
  // INDICE : Serial1.begin(250000);
  //
  // [TODO] Étape 3 : Attendre le MAB (Mark After Break)
  // Après le BREAK, la ligne est HIGH. On attend 12µs pour
  // être sûr d'avoir le MAB correct.
  // INDICE : delayMicroseconds(12);
  //
  // [TODO] Étape 4 : Envoyer le Start Code (0x00)
  // C'est le premier octet de la trame DMX. Valeur = 0.
  // INDICE : Serial1.write(0x00);
  //
  // [TODO] Étape 5 : Envoyer les 8 canaux DMX
  // Les valeurs sont dans le tableau dmxValues[0] à dmxValues[7]
  // INDICE :
  //   for (int i = 0; i < DMX_CHANNELS; i++) {
  //     Serial1.write(dmxValues[i]);
  //   }
  //
  // [TODO] Étape 6 (optionnel) : Envoyer les canaux 9-512 à 0
  // Pour une trame complète. Pas obligatoire pour tester avec
  // une seule lyre qui n'utilise que les canaux 1-8.
  //
  // [TODO] Étape 7 : Repasser en mode réception (sécurité)
  // INDICE : digitalWrite(MAX485_DE_PIN, LOW);
  
  // Repasser en mode réception (sécurité)
  digitalWrite(MAX485_DE_PIN, LOW);
}

// ============================================================
// FONCTION : sendBreak()
// Envoie un signal BREAK DMX (ligne basse ≥88µs)
// ============================================================

void sendBreak() {
  // [EXPLICATION] Le BREAK est le début de chaque trame DMX.
  // C'est une violation du format UART : la ligne reste à LOW
  // pendant plus longtemps qu'un octet normal.
  //
  // Technique : on désactive l'UART, on met TX en mode OUTPUT,
  // on force LOW, on attend 100µs, on remet HIGH, on réactive l'UART.
  //
  // [POUR LE CAMARADE]
  // Cette fonction est appelée par sendDMX(). Tu peux l'utiliser
  // directement ou l'intégrer dans sendDMX(). Le BREAK est le
  // signal le plus important du DMX — sans lui, la lyre ne
  // reconnaît pas le début de la trame.
  
  // [TODO] Implémenter le BREAK
  // INDICE (étape par étape) :
  // 1. Serial1.end();                    // Désactiver UART
  // 2. pinMode(PIN_SERIAL1_TX, OUTPUT);  // TX en sortie manuelle
  // 3. digitalWrite(PIN_SERIAL1_TX, LOW); // Forcer LOW
  // 4. delayMicroseconds(100);            // Attendre 100µs (>88µs)
  // 5. digitalWrite(PIN_SERIAL1_TX, HIGH); // Remettre HIGH
  // 6. Serial1.begin(DMX_BAUD);           // Réactiver UART
  //
  // [NOTE] PIN_SERIAL1_TX est probablement D6 sur XIAO RP2040.
  // Vérifie dans la doc du board.
}

// ============================================================
// FONCTION : sendMAB()
// Envoie le Mark After Break (ligne haute ≥8µs)
// ============================================================

void sendMAB() {
  // [EXPLICATION] Après le BREAK, la ligne doit être HIGH
  // pendant au moins 8µs avant le Start Code.
  // Avec l'UART réactivé, le niveau HIGH est déjà présent.
  // On attend juste un peu.
  
  // [TODO] Attendre 12µs (marge de sécurité)
  // INDICE : delayMicroseconds(12);
}

// ============================================================
// FONCTION : debugPrint()
// Affiche les valeurs sur le moniteur série USB (debug)
// ============================================================

void debugPrint() {
  // [POUR LE CAMARADE]
  // Cette fonction affiche les valeurs DMX reçues sur le moniteur
  // série USB. C'est très utile pour vérifier que tout fonctionne
  // sans avoir besoin de la lyre.
  //
  // Pour l'utiliser :
  // 1. Décommenter les lignes ci-dessous
  // 2. Brancher le XIAO en USB
  // 3. Ouvrir le moniteur série (Outils > Moniteur Série)
  // 4. Mettre la vitesse à 115200 baud
  //
  // Format d'affichage :
  // DMX : 128 128 128 128 0 0 0 64 | Seq: 42 | OK: 150 | Err: 2
  //       ^^^^^^^^^^^^^^^^^^^^^^^^        ^^^^       ^^^       ^^^
  //       Canaux 1-8                        Séquence   Paquets   Erreurs
  //                                                    OK        checksum
  
  // [TODO] Décommenter pour le debug
  // Serial.print("DMX : ");
  // for (int i = 0; i < DMX_CHANNELS; i++) {
  //   Serial.print(dmxValues[i]);
  //   Serial.print(" ");
  // }
  // Serial.print(" | Seq: ");
  // Serial.print(packet[8]);
  // Serial.print(" | OK: ");
  // Serial.print(packetsReceived);
  // Serial.print(" | Err: ");
  // Serial.println(packetsInvalid);
}

// ============================================================
// NOTES POUR LE PROF / DOCUMENTATION
// ============================================================

/*
 * TABLEAU RÉCAPITULATIF DES CANAUX DMX
 * 
 * Canal | Fonction        | Valeur neutre | Contrôle
 * ------|-----------------|---------------|----------
 *   1   | Pan (gauche)    | 128           | Joystick X
 *   2   | Tilt (haut)     | 128           | Joystick Y
 *   3   | Pan Fine        | 128           | Joystick X (précision)
 *   4   | Tilt Fine       | 128           | Joystick Y (précision)
 *   5   | Vitesse         | 0-249         | Joystick Z (rotation)
 *   6   | Couleur         | 0-255         | Encodeur + boutons
 *   7   | Gobo            | 0-255         | Boutons
 *   8   | Shutter         | 64-95 (ouvert)| Encodeur bouton
 * 
 * 
 * FORMAT DU PAQUET SANS FIL (10 octets)
 * 
 * Octet | Nom           | Description
 * ------|---------------|--------------------------------
 *   0   | Pan           | 0-255, 128 = centre
 *   1   | Tilt          | 0-255, 128 = centre
 *   2   | Pan Fine      | 0-255, 128 = centre
 *   3   | Tilt Fine     | 0-255, 128 = centre
 *   4   | Speed         | Voir GUIDE_RECEPTEUR.md
 *   5   | Color         | Voir GUIDE_RECEPTEUR.md
 *   6   | Gobo          | Voir GUIDE_RECEPTEUR.md
 *   7   | Shutter       | Voir GUIDE_RECEPTEUR.md
 *   8   | Sequence      | 0-255, incrémenté à chaque paquet
 *   9   | Checksum      | XOR des octets 0-8
 */

// ============================================================
// FIN DU SQUELETTE
// ============================================================
