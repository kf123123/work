// move_control.cpp
#include "config.h"
#include "motor_driver.h"
#include "move_control.h"

void chassisInit() {
  motorInit();
}

void moveForward(int pwm)        { if (pwm < 0) pwm = 0; if (pwm > PWM_MAX) pwm = PWM_MAX; motorSet( pwm,  pwm); }
void moveBackward(int pwm)       { if (pwm < 0) pwm = 0; if (pwm > PWM_MAX) pwm = PWM_MAX; motorSet(-pwm, -pwm); }
void turnLeft(int pwm)           { if (pwm < 0) pwm = 0; if (pwm > PWM_MAX) pwm = PWM_MAX; motorSet(-pwm,  pwm); }
void turnRight(int pwm)          { if (pwm < 0) pwm = 0; if (pwm > PWM_MAX) pwm = PWM_MAX; motorSet( pwm, -pwm); }
void moveStop()                  { motorStop(); }
void movePWM(int pwmL, int pwmR) { motorSet(pwmL, pwmR); }

void turnLeftForward(int pwm, float rate) {
  if (pwm < 0) pwm = 0; if (pwm > PWM_MAX) pwm = PWM_MAX;
  if (rate < 0) rate = 0; if (rate > 1) rate = 1;
  int left  = pwm * (1 - 2 * rate);
  int right = pwm;
  motorSet(left, right);
}

void turnRightForward(int pwm, float rate) {
  if (pwm < 0) pwm = 0; if (pwm > PWM_MAX) pwm = PWM_MAX;
  if (rate < 0) rate = 0; if (rate > 1) rate = 1;
  int left  = pwm;
  int right = pwm * (1 - 2 * rate);
  motorSet(left, right);
}
