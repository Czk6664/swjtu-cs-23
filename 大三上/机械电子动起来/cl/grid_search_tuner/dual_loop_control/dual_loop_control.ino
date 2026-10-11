// ==================== 双环控制系统 ====================
// 角度环：5ms更新，仅Kp和Kd
// 速度环：10ms更新，仅Kp和Ki
// 输出：角度环 - 速度环

#include <MsTimer2.h>
#include "config.h"
#include "sensors.h"
#include "control.h"

// 定时器标志
volatile bool angle_flag = false;
volatile bool speed_flag = false;

// 定时器中断（5ms触发）
void timerISR() {
  // 每5ms同时触发角度环和速度环
  angle_flag = true;
  speed_flag = true;
}

void setup() {
  Serial.begin(9600);
  delay(100);  // 等待串口稳定
  
  Serial.println("\n========================================");
  Serial.println("   初始化开始...");
  Serial.println("========================================");
  
  // 初始化MPU6050
  Serial.print("1. 初始化MPU6050...");
  initMPU6050();
  delay(100);
  Serial.println(" 完成");
  
  // 测试MPU6050通信
  Serial.print("2. 测试MPU6050通信...");
  readMPU6050();
  Serial.print(" AcX="); Serial.print(AcX);
  Serial.print(" AcY="); Serial.print(AcY);
  Serial.print(" AcZ="); Serial.println(AcZ);
  
  // 初始化编码器
  Serial.print("3. 初始化编码器...");
  pinMode(ENC_A, INPUT_PULLUP);
  pinMode(ENC_B, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(ENC_A), encoderISR, CHANGE);
  Serial.println(" 完成");
  
  // 初始化电机引脚
  Serial.print("4. 初始化电机引脚...");
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);
  pinMode(PWM_A, OUTPUT);
  pinMode(PWM_B, OUTPUT);
  Serial.println(" 完成");
  
  // 等待传感器稳定
  Serial.print("5. 等待传感器稳定");
  for(int i = 0; i < 10; i++) {
    readMPU6050();
    calculateAngle();
    Serial.print(".");
    delay(100);
  }
  Serial.println(" 完成");
  
  Serial.print("6. 初始角度: ");
  Serial.print(angleX, 2);
  Serial.println(" 度");
  
  Serial.println("\n========================================");
  Serial.println("   双环控制系统启动成功");
  Serial.println("========================================");
  Serial.println("角度环: 5ms更新 (Kp + Kd)");
  Serial.println("速度环: 5ms更新 (Kp + Ki)");
  Serial.println("输出: 角度环 - 速度环");
  Serial.println();
  Serial.print("角度环参数 - Kp: "); Serial.print(kp_angle);
  Serial.print(" Kd: "); Serial.println(kd_angle);
  Serial.print("速度环参数 - Kp: "); Serial.print(kp_speed);
  Serial.print(" Ki: "); Serial.println(ki_speed);
  Serial.println("优化: 降低速度环参数，防止积分累积");
  Serial.println("========================================");
  Serial.println("请将小车放置在直立位置...");
  Serial.println("3秒后开始运行...");
  delay(3000);
  
  // 启动定时器（5ms间隔）- 在准备好后再启动
  Serial.print("7. 启动定时器...");
  MsTimer2::set(ANGLE_INTERVAL, timerISR);
  MsTimer2::start();
  Serial.println(" 完成");
  
  Serial.println("\n开始运行！\n");
}

void loop() {
  // 角度环控制（5ms）
  if (angle_flag) {
    angle_flag = false;
    
    readMPU6050();
    calculateAngle();
    angleControl();
    setMotor();
  }
  
  // 速度环控制（10ms）
  if (speed_flag) {
    speed_flag = false;
    
    calculateSpeed();
    speedControl();
  }
  
  // 状态输出（每秒一次）
  static unsigned long last_print = 0;
  if (millis() - last_print >= 1000) {
    last_print = millis();
    
    Serial.print("角度: "); Serial.print(angleX, 2);
    Serial.print(" | 角速度: "); Serial.print(gyroX, 2);
    Serial.print(" | 速度: "); Serial.print(current_speed, 1);
    Serial.print(" | 角度输出: "); Serial.print(angle_output, 1);
    Serial.print(" | 速度输出: "); Serial.print(speed_output, 1);
    Serial.print(" | 电机: "); Serial.println(motor_output);
  }
}
