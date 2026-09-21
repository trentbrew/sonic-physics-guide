# Forces Subtopic: Underwater Physics & Buoyancy

> **Source:** [SPG:Underwater](https://info.sonicretro.org/SPG%3AUnderwater)

[← Forces Subtopic: Rebounding & Boss Impact](rebound.md) | [Index](../../README.md) | [Forces Subtopic: Speed Shoes, Super & Hyper Sonic Speeds →](super-speeds.md)

---

Player lasts 30 seconds before drowning underwater. **remaining_air** starts at 30 upon entering water. This value represents the amount of seconds of air the Player has left. Meanwhile, a timer counts down from 60 each second. Each time this timer reaches 0, the "air event" occurs:

#### Air Check

| **remaining_air** | Action |
| --- | --- |
| *25, 20, 15* | Warning chime plays. |
| *12* | Drowning music begins. |
| *12, 10, 8, 6, 4, 2* | Countdown bubble is emitted (numbers 5 to 0). |
| Below *0* | Sonic drowns. |

#### Small Breathing Bubbles

Small breathing bubbles spawn at ***Player X*** + 6 (minus when facing left) and at the ***Player Y***. There is a chance a second bubble will spawn randomly between 1 to 16 frames later.

**Notes:**

- *The sine movement of the bubble is adjusted based on the way the Player is facing to ensure the bubble begins by moving away from the Player's mouth.*
- *When moving through a water tunnel like those in Labyrinth Zone, the small breathing bubbles that spawn will move to the right by 4 pixels per frame.*
- *In [Sonic 3](https://info.sonicretro.org/Sonic_3), These bubbles specifically move up twice as fast as the bubbles that come from the [Bubble generator object](../13-game-objects.md#air_bubble_maker).*

### Count Down Warning

If at the current *air event* a countdown bubble is to be emitted, this countdown bubble will be spawned as if it were one of the small breathing bubbles from the Player's mouth.

If 2 small bubbles are emitted, there is a 25% chance the first will be the countdown bubble, otherwise the second is.

When on of these are spawned, they act like a normal breathing bubble until a frame before the number forms from the bubble. After this point, their position gets locked in place and stays on screen until the animation ends.

```c
var origin = Vector2.ZERO;
if (frame is before the number forming) {
	// Normal bubble movement code goes here.
} else {
	if (frame is when the number is forming) origin = position - camera.position; // Distance between object and camera in world space.
	position = camera.position + origin;
	// Stick objects position to the camera, so that its always present on screen.
}
```

The frame duration of countdown bubbles is 5 frames per sub-frame. The fully formed number will appear 4 times before the animation ends.

### Large Air Bubbles

When a large air bubble is breathed, the Player's **remaining_air** is reset to *30* and the timer is reset to 60. Any drowning music is cancelled.
Note:

- *For the collision and mechanics of bubbles, see [Game Objects](../13-game-objects.md#large_air_bubble).*

### Water Entry and Exit

When the Player enters the water, ***X Speed*** is divided by *2*, and ***Y Speed*** by *4*, occurring after *gravity_force* is added.

When the Player exits the water, A few check happen before speeds are altered.
If the player isn't currently being knocked back from taking damage, Player isn't being controlled by another object, and ***Y Speed*** is more than *-4*, ***Y Speed*** is doubled. ***X Speed*** is *not* affected when leaving the water.

> [!NOTE]
> ***Control Flags*** have to be disabled for both **Entry and Exit**.

Also, if the Player's ***Y Speed*** is less than *-16* it will be limited to *-16* upon exiting.

| Constants | Value |
| --- | --- |
| acceleration_speed | - |
| deceleration_speed | - |
| friction_speed | - |
| top_speed | - |
| air_acceleration_speed | - |
| roll_friction_speed | - |
| roll_deceleration_speed | 0.125 (unchanged) |
| gravity_force | - |
| jump_force | - |
| jump_release | - |

> [!NOTE]
> "-" means halved. [Speed Shoes](https://info.sonicretro.org/Speed_Shoes) doesn't affect speeds while underwater.

### Getting Hit

When [getting hit](getting-hit.md) underwater, the Player will fly back with an ***X Speed*** of *1* (or *-1*) and a ***Y Speed*** of *-2*, half that of normal.

### Bubbles

When the Player gets a bubble underwater, ***X and Y Speed*** is set to *0*.

## Drowning

When the Player drowns, ***X and Y Speed*** is set to *0*, and the *gravity_force* remains set to the lower water gravity.

### Drowning Bubbles

When drowning, 11 bubbles are created from the Player's mouth as they fall offscreen.
The first bubble can spawn from 0 to 15 frames after drowning, chosen at random. Subsequent bubbles spawn 1 to 8 frames apart, also chosen at random.

Each of the 11 bubbles has a quarter chance of being a medium bubble, otherwise it will be a small bubble.

## Animation Speeds

Being submerged doesn't affect the speed of the Player's animations at all. [Variable Speed Animations](../21-animations.md#variable_speed_animation_timings) will be attenuated by the same proportion automatically.

---

[← Forces Subtopic: Rebounding & Boss Impact](rebound.md) | [Index](../../README.md) | [Forces Subtopic: Speed Shoes, Super & Hyper Sonic Speeds →](super-speeds.md)
