// uwb_ctrl.h
// UWB 定位数据解析，Nooploop LinkTrack NLink 二进制协议
// 接线：UWB TX -> GPIO16 (UART2 RX)，UWB GND -> GND

#ifndef UWB_CTRL_H
#define UWB_CTRL_H

#include "config.h"

// ========== UWB 全局状态变量 ==========
extern float uwbPosX;
extern float uwbPosY;
extern bool  uwbDataValid;
extern unsigned long uwbLastUpdate;

// ========== UWB 函数声明 ==========

// 初始化 UWB 串口（UART2，在 Serial.begin() 之后调用）
void initUwbSerial();

// 从 Serial2 读取并解析 UWB 数据（需在 loop() 中循环调用）
void uwbSerialRead();

// 检查 UWB 数据是否在有效期内
bool isUwbDataValid();

#endif // UWB_CTRL_H
