// ==================== 硬件配置 ====================
#ifndef CONFIG_H
#define CONFIG_H

// MPU6050配置
const int MPU_ADDR = 0x68;

// 编码器引脚
const int ENC_A = 2;
const int ENC_B = 3;

// 电机驱动引脚
const int IN1 = 12;
const int IN2 = 13;
const int IN3 = 7;
const int IN4 = 6;
const int PWM_A = 9;
const int PWM_B = 10;

// 保护角度
const float PROTECT_ANGLE = 25.0;

// 平衡角度设定 - 使用grid_search_tuner的值
const float ANGLE_SETPOINT = -0.2;  // 从grid_search_tuner的angle_setpoint

// 定时器间隔
const int ANGLE_INTERVAL = 5;   // 5ms角度环
const int SPEED_INTERVAL = 10;  // 10ms速度环

#endif
