# Forces Subtopic: Getting Hit & Invulnerability Frames

> **Source:** [SPG:Getting Hit](https://info.sonicretro.org/SPG%3AGetting_Hit)

[← Forces Subtopic: Rolling Physics & Rolling Jump](rolling.md) | [Index](../../README.md) | [Forces Subtopic: Rebounding & Boss Impact →](rebound.md)

---

## Constants

| Constant | Value |
| --- | --- |
| **hurt_x_force** | *2* |
| **hurt_y_force** | *-4* |
| **hurt_gravity_force** | *0.1875 (48 subpixels)* |

## Getting Hurt

When the Player has rings and collides into a hazard, they are flung backwards and [lose their rings](../15-ring-loss.md). During this special hurt state, the Player becomes [invulnerable](../15-ring-loss.md#invulnerability) for a short time.

At the moment of impact, ***Y Speed*** is always set to **hurt_y_force** and ***X Speed*** is set to `hurt_x_force * sign(Player X Position -Hazard X Position)`.

> [!NOTE]
> sign defaults to *1* if zero.

### Hurt State

While in the hurt state, the only thing applied is **hurt_gravity_force** until they land. Upon landing, ***X Speed*** is set to *0*. The Player cannot leave the hurt state until they land.

In the [Sonic 2 Nick Arcade prototype](https://info.sonicretro.org/Sonic_the_Hedgehog_2_(Nick_Arcade_prototype)), if the Player hits a wall at ***X Speed*** of *6*, they will bounce away with the same physics, they land in a knocked flat animation.

## Dying

When the Player has no rings and touches a harmful object, they will enter a death state. ***X Speed*** is set to **0**, and ***Y Speed*** to **-7**, with normal gravity being applied. No input is read, nor are any collisions detected.

---

[← Forces Subtopic: Rolling Physics & Rolling Jump](rolling.md) | [Index](../../README.md) | [Forces Subtopic: Rebounding & Boss Impact →](rebound.md)
