# capytown_G0_s10 — RC-1: La Manzana del Tambo

**CapyTown · Robótica 2026-I · Universidad ESAN**
**Semana 10 · Prof. Marks Calderón Niquin**

---

## Integrantes del grupo

| Nombre | Código |
|--------|--------|
| (completar) | (completar) |
| (completar) | (completar) |
| (completar) | (completar) |

---

## Configuración del robot

| Parámetro | Valor |
|-----------|-------|
| **ROS_DOMAIN_ID** | 20 |
| **b_eff calibrado** | 0.24607 m |
| **T_FWD (100 cm)** | 96 mensajes @ 10 Hz |
| **T_TURN (90°)** | 24 mensajes @ 10 Hz |
| Velocidad lineal | 0.1 m/s |
| Velocidad angular | 0.5 rad/s |
| Robot | Yahboom MicroROS-Pi5 |
| ROS | ROS 2 Humble |

---

## Resultados RC-1

### Calibración b_eff (UMBmark)

| Run | b_eff usado | Odom reportado | Medido real | Error % |
|-----|------------|----------------|-------------|---------|
| 1 | 0.20000 m | 360.49° | 335.00° | 7.07% |
| 2 | 0.21522 m | 361.69° | 320.00° | 11.53% |
| 3 | 0.24326 m | 362.13° | 358.00° | **1.14%** ✅ |

**b_eff final adoptado: 0.24607 m**

### Error de cierre — 3 runs del cuadrado 1×1 m

| Run | Δx (cm) | Δy (cm) | Δθ (°) | Error total (cm) |
|-----|---------|---------|--------|-----------------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| **Promedio** | | | | |

---

## Estructura del repositorio

```
capytown_G0_s10/
├── config/
│   └── wheel_params.yaml       # b_eff=0.24607 calibrado
├── capytown_esan/
│   └── error_odom.py           # Análisis de trayectoria
├── bags/
│   ├── tambo_G0_run1/          # Bag del run 1
│   ├── tambo_G0_run2/          # Bag del run 2
│   └── tambo_G0_run3/          # Bag del run 3
├── plots/
│   ├── trayectoria_run1.png
│   ├── trayectoria_run2.png
│   └── trayectoria_run3.png
├── calibration_log.csv         # Historial calibración b_eff
├── informe.pdf                 # Informe técnico 1 página
└── README.md
```
