"""
UWB 交互式模拟器 — 模拟下位机（ESP32）接收控制指令并回传定位数据

上位机发控制指令 → 模拟器接收 → 差速运动仿真 → 回传 UWB 定位数据 → 上位机地图显示

用法：
  1. 运行本模拟器:
     python uwb_simulator.py

  2. 修改 main.py 中 TARGET_IP 为 "127.0.0.1"

  3. 运行上位机:
     python main.py

  4. 按 WASD 控制，观察地图红点移动

可选参数:
  python uwb_simulator.py --port 8888      # TCP 端口
  python uwb_simulator.py --rate 20        # 推送频率 (Hz)
  python uwb_simulator.py --no-noise       # 关闭噪声（调试用）
  python uwb_simulator.py --paused         # 启动时暂停（等待手动发指令）
"""

import socket
import json
import time
import math
import random
import threading
import argparse
import sys

# ============ 车辆参数（与 drive_sim.py 一致）============
WHEEL_BASE = 0.30          # 轮距 (m)
MAX_SPEED = 0.6            # PWM=200 最大线速度 (m/s)
PWM_TO_SPEED = MAX_SPEED / 200.0
DT = 0.05                  # 仿真步长 (s)

# ============ 指令定义 ============
CMD = {
    "STOP": 115, "FORWARD": 116, "BACKWARD": 117,
    "LEFT": 118, "RIGHT": 119,
    "FWD_LEFT": 120, "FWD_RIGHT": 121,
    "BWD_LEFT": 122, "BWD_RIGHT": 123,
}

DIR_MOTOR = {
    CMD["STOP"]:      (0, 0),
    CMD["FORWARD"]:   (1.0, 1.0),
    CMD["BACKWARD"]:  (-1.0, -1.0),
    CMD["LEFT"]:      (-1.0, 1.0),
    CMD["RIGHT"]:     (1.0, -1.0),
    CMD["FWD_LEFT"]:  (0.0, 1.0),
    CMD["FWD_RIGHT"]: (1.0, 0.0),
    CMD["BWD_LEFT"]:  (-1.0, 0.0),
    CMD["BWD_RIGHT"]: (0.0, -1.0),
}

CMD_NAMES = {v: k for k, v in CMD.items()}

# ============ 状态 ============
class CarState:
    """共享车辆状态，线程安全"""
    def __init__(self):
        self.lock = threading.Lock()
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.L = 0      # 左轮 PWM (-255 ~ 255)
        self.R = 0      # 右轮 PWM (-255 ~ 255)
        self.push_enabled = True
        self.last_cmd_desc = "等待指令..."

    def set_motors(self, L, R, desc=""):
        with self.lock:
            self.L = L
            self.R = R
            if desc:
                self.last_cmd_desc = desc

    def set_push(self, enabled):
        with self.lock:
            self.push_enabled = enabled

    def get_state(self):
        with self.lock:
            return self.L, self.R, self.push_enabled


# ============ TCP 命令接收 ============
def clamp_pwm(val):
    return max(-255, min(255, int(val)))


def describe_cmd(cmd_dict):
    """生成指令的人类可读描述"""
    t = cmd_dict.get("T")

    if t == 11:
        L = cmd_dict.get("L", 0)
        R = cmd_dict.get("R", 0)
        # 尝试推断方向
        if L == 0 and R == 0:
            return f"T=11  L={L:<4} R={R:<4}  →  停止"
        if L > 0 and R > 0:
            if abs(L - R) <= 2:
                return f"T=11  L={L:<4} R={R:<4}  →  前进 PWM≈{max(L,R)}"
            return f"T=11  L={L:<4} R={R:<4}  →  前进(偏右)" if L > R \
                else f"T=11  L={L:<4} R={R:<4}  →  前进(偏左)"
        if L < 0 and R < 0:
            return f"T=11  L={L:<4} R={R:<4}  →  后退 PWM≈{max(abs(L),abs(R))}"
        if L < 0 and R > 0:
            return f"T=11  L={L:<4} R={R:<4}  →  原地左转"
        if L > 0 and R < 0:
            return f"T=11  L={L:<4} R={R:<4}  →  原地右转"
        if L == 0 and R > 0:
            return f"T=11  L={L:<4} R={R:<4}  →  左前(急转)"
        if L > 0 and R == 0:
            return f"T=11  L={L:<4} R={R:<4}  →  右前(急转)"
        if L == 0 and R < 0:
            return f"T=11  L={L:<4} R={R:<4}  →  右后"
        if L < 0 and R == 0:
            return f"T=11  L={L:<4} R={R:<4}  →  左后"
        return f"T=11  L={L:<4} R={R:<4}"

    if t in CMD_NAMES:
        pwm = cmd_dict.get("pwm", 0)
        return f"T={t:<3} PWM={pwm:<3}  →  {CMD_NAMES[t]}"

    if t == 200:
        return "T=200 →  位置查询"

    if t == 201:
        en = cmd_dict.get("en", 0)
        return f"T=201 →  自动推送: {'开启' if en else '关闭'}"

    if t == 999:
        return "T=999 →  心跳"

    return f"T={t} →  未知指令"


def command_receiver(conn, state):
    """独立线程：从 TCP 连接读取并解析指令"""
    buffer = ""
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                print("\n[断开] 上位机已断开连接。")
                break
            buffer += data.decode("utf-8", errors="ignore")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue
                try:
                    cmd = json.loads(line)
                    handle_command(cmd, state, conn)
                except json.JSONDecodeError:
                    print(f"[解析失败] {line}")
    except (ConnectionResetError, BrokenPipeError, OSError):
        print("\n[断开] 上位机连接异常断开。")
    return


def handle_command(cmd, state, conn):
    """处理一条控制指令"""
    t = cmd.get("T")
    desc = describe_cmd(cmd)
    print(f"[指令] {desc}")

    if t == 11:
        L = clamp_pwm(cmd.get("L", 0))
        R = clamp_pwm(cmd.get("R", 0))
        state.set_motors(L, R, desc)

    elif t in (115, 116, 117, 118, 119, 120, 121, 122, 123):
        # 方向指令 → 转换为 L/R PWM
        pwm_val = clamp_pwm(cmd.get("pwm", 0))
        lr, rr = DIR_MOTOR[t]
        L = clamp_pwm(lr * pwm_val)
        R = clamp_pwm(rr * pwm_val)
        state.set_motors(L, R, desc)

    elif t == 200:
        # 位置查询：立即回复
        with state.lock:
            resp = {
                "T": 200,
                "x": round(state.x, 4),
                "y": round(state.y, 4),
                "valid": True,
                "t": int(time.time() * 1000),
            }
        try:
            conn.sendall((json.dumps(resp) + "\n").encode("utf-8"))
        except Exception:
            pass

    elif t == 201:
        state.set_push(cmd.get("en", 0) != 0)

    elif t == 999:
        pass  # 心跳，不处理

    else:
        print(f"[忽略] 不支持的指令 T={t}")


# ============ 运动仿真 ============
def simulate_step(state, noise=True):
    """基于当前 L/R 执行一步差速仿真"""
    L, R, _ = state.get_state()

    moving = (L != 0 or R != 0)

    v_l = L * PWM_TO_SPEED
    v_r = R * PWM_TO_SPEED

    if noise and moving:
        v_l *= random.gauss(1.0, 0.05)
        v_r *= random.gauss(1.0, 0.05)

    v = (v_l + v_r) / 2.0
    omega = (v_r - v_l) / WHEEL_BASE

    with state.lock:
        dtheta = omega * DT
        if noise and moving:
            dtheta += random.gauss(0, 0.002)
        state.theta += dtheta

        dx = v * math.cos(state.theta) * DT
        dy = v * math.sin(state.theta) * DT
        if noise and moving:
            dx += random.gauss(0, 0.005)
            dy += random.gauss(0, 0.005)

        state.x += dx
        state.y += dy
        state.x = round(state.x, 4)
        state.y = round(state.y, 4)


# ============ 主程序 ============
def main():
    parser = argparse.ArgumentParser(description="UWB 交互式模拟器")
    parser.add_argument("--port", type=int, default=8888, help="TCP 端口")
    parser.add_argument("--rate", type=float, default=20, help="推送频率 (Hz)")
    parser.add_argument("--no-noise", action="store_true", help="关闭噪声")
    parser.add_argument("--paused", action="store_true", help="启动时暂停")
    args = parser.parse_args()

    state = CarState()
    noise = not args.no_noise

    # 启动 TCP 服务端
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", args.port))
    server.listen(1)
    print("=" * 50)
    print("UWB 交互式模拟器 v1.0")
    print(f"监听端口: {args.port}")
    print(f"推送频率: {args.rate} Hz")
    print(f"噪声: {'关闭' if args.no_noise else '开启'}")
    print(f"状态: {'已暂停(等待控制)' if args.paused else '运行中'}")
    print("=" * 50)
    print("等待上位机连接...\n")

    conn, addr = server.accept()
    print(f"上位机已连接: {addr}\n")

    # 启动命令接收线程
    recv_thread = threading.Thread(
        target=command_receiver, args=(conn, state), daemon=True)
    recv_thread.start()

    # 如果在暂停状态，等待用户按回车开始
    if args.paused:
        input("按 Enter 开始模拟...\n")

    dt_sim = 1.0 / args.rate
    t0 = time.time()
    frame_count = 0

    try:
        while True:
            cycle_start = time.time()

            # 仿真步
            simulate_step(state, noise)

            # 发送定位数据
            _, _, push_enabled = state.get_state()
            if push_enabled:
                with state.lock:
                    data = {
                        "T": 200,
                        "x": round(state.x, 4),
                        "y": round(state.y, 4),
                        "valid": True,
                        "t": int(time.time() * 1000),
                    }
                try:
                    conn.sendall((json.dumps(data) + "\n").encode("utf-8"))
                except (BrokenPipeError, ConnectionResetError, OSError):
                    print("\n[错误] 上位机连接断开，停止发送。")
                    break

            # 状态日志（每秒一次）
            frame_count += 1
            elapsed = time.time() - t0
            if elapsed >= 1.0:
                with state.lock:
                    print(
                        f"\r[定位] x={state.x:+.3f}m  y={state.y:+.3f}m  "
                        f"θ={math.degrees(state.theta) % 360:.0f}°  "
                        f"速度={abs(state.L + state.R) / 2 * PWM_TO_SPEED:.2f}m/s  "
                        f"| {state.last_cmd_desc:<30}",
                        end="", flush=True
                    )
                t0 = time.time()
                frame_count = 0

            # 精确计时
            elapsed = time.time() - cycle_start
            sleep_time = dt_sim - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\n\n[退出] 用户中断")
    finally:
        conn.close()
        server.close()
        print("模拟器已关闭。")


if __name__ == "__main__":
    main()
