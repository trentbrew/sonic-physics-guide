# Forces Subtopic: Rolling Physics & Rolling Jump

> **Source:** [SPG:Rolling](https://info.sonicretro.org/SPG%3ARolling)

[← Forces Subtopic: Jumping & Variable Jump Height](jumping.md) | [Index](../../README.md) | [Forces Subtopic: Getting Hit & Invulnerability Frames →](getting-hit.md)

---

## Constants

| Constant | Value |
| --- | --- |
| **roll_friction_speed** | *0.0234375 (6 subpixels)* |
| **roll_deceleration_speed** | *0.125 (32 subpixels)* |

## Friction

While rolling, the Player can no longer accelerate. The only thing applied is friction (**roll_friction_speed**), half the Player's regular friction (in Sonic 3K, Super roll friction is always half of the regular friction).

## Deceleration

The Player *can* decelerate while rolling, which behaves the same while walking, except friction is still applied. Like when [walking](https://info.sonicretro.org/SPG:Running#Deceleration), if `abs(Ground Speed < 0.1484375 (38spx))` when this value is subtracted, instead of *0*, ***Ground Speed*** is set to *0.5 (128 subpixels)* in the opposite direction. This means the Player can technically turn around while rolling.

## Top Speed

***X Speed*** is capped at *16* on both signs, meanwhile ***Ground Speed*** and ***Y Speed*** isn't. This can cause the Player to be able to outrun the camera while in [wall modes](../09-slope-physics.md#the_four_modes).

For a more fair limit, you can just cap the ***Ground Speed*** instead, that is if you want the cap at all.

## Criteria

In a few cases, if ***Ground Speed*** is *0* when they try to roll, ***Ground Speed*** is set to *2*. The Player can't normally begin to roll unless `abs(Ground Speed) >= 0.5 (128spx)`.  In *[Sonic & Knuckles](https://info.sonicretro.org/Sonic_%26_Knuckles)*, it was increased to *1*, due to the Player being able to crouch while `abs(Ground Speed) < 1` to perform special moves without needing to fully stop.

Also in Sonic and Knuckles, the Player unrolls if `abs(Ground Speed) < 0.5 (128spx)`.

## Rolling Jump

You can't control the Player's trajectory through the air with the ![Left](../../images/Leftarrow.png)![Right](../../images/Rightarrow.png) buttons if you jump while rolling. Though, in *[Sonic 3](https://info.sonicretro.org/Sonic_3)* onwards, you can regain control if you perform a jump ability.

In *[Sonic CD](https://info.sonicretro.org/Sonic_CD)* and *[Sonic Mania](https://info.sonicretro.org/Sonic_Mania)*, you can control a jump made while rolling.

---

[← Forces Subtopic: Jumping & Variable Jump Height](jumping.md) | [Index](../../README.md) | [Forces Subtopic: Getting Hit & Invulnerability Frames →](getting-hit.md)
