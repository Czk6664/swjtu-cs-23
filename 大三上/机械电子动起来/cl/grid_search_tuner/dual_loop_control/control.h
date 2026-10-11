// ==================== 控制模块 ====================
#ifndef CONTROL_H
#define CONTROL_H

#include "config.h"
#include "sensors.h"

// 角度环参数（仅Kp和Kd）- 使用grid_search_tuner的最佳参数
float kp_angle = 25.0;  // 从grid_search_tuner的BEST_KP_ANGLE
float kd_angle = 0.15;  // 从grid_search_tuner调整后的值
float angle_output = 0;

// 速度环参数（仅Kp和Ki）- 使用grid_search_tuner的最佳参数
float kp_speed = 1.5;   // 从grid_search_tuner的BEST_KP_SPEED
float ki_speed = 0.1;   // 从grid_search_tuner的BEST_KI_SPEED
float speed_setpoint = 0;
float speed_output = 0;
float speed_integral = 0;

// 最终输出
int motor_output = 0;

// 角度环控制（误差×Kp - Kd×角速度）
void angleControl() {
  float error = ANGLE_SETPOINT - angleX;
  angle_output = kp_angle * error - kd_angle * gyroX;
}

// 速度环控制（仅Kp和Ki）
void speedControl() {
  float error = speed_setpoint - current_speed;
  speed_integral += error * 0.01;  // 使用grid_search_tuner的时间常数
  
  // 积分限幅（参考grid_search_tuner）
  if (speed_integral > 200) speed_integral = 200;
  if (speed_integral < -200) speed_integral = -200;
  
  speed_output = kp_speed * error + ki_speed * speed_integral;
  
  // 输出限幅（不要过度限制）
  if (speed_output > 100) speed_output = 100;
  if (speed_output < -100) speed_output = -100;
}

// 设置电机输出
void setMotor() {
  // 倾角保护
  if (abs(angleX) > PROTECT_ANGLE) {
    motor_output = 0;
    speed_integral = 0;  // 清零积分，防止累积
    analogWrite(PWM_A, 0);
    analogWrite(PWM_B, 0);
    return;
  }
  
  // 最终输出 = 角度环 - 速度环
  motor_output = angle_output - speed_output;
  
  // 输出限幅
  if (motor_output > 255) motor_output = 255;
  if (motor_output < -255) motor_output = -255;
  
  // 电机A
  if (motor_output > 0) {
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, HIGH);
  } else {
    digitalWrite(IN1, HIGH);
    digitalWrite(IN2, LOW);
  }
  analogWrite(PWM_A, abs(motor_output));
  
  // 电机B
  if (motor_output > 0) {
    digitalWrite(IN3, HIGH);
    digitalWrite(IN4, LOW);
  } else {
    digitalWrite(IN3, LOW);
    digitalWrite(IN4, HIGH);
  }
  analogWrite(PWM_B, abs(motor_output));
}

#endif
