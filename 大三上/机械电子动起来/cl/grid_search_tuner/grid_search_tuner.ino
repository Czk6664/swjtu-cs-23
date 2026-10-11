#include <Wire.h>
#include <MsTimer2.h>  // 定时器库


// ==================== 硬件配置 ====================
const int MPU_ADDR = 0x68;
int16_t AcX, AcY, AcZ, GyX, GyY, GyZ;
float angleX, gyroX;
float angle_setpoint = -0.2;  // 平衡角度设为-0.1度
const float PROTECT_ANGLE = 25.0;


const int ENC_A = 2;
const int ENC_B = 3;
volatile long enc_count = 0;
float current_speed = 0;
float speed_setpoint = 0;
float current_position = 0;
float position_setpoint = 0;

// 电机驱动引脚配置
const int IN1 = 12, IN2 = 13, IN3 = 7, IN4 = 6;
const int PWM_A = 9, PWM_B = 10;

// ==================== PID参数 ====================
float kp_angle, ki_angle, kd_angle;
float error_angle, lastError_angle, integral_angle, derivative_angle;
float angle_output;


float kp_speed = 0.0, ki_speed = 0.0, kd_speed = 0.0;
float error_speed, lastError_speed, integral_speed, derivative_speed;
float speed_output;


float kp_position = 0.0, ki_position = 0.0, kd_position = 0.0;
float error_position, lastError_position, integral_position, derivative_position;
float position_output;


int motor_output = 0;

// ==================== 定时器控制 ====================
volatile bool pid_update_flag = false;  // PID更新标志
const int PID_INTERVAL = 5;  // PID更新间隔5ms (200Hz)


// ==================== 运行模式配置 ====================
// 运行模式选择: 
// -1 = 直接运行（使用下面的BEST参数，不进行搜索）
//  0 = 角度环搜索
//  1 = 速度环搜索
//  2 = 位置环搜索
const int SEARCH_MODE = 1;  // 修改此值切换模式（1=速度环搜索）

// ==================== 直接运行的最佳参数 ====================
// 角度环最佳参数
const float BEST_KP_ANGLE = 25.0;
const float BEST_KI_ANGLE = 0.0;
const float BEST_KD_ANGLE = 0.05;

// 速度环最佳参数
const float BEST_KP_SPEED = 1.5;
const float BEST_KI_SPEED = 0.1;
const float BEST_KD_SPEED = 0.03;

// 位置环最佳参数
const float BEST_KP_POSITION = 0.0;
const float BEST_KI_POSITION = 0.0;
const float BEST_KD_POSITION = 0.0;

// 控制环启用设置（直接运行模式时使用）
// 0=仅角度环, 1=角度+速度环, 2=角度+速度+位置环
const int CONTROL_MODE = 0;  // 建议先用1测试稳定性

// ==================== 网格搜索配置 ====================
// 角度环PID搜索范围（降低Kp避免振荡，增加Kd提供阻尼）
float kp_angle_range[] = {13.0};  // 测试不同Kp值
float ki_angle_range[] = {0};                    // Ki固定为0
float kd_angle_range[] = {0.11};  // 测试不同Kd值  


// 速度环PID搜索范围（启用速度环进行搜索）
float kp_speed_range[] = {0.5, 1.0};  
float ki_speed_range[] = {0};     
float kd_speed_range[] = {0.01, 0.05};  


// 位置环PID搜索范围（初始探索范围）
float kp_position_range[] = {0};  
float ki_position_range[] = {0};     
float kd_position_range[] = {0};  


const int KP_COUNT = (SEARCH_MODE == 0) ? 1 : ((SEARCH_MODE == 1) ? 2 : 1);
const int KI_COUNT = (SEARCH_MODE == 0) ? 1 : ((SEARCH_MODE == 1) ? 1 : 1);
const int KD_COUNT = (SEARCH_MODE == 0) ? 1 : ((SEARCH_MODE == 1) ? 2 : 1);



// 测试配置
const unsigned long TEST_DURATION = 10000;  // 每组参数测试30秒
const unsigned long SETTLE_TIME = 1000;    // 参数切换后稳定时间1秒



// 性能评估指标
float best_score = 999999.0;
float best_kp = 0.0, best_ki = 0.0, best_kd = 0.0;
int current_test = 0;
int total_tests = KP_COUNT * KI_COUNT * KD_COUNT;


// ==================== 定时器中断服务函数 ====================
void timerISR() {
  pid_update_flag = true;  // 设置PID更新标志
}

// ==================== 初始化函数 ====================
void initMPU6050() {
  Wire.begin();
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B);
  Wire.write(0);
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


void calculatePosition() {
  // 位置就是编码器计数值（可以根据需要转换为实际距离）
  current_position = enc_count;
}


void anglePID() {
  error_angle = angle_setpoint - angleX;
  integral_angle += error_angle * 0.01;
  derivative_angle = (error_angle - lastError_angle) / 0.01;
  
  if (integral_angle > 500) integral_angle = 500;
  if (integral_angle < -500) integral_angle = -500;
  
  angle_output = kp_angle * error_angle + ki_angle * integral_angle + kd_angle * derivative_angle;
  lastError_angle = error_angle;
}


void speedPID() {
  error_speed = speed_setpoint - current_speed;
  integral_speed += error_speed * 0.01;
  derivative_speed = (error_speed - lastError_speed) / 0.01;
  
  if (integral_speed > 200) integral_speed = 200;
  if (integral_speed < -200) integral_speed = -200;
  
  speed_output = kp_speed * error_speed + ki_speed * integral_speed + kd_speed * derivative_speed;
  lastError_speed = error_speed;
}


void positionPID() {
  error_position = position_setpoint - current_position;
  integral_position += error_position * 0.01;
  derivative_position = (error_position - lastError_position) / 0.01;
  
  if (integral_position > 1000) integral_position = 1000;
  if (integral_position < -1000) integral_position = -1000;
  
  position_output = kp_position * error_position + ki_position * integral_position + kd_position * derivative_position;
  lastError_position = error_position;
  
  // 位置环输出作为速度环的设定值
  speed_setpoint = position_output;
  
  // 限制速度设定值
  if (speed_setpoint > 50) speed_setpoint = 50;
  if (speed_setpoint < -50) speed_setpoint = -50;
}


// ==================== PID控制主函数（定时器触发） ====================
void updatePID() {
  // 读取传感器数据
  readMPU6050();
  calculateAngle();
  calculateSpeed();
  
  // 根据当前模式执行相应的PID控制
  int active_mode = (SEARCH_MODE == -1) ? CONTROL_MODE : SEARCH_MODE;
  
  if (active_mode == 2) {
    calculatePosition();
    positionPID();
  } else {
    speed_setpoint = 0;
  }
  
  anglePID();
  speedPID();
  setMotor();
}

void setMotor() {
  if (abs(angleX) > PROTECT_ANGLE) {
    motor_output = 0;
    analogWrite(PWM_A, 0);
    analogWrite(PWM_B, 0);
    return;
  }
  
  // 根据模式组合输出
  int active_mode = (SEARCH_MODE == -1) ? CONTROL_MODE : SEARCH_MODE;
  
  if (active_mode == 2) {
    motor_output = position_output + speed_output + angle_output;
  } else if (active_mode == 1) {
    motor_output = speed_output + angle_output;
  } else {
    motor_output = angle_output;
  }
  
  if (motor_output > 255) motor_output = 255;
  if (motor_output < -255) motor_output = -255;
  
  if (motor_output > 0) {
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, HIGH);
  } else {
    digitalWrite(IN1, HIGH);
    digitalWrite(IN2, LOW);
  }
  analogWrite(PWM_A, abs(motor_output));
  
  if (motor_output > 0) {
    digitalWrite(IN3, HIGH);
    digitalWrite(IN4, LOW);
  } else {
    digitalWrite(IN3, LOW);
    digitalWrite(IN4, HIGH);
  }
  analogWrite(PWM_B, abs(motor_output));
}


// ==================== 性能评估函数 ====================
float evaluateAnglePerformance() {
  float sum_angle_error = 0;
  float sum_angle_squared = 0;
  float max_angle = 0;
  int sample_count = 0;
  int fall_count = 0;
  
  unsigned long start_time = millis();
  unsigned long eval_start = start_time + SETTLE_TIME;
  
  Serial.println("--- Testing Angle Loop (Settling...) ---");
  
  while (millis() - start_time < TEST_DURATION) {
    // 等待定时器触发PID更新
    if (pid_update_flag) {
      pid_update_flag = false;
      updatePID();
    }
    
    // 稳定期后开始采集数据
    if (millis() >= eval_start) {
      float abs_angle = abs(angleX);
      sum_angle_error += abs_angle;
      sum_angle_squared += abs_angle * abs_angle;
      if (abs_angle > max_angle) max_angle = abs_angle;
      
      // 检测跌倒
      if (abs_angle > PROTECT_ANGLE) {
        fall_count++;
      }
      
      sample_count++;
    }
  }
  
  // 计算综合得分（越小越好）
  // 得分 = 平均角度误差 + 0.5*最大角度 + 100*跌倒次数 + 0.1*角度方差
  float avg_error = sum_angle_error / sample_count;
  float variance = (sum_angle_squared / sample_count) - (avg_error * avg_error);
  float score = avg_error + 0.5 * max_angle + 100.0 * fall_count + 0.1 * variance;
  
  Serial.print("Avg Error: "); Serial.print(avg_error);
  Serial.print(" | Max Angle: "); Serial.print(max_angle);
  Serial.print(" | Falls: "); Serial.print(fall_count);
  Serial.print(" | Score: "); Serial.println(score);
  
  return score;
}

float evaluateSpeedPerformance() {
  float sum_speed_error = 0;
  float sum_speed_squared = 0;
  float sum_angle_error = 0;
  int sample_count = 0;
  int fall_count = 0;
  float max_angle = 0;
  
  unsigned long start_time = millis();
  unsigned long eval_start = start_time + SETTLE_TIME;
  
  Serial.println("--- Testing Speed Loop (Settling...) ---");
  
  // 设置速度目标（可以是0或小的值）
  speed_setpoint = 0;
  
  while (millis() - start_time < TEST_DURATION) {
    // 等待定时器触发PID更新
    if (pid_update_flag) {
      pid_update_flag = false;
      updatePID();
    }
    
    // 稳定期后开始采集数据
    if (millis() >= eval_start) {
      float abs_speed_error = abs(error_speed);
      float abs_angle = abs(angleX);
      
      sum_speed_error += abs_speed_error;
      sum_speed_squared += abs_speed_error * abs_speed_error;
      sum_angle_error += abs_angle;
      
      if (abs_angle > max_angle) max_angle = abs_angle;
      
      // 检测跌倒
      if (abs_angle > PROTECT_ANGLE) {
        fall_count++;
      }
      
      sample_count++;
    }
  }
  
  // 计算综合得分（越小越好）
  // 得分 = 平均速度误差 + 0.1*速度方差 + 2*平均角度误差 + 100*跌倒次数
  float avg_speed_error = sum_speed_error / sample_count;
  float speed_variance = (sum_speed_squared / sample_count) - (avg_speed_error * avg_speed_error);
  float avg_angle_error = sum_angle_error / sample_count;
  float score = avg_speed_error + 0.1 * speed_variance + 2.0 * avg_angle_error + 100.0 * fall_count;
  
  Serial.print("Avg Speed Error: "); Serial.print(avg_speed_error);
  Serial.print(" | Avg Angle: "); Serial.print(avg_angle_error);
  Serial.print(" | Max Angle: "); Serial.print(max_angle);
  Serial.print(" | Falls: "); Serial.print(fall_count);
  Serial.print(" | Score: "); Serial.println(score);
  
  return score;
}

float evaluatePositionPerformance() {
  float sum_position_error = 0;
  float sum_position_squared = 0;
  float sum_angle_error = 0;
  int sample_count = 0;
  int fall_count = 0;
  float max_angle = 0;
  float max_position_error = 0;
  
  unsigned long start_time = millis();
  unsigned long eval_start = start_time + SETTLE_TIME;
  
  Serial.println("--- Testing Position Loop (Settling...) ---");
  
  // 设置位置目标（相对于起始位置的偏移）
  long start_position = enc_count;
  position_setpoint = start_position;  // 保持在起始位置
  
  while (millis() - start_time < TEST_DURATION) {
    // 等待定时器触发PID更新
    if (pid_update_flag) {
      pid_update_flag = false;
      updatePID();
    }
    
    // 稳定期后开始采集数据
    if (millis() >= eval_start) {
      float abs_position_error = abs(error_position);
      float abs_angle = abs(angleX);
      
      sum_position_error += abs_position_error;
      sum_position_squared += abs_position_error * abs_position_error;
      sum_angle_error += abs_angle;
      
      if (abs_position_error > max_position_error) max_position_error = abs_position_error;
      if (abs_angle > max_angle) max_angle = abs_angle;
      
      // 检测跌倒
      if (abs_angle > PROTECT_ANGLE) {
        fall_count++;
      }
      
      sample_count++;
    }
  }
  
  // 计算综合得分（越小越好）
  // 得分 = 平均位置误差 + 0.1*位置方差 + 0.5*最大位置误差 + 2*平均角度误差 + 100*跌倒次数
  float avg_position_error = sum_position_error / sample_count;
  float position_variance = (sum_position_squared / sample_count) - (avg_position_error * avg_position_error);
  float avg_angle_error = sum_angle_error / sample_count;
  float score = avg_position_error + 0.1 * position_variance + 0.5 * max_position_error + 2.0 * avg_angle_error + 100.0 * fall_count;
  
  Serial.print("Avg Pos Error: "); Serial.print(avg_position_error);
  Serial.print(" | Max Pos Error: "); Serial.print(max_position_error);
  Serial.print(" | Avg Angle: "); Serial.print(avg_angle_error);
  Serial.print(" | Max Angle: "); Serial.print(max_angle);
  Serial.print(" | Falls: "); Serial.print(fall_count);
  Serial.print(" | Score: "); Serial.println(score);
  
  return score;
}


// ==================== 网格搜索主函数 ====================
void gridSearchAngle() {
  Serial.println("\n========================================");
  Serial.println("   ANGLE LOOP Grid Search");
  Serial.println("========================================");
  Serial.print("Total Tests: "); Serial.println(total_tests);
  Serial.println("Please ensure robot is in upright position!");
  Serial.println("Starting in 3 seconds...\n");
  delay(3000);
  
  // 设置固定的速度环参数
  kp_speed = 0.0;
  ki_speed = 0.0;
  kd_speed = 0.0;
  
  for (int i = 0; i < KP_COUNT; i++) {
    for (int j = 0; j < KI_COUNT; j++) {
      for (int k = 0; k < KD_COUNT; k++) {
        current_test++;
        
        // 设置当前测试参数
        kp_angle = kp_angle_range[i];
        ki_angle = ki_angle_range[j];
        kd_angle = kd_angle_range[k];
        
        // 重置PID状态
        lastError_angle = 0;
        integral_angle = 0;
        lastError_speed = 0;
        integral_speed = 0;
        
        Serial.println("\n----------------------------------------");
        Serial.print("Test "); Serial.print(current_test); 
        Serial.print("/"); Serial.println(total_tests);
        Serial.print("Angle Kp="); Serial.print(kp_angle);
        Serial.print(" Ki="); Serial.print(ki_angle);
        Serial.print(" Kd="); Serial.println(kd_angle);
        
        // 评估性能
        float score = evaluateAnglePerformance();
        
        // 更新最佳参数
        if (score < best_score) {
          best_score = score;
          best_kp = kp_angle;
          best_ki = ki_angle;
          best_kd = kd_angle;
          
          Serial.println("*** NEW BEST ANGLE PARAMETERS FOUND! ***");
          Serial.print("Best Kp="); Serial.print(best_kp);
          Serial.print(" Ki="); Serial.print(best_ki);
          Serial.print(" Kd="); Serial.print(best_kd);
          Serial.print(" Score="); Serial.println(best_score);
        }
        
        delay(500);  // 短暂停顿
      }
    }
  }
  
  // 输出最终结果
  Serial.println("\n========================================");
  Serial.println("   ANGLE LOOP SEARCH COMPLETED!");
  Serial.println("========================================");
  Serial.println("BEST ANGLE LOOP PARAMETERS:");
  Serial.print("float kp_angle = "); Serial.print(best_kp); Serial.println(";");
  Serial.print("float ki_angle = "); Serial.print(best_ki); Serial.println(";");
  Serial.print("float kd_angle = "); Serial.print(best_kd); Serial.println(";");
  Serial.print("Best Score: "); Serial.println(best_score);
  Serial.println("========================================");
  
  // 应用最佳参数并持续运行
  kp_angle = best_kp;
  ki_angle = best_ki;
  kd_angle = best_kd;
  Serial.println("\nApplying best parameters and running...");
  
  // 进入持续运行模式
  Serial.println("--- Running with Best Parameters (Continuous) ---");
  Serial.println("Robot is now balancing with optimized angle loop...\n");
  
  unsigned long last_print = 0;
  while (true) {  // 无限循环
    // 等待定时器触发PID更新
    if (pid_update_flag) {
      pid_update_flag = false;
      updatePID();
    }
    
    // 每秒输出一次状态
    if (millis() - last_print >= 1000) {
      last_print = millis();
      Serial.print("Angle: "); Serial.print(angleX, 2);
      Serial.print(" | Speed: "); Serial.print(current_speed, 1);
      Serial.print(" | Motor: "); Serial.println(abs(motor_output));
    }
  }
}

void gridSearchSpeed() {
  Serial.println("\n========================================");
  Serial.println("   SPEED LOOP Grid Search");
  Serial.println("========================================");
  Serial.print("Total Tests: "); Serial.println(total_tests);
  Serial.println("Please ensure robot is in upright position!");
  Serial.println("Starting in 3 seconds...\n");
  delay(3000);
  
  // 使用已调好的角度环参数
  kp_angle = 25.0;
  ki_angle = 0.0;
  kd_angle = 0.15;
  
  Serial.println("Using fixed angle loop parameters:");
  Serial.print("Angle Kp="); Serial.print(kp_angle);
  Serial.print(" Ki="); Serial.print(ki_angle);
  Serial.print(" Kd="); Serial.println(kd_angle);
  Serial.println();
  
  for (int i = 0; i < KP_COUNT; i++) {
    for (int j = 0; j < KI_COUNT; j++) {
      for (int k = 0; k < KD_COUNT; k++) {
        current_test++;
        
        // 设置当前测试参数
        kp_speed = kp_speed_range[i];
        ki_speed = ki_speed_range[j];
        kd_speed = kd_speed_range[k];
        
        // 重置PID状态
        lastError_angle = 0;
        integral_angle = 0;
        lastError_speed = 0;
        integral_speed = 0;
        
        Serial.println("\n----------------------------------------");
        Serial.print("Test "); Serial.print(current_test); 
        Serial.print("/"); Serial.println(total_tests);
        Serial.print("Speed Kp="); Serial.print(kp_speed);
        Serial.print(" Ki="); Serial.print(ki_speed);
        Serial.print(" Kd="); Serial.println(kd_speed);
        
        // 评估性能
        float score = evaluateSpeedPerformance();
        
        // 更新最佳参数
        if (score < best_score) {
          best_score = score;
          best_kp = kp_speed;
          best_ki = ki_speed;
          best_kd = kd_speed;
          
          Serial.println("*** NEW BEST SPEED PARAMETERS FOUND! ***");
          Serial.print("Best Kp="); Serial.print(best_kp);
          Serial.print(" Ki="); Serial.print(best_ki);
          Serial.print(" Kd="); Serial.print(best_kd);
          Serial.print(" Score="); Serial.println(best_score);
        }
        
        delay(500);  // 短暂停顿
      }
    }
  }
  
  // 输出最终结果
  Serial.println("\n========================================");
  Serial.println("   SPEED LOOP SEARCH COMPLETED!");
  Serial.println("========================================");
  Serial.println("BEST SPEED LOOP PARAMETERS:");
  Serial.print("float kp_speed = "); Serial.print(best_kp); Serial.println(";");
  Serial.print("float ki_speed = "); Serial.print(best_ki); Serial.println(";");
  Serial.print("float kd_speed = "); Serial.print(best_kd); Serial.println(";");
  Serial.print("Best Score: "); Serial.println(best_score);
  Serial.println("========================================");
  
  // 应用最佳参数并持续运行
  kp_speed = best_kp;
  ki_speed = best_ki;
  kd_speed = best_kd;
  Serial.println("\nApplying best parameters and running...");
  
  // 进入持续运行模式
  Serial.println("--- Running with Best Parameters (Continuous) ---");
  Serial.println("Robot is now balancing with optimized speed loop...\n");
  
  speed_setpoint = 0;
  unsigned long last_print = 0;
  while (true) {  // 无限循环
    // 等待定时器触发PID更新
    if (pid_update_flag) {
      pid_update_flag = false;
      updatePID();
    }
    
    // 每秒输出一次状态
    if (millis() - last_print >= 1000) {
      last_print = millis();
      Serial.print("Angle: "); Serial.print(angleX, 2);
      Serial.print(" | Speed: "); Serial.print(current_speed, 1);
      Serial.print(" | Motor: "); Serial.println(abs(motor_output));
    }
  }
}

void gridSearchPosition() {
  Serial.println("\n========================================");
  Serial.println("   POSITION LOOP Grid Search");
  Serial.println("========================================");
  Serial.print("Total Tests: "); Serial.println(total_tests);
  Serial.println("Please ensure robot is in upright position!");
  Serial.println("Starting in 3 seconds...\n");
  delay(3000);
  
  // 使用已调好的角度环和速度环参数
  kp_angle = 27.0;
  ki_angle = 1.5;
  kd_angle = 0.20;  // 改为0.20，与速度环测试时一致
  
  kp_speed = 1.5;
  ki_speed = 0.1;
  kd_speed = 0.03;
  
  Serial.println("Using fixed angle and speed loop parameters:");
  Serial.print("Angle Kp="); Serial.print(kp_angle);
  Serial.print(" Ki="); Serial.print(ki_angle);
  Serial.print(" Kd="); Serial.println(kd_angle);
  Serial.print("Speed Kp="); Serial.print(kp_speed);
  Serial.print(" Ki="); Serial.print(ki_speed);
  Serial.print(" Kd="); Serial.println(kd_speed);
  Serial.println();
  
  for (int i = 0; i < KP_COUNT; i++) {
    for (int j = 0; j < KI_COUNT; j++) {
      for (int k = 0; k < KD_COUNT; k++) {
        current_test++;
        
        // 设置当前测试参数
        kp_position = kp_position_range[i];
        ki_position = ki_position_range[j];
        kd_position = kd_position_range[k];
        
        // 重置PID状态
        lastError_angle = 0;
        integral_angle = 0;
        lastError_speed = 0;
        integral_speed = 0;
        lastError_position = 0;
        integral_position = 0;
        
        Serial.println("\n----------------------------------------");
        Serial.print("Test "); Serial.print(current_test); 
        Serial.print("/"); Serial.println(total_tests);
        Serial.print("Position Kp="); Serial.print(kp_position);
        Serial.print(" Ki="); Serial.print(ki_position);
        Serial.print(" Kd="); Serial.println(kd_position);
        
        // 评估性能
        float score = evaluatePositionPerformance();
        
        // 更新最佳参数
        if (score < best_score) {
          best_score = score;
          best_kp = kp_position;
          best_ki = ki_position;
          best_kd = kd_position;
          
          Serial.println("*** NEW BEST POSITION PARAMETERS FOUND! ***");
          Serial.print("Best Kp="); Serial.print(best_kp);
          Serial.print(" Ki="); Serial.print(best_ki);
          Serial.print(" Kd="); Serial.print(best_kd);
          Serial.print(" Score="); Serial.println(best_score);
        }
        
        delay(500);  // 短暂停顿
      }
    }
  }
  
  // 输出最终结果
  Serial.println("\n========================================");
  Serial.println("   POSITION LOOP SEARCH COMPLETED!");
  Serial.println("========================================");
  Serial.println("BEST POSITION LOOP PARAMETERS:");
  Serial.print("float kp_position = "); Serial.print(best_kp); Serial.println(";");
  Serial.print("float ki_position = "); Serial.print(best_ki); Serial.println(";");
  Serial.print("float kd_position = "); Serial.print(best_kd); Serial.println(";");
  Serial.print("Best Score: "); Serial.println(best_score);
  Serial.println("========================================");
  
  // 应用最佳参数并持续运行
  kp_position = best_kp;
  ki_position = best_ki;
  kd_position = best_kd;
  Serial.println("\nApplying best parameters and running...");
  
  // 进入持续运行模式
  Serial.println("--- Running with Best Parameters (Continuous) ---");
  Serial.println("Robot is now balancing with optimized position loop...\n");
  
  speed_setpoint = 0;
  position_setpoint = enc_count;
  unsigned long last_print = 0;
  while (true) {  // 无限循环
    // 等待定时器触发PID更新
    if (pid_update_flag) {
      pid_update_flag = false;
      updatePID();
    }
    
    // 每秒输出一次状态
    if (millis() - last_print >= 1000) {
      last_print = millis();
      Serial.print("Angle: "); Serial.print(angleX, 2);
      Serial.print(" | Speed: "); Serial.print(current_speed, 1);
      Serial.print(" | Position: "); Serial.print(current_position);
      Serial.print(" | Motor: "); Serial.println(abs(motor_output));
    }
  }
}

// ==================== 直接运行函数 ====================
void directRun() {
  Serial.println("\n========================================");
  Serial.println("   Direct Run Mode");
  Serial.println("========================================");
  Serial.println("Please ensure robot is in upright position!");
  Serial.println("Starting in 3 seconds...\n");
  delay(3000);
  
  // 应用最佳参数
  kp_angle = BEST_KP_ANGLE;
  ki_angle = BEST_KI_ANGLE;
  kd_angle = BEST_KD_ANGLE;
  
  kp_speed = BEST_KP_SPEED;
  ki_speed = BEST_KI_SPEED;
  kd_speed = BEST_KD_SPEED;
  
  kp_position = BEST_KP_POSITION;
  ki_position = BEST_KI_POSITION;
  kd_position = BEST_KD_POSITION;
  
  Serial.println("Using Best PID Parameters:");
  Serial.print("Angle Loop - Kp: "); Serial.print(kp_angle);
  Serial.print(" Ki: "); Serial.print(ki_angle);
  Serial.print(" Kd: "); Serial.println(kd_angle);
  
  Serial.print("Speed Loop - Kp: "); Serial.print(kp_speed);
  Serial.print(" Ki: "); Serial.print(ki_speed);
  Serial.print(" Kd: "); Serial.println(kd_speed);
  
  if (CONTROL_MODE == 2) {
    Serial.print("Position Loop - Kp: "); Serial.print(kp_position);
    Serial.print(" Ki: "); Serial.print(ki_position);
    Serial.print(" Kd: "); Serial.println(kd_position);
  }
  
  Serial.print("\nControl Mode: ");
  if (CONTROL_MODE == 0) Serial.println("Angle Only");
  else if (CONTROL_MODE == 1) Serial.println("Angle + Speed");
  else Serial.println("Angle + Speed + Position");
  Serial.println();
  
  // 直接运行控制循环（无限循环，不退出）
  Serial.println("--- Running (Continuous) ---");
  Serial.println("Robot is now balancing...\n");
  
  speed_setpoint = 0;
  if (CONTROL_MODE == 2) {
    position_setpoint = enc_count;
  }
  
  unsigned long last_print = 0;
  while (true) {  // 无限循环
    // 等待定时器触发PID更新
    if (pid_update_flag) {
      pid_update_flag = false;
      updatePID();
    }
    
    // 每秒输出一次状态
    if (millis() - last_print >= 1000) {
      last_print = millis();
      Serial.print("Angle: "); Serial.print(angleX, 2);
      Serial.print(" | Speed: "); Serial.print(current_speed, 1);
      Serial.print(" | Motor: "); Serial.println(abs(motor_output));
    }
  }
}


// ==================== Arduino主函数 ====================
void setup() {
  Serial.begin(9600);
  delay(100);  // 等待串口稳定
  
  Serial.println("\n========================================");
  Serial.println("   网格搜索调参系统");
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
  
  // 初始化电机
  Serial.print("4. 初始化电机...");
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
  
  // 初始化PID变量
  Serial.print("7. 初始化PID变量...");
  lastError_angle = 0;
  integral_angle = 0;
  lastError_speed = 0;
  integral_speed = 0;
  lastError_position = 0;
  integral_position = 0;
  Serial.println(" 完成");
  
  // 启动定时器中断 (5ms间隔, 200Hz)
  Serial.print("8. 启动定时器(200Hz)...");
  MsTimer2::set(PID_INTERVAL, timerISR);
  MsTimer2::start();
  Serial.println(" 完成");
  
  Serial.println("\n初始化完成！");
  Serial.println("========================================\n");
  
  // 根据模式执行相应功能
  if (SEARCH_MODE == -1) {
    directRun();  // 直接运行模式
  } else if (SEARCH_MODE == 0) {
    gridSearchAngle();
  } else if (SEARCH_MODE == 1) {
    gridSearchSpeed();
  } else {
    gridSearchPosition();
  }
}


void loop() {
  // PID控制由定时器中断处理，loop函数只负责非关键任务
  
  // 输出状态信息（降低频率避免影响性能）
  static unsigned long last_print = 0;
  if (millis() - last_print >= 1000) {  // 每秒输出一次
    last_print = millis();
    
    int active_mode = (SEARCH_MODE == -1) ? CONTROL_MODE : SEARCH_MODE;
    
    Serial.print("Angle: "); Serial.print(angleX, 2);
    Serial.print(" | Speed: "); Serial.print(current_speed, 1);
    
    if (active_mode == 2) {
      Serial.print(" | Position: "); Serial.print(current_position);
      Serial.print(" | PosErr: "); Serial.print(error_position, 1);
    }
    
    Serial.print(" | Motor: "); Serial.println(abs(motor_output));
  }
}