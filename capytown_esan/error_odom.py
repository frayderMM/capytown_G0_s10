#!/usr/bin/env python3
"""
error_odom.py — RC-1: Análisis de trayectoria odométrica
Uso:  python3 error_odom.py <ruta_al_bag>
      python3 error_odom.py ~/bags/tambo_G0_20260601_123456

Entregable del grupo para RC-1 — CapyTown ESAN 2026-I
"""

import sys
import os
import math
import matplotlib
matplotlib.use("Agg")           # sin pantalla (puede correrse en SSH)
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ── Intentar importar rosbag2 ──────────────────────────────────────────────────
try:
    from rosbag2_py import SequentialReader, StorageOptions, ConverterOptions
    from rclpy.serialization import deserialize_message
    from nav_msgs.msg import Odometry
    from geometry_msgs.msg import TwistStamped
    ROSBAG2_AVAILABLE = True
except ImportError:
    ROSBAG2_AVAILABLE = False


# ── Lectura del bag ────────────────────────────────────────────────────────────
def read_odom_from_bag(bag_path: str):
    """Extrae posiciones (x, y) del topic /odom."""
    if not ROSBAG2_AVAILABLE:
        raise RuntimeError(
            "rosbag2_py no está disponible.\n"
            "Ejecuta este script dentro del contenedor Docker con ROS2 Humble."
        )

    reader = SequentialReader()
    reader.open(
        StorageOptions(uri=bag_path, storage_id="sqlite3"),
        ConverterOptions("", ""),
    )

    xs, ys, thetas, timestamps = [], [], [], []

    while reader.has_next():
        topic, data, t = reader.read_next()
        if topic == "/odom_raw":
            msg = deserialize_message(data, Odometry)
            x = msg.pose.pose.position.x
            y = msg.pose.pose.position.y
            # orientación en yaw (euler z) a partir del quaternion
            qx = msg.pose.pose.orientation.x
            qy = msg.pose.pose.orientation.y
            qz = msg.pose.pose.orientation.z
            qw = msg.pose.pose.orientation.w
            yaw = math.atan2(2*(qw*qz + qx*qy), 1 - 2*(qy**2 + qz**2))
            xs.append(x)
            ys.append(y)
            thetas.append(yaw)
            timestamps.append(t * 1e-9)   # ns → s

    if not xs:
        raise ValueError("No se encontraron mensajes en /odom_raw. ¿Grabaste el bag correctamente?")

    return xs, ys, thetas, timestamps


# ── Cálculo de errores ─────────────────────────────────────────────────────────
def closing_error(xs, ys, thetas):
    """Error de cierre: distancia entre inicio y fin."""
    dx = xs[-1] - xs[0]
    dy = ys[-1] - ys[0]
    dtheta = thetas[-1] - thetas[0]
    dist = math.hypot(dx, dy)
    return dx, dy, dtheta, dist


# ── Trayectoria ideal del cuadrado ─────────────────────────────────────────────
def ideal_square(side=1.0, laps=3):
    """Vértices del cuadrado ideal (3 vueltas = regresa al origen)."""
    corners = [(0, 0), (side, 0), (side, side), (0, side), (0, 0)]
    path = []
    for _ in range(laps):
        path.extend(corners[:-1])
    path.append((0, 0))
    return path


# ── Gráfica ───────────────────────────────────────────────────────────────────
def plot_trajectory(xs, ys, bag_path: str):
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("RC-1: La Manzana del Tambo — Análisis de odometría", fontsize=13)

    # ── Panel izquierdo: trayectoria XY ──
    ax = axes[0]
    ideal = ideal_square()
    ix = [p[0] for p in ideal]
    iy = [p[1] for p in ideal]

    ax.plot(ix, iy, "--", color="#5C6D3A", linewidth=2, label="Ideal 1×1 m")
    ax.plot(xs, ys, color="#B85042", linewidth=1.5, alpha=0.85, label="Trayectoria /odom")
    ax.plot(xs[0], ys[0], "go", markersize=10, zorder=5, label="Inicio")
    ax.plot(xs[-1], ys[-1], "rs", markersize=10, zorder=5, label="Fin")

    # flecha de error de cierre
    ax.annotate(
        "", xy=(xs[-1], ys[-1]), xytext=(xs[0], ys[0]),
        arrowprops=dict(arrowstyle="->", color="crimson", lw=1.5),
    )

    dx, dy, dtheta, dist = closing_error(xs, ys, [0] * len(xs))
    ax.set_title(f"Trayectoria XY — Error cierre: {dist*100:.1f} cm")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_aspect("equal")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # ── Panel derecho: error acumulado en el tiempo ──
    ax2 = axes[1]
    errors = [math.hypot(xs[i] - xs[0], ys[i] - ys[0]) for i in range(len(xs))]
    t0 = 0
    times = list(range(len(xs)))   # muestras (proxy del tiempo)

    # marcar inicio de cada vuelta (aproximado por índices)
    lap_size = len(xs) // 3
    for lap in range(1, 3):
        ax2.axvline(lap * lap_size, color="gray", linestyle=":", alpha=0.6,
                    label=f"Inicio vuelta {lap+1}" if lap == 1 else "")

    ax2.plot(errors, color="#2E86AB", linewidth=1)
    ax2.set_title("Distancia al punto de inicio vs. muestra")
    ax2.set_xlabel("Muestra (#)")
    ax2.set_ylabel("Distancia al inicio (m)")
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()

    # guardar PNG junto al bag
    out_png = bag_path.rstrip("/") + "_trayectoria.png"
    fig.savefig(out_png, dpi=150)
    print(f"Gráfica guardada: {out_png}")
    return out_png


# ── Reporte en consola ────────────────────────────────────────────────────────
def print_report(xs, ys, thetas):
    dx, dy, dtheta, dist = closing_error(xs, ys, thetas)

    print()
    print("=" * 50)
    print("  RESULTADOS RC-1 — Error de cierre")
    print("=" * 50)
    print(f"  Punto inicio : ({xs[0]:.4f} m, {ys[0]:.4f} m)")
    print(f"  Punto final  : ({xs[-1]:.4f} m, {ys[-1]:.4f} m)")
    print()
    print(f"  Δx           : {dx*100:+.2f} cm")
    print(f"  Δy           : {dy*100:+.2f} cm")
    print(f"  Δθ           : {math.degrees(dtheta):+.2f} °")
    print(f"  Error total  : {dist*100:.2f} cm")
    print()
    if dist * 100 <= 5:
        print("  ★ BONUS alcanzable — error ≤ 5 cm")
    elif dist * 100 <= 15:
        print("  ✔ Dentro del límite — error ≤ 15 cm (2 pts)")
    else:
        print("  ✘ Error > 15 cm — ajustar b_eff y repetir")
    print("=" * 50)
    print()
    print("Estadísticas del bag:")
    print(f"  Muestras /odom: {len(xs)}")
    print(f"  Recorrido X   : [{min(xs):.3f}, {max(xs):.3f}] m")
    print(f"  Recorrido Y   : [{min(ys):.3f}, {max(ys):.3f}] m")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print("Uso: python3 error_odom.py <ruta_al_bag>")
        print("Ejemplo: python3 error_odom.py ~/bags/tambo_G0_20260601_123456")
        sys.exit(1)

    bag_path = os.path.expanduser(sys.argv[1])

    if not os.path.exists(bag_path):
        print(f"ERROR: No se encontró el bag en '{bag_path}'")
        sys.exit(1)

    print(f"Leyendo bag: {bag_path}")
    xs, ys, thetas, timestamps = read_odom_from_bag(bag_path)
    print(f"  {len(xs)} mensajes de /odom leídos.")

    print_report(xs, ys, thetas)
    plot_trajectory(xs, ys, bag_path)


if __name__ == "__main__":
    main()
