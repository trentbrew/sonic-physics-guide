# Forces Subtopic: Air State & Midair Momentum

> **Source:** [SPG:Air State](https://info.sonicretro.org/SPG%3AAir_State)

[← Forces: Physics Values, Running, Jumping, Rolling, and Impact](../10-forces.md) | [Index](../../README.md) | [Forces Subtopic: Jumping & Variable Jump Height →](jumping.md)

---

## Midair

While grounded, ***X and Y Speed*** is updated using ***Ground Speed***, so they will already be set for air motion.

| Constant | Value |
| --- | --- |
| **air_acceleration_speed** | *24 subpixels* |
| **gravity_force** | *56 subpixels* |
| **top_speed** | *6 pixels* |
| **top_gravity**([Sonic CD](https://info.sonicretro.org/Sonic_CD) only) | *16 pixels* |

Pressing ![Left](../../images/Leftarrow.png)/![Right](../../images/Rightarrow.png) subtracts/adds **air_acceleration_speed** to ***X Speed***, limited by **top_speed**. ***Ground Angle*** changes by *2.8125° (2)* nearest to *0*, this is only visual and does not affect sensor rotation. After gravity is applied to ***Y Speed***, Friction is applied when ***Y Speed*** between *-4* and *0* pixels, otherwise no friction is applied.

`if (Y Speed > -4 && Y Speed < 0) X Speed -= (floor(X Speed >> 2) / 256); // floor() removes subpixels.`

> [!NOTE]
> This only applies when the Player has no special power-up and is not [Underwater](underwater.md).

---

[← Forces: Physics Values, Running, Jumping, Rolling, and Impact](../10-forces.md) | [Index](../../README.md) | [Forces Subtopic: Jumping & Variable Jump Height →](jumping.md)
