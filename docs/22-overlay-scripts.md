# Overlay Scripts: Diagnostic HUDs for Sonic 1 & Sonic 2

> **Source:** [SPG:Overlay Scripts](https://info.sonicretro.org/SPG%3AOverlay_Scripts)

[← Animations: Scripts, Variable Speed Timings, and Rules](21-animations.md) | [Index](../README.md)

---

These Lua scripts provide a graphical overlay over the Classic sonic games akin to the images shown across the guide, showing hitboxes, variables, and more. These are built for [Gens' Re-Recording](https://segaretro.org/Gens_Re-Recording) feature, simply open ![Document-Icon.svg](../images/14px-Document-Icon.svg.png) Tools > Lua Scripting > New Lua Script Window in the toolbar and load the lua file for that game.

### Colour Keys

| **[Objects](01-basics.md#objects)** |  |
| --- | --- |
| ⬤ | [Hitboxes](07-hitboxes.md) (color varies based on hitbox type) |
| ⬤ | [Solid Objects](08-solid-objects.md) (color varies based on solidity type) |
| ⬤ | Width/Height Radii |
| ⬤ | [Trigger Areas](07-hitboxes.md#trigger_areas) |

| **[Solid Tiles](04-terrain-collision.md)/[Terrain](05-terrain-interaction.md)** |  |
| --- | --- |
| **Up, Down, Left, & Right** | Solid Tile [Sensors](04-terrain-collision.md#sensors) |
| ⬤ | Fully Solid |
| ⬤ | Top Solid only |
| ⬤ | Sides & Bottom Solid only |
| "*" | [Flagged](04-terrain-collision.md#flagged_tiles) Tiles |

### Key Bindings

| **General** |  |
| --- | --- |
| **Q** | Toggle overlay |
| **W** | Toggle shortcut list |
| **E** | Toggle player variables |
| **R** | Change darkness |
| **T** | Toggle camera bounds |
| **Y** | Toggle hex values |
| **U** | Change terrain/angle display |

| **Objects** |  |
| --- | --- |
| **I** | Toggle hitboxes |
| **O** | Toggle trigger areas |
| **P** | Toggle sensors |
| **F** | Toggle solidity |
| **G** | Toggle width/height radii |
| **H** | Toggle object info (like name and id) |
| **J** | Toggle smoothing effect |

| **Sonic the Hedgehog 2** |  |
| --- | --- |
| **K** | Toggle terrain layer display |

### Things to note

- Most collision events don't always happen after an object moves, resulting in boxes/sensors appearing to lag behind as they move. The "smoothing" option draws information where the object **appears** onscreen, rather than where the collision actually happened, although this is a less accurate representation of the process. This also messes with the player's wall sensors, as they extend  to match up with the player's position before it's actually updated.
- Sensor lines only indicates it's direction, the white dot is where the collision actually takes place.
- The special stages have been avoided since there is limited revealing information to be shown there.

### Sonic the Hedgehog (REV01)

| ![Download.svg](../images/35px-Download.svg.png) | [Download SPG:Overlay Scripts](https://info.sonicretro.org/images/2/26/SPGSonic1Rev01Overlay.lua) **File:** SPGSonic1Rev01Overlay.lua (72 kB) ([info](https://info.sonicretro.org/File:SPGSonic1Rev01Overlay.lua))<br> **Current version:** 2.2 |
| --- | --- |

### Sonic the Hedgehog 2 (Final)

| ![Download.svg](../images/35px-Download.svg.png) | [Download SPG:Overlay Scripts](https://info.sonicretro.org/images/6/68/SPGSonic2Overlay.Lua) **File:** SPGSonic2Overlay.Lua (103 kB) ([info](https://info.sonicretro.org/File:SPGSonic2Overlay.Lua))<br> **Current version:** 1.1 |
| --- | --- |

---

[← Animations: Scripts, Variable Speed Timings, and Rules](21-animations.md) | [Index](../README.md)
