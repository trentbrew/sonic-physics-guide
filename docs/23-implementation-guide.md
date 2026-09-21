# Engine Implementation Guide & AI Agent Blueprint

This guide provides practical architectural guidance, critical engineering pitfalls, and a ready-to-use AI agent prompt for implementing a 100% faithful classic Sonic physics engine using the documentation in this repository.

---

## 1. Architectural Principles

Unlike modern platformers that rely on general-purpose rigid-body physics engines (such as Box2D, Unity Rigidbody2D, or PhysX), classic Sega Genesis Sonic is a **deterministic state machine driven by a 6-sensor raycast automaton**.

```text
              [ Sensor C ]     [ Sensor D ]          <- Ceiling Probes (Inverted)
                   |                |
                   v                v
            +------------------------------+
 [Sensor E] |                              | [Sensor F]
(Left Wall) |         Origin (X, Y)        | (Right Wall)
            |                              |
            +------------------------------+
                   ^                ^
                   |                |
              [ Sensor A ]     [ Sensor B ]          <- Ground Probes (Floor)
```

### Core Invariants

1. **Discrete 60 Hz Simulation Ticks:**  
   The Genesis engine does **not** use floating-point delta time (`x += speed * dt`). All speeds and accelerations are fixed values added once per frame at 60 Hz.
2. **Fixed-Point Subpixel Units:**  
   Positions and speeds operate in 16-bit or 24-bit fixed-point arithmetic where **1 pixel = 256 subpixels** (range `0x00`–`0xFF`). Subpixels are discarded during collision probe tests (whole pixel snapping).
3. **Hex Angle System (0–255):**  
   Angles are stored as 1-byte integers from `0` to `255` (`0x00` to `0xFF`), progressing clockwise in Genesis hardware (`0` = Right, `64` = Down, `128` = Left, `192` = Up).
4. **Asymmetric Execution Order:**  
   Wall push sensors are evaluated **before** position update; ground floor sensors are evaluated **after**. This timing asymmetry prevents high-speed clipping into walls.

---

## 2. The 3 Critical Implementation Traps

### Trap 1: Variable Delta Time (The "Float Drift" Bug)

* **The Problem:** Modern engines commonly multiply movement by `deltaTime` (e.g. `x += speed * dt`). In Sonic's engine, friction, acceleration, deceleration quirks, and jump height cutoffs are integer subtractions hardcoded to single-frame ticks. Using variable `dt` makes Sonic accelerate too fast on high-refresh displays (144 Hz) or feel sluggish at 30 Hz.
* **The Solution:** Use a **fixed-timestep accumulator** loop running strictly at 60 Hz (16.666 ms per tick). Render with interpolation between the previous and current state if necessary.

```typescript
const TICK_RATE = 1 / 60;
let accumulator = 0;

function update(deltaTime: number) {
  accumulator += deltaTime;
  while (accumulator >= TICK_RATE) {
    physicsTick(); // Execute exact Genesis 60 Hz tick
    accumulator -= TICK_RATE;
  }
}
```

---

### Trap 2: Tunneling and Wall Clipping at High Speeds

* **The Problem:** At top speed (or when launched by diagonal springs), Sonic can move 16 to 24 pixels in a single frame. Because tile height masks are only 16 pixels wide, Sensors A and B can completely leap over a solid block or slope transition in a single tick.
* **The Solution:** Follow the Genesis clamp and push rules from [06-slope-collision.md](06-slope-collision.md):
  1. Wall Push Sensors E and F must be evaluated *prior* to updating `X` and `Y` position. If a wall is hit, set `Ground_Speed = 0` immediately and offset the position before floor probes run.
  2. Ground sensors check a dynamic downward reach window:  
     $$\text{Snap Range} = \min(|X\_Speed| + 4,\, 14)$$  
     The faster Sonic moves along a slope, the deeper the sensor probes ahead to prevent launching off downward hills.

---

### Trap 3: Concave Mode Jitter (Infinite Quadrant Flipping)

* **The Problem:** When running up a concave curve (such as transitioning from flat ground into a vertical 360° loop), Sonic's angle approaches 45°. If the Floor and Wall collision modes share an exact 45° boundary, the engine can oscillate back and forth between Floor mode and Right Wall mode every single frame, causing Sonic to vibrate or stall.
* **The Solution:** Respect the **overlapping hysteresis angle thresholds** documented in [06-slope-collision.md](06-slope-collision.md#grounded):

| Mode | Floor Sensor Range | Wall Push Sensor Range | Offset Applied |
| :--- | :--- | :--- | :--- |
| **Floor** | `315° (224)` to `45° (32)` | `316° (223)` to `44° (31)` | $(X,\, Y)$ |
| **Right Wall** | `46° (33)` to `134° (95)` | `45° (32)` to `135° (96)` | $(Y,\, -X)$ |
| **Ceiling** | `135° (96)` to `225° (160)` | `136° (97)` to `224° (159)` | $(X,\, -Y)$ |
| **Left Wall** | `226° (161)` to `314° (223)` | `225° (160)` to `315° (224)` | $(-Y,\, X)$ |

The Push Sensors use slightly wider boundaries than Floor Sensors. This intentional overlap creates hysteresis, eliminating mode oscillation on curved terrain.

---

## 3. The AI Agent Engine Prompt

Copy and paste the prompt below to direct an AI coding assistant (or agent) to implement a playable, Genesis-accurate Sonic physics controller:

````markdown
You are an expert retro game engine developer. Your task is to build a pixel-perfect, 
deterministic 2D Sonic physics controller based strictly on the classic Sega Genesis 
specifications documented in the Sonic Physics Guide.

### Target Tech Stack:
- Single-file HTML5 Canvas + TypeScript (or vanilla ES6 JavaScript)
- No external physics engines (do NOT use Box2D, Matter.js, or Phaser Arcade Physics)
- 60 Hz fixed-timestep game loop

### Specifications to Follow:
1. Coordinate & Units:
   - Coordinate origin (0,0) is top-left.
   - Implement fixed-point arithmetic: 1 pixel = 256 subpixels.
   - Sensor collision must occur at the integer pixel boundary (discard subpixels for raycasts).

2. 6-Sensor Collision Automaton:
   - Sensors A & B (Ground/Feet): Probe downward into 16x16 block height arrays.
   - Sensors C & D (Ceiling/Head): Active airborne and when jumping.
   - Sensors E & F (Walls/Pushers): Positioned at (Push Radius, 0) relative to center.
   - Implement the 4 collision quadrant modes (Floor, Right Wall, Ceiling, Left Wall) 
     with overlapping hysteresis thresholds as specified in docs/06-slope-collision.md.

3. Constants (Sonic 1 / Sonic 2 normal ground):
   - Acceleration: 12 spx (0.046875 px/frame)
   - Deceleration: 128 spx (0.5 px/frame)
   - Friction: 12 spx (0.046875 px/frame)
   - Top Speed: 1536 spx (6.0 px/frame)
   - Jump Force: 6.5 px/frame (6px 128spx)
   - Gravity: 56 spx (0.21875 px/frame)
   - Slope Factor: 32 spx (0.125 px/frame)

4. Key Mechanics & Edge Cases:
   - Deceleration snap: When braking drops speed past 0, snap directly to -0.5 px/frame in reverse.
   - Wall Push Timing: Push sensors must run BEFORE position updates; floor sensors run AFTER.
   - Variable Jump Height: When jump button is released mid-ascent, cap Y speed at -4.0 px/frame.
   - Slope Slipping: On slopes > 45° (hex angles 32–96 or 160–224), if |Ground Speed| < 2.5 px/frame, 
     detach from surface, set airborne state, and lock horizontal control for 30 frames.
   - Rolling: Down + Action transitions to roll state with reduced friction (6 spx) and slope assist.

5. Test Environment:
   - Create a test course featuring: flat terrain, a 30° gentle slope, a steep 45° curve, 
     and a full 360° vertical loop-de-loop with collision layer switching.
   - Render diagnostic sensor points (Sensors A–F) and velocity vectors over Sonic.
````

---

## 4. Character Sprite Assets

The complete original Sega Genesis *Sonic the Hedgehog 1* character spritesheet is preserved locally in the [`images/`](../images/) directory:

- **Transparent Alpha PNG:** [`images/Sonic1_Spritesheet_Transparent.png`](../images/Sonic1_Spritesheet_Transparent.png) (Ready for canvas/engine rendering)
- **Original Chroma-Keyed PNG:** [`images/Sonic1_Spritesheet.png`](../images/Sonic1_Spritesheet.png)

```text
Row 1: Idle stance, foot tap impatience, walk animation cycle (frames 1–6)
Row 2: Jog & run animation cycle (frames 1–4)
Row 3: Full-speed Peel-Out sprint cycle, rolling ball frames (1–5)
Row 4: Skid/braking, looking up, ducking/crouching, pushing against walls
Row 5: Balancing on ledges (shallow and steep), spring bounce recoil
Row 6: Hurt knockback, drowning, breathing air bubbles, victory pose
```

See [docs/21-animations.md](21-animations.md) for the exact frame delay calculation formulas used to scale animation speeds to Sonic's actual running velocity.
