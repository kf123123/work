# -*- coding: utf-8 -*-

import sys
import socket
import cv2
import numpy as np
import signal
import struct
import json
import time
import math
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsView
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QImage, QPixmap, QKeyEvent, QPen, QBrush, QColor
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QPainterPath

# ==================== UI 样式表 ====================
TEAL_STYLE = """
QMainWindow { background-color: #111827; }
QWidget { color: #e2e8f0; font-family: "Microsoft YaHei","Segoe UI","PingFang SC",sans-serif; font-size: 13px; }
QGroupBox {
    background-color: #1f2937; border: 1px solid #374151; border-radius: 6px;
    margin-top: 10px; padding: 14px 8px 8px 8px; font-weight: bold; font-size: 13px; color: #9ca3af;
}
QGroupBox::title {
    subcontrol-origin: margin; subcontrol-position: top left;
    padding: 2px 8px; background-color: transparent; color: #2dd4bf; letter-spacing: 1px;
}
QPushButton {
    background-color: #374151; color: #e2e8f0; border: 1px solid #4b5563;
    border-radius: 6px; padding: 4px 10px; font-size: 12px; font-weight: bold;
}
QPushButton:hover { background-color: #4b5563; border-color: #6b7280; }
QPushButton:pressed { background-color: #1f2937; }
QPushButton#btn_forward {
    background-color: #064e3b; border-color: #059669; color: #6ee7b7;
}
QPushButton#btn_forward:hover { background-color: #065f46; border-color: #10b981; }
QPushButton#btn_forward:pressed { background-color: #022c22; border-color: #34d399; }
QPushButton#btn_back {
    background-color: #7c2d12; border-color: #c2410c; color: #fdba74;
}
QPushButton#btn_back:hover { background-color: #9a3412; border-color: #ea580c; }
QPushButton#btn_back:pressed { background-color: #431407; border-color: #fb923c; }
QPushButton#btn_left, QPushButton#btn_right {
    background-color: #1e3a5f; border-color: #1d4ed8; color: #93c5fd;
}
QPushButton#btn_left:hover, QPushButton#btn_right:hover { background-color: #1e40af; border-color: #3b82f6; }
QPushButton#btn_left:pressed, QPushButton#btn_right:pressed { background-color: #172554; border-color: #60a5fa; }
QPushButton#btn_fwd_left, QPushButton#btn_fwd_right {
    background-color: #155e75; border-color: #0891b2; color: #67e8f9;
}
QPushButton#btn_fwd_left:hover, QPushButton#btn_fwd_right:hover { background-color: #164e63; border-color: #06b6d4; }
QPushButton#btn_fwd_left:pressed, QPushButton#btn_fwd_right:pressed { background-color: #083344; border-color: #22d3ee; }
QPushButton#btn_bwd_left, QPushButton#btn_bwd_right {
    background-color: #4c1d95; border-color: #7c3aed; color: #c4b5fd;
}
QPushButton#btn_bwd_left:hover, QPushButton#btn_bwd_right:hover { background-color: #5b21b6; border-color: #8b5cf6; }
QPushButton#btn_bwd_left:pressed, QPushButton#btn_bwd_right:pressed { background-color: #2e1065; border-color: #a78bfa; }
QPushButton#btn_stop {
    background-color: #7f1d1d; border-color: #dc2626; color: #fca5a5; font-size: 14px;
}
QPushButton#btn_stop:hover { background-color: #991b1b; border-color: #ef4444; }
QPushButton#btn_stop:pressed { background-color: #450a0a; border-color: #f87171; }
QLabel#video_window { background-color: #0f172a; border: 1px solid #374151; border-radius: 4px; }
QTableView {
    background-color: #1f2937; alternate-background-color: #1a2332; border: 1px solid #374151;
    border-radius: 4px; gridline-color: transparent;
    selection-background-color: transparent; selection-color: #e2e8f0;
}
QTableView::item { padding: 8px 12px; border-bottom: 1px solid #374151; }
QHeaderView::section {
    background-color: #111827; color: #9ca3af; border: none;
    border-bottom: 1px solid #374151; padding: 8px 12px; font-weight: bold;
}
QSlider::groove:vertical { border: 1px solid #374151; background: #111827; border-radius: 3px; width: 6px; }
QSlider::handle:vertical { background: #2dd4bf; border: none; border-radius: 4px; height: 16px; width: 16px; margin: -4px -4px; }
QSlider::handle:vertical:hover { background: #5eead4; }
QSlider::sub-page:vertical { background: #14b8a6; border-radius: 3px; }
QSlider::add-page:vertical { background: #111827; border-radius: 3px; }
QSlider::tick { color: #4b5563; }
QGraphicsView { background-color: #0f172a; border: 1px solid #374151; border-radius: 4px; }
QMenuBar { background-color: #111827; border-bottom: 1px solid #1f2937; color: #9ca3af; padding: 2px; }
QMenuBar::item:selected { background-color: #1f2937; color: #e2e8f0; }
QStatusBar { background-color: #111827; border-top: 1px solid #1f2937; color: #9ca3af; font-size: 12px; padding: 2px 8px; }
QScrollBar:vertical { background: #111827; width: 8px; border: none; }
QScrollBar::handle:vertical { background: #4b5563; border-radius: 4px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #6b7280; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QLabel#key_hint { color: #4b5563; font-size: 11px; }
QLabel#speed_value_label { color: #2dd4bf; font-size: 20px; font-weight: bold; }
QLabel#speed_label { color: #9ca3af; font-size: 12px; }
"""

# ==================== 通信协议 T 值 ====================
CMD = {
    "STOP": 115, "FORWARD": 116, "BACKWARD": 117,
    "LEFT": 118, "RIGHT": 119,
    "FWD_LEFT": 120, "FWD_RIGHT": 121,
    "BWD_LEFT": 122, "BWD_RIGHT": 123,
}

# 差速驱动: 每个方向对应的 (L_ratio, R_ratio)
# 正数 = 前进, 负数 = 后退, 比值乘 pwm 得到最终 L/R 值
DIR_MOTOR = {
    CMD["STOP"]:      (0, 0),
    CMD["FORWARD"]:   (0.9, 1.0),
    CMD["BACKWARD"]:  (-1.0, -1.0),
    CMD["LEFT"]:      (-0.5, 0.5),    # 原地左转
    CMD["RIGHT"]:     (0.5, -0.5),    # 原地右转
    CMD["FWD_LEFT"]:  (0.0, 1.0),     # 左前(左轮停右轮转,急转弯)
    CMD["FWD_RIGHT"]: (1.0, 0.0),     # 右前(右轮停左轮转)
    CMD["BWD_LEFT"]:  (-1.0, 0.0),    # 左后(左轮后退右轮停)
    CMD["BWD_RIGHT"]: (0.0, -1.0),    # 右后(右轮后退左轮停)
}

STATE_NAMES = {
    None: "停止", 115: "停止", 116: "前进中", 117: "后退中",
    118: "左转中", 119: "右转中", 120: "左上前进",
    121: "右上前进", 122: "左后后退", 123: "右后后退",
}


# ==================== 1. 视频分片接收 ====================
class VideoReceiveThread(QThread):
    new_frame_signal = pyqtSignal(QImage)
    fps_signal = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.running = True
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_socket.bind(('0.0.0.0', 8080))
        self.udp_socket.settimeout(1.0)
        self.frame_buffer = {}
        self.frame_count = 0
        self.last_fps_time = time.time()

    def run(self):
        print("电脑端 UDP 接收服务已启动，正在监听 8080 端口...")
        while self.running:
            try:
                data, addr = self.udp_socket.recvfrom(2048)
                if data.startswith(b"TEXT_TEST:"):
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

                        self.frame_count += 1
                        now = time.time()
                        if now - self.last_fps_time >= 1.0:
                            elapsed = now - self.last_fps_time
                            fps = int(self.frame_count / elapsed)
                            self.fps_signal.emit(fps)
                            self.frame_count = 0
                            self.last_fps_time = now

            except socket.timeout:
                continue
            except Exception as e:
                print(f"视频接收异常: {e}")
        self.udp_socket.close()
        print("UDP 接收线程已安全关闭。")


# ==================== 2. TCP 定位接收 ====================
class TcpReceiveThread(QThread):
    location_received_signal = pyqtSignal(dict)

    def __init__(self, tcp_socket):
        super().__init__()
        self.tcp_socket = tcp_socket
        self.running = True
        self.buffer = ""

    def run(self):
        print("TCP 定位数据接收服务已启动...")
        while self.running and self.tcp_socket:
            try:
                data = self.tcp_socket.recv(1024)
                if not data:
                    print("下位机断开了 TCP 连接。")
                    break
                self.buffer += data.decode('utf-8', errors='ignore')
                while "\n" in self.buffer:
                    line, self.buffer = self.buffer.split("\n", 1)
                    line = line.strip()
                    if line:
                        try:
                            data_dict = json.loads(line)
                            if data_dict.get("T") == 200:
                                print(f"定位: x={data_dict.get('x',0):.3f}, y={data_dict.get('y',0):.3f}")
                                self.location_received_signal.emit(data_dict)
                        except json.JSONDecodeError:
                            print(f"解析失败: {line}")
            except Exception as e:
                if self.running:
                    print(f"TCP 接收异常: {e}")
                break
        print("TCP 接收线程已关闭。")


# ==================== 3. 主界面 ====================
from main_window import Ui_MainWindow


class ControlWindow(QMainWindow, Ui_MainWindow):
    # 地图
    MAP_SIZE = 500       # 5m × 5m, 1m=100px
    SCALE_FACTOR = 100.0
    CENTER = MAP_SIZE / 2
    MAX_TRAIL_PX = 50    # 保留最近 50cm 轨迹

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("车辆遥控控制系统 — 监控中心")

        # ---- 网络 ----
        # self.TARGET_IP = "192.168.195.73"
        self.TARGET_IP = "127.0.0.1"
        self.TARGET_PORT = 8888
        self.tcp_socket = None
        self.tcp_thread = None

        # ---- 状态 ----
        self.current_cmd = None
        self.current_pwm = self.speedviewer.value()
        self.current_fps = 0

        # ---- 轨迹 ----
        self.trajectory_points = []
        self.trajectory_item = None

        # ---- 地图 ----
        self._init_map()

        # ---- 状态表格 ----
        self.state_model = QStandardItemModel()
        self.state_model.setHorizontalHeaderLabels(["参数", "数值"])
        self.state.setModel(self.state_model)
        self._update_state_table()

        # ---- 信号 ----
        self.speedviewer.valueChanged.connect(self.on_speed_changed)
        self.speed_value_label.setText(str(self.speedviewer.value()))

        # ---- 网络与线程 ----
        self.init_tcp_connection()
        self.video_thread = VideoReceiveThread()
        self.video_thread.new_frame_signal.connect(self.update_video_label)
        self.video_thread.fps_signal.connect(self.on_fps_updated)
        self.video_thread.start()
        self._bind_buttons()

    # ==================== 地图 ====================
    def _init_map(self):
        from PyQt5.QtWidgets import QGraphicsScene

        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, self.MAP_SIZE, self.MAP_SIZE)
        self.graphicsView.setScene(self.scene)
        self.graphicsView.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.graphicsView.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        bg = np.ones((self.MAP_SIZE, self.MAP_SIZE, 3), dtype=np.uint8) * 248

        # 细网格 10cm (10px)
        for i in range(0, self.MAP_SIZE + 1, 10):
            cv2.line(bg, (i, 0), (i, self.MAP_SIZE), (230, 230, 230), 1)
            cv2.line(bg, (0, i), (self.MAP_SIZE, i), (230, 230, 230), 1)

        # 粗网格 50cm (50px)
        for i in range(0, self.MAP_SIZE + 1, 50):
            cv2.line(bg, (i, 0), (i, self.MAP_SIZE), (190, 190, 190), 2)
            cv2.line(bg, (0, i), (self.MAP_SIZE, i), (190, 190, 190), 2)

        # 原点十字
        c = int(self.CENTER)
        cv2.line(bg, (c - 15, c), (c + 15, c), (255, 100, 100), 2)
        cv2.line(bg, (c, c - 15), (c, c + 15), (255, 100, 100), 2)

        # 轴标
        cv2.putText(bg, "+X", (self.MAP_SIZE - 35, c - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (100, 100, 150), 1)
        cv2.putText(bg, "+Y", (c + 5, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (100, 100, 150), 1)

        h, w, ch = bg.shape
        self.scene.addPixmap(QPixmap.fromImage(
            QImage(bg.data, w, h, ch * w, QImage.Format_RGB888).copy()))

        # 红点 (中心)
        pen = QPen(Qt.black, 1)
        brush = QBrush(QColor(255, 50, 50))
        self.car_dot = self.scene.addEllipse(0, 0, 14, 14, pen, brush)
        self.car_dot.setPos(self.CENTER - 7, self.CENTER - 7)
        self.car_dot.setZValue(2)

        self.car_center = self.scene.addEllipse(
            0, 0, 4, 4, QPen(Qt.NoPen), QBrush(QColor(255, 255, 255)))
        self.car_center.setPos(self.CENTER - 2, self.CENTER - 2)
        self.car_center.setZValue(2)

        self.graphicsView.fitInView(0, 0, self.MAP_SIZE, self.MAP_SIZE, Qt.KeepAspectRatio)

    # ==================== 轨迹 ====================
    def _update_trajectory(self, px, py):
        self.trajectory_points.append((px, py))

        # 从尾向前累加距离，超出 MAX_TRAIL_PX 则裁剪
        total = 0.0
        cut = 0
        for i in range(len(self.trajectory_points) - 1, 0, -1):
            dx = self.trajectory_points[i][0] - self.trajectory_points[i - 1][0]
            dy = self.trajectory_points[i][1] - self.trajectory_points[i - 1][1]
            total += math.hypot(dx, dy)
            if total > self.MAX_TRAIL_PX:
                cut = i
                break

        if cut > 0:
            self.trajectory_points = self.trajectory_points[cut:]

        # 重绘
        if self.trajectory_item is not None:
            self.scene.removeItem(self.trajectory_item)

        if len(self.trajectory_points) >= 2:
            path = QPainterPath()
            path.moveTo(self.trajectory_points[0][0], self.trajectory_points[0][1])
            for i in range(1, len(self.trajectory_points)):
                path.lineTo(self.trajectory_points[i][0], self.trajectory_points[i][1])
            self.trajectory_item = self.scene.addPath(path, QPen(QColor(255, 165, 0), 2.5))
            self.trajectory_item.setZValue(1)
        else:
            self.trajectory_item = None

    # ==================== 状态表格 ====================
    def _update_state_table(self):
        self.state_model.clear()
        self.state_model.setHorizontalHeaderLabels(["参数", "数值"])
        for param, value in [
            ("运行状态", STATE_NAMES.get(self.current_cmd, "停止")),
            ("当前速度", str(self.current_pwm)),
            ("视频帧率", f"{self.current_fps} FPS"),
        ]:
            ip = QStandardItem(param)
            ip.setEditable(False)
            iv = QStandardItem(value)
            iv.setEditable(False)
            iv.setTextAlignment(Qt.AlignCenter)
            self.state_model.appendRow([ip, iv])

        si = self.state_model.item(0, 1)
        if si:
            if self.current_cmd is None or self.current_cmd == CMD["STOP"]:
                si.setForeground(QColor("#9ca3af"))
            else:
                si.setForeground(QColor("#2dd4bf"))

    # ==================== 按钮 ====================
    def _bind_buttons(self):
        try:
            for name, cmd in [
                ("forward", "FORWARD"), ("back", "BACKWARD"),
                ("left", "LEFT"), ("right", "RIGHT"),
                ("stop", "STOP"),
                ("fwd_left", "FWD_LEFT"), ("fwd_right", "FWD_RIGHT"),
                ("bwd_left", "BWD_LEFT"), ("bwd_right", "BWD_RIGHT"),
            ]:
                btn = getattr(self, f"btn_{name}")
                btn.clicked.connect(lambda checked, t=CMD[cmd]: self.send_command(t))
        except AttributeError as e:
            print(f"UI: 按钮绑定失败: {e}")

    # ==================== 速度 ====================
    def on_speed_changed(self, value):
        self.current_pwm = value
        self.speed_value_label.setText(str(value))
        self._update_state_table()
        if self.current_cmd is not None and self.current_cmd != CMD["STOP"]:
            self._send_raw(self._make_motor_cmd(self.current_cmd))

    # ==================== 指令 ====================
    def _make_motor_cmd(self, direction):
        """根据方向和当前速度计算 L/R 轮速"""
        if direction is None or direction == CMD["STOP"]:
            return {"T": 11, "L": 0, "R": 0}
        lr, rr = DIR_MOTOR[direction]
        l = max(-255, min(255, int(lr * self.current_pwm)))
        r = max(-255, min(255, int(rr * self.current_pwm)))
        return {"T": 11, "L": l, "R": r}

    def send_command(self, t_value):
        self.current_cmd = None if t_value == CMD["STOP"] else t_value
        self._send_raw(self._make_motor_cmd(self.current_cmd))
        if t_value == CMD["STOP"]:
            self._send_raw({"T": 115})       # 补发专用停止指令，双重保险
        self._update_state_table()

    def _send_raw(self, cmd_dict):
        if self.tcp_socket is None:
            self.init_tcp_connection()
            if self.tcp_socket is None:
                return
        try:
            self.tcp_socket.sendall((json.dumps(cmd_dict) + "\n").encode('utf-8'))
            print(f"已发送: {cmd_dict}")
        except Exception as e:
            print(f"发送异常: {e}")
            self.cleanup_tcp()

    def on_fps_updated(self, fps):
        self.current_fps = fps
        self._update_state_table()

    # ==================== TCP ====================
    def init_tcp_connection(self):
        try:
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.settimeout(2.0)
            print(f"连接下位机 TCP [{self.TARGET_IP}:{self.TARGET_PORT}]...")
            self.tcp_socket.connect((self.TARGET_IP, self.TARGET_PORT))
            print("连接成功！")
            self.tcp_socket.settimeout(None)
            self.tcp_thread = TcpReceiveThread(self.tcp_socket)
            self.tcp_thread.location_received_signal.connect(self.handle_incoming_location)
            self.tcp_thread.start()
        except Exception as e:
            print(f"TCP 连接失败: {e}")
            self.tcp_socket = None

    # ==================== 定位 ====================
    def handle_incoming_location(self, data):
        x = data.get("x", 0.0)
        y = data.get("y", 0.0)
        valid = data.get("valid", False)
        ts = data.get("t", 0)

        self.statusbar.showMessage(
            f"车辆位置: X={x:.3f}m  Y={y:.3f}m  有效性: {valid}  时间戳: {ts}")

        if valid:
            px = self.CENTER + x * self.SCALE_FACTOR
            py = self.CENTER - y * self.SCALE_FACTOR
            px = max(0.0, min(self.MAP_SIZE, px))
            py = max(0.0, min(self.MAP_SIZE, py))

            self.car_dot.setPos(px - 7, py - 7)
            self.car_center.setPos(px - 2, py - 2)
            self._update_trajectory(px, py)

    # ==================== 视频 ====================
    def update_video_label(self, q_img):
        pixmap = QPixmap.fromImage(q_img)
        scaled = pixmap.scaled(self.video_window.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.video_window.setPixmap(scaled)

    # ==================== 键盘 ====================
    def keyPressEvent(self, event: QKeyEvent):
        k = event.key()

        m = {
            Qt.Key_W: CMD["FORWARD"], Qt.Key_X: CMD["BACKWARD"],
            Qt.Key_A: CMD["LEFT"], Qt.Key_D: CMD["RIGHT"],
            Qt.Key_Q: CMD["FWD_LEFT"], Qt.Key_E: CMD["FWD_RIGHT"],
            Qt.Key_Z: CMD["BWD_LEFT"], Qt.Key_C: CMD["BWD_RIGHT"],
            Qt.Key_S: CMD["STOP"], Qt.Key_Space: CMD["STOP"],
        }
        if k in m:
            self.send_command(m[k])
            return

        if k == Qt.Key_Up:
            self.speedviewer.setValue(min(200, self.speedviewer.value() + 10))
            return
        if k == Qt.Key_Down:
            self.speedviewer.setValue(max(0, self.speedviewer.value() - 10))
            return

        if k == Qt.Key_Escape:
            self.close()

    # ==================== 窗口缩放 ====================
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.graphicsView.fitInView(0, 0, self.MAP_SIZE, self.MAP_SIZE, Qt.KeepAspectRatio)

    # ==================== 清理 ====================
    def cleanup_tcp(self):
        if self.tcp_thread:
            self.tcp_thread.running = False
            self.tcp_thread.wait()
            self.tcp_thread = None
        if self.tcp_socket:
            try:
                self.tcp_socket.close()
            except Exception:
                pass
            self.tcp_socket = None

    def closeEvent(self, event):
        self.video_thread.running = False
        self.video_thread.wait()
        self.cleanup_tcp()
        event.accept()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)
    app.setStyleSheet(TEAL_STYLE)
    window = ControlWindow()
    window.show()
    sys.exit(app.exec_())
