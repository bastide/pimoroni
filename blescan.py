import asyncio
from bleak import BleakScanner
import logging
import json

# Seuil RSSI pour considérer une balise comme "proche" (en dBm)
RSSI_THRESHOLD = -70
# Liste des noms de balises à surveiller
NOMS_BALISES = ["CF:1D:EB:92:AF:89", "C1:96:B3:D2:D9:0C", "5C-6B-64-D8-0C-D4"]

async def scan_ble_proches(balises):
    try:
        # Scanner pendant 4 secondes
        devices = await BleakScanner.discover(timeout=4.0, return_adv=True)
        proches = []
        for device, adv_data in devices.values():
            # Vérifier si le RSSI est supérieur au seuil et si le nom de la balise est dans la liste
            # des balises à surveiller
            if adv_data.rssi > RSSI_THRESHOLD and balises.get(device.address) is not None:
                # Ajouter la balise à la liste des balises proches
                
                proches.append(f"Adresse: {device.address}, RSSI: {adv_data.rssi} dBm, Nom: {balises.get(device.address)}")
        return proches
    except Exception as e:
        print(f"Erreur lors du scan : {e}")
        return []

async def main():
    balises = load_config()
    
    print("Démarrage du scan des balises proches...")
    while True:
        proches = await scan_ble_proches(balises)
        proches.sort(key=lambda x: x.split(", Nom: ")[-1])
        if proches:
            print(f"\nNombre de balises détectées : {len(proches)}")
            for balise in proches:
                print(balise)
        else:
            print("\nAucune balise proche détectée.")
        print("Prochain scan dans 5 secondes...")
        await asyncio.sleep(5)

def load_config():
    # Charger la configuration depuis un fichier JSON
    try:
        with open('beacons.json', 'r') as f:
            config = json.load(f)
            return config
    except FileNotFoundError:
        print("Fichier de configuration non trouvé.")
        return {}
    except json.JSONDecodeError:
        print("Erreur lors du chargement du fichier de configuration.")
        return {}
    except Exception as e:
        print(f"Erreur inattendue : {e}")
        return {}
    
    
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nArrêt du programme.")