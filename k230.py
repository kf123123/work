import time, os, sys, socket, struct, network
from media.sensor import *
from media.media import *

# ================== 1. 基础配置 ==================
WIFI_SSID = "fast_wifi"
WIFI_PASS = "12345678"

SERVER_IP = "192.168.153.189"
SERVER_PORT = 8080

MAX_UDP_SIZE = 1400

time.sleep(10)
# ================== 2. 无线网卡初始化与联网 ==================
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(WIFI_SSID, WIFI_PASS)

print("正在连接 Wi-Fi...")
while not wlan.isconnected():
    time.sleep(0.5)
    print(".", end="")

print("\n[成功] Wi-Fi 连接成功！")
print("K230 本机 IP 地址为:", wlan.ifconfig()[0])


# ================== 3. 摄像头与媒体硬件初始化 ==================
sensor = Sensor()
sensor.reset()
sensor.set_framesize(width=640, height=480)
sensor.set_pixformat(Sensor.RGB565)

MediaManager.init()
sensor.run()


# ================== 4. 创建 UDP 套接字 ==================
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
dest_addr = (SERVER_IP, SERVER_PORT)

print("--- K230 高帧率 UDP 传输启动 ---")
frame_id = 0

try:
    while True:
        img = sensor.snapshot()

        # 【核心优化点 1】：加入 quality 参数降低质量。数值越小，图片越小，帧率越高！
        # 推荐范围 20 - 50。这里设为 35 可以在保持看清路况的同时获得极高帧率。
        jpeg_tuple = img.compress_for_ide(quality=35)

        # 超级防御机制
        jpeg_data = None
        if jpeg_tuple is not None:
            if isinstance(jpeg_tuple, (tuple, list)):
                jpeg_data = jpeg_tuple[0]
            elif isinstance(jpeg_tuple, (bytes, bytearray)):
                jpeg_data = jpeg_tuple
            else:
                try:
                    jpeg_data = bytes(jpeg_tuple)
                except:
                    pass

        if jpeg_data is None or not isinstance(jpeg_data, (bytes, bytearray)):
            time.sleep_ms(5)
            continue

        frame_len = len(jpeg_data)

        if frame_len > 0:
            frame_id = (frame_id + 1) & 0xFFFF
            total_chunks = (frame_len + MAX_UDP_SIZE - 1) // MAX_UDP_SIZE

            # 5. 分片循环发送
            for chunk_id in range(total_chunks):
                start = chunk_id * MAX_UDP_SIZE
                end = min(start + MAX_UDP_SIZE, frame_len)

                payload = bytes(jpeg_data[start:end])
                header = struct.pack("!HHH", frame_id, total_chunks, chunk_id)

                try:
                    udp_socket.sendto(header + payload, dest_addr)
                except Exception as e:
                    pass # 高频传输中偶发单包失败直接跳过，保证实时性

        # 【核心优化点 2】：将强制死等 30ms 改为 1ms，解除软件限速，全力压榨硬件传输极限
        time.sleep_ms(1)

except KeyboardInterrupt:
    print("\n用户中断...")
finally:
    sensor.stop()
    MediaManager.deinit()
    udp_socket.close()
    wlan.active(False)
    print("资源已释放。")
