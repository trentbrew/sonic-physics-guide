# Elemental Shields: Flame, Bubble, and Lightning Shield Actions

> **Source:** [SPG:Elemental Shields](https://info.sonicretro.org/SPG%3AElemental_Shields)

[← Special Abilities: Spindash, Peel Out, Drop Dash, Flight, Glide](16-special-abilities.md) | [Index](../README.md) | [Player 2: CPU AI, Follower Physics, and Respawning →](18-player-2.md)

---

**Notes:**

- *The research applies to all four of the [Sega Mega Drive](https://info.sonicretro.org/Sega_Mega_Drive) games and [Sonic CD](https://info.sonicretro.org/Sonic_CD).*
- *For moves like spindash, dropdash, peelout, flying, and gliding, these are detailed in [Special Abilities](16-special-abilities.md).*

## Reflecting Bullets

This goes for all Elemental Shields and in [Sonic Mania](https://info.sonicretro.org/Sonic_Mania), the Blue Shield.

First, when the game notices that you have a shield, it will create a *48* x *48* pixel sized [hitbox](07-hitboxes.md) for it.
If any object considers a projectile overlaps this hitbox, it will get the angle from two points: The player's position and the objects position.
Then, it will set that object's speed to *8* in the direction of that angle.

Here is the sudo-code of what that looks like:

```c
Has object collided with shield hitbox {
	Object is a projectile {
		var distance = Player's Position - Object's Position; // Direction of where the object is relative to the player
		var angle = to_angle(distance); // Turning that into a usable angle for trig functions

		// Shoot object off in the direction of impact
		object.speed.x = (-cos(angle) * 8);
		object.speed.y = (-sin(angle) * 8);

		// Remove object hitbox
		object.hitbox().remove();
	}
}
```

<br>

## Flame Shield

When Sonic performs the Flame Shield action while airborne, his ***X Speed*** is set to **8** in the direction he is facing, and his Y speed is set to **0**, regardless of their previous values.

## Bubble Shield

| Constant | Value |
| --- | --- |
| **down_force** | *8* |
| **bounce_force** | *7.5* - *4* if underwater |

When Sonic performs the Bubble Shield bounce, his ***X Speed*** is set to *0*, and his ***Y Speed*** to **down_force**.  However, in [Sonic Mania](https://info.sonicretro.org/Sonic_Mania), ***X Speed*** is halved instead of set to *0*.

When he rebounds from the ground, **bounce_force** is subtracted from X Speed and Y Speed, using cos() and sin() to get the right values.

```c
X Speed -= bounce_force * sin(Ground Angle);
Y Speed -= bounce_force * cos(Ground Angle);
```

On steep slopes, the bubble shield is unlikely to bounce at the right angle. That's because this bounce speed is applied AFTER Sonic lands and has calculated his new Ground Speeds and new ***X Speed*** and ***Y Speed*** from [landing on the ground](09-slope-physics.md#landing_on_the_ground). On steep slopes, this landing ***Y Speed*** is likely to be high (downwards), effectively cancelling out a lot of the bounce ***Y Speed*** that gets applied.

## Lightning Shield

When Sonic performs the Lightning Shield double jump, his ***X Speed*** is unaffected, but his ***Y Speed*** is set to **-5.5** regardless of its previous value.

> [!NOTE]
> All of the Shield abilities can only be performed once in the air.  Sonic must land on the ground before he can perform them again.

### Ring Magnetization

When Sonic has a Lightning shield, nearby Rings will become mobile and begin moving towards him in a unique way.

| Constant | Value |
| --- | --- |
| **follow_speed** | *0.1875* |
| **turn_speed** | *0.75* |

If a Ring falls within a box *128* x *128* pixels around Sonic's position, it will become Magnetized and begin to move. When Magnetized, the Rings have an ***X*** and ***Y Speed*** and do not collide with anything (except for Sonic). In order to move correctly, we have to calculate how fast to move the Ring, and in what direction to accelerate. The Ring accelerates at two different rates depending on its relative position and speed, **follow_speed** when already moving towards Sonic (in order to not pass him too quickly), and **turn_speed** when not (in order to quickly catch back up with him).

First, it does a check to see where Sonic is in relative position horizontally.

| Sonic is to the left of the Ring |
| --- |
| If the Ring's ***X Speed*** is less than *0*, subtract **follow_speed** from the Ring's ***X Speed***. Otherwise, subtract **turn_speed** from the Ring's ***X Speed***. |
| Sonic is to the right of the Ring |
| If the Ring's ***X Speed*** is greater than *0*, add **follow_speed** to the Ring's ***X Speed***. Otherwise, add **turn_speed** to the Ring's ***X Speed***. |

Then, the attracted Ring checks Sonic's relative position vertically.

| If Sonic is to the left of the Ring |
| --- |
| Sonic is above the Ring |
| If the Ring's ***Y Speed*** is less than *0*, subtract **follow_speed** from the ring's ***Y Speed***. Otherwise, subtract **turn_speed** from the Ring's ***Y Speed***. |
| Sonic is below the Ring |
| If the Ring's ***Y Speed*** is greater than 0, add **follow_speed** to the Ring's ***Y Speed***. Otherwise, add **turn_speed** to the Ring's ***Y Speed***. |

The Ring's ***X*** and ***Y Speed*** is then added to the Ring's ***X*** and ***Y Positions***, moving it.

Here's some example code for the ring while magnetized:

```c
if Ring is magnetized
{
	// Relative positions
	var sx = sign(Sonic's X Position - Ring's X Position);
	var sy = sign(Sonic's Y Position - Ring's Y Position);

	// Check Ring's relative movement (0 if moving away from sonic, 1 if moving towards)
	var tx = (sign(Ring's X Speed) == sx)
	var ty = (sign(Ring's Y Speed) == sy)

	// Add to speed
	Ring's X Speed += (ring_acceleration[tx] * sx);
	Ring's Y Speed += (ring_acceleration[ty] * sy);
	//"ring_acceleration" would be an array, where: [0] = turn_speed, [1] = follow_speed

	// Move
	Ring's X Position += Ring's X Speed;
	Ring's Y Position += Ring's Y Speed;
}
```

<br>
If a ring has been magnetized, but the player has lost the Lightning shield before collecting that ring, the ring will turn into a [Spilled Ring](13-game-objects.md#scattered_rings).
the new ring maintains its speed from being magnetized.

---

[← Special Abilities: Spindash, Peel Out, Drop Dash, Flight, Glide](16-special-abilities.md) | [Index](../README.md) | [Player 2: CPU AI, Follower Physics, and Respawning →](18-player-2.md)
