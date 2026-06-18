// wifi_tcp.h
// WiFi + TCP 通信 + 串口命令 + UWB 数据推送

#ifndef WIFI_TCP_H
#define WIFI_TCP_H

#include <WiFi.h>

// 初始化 WiFi 和 TCP Server
void wifiTcpInit();

// 处理 TCP 连接、数据接收、UWB 推送（在 loop 中调用）
void wifiTcpLoop();

// 处理串口命令（在 loop 中调用）
void handleSerial();

// 解析并执行 JSON 命令（TCP 和 串口 共用）
void execCommand(const String &jsonStr);

// 获取 ESP32 的 IP 地址
String getDeviceIP();

// 检查是否有 TCP 客户端连接
bool isClientConnected();

// 发送 UWB 数据到 TCP 客户端（JSON 格式）
void sendUwbData();

#endif
