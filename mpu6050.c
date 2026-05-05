#include "mpu6050.h"
#include "hardware/i2c.h"

#define I2C_PORT i2c0

uint8_t g_imu_addr = MPU6050_ADDR;

static void i2c_write_reg(uint8_t addr, uint8_t reg, uint8_t value) {
    uint8_t buf[2] = {reg, value};
    i2c_write_blocking(I2C_PORT, addr, buf, 2, false);
}

static uint8_t i2c_read_reg(uint8_t addr, uint8_t reg) {
    uint8_t value = 0;
    i2c_write_blocking(I2C_PORT, addr, &reg, 1, true);
    i2c_read_blocking(I2C_PORT, addr, &value, 1, false);
    return value;
}

static void i2c_read_burst(uint8_t addr, uint8_t start_reg, uint8_t *buf, size_t len) {
    i2c_write_blocking(I2C_PORT, addr, &start_reg, 1, true);
    i2c_read_blocking(I2C_PORT, addr, buf, len, false);
}

static int16_t combine_bytes(uint8_t high, uint8_t low) {
    return (int16_t)(((uint16_t)high << 8) | low);
}

static uint8_t detect_mpu6050_address(void) {
    uint8_t who = i2c_read_reg(MPU6050_ADDR, WHO_AM_I);
    if (who == 0x68 || who == 0x98) return MPU6050_ADDR;

    who = i2c_read_reg(MPU6050_ALT_ADDR, WHO_AM_I);
    if (who == 0x68 || who == 0x98) return MPU6050_ALT_ADDR;

    return 0xFF;
}

static void mpu6050_init(uint8_t addr) {
    i2c_write_reg(addr, PWR_MGMT_1, 0x00);
    i2c_write_reg(addr, ACCEL_CONFIG, 0x00);
    i2c_write_reg(addr, GYRO_CONFIG, 0x18);
}

bool mpu6050_setup(void) {
    g_imu_addr = detect_mpu6050_address();
    if (g_imu_addr == 0xFF) return false;

    mpu6050_init(g_imu_addr);
    return true;
}

void mpu6050_read_all(uint8_t addr, mpu6050_data_t *d) {
    uint8_t buf[14];
    i2c_read_burst(addr, ACCEL_XOUT_H, buf, 14);

    d->ax_raw   = combine_bytes(buf[0],  buf[1]);
    d->ay_raw   = combine_bytes(buf[2],  buf[3]);
    d->az_raw   = combine_bytes(buf[4],  buf[5]);
    d->temp_raw = combine_bytes(buf[6],  buf[7]);
    d->gx_raw   = combine_bytes(buf[8],  buf[9]);
    d->gy_raw   = combine_bytes(buf[10], buf[11]);
    d->gz_raw   = combine_bytes(buf[12], buf[13]);

    d->ax_g   = d->ax_raw * 0.000061f;
    d->ay_g   = d->ay_raw * 0.000061f;
    d->az_g   = d->az_raw * 0.000061f;
    d->temp_c = d->temp_raw / 340.0f + 36.53f;
    d->gx_dps = d->gx_raw * 0.007630f;
    d->gy_dps = d->gy_raw * 0.007630f;
    d->gz_dps = d->gz_raw * 0.007630f;
}
