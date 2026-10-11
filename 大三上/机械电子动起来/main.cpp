#include <MsTimer2.h>
#include <MPU6050_tockn.h>
#include <Wire.h>

// TODO: 加上速度环

// 硬件定义
#define SDA_Pin A4
#define SCL_Pin A5
#define LStart_PWM 24 // 左轮起转PWM
#define RStart_PWM 22 // 右轮起转PWM

// PID推送计时器（1秒推送一次当前参数）
unsigned long lastPushTime = 0;
const long pushInterval = 1000;

// 电机引脚
int PWMA = 10; // 左轮PWM
int IN_1 = 12; // 左轮方向1
int IN_2 = 13; // 左轮方向2
int A_C1 = 3;  // 左轮编码器 (注意：必须接Pin 3以支持中断)
int countA = 0;

int PWMB = 9; // 右轮PWM
int IN_3 = 7; // 右轮方向1
int IN_4 = 6; // 右轮方向2
int B_C1 = 2; // 右轮编码器
int countB = 0;

// MPU6050初始化
MPU6050 Mpu6050(Wire);
void MPU6050_begin() {
    Wire.begin();
    Mpu6050.begin();
    Mpu6050.calcGyroOffsets(true);
}

// 全局参数
int TIME_PID = 20;
float Keep_Angle = 0.278;

// 角度PID参数（前端可修改）
float Ang_Kp = 10.0; // 降低比例项防止爆冲
float Ang_Ki = 0.8;  // 降低积分项
float Ang_Kd = 0.7;  // 增加微分项抑制过冲

// PWM限制和平滑控制
const int MAX_ANG_PWM = 120; // 降低最大输出PWM防止爆冲
const int PWM_RAMP_RATE = 3; // PWM渐变速率（更平滑）
int lastAngPWM = 0;

// 角度控制变量
float AngleX, GyroX, GyroZ;
float Ang_Dif_Val, Ang_intg_Val;
int Ang_PWM;
int Speed_PWM = 0; // 速度环PWM输出

// 转速PID参数（备用）
float targetRPM_A = 0; // 目标速度设为0，保持静止
float cur_RPM_A = 0;
float error_A = 0;
float lastError_A = 0;
float derivative_A = 0;
float output_A = 0;
float integral_A = 0;

float targetRPM_B = 100;
float cur_RPM_B = 0;
float error_B = 0;
float lastError_B = 0;
float derivative_B = 0;
float output_B = 0;
float integral_B = 0;

float Speed_Kp = 1.0;
float Speed_Ki = 0.2;
float Speed_Kd = 0.01;

const int MIN_PWM = 0;
const int MAX_PWM = 255;
int test_speed = 0;
volatile bool pidFlag = false;

void MotorRun(int speedA, int speedB);

void pidTick() {
    pidFlag = true;
}

// 平滑电机控制函数
void SmoothMotorRun(int targetPWM_A, int targetPWM_B) {
    // 限制目标PWM范围
    targetPWM_A = constrain(targetPWM_A, -MAX_ANG_PWM, MAX_ANG_PWM);
    targetPWM_B = constrain(targetPWM_B, -MAX_ANG_PWM, MAX_ANG_PWM);

    // 平滑渐变 - 限制PWM变化速率
    if (targetPWM_A > lastAngPWM) {
        targetPWM_A = min(lastAngPWM + PWM_RAMP_RATE, targetPWM_A);
    } else if (targetPWM_A < lastAngPWM) {
        targetPWM_A = max(lastAngPWM - PWM_RAMP_RATE, targetPWM_A);
    }

    lastAngPWM = targetPWM_A;

    // 执行电机控制
    MotorRun(targetPWM_A, targetPWM_B);
}

// 解析前端PID数据
void parsePIDData(String data) {
    if (data.startsWith("PID:")) {
        int colonIndex = data.indexOf(':');
        String paramStr = data.substring(colonIndex + 1);

        int comma1 = paramStr.indexOf(',');
        int comma2 = paramStr.lastIndexOf(',');
        if (comma1 != -1 && comma2 != -1) {
            // 更新角度PID参数
            Ang_Kp = paramStr.substring(0, comma1).toFloat();
            Ang_Ki = paramStr.substring(comma1 + 1, comma2).toFloat();
            Ang_Kd = paramStr.substring(comma2 + 1).toFloat();

            // 重置积分项和上次PWM值，防止参数切换时的冲击
            Ang_intg_Val = 0;
            lastAngPWM = 0;

            // 回复前端确认
            Serial.print("PID_OK:");
            Serial.print(Ang_Kp);
            Serial.print(",");
            Serial.print(Ang_Ki);
            Serial.print(",");
            Serial.println(Ang_Kd);

            // 串口调试输出
            Serial.print("更新角度PID: ");
            Serial.print("Kp=");
            Serial.print(Ang_Kp);
            Serial.print(" Ki=");
            Serial.print(Ang_Ki);
            Serial.print(" Kd=");
            Serial.println(Ang_Kd);
        } else {
            Serial.println("PID_ERR: 格式错误（需为 PID:kp,ki,kd）");
        }
    }
    // 新增：在线调整平衡角度 (格式: ANG:0.5)
    else if (data.startsWith("ANG:")) {
        int colonIndex = data.indexOf(':');
        float newAngle = data.substring(colonIndex + 1).toFloat();
        Keep_Angle = newAngle;
        Serial.print("Angle_Updated:");
        Serial.println(Keep_Angle);
    }
    // 保留原速度控制
    else if (data.length() == 1) {
        char Receive_char = data[0];
        switch (Receive_char) {
        case '1': test_speed++; break;
        case '2': test_speed--; break;
        }
        Serial.print("Speed=");
        Serial.println(test_speed);
    }
}

// 编码器计数
void encoderISR_A() {
    countA++;
}
void encoderISR_B() {
    countB++;
}

// 改进的角度PID计算 - 防止爆冲
void AngPID_PWMCount() {
    Mpu6050.update();
    AngleX = Mpu6050.getAngleX();
    GyroX = Mpu6050.getGyroX();

    // 安全保护：角度过大时立即停止并重置积分
    if (abs(AngleX) > 25) {
        Ang_PWM = 0;
        Ang_intg_Val = 0; // 重置积分防止饱和
        lastAngPWM = 0;   // 重置上次PWM
        return;
    }

    Ang_Dif_Val = AngleX - Keep_Angle;

    // 死区控制：小角度偏差时不积分，防止积分饱和
    if (abs(Ang_Dif_Val) > 0.3) { // 减小死区阈值
        Ang_intg_Val += Ang_Dif_Val;
    } else {
        Ang_intg_Val *= 0.95; // 缓慢释放积分
    }

    // 更严格的积分限幅
    Ang_intg_Val = constrain(Ang_intg_Val, -150, 150);

    // PID计算
    Ang_PWM = Ang_Kp * Ang_Dif_Val + Ang_Ki * Ang_intg_Val + Ang_Kd * GyroX;

    // 输出限幅
    Ang_PWM = constrain(Ang_PWM, -MAX_ANG_PWM, MAX_ANG_PWM);
}

// 转速PID计算
void SpeedPID_PWMCount() {
    // 改进：根据电机驱动方向判断速度方向 (因为只有单相编码器)
    int direction = (Ang_PWM >= 0) ? 1 : -1;

    if (countA > 0) {
        cur_RPM_A = countA / 13.0 * (60000.0 / TIME_PID) * direction;
        countA = 0;
    } else {
        cur_RPM_A = 0;
    }

    // PID计算
    error_A = targetRPM_A - cur_RPM_A;
    integral_A += error_A;
    integral_A = constrain(integral_A, -2000, 2000);

    derivative_A = error_A - lastError_A;
    lastError_A = error_A;

    // 计算速度环输出
    float output = Speed_Kp * error_A + Speed_Ki * integral_A + Speed_Kd * derivative_A;

    // 更新全局速度PWM变量 (这里假设速度环对两个电机影响相同)
    // 注意：通常平衡小车的速度环输出是作为角度环的目标角度，或者直接叠加PWM
    // 这里按照要求直接叠加PWM
    Speed_PWM = (int)constrain(output, -MAX_PWM, MAX_PWM);
}

// 电机控制函数
void MotorRun(int speedA, int speedB) {
    int A_PWM, B_PWM;

    // 左轮控制
    if (speedA == 0) {
        analogWrite(PWMA, 0);
    } else if (speedA > 0) {
        digitalWrite(IN_1, HIGH);
        digitalWrite(IN_2, LOW);
        A_PWM = LStart_PWM + speedA;
        analogWrite(PWMA, constrain(A_PWM, MIN_PWM, MAX_PWM));
    } else {
        digitalWrite(IN_1, LOW);
        digitalWrite(IN_2, HIGH);
        A_PWM = -LStart_PWM + speedA;
        analogWrite(PWMA, constrain(-A_PWM, MIN_PWM, MAX_PWM));
    }

    // 右轮控制
    if (speedB == 0) {
        analogWrite(PWMB, 0);
    } else if (speedB > 0) {
        digitalWrite(IN_3, LOW);
        digitalWrite(IN_4, HIGH);
        B_PWM = RStart_PWM + speedB;
        analogWrite(PWMB, constrain(B_PWM, MIN_PWM, MAX_PWM));
    } else {
        digitalWrite(IN_3, HIGH);
        digitalWrite(IN_4, LOW);
        B_PWM = -RStart_PWM + speedB;
        analogWrite(PWMB, constrain(-B_PWM, MIN_PWM, MAX_PWM));
    }
}

// 推送当前PID参数到前端
void pushCurrentPID() {
    unsigned long currentTime = millis();
    if (currentTime - lastPushTime >= pushInterval) {
        lastPushTime = currentTime;
        // 推送格式：CUR_PID:kp,ki,kd
        Serial.print("CUR_PID:");
        Serial.print(Ang_Kp);
        Serial.print(",");
        Serial.print(Ang_Ki);
        Serial.print(",");
        Serial.println(Ang_Kd);

        // 同时推送角度和PWM信息用于调试
        Serial.print("DEBUG: Angle=");
        Serial.print(AngleX);
        Serial.print(" PWM=");
        Serial.println(Ang_PWM);
    }
}

// 电机初始化
void Motor_begin() {
    pinMode(IN_1, OUTPUT);
    pinMode(IN_2, OUTPUT);
    pinMode(PWMA, OUTPUT);
    pinMode(A_C1, INPUT_PULLUP);

    pinMode(IN_3, OUTPUT);
    pinMode(IN_4, OUTPUT);
    pinMode(PWMB, OUTPUT);
    pinMode(B_C1, INPUT_PULLUP);

    digitalWrite(IN_1, HIGH);
    digitalWrite(IN_2, LOW);
    analogWrite(PWMA, 0);

    digitalWrite(IN_3, LOW);
    digitalWrite(IN_4, HIGH);
    analogWrite(PWMB, 0);
}

void setup() {
    Serial.begin(9600); // 蓝牙波特率（与模块一致）
    Motor_begin();
    MPU6050_begin();

    // 附加编码器中断
    attachInterrupt(digitalPinToInterrupt(A_C1), encoderISR_A, CHANGE);
    attachInterrupt(digitalPinToInterrupt(B_C1), encoderISR_B, CHANGE);

    while (!Serial) { ; } // 等待串口就绪
    Serial.println("Ready! 平衡小车已启动（防爆冲模式）");
    Serial.println("初始PID参数:");
    Serial.print("Kp=");
    Serial.print(Ang_Kp);
    Serial.print(" Ki=");
    Serial.print(Ang_Ki);
    Serial.print(" Kd=");
    Serial.println(Ang_Kd);
    Serial.print("最大PWM限制: ");
    Serial.println(MAX_ANG_PWM);

    MsTimer2::set(TIME_PID, pidTick);
    MsTimer2::start();
}

void loop() {
    if (pidFlag) {
        noInterrupts();
        pidFlag = false;
        interrupts();

        AngPID_PWMCount();   // 计算角度环
        SpeedPID_PWMCount(); // 计算速度环

        // 最终PWM = 角度环 - 速度环 (负反馈：速度过快时需反向倾斜以减速)
        int Total_PWM = Ang_PWM - Speed_PWM;

        SmoothMotorRun(Total_PWM, Total_PWM);
    }

    // 读取前端蓝牙数据
    if (Serial.available() > 0) {
        String data = Serial.readStringUntil('\n');
        data.trim();
        if (data.length() > 0) {
            parsePIDData(data);
        }
    }

    pushCurrentPID();
}