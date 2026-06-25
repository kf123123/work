# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'main_window.ui'
# Manual redesign: professional industrial monitoring layout

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1254, 800)
        MainWindow.setMinimumSize(1100, 700)

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        # ============ Main horizontal layout ============
        self.main_layout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.main_layout.setContentsMargins(16, 16, 16, 16)
        self.main_layout.setSpacing(16)

        # ================== LEFT PANEL ==================
        self.left_panel = QtWidgets.QWidget()
        self.left_panel.setObjectName("left_panel")
        self.left_layout = QtWidgets.QVBoxLayout(self.left_panel)
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        self.left_layout.setSpacing(12)

        # --- Video feed group ---
        self.video_group = QtWidgets.QGroupBox(self.left_panel)
        self.video_group.setObjectName("video_group")
        self.video_group.setTitle("  ■ 视频画面  ")
        self.video_group.setMinimumSize(640, 480)
        video_layout = QtWidgets.QVBoxLayout(self.video_group)
        video_layout.setContentsMargins(2, 8, 2, 2)

        self.video_window = QtWidgets.QLabel(self.video_group)
        self.video_window.setObjectName("video_window")
        self.video_window.setMinimumSize(636, 440)
        self.video_window.setFixedHeight(440)
        self.video_window.setAlignment(QtCore.Qt.AlignCenter)
        self.video_window.setScaledContents(True)
        video_layout.addWidget(self.video_window)

        self.left_layout.addWidget(self.video_group)

        # --- Control group (8-direction D-pad) ---
        self.control_group = QtWidgets.QGroupBox(self.left_panel)
        self.control_group.setObjectName("control_group")
        self.control_group.setTitle("  ■ 车辆控制  ")
        control_layout = QtWidgets.QHBoxLayout(self.control_group)
        control_layout.setContentsMargins(24, 12, 24, 12)
        control_layout.setSpacing(30)

        # D-pad 3x3 grid
        self.dpad_widget = QtWidgets.QWidget(self.control_group)
        self.dpad_widget.setObjectName("dpad_widget")
        self.dpad_widget.setFixedSize(260, 180)
        dpad_grid = QtWidgets.QGridLayout(self.dpad_widget)
        dpad_grid.setContentsMargins(0, 0, 0, 0)
        dpad_grid.setSpacing(4)

        # Diagonals
        self.btn_fwd_left = QtWidgets.QPushButton(self.dpad_widget)
        self.btn_fwd_left.setObjectName("btn_fwd_left")
        self.btn_fwd_left.setMinimumSize(68, 44)
        dpad_grid.addWidget(self.btn_fwd_left, 0, 0, 1, 1,
                            alignment=QtCore.Qt.AlignCenter)

        self.btn_forward = QtWidgets.QPushButton(self.dpad_widget)
        self.btn_forward.setObjectName("btn_forward")
        self.btn_forward.setMinimumSize(68, 44)
        dpad_grid.addWidget(self.btn_forward, 0, 1, 1, 1,
                            alignment=QtCore.Qt.AlignCenter)

        self.btn_fwd_right = QtWidgets.QPushButton(self.dpad_widget)
        self.btn_fwd_right.setObjectName("btn_fwd_right")
        self.btn_fwd_right.setMinimumSize(68, 44)
        dpad_grid.addWidget(self.btn_fwd_right, 0, 2, 1, 1,
                            alignment=QtCore.Qt.AlignCenter)

        # Middle row
        self.btn_left = QtWidgets.QPushButton(self.dpad_widget)
        self.btn_left.setObjectName("btn_left")
        self.btn_left.setMinimumSize(68, 44)
        dpad_grid.addWidget(self.btn_left, 1, 0, 1, 1,
                            alignment=QtCore.Qt.AlignCenter)

        self.btn_stop = QtWidgets.QPushButton(self.dpad_widget)
        self.btn_stop.setObjectName("btn_stop")
        self.btn_stop.setMinimumSize(68, 44)
        dpad_grid.addWidget(self.btn_stop, 1, 1, 1, 1,
                            alignment=QtCore.Qt.AlignCenter)

        self.btn_right = QtWidgets.QPushButton(self.dpad_widget)
        self.btn_right.setObjectName("btn_right")
        self.btn_right.setMinimumSize(68, 44)
        dpad_grid.addWidget(self.btn_right, 1, 2, 1, 1,
                            alignment=QtCore.Qt.AlignCenter)

        # Bottom row
        self.btn_bwd_left = QtWidgets.QPushButton(self.dpad_widget)
        self.btn_bwd_left.setObjectName("btn_bwd_left")
        self.btn_bwd_left.setMinimumSize(68, 44)
        dpad_grid.addWidget(self.btn_bwd_left, 2, 0, 1, 1,
                            alignment=QtCore.Qt.AlignCenter)

        self.btn_back = QtWidgets.QPushButton(self.dpad_widget)
        self.btn_back.setObjectName("btn_back")
        self.btn_back.setMinimumSize(68, 44)
        dpad_grid.addWidget(self.btn_back, 2, 1, 1, 1,
                            alignment=QtCore.Qt.AlignCenter)

        self.btn_bwd_right = QtWidgets.QPushButton(self.dpad_widget)
        self.btn_bwd_right.setObjectName("btn_bwd_right")
        self.btn_bwd_right.setMinimumSize(68, 44)
        dpad_grid.addWidget(self.btn_bwd_right, 2, 2, 1, 1,
                            alignment=QtCore.Qt.AlignCenter)

        control_layout.addWidget(self.dpad_widget)

        # Separator
        separator = QtWidgets.QFrame(self.control_group)
        separator.setFrameShape(QtWidgets.QFrame.VLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        separator.setObjectName("ctrl_separator")
        separator.setStyleSheet("border: none; border-left: 1px solid #334155;")
        control_layout.addWidget(separator)

        # Speed slider area
        self.speed_widget = QtWidgets.QWidget(self.control_group)
        self.speed_widget.setObjectName("speed_widget")
        speed_vbox = QtWidgets.QVBoxLayout(self.speed_widget)
        speed_vbox.setContentsMargins(0, 0, 0, 0)
        speed_vbox.setAlignment(QtCore.Qt.AlignCenter)

        self.speed_label = QtWidgets.QLabel(self.speed_widget)
        self.speed_label.setObjectName("speed_label")
        self.speed_label.setAlignment(QtCore.Qt.AlignCenter)
        speed_vbox.addWidget(self.speed_label)

        self.speedviewer = QtWidgets.QSlider(self.speed_widget)
        self.speedviewer.setObjectName("speedviewer")
        self.speedviewer.setMaximum(200)
        self.speedviewer.setValue(150)
        self.speedviewer.setOrientation(QtCore.Qt.Vertical)
        self.speedviewer.setTickPosition(QtWidgets.QSlider.TicksRight)
        self.speedviewer.setTickInterval(25)
        self.speedviewer.setFixedSize(32, 120)
        speed_vbox.addWidget(self.speedviewer, 0, QtCore.Qt.AlignCenter)

        self.speed_value_label = QtWidgets.QLabel(self.speed_widget)
        self.speed_value_label.setObjectName("speed_value_label")
        self.speed_value_label.setAlignment(QtCore.Qt.AlignCenter)
        speed_vbox.addWidget(self.speed_value_label)

        # Keyboard hint
        self.key_hint = QtWidgets.QLabel(self.speed_widget)
        self.key_hint.setObjectName("key_hint")
        self.key_hint.setAlignment(QtCore.Qt.AlignCenter)
        speed_vbox.addWidget(self.key_hint)

        control_layout.addWidget(self.speed_widget)

        self.left_layout.addWidget(self.control_group)

        # Add left panel to main layout (stretch 7 = ~70% width)
        self.main_layout.addWidget(self.left_panel, 7)

        # ================== RIGHT PANEL ==================
        self.right_panel = QtWidgets.QWidget()
        self.right_panel.setObjectName("right_panel")
        self.right_layout = QtWidgets.QVBoxLayout(self.right_panel)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.setSpacing(12)

        # --- Status table group ---
        self.status_group = QtWidgets.QGroupBox(self.right_panel)
        self.status_group.setObjectName("status_group")
        self.status_group.setTitle("  ■ 车辆状态  ")
        status_layout = QtWidgets.QVBoxLayout(self.status_group)
        status_layout.setContentsMargins(4, 8, 4, 4)

        self.state = QtWidgets.QTableView(self.status_group)
        self.state.setObjectName("state")
        self.state.setAlternatingRowColors(True)
        self.state.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.state.horizontalHeader().setStretchLastSection(True)
        self.state.verticalHeader().setVisible(False)
        self.state.setShowGrid(False)
        status_layout.addWidget(self.state)

        self.right_layout.addWidget(self.status_group)

        # --- Map group ---
        self.map_group = QtWidgets.QGroupBox(self.right_panel)
        self.map_group.setObjectName("map_group")
        self.map_group.setTitle("  ■ 定位地图  ")
        map_layout = QtWidgets.QVBoxLayout(self.map_group)
        map_layout.setContentsMargins(4, 8, 4, 4)

        self.graphicsView = QtWidgets.QGraphicsView(self.map_group)
        self.graphicsView.setObjectName("graphicsView")
        self.graphicsView.setMinimumSize(340, 260)
        map_layout.addWidget(self.graphicsView)

        self.right_layout.addWidget(self.map_group)

        self.main_layout.addWidget(self.right_panel, 3)

        # ============ Menu & Status ============
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1254, 22))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "车辆遥控控制系统 — 监控中心"))
        self.video_window.setText(_translate("MainWindow", "等待视频连接..."))
        self.btn_fwd_left.setText(_translate("MainWindow", "↖ 左上"))
        self.btn_forward.setText(_translate("MainWindow", "↑ 前进"))
        self.btn_fwd_right.setText(_translate("MainWindow", "↗ 右上"))
        self.btn_left.setText(_translate("MainWindow", "← 左转"))
        self.btn_stop.setText(_translate("MainWindow", "■ 停止"))
        self.btn_right.setText(_translate("MainWindow", "→ 右转"))
        self.btn_bwd_left.setText(_translate("MainWindow", "↙ 左下"))
        self.btn_back.setText(_translate("MainWindow", "↓ 后退"))
        self.btn_bwd_right.setText(_translate("MainWindow", "↘ 右下"))
        self.speed_label.setText(_translate("MainWindow", "速度"))
        self.speed_value_label.setText(_translate("MainWindow", "150"))
        self.key_hint.setText(_translate("MainWindow", "W A S D / X / 空格 / Q E Z C"))
