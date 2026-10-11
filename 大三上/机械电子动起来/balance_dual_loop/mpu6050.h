// MPU6050传感器模块
#ifndef MPU6050_H
#define MPU6050_H

#include <Arduino.h>
#include <Wire.h>
#include "config.h"

// 传感器数据
int16_t AcX, AcY, AcZ, GyX, GyY, GyZ;
float angleX = 0;     // 当前角度
float gyroX = 0;      // 陀螺仪角速度

// 初始化MPU6050
void initMPU6050() {
  Serial.println("  Starting I2C...");
  Wire.begin();
  Wire.setClock(400000);  // 设置I2C为400kHz快速模式
  Serial.println("  I2C started at 400kHz");
  
  Serial.println("  Waking up MPU6050...");
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B);  // PWR_MGMT_1寄存器
  Wire.write(0);     // 唤醒MPU6050
  byte error = Wire.endTransmission(true);
  
  if (error == 0) {
    Serial.println("  MPU6050 wakeup OK");
  } else {
    Serial.print("  MPU6050 init ERROR: ");
    Serial.println(error);
    Serial.println("  Check I2C connection!");
  }
  
  delay(50);  // 等待MPU6050启动
  Serial.println("  MPU6050 init complete");
}

// 读取MPU6050数据(在主循环中调用，带超时保护)
void readMPU6050() {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B);  // 从ACCEL_XOUT_H开始读取
  byte error = Wire.endTransmission(false);
  
  if (error != 0) {
    // I2C通信错误，使用上次的值
    return;
  }
  
  // 请求14字节数据（加速度6 + 温度2 + 陀螺仪6）
  Wire.requestFrom(MPU_ADDR, 14, true);
  
  // 等待数据，最多5ms超时
  unsigned long startTime = millis();
  while (Wire.available() < 14 && (millis() - startTime) < 5) {
    // 等待数据到达
  }
  
  if (Wire.available() >= 14) {
    AcX = Wire.read() << 8 | Wire.read();
    AcY = Wire.read() << 8 | Wire.read();
    AcZ = Wire.read() << 8 | Wire.read();
    Wire.read() << 8 | Wire.read();  // 跳过温度
    GyX = Wire.read() << 8 | Wire.read();
    GyY = Wire.read() << 8 | Wire.read();
    GyZ = Wire.read() << 8 | Wire.read();
  }
}

// 计算角度(互补滤波)
void calculateAngle() {
  float accel_angle = atan2(AcY, AcZ) * RAD_TO_DEG;
  gyroX = GyX / 131.0;  // 陀螺仪转换为度/秒
  angleX = 0.96 * (angleX + gyroX * 0.005) + 0.04 * accel_angle;  // 5ms周期
}

#endif
