import sys
import socket
import cv2
import numpy as np
import signal
import struct
import json  # 新增：用于处理 JSON 指令
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QImage, QPixmap, QKeyEvent
from main_window import Ui_MainWindow  # 确保你的 main_window.py 在同目录下

# ==================== 1. 视频分片接收与组包线程 (保持不变) ====================
class VideoReceiveThread(QThread):
    new_frame_signal = pyqtSignal(QImage)

    def __init__(self):
        super().__init__()
        self.running = True
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_socket.bind(('0.0.0.0', 8080)) 
        self.udp_socket.settimeout(1.0) 
        self.frame_buffer = {} 

    def run(self):
        print("电脑端 UDP 接收服务已启动，正在监听 8080 端口...")
        while self.running:
            try:
                data, addr = self.udp_socket.recvfrom(2048)
                if data.startswith(b"TEXT_TEST:"):
                    print(f"【网络测试成功】成功接收到 K230 发来的文本: {data.decode('utf-8')} 来自: {addr}")
                    continue 
                
                if len(data) < 6:
                    continue
                
                frame_id, total_chunks, chunk_id = struct.unpack("!HHH", data[:6])
                payload = data[6:]
                
                if frame_id not in self.frame_buffer:
                    self.frame_buffer[frame_id] = [None] * total_chunks
                
                if chunk_id < total_chunks:
                    self.frame_buffer[frame_id][chunk_id] = payload
                
                if all(p is not None for p in self.frame_buffer[frame_id]):
                    jpeg_data = b"".join(self.frame_buffer[frame_id])
                    del self.frame_buffer[frame_id]
                    
                    nparr = np.frombuffer(jpeg_data, np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    
                    if frame is not None:
                        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        h, w, ch = rgb_image.shape
                        q_img = QImage(rgb_image.data, w, h, ch * w, QImage.Format_RGB888).copy()
                        self.new_frame_signal.emit(q_img)
                    else:
                        print(f"⚠️ 拼图完成，但 OpenCV 格式解析失败。")

            except socket.timeout:
                continue
            except Exception as e:
                print(f"视频接收异常: {e}")
                
        self.udp_socket.close()
        print("UDP 接收线程已安全关闭。")


# ==================== 2. 主界面控制窗体（已接入 TCP 逻辑） ====================
class ControlWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self) 
        self.setWindowTitle("车辆遥控控制系统 - 监控中心")

        # ---------------- 配置下位机 TCP 参数 ----------------
        self.TARGET_IP = "192.168.25.54"  # 填入你下位机（如车载树莓派/ESP32）的实际 IP
        self.TARGET_PORT = 8888           # 填入下位机 TCP 监听的端口
        self.tcp_socket = None
        
        # 初始化 TCP 连接
        self.init_tcp_connection()

        # 启动接收视频子线程
        self.video_thread = VideoReceiveThread()
        self.video_thread.new_frame_signal.connect(self.update_video_label)
        self.video_thread.start() 

        # 绑定遥控按钮点击事件 (直接下发对应的格式化字典/或映射字符)
        try:
            # 基础前后停
            self.btn_forward.clicked.connect(lambda: self.send_command({"T": 116, "pwm": 150}))
            self.btn_back.clicked.connect(lambda: self.send_command({"T": 117, "pwm": 150}))
            self.btn_stop.clicked.connect(lambda: self.send_command({"T": 115}))
            
            # 如果你的 UI 里有左右转向按钮，可以解开下面两行注释并对应好 UI 控件名
            self.btn_left.clicked.connect(lambda: self.send_command({"T": 118, "pwm": 150}))
            self.btn_right.clicked.connect(lambda: self.send_command({"T": 119, "pwm": 150}))
            
        except AttributeError as e:
            print(f"⚠️ UI提示: 部分遥控按钮可能未在 UI 文件中找到: {e}")

    def init_tcp_connection(self):
        """ 初始化 TCP 客户端并连接下位机 """
        try:
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # 设置超时时间，防止连不上时界面死锁
            self.tcp_socket.settimeout(2.0)
            print(f"正在尝试连接下位机 TCP [{self.TARGET_IP}:{self.TARGET_PORT}]...")
            self.tcp_socket.connect((self.TARGET_IP, self.TARGET_PORT))
            print("连接下位机成功！可以开始控制。")
            # 连接成功后恢复阻塞模式或保持合理超时
            self.tcp_socket.settimeout(None) 
        except Exception as e:
            print(f"❌ TCP 连接失败: {e}。请检查下位机网络或 IP/端口设置。")
            # 即使失败也别崩溃，允许后续重新初始化或单机调试
            self.tcp_socket = None

    def send_command(self, cmd_dict):
        """ 核心修改：通过 TCP 发送 JSON 指令 """
        if self.tcp_socket is None:
            print("⚠️ 发送失败：TCP 未连接，正在尝试重新连接...")
            self.init_tcp_connection()
            if self.tcp_socket is None:
                return

        try:
            # 将字典转换为紧凑型 JSON 字符串，并追加换行符 \n（很多下位机习惯以 \n 作为单条指令结束标志）
            json_str = json.dumps(cmd_dict) + "\n"
            
            # 发送数据
            self.tcp_socket.sendall(json_str.encode('utf-8'))
            print(f"成功发送 TCP 指令: {json_str.strip()}")
            
        except Exception as e:
            print(f"❌ 指令发送异常: {e}，断开连接准备重连。")
            try:
                self.tcp_socket.close()
            except:
                pass
            self.tcp_socket = None

    def update_video_label(self, q_img):
        pixmap = QPixmap.fromImage(q_img)
        scaled_pixmap = pixmap.scaled(self.video_window.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.video_window.setPixmap(scaled_pixmap)

    def keyPressEvent(self, event: QKeyEvent):
        # 扩展：键盘快捷键控制
        if event.key() == Qt.Key_W:
            self.send_command({"T": 116, "pwm": 150}) # W 键前进
        elif event.key() == Qt.Key_S:
            self.send_command({"T": 117, "pwm": 150}) # S 键后退
        elif event.key() == Qt.Key_A:
            self.send_command({"T": 118, "pwm": 150}) # A 键左转
        elif event.key() == Qt.Key_D:
            self.send_command({"T": 119, "pwm": 150}) # D 键右转
        elif event.key() == Qt.Key_Space:
            self.send_command({"T": 115})             # 空格键停止
        elif event.key() == Qt.Key_Q or event.key() == Qt.Key_Escape:
            print("检测到退出快捷键，正在关闭窗口...")
            self.close()

    def closeEvent(self, event):
        print("正在关闭后台网络监听与控制连接...")
        # 1. 关闭 UDP 视频线程
        self.video_thread.running = False 
        self.video_thread.wait() 
        
        # 2. 关闭 TCP 链路
        if self.tcp_socket:
            try:
                self.tcp_socket.close()
                print("TCP 控制连接已安全断开。")
            except:
                pass
                     
        event.accept() 
        print("系统已完全退出。")

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)
    window = ControlWindow()
    window.show()
    sys.exit(app.exec_())