import sys
import socket
import cv2
import numpy as np
import signal
import struct
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QImage, QPixmap, QKeyEvent
from main_window import Ui_MainWindow  # 确保你的 main_window.py 在同目录下

# ==================== 1. 视频分片接收与组包线程 ====================
class VideoReceiveThread(QThread):
    new_frame_signal = pyqtSignal(QImage)

    def __init__(self):
        super().__init__()
        self.running = True
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # 绑定的端口必须与你在 K230 上设置的 SERVER_PORT 一致 (8080)
        self.udp_socket.bind(('0.0.0.0', 8080)) 
        self.udp_socket.settimeout(1.0) # 防止无数据时接收无限锁死
        
        # 【核心新增】：建立用于缓存和组装分片的字典
        self.frame_buffer = {} 

    def run(self):
        print("电脑端 UDP 接收服务已启动，正在监听 8080 端口...")
        
        while self.running:
            try:
                # 接收 UDP 数据包（单包最大约 1500 字节，设 2048 足够）
                data, addr = self.udp_socket.recvfrom(2048)
                
                # 1. 兼容性拦截：文本心跳包
                if data.startswith(b"TEXT_TEST:"):
                    print(f"【网络测试成功】成功接收到 K230 发来的文本: {data.decode('utf-8')} 来自: {addr}")
                    continue 
                
                # 2. 核心逻辑：解析自定义分片网络包头部（前 6 字节）
                if len(data) < 6:
                    continue
                
                # 解包格式: !HHH 代表三个大端模式的 16 位无符号短整型（2字节 * 3）
                frame_id, total_chunks, chunk_id = struct.unpack("!HHH", data[:6])
                payload = data[6:] # 剥离头部，拿到真正的 JPEG 数据碎片
                
                # 3. 组包逻辑
                # 如果是新的一帧，在缓冲区里为它开辟对应的切片阵列空间
                if frame_id not in self.frame_buffer:
                    self.frame_buffer[frame_id] = [None] * total_chunks
                
                # 将碎片塞入对应的索引位置
                if chunk_id < total_chunks:
                    self.frame_buffer[frame_id][chunk_id] = payload
                
                # 4. 可靠性校验：检查这一帧的所有碎片是否全齐了
                if all(p is not None for p in self.frame_buffer[frame_id]):
                    # 碎片完整，开始把所有 bytes 链式拼回成一个大 JPEG
                    jpeg_data = b"".join(frame_buffer_list := self.frame_buffer[frame_id])
                    
                    # 拼完立刻清除这一帧在字典里的缓存，防止内存暴涨
                    del self.frame_buffer[frame_id]
                    
                    # 5. 解码并送入 PyQt5 信号槽
                    nparr = np.frombuffer(jpeg_data, np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    
                    if frame is not None:
                        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        h, w, ch = rgb_image.shape
                        
                        # .copy() 保证多线程多进程渲染内存安全
                        q_img = QImage(rgb_image.data, w, h, ch * w, QImage.Format_RGB888).copy()
                        self.new_frame_signal.emit(q_img)
                    else:
                        print(f"⚠️ 拼图完成，但 OpenCV 格式解析失败，可能传输过程存在丢包。")

            except socket.timeout:
                continue
            except Exception as e:
                print(f"视频接收异常: {e}")
                
        self.udp_socket.close()
        print("UDP 接收线程已安全关闭。")

# ==================== 2. 主界面控制窗体（保持你的逻辑） ====================
class ControlWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self) 
        self.setWindowTitle("车辆遥控控制系统 - 监控中心")

        # 启动接收子线程
        self.video_thread = VideoReceiveThread()
        self.video_thread.new_frame_signal.connect(self.update_video_label)
        self.video_thread.start() 

        # 绑定遥控按钮点击事件
        try:
            self.btn_forward.clicked.connect(lambda: self.send_command("MOVE_F"))
            self.btn_back.clicked.connect(lambda: self.send_command("MOVE_B"))
            self.btn_stop.clicked.connect(lambda: self.send_command("STOP"))
        except AttributeError as e:
            print(f"⚠️ UI提示: 部分遥控按钮可能未在 UI 文件中找到: {e}")

    def update_video_label(self, q_img):
        # 自适应缩放展示画面
        pixmap = QPixmap.fromImage(q_img)
        scaled_pixmap = pixmap.scaled(self.video_window.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.video_window.setPixmap(scaled_pixmap)

    def send_command(self, cmd):
        print(f"正在下发指令: {cmd}")

    # 快捷按键退出 (Q键 或 Esc键)
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Q or event.key() == Qt.Key_Escape:
            print("检测到退出快捷键，正在关闭窗口...")
            self.close()

    # 重写关闭事件：当点击右上角 X 按钮时，强制彻底杀死子线程
    def closeEvent(self, event):
        print("正在关闭后台网络监听...")
        self.video_thread.running = False 
        self.video_thread.wait()          
        event.accept()                    
        print("系统已完全退出。")

if __name__ == "__main__":
    # 允许标准的 终端 Ctrl+C 信号终止 PyQt5 进程
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    app = QApplication(sys.argv)
    window = ControlWindow()
    window.show()
    sys.exit(app.exec_())