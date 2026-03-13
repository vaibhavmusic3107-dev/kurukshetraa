#!/usr/bin/env python3
"""
KURUKSHETRA CHESS — Multiplayer Server
Pure Python stdlib — no pip installs needed.
Run: python3 server.py
Then open: http://localhost:8765
"""

import asyncio
import hashlib
import base64
import json
import struct
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import socket

# --- Chess Logic (pure Python, no lib needed) ---
STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

# --- WebSocket Server ---
WS_MAGIC = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

def ws_handshake(client_sock, request_data):
    key = ""
    for line in request_data.split("\r\n"):
        if line.startswith("Sec-WebSocket-Key:"):
            key = line.split(": ")[1].strip()
    accept = base64.b64encode(
        hashlib.sha1((key + WS_MAGIC).encode()).digest()
    ).decode()
    response = (
        "HTTP/1.1 101 Switching Protocols\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Accept: {accept}\r\n\r\n"
    )
    client_sock.send(response.encode())

def ws_recv(client_sock):
    try:
        header = client_sock.recv(2)
        if len(header) < 2:
            return None
        opcode = header[0] & 0x0F
        if opcode == 8:  # close
            return None
        masked = (header[1] & 0x80) != 0
        length = header[1] & 0x7F
        if length == 126:
            length = struct.unpack(">H", client_sock.recv(2))[0]
        elif length == 127:
            length = struct.unpack(">Q", client_sock.recv(8))[0]
        if masked:
            mask = client_sock.recv(4)
            data = bytearray(client_sock.recv(length))
            for i in range(len(data)):
                data[i] ^= mask[i % 4]
            return data.decode("utf-8")
        return client_sock.recv(length).decode("utf-8")
    except:
        return None

def ws_send(client_sock, msg):
    try:
        data = msg.encode("utf-8")
        length = len(data)
        if length <= 125:
            header = bytes([0x81, length])
        elif length <= 65535:
            header = bytes([0x81, 126]) + struct.pack(">H", length)
        else:
            header = bytes([0x81, 127]) + struct.pack(">Q", length)
        client_sock.sendall(header + data)
        return True
    except:
        return False

# --- Game Rooms ---
rooms = {}

class Room:
    def __init__(self, rid):
        self.rid = rid
        self.players = []   # (socket, color)
        self.fen = STARTING_FEN

    def broadcast(self, msg):
        txt = json.dumps(msg)
        dead = []
        for sock, _ in self.players:
            if not ws_send(sock, txt):
                dead.append(sock)
        for s in dead:
            self.players = [(sock, c) for sock, c in self.players if sock != s]

def handle_client(client_sock, addr):
    try:
        data = b""
        while b"\r\n\r\n" not in data:
            chunk = client_sock.recv(1024)
            if not chunk:
                return
            data += chunk
        request = data.decode("utf-8", errors="replace")

        # Check if WebSocket upgrade
        if "Upgrade: websocket" not in request:
            client_sock.close()
            return

        # Get room ID from URL
        room_id = "default"
        for line in request.split("\r\n"):
            if line.startswith("GET"):
                path = line.split()[1]
                if "/" in path[1:]:
                    room_id = path.strip("/").split("/")[-1] or "default"
                break

        ws_handshake(client_sock, request)

        if room_id not in rooms:
            rooms[room_id] = Room(room_id)
        room = rooms[room_id]

        if len(room.players) >= 2:
            ws_send(client_sock, json.dumps({"type": "error", "msg": "Room full"}))
            client_sock.close()
            return

        color = "white" if len(room.players) == 0 else "black"
        room.players.append((client_sock, color))

        ws_send(client_sock, json.dumps({
            "type": "connected",
            "color": color,
            "fen": room.fen,
            "roomId": room_id
        }))

        if len(room.players) == 2:
            room.broadcast({"type": "game_start", "fen": room.fen})

        while True:
            msg = ws_recv(client_sock)
            if msg is None:
                break
            try:
                data = json.loads(msg)
                if data.get("type") == "move":
                    # Forward move to opponent
                    response = dict(data)
                    response["type"] = "opponent_move"
                    for sock, c in room.players:
                        if sock != client_sock:
                            ws_send(sock, json.dumps(response))
                elif data.get("type") == "fen_update":
                    room.fen = data.get("fen", room.fen)
                elif data.get("type") == "chat":
                    room.broadcast({"type": "chat", "msg": data.get("msg", ""), "color": color})
            except:
                pass

    except Exception as e:
        pass
    finally:
        try:
            room = None
            for rid, r in list(rooms.items()):
                if any(s == client_sock for s, _ in r.players):
                    room = r
                    r.players = [(s, c) for s, c in r.players if s != client_sock]
                    if len(r.players) == 0:
                        del rooms[rid]
                    else:
                        r.broadcast({"type": "opponent_left"})
                    break
        except:
            pass
        try:
            client_sock.close()
        except:
            pass

def run_ws_server(host="0.0.0.0", port=8765):
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((host, port))
    server_sock.listen(10)
    print(f"✅ WebSocket server: ws://localhost:{port}")
    while True:
        client, addr = server_sock.accept()
        t = threading.Thread(target=handle_client, args=(client, addr), daemon=True)
        t.start()

def run_http_server(port=8080):
    os.chdir(os.path.join(os.path.dirname(__file__), "client"))
    handler = SimpleHTTPRequestHandler
    handler.log_message = lambda *a: None
    httpd = HTTPServer(("0.0.0.0", port), handler)
    print(f"✅ Game client:    http://localhost:{port}")
    httpd.serve_forever()

if __name__ == "__main__":
    print("\n" + "="*50)
    print("  ⚔️  KURUKSHETRA — Epic Chess  ⚔️")
    print("="*50)
    t = threading.Thread(target=run_ws_server, daemon=True)
    t.start()
    run_http_server()
