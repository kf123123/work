import time, os, sys, socket, struct, network
from media.sensor import *
from media.media import *

# ================== 1. 基础配置（请根据实际情况修改） ==================
WIFI_SSID = "最快的wifi"     # 👈 替换为你的 Wi-Fi 名字
WIFI_PASS = "12345678"     # 👈 替换为你的 Wi-Fi 密码

SERVER_IP = "192.168.25.189"  # 👈 替换为你电脑的实际 IP 地址
SERVER_PORT = 8080

MAX_UDP_SIZE = 1400           # 每个 UDP 包的最大负载（小于以太网 MTU 1500）


# ================== 2. 无线网卡初始化与联网 ==================
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(WIFI_SSID, WIFI_PASS)

print("正在连接 Wi-Fi...")
retry_count = 0
while not wlan.isconnected():
    time.sleep(0.5)
    print(".", end="")
    retry_count += 1
    if retry_count > 30: # 超过15秒未连上提示检查
        print("\n[警告] Wi-Fi 连接时间过长，请检查名称和密码是否正确！")
        retry_count = 0

print("\n[成功] Wi-Fi 连接成功！")
print("K230 本机 IP 地址为:", wlan.ifconfig()[0])


# ================== 3. 摄像头与媒体硬件初始化 ==================
sensor = Sensor() 
sensor.reset() 
sensor.set_framesize(width=640, height=480) # 采集 VGA 分辨率，兼顾清晰度与网络流畅度
sensor.set_pixformat(Sensor.RGB565)         # 01科技硬件支持的标准格式

MediaManager.init() # 初始化媒体资源管理器
sensor.run()        # 启动摄像头


# ================== 4. 创建 UDP 套接字 ==================
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
dest_addr = (SERVER_IP, SERVER_PORT)

print("--- 01Studio K230 UDP 分片传输已就绪，开始发射视频流 ---")
frame_id = 0

try:
    while True:
        # 捕捉一帧画面
        img = sensor.snapshot()
        
        # 将画面在内存中压缩为 JPEG 格式
        jpeg_tuple = img.compress_for_ide(fps=30) 
        
        # 【超级防御机制】：解决部分固件返回 tuple 导致 bytes 拼接报错的问题
        jpeg_data = None
        if jpeg_tuple is not None:
            if isinstance(jpeg_tuple, (tuple, list)):
                jpeg_data = jpeg_tuple[0] # 提取元组内的纯 bytes
            elif isinstance(jpeg_tuple, (bytes, bytearray)):
                jpeg_data = jpeg_tuple
            else:
                try:
                    jpeg_data = bytes(jpeg_tuple)
                except:
                    pass

        # 容错处理：如果提取数据失败，跳过本帧
        if jpeg_data is None or not isinstance(jpeg_data, (bytes, bytearray)):
            print("当前帧压缩数据异常，自动跳过")
            time.sleep_ms(10)
            continue
            
        frame_len = len(jpeg_data)
        
        if frame_len > 0:
            frame_id = (frame_id + 1) & 0xFFFF # 帧 ID 自增循环
            total_chunks = (frame_len + MAX_UDP_SIZE - 1) // MAX_UDP_SIZE
            
            # 5. 开始分片循环发送
            for chunk_id in range(total_chunks):
                start = chunk_id * MAX_UDP_SIZE
                end = min(start + MAX_UDP_SIZE, frame_len)
                
                # 强转 bytes 确保数据切片类型绝对纯正
                payload = bytes(jpeg_data[start:end]) 
                
                # 构造 6 字节自定义头部: [帧ID(2字节)][总片数(2字节)][当前片序号(2字节)]
                header = struct.pack("!HHH", frame_id, total_chunks, chunk_id)
                
                # 此时 header 和 payload 均为 bytes，完美拼接并由网卡发射
                try:
                    udp_socket.sendto(header + payload, dest_addr)
                except Exception as e:
                    print("网络发送突发失败:", e)
                
        # 维持在 30 帧左右的频率发送
        time.sleep_ms(30) 

except KeyboardInterrupt:
    print("\n用户中断，正在停止服务...")
finally:
    # 6. 安全倒序释放硬件与网络资源
    sensor.stop()
    MediaManager.deinit()
    udp_socket.close()
    wlan.active(False)
    print("资源已完全释放，程序退出。")