# UGV 完整项目代码

## 项目说明

ESP32 智能小车控制程序，集成电机驱动、WiFi TCP 通信、UWB 定位数据推送。

**适配 ESP32 Arduino Core 3.x**（已修复 ledcSetup/ledcAttachPin 兼容性问题）

## 文件清单

| 文件 | 功能 |
|------|------|
| `ugv_main.ino` | Arduino 主程序（setup + loop） |
| `config.h` | 引脚定义、PWM配置、WiFi配置、UWB配置 |
| `motor_driver.h/cpp` | 电机 PWM 驱动（ESP32 3.x API） |
| `move_control.h/cpp` | 运动控制（前进/后退/转弯/差速） |
| `uwb_ctrl.h/cpp` | UWB 定位数据解析（NLink 协议） |
| `wifi_tcp.h/cpp` | WiFi + TCP Server + 命令解析 + UWB 推送 |
| `test_tcp.py` | PC 端 TCP 控制脚本 |

## 引脚接线

### 电机驱动板
| 驱动板 | ESP32 GPIO |
|--------|-----------|
| PWMA | 25 |
| AIN2 | 17 |
| AIN1 | 21 |
| BIN1 | 22 |
| BIN2 | 23 |
| PWMB | 26 |

### UWB 模块（Nooploop LinkTrack）
| UWB 模块 | ESP32 |
|---------|-------|
| TX | GPIO16 (UART2 RX) |
| GND | GND |

## Arduino IDE 使用步骤

### 1. 安装依赖库

菜单 **工具 > 管理库**，搜索并安装：**ArduinoJson**（by Benoit Blanchon）

### 2. 修改 WiFi 配置

编辑 `config.h`：
```cpp
#define WIFI_STA_SSID     "你的WiFi名称"
#define WIFI_STA_SSID     "你的WiFi密码"
```

### 3. 打开项目

1. 将整个 `ugv_main` 文件夹放到 Arduino sketchbook 目录下
2. Arduino IDE：文件 > 打开 > 选择 `ugv_main.ino`
3. 开发板选择：**ESP32 Dev Module**
4. 点击上传

### 4. 串口监视器

波特率：**115200**，可查看调试输出

## TCP 命令格式

### 电机控制
```json
{"T":1,"L":0.5,"R":0.5}     // 差速控制（-1.0 ~ 1.0）
{"T":11,"L":150,"R":150}    // 直接 PWM（-255 ~ 255）
{"T":115}                       // 停止
{"T":116,"pwm":150}           // 前进
{"T":117,"pwm":150}           // 后退
{"T":118,"pwm":150}           // 原地左转
{"T":119,"pwm":150}           // 原地右转
{"T":999}                       // 心跳
```

### UWB 数据
```json
{"T":200}                       // 主动查询 UWB 数据
{"T":201,"en":1}              // 开启 UWB 自动推送（默认已开启）
{"T":201,"en":0}              // 关闭 UWB 自动推送
```

### UWB 数据回复（ESP32 -> PC）
```json
{"T":200,"x":1.234,"y":0.567,"valid":true,"t":12345}
```

推送频率：默认 5Hz（每 200ms 一次）

## PC 端控制

```bash
python test_tcp.py
```

按键控制：
- `W/S` - 前进/后退
- `A/D` - 左转/右转
- `Q` - 停止
- `U` - 查询 UWB 数据
- `P` - 切换 UWB 自动推送
- `X` - 退出

## 本次修复内容

### 1. ESP32 Arduino 3.x LEDC API 兼容性
| 旧 API (2.x) | 新 API (3.x) |
|---|---|
| `ledcSetup(channel, freq, bits)` + `ledcAttachPin(pin, channel)` | `ledcAttach(pin, freq, bits)` |
| `ledcWrite(channel, duty)` | `ledcWrite(pin, duty)` |

### 2. GPIO17 引脚冲突修复
- `PIN_AIN2` 使用 GPIO17（电机方向控制）
- `UWB_UART_TX_PIN` 改为 `-1`（不使用 TX，避免冲突）
- UWB 为单向接收模式，无需 TX 引脚
