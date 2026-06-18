import cv2
import socket
import struct
import time
import numpy as np

TARGET_IP = '127.0.0.1'
TARGET_PORT = 8080
MAX_UDP_SIZE = 1400

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# 尝试打开摄像头，如果没有则生成模拟测试画面
cap = cv2.VideoCapture(0)
use_camera = cap.isOpened()

if not use_camera:
    print("未检测到摄像头，使用模拟测试画面。")
    # 创建一个测试图案
    test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(test_frame, "TEST VIDEO", (150, 240),
                cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)

print(f"正在发送分片视频到 {TARGET_IP}:{TARGET_PORT} ...")
print("按 Ctrl+C 停止\n")

frame_id = 0
try:
    while True:
        if use_camera:
            ret, frame = cap.read()
            if not ret:
                continue
        else:
            # 生成带时间戳的动态测试画面
            test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            # 网格背景
            for i in range(0, 640, 40):
                cv2.line(test_frame, (i, 0), (i, 480), (32, 32, 32), 1)
            for j in range(0, 480, 40):
                cv2.line(test_frame, (0, j), (640, j), (32, 32, 32), 1)
            # 中心圆
            cv2.circle(test_frame, (320, 240), 60, (0, 120, 255), -1)
            cv2.circle(test_frame, (320, 240), 40, (0, 200, 255), -1)
            # 文本
            now_str = time.strftime("%H:%M:%S")
            cv2.putText(test_frame, f"Test Video {now_str}", (180, 240),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            frame = test_frame

        # 压缩 JPEG
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 40])
        jpeg_data = buffer.tobytes()

        frame_id = (frame_id + 1) & 0xFFFF
        total_chunks = (len(jpeg_data) + MAX_UDP_SIZE - 1) // MAX_UDP_SIZE

        for chunk_id in range(total_chunks):
            start = chunk_id * MAX_UDP_SIZE
            end = min(start + MAX_UDP_SIZE, len(jpeg_data))
            payload = jpeg_data[start:end]
            header = struct.pack("!HHH", frame_id, total_chunks, chunk_id)
            sock.sendto(header + payload, (TARGET_IP, TARGET_PORT))

        # 本地预览窗口
        cv2.imshow('Test Sender', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        time.sleep(0.03)

except KeyboardInterrupt:
    print("\n已停止")
finally:
    if use_camera:
        cap.release()
    sock.close()
    cv2.destroyAllWindows()
