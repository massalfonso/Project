import asyncio
import json
import serial
import websockets

# ---- CONFIG ----
SERIAL_PORT = "/dev/ttyACM0"
BAUD_RATE = 9600

clients = set()

async def handler(websocket, path):
    clients.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        clients.remove(websocket)

async def serial_reader():
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)

    # Give Arduino time to reboot after serial opens
    await asyncio.sleep(2)

    while True:
        line = ser.readline().decode().strip()

        # Skip empty reads
        if not line:
            continue

        # Try to parse JSON safely
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue  # skip malformed packets

        # Broadcast to all connected clients
        if clients:
            msg = json.dumps(data)
            await asyncio.gather(*(ws.send(msg) for ws in clients))

async def main():
    # Start WebSocket server
    server = await websockets.serve(handler, "0.0.0.0", 8080)
    print("WebSocket server running on ws://0.0.0.0:8080")

    # Start serial reader
    await serial_reader()

asyncio.run(main())

