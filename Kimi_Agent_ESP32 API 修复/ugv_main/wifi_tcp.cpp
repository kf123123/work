// wifi_tcp.cpp
// WiFi + TCP Server + 串口命令处理 + UWB 数据定时推送

#include "config.h"
#include "wifi_tcp.h"
#include "motor_driver.h"
#include "move_control.h"
#include "uwb_ctrl.h"
#include <ArduinoJson.h>

static WiFiServer tcpServer(TCP_SERVER_PORT);
static WiFiClient tcpClient;
static unsigned long lastHeartBeat = 0;
static String recvBuffer = "";
static String serialBuffer = "";

// UWB 定时推送状态
static unsigned long lastUwbPush = 0;
static bool uwbPushEnabled = true;   // 默认开启 UWB 自动推送

#define WIFI_CONNECT_TIMEOUT  15000

// ========== WiFi ==========

static bool wifiConnect() {
  Serial.println("\n========== [WiFi] Connecting... ==========");
  Serial.print("[WiFi] SSID: "); Serial.println(WIFI_STA_SSID);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_STA_SSID, WIFI_STA_PASSWORD);

  Serial.print("[WiFi] Connecting");
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    if (millis() - start > WIFI_CONNECT_TIMEOUT) {
      Serial.println("\n[WiFi] TIMEOUT!");
      return false;
    }
  }

  Serial.println("\n[WiFi] CONNECTED!");
  Serial.print("[WiFi] IP: ");   Serial.println(WiFi.localIP().toString());
  Serial.print("[WiFi] RSSI: "); Serial.print(WiFi.RSSI());
  Serial.println(" dBm");
  Serial.println("==========================================\n");
  return true;
}

static void wifiStartAP() {
  Serial.println("\n[WiFi] Fallback to AP mode...");
  WiFi.mode(WIFI_AP);
  WiFi.softAP(WIFI_AP_SSID, WIFI_AP_PASSWORD);
  Serial.print("[WiFi] AP: ");     Serial.println(WIFI_AP_SSID);
  Serial.print("[WiFi] Password: "); Serial.println(WIFI_AP_PASSWORD);
  Serial.print("[WiFi] IP: ");     Serial.println(WiFi.softAPIP().toString());
}

void wifiTcpInit() {
  lastHeartBeat = millis();
  lastUwbPush = millis();

  bool staOk = wifiConnect();
  if (!staOk) {
    wifiStartAP();
  }
  tcpServer.begin();
  Serial.println("\n========== [TCP] Server Ready ==========");
  Serial.print("[TCP] Port: "); Serial.println(TCP_SERVER_PORT);
  Serial.print("[TCP] Device IP: "); Serial.println(getDeviceIP());
  Serial.println("========================================\n");
}

// ========== UWB 数据发送到 TCP ==========

void sendUwbData() {
  if (!tcpClient || !tcpClient.connected()) return;

  StaticJsonDocument<128> doc;
  doc["T"] = 200;           // UWB 数据消息类型
  doc["x"] = uwbPosX;       // X 坐标 (m)
  doc["y"] = uwbPosY;       // Y 坐标 (m)
  doc["valid"] = isUwbDataValid();  // 数据是否有效
  doc["t"] = millis();      // 时间戳

  String out;
  serializeJson(doc, out);
  tcpClient.println(out);
}

// ========== 命令解析（TCP 和 串口 共用） ==========

void execCommand(const String &jsonStr) {
  Serial.print("[CMD RECV] [");
  Serial.print(jsonStr.length());
  Serial.print("] ");
  Serial.println(jsonStr);

  if (jsonStr.length() == 0) return;

  StaticJsonDocument<256> doc;
  DeserializationError err = deserializeJson(doc, jsonStr);
  if (err) {
    Serial.print("[CMD] JSON error: ");
    Serial.println(err.c_str());
    return;
  }

  int cmd = doc["T"] | -1;

  switch (cmd) {
    // ----- 电机控制命令 -----
    case 1: {
      float l = doc["L"] | 0.0f;
      float r = doc["R"] | 0.0f;
      int pwmL = constrain((int)(l * PWM_MAX), -PWM_MAX, PWM_MAX);
      int pwmR = constrain((int)(r * PWM_MAX), -PWM_MAX, PWM_MAX);
      movePWM(pwmL, pwmR);
      Serial.printf("[CMD] Speed: L=%d R=%d\n", pwmL, pwmR);
      break;
    }

    case 11: {
      int pwmL = constrain(doc["L"] | 0, -PWM_MAX, PWM_MAX);
      int pwmR = constrain(doc["R"] | 0, -PWM_MAX, PWM_MAX);
      movePWM(pwmL, pwmR);
      Serial.printf("[CMD] PWM: L=%d R=%d\n", pwmL, pwmR);
      break;
    }

    case 115:
      moveStop();
      Serial.println("[CMD] STOP");
      break;

    case 116: {
      int pwm = doc["pwm"] | 150;
      moveForward(pwm);
      Serial.printf("[CMD] Forward: pwm=%d\n", pwm);
      break;
    }

    case 117: {
      int pwm = doc["pwm"] | 150;
      moveBackward(pwm);
      Serial.printf("[CMD] Backward: pwm=%d\n", pwm);
      break;
    }

    case 118: {
      int pwm = doc["pwm"] | 150;
      turnLeft(pwm);
      Serial.printf("[CMD] TurnLeft: pwm=%d\n", pwm);
      break;
    }

    case 119: {
      int pwm = doc["pwm"] | 150;
      turnRight(pwm);
      Serial.printf("[CMD] TurnRight: pwm=%d\n", pwm);
      break;
    }

    // ----- UWB 相关命令 -----
    case 200: {
      // PC 主动查询 UWB 数据 -> 立即发送一次
      sendUwbData();
      Serial.println("[CMD] UWB data sent");
      break;
    }

    case 201: {
      // 开启/关闭 UWB 自动推送
      int en = doc["en"] | 1;
      uwbPushEnabled = (en != 0);
      Serial.printf("[CMD] UWB auto push: %s\n", uwbPushEnabled ? "ON" : "OFF");

      // 发送确认
      if (tcpClient && tcpClient.connected()) {
        StaticJsonDocument<64> ack;
        ack["T"] = 201;
        ack["en"] = uwbPushEnabled;
        String out;
        serializeJson(ack, out);
        tcpClient.println(out);
      }
      break;
    }

    case 999: {
      Serial.println("[CMD] Heartbeat OK");
      break;
    }

    default:
      Serial.printf("[CMD] Unknown T=%d\n", cmd);
      break;
  }

  lastHeartBeat = millis();
}

// ========== 串口处理 ==========

void handleSerial() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (serialBuffer.length() > 0) {
        execCommand(serialBuffer);
        serialBuffer = "";
      }
    } else if (serialBuffer.length() < 512) {
      serialBuffer += c;
    }
  }
}

// ========== TCP 处理（含 UWB 推送） ==========

void wifiTcpLoop() {
  // 检查新连接
  if (tcpServer.hasClient()) {
    if (tcpClient && tcpClient.connected()) {
      tcpClient.stop();
      Serial.println("[TCP] Old client kicked");
    }
    tcpClient = tcpServer.available();
    recvBuffer = "";
    Serial.print("[TCP] Client connected: ");
    Serial.println(tcpClient.remoteIP().toString());
    tcpClient.println("{\"msg\":\"UGV OK\",\"ip\":\"" + getDeviceIP() + "\"}");
  }

  // 读取 TCP 数据
  if (tcpClient && tcpClient.connected()) {
    while (tcpClient.available()) {
      char c = tcpClient.read();
      if (c == '\n' || c == '\r') {
        if (recvBuffer.length() > 0) {
          execCommand(recvBuffer);
          recvBuffer = "";
        }
      } else if (recvBuffer.length() < 512) {
        recvBuffer += c;
      }
    }

    // 心跳超时检测
    if (millis() - lastHeartBeat > HEART_BEAT_TIMEOUT) {
      moveStop();
      lastHeartBeat = millis();
    }

    // ===== UWB 数据定时推送 =====
    if (uwbPushEnabled && (millis() - lastUwbPush >= UWB_PUSH_INTERVAL)) {
      lastUwbPush = millis();
      sendUwbData();
    }
  }

  // 检测断连
  if (tcpClient && !tcpClient.connected()) {
    tcpClient.stop();
    moveStop();
    Serial.println("[TCP] Client disconnected");
  }
}

String getDeviceIP() {
  if (WiFi.getMode() & WIFI_STA) {
    return WiFi.localIP().toString();
  }
  return WiFi.softAPIP().toString();
}

bool isClientConnected() {
  return tcpClient && tcpClient.connected();
}
