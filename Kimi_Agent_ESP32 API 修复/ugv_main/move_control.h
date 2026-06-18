// move_control.h
// 运动控制函数：直接 PWM 控制，无编码器无 PID

#ifndef MOVE_CONTROL_H
#define MOVE_CONTROL_H

// 初始化底盘（电机驱动）
void chassisInit();

// 直线前进，pwm 范围 0~255
void moveForward(int pwm);

// 直线后退，pwm 传正数
void moveBackward(int pwm);

// 原地左转，pwm 传正数
void turnLeft(int pwm);

// 原地右转，pwm 传正数
void turnRight(int pwm);

// 差速左转（前进同时左转）
// pwm: 基准速度 0~255,  rate: 转弯强度 0.0~1.0（0=直行，1=原地转）
void turnLeftForward(int pwm, float rate);

// 差速右转（前进同时右转）
void turnRightForward(int pwm, float rate);

// 停车
void moveStop();

// 自定义左右轮 PWM (-255~255)
void movePWM(int pwmLeft, int pwmRight);

#endif
