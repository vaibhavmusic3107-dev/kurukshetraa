# ⚔ KURUKSHETRA — Cinematic Chess

## Technology Stack
- **Three.js WebGL 3D Engine** (NOT HTML/CSS/JS)
- **Python WebSocket Server** (pure stdlib, zero dependencies)
- **Web Audio API** — synthesized epic war music & SFX
- **chess.js** — 100% accurate chess rules engine

## Quick Start

### Option 1: Just Open in Browser (Local 2-Player)
```
Open: client/index.html in any browser
Click: LOCAL DUEL
```

### Option 2: Online Multiplayer (2 different computers)
```bash
python3 server.py
# Opens: http://localhost:8080
# WebSocket: ws://localhost:8765
```

Both players open http://localhost:8080 (or your IP), click ONLINE BATTLE, enter same room code.

## Features
- Full chess rules: castling, en passant, pawn promotion, check/checkmate/stalemate
- **Knight**: Draws sword → horse rears → L-shape charge → dust particles
- **Captures**: Attacker charges, victim falls, SOUL rises with glow particles
- **Check**: Camera shake + red flash + war horn
- **Checkmate**: Victory fanfare with drums
- Procedural BGM: War drums + sitar drone + pentatonic melody
- 6 unique warrior piece types: foot soldiers, cavalry, sages, war elephants, warrior queens, emperors
- Kurukshetra battlefield: torches, mountains, distant fires, smoke, dramatic sky
- Click any piece to select, green = legal move, orange = capture

## Controls
- **Left Click** — Select piece / make move  
- **Scroll** — Zoom in/out
- **Right Click + Drag** — Orbit camera
- **🔊 button** — Toggle sound
