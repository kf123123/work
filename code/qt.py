import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt

class CarControlApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("车辆远程控制中心 v1.0") # [cite: 15]
        self.setGeometry(100, 100, 800, 600)

        # 1. 创建一个容器（中央部件）
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # 2. 创建布局（垂直排列）
        self.layout = QVBoxLayout(self.central_widget)

        # 3. 添加一个显示标签，未来用来放视频
        self.video_display = QLabel("等待视频信号...")
        self.video_display.setAlignment(Qt.AlignCenter)
        self.video_display.setStyleSheet("background-color: black; color: white; font-size: 20px;")
        
        self.layout.addWidget(self.video_display)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CarControlApp()
    window.show()
    sys.exit(app.exec_())