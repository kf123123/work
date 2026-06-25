"""
车辆运动仿真脚本 — 根据控制指令模拟行驶轨迹，绘入栅格地图
用法：
  python drive_sim.py               # 预设测试路径
"""

import math
import random
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Arc

# ============ 车辆参数 ============
WHEEL_BASE = 0.30          # 轮距 (m)
MAX_SPEED = 0.6            # PWM=200 最大线速度 (m/s)
PWM_TO_SPEED = MAX_SPEED / 200.0
DT = 0.05                  # 仿真步长 (s)

# ============ 指令定义（与上位机一致）============
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

# ============ 预设测试路径 ============
# (T值, PWM, 持续秒数)
TEST_SEQUENCES = {
    "square": [
        (CMD["FORWARD"],  150, 2.0),
        (CMD["LEFT"],     150, 1.0),
        (CMD["FORWARD"],  150, 2.0),
        (CMD["LEFT"],     150, 1.0),
        (CMD["FORWARD"],  150, 2.0),
        (CMD["LEFT"],     150, 1.0),
        (CMD["FORWARD"],  150, 2.0),
        (CMD["LEFT"],     150, 1.0),
        (CMD["STOP"],       0, 0.5),
    ],
    "zigzag": [
        (CMD["FORWARD"], 150, 1.2),
        (CMD["FWD_RIGHT"], 150, 0.6),
        (CMD["FORWARD"], 150, 1.2),
        (CMD["FWD_LEFT"], 150, 0.6),
        (CMD["FORWARD"], 150, 1.2),
        (CMD["FWD_RIGHT"], 150, 0.6),
        (CMD["FORWARD"], 150, 1.2),
        (CMD["STOP"], 0, 0.5),
    ],
    "circle": [
        (CMD["RIGHT"], 180, 6.0),
        (CMD["STOP"], 0, 0.5),
    ],
}


def simulate(seq, noise=True):
    """执行指令序列，返回轨迹点列表 [(x,y), ...]"""
    x, y, theta = 0.0, 0.0, 0.0
    trail = [(x, y)]

    for t_val, pwm, duration in seq:
        lr, rr = DIR_MOTOR[t_val]
        steps = int(duration / DT)

        for _ in range(steps):
            v_l = lr * pwm * PWM_TO_SPEED
            v_r = rr * pwm * PWM_TO_SPEED

            if noise:
                v_l *= random.gauss(1.0, 0.05)   # 速度噪声 5%
                v_r *= random.gauss(1.0, 0.05)

            # 差速模型
            v = (v_l + v_r) / 2.0
            omega = (v_r - v_l) / WHEEL_BASE

            dtheta = omega * DT
            if noise:
                dtheta += random.gauss(0, 0.002)  # 角度漂移
            theta += dtheta

            dx = v * math.cos(theta) * DT
            dy = v * math.sin(theta) * DT
            if noise:
                dx += random.gauss(0, 0.005)      # 位置抖动
                dy += random.gauss(0, 0.005)

            x += dx
            y += dy
            trail.append((x, y))

    return trail


def draw_map(trail_noise, trail_true, seq, title=""):
    """绘制栅格地图 + 轨迹"""
    map_size = 5.0
    scale = 100
    px_size = map_size * scale
    center = px_size / 2

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_facecolor("#f8f9fa")
    ax.set_aspect("equal")

    # 栅格
    for i in range(0, int(px_size) + 1, 10):
        alpha = 0.2 if i % 50 == 0 else 0.08
        lw = 1.0 if i % 50 == 0 else 0.5
        ax.axhline(i, color="#888", alpha=alpha, lw=lw)
        ax.axvline(i, color="#888", alpha=alpha, lw=lw)

    # 原点十字
    ax.plot([center - 15, center + 15], [center, center], color="red", lw=2)
    ax.plot([center, center], [center - 15, center + 15], color="red", lw=2)
    ax.text(center + 5, center - 18, "O", fontsize=12, color="red", ha="center")
    ax.text(px_size - 10, center - 12, "+X", fontsize=10, color="#555")
    ax.text(center + 10, 18, "+Y", fontsize=10, color="#555")

    # 真实轨迹（无噪声）
    tx = [center + p[0] * scale for p in trail_true]
    ty = [center - p[1] * scale for p in trail_true]
    ax.plot(tx, ty, "--", color="#99ccff", lw=1.5, alpha=0.6, label="真实路径")

    # 噪声轨迹
    nx = [center + p[0] * scale for p in trail_noise]
    ny = [center - p[1] * scale for p in trail_noise]
    ax.plot(nx, ny, "-", color="#2563eb", lw=2.5, alpha=0.85, label="仿真路径 (含噪声)")

    # 起点/终点
    ax.scatter(nx[0], ny[0], c="#10b981", s=100, zorder=5, edgecolors="white",
               linewidth=1.5, label="起点")
    ax.scatter(nx[-1], ny[-1], c="#ef4444", s=100, zorder=5, marker="s",
               edgecolors="white", linewidth=1.5, label="终点")

    # 方向箭头
    step = max(1, len(trail_noise) // 20)
    for i in range(step, len(trail_noise), step):
        dx = nx[i] - nx[i - 1]
        dy = ny[i] - ny[i - 1]
        d = math.hypot(dx, dy)
        if d > 2:
            ax.annotate("", xy=(nx[i], ny[i]),
                        xytext=(nx[i] - dx / d * 10, ny[i] - dy / d * 10),
                        arrowprops=dict(arrowstyle="->", color="#2563eb", lw=1, alpha=0.5))

    ax.set_xlim(-30, px_size + 30)
    ax.set_ylim(-30, px_size + 30)
    ax.axis("off")
    ax.legend(loc="upper right", fontsize=10, framealpha=0.9, edgecolor="#ddd")

    # 信息
    dist = sum(math.hypot(trail_noise[i][0] - trail_noise[i - 1][0],
                          trail_noise[i][1] - trail_noise[i - 1][1])
               for i in range(1, len(trail_noise)))
    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
    ax.text(0.02, 0.98,
            f"总里程: {dist:.2f} m\n"
            f"起点: ({trail_noise[0][0]:.2f}, {trail_noise[0][1]:.2f})\n"
            f"终点: ({trail_noise[-1][0]:.2f}, {trail_noise[-1][1]:.2f})",
            transform=ax.transAxes, fontsize=9, color="#333", va="top",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="white",
                      edgecolor="#ddd", alpha=0.9))

    plt.tight_layout()
    plt.savefig("drive_sim_result.png", dpi=150, bbox_inches="tight")
    print("已保存: drive_sim_result.png")
    plt.show()


def main():
    print("=" * 40)
    print("车辆运动仿真脚本")
    print("可选路径: square, zigzag, circle")
    print("=" * 40)

    pattern = input("选择路径 (默认 square): ").strip() or "square"
    if pattern not in TEST_SEQUENCES:
        pattern = "square"

    seq = TEST_SEQUENCES[pattern]

    print(f"\n执行路径: {pattern}")
    for cmd, pwm, dur in seq:
        name = {v: k for k, v in CMD.items()}.get(cmd, f"T={cmd}")
        print(f"  {name:<8} PWM={pwm:<3} {dur:.1f}s")

    trail_true = simulate(seq, noise=False)
    trail_noise = simulate(seq, noise=True)

    print(f"\n轨迹点数: {len(trail_noise)}")
    print(f"终点: ({trail_noise[-1][0]:.2f}, {trail_noise[-1][1]:.2f})")

    draw_map(trail_noise, trail_true, seq,
             f"车辆行驶模拟 — {pattern.upper()}")


if __name__ == "__main__":
    main()
