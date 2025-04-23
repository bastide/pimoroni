import asyncio

# Première boucle infinie avec contrôle par Event
async def boucle_1(stop_event):
    while not stop_event.is_set():  # Continue tant que l'événement n'est pas déclenché
        print("Boucle 1 en cours...")
        await asyncio.sleep(1)
    print("Boucle 1 arrêtée")

# Deuxième boucle infinie (sans arrêt)
async def boucle_2():
    while True:
        print("Boucle 2 en cours...")
        await asyncio.sleep(2)

# Fonction principale
async def main():
    # Créer un Event pour contrôler l'arrêt de boucle_1
    stop_event = asyncio.Event()

    # Lancer les deux boucles concurremment
    tasks = asyncio.gather(boucle_1(stop_event), boucle_2(), return_exceptions=True)

    # Attendre 5 secondes, puis déclencher l'arrêt de boucle_1
    await asyncio.sleep(5)
    print("Déclenchement de l'arrêt de boucle_1")
    stop_event.set()  # Signale l'arrêt de boucle_1

    # Attendre que boucle_1 se termine, boucle_2 continue
    await asyncio.sleep(5)  # Laisser du temps pour voir que boucle_2 continue
    tasks.cancel()  # Annuler toutes les tâches pour arrêter proprement

# Exécuter le programme
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except asyncio.CancelledError:
        print("Programme arrêté")
    except KeyboardInterrupt:
        print("Programme arrêté par l'utilisateur")