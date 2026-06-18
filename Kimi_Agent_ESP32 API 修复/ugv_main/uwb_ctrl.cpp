// uwb_ctrl.cpp
// UWB 定位数据解析实现（Nooploop LinkTrack NLink 二进制协议）

#include "config.h"
#include "uwb_ctrl.h"

// ========== 全局状态变量定义 ==========
float uwbPosX = 0.0;
float uwbPosY = 0.0;
bool  uwbDataValid = false;
unsigned long uwbLastUpdate = 0;

// ========== 内部静态变量 ==========
static uint8_t  uwbBuf[UWB_BUF_SIZE];
static uint8_t  uwbIdx = 0;
static uint16_t uwbFrameLen = 0;
static bool     uwbSynced = false;
static uint16_t uwbFrameCount = 0;
static unsigned long uwbTimeout = UWB_TIMEOUT_MS;

// ========== 内部辅助函数 ==========

// Parse int24: 3-byte little-endian signed -> int32_t
static int32_t parseInt24(const uint8_t *b) {
  return (int32_t)(((uint32_t)b[0] << 8) | ((uint32_t)b[1] << 16) | ((uint32_t)b[2] << 24)) / 256;
}

// NLink checksum: sum of all bytes except last == last byte
static bool nlinkChecksumOk(const uint8_t *data, uint16_t len) {
  if (len < 2) return false;
  uint8_t sum = 0;
  for (uint16_t i = 0; i < len - 1; i++) sum += data[i];
  return sum == data[len - 1];
}

// Process a validated NLink frame and extract position.
static void processNLinkFrame() {
  uint8_t funcMark = uwbBuf[1];

  switch (funcMark) {
    case 0x01: {
      if (uwbIdx < 10) return;
      uwbPosX = parseInt24(uwbBuf + 4) / 1000.0f;
      uwbPosY = parseInt24(uwbBuf + 7) / 1000.0f;
      break;
    }
    case 0x04: {
      if (uwbFrameLen < 22 || !nlinkChecksumOk(uwbBuf, uwbFrameLen)) return;
      uwbPosX = parseInt24(uwbBuf + 12) / 1000.0f;
      uwbPosY = parseInt24(uwbBuf + 15) / 1000.0f;
      break;
    }
    default: return;
  }

  uwbDataValid = true;
  uwbLastUpdate = millis();

  // Print position every ~1s (50 frames) to avoid flooding serial monitor.
  uwbFrameCount++;
  if (uwbFrameCount >= 50) {
    uwbFrameCount = 0;
    Serial.print("[UWB] x="); Serial.print(uwbPosX, 3);
    Serial.print(" y="); Serial.println(uwbPosY, 3);
  }
}

// ========== 外部接口函数 ==========

void initUwbSerial() {
  // UART2 (Serial2) for UWB data, avoids conflict with UART0 debug output
  Serial2.begin(UWB_BAUD_RATE, SERIAL_8N1, UWB_UART_RX_PIN, UWB_UART_TX_PIN);
  uwbIdx = 0;
  uwbSynced = false;
  uwbFrameCount = 0;
  Serial.println("[UWB] NLink parser ready on Serial2 (921600), RX=GPIO16");
}

void uwbSerialRead() {
  while (Serial2.available() > 0) {
    uint8_t c = Serial2.read();

    if (!uwbSynced) {
      if (c == 0x55) {
        uwbBuf[0] = c;
        uwbIdx = 1;
        uwbFrameLen = 0;
        uwbSynced = true;
      }
      continue;
    }

    if (uwbIdx < UWB_BUF_SIZE) {
      uwbBuf[uwbIdx++] = c;
    } else {
      uwbSynced = false;
      continue;
    }

    if (uwbIdx == 2 && uwbFrameLen == 0) {
      uint8_t fm = uwbBuf[1];
      if (fm != 0x01 && fm != 0x04) {
        uwbSynced = false;
      }
    }

    // Tag_Frame0: extract once we have 10 bytes (header + pos fields).
    if (uwbBuf[1] == 0x01 && uwbIdx >= 10) {
      processNLinkFrame();
      uwbSynced = false;
      continue;
    }

    // Node_Frame2: read frame length from bytes 2-3.
    if (uwbBuf[1] == 0x04 && uwbIdx >= 4 && uwbFrameLen == 0) {
      uwbFrameLen = (uint16_t)uwbBuf[2] | ((uint16_t)uwbBuf[3] << 8);
      if (uwbFrameLen > UWB_BUF_SIZE || uwbFrameLen < 4) {
        uwbSynced = false;
      }
    }

    // Node_Frame2: frame complete?
    if (uwbBuf[1] == 0x04 && uwbFrameLen > 0 && uwbIdx >= uwbFrameLen) {
      processNLinkFrame();
      uwbSynced = false;
    }
  }

  // Check data timeout
  if (uwbDataValid && (millis() - uwbLastUpdate > uwbTimeout)) {
    uwbDataValid = false;
  }
}

bool isUwbDataValid() {
  return uwbDataValid && (millis() - uwbLastUpdate <= uwbTimeout);
}
