#include <Wire.h>
#include <PinChangeInterrupt.h>  // 引脚变化中断库（统一用于A/B编码器）

// MPU6050 Register Addresses
const int MPU_ADDR = 0x68;
int16_t AcX, AcY, AcZ, GyX, GyY, GyZ;
float angleX, gyroX;
float setpoint = 0;  // 目标平衡角度（直立状态）

// 角度安全阈值（±30°）
const float ANGLE_THRESHOLD = 10.0;

// ========== 角度环PID参数 ==========
// 角度环：控制车身直立，输出为速度目标值
float kp_angle = 14.0;   // 比例系数
float ki_angle = 2.0;    // 积分系数
float kd_angle = 0.05;   // 微分系数
float error_angle = 0;
float lastError_angle = 0;
float integral_angle = 0;
float derivative_angle = 0;
float output_angle = 0;  // 角度环输出（作为速度环的目标值）

// ========== 速度环PID参数 ==========
// 速度环：控制电机转速，输出为PWM控制量
float kp_speed = 1.0;    // 比例系数
float ki_speed = 0.5;    // 积分系数
float kd_speed = 0.01;    // 微分系数
float error_speedA = 0, error_speedB = 0;
float lastError_speedA = 0, lastError_speedB = 0;
float integral_speedA = 0, integral_speedB = 0;
float derivative_speedA = 0, derivative_speedB = 0;
float output_speedA = 0, output_speedB = 0;
float targetSpeed = 0;   // 速度环目标值（来自角度环输出）

// ========== 位置环PID参数 ==========
// 位置环：控制小车位置，输出为角度偏移量
float kp_position = 0.0;  // 比例系数
float ki_position = 0.0; // 积分系数
float kd_position = 0.0;  // 微分系数
float error_position = 0;
float lastError_position = 0;
float integral_position = 0;
float derivative_position = 0;
float output_position = 0;  // 位置环输出（作为角度环的偏移）
float targetPosition = 0;   // 目标位置（编码器脉冲数）
float currentPosition = 0;  // 当前位置（编码器脉冲数平均值）

// ========== 控制模式 ==========
// 始终使用三环级联：位置环 -> 角度环 -> 速度环 -> PWM

// ========== 积分限幅参数 ==========
const float INTEGRAL_LIMIT_ANGLE = 500.0;
const float INTEGRAL_LIMIT_SPEED = 300.0;
const float INTEGRAL_LIMIT_POSITION = 1000.0;

// 电机引脚定义（根据实际接线修改）
const int IN1 = 12;
const int IN2 = 13;
const int IN3 = 7;
const int IN4 = 6;
const int PWM_A = 9;
const int PWM_B = 10;

// 编码器引脚定义（需支持PCINT，如UNO的2/3/4/5脚均支持）
const int encoderA1 = 2;  // 电机A编码器A相
const int encoderA2 = 3;  // 电机A编码器B相
const int encoderB1 = 4;  // 电机B编码器A相
const int encoderB2 = 5;  // 电机B编码器B相

// 编码器参数（根据实际编码器手册修改）
const int PULSES_PER_REV_A = 100;  // 电机A编码器每转脉冲数
const int PULSES_PER_REV_B = 100;  // 电机B编码器每转脉冲数（允许与A不同）

// ========== 车轮参数（用于位置计算）==========
const float WHEEL_DIAMETER = 65.0;  // 车轮直径（mm）
const float GEAR_RATIO = 30.0;      // 减速比
const float MM_PER_PULSE_A = (PI * WHEEL_DIAMETER) / (PULSES_PER_REV_A * GEAR_RATIO);
const float MM_PER_PULSE_B = (PI * WHEEL_DIAMETER) / (PULSES_PER_REV_B * GEAR_RATIO);

// 编码器计数与速度变量
volatile long encoderCountA = 0;  // 电机A计数（volatile用于中断访问）
volatile long encoderCountB = 0;  // 电机B计数
long lastEncoderCountA = 0;
long lastEncoderCountB = 0;
unsigned long lastSpeedCalcTime = 0;
float motorSpeedA = 0.0;  // 电机A转速（RPM）
float motorSpeedB = 0.0;  // 电机B转速（RPM）

// 速度平滑：滑动平均参数（5次采样）
const int SPEED_HISTORY_LEN = 5;
float speedAHistory[SPEED_HISTORY_LEN] = {0};
float speedBHistory[SPEED_HISTORY_LEN] = {0};
int historyIndex = 0;

// ========== 控制周期 ==========
const float DT = 0.01;  // 控制周期10ms = 0.01s

// ========== 速度同步控制参数 ==========
float kp_sync = 1.0;      // 速度同步比例系数
float ki_sync = 0.2;      // 速度同步积分系数
float kd_sync = 0.05;     // 速度同步微分系数
float error_sync = 0;
float lastError_sync = 0;
float integral_sync = 0;
float derivative_sync = 0;
const float INTEGRAL_LIMIT_SYNC = 100.0;

// 初始化MPU6050
void initMPU6050() {
  Wire.begin();
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B);  // PWR_MGMT_1寄存器
  Wire.write(0);     // 唤醒MPU6050
  Wire.endTransmission(true);
}

// 读取MPU6050原始数据
void readMPU6050() {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B);  // 从ACCEL_XOUT_H开始读取
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_ADDR, 14, true);  // 读取14字节数据
  
  AcX = Wire.read() << 8 | Wire.read();
  AcY = Wire.read() << 8 | Wire.read();
  AcZ = Wire.read() << 8 | Wire.read();
  Wire.read() << 8 | Wire.read();  // 跳过温度数据
  GyX = Wire.read() << 8 | Wire.read();
  GyY = Wire.read() << 8 | Wire.read();
  GyZ = Wire.read() << 8 | Wire.read();
}

// 计算角度（加速度计+陀螺仪融合）
void calculateAngle() {
  // 加速度计角度
  float accel_angle = atan2(AcY, AcZ) * RAD_TO_DEG;
  // 陀螺仪角速度（度/秒）
  gyroX = GyX / 131.0;
  // 互补滤波融合
  angleX = 0.96 * (angleX + gyroX * 0.01) + 0.04 * accel_angle;
}

// 电机控制函数
void setMotor(int speedA, int speedB) {
  // 电机A方向与PWM
  if (speedA > 0) {
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, HIGH);
  } else {
    digitalWrite(IN1, HIGH);
    digitalWrite(IN2, LOW);
  }
  analogWrite(PWM_A, abs(speedA));
  
  // 电机B方向与PWM
  if (speedB > 0) {
    digitalWrite(IN3, HIGH);
    digitalWrite(IN4, LOW);
  } else {
    digitalWrite(IN3, LOW);
    digitalWrite(IN4, HIGH);
  }
  analogWrite(PWM_B, abs(speedB));
}

// 停止所有电机
void stopMotors() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
  analogWrite(PWM_A, 0);
  analogWrite(PWM_B, 0);
}

// 电机A编码器中断服务函数（精简逻辑）
void handleEncoderA() {
  int a = digitalRead(encoderA1);
  int b = digitalRead(encoderA2);
  encoderCountA += (a != b) ? 1 : -1;  // 正转+1，反转-1
}

// 电机B编码器中断服务函数（精简逻辑）
void handleEncoderB() {
  int a = digitalRead(encoderB1);
  int b = digitalRead(encoderB2);
  encoderCountB += (a != b) ? 1 : -1;  // 正转+1，反转-1
}

// 计算电机转速（带滑动平均平滑）
void calculateMotorSpeed() {
  unsigned long currentTime = millis();
  unsigned long timeDiff = currentTime - lastSpeedCalcTime;
  
  if (timeDiff >= 200) {  // 延长计算窗口至200ms，减少波动
    // 计算脉冲差
    long pulseDiffA = encoderCountA - lastEncoderCountA;
    long pulseDiffB = encoderCountB - lastEncoderCountB;
    
    // 计算瞬时速度（RPM）
    float tempSpeedA = (pulseDiffA * 60.0 * 1000.0) / (PULSES_PER_REV_A * timeDiff);
    float tempSpeedB = (pulseDiffB * 60.0 * 1000.0) / (PULSES_PER_REV_B * timeDiff);
    
    // 滑动平均：更新历史数据并求平均
    speedAHistory[historyIndex] = tempSpeedA;
    speedBHistory[historyIndex] = tempSpeedB;
    historyIndex = (historyIndex + 1) % SPEED_HISTORY_LEN;  // 循环索引
    
    // 计算平均速度（平滑后）
    motorSpeedA = 0;
    motorSpeedB = 0;
    for (int i = 0; i < SPEED_HISTORY_LEN; i++) {
      motorSpeedA += speedAHistory[i];
      motorSpeedB += speedBHistory[i];
    }
    motorSpeedA /= SPEED_HISTORY_LEN;
    motorSpeedB /= SPEED_HISTORY_LEN;
    
    // 更新历史计数和时间
    lastEncoderCountA = encoderCountA;
    lastEncoderCountB = encoderCountB;
    lastSpeedCalcTime = currentTime;
  }
}

// ========== 角度环PID控制 ==========
// 输入：目标角度、当前角度
// 输出：速度目标值
float anglePID(float target, float current) {
  // 计算偏差 e(k)
  error_angle = target - current;
  
  // 积分项 Σe(k)
  integral_angle += error_angle * DT;
  integral_angle = constrain(integral_angle, -INTEGRAL_LIMIT_ANGLE, INTEGRAL_LIMIT_ANGLE);
  
  // 微分项 [e(k) - e(k-1)]
  derivative_angle = (error_angle - lastError_angle) / DT;
  
  // PID公式：u(k) = kp*e(k) + ki*Σe(k) + kd*[e(k)-e(k-1)]
  output_angle = kp_angle * error_angle + 
                 ki_angle * integral_angle + 
                 kd_angle * derivative_angle;
  
  lastError_angle = error_angle;
  
  return output_angle;
}

// ========== 速度环PID控制 ==========
// 输入：目标速度、当前速度
// 输出：PWM控制量
float speedPID(float target, float current, 
               float &error, float &lastError, 
               float &integral, float &derivative) {
  // 计算偏差 e(k)
  error = target - current;
  
  // 积分项 Σe(k)
  integral += error * DT;
  integral = constrain(integral, -INTEGRAL_LIMIT_SPEED, INTEGRAL_LIMIT_SPEED);
  
  // 微分项 [e(k) - e(k-1)]
  derivative = (error - lastError) / DT;
  
  // PID公式：u(k) = kp*e(k) + ki*Σe(k) + kd*[e(k)-e(k-1)]
  float output = kp_speed * error + 
                 ki_speed * integral + 
                 kd_speed * derivative;
  
  lastError = error;
  
  return output;
}

// ========== 位置环PID控制 ==========
// 输入：目标位置、当前位置
// 输出：角度偏移量
float positionPID(float target, float current) {
  // 计算偏差 e(k)
  error_position = target - current;
  
  // 积分项 Σe(k)
  integral_position += error_position * DT;
  integral_position = constrain(integral_position, -INTEGRAL_LIMIT_POSITION, INTEGRAL_LIMIT_POSITION);
  
  // 微分项 [e(k) - e(k-1)]
  derivative_position = (error_position - lastError_position) / DT;
  
  // PID公式：u(k) = kp*e(k) + ki*Σe(k) + kd*[e(k)-e(k-1)]
  output_position = kp_position * error_position + 
                    ki_position * integral_position + 
                    kd_position * derivative_position;
  
  lastError_position = error_position;
  
  return output_position;
}

// ========== 速度同步PID控制 ==========
// 输入：两轮速度差
// 输出：PWM补偿量
float speedSyncPID(float speedDiff) {
  // 计算偏差 e(k) = 速度差（目标是0）
  error_sync = speedDiff;
  
  // 积分项 Σe(k)
  integral_sync += error_sync * DT;
  integral_sync = constrain(integral_sync, -INTEGRAL_LIMIT_SYNC, INTEGRAL_LIMIT_SYNC);
  
  // 微分项 [e(k) - e(k-1)]
  derivative_sync = (error_sync - lastError_sync) / DT;
  
  // PID公式：u(k) = kp*e(k) + ki*Σe(k) + kd*[e(k)-e(k-1)]
  float correction = kp_sync * error_sync + 
                     ki_sync * integral_sync + 
                     kd_sync * derivative_sync;
  
  lastError_sync = error_sync;
  
  return correction;
}

// ========== 解析串口指令 ==========
void processSerialCommands() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    
    // 设置目标位置："pos:1000"
    if (input.startsWith("pos:")) {
      targetPosition = input.substring(4).toFloat();
      Serial.print("Target position set to: ");
      Serial.println(targetPosition);
    }
    // 调整角度PID参数："ap:16,2,0.05"
    else if (input.startsWith("ap:")) {
      String data = input.substring(3);
      int c1 = data.indexOf(',');
      int c2 = data.lastIndexOf(',');
      if (c1 != -1 && c2 != -1) {
        kp_angle = data.substring(0, c1).toFloat();
        ki_angle = data.substring(c1 + 1, c2).toFloat();
        kd_angle = data.substring(c2 + 1).toFloat();
        Serial.print("Angle PID: Kp=");
        Serial.print(kp_angle);
        Serial.print(", Ki=");
        Serial.print(ki_angle);
        Serial.print(", Kd=");
        Serial.println(kd_angle);
      }
    }
    // 调整速度PID参数："sp:2,0.5,0.1"
    else if (input.startsWith("sp:")) {
      String data = input.substring(3);
      int c1 = data.indexOf(',');
      int c2 = data.lastIndexOf(',');
      if (c1 != -1 && c2 != -1) {
        kp_speed = data.substring(0, c1).toFloat();
        ki_speed = data.substring(c1 + 1, c2).toFloat();
        kd_speed = data.substring(c2 + 1).toFloat();
        Serial.print("Speed PID: Kp=");
        Serial.print(kp_speed);
        Serial.print(", Ki=");
        Serial.print(ki_speed);
        Serial.print(", Kd=");
        Serial.println(kd_speed);
      }
    }
    // 调整位置PID参数："pp:0.5,0.01,0.2"
    else if (input.startsWith("pp:")) {
      String data = input.substring(3);
      int c1 = data.indexOf(',');
      int c2 = data.lastIndexOf(',');
      if (c1 != -1 && c2 != -1) {
        kp_position = data.substring(0, c1).toFloat();
        ki_position = data.substring(c1 + 1, c2).toFloat();
        kd_position = data.substring(c2 + 1).toFloat();
        Serial.print("Position PID: Kp=");
        Serial.print(kp_position);
        Serial.print(", Ki=");
        Serial.print(ki_position);
        Serial.print(", Kd=");
        Serial.println(kd_position);
      }
    }
    // 调整速度同步PID参数："sync:1,0.2,0.05"
    else if (input.startsWith("sync:")) {
      String data = input.substring(5);
      int c1 = data.indexOf(',');
      int c2 = data.lastIndexOf(',');
      if (c1 != -1 && c2 != -1) {
        kp_sync = data.substring(0, c1).toFloat();
        ki_sync = data.substring(c1 + 1, c2).toFloat();
        kd_sync = data.substring(c2 + 1).toFloat();
        Serial.print("Speed Sync PID: Kp=");
        Serial.print(kp_sync);
        Serial.print(", Ki=");
        Serial.print(ki_sync);
        Serial.print(", Kd=");
        Serial.println(kd_sync);
      }
    }
    // 重置所有积分项："reset"
    else if (input.equals("reset")) {
      integral_angle = 0;
      integral_speedA = 0;
      integral_speedB = 0;
      integral_position = 0;
      integral_sync = 0;
      encoderCountA = 0;
      encoderCountB = 0;
      targetPosition = 0;
      Serial.println("All integrals and encoders reset");
    }
    // 帮助信息
    else if (input.equals("help")) {
      Serial.println("=== PID Balance Car (3-Loop Cascade) ===");
      Serial.println("pos:1000 - Set target position");
      Serial.println("ap:Kp,Ki,Kd - Set angle PID params");
      Serial.println("sp:Kp,Ki,Kd - Set speed PID params");
      Serial.println("pp:Kp,Ki,Kd - Set position PID params");
      Serial.println("sync:Kp,Ki,Kd - Set speed sync PID params");
      Serial.println("reset - Reset all integrals");
      Serial.println("help - Show this message");
    }
  }
}

void setup() {
  Serial.begin(9600);
  initMPU6050();
  
  // 初始化电机引脚
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);
  pinMode(PWM_A, OUTPUT);
  pinMode(PWM_B, OUTPUT);
  
  // 初始化编码器引脚（启用内部上拉）
  pinMode(encoderA1, INPUT_PULLUP);
  pinMode(encoderA2, INPUT_PULLUP);
  pinMode(encoderB1, INPUT_PULLUP);
  pinMode(encoderB2, INPUT_PULLUP);
  
  // 统一使用PinChangeInterrupt（消除中断类型差异）
  attachPinChangeInterrupt(
    digitalPinToPinChangeInterrupt(encoderA1),
    handleEncoderA,
    CHANGE
  );
  attachPinChangeInterrupt(
    digitalPinToPinChangeInterrupt(encoderB1),
    handleEncoderB,
    CHANGE
  );
  
  // 初始化速度历史数组
  for (int i = 0; i < SPEED_HISTORY_LEN; i++) {
    speedAHistory[i] = 0;
    speedBHistory[i] = 0;
  }
  
  delay(1000);  // 等待传感器稳定
  Serial.println("System initialized. Ready for commands.");
}

void loop() {
  readMPU6050();        // 读取MPU数据
  calculateAngle();     // 计算角度
  calculateMotorSpeed();// 计算转速（带平滑）
  processSerialCommands();// 处理串口指令
  
  // 计算当前位置（两轮平均）
  currentPosition = (encoderCountA + encoderCountB) / 2.0;
  
  // 角度安全检查
  if (abs(angleX - setpoint) > ANGLE_THRESHOLD) {
    stopMotors();
    Serial.println("Angle out of range! Motors stopped.");
  } else {
    // ========== 三环级联PID控制 ==========
    // 位置环 -> 角度环 -> 速度环 -> PWM
    
    // 1. 位置环：输出角度偏移
    output_position = positionPID(targetPosition, currentPosition);
    float angleTarget = setpoint + constrain(output_position, -5.0, 5.0);  // 限制角度偏移±5°
    
    // 2. 角度环：输出速度目标
    targetSpeed = anglePID(angleTarget, angleX);
    targetSpeed = constrain(targetSpeed, -100, 100);  // 限制目标速度
    
    // 3. 速度环：输出PWM
    float pwmA = speedPID(targetSpeed, motorSpeedA, error_speedA, lastError_speedA, 
                    integral_speedA, derivative_speedA);
    float pwmB = speedPID(targetSpeed, motorSpeedB, error_speedB, lastError_speedB, 
                    integral_speedB, derivative_speedB);
    
    // ========== 速度同步控制（确保两轮速度一致）==========
    // 计算两轮速度差
    float speedDiff = motorSpeedA - motorSpeedB;
    
    // 使用PID控制器计算补偿量
    float syncCorrection = speedSyncPID(speedDiff);
    
    // 对速度快的轮子减速，慢的轮子加速
    pwmA -= syncCorrection;
    pwmB += syncCorrection;
    
    // PWM输出限幅并控制电机
    pwmA = constrain(pwmA, -255, 255);
    pwmB = constrain(pwmB, -255, 255);
    setMotor((int)pwmA, (int)pwmB);
  }
  
  // ========== 串口监控输出 ==========
  Serial.print("Ang:");
  Serial.print(angleX, 1);
  Serial.print(" Pos:");
  Serial.print(currentPosition, 0);
  Serial.print("/");
  Serial.print(targetPosition, 0);
  Serial.print(" Spd:");
  Serial.print(motorSpeedA, 1);
  Serial.print("/");
  Serial.print(motorSpeedB, 1);
  Serial.print(" Diff:");
  Serial.print(motorSpeedA - motorSpeedB, 1);
  Serial.print(" TgtSpd:");
  Serial.println(targetSpeed, 1);
  
  delay(10);  // 控制周期~10ms（100Hz）
}