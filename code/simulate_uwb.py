"""
UWB 定位模拟器 — 模拟下位机发送车辆位置数据
用来测试上位机的定位地图、红点移动和轨迹绘制。

用法：
  1. 先运行本模拟器 (默认端口 8888)：
     python simulate_uwb.py
  2. 再运行上位机（确保 TARGET_IP=127.0.0.1）：
     python main.py
  3. 观察地图上红点移动和橙色轨迹

可选参数：
  python simulate_uwb.py --pattern circle    # 圆形 (默认)
  python simulate_uwb.py --pattern square    # 方形
  python simulate_uwb.py --pattern eight     # 8字形
  python simulate_uwb.py --speed 2.0         # 移动速度 (m/s)
"""

import socket
import json
import time
import math
import sys
import argparse

HOST = "0.0.0.0"
PORT = 8888


def generate_circle(t, speed):
    """ 半径 1.5m 的圆, 1周/5秒 """
    r = 1.5
    omega = 2 * math.pi / 5.0  # 5秒一圈
    x = r * math.cos(omega * t)
    y = r * math.sin(omega * t)
    return x, y


def generate_square(t, speed):
    """ 1.5m 方形路径 """
    period = 8.0
    tt = t % period / period  # 0→1
    s = 1.5
    if tt < 0.25:
        x = 4 * tt * s
        y = 0
    elif tt < 0.5:
        x = s
        y = 4 * (tt - 0.25) * s
    elif tt < 0.75:
        x = s - 4 * (tt - 0.5) * s
        y = s
    else:
        x = 0
        y = s - 4 * (tt - 0.75) * s
    return x - s / 2, y - s / 2


def generate_eight(t, speed):
    """ 8字形 ∞ """
    r = 1.2
    omega = 2 * math.pi / 6.0
    x = r * math.sin(omega * t)
    y = r * math.sin(2 * omega * t) / 2
    return x, y


PATTERNS = {
    "circle": generate_circle,
    "square": generate_square,
    "eight": generate_eight,
}


def main():
    parser = argparse.ArgumentParser(description="UWB 定位模拟器")
    parser.add_argument("--pattern", choices=PATTERNS.keys(), default="circle")
    parser.add_argument("--speed", type=float, default=1.0, help="速度倍率")
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()

    gen = PATTERNS[args.pattern]

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, args.port))
    server.listen(1)
    print(f"UWB 模拟器已启动 [{args.pattern}] @ {HOST}:{args.port}")
    print(f"速度倍率: {args.speed}x")
    print("等待上位机连接...\n")

    conn, addr = server.accept()
    print(f"上位机已连接: {addr}\n")

    t0 = time.time()
    t = 0.0
    try:
        while True:
            x, y = gen(t, args.speed)

            data = {
                "T": 200,
                "x": round(x, 4),
                "y": round(y, 4),
                "valid": True,
                "t": int(time.time() * 1000),
            }
            conn.sendall((json.dumps(data) + "\n").encode("utf-8"))

            info = f"\r发送 → x={x:+.3f}m  y={y:+.3f}m  [{args.pattern}]"
            print(info, end="", flush=True)

            time.sleep(0.05)
            t += 0.05 * args.speed

    except (BrokenPipeError, ConnectionResetError, KeyboardInterrupt):
        print("\n\n已断开")
    finally:
        conn.close()
        server.close()


if __name__ == "__main__":
    main()
