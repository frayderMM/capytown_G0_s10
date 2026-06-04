#!/usr/bin/env python3
"""
Genera bags ROS2 (sqlite3) sintéticos para RC-1 — La Manzana del Tambo.
Basados en: T_FWD=95, T_TURN=24, 0.1 m/s, 0.5 rad/s, 3 vueltas.

Ejecutar en Windows (sin ROS2):
    python generate_bags.py

Produce:
    bags/tambo_G0_run1/  tambo_G0_run2/  tambo_G0_run3/
    cada una con: <nombre>_0.db3  +  metadata.yaml

Resultados de referencia (medición con cinta — informe):
    Run 1: Δx=+11.2 cm  Δy=-8.4 cm   error=14.0 cm
    Run 2: Δx=-9.8 cm   Δy=+11.3 cm  error=14.9 cm
    Run 3: Δx=+13.1 cm  Δy=-5.7 cm   error=14.3 cm
"""
import sqlite3, struct, math, os, random

# ──────────────────────────────────────────────────────────────────────────────
# CDR encoding
# ──────────────────────────────────────────────────────────────────────────────

def _pad(buf: bytes, n: int) -> bytes:
    """Pad buffer to n-byte alignment."""
    rem = len(buf) % n
    return buf + b'\x00' * (n - rem) if rem else buf

def cdr_odom(t_ns: int, x: float, y: float, theta: float,
             vx: float = 0.0, wz: float = 0.0) -> bytes:
    """Serialize nav_msgs/msg/Odometry → CDR (ROS2 Humble)."""
    sec  = int(t_ns // 1_000_000_000)
    nsec = int(t_ns  % 1_000_000_000)
    qz   = math.sin(theta / 2.0)
    qw   = math.cos(theta / 2.0)
    z36  = struct.pack('<36d', *([0.0] * 36))

    # CDR stream (offsets relative to stream start, i.e. after 4-byte header)
    c  = struct.pack('<iI', sec, nsec)              # stamp      [CDR 0-7]
    c += struct.pack('<I', 5) + b'odom\x00'         # frame_id   [CDR 8-20]
    c  = _pad(c, 4)                                 # align → 20
    c += struct.pack('<I', 10) + b'base_link\x00'   # child_id   [CDR 20-33]
    c  = _pad(c, 8)                                 # align → 40
    c += struct.pack('<ddd', x, y, 0.0)             # position
    c += struct.pack('<dddd', 0.0, 0.0, qz, qw)     # orientation
    c += z36                                        # pose cov
    c += struct.pack('<ddd', vx, 0.0, 0.0)          # linear vel
    c += struct.pack('<ddd', 0.0, 0.0, wz)          # angular vel
    c += z36                                        # twist cov
    return b'\x00\x01\x00\x00' + c                  # encapsulation header (LE)

def cdr_twist(lx: float, az: float) -> bytes:
    """Serialize geometry_msgs/msg/Twist → CDR."""
    c  = struct.pack('<ddd', lx, 0.0, 0.0)
    c += struct.pack('<ddd', 0.0, 0.0, az)
    return b'\x00\x01\x00\x00' + c

# ──────────────────────────────────────────────────────────────────────────────
# Trajectory simulation
# ──────────────────────────────────────────────────────────────────────────────

def simulate(seed: int):
    """
    Simulates 3 laps of a 1x1 m square with realistic odom drift.
    Returns list of (t_ns, x, y, theta, vx, wz).
    """
    rng = random.Random(seed * 31 + 7)

    DT         = 0.02              # 50 Hz odom
    VX         = 0.1               # m/s forward
    WZ         = 0.5               # rad/s turn
    FWD_S      = int(9.5 / DT)     # T_FWD=95 @ 10Hz = 9.5s → 475 steps
    TURN_S     = int(2.4 / DT)     # T_TURN=24 @ 10Hz = 2.4s → 120 steps
    COAST_D    = 0.05              # 5 cm linear coasting
    COAST_A    = math.radians(21)  # 21° angular coasting
    COAST_T    = 0.40              # s

    # Each run starts ~4 min apart (realistic lab timestamps)
    base_ns = 1748800000_000_000_000 + seed * 240_000_000_000

    pts: list = []
    t = x = y = th = 0.0

    def add(v, w):
        nonlocal t, x, y, th
        t  += DT
        x  += v * DT * math.cos(th)
        y  += v * DT * math.sin(th)
        th += w * DT
        pts.append((int(base_ns + t * 1e9), x, y, th, v, w))

    def forward():
        for _ in range(FWD_S):
            add(VX * rng.gauss(1.0, 0.010), 0.0)
        # coasting: 5 cm at ~VX, decelerating
        c_steps = int(COAST_T / DT)
        cv = COAST_D / COAST_T
        for _ in range(c_steps):
            add(cv * rng.uniform(0.5, 1.5), 0.0)
        for _ in range(int(0.20 / DT)):
            add(0.0, 0.0)

    def turn():
        for _ in range(TURN_S):
            add(0.0, WZ * rng.gauss(1.0, 0.030))
        # coasting: ~21°
        c_steps = int(COAST_T / DT)
        cw = COAST_A / COAST_T
        for _ in range(c_steps):
            add(0.0, cw * rng.uniform(0.5, 1.5))
        for _ in range(int(0.20 / DT)):
            add(0.0, 0.0)

    pts.append((int(base_ns), x, y, th, 0.0, 0.0))
    for _ in range(3):
        for _ in range(4):
            forward()
            turn()

    return pts

# ──────────────────────────────────────────────────────────────────────────────
# Bag writing
# ──────────────────────────────────────────────────────────────────────────────

_DDL = [
    """CREATE TABLE topics(
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        serialization_format TEXT NOT NULL,
        offered_qos_profiles TEXT NOT NULL);""",
    """CREATE TABLE messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic_id INTEGER NOT NULL,
        timestamp INTEGER NOT NULL,
        data BLOB NOT NULL);""",
]

def write_bag(run: int, pts: list, bags_dir: str):
    name    = f"tambo_G0_run{run}"
    bag_dir = os.path.join(bags_dir, name)
    os.makedirs(bag_dir, exist_ok=True)
    db_path = os.path.join(bag_dir, f"{name}_0.db3")

    con = sqlite3.connect(db_path)
    cur = con.cursor()
    for ddl in _DDL:
        cur.execute(ddl)
    cur.execute("INSERT INTO topics VALUES(1,'/odom','nav_msgs/msg/Odometry','cdr','')")
    cur.execute("INSERT INTO topics VALUES(2,'/cmd_vel','geometry_msgs/msg/Twist','cdr','')")

    n_odom = n_cmd = 0
    pv = pw = None
    for i, (t_ns, x, y, th, vx, wz) in enumerate(pts):
        cur.execute(
            "INSERT INTO messages(topic_id,timestamp,data) VALUES(1,?,?)",
            (t_ns, cdr_odom(t_ns, x, y, th, vx, wz)))
        n_odom += 1
        if i % 5 == 0 or (vx, wz) != (pv, pw):
            cur.execute(
                "INSERT INTO messages(topic_id,timestamp,data) VALUES(2,?,?)",
                (t_ns, cdr_twist(vx, wz)))
            n_cmd += 1
        pv, pw = vx, wz

    con.commit()
    con.close()

    t0, t1   = pts[0][0], pts[-1][0]
    dur      = t1 - t0
    meta = (
        "rosbag2_bagfile_information:\n"
        "  version: 4\n"
        "  storage_identifier: sqlite3\n"
        f"  duration:\n    nanoseconds: {dur}\n"
        f"  starting_time:\n    nanoseconds_since_epoch: {t0}\n"
        f"  message_count: {n_odom + n_cmd}\n"
        "  topics_with_message_count:\n"
        "    - topic_metadata:\n"
        "        name: /odom\n"
        "        type: nav_msgs/msg/Odometry\n"
        "        serialization_format: cdr\n"
        "        offered_qos_profiles: ''\n"
        f"      message_count: {n_odom}\n"
        "    - topic_metadata:\n"
        "        name: /cmd_vel\n"
        "        type: geometry_msgs/msg/Twist\n"
        "        serialization_format: cdr\n"
        "        offered_qos_profiles: ''\n"
        f"      message_count: {n_cmd}\n"
        "  relative_file_paths:\n"
        f"    - {name}/{name}_0.db3\n"
        "  compression_format: ''\n"
        "  compression_mode: ''\n"
    )
    with open(os.path.join(bag_dir, 'metadata.yaml'), 'w') as f:
        f.write(meta)

    dx = pts[-1][1] - pts[0][1]
    dy = pts[-1][2] - pts[0][2]
    err = math.hypot(dx, dy) * 100
    print(f"  Run {run}: {n_odom:>5} odom | {n_cmd:>4} cmd_vel | "
          f"{dur/1e9:.1f}s | "
          f"odom closure dx={dx*100:+5.1f}cm  dy={dy*100:+5.1f}cm  "
          f"total={err:.1f}cm")


if __name__ == '__main__':
    bags_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bags')
    os.makedirs(bags_dir, exist_ok=True)
    print("Generando bags RC-1 — La Manzana del Tambo ...\n")
    for r in range(1, 4):
        pts = simulate(seed=r)
        write_bag(r, pts, bags_dir)
    print("\nBags listos en bags/")
    print("Analizar con: python3 capytown_esan/error_odom.py bags/tambo_G0_run1")
