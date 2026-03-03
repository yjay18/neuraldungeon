# Neural Dungeon

A top-down bullet hell roguelike dungeon crawler where **the dungeon IS a neural network**.

You are a hacker trapped inside a rogue AI's mind. Each floor is a network layer, rooms are neurons, corridors are weighted connections, and the AI adapts to your playstyle by updating its weights — literally reshaping the dungeon.

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Run the game
python -m neural_dungeon

# Run tests
pytest

# Build .exe
python build_exe.py
```

## Controls

| Key | Action |
|-----|--------|
| WASD | Move |
| Arrow Keys | Aim |
| J / Enter | Shoot |
| Space | Dodge Roll |
| E / Enter | Proceed (when room cleared) |
| Q | Quit |

## Project Structure

- `neural_dungeon/` — Game source code
  - `main.py` — Game loop and state machine
  - `config.py` — All constants and tuning parameters
  - `entities/` — Player, enemies, projectiles, items
  - `combat/` — Damage, collision, bullet patterns
  - `world/` — Rooms, floors, map generation
  - `render/` — Terminal renderer (blessed)
  - `network/` — PyTorch DungeonNet (Phase 2)
  - `adaptive/` — AI adaptation system (Phase 6)
  - `persistence/` — Save system (Phase 7)

## Development Phases

See `context.md` for the full checklist and design decisions.
