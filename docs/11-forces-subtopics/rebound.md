# Forces Subtopic: Rebounding & Boss Impact

> **Source:** [SPG:Rebound](https://info.sonicretro.org/SPG%3ARebound)

[← Forces Subtopic: Getting Hit & Invulnerability Frames](getting-hit.md) | [Index](../../README.md) | [Forces Subtopic: Underwater Physics & Buoyancy →](underwater.md)

---

When the Player destroys an object in the air, the game checks to see if they should rebound or not.

If `Player Y Speed < Object Y Speed && Player Y Speed >= 0`, ***Y Speed*** is reversed. `sign(Y Speed)` is subtracted from ***Y Speed*** (e.g. *0.25 (64spx)* -> *-0.75 (-192spx)*) if this isn't the case, giving a bit of weight when hit from below.

> [!NOTE]
> for **Item Monitors**, ***Y Speed*** is always reversed.

## Bosses

***X and Y Speed*** is multiplied by *-0.5*. ***Ground Speed*** is not affected.

> [!NOTE]
> [Variable Jump Height](jumping.md#variable_jump_height) is still in effect, as it's a part of the Player's code.

---

[← Forces Subtopic: Getting Hit & Invulnerability Frames](getting-hit.md) | [Index](../../README.md) | [Forces Subtopic: Underwater Physics & Buoyancy →](underwater.md)
