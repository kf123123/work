import cv2
import socket
import numpy as np

# 配置目标：发送到本地 (127.0.0.1)，端口 8080
TARGET_IP = '127.0.0.1' 
TARGET_PORT = 8080
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

cap = cv2.VideoCapture(0)

print("正在模拟车辆端发送视频流...")
while True:
    ret, frame = cap.read()
    if not ret: break

    # 1. 压缩图片以适应 UDP 传输（非常重要）
    # 将画面缩小到 320x240，质量设为 50，防止数据包过大导致丢包
    frame = cv2.resize(frame, (320, 240))
    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
    
    # 2. 发送字节流
    sock.sendto(buffer, (TARGET_IP, TARGET_PORT))
    
    cv2.imshow('Sender (Vehicle Side)', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
sock.close()