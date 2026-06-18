// motor_driver.cpp
#include "config.h"
#include "motor_driver.h"

void motorInit() {
  pinMode(PIN_AIN1, OUTPUT);
  pinMode(PIN_AIN2, OUTPUT);
  pinMode(PIN_PWMA, OUTPUT);
  pinMode(PIN_BIN1, OUTPUT);
  pinMode(PIN_BIN2, OUTPUT);
  pinMode(PIN_PWMB, OUTPUT);

  // ESP32 Arduino 3.x 新 API：ledcAttach 同时完成频率设置和引脚绑定
  ledcAttach(PIN_PWMA, PWM_FREQ, PWM_BITS);
  ledcAttach(PIN_PWMB, PWM_FREQ, PWM_BITS);

  digitalWrite(PIN_AIN1, LOW);
  digitalWrite(PIN_AIN2, LOW);
  digitalWrite(PIN_BIN1, LOW);
  digitalWrite(PIN_BIN2, LOW);
}

static inline void driveA(int pwm) {
  if (MOTOR_DIR_REVERSED) {
    if (pwm >= 0) { digitalWrite(PIN_AIN1, LOW);  digitalWrite(PIN_AIN2, HIGH); }
    else          { digitalWrite(PIN_AIN1, HIGH); digitalWrite(PIN_AIN2, LOW);  pwm = -pwm; }
  } else {
    if (pwm >= 0) { digitalWrite(PIN_AIN1, HIGH); digitalWrite(PIN_AIN2, LOW);  }
    else          { digitalWrite(PIN_AIN1, LOW);  digitalWrite(PIN_AIN2, HIGH); pwm = -pwm; }
  }
  if (pwm > PWM_MAX) pwm = PWM_MAX;
  // ESP32 Arduino 3.x：ledcWrite 按引脚写入（不再是按通道）
  ledcWrite(PIN_PWMA, pwm);
}

static inline void driveB(int pwm) {
  if (MOTOR_DIR_REVERSED) {
    if (pwm >= 0) { digitalWrite(PIN_BIN1, LOW);  digitalWrite(PIN_BIN2, HIGH); }
    else          { digitalWrite(PIN_BIN1, HIGH); digitalWrite(PIN_BIN2, LOW);  pwm = -pwm; }
  } else {
    if (pwm >= 0) { digitalWrite(PIN_BIN1, HIGH); digitalWrite(PIN_BIN2, LOW);  }
    else          { digitalWrite(PIN_BIN1, LOW);  digitalWrite(PIN_BIN2, HIGH); pwm = -pwm; }
  }
  if (pwm > PWM_MAX) pwm = PWM_MAX;
  // ESP32 Arduino 3.x：ledcWrite 按引脚写入（不再是按通道）
  ledcWrite(PIN_PWMB, pwm);
}

void leftMotor(int pwm)  { driveA(pwm); }
void rightMotor(int pwm) { driveB(pwm); }

void motorSet(int pwmLeft, int pwmRight) {
  driveA(pwmLeft);
  driveB(pwmRight);
}

void motorStop() {
  digitalWrite(PIN_AIN1, LOW); digitalWrite(PIN_AIN2, LOW);
  digitalWrite(PIN_BIN1, LOW); digitalWrite(PIN_BIN2, LOW);
  // ESP32 Arduino 3.x：ledcWrite 按引脚写入（不再是按通道）
  ledcWrite(PIN_PWMA, 0);
  ledcWrite(PIN_PWMB, 0);
}
