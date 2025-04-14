import asyncio
from bleak import BleakScanner
# Seuil RSSI pour considérer une balise comme "proche" (en dBm)
RSSI_THRESHOLD = -70
# Liste des noms de balises à surveiller
NOMS_BALISES = ["WGX_iBeacon", "61-8E-38-26-BF-B1", "5C-6B-64-D8-0C-D4"]
async def scan_ble_proches():
    try:
        # Scanner pendant 4 secondes
        devices = await BleakScanner.discover(timeout=4.0, return_adv=True)
        proches = []
        for device, adv_data in devices.values():
            # Vérifier si le RSSI est supérieur au seuil et si le nom de la balise est dans la liste
            # des balises à surveiller
            if adv_data.rssi > RSSI_THRESHOLD:
                # Ajouter la balise à la liste des balises proches
                
                proches.append(f"Adresse: {device.address}, RSSI: {adv_data.rssi} dBm, Nom: {device.name}")
        return proches
    except Exception as e:
        print(f"Erreur lors du scan : {e}")
        return []

async def main():
    print("Démarrage du scan des balises proches...")
    while True:
        proches = await scan_ble_proches()
        proches.sort(key=lambda x: x.split(", Nom: ")[-1])
        if proches:
            print(f"\nNombre de balises détectées : {len(proches)}")
            for balise in proches:
                print(balise)
        else:
            print("\nAucune balise proche détectée.")
        print("Prochain scan dans 5 secondes...")
        await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nArrêt du programme.")