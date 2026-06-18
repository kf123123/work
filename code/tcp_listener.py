"""
TCP 指令监听器 — 模拟下位机接收端
在本地起一个 TCP 服务端，打印收到的控制指令，
用来验证上位机按键/按钮是否能正确发送。

用法：
  1. 先运行本监听器：
     python tcp_listener.py
  2. 修改 main.py 中 TARGET_IP 为 "127.0.0.1"
  3. 再运行 main.py：
     python main.py
  4. 按键盘或点按钮，观察本窗口打印的 JSON
"""

import socket
import threading
import time

HOST = "0.0.0.0"
PORT = 8888


def handle_client(conn, addr):
    print(f"[连接] 上位机已连接: {addr}")
    buffer = ""
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            buffer += data.decode("utf-8", errors="ignore")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if line:
                    print(f"[收到指令] {line}")
    except ConnectionResetError:
        pass
    finally:
        print(f"[断开] {addr}")
        conn.close()


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(1)
    print(f"TCP 监听器已启动: {HOST}:{PORT}")
    print("等待上位机连接...")
    print("=" * 40)

    while True:
        conn, addr = server.accept()
        t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
        t.start()


if __name__ == "__main__":
    main()
