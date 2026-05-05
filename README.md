# HW10 - Pico + Pygame Zero serial interaction

## Overview
This project uses two hardware inputs on the Pico:
1. MPU6050 accelerometer (I2C)
2. Pushbutton on GP14

The Pico streams sensor data over USB serial in a simple CSV protocol:

ax,ay,button

Example:
0.123,-0.456,1

## Game: Gravity Ball

**Gravity Ball** is an interactive physics-based game controlled entirely by a Raspberry Pi Pico 2 microcontroller with an MPU6050 IMU and a pushbutton.

The game renders a glowing neon ball inside a dark arena. Instead of a keyboard or mouse, the player physically tilts the Pico board to roll the ball — the IMU's accelerometer reads the tilt angle in real time and applies it as a gravitational force on the ball, which then accelerates, slides, and bounces off the walls with realistic physics. Tilt right and the ball rolls right; tilt forward and it climbs up the screen.

Pressing the physical button triggers a particle explosion effect and cycles the ball through five neon color palettes — cyan, hot pink, green, gold, and violet.

**Controls:**
- Tilt left/right → roll ball left/right
- Tilt forward/back → roll ball up/down
- Press button → trigger explosion effect + cycle color

## Hardware wiring

### MPU6050
- Pico GP0 -> SDA
- Pico GP1 -> SCL
- Pico 3V3(OUT) -> VCC
- Pico GND -> GND

### Button
- One side of button -> GP14
- Other side of button -> GND
- Internal pull-up is enabled in code

### Optional heartbeat LED
- GP16 -> 330 ohm resistor -> LED -> GND

## Files
- HW10_pico_main.c
- mpu6050.c
- mpu6050.h
- CMakeLists.txt
- hw10_visualizer.py

## Build the Pico code
1. Open the HW10 folder in VS Code with the Pico extension
2. Build and flash the Pico program
3. Open a serial monitor and verify lines like:
   0.015,-0.982,0

## Run the Python visualizer
1. Create and activate a Python virtual environment
2. Install pgzero and pyserial
3. Edit SERIAL_PORT in hw10_visualizer.py
4. Run:
   python hw10_visualizer.py

## Demo idea
Show:
1. Pico connected to IMU and button
2. Serial monitor printing data
3. Pygame Zero window with ball rolling in response to board tilt
4. Button triggering explosion effect and color change
