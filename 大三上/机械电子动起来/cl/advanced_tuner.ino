#include <Wire.h>

// ==================== 硬件配置 ====================
const int MPU_ADDR = 0x68;
int16_t AcX, AcY, AcZ, GyX, GyY, GyZ;
float angleX, gyroX;
float angle_setpoint = 0;
const float PROTECT_ANGLE = 15.0;

const int ENC_A = 2, ENC_B = 3;
volatile long enc_count = 0;
float current_speed = 0, speed_setpoint = 0;

const int IN1 = 12, IN2 = 13, IN3 = 7, IN4 = 6;
const int PWM_A = 9, PWM_B = 10;

// ==================== PID参数 ====================
float kp_angle, ki_angle, kd_angle;
float error_angle, lastError_angle, integral_angle, derivative_angle, angle_output;
float kp_speed = 0.0, ki_speed = 0.0, kd_speed = 0.0;
float error_speed, lastError_speed, integral_speed, derivative_speed, speed_output;
int motor_output = 0;

// ==================== 自适应网格搜索配置 ====================
// 第一阶段：粗搜索（大范围）
float kp_coarse[] = {10.0, 14.0, 18.0, 22.0, 26.0};
float ki_coarse[] = {0.3, 0.8, 1.3, 1.8, 2.3};
float kd_coarse[] = {0.005, 0.010, 0.015, 0.020, 0.025};

// 第二阶段：精细搜索（小范围，围绕最佳值）
float kp_fine[5], ki_fine[5], kd_fine[5];

const unsigned long TEST_DURATION = 4000;   // 测试时长4秒
const unsigned long SETTLE_TIME = 800;      // 稳定时间0.8秒
const int SEARCH_PHASES = 2;                // 搜索阶段数

float best_score = 999999.0;
float best_kp = 16.0, best_ki = 1.30, best_kd = 0.012;

// ==================== 基础函数 ====================
void initMPU6050() {
  Wire.begin();
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B); Wire.write(0);
  Wire.endTransmission(true);
}

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

void calculateAngle() {
  float accel_angle = atan2(AcY, AcZ) * RAD_TO_DEG;
  gyroX = GyX / 131.0;
  angleX = 0.96 * (angleX + gyroX * 0.01) + 0.04 * accel_angle;
}

void encoderISR() {
  if (digitalRead(ENC_A) == digitalRead(ENC_B)) enc_count++;
  else enc_count--;
}

void calculateSpeed() {
  static unsigned long last_time = 0;
  static long last_count = 0;
  unsigned long current_time = millis();
  if (current_time - last_time >= 10) {
    current_speed = enc_count - last_count;
    last_count = enc_count;
    last_time = current_time;
  }
}

void anglePID() {
  error_angle = angle_setpoint - angleX;
  integral_angle += error_angle * 0.01;
  derivative_angle = (error_angle - lastError_angle) / 0.01;
  integral_angle = constrain(integral_angle, -500, 500);
  angle_output = kp_angle * error_angle + ki_angle * integral_angle + kd_angle * derivative_angle;
  lastError_angle = error_angle;
}

void speedPID() {
  error_speed = speed_setpoint - current_speed;
  integral_speed += error_speed * 0.01;
  derivative_speed = (error_speed - lastError_speed) / 0.01;
  integral_speed = constrain(integral_speed, -200, 200);
  speed_output = kp_speed * error_speed + ki_speed * integral_speed + kd_speed * derivative_speed;
  lastError_speed = error_speed;
}

void setMotor() {
  if (abs(angleX) > PROTECT_ANGLE) {
    motor_output = 0;
    analogWrite(PWM_A, 0);
    analogWrite(PWM_B, 0);
    return;
  }
  
  motor_output = constrain((int)(speed_output + angle_output), -255, 255);
  
  digitalWrite(IN1, motor_output > 0 ? LOW : HIGH);
  digitalWrite(IN2, motor_output > 0 ? HIGH : LOW);
  analogWrite(PWM_A, abs(motor_output));
  
  digitalWrite(IN3, motor_output > 0 ? HIGH : LOW);
  digitalWrite(IN4, motor_output > 0 ? LOW : HIGH);
  analogWrite(PWM_B, abs(motor_output));
}

void resetPID() {
  lastError_angle = 0; integral_angle = 0;
  lastError_speed = 0; integral_speed = 0;
}

// ==================== 性能评估（改进版） ====================
float evaluatePerformance(bool verbose = false) {
  float sum_angle_error = 0, sum_angle_squared = 0, max_angle = 0;
  float sum_oscillation = 0;  // 振荡指标
  int sample_count = 0, fall_count = 0;
  float last_angle = 0;
  
  unsigned long start_time = millis();
  unsigned long eval_start = start_time + SETTLE_TIME;
  
  if (verbose) Serial.println("Testing...");
  
  while (millis() - start_time < TEST_DURATION) {
    readMPU6050();
    calculateAngle();
    calculateSpeed();
    anglePID();
    speedPID();
    setMotor();
    
    if (millis() >= eval_start) {
      float abs_angle = abs(angleX);
      sum_angle_error += abs_angle;
      sum_angle_squared += abs_angle * abs_angle;
      if (abs_angle > max_angle) max_angle = abs_angle;
      
      // 计算振荡（角度变化率）
      sum_oscillation += abs(angleX - last_angle);
      last_angle = angleX;
      
      if (abs_angle > PROTECT_ANGLE) fall_count++;
      sample_count++;
    }
    delay(10);
  }
  
  // 综合评分：平均误差 + 最大角度 + 跌倒惩罚 + 振荡惩罚
  float avg_error = sum_angle_error / sample_count;
  float variance = (sum_angle_squared / sample_count) - (avg_error * avg_error);
  float avg_oscillation = sum_oscillation / sample_count;
  float score = avg_error + 0.3 * max_angle + 200.0 * fall_count + 0.05 * variance + 0.2 * avg_oscillation;
  
  if (verbose) {
    Serial.print("AvgErr="); Serial.print(avg_error, 2);
    Serial.print(" MaxAng="); Serial.print(max_angle, 2);
    Serial.print(" Osc="); Serial.print(avg_oscillation, 2);
    Serial.print(" Falls="); Serial.print(fall_count);
    Serial.print(" Score="); Serial.println(score, 2);
  }
  
  return score;
}

// ==================== 自适应网格搜索 ====================
void adaptiveGridSearch() {
  Serial.println("\n╔════════════════════════════════════════╗");
  Serial.println("║  Adaptive PID Grid Search Tuner       ║");
  Serial.println("╚════════════════════════════════════════╝");
  Serial.println("Phase 1: Coarse Search (5x5x5 = 125 tests)");
  Serial.println("Phase 2: Fine Search (5x5x5 = 125 tests)");
  Serial.println("Total: 250 tests (~20 minutes)");
  Serial.println("\nEnsure robot is upright! Starting in 5s...\n");
  delay(5000);
  
  // ========== 阶段1：粗搜索 ==========
  Serial.println("\n>>> PHASE 1: COARSE SEARCH <<<");
  int test_num = 0;
  
  for (int i = 0; i < 5; i++) {
    for (int j = 0; j < 5; j++) {
      for (int k = 0; k < 5; k++) {
        test_num++;
        kp_angle = kp_coarse[i];
        ki_angle = ki_coarse[j];
        kd_angle = kd_coarse[k];
        resetPID();
        
        Serial.print("["); Serial.print(test_num); Serial.print("/125] ");
        Serial.print("Kp="); Serial.print(kp_angle, 1);
        Serial.print(" Ki="); Serial.print(ki_angle, 2);
        Serial.print(" Kd="); Serial.print(kd_angle, 3);
        Serial.print(" -> ");
        
        float score = evaluatePerformance(true);
        
        if (score < best_score) {
          best_score = score;
          best_kp = kp_angle;
          best_ki = ki_angle;
          best_kd = kd_angle;
          Serial.println("★ NEW BEST! ★");
        }
        delay(300);
      }
    }
  }
  
  Serial.println("\n--- Phase 1 Complete ---");
  Serial.print("Best: Kp="); Serial.print(best_kp);
  Serial.print(" Ki="); Serial.print(best_ki);
  Serial.print(" Kd="); Serial.println(best_kd);
  
  // ========== 阶段2：精细搜索 ==========
  Serial.println("\n>>> PHASE 2: FINE SEARCH <<<");
  Serial.println("Refining around best parameters...");
  
  // 生成精细搜索范围（±20%）
  float kp_step = best_kp * 0.1;
  float ki_step = best_ki * 0.1;
  float kd_step = best_kd * 0.1;
  
  for (int i = 0; i < 5; i++) {
    kp_fine[i] = best_kp + (i - 2) * kp_step;
    ki_fine[i] = best_ki + (i - 2) * ki_step;
    kd_fine[i] = best_kd + (i - 2) * kd_step;
    if (kp_fine[i] < 0) kp_fine[i] = 0.1;
    if (ki_fine[i] < 0) ki_fine[i] = 0.01;
    if (kd_fine[i] < 0) kd_fine[i] = 0.001;
  }
  
  test_num = 0;
  for (int i = 0; i < 5; i++) {
    for (int j = 0; j < 5; j++) {
      for (int k = 0; k < 5; k++) {
        test_num++;
        kp_angle = kp_fine[i];
        ki_angle = ki_fine[j];
        kd_angle = kd_fine[k];
        resetPID();
        
        Serial.print("["); Serial.print(test_num); Serial.print("/125] ");
        Serial.print("Kp="); Serial.print(kp_angle, 2);
        Serial.print(" Ki="); Serial.print(ki_angle, 3);
        Serial.print(" Kd="); Serial.print(kd_angle, 4);
        Serial.print(" -> ");
        
        float score = evaluatePerformance(true);
        
        if (score < best_score) {
          best_score = score;
          best_kp = kp_angle;
          best_ki = ki_angle;
          best_kd = kd_angle;
          Serial.println("★ NEW BEST! ★");
        }
        delay(300);
      }
    }
  }
  
  // ========== 输出最终结果 ==========
  Serial.println("\n╔════════════════════════════════════════╗");
  Serial.println("║     TUNING COMPLETE!                   ║");
  Serial.println("╚════════════════════════════════════════╝");
  Serial.println("\n✓ OPTIMAL PARAMETERS:");
  Serial.println("Copy these to your main code:\n");
  Serial.print("float kp_angle = "); Serial.print(best_kp, 3); Serial.println(";");
  Serial.print("float ki_angle = "); Serial.print(best_ki, 3); Serial.println(";");
  Serial.print("float kd_angle = "); Serial.print(best_kd, 4); Serial.println(";");
  Serial.print("\nFinal Score: "); Serial.println(best_score, 2);
  Serial.println("════════════════════════════════════════\n");
  
  kp_angle = best_kp;
  ki_angle = best_ki;
  kd_angle = best_kd;
  Serial.println("Applying best parameters...\n");
}

// ==================== Arduino主函数 ====================
void setup() {
  Serial.begin(9600);
  while (!Serial && millis() < 3000);  // 等待串口
  
  initMPU6050();
  pinMode(ENC_A, INPUT_PULLUP);
  pinMode(ENC_B, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(ENC_A), encoderISR, CHANGE);
  
  pinMode(IN1, OUTPUT); pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT); pinMode(IN4, OUTPUT);
  pinMode(PWM_A, OUTPUT); pinMode(PWM_B, OUTPUT);
  
  delay(1000);
  resetPID();
  
  // 执行自适应网格搜索
  adaptiveGridSearch();
}

void loop() {
  // 使用最优参数持续运行
  readMPU6050();
  calculateAngle();
  calculateSpeed();
  anglePID();
  speedPID();
  setMotor();
  
  // 每秒输出一次状态
  static unsigned long last_print = 0;
  if (millis() - last_print > 1000) {
    Serial.print("Angle="); Serial.print(angleX, 2);
    Serial.print("° Speed="); Serial.print(current_speed, 0);
    Serial.print(" Motor="); Serial.println(motor_output);
    last_print = millis();
  }
  
  delay(10);
}
