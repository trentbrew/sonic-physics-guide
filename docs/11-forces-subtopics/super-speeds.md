# Forces Subtopic: Speed Shoes, Super & Hyper Sonic Speeds

> **Source:** [SPG:Super Speeds](https://info.sonicretro.org/SPG%3ASuper_Speeds)

[← Forces Subtopic: Underwater Physics & Buoyancy](underwater.md) | [Index](../../README.md) | [Main Game Loop: Execution Order per Frame →](../12-main-game-loop.md)

---

## Super Fast Shoes

| Variable | Value |
| --- | --- |
| Acceleration | 0.09375 |
| Deceleration | 0.5 (unchanged) |
| Friction | 0.09375 |
| Top Speed | 12 |
| Air Acceleration | 0.1875 |
| Rolling Friction | 0.046875 |
| Rolling Deceleration | 0.125 (unchanged) |

> [!NOTE]
> Underwater variables override Speed Shoes completely. If you jump back out of the water, the Super Fast Shoes stay gone. This is the case for all 5 games.

In Sonic 3 & Knuckles, the tempo of the song is multiplied by 1.25.

## Super/Hyper Sonic

| Variable | Value | Value (Underwater) |
| --- | --- | --- |
| Acceleration | 0.1875 | 0.09375 |
| Deceleration | 1 | 0.5 |
| Friction | 0.046875 (unchanged) | 0.046875 (unchanged) |
| Top Speed | 10 | 5 |
| Air Acceleration | 0.375 | 0.1875 |
| Initial Jump Velocity | 8 (unchanged for Knuckles only) | 3.5 (unchanged) |
| Release Jump Velocity | 4 (unchanged) | 2 (unchanged) |
| Rolling Friction | 0.09375 (0.0234375 in Sonic 3 & K) | 0.046875 (0.0234375 in Sonic 3 & K) |
| Rolling Deceleration | 0.125 (unchanged) | 0.125 (unchanged) |

### Ring Countdown

Every second, *1* Ring is taken away while **Super/Hyper**.

### Hyper Blast Ability (Hyper Sonic Only)

When you press the jump button a second time in the air, X speed is set to **8** (**-8** facing left), and Y speed is set to **0**.  If you were holding Up on the D-pad, Sonic's Y speed is set to **-8**, and X speed is set to **0** instead.

## Super Tails, Super/Hyper Knuckles

| Variable | Value | Value (Underwater) |
| --- | --- | --- |
| Acceleration | 0.09375 | 0.046875 |
| Deceleration | 0.75 | 0.375 |
| Friction | 0.046875 (unchanged) | 0.046875 (unchanged) |
| Top Speed | 8 | 4 |
| Air Acceleration | 0.1875 | 0.09375 |
| Initial Jump Velocity | (unchanged) | (unchanged) |
| Release Jump Velocity | (unchanged) | (unchanged) |
| Rolling Friction | 0.0234375 | 0.0234375 |
| Rolling Deceleration | 0.125 (unchanged) | 0.125 (unchanged) |
| Climbing Speed *(Knuckles only)* | 2 | 2 |
| Gliding Initial Speed *(Knuckles only)* | 4 (unchanged) | 4 (unchanged) |
| Gliding Acceleration *(Knuckles only)* | 0.046875 | 0.046875 |

### Wall Quake (Hyper Knuckles Only)

If **X Speed** is more/equal to **4.5**, the screen will shake when connecting to a wall from gliding.

**Notes:**

- Speed Shoes supersede **Super/Hyper** variables, in effect slowing them down.
- If a character turns **Super/Hyper** while underwater, they incorrectly use their above water speeds.

---

[← Forces Subtopic: Underwater Physics & Buoyancy](underwater.md) | [Index](../../README.md) | [Main Game Loop: Execution Order per Frame →](../12-main-game-loop.md)
