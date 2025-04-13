#!/usr/bin/env python

import time

import bme680

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import time
from datetime import datetime

# InfluxDB 2.x configuration
INFLUXDB_URL = "https://us-east-1-1.aws.cloud2.influxdata.com"  # Change if remote
INFLUXDB_TOKEN = "hEcEfCBEV2i9iYE8TUnkAiKYT1XPTf-jZMumYe0Vl5Al80eJNqRwkgRtoTsI2CdIWr4tNPljAC8cKDKIN0TS_A=="      # From InfluxDB UI
INFLUXDB_ORG = "ffe282e26b5d954c"          # Your organization name
INFLUXDB_BUCKET = "bme680_data"         # Your bucket name

# Initialize InfluxDB client
client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)

print("""read-all.py - Displays temperature, pressure, humidity, and gas.

Press Ctrl+C to exit!

""")

try:
    sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)
except (RuntimeError, IOError):
    sensor = bme680.BME680(bme680.I2C_ADDR_SECONDARY)

# These calibration data can safely be commented
# out, if desired.

print('Calibration data:')
for name in dir(sensor.calibration_data):

    if not name.startswith('_'):
        value = getattr(sensor.calibration_data, name)

        if isinstance(value, int):
            print('{}: {}'.format(name, value))

# These oversampling settings can be tweaked to
# change the balance between accuracy and noise in
# the data.

sensor.set_humidity_oversample(bme680.OS_2X)
sensor.set_pressure_oversample(bme680.OS_4X)
sensor.set_temperature_oversample(bme680.OS_8X)
sensor.set_filter(bme680.FILTER_SIZE_3)
sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)

print('\n\nInitial reading:')
for name in dir(sensor.data):
    value = getattr(sensor.data, name)

    if not name.startswith('_'):
        print('{}: {}'.format(name, value))

sensor.set_gas_heater_temperature(320)
sensor.set_gas_heater_duration(150)
sensor.select_gas_heater_profile(0)

# Up to 10 heater profiles can be configured, each
# with their own temperature and duration.
# sensor.set_gas_heater_profile(200, 150, nb_profile=1)
# sensor.select_gas_heater_profile(1)

print('\n\nPolling:')
try:
    while True:
        if sensor.get_sensor_data():
                        # Collect measurements
            temp = sensor.data.temperature
            humidity = sensor.data.humidity
            pressure = sensor.data.pressure
            gas = sensor.data.gas_resistance if sensor.data.heat_stable else None

            output = '{0:.2f} C,{1:.2f} hPa,{2:.2f} %RH'.format(
                temp,
                pressure,
                humidity)

            if sensor.data.heat_stable:
                print('{0},{1} Ohms'.format(
                    output,
                    sensor.data.gas_resistance))

            else:
                print(output)
            # Create a data point
            point = Point("bme680_measurements") \
                .tag("sensor", "bme680") \
                .tag("location", "raspberry_pi") \
                .field("temperature", temp) \
                .field("humidity", humidity) \
                .field("pressure", pressure)

            # Add gas resistance only if stable
            if gas is not None:
                point.field("gas_resistance", gas)

            # Set timestamp to current time
            point.time(datetime.utcnow(), WritePrecision.NS)

            # Write to InfluxDB
            write_api.write(bucket=INFLUXDB_BUCKET, record=point)

            # Print for confirmation
            print(f"Sent to InfluxDB: T={temp:.2f}°C, H={humidity:.2f}%RH, P={pressure:.2f}hPa, Gas={gas if gas else 'unstable'} Ohms")

        time.sleep(10)

except KeyboardInterrupt:
    print("Stopped by user")
except Exception as e:
    print(f"Error: {e}")
finally:
    client.close()  # Clean up InfluxDB client