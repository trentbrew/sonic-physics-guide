# Sonic Physics Guide (SPG) Documentation

This repository contains a complete, offline-ready Markdown documentation suite for the **Sonic Physics Guide** from [Sonic Retro](https://info.sonicretro.org/Sonic_Physics_Guide).

The Sonic Physics Guide is the canonical reference detailing the exact mathematical models, object logic, terrain collision, slopes, angle systems, subpixel math, and frame-by-frame simulation used across classic Sega Genesis Sonic games (*Sonic the Hedgehog 1, Sonic the Hedgehog 2, Sonic CD, and Sonic the Hedgehog 3 & Knuckles*).

---

## Guide Conventions

| Concept | Specification | Description |
| --- | --- | --- |
| **Coordinate System** | Origin (0,0) Top-Left | X increases rightward, Y increases downward. |
| **Units** | Pixels & Subpixels | 1 Pixel = 256 Subpixels (range 0–255). |
| **Angle System** | Hex Angles (0–255) / Degrees | 0 = Right, 64 = Down, 128 = Left, 192 = Up (clockwise in Genesis hex, counter-clockwise in math notation). |
| **Target Framerate** | 60 FPS (NTSC) | Physics speeds and accelerations are applied per frame at 60 Hz. |
| **Collision Basis** | Whole Pixels | Subpixels are discarded during collision sensor tests. |

---

## Table of Contents

### 1. Core Mechanics
- **[00. Guide Overview](docs/00-overview.md)** - Introduction, purpose, and engine architecture.
- **[01. Basics](docs/01-basics.md)** - Hexadecimal, data types, **Objects** (variables, collision radius, hitboxes), level map hierarchy (Cells, Blocks, Chunks), subpixel math, angles, and framerates.
- **[02. Calculations](docs/02-calculations.md)** - Angle range classifications, sine/cosine conversion, fixed-point subpixel arithmetic.
- **[03. Characters](docs/03-characters.md)** - Physics attribute comparison between Sonic, Tails, and Knuckles.

### 2. Collision System
- **[04. Terrain Collision](docs/04-terrain-collision.md)** - Solid tile format, 16x16 block collision arrays, angle arrays, sensor probes.
- **[05. Terrain Interaction](docs/05-terrain-interaction.md)** - Collision layer switching, 360° vertical loop traversal mechanics.
- **[06. Slope Collision](docs/06-slope-collision.md)** - Sensor positioning (A, B, C, D, E, F), grounded slope snapping, wall pushers, airborne landing.
- **[07. Hitboxes](docs/07-hitboxes.md)** - Player interaction hitboxes vs. terrain radius boxes, item triggers, hurtboxes.
- **[08. Solid Objects](docs/08-solid-objects.md)** - Moving platforms, sloped objects, jump-through platforms, pushable blocks, item monitors.

### 3. Physics & Forces
- **[09. Slope Physics](docs/09-slope-physics.md)** - Slope factor acceleration, sliding thresholds, fall-off speeds, wall/ceiling adhesion.
- **[10. Forces & Movement](docs/10-forces.md)** - Master physics table: acceleration, deceleration, top speed, jumping, rolling, damage rebound, and water entry.
- **Forces Deep Dives:**
  - **[Air State](docs/11-forces-subtopics/air-state.md)** - Midair speed transitions, air acceleration, drag.
  - **[Jumping](docs/11-forces-subtopics/jumping.md)** - Jump impulse values, variable height cutoff logic.
  - **[Rolling](docs/11-forces-subtopics/rolling.md)** - Rolling friction, slope assist, rolling jump behavior.
  - **[Getting Hit](docs/11-forces-subtopics/getting-hit.md)** - Knockback trajectory, ring scatter triggers, invulnerability timers.
  - **[Rebound](docs/11-forces-subtopics/rebound.md)** - Badnik bounce-back and boss impact recoil.
  - **[Underwater](docs/11-forces-subtopics/underwater.md)** - Water physics dampening, buoyancy, gravity reduction.
  - **[Super Speeds](docs/11-forces-subtopics/super-speeds.md)** - Speed Shoes multiplier and Super/Hyper Sonic constants.

### 4. Gameplay Logic
- **[12. Main Game Loop](docs/12-main-game-loop.md)** - Frame execution order: Player control -> Object routine -> Collision -> Camera -> V-INT.
- **[13. Game Objects](docs/13-game-objects.md)** - Springs (vertical, horizontal, diagonal), Spikes, Rings, Item Monitors, Bumpers, Starposts.
- **[14. Game Enemies](docs/14-game-enemies.md)** - Badnik archetypes (Motobug, Chopper, Buzz Bomber, Crabmeat) and Boss logic.
- **[15. Ring Loss](docs/15-ring-loss.md)** - Ring scatter angle distribution, bouncing physics, collection lockout delay.
- **[16. Special Abilities](docs/16-special-abilities.md)** - Spindash, Super Peel Out, Drop Dash, Insta-Shield, Tails Flight/Swim, Knuckles Glide & Climb.
- **[17. Elemental Shields](docs/17-elemental-shields.md)** - Flame Shield (Fire Dash), Bubble Shield (Bounce Attack), Lightning Shield (Double Jump).
- **[18. Player 2 Logic](docs/18-player-2.md)** - Tails CPU companion AI, follow pathing, respawning flight.
- **[19. Special Stages](docs/19-special-stages.md)** - Sonic 1 360° rotating maze physics, bumper grid, goal triggers.

### 5. Presentation & Diagnostics
- **[20. Camera](docs/20-camera.md)** - Scrolling boundaries, look up/down delays, speed lag margins.
- **[21. Animations](docs/21-animations.md)** - Sprite animation scripts, frame duration formulas based on player speed.
- **[22. Overlay Scripts](docs/22-overlay-scripts.md)** - Gens/Lua diagnostic overlays for real-time sensor and speed monitoring.

---

## Quick Reference: Physics Constants (Sonic 1 / 2 / 3&K)

| Constant | Normal Value (Hex / Dec) | Underwater Value | Description |
| --- | --- | --- | --- |
| `acc` | `0x000C` (12 spx / 0.046875 px/frame) | `0x0006` (6 spx) | Acceleration per frame while holding direction |
| `dec` | `0x0080` (128 spx / 0.5 px/frame) | `0x0040` (64 spx) | Deceleration per frame when braking against motion |
| `frc` | `0x000C` (12 spx / 0.046875 px/frame) | `0x0006` (6 spx) | Friction per frame when coasting without input |
| `top` | `0x0600` (1536 spx / 6.0 px/frame) | `0x0300` (768 spx) | Normal maximum running speed on flat ground |
| `jmp` | `0x0680` (6.5 px/frame) / Knux `0x0600` | `0x0380` (3.5 px/frame) | Initial upward velocity applied on jump press |
| `grv` | `0x0038` (56 spx / 0.21875 px/frame) | `0x0010` (16 spx) | Downward acceleration applied each frame while airborne |
| `slp` | `0x0020` (32 spx / 0.125 px/frame) | `0x0020` (32 spx) | Slope factor added to Ground Speed when running on slopes |

---

## Updating the Documentation

To re-fetch and re-generate this documentation suite:

```bash
python3 scripts/scraper.py
```
