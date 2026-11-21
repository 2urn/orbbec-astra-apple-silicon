"""Stream the Astra to browser apps on this Mac.

    python web_bridge.py                 stream on ws://localhost:8766
    python web_bridge.py --web MYPAGES   also serve a folder of pages on http://localhost:8765

Only this Mac can connect: everything listens on 127.0.0.1.

Each WebSocket message is one binary frame:
    bytes 0-3   b"AST1"
    bytes 4-5   width  (uint16, little-endian)
    bytes 6-7   height (uint16, little-endian)
    then        width*height uint16 depth in millimetres (0 = no reading)
    then        width*height*3 uint8 RGB colour, lined up with the depth
"""
import argparse
import asyncio
import functools
import http.server
import os
import struct
import threading
import webbrowser

from websockets.asyncio.server import broadcast, serve

from astra import Astra

ap = argparse.ArgumentParser()
ap.add_argument("--port", type=int, default=8765, help="web page port; the WebSocket uses port+1 (default 8766)")
ap.add_argument("--web", metavar="FOLDER", help="also serve this folder of web pages on --port")
ap.add_argument("--full", action="store_true", help="send 640x480 instead of 320x240")
ap.add_argument("--open", action="store_true", help="open the served pages in the browser")
args = ap.parse_args()

clients = set()


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):  # keep the window quiet
        pass


def start_http(folder):
    handler = functools.partial(QuietHandler, directory=os.path.abspath(folder))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()


async def on_connect(ws):
    clients.add(ws)
    print(f"App connected ({len(clients)} open)")
    try:
        await ws.wait_closed()
    finally:
        clients.discard(ws)
        print(f"App disconnected ({len(clients)} open)")


async def main():
    if args.web:
        start_http(args.web)
    loop = asyncio.get_running_loop()
    step = 1 if args.full else 2
    with Astra() as cam:
        async with serve(on_connect, "127.0.0.1", args.port + 1, max_size=None,
                         compression=None):
            print(f"Astra bridge streaming on ws://localhost:{args.port + 1}  (keep this window open, Ctrl+C to stop)")
            if args.web:
                url = f"http://localhost:{args.port}"
                print(f"Serving {args.web} on {url}")
                if args.open:
                    webbrowser.open(url)
            while True:
                depth, color = await loop.run_in_executor(None, cam.read)
                if not clients:
                    continue
                d = depth[::step, ::step]
                c = color[::step, ::step, ::-1]  # BGR -> RGB
                h, w = d.shape
                msg = b"AST1" + struct.pack("<HH", w, h) + d.tobytes() + c.tobytes()
                broadcast(clients, msg)


try:
    asyncio.run(main())
except KeyboardInterrupt:
    pass
