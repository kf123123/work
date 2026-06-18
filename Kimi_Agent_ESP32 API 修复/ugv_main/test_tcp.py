#!/usr/bin/env python3
"""
UGV TCP 控制脚本 + UWB 数据接收
用法: python test_tcp.py

功能：
  - 发送电机控制命令（前进/后退/左转/右转/停止）
  - 接收 UWB 定位数据（自动定时推送或主动查询）
  - 手动键盘控制
"""

import socket
import json
import time
import sys
import threading

ESP32_IP = "192.168.4.1"
ESP32_PORT = 8888

# 全局状态
uwb_data = {"x": 0.0, "y": 0.0, "valid": False}
receive_thread_running = False


def send_cmd(sock, T, **kwargs):
    """发送 JSON 命令"""
    cmd = {"T": T, **kwargs}
    data = json.dumps(cmd) + "\n"
    try:
        sock.send(data.encode())
        print(f"  SEND: {json.dumps(cmd)}")
    except Exception as e:
        print(f"  SEND ERROR: {e}")
    time.sleep(0.05)


def receive_loop(sock):
    """后台线程：持续接收 TCP 数据（UWB 遥测等）"""
    global uwb_data, receive_thread_running
    receive_thread_running = True
    while receive_thread_running:
        try:
            data = sock.recv(1024).decode().strip()
            if not data:
                continue
            # 处理可能的多条 JSON（以换行分隔）
            for line in data.split('\n'):
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                    # UWB 数据消息 T=200
                    if msg.get("T") == 200:
                        uwb_data["x"] = msg.get("x", 0.0)
                        uwb_data["y"] = msg.get("y", 0.0)
                        uwb_data["valid"] = msg.get("valid", False)
                        uwb_data["t"] = msg.get("t", 0)
                        print(f"\r  [UWB] x={uwb_data['x']:.3f} y={uwb_data['y']:.3f} valid={uwb_data['valid']}  ", end="", flush=True)
                    # UWB 自动推送开关确认 T=201
                    elif msg.get("T") == 201:
                        print(f"\n  [UWB] Auto push: {'ON' if msg.get('en') else 'OFF'}")
                    # 其他消息
                    elif "msg" in msg:
                        print(f"\n  [MSG] {msg['msg']}")
                    else:
                        print(f"\n  [RECV] {line}")
                except json.JSONDecodeError:
                    print(f"\n  [RECV] {line}")
        except socket.timeout:
            continue
        except Exception as e:
            if receive_thread_running:
                print(f"\n  [RECV ERROR] {e}")
            break


def test_sequence(sock):
    """自动测试序列"""
    print("\n=== 测试序列开始 ===\n")

    print("[1/8] 前进 pwm=150")
    send_cmd(sock, 116, pwm=150)
    time.sleep(2)

    print("[2/8] 停止")
    send_cmd(sock, 115)
    time.sleep(1)

    print("[3/8] 后退 pwm=150")
    send_cmd(sock, 117, pwm=150)
    time.sleep(2)

    print("[4/8] 停止")
    send_cmd(sock, 115)
    time.sleep(1)

    print("[5/8] 原地左转 pwm=150")
    send_cmd(sock, 118, pwm=150)
    time.sleep(2)

    print("[6/8] 停止")
    send_cmd(sock, 115)
    time.sleep(1)

    print("[7/8] 查询 UWB 数据")
    send_cmd(sock, 200)
    time.sleep(1)

    print("[8/8] 停止")
    send_cmd(sock, 115)

    print("\n=== 测试完成 ===")


def manual_control(sock):
    """手动键盘控制 + UWB 数据显示"""
    print("\n=== 手动控制模式 ===")
    print("  W/S - 前进/后退")
    print("  A/D - 左转/右转")
    print("  Q   - 停止")
    print("  U   - 查询 UWB 数据")
    print("  P   - 切换 UWB 自动推送")
    print("  X   - 退出")
    print("====================\n")

    pwm = 150
    while True:
        try:
            key = input("按键: ").strip().lower()
            if key == 'w':
                send_cmd(sock, 116, pwm=pwm)
            elif key == 's':
                send_cmd(sock, 117, pwm=pwm)
            elif key == 'a':
                send_cmd(sock, 118, pwm=pwm)
            elif key == 'd':
                send_cmd(sock, 119, pwm=pwm)
            elif key == 'q':
                send_cmd(sock, 115)
            elif key == 'u':
                send_cmd(sock, 200)
            elif key == 'p':
                send_cmd(sock, 201, en=-1)  # 切换
            elif key == 'x':
                send_cmd(sock, 115)
                break
            else:
                print("  未知按键")
        except KeyboardInterrupt:
            send_cmd(sock, 115)
            break


def main():
    global receive_thread_running

    print(f"Connecting to {ESP32_IP}:{ESP32_PORT}...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.0)  # 1秒超时用于接收线程
        sock.connect((ESP32_IP, ESP32_PORT))
        print("Connected!")

        # 接收欢迎消息
        try:
            welcome = sock.recv(1024).decode()
            print(f"ESP32: {welcome.strip()}")
        except:
            pass

    except Exception as e:
        print(f"Connection failed: {e}")
        print("请检查:")
        print("  1. 电脑是否连接了 UGV_Car WiFi 热点")
        print("  2. ESP32 是否已烧录程序并启动")
        sys.exit(1)

    # 启动接收线程
    recv_thread = threading.Thread(target=receive_loop, args=(sock,), daemon=True)
    recv_thread.start()

    print("\n选择模式:")
    print("  1 - 自动测试序列")
    print("  2 - 手动键盘控制")
    choice = input("输入 1 或 2: ").strip()

    if choice == '1':
        test_sequence(sock)
    elif choice == '2':
        manual_control(sock)
    else:
        print("无效选择")

    # 清理
    receive_thread_running = False
    send_cmd(sock, 115)
    time.sleep(0.5)
    sock.close()
    print("\nDisconnected")


if __name__ == "__main__":
    main()
