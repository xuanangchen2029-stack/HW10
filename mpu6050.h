#ifndef MPU6050_H
#define MPU6050_H
#include <stdbool.h>
#include <stdint.h>

#define MPU6050_ADDR     0x68
#define MPU6050_ALT_ADDR 0x69

#define CONFIG       0x1A
#define GYRO_CONFIG  0x1B
#define ACCEL_CONFIG 0x1C
#define PWR_MGMT_1   0x6B
#define PWR_MGMT_2   0x6C

#define ACCEL_XOUT_H 0x3B
#define WHO_AM_I     0x75

typedef struct {
    int16_t ax_raw, ay_raw, az_raw;
    int16_t temp_raw;
    int16_t gx_raw, gy_raw, gz_raw;
    float ax_g, ay_g, az_g;
    float temp_c;
    float gx_dps, gy_dps, gz_dps;
} mpu6050_data_t;

extern uint8_t g_imu_addr;

bool mpu6050_setup(void);
void mpu6050_read_all(uint8_t addr, mpu6050_data_t *d);

#endif
