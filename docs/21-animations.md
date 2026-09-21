# Animations: Scripts, Variable Speed Timings, and Rules

> **Source:** [SPG:Animations](https://info.sonicretro.org/SPG%3AAnimations)

[← Camera: Scrolling Boundaries, Lag, and Pan Delays](20-camera.md) | [Index](../README.md) | [Overlay Scripts: Diagnostic HUDs for Sonic 1 & Sonic 2 →](22-overlay-scripts.md)

---

**Notes:**

- *The research applies to all four of the [Sega Mega Drive](https://info.sonicretro.org/Sega_Mega_Drive) games and [Sonic CD](https://info.sonicretro.org/Sonic_CD).*
- *Animation notes for [Tails](https://info.sonicretro.org/Tails) and [Knuckles](https://info.sonicretro.org/Knuckles_the_Echidna) are not yet included.*
- *"subimage" refers to an animation frame, while "frame" refers to a game frame, or 1/60th of a second.*

## Animation System

The animation system works as a simple counter, counting down the animation subimage for a specific number of frames (the **duration**), then updating the animation upon completion, and resetting the counter.

The timings are very specifically coded however. For example, an animation might set the duration counter for its subimages to 7, and counts down every frame after. On the frame this counter reaches -1, the duration counter is reset and the subimage is increased. This means the subimage lasts for 1 frame more than the duration is actually set to.  Bizarrely, to account for this the values in the game code are deliberately 1 less than the actual intended duration. So if an animation subimage needs to show onscreen for exactly 24 frames, the game actually uses a value of 23 in its animation system. This is important to note.

### Process

On the frame that the animation is first changed to a variable animation, the subimage will be set to the first of the animation (or another if specified), and the subimage duration timer will be set. On the next frame, the duration counter will begin decreasing by one each frame. Once the counter reaches -1, on that same frame the animation moves to the next subimage and the duration counter is set. On the next frame, the counter will begin to decrease again.

A simplified code example for an animation counter setup similar to this would go as follows:

```c
if (Animation != AnimationToBeSet) //on the event of an animation needing to change
    {
        Animation = AnimationToBeSet; //set animation
        AniSubImageDurationTimer = AniSubImageDurationSet; //reset subimage duration counter, "AniSubImageDurationSet" would be whatever the duration should be at that moment
        AniSubImage = 0; //0 being the first subimage
    }
    else
    {
        //subimage handling
        if (AniSubImageDurationTimer > 0)
        {
            AniSubImageDurationTimer -= 1; //count down subimage duration
        }
        else
        {
            //timer was on 0, so move to next subimage
            AniSubImage = AniSubImage + 1; //next subimage
            if (AniSubImage > (AniSubImageNumber - 1)) AniSubImage = 1; //animation has ended, loop back to start of animation. "AniSubImageNumber" is the number of subimages in the animation loop

            AniSubImageDurationTimer = AniSubImageDurationSet; //reset duration counter, "AniSubImageDurationSet" would be whatever the duration should be at that moment
        }
    }
```

Using this system, the **AniSubImageDurationSet** value can be changed at any time, but it will only take effect when a subimage actually changes, thus emulating the original game with ease.

### Simpler Method For Displaying Subimage Durations

If you don't mind slight innacuracy in the speed of animations, and are using GameMaker or MMF you can use the "image speed" of an animation per frame instead of timing the duration of the subimages.

- This is a very rough way to animate the sprites closely but may result in off-speed variable speed animations, and other differences.
- In GameMaker, the animation speed (image_speed) is how many subimages will be advanced per frame, so a speed of 1 will advance a subimage each frame,and 0.5 will advance a subimage every 2 frames. Although it's better to just set the image_speed like this in the first place.

  - To convert a subimage duration to a GameMaker image speed,  simply divide 1 by it.

```c
image_speed = (1/subimage_duration);
```

## Variable Speed Animation Timings

> [!NOTE]
>

- *This applies to the walk, run, pushing, & ball (rolling & jumping) animations only.*

Some animations update their subimage durations dynamically, to allow animations to speed up or slow down based on the Player's movement. However it works in a very specific way. Unlike updating "image_speed" every frame in Game Maker, the duration of a subimage is only updated every time the subimage actually changes.

For Player animations that have variable speed, this speed is based on Sonic's ground speed. On a frame that the subimage duration is set, the following will happen:

For walking and running

```c
duration = floor(max(0, 8-abs(GroundSpeed)))
```

For rolling and jumping

```c
duration = floor(max(0, 4-abs(GroundSpeed)))
```

For pushing

```c
duration = floor(max(0, 8-abs(GroundSpeed)) * 4) //this is because sonic can be moving while pushing, such as when pushing a block in MZ
```

<br>
Notes:

- *The values from these calculations are directly used as subimage durations by the animation system. So the subimages actually spend 1 more frame onscreen than those values.*
- *When rolling in the air or jumping, the animation speed will remain constant due to the fact that ground speed does NOT update in the air. In other words, the animation remains the speed it was when you left the ground until you land.*
- *Once the subimage exceeds the amount of subimages in a looping animation, on that frame the subimage is simply set to the first subimage.*

## Normal Animation Timings

Shown below are the subimage durations of the animations featured in the [Sonic games](https://info.sonicretro.org/Sonic_games).

> [!NOTE]
>

- *From this point whenever a subimage frame timing is directly specified, the value represents the time the subimage*actually*spends on screen. The value used in the game code for the duration will be 1 less.*

### Idle

#### [Sonic 1](https://info.sonicretro.org/Sonic_1)

Every [sprite](https://segaretro.org/Sprite) subimage in this animation lasts for **24 frames**. [Sonic](https://info.sonicretro.org/Sonic) stays still for 288 frames (the subimage occurs 12 times in the animation code) before entering the waiting subimages of the idle animation. When the waiting portion begins, Sonic enters a subimage for 24 frames, then has his eyes wide open for 72 frames. Afterwards, he will alternate between two subimages every 24 frames, making Sonic appear to tap his foot on the ground. This will loop until the player takes action.

#### [Sonic 2](https://info.sonicretro.org/Sonic_2)

Every sprite subimage in this animation lasts for **6 frames**. Sonic stays still for 180 frames (the subimage occurs 30 times in the animation code) before entering the first set of waiting subimages of the idle animation. He then blinks, which lasts for 6 frames, then has his eyes wide open for 30 frames. Afterwards, he will alternate between two subimages every 18 frames, making Sonic appear to tap his foot on the ground. This will loop until the player takes action.

Should the player NOT take action after Sonic taps his foot 3 times (126 frames) (Note: the animation starts with Sonic's foot down and ends with it pointing upwards), he will then look down at his wrist(watch?) for 60 frames, then resume tapping his foot. This foot-tapping/wristwatch sequence will continue 3 more times (204 frames/sequence*4=816 total frames). Afterwards, if no action is taken at this point, Sonic will enter a new animation where he lies down on the floor. It takes 6 frames for him to drop to the ground. He then enters a final alternating sequence tapping his finger against his shoe. Both subimages in this sequence last for 18 frames each.

#### [Sonic 3K](https://info.sonicretro.org/Sonic_the_Hedgehog_3_%26_Knuckles)

Every sprite subimage in this animation lasts for **6 frames**.

### Balancing

#### [Sonic 1](https://info.sonicretro.org/Sonic_1)

While balancing, the animation waits **32 frames** before advancing to the next subimage.

#### [Sonic 2](https://info.sonicretro.org/Sonic_2)

In Sonic 2 each of the 3 balancing animations have different animation speeds.

The facing forward balance animation waits **10 frames** before advancing to the next subimage.

The backwards balance animation waits **20 frames** before advancing to the next subimage.

And the last balance animation waits **4 frames** before advancing to the next subimage.

#### [Sonic 3](https://info.sonicretro.org/Sonic_3)

In Sonic 3 there are only 2 balancing animations, the one when you're at the edge, and the one when you're further down the edge.

The first one waits **8 frames** before advancing to the next subimage.

And the second one waits **6 frames** before advancing to the next subimage.

### Braking (Skidding)

Skidding is merely an animation, with no deceleration or friction calculations exclusive to it. In Sonic 1, the animation waits 8 frames before advancing to the next subimage while braking. It will continue to loop between the two subimages until Sonic has stopped. In Sonic 2 and Sonic 3K, the animation will stop when it finishes, instead of looping.

> [!NOTE]
> *Sonic can only brake ("screech to a halt") in Floor mode.*

### Spindash

The spindash animation itself waits 1 frame to advance a subimage.

When a button is pressed to charge up the spindash, the subimage is set to 1 (therefore resetting it).

## Animation Rules

Of course, it's not enough to simply know how these animations play, you have to know when and why they play (for those where it's not exactly obvious).

### Idle/Walking/Running Animation

If you include Sonic CD in the mix, Sonic has 3 different running animations. He is depicted as standing still only if *gsp* is exactly zero. If he has any *gsp* whatsoever, he enters his walking animation, the subimage advances in relation to his ground speed as described above.

Once his *gsp* equals (or exceeds) 6, he enters his running animation, with the whirling feet. Once his *gsp* equals (or exceeds) 10, he enters his Dashing animation, with the figure-eight feet. Of course, the Dashing animation is only in Sonic CD.

### Rolling and Jumping Animation

Typically Sonic's jump/ball animation includes one full ball subimage and 4 detailed subimages of his body rotating (once every spin). However if *gsp* equals (or exceeds) 6, even while in the air, the animation will include a full ball subimage after every 2 full body subimages (twice every spin).

### Spring Animation

The "up" springboard animation waits 48 frames before changing to the walking animation.

For all of the diagonal springboards, Sonic doesn't change to the walking animation in the air at all. Instead, he remains in the corkscrew (3D spinning) animation, this animation waits 5.5 frames before advancing a subimage.

### Braking Animation

Sonic enters his braking animation when you turn around only if his absolute *gsp* is equal to or more than 4. In Sonic 1 and Sonic CD, he then stays in the braking animation until *gsp* reaches zero or changes sign. In the other 3 games, Sonic returns to his walking animation after the braking animation finishes displaying all of its frames.

---

[← Camera: Scrolling Boundaries, Lag, and Pan Delays](20-camera.md) | [Index](../README.md) | [Overlay Scripts: Diagnostic HUDs for Sonic 1 & Sonic 2 →](22-overlay-scripts.md)
