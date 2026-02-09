import serial
import json
import asyncio
import websockets

clients = set()

async def handler(websocket, path):
    clients.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        clients.remove(websocket)

async def serial_reader():
    ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
    while True:
        line = ser.readline().decode().strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            if clients:
                msg = json.dumps(data)
                await asyncio.gather(*[ws.send(msg) for ws in clients])
        except json.JSONDecodeError:
            pass

async def main():
    await websockets.serve(handler, "0.0.0.0", 8080)
    await serial_reader()

asyncio.run(main())
