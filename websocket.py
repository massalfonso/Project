import asyncio
import json
import serial
import websockets

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

    # Arduino resets when serial opens — give it time
    await asyncio.sleep(2)

    while True:
        try:
            raw = ser.readline()
        except serial.SerialException:
            continue  # port hiccup, skip and keep going

        print("RAW:", raw)   # ← DEBUG PRINT ADDED HERE

        if not raw:
            continue  # empty read, skip

        try:
            line = raw.decode(errors="ignore").strip()
        except:
            continue

        if not line:
            continue

        try:
            data = json.loads(line)
        except:
            continue  # malformed JSON, skip

        if clients:
            msg = json.dumps(data)
            await asyncio.gather(*(ws.send(msg) for ws in clients))

async def main():
    print("WebSocket server running on ws://0.0.0.0:8080")
    await websockets.serve(handler, "127.0.0.1", 8080)
    await serial_reader()

asyncio.run(main())



