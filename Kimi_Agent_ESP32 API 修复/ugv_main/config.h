// config.h
// 引脚定义 + 参数配置 + WiFi配置 + UWB配置

#ifndef CONFIG_H
#define CONFIG_H

#include <Arduino.h>

// ========== 电机引脚 ==========
#define PIN_PWMA  25
#define PIN_AIN2  17
#define PIN_AIN1  21
#define PIN_BIN1  22
#define PIN_BIN2  23
#define PIN_PWMB  26

// ========== PWM 配置 ==========
// ESP32 Arduino 3.x: ledcAttach(pin, freq, bits) 直接绑定引脚，不再需要通道号
#define PWM_BITS   8
#define PWM_FREQ   100000
#define PWM_MAX    255

// ========== 电机方向反转开关 ==========
#define MOTOR_DIR_REVERSED   true

// ========== WiFi 模式 ==========
#define UGV_WIFI_STA   1
#define UGV_WIFI_AP    2
#define UGV_WIFI_BOTH  3
#define WIFI_DEFAULT_MODE  UGV_WIFI_STA

#define WIFI_AP_SSID      "UGV_car"
#define WIFI_AP_PASSWORD  "12345678"
#define WIFI_STA_SSID     " fast_wifi"
#define WIFI_STA_PASSWORD "12345678"

// TCP 服务器端口
#define TCP_SERVER_PORT   8888

// 心跳超时(ms)
#define HEART_BEAT_TIMEOUT  1000000000

// ========== UWB 配置 ==========
// UWB 使用 UART2（Serial2），避免与 UART0 调试串口冲突
// 接线：UWB TX -> GPIO16 (UART2 RX)，UWB GND -> GND
// TX 设为 -1 表示不使用（单向接收），避免与 PIN_AIN2 (GPIO17) 冲突
#define UWB_UART_RX_PIN   16   // UART2 RX (GPIO16)
#define UWB_UART_TX_PIN   -1   // 不使用 TX（单向接收），避免与 GPIO17 冲突
#define UWB_BAUD_RATE     921600

// UWB 数据缓冲区大小
#define UWB_BUF_SIZE      256

// UWB 数据超时(ms)
#define UWB_TIMEOUT_MS    1000

// UWB 数据推送间隔(ms)，默认 200ms = 5Hz
#define UWB_PUSH_INTERVAL  200

#endif
