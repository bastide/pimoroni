#!/usr/bin/env python

import asyncio
import time # Keep for initial sensor setup if needed, but use asyncio.sleep in loop
import bme680
from datetime import datetime
import signal # For graceful shutdown
from bleak import BleakScanner
import logging
import json


# Import async InfluxDB client
from influxdb_client import Point, WritePrecision
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync

# InfluxDB 2.x configuration (Keep your credentials secure!)
INFLUXDB_URL = "https://us-east-1-1.aws.cloud2.influxdata.com"
INFLUXDB_TOKEN = "hEcEfCBEV2i9iYE8TUnkAiKYT1XPTf-jZMumYe0Vl5Al80eJNqRwkgRtoTsI2CdIWr4tNPljAC8cKDKIN0TS_A==" # Consider using environment variables or a config file
INFLUXDB_ORG = "ffe282e26b5d954c"
INFLUXDB_ENVIRONMENT_BUCKET = "bme680_data"
INFLUXDB_LOCATION_BUCKET = "balenaLocating"  
# Seuil RSSI pour considérer une balise comme "proche" (en dBm)
RSSI_THRESHOLD = -70

async def main():
    # Global flag to signal shutdown
    shutdown_event = asyncio.Event()

    def handle_signal(sig, frame):
        """Signal handler to initiate graceful shutdown."""
        print(f"\nReceived signal {sig}, initiating shutdown...")
        shutdown_event.set()

    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, handle_signal)  # Handle Ctrl+C
    signal.signal(signal.SIGTERM, handle_signal) # Handle termination signals
        
    # Initialize InfluxDB async client
    # Use an 'async with' block for automatic cleanup
    async with InfluxDBClientAsync(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG) as client:
        # Get the asynchronous write API
        # Default write options are generally suitable for async
        write_api = client.write_api()

        await asyncio.gather(
            environment_sensors(write_api,shutdown_event),  # Environment sensor loop
            location_sensors(write_api,shutdown_event),  # Location sensor loop
            return_exceptions=True)  # Handle exceptions in tasks
    # The 'async with' block handles client.close() automatically


# Première boucle infinie avec contrôle par Event
async def location_sensors(write_api,shutdown_event):
    """Main asynchronous function to scan BLE devices and write to InfluxDB."""

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
        
    async def scan_ble_proches(balises):
        try:
            # Scanner pendant 4 secondes
            devices = await BleakScanner.discover(timeout=4.0, return_adv=True)
            proches = []
            for device, adv_data in devices.values():
                device_name = balises.get(device.address)
                # Vérifier si le RSSI est supérieur au seuil et si le nom de la balise est dans la liste
                # des balises à surveiller
                if adv_data.rssi > RSSI_THRESHOLD and device_name is not None:
                    # Ajouter la balise à la liste des balises proches
                    proches.append(f"Adresse: {device.address}, RSSI: {adv_data.rssi} dBm, Nom: {device_name}")
                    # create InfluxDB data point
                    point = Point("ble_measurements") \
                        .tag("sensor", "ble") \
                        .tag("location", "raspberry_pi") \
                        .tag("device_name", device_name) \
                        .field("rssi", int(adv_data.rssi)) \
                        .time(datetime.utcnow(), WritePrecision.NS)
                    # Write to InfluxDB asynchronously
                    try:
                        await write_api.write(bucket=INFLUXDB_LOCATION_BUCKET, record=point)
                        print(f"Sent to InfluxDB: {point}")
                    except Exception as influx_err:
                        # Handle potential InfluxDB write errors (e.g., network issues)
                        print(f"Error writing to InfluxDB: {influx_err}")
                        # Consider adding retry logic or logging here
            return proches
        except Exception as e:
            print(f"Erreur lors du scan : {e}")
            return []    

    print("""location.py (async) - Scans for BLE devices and writes to InfluxDB.
    Press Ctrl+C to exit!
    """)    
    balises = load_config()

    while not shutdown_event.is_set():  # Continue tant que l'événement n'est pas déclenché
        proches = await scan_ble_proches(balises)
        if proches:
            proches.sort(key=lambda x: x.split(", Nom: ")[-1])
            print(f"\nNombre de balises détectées : {len(proches)}")
            for balise in proches:
                print(balise)
        else:
            print("\nAucune balise proche détectée.")
        print("Prochain scan dans 5 secondes...")
        # Use asyncio.sleep for non-blocking delay
        try:
                await asyncio.wait_for(shutdown_event.wait(), timeout=5)
                # If wait() completes, shutdown was triggered during sleep
                break # Exit loop if shutdown event is set
        except asyncio.TimeoutError:
                # Timeout occurred, continue loop normally
                pass
    print("Location loop arrêtée")
    
async def environment_sensors(write_api,shutdown_event):
    """Main asynchronous function to read sensor data and write to InfluxDB."""
    print("""read-all.py (async) - Displays temperature, pressure, humidity, and gas.

    Press Ctrl+C to exit!
    """)

    # Initialize BME680 sensor
    try:
        sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)
    except (RuntimeError, IOError) as e:
        print(f"Could not initialize sensor at primary address: {e}. Trying secondary...")
        try:
            sensor = bme680.BME680(bme680.I2C_ADDR_SECONDARY)
        except (RuntimeError, IOError) as e2:
            print(f"Error initializing sensor at secondary address: {e2}. Exiting.")
            return # Exit if sensor cannot be initialized

    # --- Sensor Configuration ---
    # Optional: Print calibration data
    print('Calibration data:')
    for name in dir(sensor.calibration_data):
        if not name.startswith('_'):
            value = getattr(sensor.calibration_data, name)
            if isinstance(value, int):
                print(f'{name}: {value}')

    # Set sensor parameters
    sensor.set_humidity_oversample(bme680.OS_2X)
    sensor.set_pressure_oversample(bme680.OS_4X)
    sensor.set_temperature_oversample(bme680.OS_8X)
    sensor.set_filter(bme680.FILTER_SIZE_3)
    sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)

    # Optional: Print initial reading
    print('\n\nInitial reading:')
    # It's good practice to get initial data before setting heater
    if sensor.get_sensor_data():
         for name in dir(sensor.data):
            if not name.startswith('_'):
                value = getattr(sensor.data, name)
                print(f'{name}: {value}')
    else:
        print("Could not get initial sensor data.")


    sensor.set_gas_heater_temperature(320)
    sensor.set_gas_heater_duration(150)
    sensor.select_gas_heater_profile(0)
    # --- End Sensor Configuration ---
    print('\n\nPolling (async):')
    try:
        while not shutdown_event.is_set():
            # Sensor reading is synchronous
            if sensor.get_sensor_data():
                # Collect measurements
                temp = sensor.data.temperature
                humidity = sensor.data.humidity
                pressure = sensor.data.pressure
                # Check heat_stable *before* accessing gas_resistance
                gas = sensor.data.gas_resistance if sensor.data.heat_stable else None

                # Prepare console output
                output = f'{temp:.2f} C, {pressure:.2f} hPa, {humidity:.2f} %RH'
                if gas is not None:
                    print(f'{output}, {gas:.2f} Ohms')
                else:
                    print(f'{output}, Gas reading not stable')

                # Create InfluxDB data point
                point = Point("bme680_measurements") \
                    .tag("sensor", "bme680") \
                    .tag("location", "raspberry_pi") \
                    .field("temperature", float(temp)) \
                    .field("humidity", float(humidity)) \
                    .field("pressure", float(pressure)) \
                    .time(datetime.utcnow(), WritePrecision.NS) # Use UTC time

                # Add gas resistance only if stable and valid
                if gas is not None:
                    # Ensure gas is float, handle potential errors if needed
                    try:
                        point.field("gas_resistance", float(gas))
                    except ValueError:
                        print(f"Warning: Could not convert gas resistance '{gas}' to float.")
                        # Decide how to handle: skip field, log error, etc.

                # Write to InfluxDB asynchronously
                try:
                    await write_api.write(bucket=INFLUXDB_ENVIRONMENT_BUCKET, record=point)
                    print(f"Sent to InfluxDB: {point}")
                except Exception as influx_err:
                    # Handle potential InfluxDB write errors (e.g., network issues)
                    print(f"Error writing to InfluxDB: {influx_err}")
                    # Consider adding retry logic or logging here

            else:
                print("Failed to retrieve sensor data.")

            # Use asyncio.sleep for non-blocking delay
            try:
                await asyncio.wait_for(shutdown_event.wait(), timeout=10)
                # If wait() completes, shutdown was triggered during sleep
                break # Exit loop if shutdown event is set
            except asyncio.TimeoutError:
                # Timeout occurred, continue loop normally
                pass
    except Exception as e:
        # Catch unexpected errors during the loop
        print(f"An unexpected error occurred: {e}")
    finally:
            print("Exiting polling loop.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # This might still catch the initial Ctrl+C if it happens before the loop starts
        print("\nShutdown requested (KeyboardInterrupt outside loop).")
    finally:
        print("Script finished.")

