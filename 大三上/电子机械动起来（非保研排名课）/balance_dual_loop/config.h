// 配置文件：引脚定义和参数设置
#ifndef CONFIG_H
#define CONFIG_H

// ========== 电机引脚 ==========
const int IN1 = 12;
const int IN2 = 13;
const int IN3 = 7;
const int IN4 = 6;
const int PWM_A = 9;
const int PWM_B = 10;

// ========== 编码器引脚 ==========
const int ENC_A1 = 4;  // 电机A编码器A相
const int ENC_A2 = 8;  // 电机A编码器B相
const int ENC_B1 = 2;  // 电机B编码器A相
const int ENC_B2 = 5;  // 电机B编码器B相

// ========== MPU6050地址 ==========
const int MPU_ADDR = 0x68;

// ========== 控制参数 ==========
const float ANGLE_THRESHOLD = 30.0;  // 角度保护阈值(度)
const float ANGLE_SETPOINT = 0.0;    // 目标角度(直立)

// ========== 角度环PID参数(仅Kp和Kd) ==========
float kp_angle = 10.0;   // 角度比例系数(增大以获得更强响应)
float kd_angle = 1;    // 角度微分系数(作用于陀螺仪)

// ========== 速度环PID参数(仅Kp和Ki) ==========
float kp_speed = 0.05;    // 速度比例系数
float ki_speed = kp_speed/100;    // 速度积分系数

// ========== 积分限幅 ==========
const float INTEGRAL_LIMIT_SPEED = 200.0;

#endif
