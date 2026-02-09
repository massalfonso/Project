import asyncio
import json
import serial
import websockets

SERIAL_PORT = "/dev/ttyACM0"
BAUD_RATE = 9600

clients = set()

async def handler(websocket, path):
    clients.add(websocket)
    print(f"✓ Client connected (total: {len(clients)})")
    try:
        await websocket.wait_closed()
    finally:
        clients.remove(websocket)
        print(f"✗ Client disconnected (remaining: {len(clients)})")

async def serial_reader():
    # Run serial reading in executor to avoid blocking
    loop = asyncio.get_event_loop()
    
    def read_serial():
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"✓ Serial port {SERIAL_PORT} opened at {BAUD_RATE} baud")
        return ser
    
    # Open serial in thread pool
    ser = await loop.run_in_executor(None, read_serial)
    
    # Give Arduino time to reset after serial connection
    await asyncio.sleep(2)
    print("✓ Serial connection ready\n")

    while True:
        # Read serial line in thread pool (non-blocking)
        raw = await loop.run_in_executor(None, ser.readline)

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
            print(f"📊 RPM: {data.get('rpm')} | Eff: {data.get('efficiency')}% | Current: {data.get('current')}A")
        except json.JSONDecodeError:
            print(f"Invalid JSON: {line}")
            continue

        # Broadcast to all connected clients
        if clients:
            msg = json.dumps(data)
            await asyncio.gather(*[ws.send(msg) for ws in clients], return_exceptions=True)

async def main():
    print("=" * 50)
    print("Regenerative Braking Dashboard Server")
    print("=" * 50)
    print("WebSocket server starting on ws://0.0.0.0:8080")
    
    async with websockets.serve(handler, "0.0.0.0", 8080):
        await serial_reader()

asyncio.run(main())