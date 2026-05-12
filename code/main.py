import sys
import socket
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QImage, QPixmap
from main_window import Ui_MainWindow  # 导入你转换生成的界面类

# 1. 视频流接收线程 (UDP 模式)
class VideoReceiveThread(QThread):
    # 定义一个信号，负责把解码后的图片传给主界面
    new_frame_signal = pyqtSignal(QImage)

    def run(self):
        # 建立 UDP Socket 监听 OpenMV 发来的数据
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.bind(('0.0.0.0', 8080))  # 端口需与 OpenMV 一致
        
        while True:
            try:
                # 接收 UDP 数据包
                data, _ = udp_socket.recvfrom(65535)
                # 将字节流转换为 OpenCV 图像格式
                nparr = np.frombuffer(data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if frame is not None:
                    # 转换颜色空间 (BGR -> RGB) 并封装为 QImage
                    rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    h, w, ch = rgb_image.shape
                    q_img = QImage(rgb_image.data, w, h, ch * w, QImage.Format_RGB888)
                    # 发送信号给主线程
                    self.new_frame_signal.emit(q_img)
            except Exception as e:
                print(f"视频接收异常: {e}")

# 2. 主界面控制类
class ControlWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self) # 初始化 Designer 里的零件
        self.setWindowTitle("车辆遥控控制系统 - 监控中心")

        # 启动视频接收线程
        self.video_thread = VideoReceiveThread()
        self.video_thread.new_frame_signal.connect(self.update_video_label)
        self.video_thread.start()

        # 绑定按钮点击事件 (对应你的 objectName)
        self.btn_forward.clicked.connect(lambda: self.send_command("MOVE_F"))
        self.btn_back.clicked.connect(lambda: self.send_command("MOVE_B"))
        self.btn_stop.clicked.connect(lambda: self.send_command("STOP"))

    def update_video_label(self, q_img):
        # 将 QImage 转换成 Pixmap 并贴到你设计的 video_window 零件上
        self.video_window.setPixmap(QPixmap.fromImage(q_img))

    def send_command(self, cmd):
        # 这里将来对接白宇负责的 Zigbee 串口通信
        print(f"正在下发指令: {cmd}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ControlWindow()
    window.show()
    sys.exit(app.exec_())