#include <Wire.h>  // 仅使用内置I2C库，符合教程硬件依赖

// 1. 硬件引脚与核心参数定义（教程1-6、1-11）
// MPU6050（角度环，教程1-10至1-11）
const int MPU_ADDR = 0x68;
int16_t AcX, AcY, AcZ, GyX, GyY, GyZ;
float angleX, gyroX;
float angle_setpoint = 0;         // 角度环目标（直立状态，教程1-11）
const float PROTECT_ANGLE = 15.0;  // 15度保护角度

// 编码器（速度环，教程1-8至1-9：M法测速）
const int ENC_A = 2;
const int ENC_B = 3;
volatile long enc_count = 0;
float current_speed = 0;
float speed_setpoint = 0;

// 电机（执行器，教程：PID输出PWM控制）
const int IN1 = 12;
const int IN2 = 13;
const int IN3 = 7;
const int IN4 = 6;
const int PWM_A = 9;
const int PWM_B = 10;

// 2. 双环PID参数+全局电机输出变量（关键修复：扩大motor_output作用域）
// 角度环PID（教程1-11：控制直立）
float kp_angle = 65.0;
float ki_angle = 1.30;
float kd_angle = 0.012;
float error_angle, lastError_angle, integral_angle, derivative_angle;
float angle_output;

// 速度环PID（教程1-9：控制车速）
float kp_speed = 0.0;
float ki_speed = 0.0;
float kd_speed = 0.0;
float error_speed, lastError_speed, integral_speed, derivative_speed;
float speed_output;

// 关键修复：将motor_output定义为全局变量，确保loop()可引用
int motor_output = 0;

// 初始化MPU6050（教程1-11：唤醒传感器）
void initMPU6050() {
  Wire.begin();
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B);  // PWR_MGMT_1寄存器
  Wire.write(0);     // 唤醒MPU6050
  Wire.endTransmission(true);
}

// 读取MPU6050原始数据（教程1-11：角度环输入）
void readMPU6050() {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B);  // 从ACCEL_XOUT_H开始读取
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_ADDR, 14, true);
  
  AcX = Wire.read() << 8 | Wire.read();
  AcY = Wire.read() << 8 | Wire.read();
  AcZ = Wire.read() << 8 | Wire.read();
  Wire.read() << 8 | Wire.read();  // 跳过温度数据
  GyX = Wire.read() << 8 | Wire.read();
  GyY = Wire.read() << 8 | Wire.read();
  GyZ = Wire.read() << 8 | Wire.read();
}

// 计算角度（加速度计+陀螺仪融合，教程1-11：倾斜角度为误差）
void calculateAngle() {
  float accel_angle = atan2(AcY, AcZ) * RAD_TO_DEG;
  gyroX = GyX / 131.0;  // 陀螺仪数据转换（度/秒）
  angleX = 0.96 * (angleX + gyroX * 0.01) + 0.04 * accel_angle;  // 互补滤波
}

// 编码器中断（教程1-6：累计脉冲数，速度计算依据）
void encoderISR() {
  if (digitalRead(ENC_A) == digitalRead(ENC_B)) enc_count++;
  else enc_count--;
}

// 计算当前速度（教程1-9：M法测速=单位时间脉冲数）
void calculateSpeed() {
  static unsigned long last_time = 0;
  static long last_count = 0;
  unsigned long current_time = millis();
  
  if (current_time - last_time >= 10) {
    current_speed = enc_count - last_count;  // 速度单位：脉冲/10ms
    last_count = enc_count;
    last_time = current_time;
  }
}

// 角度环PID计算（教程1-2离散PID公式）
void anglePID() {
  error_angle = angle_setpoint - angleX;
  integral_angle += error_angle * 0.01;
  derivative_angle = (error_angle - lastError_angle) / 0.01;
  
  // 积分限幅（教程1-7：防止积分饱和）
  if (integral_angle > 500) integral_angle = 500;
  if (integral_angle < -500) integral_angle = -500;
  
  angle_output = kp_angle * error_angle + ki_angle * integral_angle + kd_angle * derivative_angle;
  lastError_angle = error_angle;
}

// 速度环PID计算（教程1-2离散PID公式）
void speedPID() {
  error_speed = speed_setpoint - current_speed;
  integral_speed += error_speed * 0.01;
  derivative_speed = (error_speed - lastError_speed) / 0.01;
  
  // 积分限幅（教程1-7：防止执行器过载）
  if (integral_speed > 200) integral_speed = 200;
  if (integral_speed < -200) integral_speed = -200;
  
  speed_output = kp_speed * error_speed + ki_speed * integral_speed + kd_speed * derivative_speed;
  lastError_speed = error_speed;
}

// 电机控制（含角度保护，使用全局motor_output变量）
void setMotor() {
  // 角度保护：超15度停止电机
  if (abs(angleX) > PROTECT_ANGLE) {
    motor_output = 0;  // 全局变量赋值：停止状态
    analogWrite(PWM_A, 0);
    analogWrite(PWM_B, 0);
    Serial.println("Angle Over 15°! Motor Stopped");
    return;
  }
  
  // 正常控制：融合双环输出（教程1-3多环协同逻辑）
  motor_output = speed_output + angle_output;
  // 输出限幅（PWM范围0-255，教程1-7执行器约束）
  if (motor_output > 255) motor_output = 255;
  if (motor_output < -255) motor_output = -255;
  
  // 电机A控制
  if (motor_output > 0) {
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, HIGH);
  } else {
    digitalWrite(IN1, HIGH);
    digitalWrite(IN2, LOW);
  }
  analogWrite(PWM_A, abs(motor_output));
  
  // 电机B控制
  if (motor_output > 0) {
    digitalWrite(IN3, HIGH);
    digitalWrite(IN4, LOW);
  } else {
    digitalWrite(IN3, LOW);
    digitalWrite(IN4, HIGH);
  }
  analogWrite(PWM_B, abs(motor_output));
}

// 初始化函数（Arduino核心入口）
void setup() {
  Serial.begin(9600);
  initMPU6050();
  
  // 初始化编码器（教程1-9：中断读取脉冲）
  pinMode(ENC_A, INPUT_PULLUP);
  pinMode(ENC_B, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(ENC_A), encoderISR, CHANGE);
  
  // 初始化电机引脚
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);
  pinMode(PWM_A, OUTPUT);
}
