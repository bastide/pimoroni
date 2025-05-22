from aiomqtt import Client
import asyncio
import json

async def main():
    async with Client("localhost", 1883, keepalive=60) as client:
        payload = json.dumps({"temperature": 22.5})
        await client.publish("pemesa/temperature/outside", payload)
    
asyncio.run(main())