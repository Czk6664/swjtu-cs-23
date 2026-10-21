// 双环PID平衡小车主程序
// 角度环(5ms) + 速度环(10ms)
// 使用MsTimer2定时器触发控制

#include <Wire.h>
#include <PinChangeInterrupt.h>
#include <MsTimer2.h>

#include "config.h"
#include "mpu6050.h"
#include "encoder.h"
#include "motor.h"
#include "control.h"

void setup() {
  Serial.begin(9600);
  delay(100);
  Serial.println("Starting...");
  
  // 初始化电机(先初始化，确保停止状态)
  Serial.println("Init Motor...");
  initMotor();
  stopMotor();
  
  // 初始化MPU6050
  Serial.println("Init MPU6050...");
  initMPU6050();
  delay(100);
  
  // 初始化编码器
  Serial.println("Init Encoder...");
  initEncoder();
  
  Serial.println("Waiting for sensor stable...");
  delay(500);
  
  // 读取初始角度(添加超时保护)
  Serial.println("Reading initial angle...");
  for(int i = 0; i < 10; i++) {
    Serial.print("Read ");
    Serial.print(i+1);
    Serial.print(": ");
    readMPU6050();
    Serial.print("MPU_OK ");
    calculateAngle();
    Serial.print("Angle=");
    Serial.println(angleX, 2);
    delay(10);
  }
  Serial.print("Final Initial angle: ");
  Serial.println(angleX);
  
  // 启动定时器：5ms触发一次
  Serial.println("Starting MsTimer2...");
  Serial.flush();  // 确保串口输出完成
  MsTimer2::set(5, timerISR);
  Serial.println("MsTimer2 configured");
  Serial.flush();
  MsTimer2::start();
  Serial.println("MsTimer2 started");
  Serial.flush();
  
  Serial.println("=== System Ready ===");
  Serial.println("t=test, p=params, r=reset");
}

void loop() {
  // 持续读取传感器数据（在主循环中，不在中断中）
  readMPU6050();
  calculateAngle();
  
  // 定期输出调试信息
  static unsigned long lastPrint = 0;
  if (millis() - lastPrint > 300) {
    lastPrint = millis();
    
    // 检查角度是否超限
    if (abs(angleX) > ANGLE_THRESHOLD) {
      Serial.print("*** STOPPED - Angle too large: ");
      Serial.println(angleX, 2);
    } else {
      Serial.print("Ang:");
      Serial.print(angleX, 2);
      Serial.print(" Gyro:");
      Serial.print(gyroX, 2);
      Serial.print(" AOut:");
      Serial.print(angle_output, 1);
      Serial.print(" SOut:");
      Serial.print(speed_output, 1);
      Serial.print(" Spd:");
      Serial.print((motorSpeedA + motorSpeedB) / 2.0, 1);
      Serial.print(" Final:");
      Serial.print(final_output);
      Serial.print(" EncA:");
      Serial.print(encoderCountA);
      Serial.print(" EncB:");
      Serial.println(encoderCountB);
    }
  }
  
  // 处理串口命令
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    
    // 调整角度环参数："a:30,0.8"
    if (cmd.startsWith("a:")) {
      int comma = cmd.indexOf(',');
      if (comma != -1) {
        kp_angle = cmd.substring(2, comma).toFloat();
        kd_angle = cmd.substring(comma + 1).toFloat();
        Serial.print("Angle: Kp=");
        Serial.print(kp_angle);
        Serial.print(", Kd=");
        Serial.println(kd_angle);
      }
    }
    // 调整速度环参数："s:0.5,0.1"
    else if (cmd.startsWith("s:")) {
      int comma = cmd.indexOf(',');
      if (comma != -1) {
        kp_speed = cmd.substring(2, comma).toFloat();
        ki_speed = cmd.substring(comma + 1).toFloat();
        Serial.print("Speed: Kp=");
        Serial.print(kp_speed);
        Serial.print(", Ki=");
        Serial.println(ki_speed);
      }
    }
    // 重置积分："r"
    else if (cmd.equals("r")) {
      integral_speed = 0;
      encoderCountA = 0;
      encoderCountB = 0;
      Serial.println("Reset done");
    }
    // 显示当前参数："p"
    else if (cmd.equals("p")) {
      Serial.print("Angle Kp=");
      Serial.print(kp_angle);
      Serial.print(" Kd=");
      Serial.println(kd_angle);
      Serial.print("Speed Kp=");
      Serial.print(kp_speed);
      Serial.print(" Ki=");
      Serial.println(ki_speed);
    }
    // 电机测试："t"
    else if (cmd.equals("t")) {
      Serial.println("Motor test: 100 PWM for 2 seconds");
      MsTimer2::stop();
      setMotor(100, 100);
      delay(2000);
      stopMotor();
      MsTimer2::start();
      Serial.println("Test done");
    }
  }
  
  // 不需要delay，让传感器读取尽可能快
}
