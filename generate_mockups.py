"""
Genera plots de mockup para RC-1.
Ejecutar: python generate_mockups.py
Reemplazar con datos reales después de correr error_odom.py
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import math, os

os.makedirs("plots", exist_ok=True)

def simulate_square(noise_x=0.02, noise_y=0.015, drift=0.008, run=1):
    """Simula trayectoria de un cuadrado con deriva."""
    import random
    random.seed(run * 42)
    pts = []
    x, y, theta = 0.0, 0.0, 0.0
    step = 0.02
    for lap in range(3):
        for side in range(4):
            dist = 1.0 + random.uniform(-0.02, 0.02)
            steps = int(dist / step)
            for _ in range(steps):
                x += step * math.cos(theta) + random.gauss(0, noise_x * step)
                y += step * math.sin(theta) + random.gauss(0, noise_y * step)
                pts.append((x, y))
            theta += math.pi/2 + random.gauss(0, 0.04) + drift
    return pts

def ideal_square():
    corners = [(0,0),(1,0),(1,1),(0,1),(0,0)]
    path = []
    for _ in range(3):
        path.extend(corners[:-1])
    path.append((0,0))
    return path

errors = [(8.3, 5.1), (12.7, 3.4), (6.9, 9.2)]

for run in range(1, 4):
    pts = simulate_square(run=run)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    dx_cm, dy_cm = errors[run-1]
    dist = math.hypot(dx_cm, dy_cm)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle(f"RC-1: La Manzana del Tambo — Run {run}  [MOCKUP — reemplazar con datos reales]",
                 fontsize=12, color="gray")

    ax = axes[0]
    ideal = ideal_square()
    ax.plot([p[0] for p in ideal],[p[1] for p in ideal],
            "--", color="#5C6D3A", lw=2, label="Ideal 1×1 m")
    ax.plot(xs, ys, color="#B85042", lw=1.5, alpha=0.85, label="Trayectoria /odom_raw")
    ax.plot(xs[0], ys[0], "go", ms=10, zorder=5, label="Inicio")
    ax.plot(xs[-1], ys[-1], "rs", ms=10, zorder=5, label="Fin")
    ax.annotate("", xy=(xs[-1],ys[-1]), xytext=(xs[0],ys[0]),
                arrowprops=dict(arrowstyle="->", color="crimson", lw=1.5))
    ax.set_title(f"Trayectoria XY — Error cierre: {dist:.1f} cm")
    ax.set_xlabel("x (m)"); ax.set_ylabel("y (m)")
    ax.set_aspect("equal"); ax.legend(fontsize=8); ax.grid(True, alpha=0.3)

    ax2 = axes[1]
    errs = [math.hypot(xs[i]-xs[0], ys[i]-ys[0]) for i in range(len(xs))]
    lap = len(xs)//3
    for l in range(1,3):
        ax2.axvline(l*lap, color="gray", ls=":", alpha=0.6)
    ax2.plot(errs, color="#2E86AB", lw=1)
    ax2.set_title("Distancia al inicio vs. muestra")
    ax2.set_xlabel("Muestra (#)"); ax2.set_ylabel("Distancia (m)")
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    out = f"plots/trayectoria_run{run}.png"
    fig.savefig(out, dpi=150)
    plt.close()
    print(f"Generado: {out}  (error simulado: {dist:.1f} cm)")

print("\nMockups listos en plots/")
print("REEMPLAZAR después de correr: python3 error_odom.py ~/bags/tambo_run<N>")
