// 控制模块：双环PID控制逻辑
#ifndef CONTROL_H
#define CONTROL_H

#include <Arduino.h>
#include "config.h"
#include "mpu6050.h"
#include "encoder.h"
#include "motor.h"

// 速度环变量
float error_speed = 0;
float integral_speed = 0;
float targetSpeed = 0;

// 角度环输出
float angle_output = 0;

// 速度环输出
float speed_output = 0;

// 最终输出
int final_output = 0;

// 定时器计数
volatile int timer_count = 0;

// 角度环控制(5ms执行一次)
// 公式：output = Kp × 误差 + Kd × 陀螺仪角速度
// 注意：不在此函数中读取传感器，使用全局变量中的最新值
void angleControl() {
  // 计算角度误差
  float error_angle = ANGLE_SETPOINT - angleX;
  
  // 角度环输出 = Kp×误差 + Kd×陀螺仪 (提供阻尼)
  angle_output = kp_angle * error_angle + kd_angle * gyroX;
}

// 速度环控制(10ms执行一次)
// 公式：output = Kp × 误差 + Ki × 积分
void speedControl() {
  calculateSpeed();
  
  // 计算平均速度
  float currentSpeed = (motorSpeedA + motorSpeedB) / 2.0;
  
  // 速度误差
  error_speed = targetSpeed - currentSpeed;
  
  // 积分累加
  integral_speed += error_speed * 0.01;  // 10ms = 0.01s
  integral_speed = constrain(integral_speed, -INTEGRAL_LIMIT_SPEED, INTEGRAL_LIMIT_SPEED);
  
  // 速度环输出 = Kp×误差 + Ki×积分
  speed_output = kp_speed * error_speed + ki_speed * integral_speed;
}

// 定时器中断服务函数(5ms触发一次)
void timerISR() {
  static bool inISR = false;
  if (inISR) return;  // 防止重入
  inISR = true;
  
  timer_count++;
  
  // 每5ms执行角度环
  angleControl();
  
  // 每10ms执行速度环(timer_count为偶数时)
  if (timer_count % 2 == 0) {
    speedControl();
  }
  
  // 角度保护
  if (abs(angleX) > ANGLE_THRESHOLD) {
    stopMotor();
    integral_speed = 0;  // 重置积分
    inISR = false;
    return;
  }
  
  // 最终输出 = 角度环 + 速度环
  final_output = (int)(angle_output + speed_output);
  
  // PWM限幅
  final_output = constrain(final_output, -255, 255);
  
  // 输出到电机
  setMotor(final_output, final_output);
  
  inISR = false;
}

#endif
