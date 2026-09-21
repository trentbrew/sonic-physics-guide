# Calculations: Angle Ranges & Trigonometric Functions

> **Source:** [SPG:Calculations](https://info.sonicretro.org/SPG%3ACalculations)

[← Basics: Objects, Maps, Subpixels, Angles, and Framerates](01-basics.md) | [Index](../README.md) | [Characters: Sonic, Tails, and Knuckles Physics Differences →](03-characters.md)

---

This is a supplementary page to [SPG:Basics](01-basics.md), and shows how indistinguishable accuracy can be achieved with modern frameworks/engines. Most functions aren't used in the original game, but they may come in handy for modern developers using this guide.

If you want absolute pinpoint accuracy to the originals, you need to use a Hex angles system and trigonometry functions. Any decimal degree values presented in the guide are approximated.

## Angle Ranges

For example, if the Player's landing angle points more to the right than up or down, the game needs to know.

`new_range_angle = ((angle - 32) % 256) >> 6`.

This calculation returns a value for each 90 degree sector, from 0 to 3 (90° to 270°). *32* (45°) is offset from the hex angle, centering them on each cardinal direction. These ranges aren't symmetrical, since each 45° cannot be shared between sectors.

## Functions

Various useful functions for modern implementation.

```c
// -- CONVERSION FUNCTIONS --

// converts Clockwise hex angles into Anti-Clockwise degree angles.
int hextodeg(hex_ang) return ((256 - hex_ang) / 256) * 360;
int degtohex(deg_ang) return ((360 - deg_ang) / 360) * 256;

// converts Pixels and Subpixels to a Decimal value.
float subpixel_to_decimal(pix, subpix) return pix + (subpix / 256);

// -- TRIGNOMETRIC FUNCTIONS --

// To perform (Co)sine fast, list of pre-calculated values is used
SINCOSLIST[] = {0,6,12,18,25,31,37,43,49,56,62,68,74,80,86,92,97,103,109,115,120,126,131,136,142,147,152,157,162,167,171,176,181,185,189,193,197,201,205,209,212,216,219,222,225,228,231,234,236,238,241,243,244,246,248,249,251,252,253,254,254,255,255,255,
256,255,255,255,254,254,253,252,251,249,248,246,244,243,241,238,236,234,231,228,225,222,219,216,212,209,205,201,197,193,189,185,181,176,171,167,162,157,152,147,142,136,131,126,120,115,109,103,97,92,86,80,74,68,62,56,49,43,37,31,25,18,12,6,
0,-6,-12,-18,-25,-31,-37,-43,-49,-56,-62,-68,-74,-80,-86,-92,-97,-103,-109,-115,-120,-126,-131,-136,-142,-147,-152,-157,-162,-167,-171,-176,-181,-185,-189,-193,-197,-201,-205,-209,-212,-216,-219,-222,-225,-228,-231,-234,-236,-238,-241,-243,-244,-246,-248,-249,-251,-252,-253,-254,-254,-255,-255,-255,
-256,-255,-255,-255,-254,-254,-253,-252,-251,-249,-248,-246,-244,-243,-241,-238,-236,-234,-231,-228,-225,-222,-219,-216,-212,-209,-205,-201,-197,-193,-189,-185,-181,-176,-171,-167,-162,-157,-152,-147,-142,-136,-131,-126,-120,-115,-109,-103,-97,-92,-86,-80,-74,-68,-62,-56,-49,-43,-37,-31,-25,-18,-12,-6};

// Used in various functions (possibly atan list?)
ANGLELIST[] = {0,0,0,0,1,1,1,1,1,1,2,2,2,2,2,2,3,3,3,3,3,3,3,4,4,4,4,4,4,5,5,5,5,5,5,6,6,6,6,6,6,6,7,7,7,7,7,7,8,8,8,8,8,8,8,9,9,9,9,9,9,10,10,10,10,10,10,10,11,11,11,11,11,11,11,12,12,12,12,12,12,12,13,13,13,13,13,13,13,14,14,14,14,14,14,14,15,15,15,15,15,15,15,16,16,16,16,16,16,16,17,17,17,17,17,17,17,17,18,18,18,18,18,18,18,19,19,19,19,19,19,19,19,20,20,20,20,20,20,20,20,21,21,21,21,21,21,21,21,21,22,22,22,22,22,22,22,22,23,23,23,23,23,23,23,23,23,24,24,24,24,24,24,24,24,24,25,25,25,25,25,25,25,25,25,25,26,26,26,26,26,26,26,26,26,27,27,27,27,27,27,27,27,27,27,28,28,28,28,28,28,28,28,28,28,28,29,29,29,29,29,29,29,29,29,29,29,30,30,30,30,30,30,30,30,30,30,30,31,31,31,31,31,31,31,31,31,31,31,31,32,32,32,32,32,32,32,0};

// Returns a hex Sine value from -256 to 256 (divide 256 to get a -1 to 1 decimal result)
int hexsin(hex_ang) return SINCOSLIST[hex_ang % 256];
#define hexcos(hex_ang) hexsin(hex_ang + 64)

// Returns a hex angle to the x/y distance.
int postohexdir(xdist, ydist) {
	// Default
	if (!xdist && !ydist) return 64;

	int xx, yy, compare, angle;

	// Force positive
	xx = abs(xdist);
	yy = abs(ydist);

	// Get initial angle
	if (yy >= xx) {
		compare = (xx * 256) / yy;
		angle = 64 - ANGLELIST[compare];
	} else {
		compare = (yy * 256) / xx;
		angle = ANGLELIST[compare];
	}

	// Check angle
	if (xdist <= 0) angle = -angle + 128;
	if (ydist <= 0) angle = -angle + 256;

	return angle;
}

unsigned long rand; // global variable

#define Swap16(val) ((val) << 16) | ((val) >> 16)

void RandomNumber() { // random function eyed conversion from Sonic 1
    if (!rand) rand = 0x2A6D365A; // reset seed
    unsigned long helper = rand;

    // .scramble
    rand = (rand << 2) + helper;
    rand = (rand << 3) + helper;

    helper = rand;
    rand = Swap16(rand) + helper;
    rand = Swap16(rand);

    rand &= 0xFFFFFFFF; // use only 32 bits.
}
```

---

[← Basics: Objects, Maps, Subpixels, Angles, and Framerates](01-basics.md) | [Index](../README.md) | [Characters: Sonic, Tails, and Knuckles Physics Differences →](03-characters.md)
