// 编码器模块
#ifndef ENCODER_H
#define ENCODER_H

#include <Arduino.h>
#include <PinChangeInterrupt.h>
#include "config.h"

// 编码器计数
volatile long encoderCountA = 0;
volatile long encoderCountB = 0;

// 速度变量
float motorSpeedA = 0;
float motorSpeedB = 0;
long lastCountA = 0;
long lastCountB = 0;

// 电机A编码器中断
void handleEncoderA() {
  int a = digitalRead(ENC_A1);
  int b = digitalRead(ENC_A2);
  encoderCountA += (a != b) ? 1 : -1;
}

// 电机B编码器中断
void handleEncoderB() {
  int a = digitalRead(ENC_B1);
  int b = digitalRead(ENC_B2);
  encoderCountB += (a != b) ? 1 : -1;
}

// 初始化编码器
void initEncoder() {
  pinMode(ENC_A1, INPUT_PULLUP);
  pinMode(ENC_A2, INPUT_PULLUP);
  pinMode(ENC_B1, INPUT_PULLUP);
  pinMode(ENC_B2, INPUT_PULLUP);
  
  attachPinChangeInterrupt(
    digitalPinToPinChangeInterrupt(ENC_A1),
    handleEncoderA,
    CHANGE
  );
  attachPinChangeInterrupt(
    digitalPinToPinChangeInterrupt(ENC_B1),
    handleEncoderB,
    CHANGE
  );
}

// 计算速度(10ms调用一次)
void calculateSpeed() {
  long diffA = encoderCountA - lastCountA;
  long diffB = encoderCountB - lastCountB;
  
  motorSpeedA = diffA;  // 速度单位：脉冲/10ms
  motorSpeedB = diffB;
  
  lastCountA = encoderCountA;
  lastCountB = encoderCountB;
}

#endif
