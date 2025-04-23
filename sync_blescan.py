#!/usr/bin/env python

import time
from bleak import BleakScanner
import logging # Although imported, logging is not used in this version
import json

# Seuil RSSI pour considérer une balise comme "proche" (en dBm)
# RSSI threshold to consider a beacon "nearby" (in dBm)
RSSI_THRESHOLD = -70

def load_config():
    """Loads beacon configuration from beacons.json."""
    # Charger la configuration depuis un fichier JSON
    # Load configuration from a JSON file
    try:
        with open('beacons.json', 'r') as f:
            config = json.load(f)
            print("Configuration chargée avec succès depuis beacons.json.")
            # Configuration loaded successfully from beacons.json.
            return config
    except FileNotFoundError:
        print("Erreur : Fichier de configuration 'beacons.json' non trouvé.")
        # Error: Configuration file 'beacons.json' not found.
        return {}
    except json.JSONDecodeError:
        print("Erreur : Impossible de décoder le fichier JSON 'beacons.json'. Vérifiez la syntaxe.")
        # Error: Could not decode JSON file 'beacons.json'. Check syntax.
        return {}
    except Exception as e:
        print(f"Erreur inattendue lors du chargement de la configuration : {e}")
        # Unexpected error loading configuration: {e}
        return {}

def scan_ble_proches(balises):
    """Scans for nearby BLE devices and filters them based on RSSI and known beacons."""
    try:
        print("Scanning for BLE devices...")
        # Scanner pendant 4 secondes (bloquant)
        # Scan for 4 seconds (blocking)
        # Note: BleakScanner.discover is blocking when not awaited in an async context
        devices = BleakScanner.discover(timeout=4.0, return_adv=True)
        proches = []
        print(f"Scan terminé. {len(devices)} appareils trouvés.")
        # Scan finished. {len(devices)} devices found.

        for device_address, (device, adv_data) in devices.items():
            # Vérifier si le RSSI est supérieur au seuil et si l'adresse MAC est dans la liste
            # des balises connues
            # Check if RSSI is above threshold and if MAC address is in the list
            # of known beacons
            if adv_data.rssi > RSSI_THRESHOLD and device.address in balises:
                nom_balise = balises.get(device.address, "Nom Inconnu") # Get name, default if somehow missing after check
                # Ajouter la balise à la liste des balises proches
                # Add the beacon to the list of nearby beacons
                proches.append({
                    "address": device.address,
                    "rssi": adv_data.rssi,
                    "name": nom_balise
                })
                # print(f"  -> Trouvé balise connue : {device.address} (RSSI: {adv_data.rssi} dBm)")
                # -> Found known beacon: ...
        return proches
    except Exception as e:
        print(f"Erreur lors du scan BLE : {e}")
        # Error during BLE scan: {e}
        return []

def main():
    """Main function to load config and continuously scan for beacons."""
    balises = load_config()
    if not balises:
        print("Aucune configuration de balise chargée. Le programme ne peut pas identifier les balises spécifiques.")
        # No beacon configuration loaded. The program cannot identify specific beacons.
        print("Veuillez créer un fichier 'beacons.json' avec le format {'MAC_ADDRESS': 'BEACON_NAME', ...}")
        # Please create a 'beacons.json' file with the format {'MAC_ADDRESS': 'BEACON_NAME', ...}
        return # Exit if config is empty

    print("\nDémarrage du scan des balises proches...")
    # Starting scan for nearby beacons...
    try:
        while True:
            proches = scan_ble_proches(balises)
            if proches:
                # Trier par nom pour une meilleure lisibilité
                # Sort by name for better readability
                proches.sort(key=lambda x: x["name"])
                print(f"\n--- Balises connues proches détectées ({len(proches)}) ---")
                # --- Known nearby beacons detected ---
                for balise_info in proches:
                    print(f"  Nom: {balise_info['name']}, Adresse: {balise_info['address']}, RSSI: {balise_info['rssi']} dBm")
            else:
                print("\n--- Aucune balise connue proche détectée ---")
                # --- No known nearby beacons detected ---

            print(f"\nProchain scan dans 5 secondes...")
            # Next scan in 5 seconds...
            time.sleep(5) # Use time.sleep for synchronous pause

    except KeyboardInterrupt:
        print("\nArrêt du programme demandé par l'utilisateur.")
        # Program shutdown requested by user.
    except Exception as e:
        print(f"\nUne erreur inattendue est survenue dans la boucle principale : {e}")
        # An unexpected error occurred in the main loop: {e}

if __name__ == "__main__":
    main() # Directly call the synchronous main function
