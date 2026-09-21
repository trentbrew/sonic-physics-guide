# Ring Loss: Scatter Trajectories, Speeds, and Timers

> **Source:** [SPG:Ring Loss](https://info.sonicretro.org/SPG%3ARing_Loss)

[← Game Enemies: Badniks and Bosses Mechanics](14-game-enemies.md) | [Index](../README.md) | [Special Abilities: Spindash, Peel Out, Drop Dash, Flight, Glide →](16-special-abilities.md)

---

**Notes:**

- *The research applies to all four of the [Sega Mega Drive](https://info.sonicretro.org/Sega_Mega_Drive) games and [Sonic CD](https://info.sonicretro.org/Sonic_CD).*
- *For the behaviour & movement of scattered Ring objects themselves, see [Game Objects](13-game-objects.md#scattered_rings).*

## Ring Limit

When the Player gets hit, the number of [rings](https://info.sonicretro.org/Rings) they are carrying scatter away, unless they are carrying more than 32, in which case any rings over 32 are ignored. The Player is therefore no safer carrying 100 rings than 32.

## Ring Distribution

The rings that scatter away from the Player are distributed in a specific pattern of 2 concentric circles, each containing a maximum of 16 rings.  The rings in the first circle move outward faster than the rings in the second.
Here is example code for creating the rings, which can be converted into the programming language of your choice:

```c
// Variables and Constants
var ring_counter = 0;
var ring_starting_angle = 101.25° (184) ($B8);
var ring_angle = ring_starting_angle;
var ring_flip = false;
var ring_speed = 4;

// Perform loop while the ring counter is less than number of lost rings
while ring_counter < number of rings (max 32)
{
    // Create the ring
    create a bouncing ring object at the Player's X and Y Position;
    ring's X Speed = cosine(ring_angle) * ring_speed;
    ring's Y Speed = -sine(ring_angle) * ring_speed;

    // Every ring created will moving be at the same angle as the other in the current pair, but flipped the other side of the circle
    if ring_flip == true
    {
        ring's X Speed = ring's X Speed * -1;  // Reverse ring's X Speed
        ring_angle += 22.5° (16) ($10);  // We increment angle on every other ring which makes 2 even rings either side
    }

    // Toggle flip
    ring_flip = !ring_flip;  // If flip is false, flip becomes true and vice versa

    // Increment counter
    ring_counter += 1;

    // If we are halfway, start second "circle" of rings with lower speed
    if ring_counter == 16
    {
        ring_speed = 2;
        ring_angle = ring_starting_angle;  // Reset the angle
    }
}
```

So, the first 16 rings move at a speed of 4 pixels per frame, and the second 16 move at half that rate, or 2 pixels per frame.

## Regathering Rings

*64* frames must have passed since the Player was hit before they can regather any rings, scattered or otherwise.

## Invulnerability

The Player remains invulnerable for a short time after being hit. This invulnerability lasts while the Player is flying back from the blow, and then *120* frames more after they land and recover movement.  During those *120* frames, they flash on and off, spending *4* frames on and *4* frames off.

While in this state, the Player can not collect level rings until less than *90* invulnerability frames remain.

## Ring Depth

All rings, scattered or fixed, have a higher depth than the Player, i.e. behind them.  But they have a lower depth, i.e. in front of them, when they turn into sparkles.

---

[← Game Enemies: Badniks and Bosses Mechanics](14-game-enemies.md) | [Index](../README.md) | [Special Abilities: Spindash, Peel Out, Drop Dash, Flight, Glide →](16-special-abilities.md)
