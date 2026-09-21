# Player 2: CPU AI, Follower Physics, and Respawning

> **Source:** [SPG:Player 2](https://info.sonicretro.org/SPG%3APlayer_2)

[← Elemental Shields: Flame, Bubble, and Lightning Shield Actions](17-elemental-shields.md) | [Index](../README.md) | [Special Stages: Sonic 1 Rotating Maze Physics →](19-special-stages.md)

---

<br>
**Notes:**

- Every time Controller 2 detects input, CPU control will be disabled for 10 seconds.
- ![A](../images/Abtn.png)![B](../images/Bbtn.png)![C](../images/Cbtn.png) will be referred to as the **Action Button(s)**.
- All frames are checked on a global timer.

## Player 2 Control

There are *3* different lists keeping track of Player 1 in the last 32 frames.

| Position List | ***X/Y Position*** |
| --- | --- |
| States List | The Grounded, Pushing, and Jumping states, and direction the player is facing. |
| Control List | Controller 1 Inputs. |

When Player 2 uses this information it will be labelled as **Target Input, X, Y, Grounded, etc.**. These will reference Player 1's state *16* frames in the past from these lists.

### CPU Inputs

Player 2 uses **Target Inputs** as their own. If Player 2 has an active [control lock](https://info.sonicretro.org/SPG:Running#Control_Lock) and ***Ground Speed*** is *0*, they are most likely stuck and will enter their [Spindash state](18-player-2.md#cpu_spindash_state).  Otherwise, Player 2 will continue onto [CPU following](18-player-2.md#cpu_following_state).

If Player 2 is pushing and **Target Pushing** is not, it's stuck against a wall/object, move to [jumping](18-player-2.md#jumping). Otherwise, continue normal movement.

#### Normal Movement

> [!NOTE]
> In Sonic 3 onwards, if Player 1's `abs(Ground Speed) < 4` while not standing on an object, *32* is subtracted from **Target X**.

If `abs(X Position - Target X) > 16` (*48* in Sonic 3), move ![Left](../images/Leftarrow.png)/![Right](../images/Rightarrow.png) depending on which side the player is on. If ***Ground Speed*** isn't *0* and they are not pushing, add 1px to ***X Position*** in the direction they're facing, forcefully pulling them towards Player 1. If ***X Position*** equals **Target X**, face **Target Direction**.

##### Actions & Checks

If the CPU following code is exited for the current frame after any of these checks, this means that any further checks and [jumping](18-player-2.md#jumping) will not occur.

- If Player 2 is jumping midair, hold down the **Action button** and exit the code.
- If the `abs(X Position - Target X) > 64`, exit the code.
- If `Target Y is >= Y Position`, Player 1 is below Player 2 and will exit.
- If `Target Y - Y Position < -32px` Player 1 is less than 32 pixels above Player 2 and will exit.

#### Jumping

A Jump is performed every *64* frames. If not crouching, hold the jump buttons, then finish execution.

> [!NOTE]
> In other cases, like Player 2 being close to Player 1, it will instead use the [input buffer](18-player-2.md#cpu_inputs) directly, as mentioned before.

### CPU Spindash State

If [control lock](https://info.sonicretro.org/SPG:Running#Control_Lock) is active or ***Ground Speed*** isn't *0*, exit the code. Turn to face Player 1, pressing ![Down](../images/Downarrow.png) to crouch. When in the ducking sprite, tap the **Action button** to start Spindashing. If not crouching, every *128* frames cancel the state and move to the CPU Follow state.

#### Spindash

Tap the **Action button** every *32* frames. Every *128* frames, release the Spindash, and set state back to CPU Follow.

## CPU Logic Loop

To make it easier to understand how each of these states go together, here is the correct order in how the CPU determines what it does next:

| Away from Player 1 (Greater than 64 pixels) | Close to Player 1 (Lower or equal than 64 pixels) | Panic Spindash |
| --- | --- | --- |
| Player 2 is away from Player 1 1. Player 2 controls locked [(from a slope)](09-slope-physics.md#falling_and_slipping_down_slopes), and isn't moving? - Transition to [Panic Spindash](18-player-2.md#cpu_spindash_state). 2. Player 2 is on the Left side of Player 1? - Force the Player 2 to hold Right. - Pull Player 2 twards Player 1 if Player 1 is facing left and is moving. 3. Player 2 is on the Left side of Player 1? - Force the Player 2 to hold Left. - Pull Player 2 twards Player 1 if Player 1 is facing right and is moving. | Player 2 is close to Player 1 1. Player 2 controls locked [(from a slope)](09-slope-physics.md#falling_and_slipping_down_slopes), and isn't moving? - Transition to [Panic Spindash](18-player-2.md#cpu_spindash_state). 2. Player 2 is on the Left side of Player 1? - Pull Player 2 twards Player 1 if Player 1 is facing left and is moving. 3. Player 2 is on the Left side of Player 1? - Pull Player 2 twards Player 1 if Player 1 is facing right and is moving. 4. Is Player 2 pushing a wall, and Player 1 isn't? - Are we not jumping? Are we below `target_y + 32`? Not far away? - If previous statement is true, jump every 64 frames when not crouching or looking up. | Player 2 is in [Panic Spindash](18-player-2.md#cpu_spindash_state) 1. Freeze all control. 2. Player 2 at a standstill? Halt execution until true. - Face Player 1 - Did the Spindash Release timer go off? Release - Not Spindashing? Press the inputs on Player 2 to start one. - Charge Spindash everytime the Spindash Charge Timer goes off. |

## Respawning

Player 2 will Respawn if they are offscreen for *5* seconds.

### Tails

Upon respawning, ***X Position*** is set to Player 1 ***X Position***, ***Y Position*** is set to `Player 1 Y Position - 192`. **Target X** and **Target Y** will be set to Player 1's current positions (for that frame only, from here on it uses the delayed values).

#### Horizontal Movement

```c
x_difference = Player 2's X Position - target_x;
y_difference = Player 2's y Position - target_y;

if (x_difference != 0){
	var move_x = min(abs(dist_x) >> 4, 12);
	// ">> 4" here is equivalent to dividing by 16, floored. I wouldn't recommend this unless your engine cant do bitmaths
 	move_x += round(abs(target_x_speed)) + 1;
 	if (x_difference >= 0){
 	 	//Left side of Player 1
 	 	if move_x >= x_difference {
			move_x = x_difference;
			dist_x = 0;
			// Prevents jittering if you move farther than where Player 1 is
		}
		Player 2 X Position -= move_x;
	} else {
		//Right side of Player 1
		x_difference = -x_difference // Invert difference to go left
		if move_x >= x_difference {
			move_x = x_difference;
			dist_x = 0;
		}
		Player 2 X Position += move_x;
	}
}
```

Tails will face **Target X**, and will move towards it by the distance away from Player 1 at a maximum speed of 12px.
`move_x` is the distance from **Target X** being constantly interpolated towards 0, like the [Air Drag](11-forces-subtopics/air-state.md#air_drag) function in the Player's air state. To prevent Tails from stopping short of **Target X**, ` target_x_speed + 1` is added to `move_x`. The logic below that is to prevent Tails from moving beyond **Target X**.

#### Vertical Movement

Vertically, Tails will move up or down (modifying ***Y Position*** rather than using speeds) by 1px per frame until they reach Player 1's ***Y Position***.

#### Landing

Player 2 will land when close enough to Sonic, ***X and Y Position*** equals **Target X and Y**, **Target Grounded** must be true.

In *[Sonic 3](https://info.sonicretro.org/Sonic_3)*, the game also makes sure that Player 1 isn't in their dying state.

If you notice Tails can be incredibility stingy about land, if you dislike this you may want to implement a distance comparison instead of the comparison above.
See the pseudo-code below to get a good idea of what that would look like:

```c
// The rest of the return flight code would be present above this line...

var reached_x = false;
var reached_y = false;

if abs(x_difference) <= 4{
	reached_x = true;
}
if abs(y_difference) <= 4{
	reached_y = true;
}

if (reached_x && reached_y && target_grounded){
	// Transition Player 2 to jump state.
}
```

---

[← Elemental Shields: Flame, Bubble, and Lightning Shield Actions](17-elemental-shields.md) | [Index](../README.md) | [Special Stages: Sonic 1 Rotating Maze Physics →](19-special-stages.md)
