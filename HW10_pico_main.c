#include <stdio.h>
#include <stdbool.h>

#include "pico/stdlib.h"
#include "pico/stdio_usb.h"
#include "hardware/i2c.h"
#include "hardware/gpio.h"

#include "mpu6050.h"

#define I2C_PORT        i2c0
#define I2C_SDA_PIN     0
#define I2C_SCL_PIN     1
#define I2C_BAUD        400000

#define BUTTON_PIN      14      // button to GND, internal pull-up enabled
#define HEARTBEAT_LED   16      // optional external LED

#define STREAM_PERIOD_MS 30     // ~33 Hz, easier for pgzero to keep up

int main() {
    stdio_init_all();

    // Give USB time to enumerate before printing
    sleep_ms(2000);

    // Button input with internal pull-up
    gpio_init(BUTTON_PIN);
    gpio_set_dir(BUTTON_PIN, GPIO_IN);
    gpio_pull_up(BUTTON_PIN);

    // Optional heartbeat LED
    gpio_init(HEARTBEAT_LED);
    gpio_set_dir(HEARTBEAT_LED, GPIO_OUT);
    gpio_put(HEARTBEAT_LED, 0);

    // I2C setup for MPU6050
    i2c_init(I2C_PORT, I2C_BAUD);
    gpio_set_function(I2C_SDA_PIN, GPIO_FUNC_I2C);
    gpio_set_function(I2C_SCL_PIN, GPIO_FUNC_I2C);
    gpio_pull_up(I2C_SDA_PIN);
    gpio_pull_up(I2C_SCL_PIN);

    sleep_ms(50);

    // Try to initialize IMU
    if (!mpu6050_setup()) {
        // Fast blink forever if IMU is not found
        while (1) {
            gpio_put(HEARTBEAT_LED, 1);
            sleep_ms(100);
            gpio_put(HEARTBEAT_LED, 0);
            sleep_ms(100);
        }
    }

    mpu6050_data_t imu;
    bool led_state = false;

    while (1) {
        // Read IMU
        mpu6050_read_all(g_imu_addr, &imu);

        // Read button: pull-up means pressed = 0 electrically
        int button_pressed = gpio_get(BUTTON_PIN) ? 0 : 1;

        // Toggle heartbeat LED each packet
        led_state = !led_state;
        gpio_put(HEARTBEAT_LED, led_state);

        // CSV protocol for Python side:
        // ax,ay,button
        printf("%.3f,%.3f,%d\n", imu.ax_g, imu.ay_g, button_pressed);

        sleep_ms(STREAM_PERIOD_MS);
    }

    return 0;
}