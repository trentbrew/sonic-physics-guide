# Forces: Physics Values, Running, Jumping, Rolling, and Impact

> **Source:** [SPG:Forces](https://info.sonicretro.org/SPG%3AForces)

[← Slope Physics: Moving, Slipping, 360° Momentum, and Landing](09-slope-physics.md) | [Index](../README.md) | [Forces Subtopic: Air State & Midair Momentum →](11-forces-subtopics/air-state.md)

---

## Physics Values

| **Constants** | Value | Underwater |
| --- | --- | --- |
| **Friction** | 12spx | / |
| **Hurt X Force** | 2px | / |
| **Hurt Y Force** | -4px | / |
| ***-- Rolling --*** |  |  |
| **Roll Deceleration** | 32spx | ***S*** |
| ***-- Airborne --*** |  |  |
| **Gravity** | 56spx | 16spx |
| **Hurt Gravity** | 48spx | 16spx |
| **Top Gravity** *([Sonic CD](https://info.sonicretro.org/Sonic_CD))* | 16px | ***S*** |

| **Normal** | Value | Underwater |
| --- | --- | --- |
| **Acceleration** | 12spx | / |
| **Deceleration** | 128spx | / |
| **Top Speed** | 6px | / |
| **Jump Force** | 6px, 128spx (***Knuckles:*** 6px) | / |
| ***-- Rolling --*** |  |  |
| **Roll Friction** | 6spx | / |
| ***-- Airborne --*** |  |  |
| **Air Acceleration** | 24spx | / |

| **Super/Hyper Sonic** | Value | Underwater |
| --- | --- | --- |
| **Acceleration** | 48spx | / |
| **Deceleration** | 1px | / |
| **Top Speed** | 10px | / |
| **Jump Force** | 8px (***K.T.E:*** 6px) | / |
| ***-- Rolling --*** |  |  |
| **Roll Friction** | 24spx (***S3:*** 6spx) | / (***S3: S***) |
| ***-- Airborne --*** |  |  |
| **Air Acceleration** | 96spx | / |

| **Super/Hyper Tails & Knuckles** | Value | Underwater |
| --- | --- | --- |
| **Acceleration** | 24spx | / |
| **Deceleration** | 192spx | / |
| **Top Speed** | 8px | / |
| ***-- Airborne --*** |  |  |
| **Air Acceleration** | 48spx | / |
| ***-- Knuckles --*** |  |  |
| **Climb Speed** | 2px | ***S*** |
| **Glide Acceleration** | 12spx | ***S*** |

> [!NOTE]
> ***S*** means same, "/" means halved.

## Running

When pressing ![Left](../images/Leftarrow.png) or ![Right](../images/Rightarrow.png), **Ground Speed** is changed by **Acceleration**. If you're pressing in the opposite direction of **Ground Speed**, **Deceleration** is added instead. Whenever **Deceleration** changes the sign of ***Ground Speed***, it's set to *0.5 (128spx)* in the opposite direction. When neither ![Left](../images/Leftarrow.png) or ![Right](../images/Rightarrow.png) is pressed, **Friction** decreases ***Ground Speed*** until it reaches *0*.

> [!NOTE]
> ![Left](../images/Leftarrow.png) subtracts, ![Right](../images/Rightarrow.png) adds. Holding both ![Left](../images/Leftarrow.png) and ![Right](../images/Rightarrow.png) will run both direction's code in one step.

### Top Speed

In *[Sonic 1](https://info.sonicretro.org/Sonic_1)*, if ![Left](../images/Leftarrow.png) or ![Right](../images/Rightarrow.png) is pressed while **Ground Speed** is more than **Top Speed**, it will be set to it. In every game following, **Acceleration** is not applied when **Ground Speed** is more than **Top Speed**.

```c
if (the player is pressing left) {
    if (Ground Speed > 0) {
        Ground Speed -= deceleration_speed;
        if (Ground Speed <= 0) Ground Speed = -0.5; //deceleration quirk
    }
    else if (Ground Speed > -top_speed) {
        Ground Speed -= acceleration_speed;
        if (Ground Speed <= -top_speed) Ground Speed = -top_speed;
    }
}

if (the player is pressing right) {
    if (Ground Speed < 0) {
        Ground Speed += deceleration_speed;
        if (Ground Speed >= 0) Ground Speed = 0.5; //deceleration quirk
    }
    else if (Ground Speed < top_speed) {
        Ground Speed += acceleration_speed;
        if (Ground Speed >= top_speed) Ground Speed = top_speed;
    }
}

if (the player is not pressing left or right)
    Ground Speed -= min(abs(Ground Speed), friction_speed) * sign(Ground Speed); //decelerate
```

### Control Lock

Control lock is used (set to specific durations) when the Player [slips or falls down a slope](09-slope-physics.md#falling_and_slipping_down_slopes), and [bounces on a horizontal spring](13-game-objects.md#horizontal_springs). While on the ground, the control lock ticks down and prevents ![Left](../images/Leftarrow.png)/![Right](../images/Rightarrow.png) input until it reaches zero.

> [!NOTE]
> Friction** still reacts to ![Left](../images/Leftarrow.png)/![Right](../images/Rightarrow.png) input while the timer is non-zero.

## Jumping

Jumping is affected by ***Ground Angle***. **Jump Force** is subtracted from ***X and Y Speed*** to preserve the values set from ***Ground Speed***.

```c
X Speed -= Jump Force * sin(Ground Angle);
Y Speed -= Jump Force * cos(Ground Angle);
```

### Variable Jump Height

When the jump button is no longer being held, ***Y Speed*** is capped at *-4*. This is performed before the Player is moved the new position and **Gravity** is added to ***Y Speed***.

### Bugs

| ![SPG RollingJumpLandBug](../images/SPGRollingJumpLandBug.gif) |
| --- |
| If you jump while rolling, the Player's hitbox gets reset. Since they're rolling while landing, the hitbox resets again, and *5* is subtracted from ***Y Position***. |

| ![SPG JumpDelay](../images/SPGJumpDelay.gif) |
| --- |
| When you jump, it exits the rest of the movement cycle, meaning the Player won't move at all during that frame. |

| **Changes in [Sonic Mania](https://info.sonicretro.org/Sonic_Mania)** |
| --- |
| **Gravity** is added when **Jump Force** is applied, cancelling the addition of gravity for the first frame in the air. The **Jump Delay** is also fixed, the Player will begin to move upwards on the frame of pressing jump. |

## Midair

While grounded, ***X and Y Speed*** is updated using ***Ground Speed***, so they will already be set for air motion.

Pressing ![Left](../images/Leftarrow.png)/![Right](../images/Rightarrow.png) subtracts/adds **Air Acceleration** to ***X Speed***, limited by **Top Speed**. ***Ground Angle*** changes by *2.8125° (2)* nearest to *0*, this is only visual and does not affect sensor rotation. After gravity is applied to ***Y Speed***, Friction is applied when ***Y Speed*** between *-4* and *0* pixels, otherwise no friction is applied.

`if (Y Speed > -4 && Y Speed < 0) X Speed -= (floor(X Speed >> 2) / 256); // floor() removes subpixels.`

## Rolling

While rolling, the Player can no longer accelerate. Only **Roll Friction** is applied. The Player *can* decelerate while rolling, except friction is still applied. If `abs(Ground Speed) < 38spx` when it's subtracted, instead of *0*, ***Ground Speed*** is set to *0.5 (128spx)* in the opposite direction. ***X Speed*** is capped at *16* on both signs, meanwhile ***Ground Speed*** and ***Y Speed*** isn't. Causing the Player to outrun the camera while in [wall modes](09-slope-physics.md#the_four_modes).

### Criteria

In a few cases, if ***Ground Speed*** is *0* when they try to roll, ***Ground Speed*** is set to *2*. The Player can't roll unless `abs(Ground Speed) >= 128spx`.

In *[Sonic & Knuckles](https://info.sonicretro.org/Sonic_%26_Knuckles)*, it was increased to *1px*, since the Player can crouch while `abs(Ground Speed) < 1px` to perform special moves without needing to fully stop. The Player unrolls if `abs(Ground Speed) < 128spx`.

### Rolling Jump

You can't control the Player's trajectory through the air with ![Left](../images/Leftarrow.png)/![Right](../images/Rightarrow.png) if you jump while rolling. In *[Sonic 3](https://info.sonicretro.org/Sonic_3)* onwards, you can regain control if you perform a jump ability.

In *[Sonic CD](https://info.sonicretro.org/Sonic_CD)* and *[Sonic Mania](https://info.sonicretro.org/Sonic_Mania)*, you can control a jump made while rolling.

## Getting Hit

When the Player has rings and collides into a hazard, ***Y Speed*** is set to **Hurt Y Force** and ***X Speed*** is set to `Hurt X Force * sign(Player  X - Hazard X)`. While in this state, **Hurt Gravity** is applied until they land. Upon landing, ***X Speed*** is set to *0*. The Player cannot leave the hurt state until they land.

In the [Sonic 2 Nick Arcade prototype](https://info.sonicretro.org/Sonic_the_Hedgehog_2_(Nick_Arcade_prototype)), if the Player hits a wall at ***X Speed*** of *6*, they will bounce away with the same physics, they land in a knocked flat animation.

> [!NOTE]
> sign defaults to *1* if zero.

## Dying

When the Player has no rings and touches a harmful object, they will enter a death state. ***X Speed*** is set to **0**, and ***Y Speed*** to **-7**, with normal gravity being applied. No input is read, nor are any collisions detected.

## Rebounding

When the Player destroys an object in the air, if `Player Y Speed < Object Y Speed && Player Y Speed >= 0`, ***Y Speed*** is reversed. `sign(Y Speed)` is subtracted from ***Y Speed*** (e.g. *0.25 (64spx)* -> *-0.75 (-192spx)*) if this isn't the case, giving a bit of weight when hit from below.

> [!NOTE]
> for **Item Monitors**, ***Y Speed*** is always reversed.

### Bosses

***X and Y Speed*** is multiplied by *-0.5*. ***Ground Speed*** is not affected.

> [!NOTE]
> [Variable Jump Height](11-forces-subtopics/jumping.md#variable_jump_height) is still in effect, as it's a part of the Player's code.

## Water Entry

**Remaining Air** starts at 30 upon entering water, and counts down by 1 each second.

| **remaining_air** | Action |
| --- | --- |
| *25, 20, 15* | Warning chime plays. |
| *12* | Drowning music begins. |
| *12, 10, 8, 6, 4, 2* | Countdown bubble is emitted (numbers 5 to 0). |
| Below *0* | Sonic drowns. |

When the Player enters the water, ***X Speed*** is divided by *2*, and ***Y Speed*** by *4*, occurring after *Gravity* is added. When the Player exits the water, if the Player isn't being knocked back from taking damage or controlled by another object, and ***Y Speed*** is more than *-4*, ***Y Speed*** is doubled. ***X Speed*** is *not* affected when leaving the water. If the Player's ***Y Speed*** is less than *-16* it will be limited to *-16* upon exiting.

> [!NOTE]
> ***Control Flags*** have to be disabled for both **Entry and Exit**.

---

[← Slope Physics: Moving, Slipping, 360° Momentum, and Landing](09-slope-physics.md) | [Index](../README.md) | [Forces Subtopic: Air State & Midair Momentum →](11-forces-subtopics/air-state.md)
