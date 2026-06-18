// ugv_main.ino
// UGV 主程序：电机控制 + WiFi TCP + UWB 定位数据推送
//
// 功能：
//   - WiFi STA/AP 双模式，TCP Server 监听端口 8888
//   - 接收 JSON 命令控制电机（前进/后退/转弯/差速）
//   - UART2 接收 UWB 数据（Nooploop NLink 协议），解析 pos.x / pos.y
//   - UWB 数据定时推送（5Hz）到 TCP 客户端
//
// 依赖库：ArduinoJson (by Benoit Blanchon)
// 开发板：ESP32 Dev Module

#include "config.h"
#include "motor_driver.h"
#include "move_control.h"
#include "wifi_tcp.h"
#include "uwb_ctrl.h"

void setup() {
  // 串口调试初始化（UART0，115200）
  Serial.begin(115200);
  delay(500);

  Serial.println("\n\n========================================");
  Serial.println("  UGV Car + UWB - ESP32");
  Serial.println("  PWM Motor | WiFi TCP | UWB Position");
  Serial.println("========================================\n");

  // 初始化电机驱动
  Serial.println("[INIT] Motor driver...");
  chassisInit();
  Serial.println("[INIT] Motor OK");

  // 初始化 UWB 串口（UART2）
  Serial.println("[INIT] UWB serial...");
  initUwbSerial();
  Serial.println("[INIT] UWB OK");

  // 初始化 WiFi + TCP Server
  Serial.println("[INIT] WiFi & TCP...");
  wifiTcpInit();
  Serial.println("[INIT] WiFi TCP OK\n");

  Serial.println("========================================");
  Serial.println("  Setup complete, entering main loop");
  Serial.println("========================================\n");
}

void loop() {
  // 1. 处理 UWB 数据读取（必须在 loop 中高频调用）
  uwbSerialRead();

  // 2. 处理 TCP 连接、命令解析、UWB 定时推送
  wifiTcpLoop();

  // 3. 处理串口命令（调试用）
  handleSerial();
}
