// ==================== 传感器模块 ====================
#ifndef SENSORS_H
#define SENSORS_H

#include <Wire.h>
#include "config.h"

// MPU6050数据
int16_t AcX, AcY, AcZ, GyX, GyY, GyZ;
float angleX = 0;
float gyroX = 0;

// 编码器数据
volatile long enc_count = 0;
float current_speed = 0;

// 初始化MPU6050
void initMPU6050() {
  Wire.begin();
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B);
  Wire.write(0);
  Wire.endTransmission(true);
}

// 读取MPU6050
void readMPU6050() {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_ADDR, 14, true);
  
  AcX = Wire.read() << 8 | Wire.read();
  AcY = Wire.read() << 8 | Wire.read();
  AcZ = Wire.read() << 8 | Wire.read();
  Wire.read() << 8 | Wire.read();
  GyX = Wire.read() << 8 | Wire.read();
  GyY = Wire.read() << 8 | Wire.read();
  GyZ = Wire.read() << 8 | Wire.read();
}

// 计算角度（互补滤波）- 使用grid_search_tuner的时间常数
void calculateAngle() {
  float accel_angle = atan2(AcY, AcZ) * RAD_TO_DEG;
  gyroX = GyX / 131.0;
  angleX = 0.96 * (angleX + gyroX * 0.01) + 0.04 * accel_angle;  // 10ms时间常数
}

// 编码器中断
void encoderISR() {
  if (digitalRead(ENC_A) == digitalRead(ENC_B)) enc_count++;
  else enc_count--;
}

// 计算速度
void calculateSpeed() {
  static long last_count = 0;
  current_speed = enc_count - last_count;
  last_count = enc_count;
}

#endif
