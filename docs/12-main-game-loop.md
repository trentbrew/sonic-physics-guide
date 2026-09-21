# Main Game Loop: Execution Order per Frame

> **Source:** [SPG:Main Game Loop](https://info.sonicretro.org/SPG%3AMain_Game_Loop)

[← Forces Subtopic: Speed Shoes, Super & Hyper Sonic Speeds](11-forces-subtopics/super-speeds.md) | [Index](../README.md) | [Game Objects: Springs, Spikes, Rings, Monitors, and Bumpers →](13-game-objects.md)

---

<br>

## Introduction

In order to have a full understanding of how the games work, knowing the order of the routines is just as important as what they're doing.

## Players

When the object routine begins the players are the first in the queue to be processed, with their current state changing how they react to the environment.

| Normal/Rolling (Not Airborne) |
| --- |
| **Where "Normal" state starts.** 1. Check for special animations (e.g. balancing) that prevent control. 2. Check for various [Special Abilities](16-special-abilities.md). <br> **Where "Rolling" state starts.** 1. Adjust ***Ground Speed*** based on current ***Ground Angle*** ([Slope Factor](09-slope-physics.md#slowing_down_uphill_and_speeding_up_downhill)). 2. Jump check routine. 3. Update ***Ground Speed*** based on directional input and apply [friction](https://info.sonicretro.org/SPG:Running#Friction). 4. Check for starting crouching, balancing on ledges, etc. 5. [Push Sensor collision](06-slope-collision.md#push_sensors_28grounded29) occurs. - Based on [Sensor Activation](06-slope-collision.md#grounded_sensor_activation). - Occurs before the new position is set, current ***X and Y Speed*** is used to offset the sensor's position. 6. [Rolling Check](11-forces-subtopics/rolling.md#criteria) routine. 7. Handle camera boundaries (keep the object in view and handle the kill plane). 8. Move the Player object. - Calculate [***X and Y Speed*** from ***Ground Speed*** and ***Ground Angle***](09-slope-physics.md#moving_along_slopes). - Update ***X and Y Position*** based on ***X and Y Speed***. 9. Grounded [Ground Sensor collision](06-slope-collision.md#ground_sensors_28grounded29) occurs. - Update ***Ground Angle***. - Align the object to surface of terrain or become airborne if none found. 10. Check for [Slipping/Falling](09-slope-physics.md#falling_and_slipping_down_slopes) when ***Ground Speed*** is too low on walls/ceilings. |

| Airborne (Not Grounded) |
| --- |
| 1. Check for jump button release ([Variable Jump Velocity](11-forces-subtopics/jumping.md#jump_velocity)). 2. Check for Super transformation. 3. Update ***X Speed*** based on directional input. 4. Apply [Air Drag](11-forces-subtopics/air-state.md#air_drag). 5. Move the Player object. - Update ***X and Y Position*** based on ***X and Y Speed***. 6. Apply [Gravity](11-forces-subtopics/air-state.md#gravity) (By updating ***Y Speed***). - Occurs after the new position is set. This is important for ensuring jump height is correct. 7. Reduce underwater gravity. 8. Rotate ***Ground Angle*** [Back to 0](11-forces-subtopics/air-state.md#air_rotation). 9. Check collisions. - The sensors used depend on the [Sensor Activation](06-slope-collision.md#while_airborne). - [Push Sensors](06-slope-collision.md#push_sensors_28airborne29), then [Ground](06-slope-collision.md#ground_sensors_28airborne29)/[Ceiling Sensors](06-slope-collision.md#ceiling_sensors) second. |

### Hitboxes

After moving is complete, the Player object checks for any other colliding object hitboxes. Note that this happens during the Player object's routine, before the rest of objects in the queue begin theirs.

<br>

## Objects

***Special Objects*** (e.g. title cards) are reserved special events and execute before general objects (rings, enemies, bosses, etc.), in which they can occur in no particular order. Every object is runs separately and has their own routines to make them function, and therefore they can run routines in any order they please (e.g. updating ***X and Y Speed*** before or after the new position is set).

*See: [Game Objects](13-game-objects.md) and [Game Enemies](14-game-enemies.md); for descriptions of the actions that general objects will execute here.*

### Object Player Collision

Collision between objects and Players also happens here. As stated in [Solid Objects](08-solid-objects.md#solid_objects), solid objects use their own code to keep the Player out, which allows for flexibility when it comes to implementing object behavior. If the object uses a [trigger area](07-hitboxes.md#trigger_areas), overlap will be checked using the Player's position anywhere during the object routine.

---

[← Forces Subtopic: Speed Shoes, Super & Hyper Sonic Speeds](11-forces-subtopics/super-speeds.md) | [Index](../README.md) | [Game Objects: Springs, Spikes, Rings, Monitors, and Bumpers →](13-game-objects.md)
