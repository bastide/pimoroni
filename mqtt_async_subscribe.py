import aiomqtt
import asyncio

async def main():
    # test.mosquitto.org is a public MQTT broker
    client = aiomqtt.Client("localhost", 1883, keepalive=60)
    interval = 5  # Seconds
    while True:
        try:
            async with client:
                await client.subscribe("pemesa/temperature/#")
                async for message in client.messages:
                    print(f"Received: {message.payload.decode()} on {message.topic}")
        except aiomqtt.MqttError as e:
                print(f"Error: {e}")
                print("Attempting to reconnect...")
                await asyncio.sleep(interval)  # Wait before reconnecting

asyncio.run(main())