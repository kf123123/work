// motor_driver.h
// 电机驱动：直接 PWM 控制

#ifndef MOTOR_DRIVER_H
#define MOTOR_DRIVER_H

void motorInit();
void leftMotor(int pwm);
void rightMotor(int pwm);
void motorSet(int pwmLeft, int pwmRight);
void motorStop();

#endif
