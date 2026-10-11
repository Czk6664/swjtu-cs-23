#include <Wire.h>
#include <PinChangeInterrupt.h>
#include <EEPROM.h>  // 用于保存参数到EEPROM

// MPU6050 Register Addresses
const int MPU_ADDR = 0x68;
int16_t AcX, AcY, AcZ, GyX, GyY, GyZ;
float angleX, gyroX;
float setpoint = 0;  // 目标平衡角度（直立状态）

// 角度安全阈值
const float ANGLE_THRESHOLD = 30.0;  // 调参时放宽到±30°

// ========== PID参数（将被自动调整）==========
float kp_angle = 10.0;
float ki_angle = 0.0;
float kd_angle = 0.0;
float error_angle = 0;
float lastError_angle = 0;
float integral_angle = 0;
float derivative_angle = 0;
float output_angle = 0;

// ========== 网格搜索参数范围 ==========
// Kp范围
const float KP_MIN = 5.0;
const float KP_MAX = 25.0;
const float KP_STEP = 2.0;

// Ki范围
const float KI_MIN = 0.0;
const float KI_MAX = 5.0;
const float KI_STEP = 0.5;

// Kd范围
const float KD_MIN = 0.0;
const float KD_MAX = 0.5;
const float KD_STEP = 0.05;

// ========== 评估参数 ==========
const unsigned long TEST_DURATION = 5000;  // 每组参数测试5秒
const float STABILITY_THRESHOLD = 3.0;     // 稳定性阈值：角度偏差<3°
const int MIN_STABLE_COUNT = 400;          // 最少稳定次数（5秒内80%的时间）

// 最佳参数记录
float best_kp = 0;
float best_ki = 0;
float best_kd = 0;
float best_score = 0;
int best_stable_count = 0;

// 当前测试状态
bool tuning_active = false;
unsigned long test_start_time = 0;
int stable_count = 0;
float angle_error_sum = 0;
int sample_count = 0;

// 电机引脚定义
const int IN1 = 12;
const int IN2 = 13;
const int IN3 = 7;
const int IN4 = 6;
const int PWM_A = 9;
const int PWM_B = 10;

// 编码器引脚定义
const int encoderA1 = 2;
const int encoderA2 = 3;
const int encoderB1 = 4;
const int encoderB2 = 5;

// 编码器计数
volatile long encoderCountA = 0;
volatile long encoderCountB = 0;

const float DT = 0.01;  // 控制周期10ms
const float INTEGRAL_LIMIT_ANGLE = 500.0;

// EEPROM地址
const int EEPROM_ADDR_KP = 0;
const int EEPROM_ADDR_KI = 4;
const int EEPROM_ADDR_KD = 8;
const int EEPROM_ADDR_VALID = 12;  // 验证标志

// ========== MPU6050初始化 ==========
void initMPU6050() {
  Wire.begin();
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B);
  Wire.write(0);
  Wire.endTransmission(true);
  delay(100);
}

// ========== 读取MPU6050 ==========
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

// ========== 计算角度 ==========
void calculateAngle() {
  float accel_angle = atan2(AcY, AcZ) * RAD_TO_DEG;
  gyroX = GyX / 131.0;
  angleX = 0.96 * (angleX + gyroX * 0.01) + 0.04 * accel_angle;
}

// ========== 角度环PID ==========
float anglePID(float target, float current) {
  error_angle = target - current;
  integral_angle += error_angle * DT;
  integral_angle = constrain(integral_angle, -INTEGRAL_LIMIT_ANGLE, INTEGRAL_LIMIT_ANGLE);
  derivative_angle = (error_angle - lastError_angle) / DT;
  
  output_angle = kp_angle * error_angle + 
                 ki_angle * integral_angle + 
                 kd_angle * derivative_angle;
  
  lastError_angle = error_angle;
  return output_angle;
}

// ========== 电机控制 ==========
void setMotor(int speedA, int speedB) {
  if (speedA > 0) {
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, HIGH);
  } else {
    digitalWrite(IN1, HIGH);
    digitalWrite(IN2, LOW);
  }
  analogWrite(PWM_A, abs(speedA));
  
  if (speedB > 0) {
    digitalWrite(IN3, HIGH);
    digitalWrite(IN4, LOW);
  } else {
    digitalWrite(IN3, LOW);
    digitalWrite(IN4, HIGH);
  }
  analogWrite(PWM_B, abs(speedB));
}

// ========== 停止电机 ==========
void stopMotors() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
  analogWrite(PWM_A, 0);
  analogWrite(PWM_B, 0);
}

// ========== 编码器中断 ==========
void handleEncoderA() {
  int a = digitalRead(encoderA1);
  int b = digitalRead(encoderA2);
  encoderCountA += (a != b) ? 1 : -1;
}

void handleEncoderB() {
  int a = digitalRead(encoderB1);
  int b = digitalRead(encoderB2);
  encoderCountB += (a != b) ? 1 : -1;
}

// ========== 保存参数到EEPROM ==========
void saveParametersToEEPROM(float kp, float ki, float kd) {
  EEPROM.put(EEPROM_ADDR_KP, kp);
  EEPROM.put(EEPROM_ADDR_KI, ki);
  EEPROM.put(EEPROM_ADDR_KD, kd);
  EEPROM.put(EEPROM_ADDR_VALID, 0xAA55);  // 验证标志
  
  Serial.println("=== Parameters Saved to EEPROM ===");
  Serial.print("Kp="); Serial.print(kp, 3);
  Serial.print(", Ki="); Serial.print(ki, 3);
  Serial.print(", Kd="); Serial.println(kd, 3);
}

// ========== 从EEPROM加载参数 ==========
bool loadParametersFromEEPROM() {
  int valid;
  EEPROM.get(EEPROM_ADDR_VALID, valid);
  
  if (valid == 0xAA55) {
    EEPROM.get(EEPROM_ADDR_KP, kp_angle);
    EEPROM.get(EEPROM_ADDR_KI, ki_angle);
    EEPROM.get(EEPROM_ADDR_KD, kd_angle);
    
    Serial.println("=== Parameters Loaded from EEPROM ===");
    Serial.print("Kp="); Serial.print(kp_angle, 3);
    Serial.print(", Ki="); Serial.print(ki_angle, 3);
    Serial.print(", Kd="); Serial.println(kd_angle, 3);
    return true;
  }
  return false;
}

// ========== 评估当前参数 ==========
void evaluateCurrentParameters() {
  unsigned long current_time = millis();
  
  // 检查是否在稳定范围内
  if (abs(angleX - setpoint) < STABILITY_THRESHOLD) {
    stable_count++;
  }
  
  // 累计角度误差
  angle_error_sum += abs(angleX - setpoint);
  sample_count++;
  
  // 测试时间到
  if (current_time - test_start_time >= TEST_DURATION) {
    // 计算评分：稳定次数越多越好，平均误差越小越好
    float avg_error = angle_error_sum / sample_count;
    float score = stable_count - (avg_error * 10);  // 综合评分
    
    Serial.print("Test: Kp="); Serial.print(kp_angle, 2);
    Serial.print(" Ki="); Serial.print(ki_angle, 2);
    Serial.print(" Kd="); Serial.print(kd_angle, 3);
    Serial.print(" | Stable="); Serial.print(stable_count);
    Serial.print("/"); Serial.print(sample_count);
    Serial.print(" AvgErr="); Serial.print(avg_error, 2);
    Serial.print(" Score="); Serial.println(score, 1);
    
    // 更新最佳参数
    if (stable_count >= MIN_STABLE_COUNT && score > best_score) {
      best_score = score;
      best_kp = kp_angle;
      best_ki = ki_angle;
      best_kd = kd_angle;
      best_stable_count = stable_count;
      
      Serial.println(">>> NEW BEST PARAMETERS FOUND! <<<");
      saveParametersToEEPROM(best_kp, best_ki, best_kd);
    }
    
    // 准备下一组参数
    tuning_active = false;
  }
}

// ========== 网格搜索主函数 ==========
void gridSearchTuning() {
  static float current_kp = KP_MIN;
  static float current_ki = KI_MIN;
  static float current_kd = KD_MIN;
  static bool search_complete = false;
  
  if (search_complete) {
    return;  // 搜索已完成
  }
  
  if (!tuning_active) {
    // 设置新的参数组合
    kp_angle = current_kp;
    ki_angle = current_ki;
    kd_angle = current_kd;
    
    // 重置评估变量
    integral_angle = 0;
    lastError_angle = 0;
    stable_count = 0;
    angle_error_sum = 0;
    sample_count = 0;
    test_start_time = millis();
    tuning_active = true;
    
    Serial.println("--- Starting Test ---");
    
    // 移动到下一组参数
    current_kd += KD_STEP;
    if (current_kd > KD_MAX) {
      current_kd = KD_MIN;
      current_ki += KI_STEP;
      
      if (current_ki > KI_MAX) {
        current_ki = KI_MIN;
        current_kp += KP_STEP;
        
        if (current_kp > KP_MAX) {
          // 搜索完成
          search_complete = true;
          Serial.println("\n========================================");
          Serial.println("GRID SEARCH COMPLETE!");
          Serial.println("========================================");
          Serial.print("Best Parameters: Kp="); Serial.print(best_kp, 3);
          Serial.print(", Ki="); Serial.print(best_ki, 3);
          Serial.print(", Kd="); Serial.println(best_kd, 3);
          Serial.print("Best Score: "); Serial.println(best_score, 1);
          Serial.print("Stable Count: "); Serial.print(best_stable_count);
          Serial.print("/"); Serial.println(TEST_DURATION / 10);
          Serial.println("========================================");
          
          // 应用最佳参数
          kp_angle = best_kp;
          ki_angle = best_ki;
          kd_angle = best_kd;
        }
      }
    }
  }
}

// ========== 串口命令处理 ==========
void processSerialCommands() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    
    if (input.equals("start")) {
      Serial.println("Starting Grid Search Auto-Tuning...");
      Serial.println("Please keep the car upright manually at start!");
      delay(3000);
      Serial.println("Starting in 3...");
      delay(1000);
      Serial.println("2...");
      delay(1000);
      Serial.println("1...");
      delay(1000);
      Serial.println("GO! Release the car now!");
      
      // 重置搜索
      best_score = -999999;
      best_stable_count = 0;
      tuning_active = false;
    }
    else if (input.equals("stop")) {
      stopMotors();
      Serial.println("Motors stopped. Tuning paused.");
    }
    else if (input.equals("load")) {
      loadParametersFromEEPROM();
    }
    else if (input.equals("help")) {
      Serial.println("=== Auto-Tune PID Commands ===");
      Serial.println("start - Start grid search tuning");
      Serial.println("stop - Stop motors");
      Serial.println("load - Load saved parameters from EEPROM");
      Serial.println("help - Show this message");
    }
  }
}

void setup() {
  Serial.begin(9600);
  Serial.println("=== PID Auto-Tuner (Grid Search) ===");
  
  initMPU6050();
  
  // 初始化电机引脚
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);
  pinMode(PWM_A, OUTPUT);
  pinMode(PWM_B, OUTPUT);
  
  // 初始化编码器引脚
  pinMode(encoderA1, INPUT_PULLUP);
  pinMode(encoderA2, INPUT_PULLUP);
  pinMode(encoderB1, INPUT_PULLUP);
  pinMode(encoderB2, INPUT_PULLUP);
  
  // 设置编码器中断
  attachPinChangeInterrupt(digitalPinToPinChangeInterrupt(encoderA1), handleEncoderA, CHANGE);
  attachPinChangeInterrupt(digitalPinToPinChangeInterrupt(encoderB1), handleEncoderB, CHANGE);
  
  delay(1000);
  
  // 尝试加载已保存的参数
  if (loadParametersFromEEPROM()) {
    Serial.println("Using saved parameters.");
  } else {
    Serial.println("No saved parameters found.");
  }
  
  Serial.println("\nCommands:");
  Serial.println("  start - Begin auto-tuning");
  Serial.println("  stop  - Stop motors");
  Serial.println("  load  - Load saved params");
  Serial.println("  help  - Show help");
  Serial.println("\nReady!");
}

void loop() {
  readMPU6050();
  calculateAngle();
  processSerialCommands();
  
  // 执行网格搜索
  gridSearchTuning();
  
  // 角度安全检查
  if (abs(angleX - setpoint) > ANGLE_THRESHOLD) {
    stopMotors();
    if (tuning_active) {
      Serial.println("FAILED: Angle exceeded threshold!");
      tuning_active = false;  // 跳过当前参数
    }
  } else if (tuning_active) {
    // 执行PID控制
    float pwm = anglePID(setpoint, angleX);
    pwm = constrain(pwm, -255, 255);
    setMotor((int)pwm, (int)pwm);
    
    // 评估当前参数
    evaluateCurrentParameters();
  }
  
  delay(10);
}
