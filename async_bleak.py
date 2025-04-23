import asyncio
import time
from bleak import BleakScanner

# Première boucle infinie avec contrôle par Events
async def boucle_1(stop_event):
    while not stop_event.is_set():  # Continue tant que l'événement n'est pas déclenché
        print("Boucle 1 en cours...")
        await asyncio.sleep(1)
    print("Boucle 1 arrêtée")
    
    
async def main(stop_event):
    def callback(device, advertising_data):
        print(f"Device: {device}, RSSI: {advertising_data.rssi}")
        # If you want to stop the scanner when a device is found, uncomment the line below
        # stop_event.set()

    async with BleakScanner(callback) as scanner:
        # Important! Wait for an event to trigger stop, otherwise scanner
        # will stop immediately.
        await stop_event.wait()
        print("Stopping scanner...")
        

# Exécuter le programme
if __name__ == "__main__":
    stop_event = asyncio.Event()
    try:
        # asyncio.run(main(stop_event))
        # Lancer les deux boucles concurremment
        tasks = asyncio.gather(boucle_1(stop_event), main(stop_event), return_exceptions=True)
    except asyncio.CancelledError:
        print("Programme arrêté")
    except KeyboardInterrupt:
        stop_event.set()
        asyncio.sleep(10)
        print("Programme arrêté par l'utilisateur")