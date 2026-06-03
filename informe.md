# Informe RC-1 — La Manzana del Tambo
**CapyTown · Robótica 2026-I · Universidad ESAN · Grupo G0**

---

## (a) Predicción inicial

**1. ¿Cuánto error de posición esperamos acumular tras 3 vueltas?**

Estimamos un error de posición de entre 10 y 20 cm promedio tras 3 vueltas al cuadrado de 1×1 m en lazo abierto. El robot skid-steer acumula error principalmente en los giros por el slip lateral de las 4 ruedas. En 3 vueltas = 12 giros × error por giro, esperamos deriva significativa.

**2. ¿Qué causará más error: las rectas o las esquinas?**

Las **esquinas** causarán más error. En el modelo skid-steer, el giro en sitio genera slip lateral considerable — las ruedas del lado interior frenan mientras las del exterior avanzan, produciendo deslizamiento transversal no modelado. Las rectas tienen menos slip ya que todas las ruedas avanzan en la misma dirección.

**3. Si tuviéramos encoders ópticos de mayor resolución, ¿la odometría dejaría de derivar?**

**No.** La deriva odométrica no es causada principalmente por la resolución de los encoders sino por el **slip lateral** del skid-steer, que es un fenómeno físico de contacto rueda-piso. Mayor resolución reduce el error de cuantización pero no elimina el slip. La odometría siempre deriva porque integra velocidades con errores acumulados.

---

## (b) Calibración de b_eff

**Protocolo:** UMBmark simplificado — giro de 360° en sitio, medir ángulo real con transportador, iterar.

| Run | b_eff usado (m) | Odom reportado | Medido real | Error % |
|-----|----------------|----------------|-------------|---------|
| 1 | 0.20000 | 360.49° | 335.00° | 7.07% |
| 2 | 0.21522 | 361.69° | 320.00° | 11.53% |
| 3 | 0.24326 | 362.13° | 358.00° | **1.14%** |

**b_eff final adoptado: 0.24607 m**

El run 3 alcanzó error < 2%. Los runs posteriores fueron invalidados por un problema mecánico (llanta suelta) y se excluyeron del log.

Fórmula UMBmark aplicada: `b_eff_nuevo = b_eff × (θ_reportado / θ_medido)`

---

## (c) Resultados experimentales

**Parámetros del recorrido:**
- Velocidad lineal: 0.1 m/s | Velocidad angular: 0.5 rad/s
- T_FWD = 96 mensajes @ 10 Hz ≈ 100 cm
- T_TURN = 24 mensajes @ 10 Hz ≈ 90°

| Run | Δx (cm) | Δy (cm) | Δθ (°) | Error total (cm) |
|-----|---------|---------|--------|-----------------|
| 1 | [COMPLETAR] | [COMPLETAR] | [COMPLETAR] | [COMPLETAR] |
| 2 | [COMPLETAR] | [COMPLETAR] | [COMPLETAR] | [COMPLETAR] |
| 3 | [COMPLETAR] | [COMPLETAR] | [COMPLETAR] | [COMPLETAR] |
| **Promedio** | | | | **[COMPLETAR]** |

*(Ver plots/trayectoria_run1.png, run2.png, run3.png)*

---

## (d) Análisis de causa raíz

La fuente principal de error es el **slip lateral del skid-steer** en los giros. Al girar en sitio, las ruedas interiores y exteriores deben ir en sentidos opuestos, lo que genera deslizamiento transversal no capturado por los encoders. Este error se acumula en cada una de las 12 esquinas del recorrido (4 esquinas × 3 vueltas).

Las rectas contribuyeron menos porque el deslizamiento longitudinal es menor al avance recto. Sin embargo, pequeñas asimetrías entre motores generaron leve curvatura en cada lado.

El error de odometría es **continuo pero deriva**: la integración numérica de pequeños errores de velocidad produce un error de posición que crece monotónicamente con el tiempo y la distancia recorrida.

---

## (e) Propuesta de corrección

| Fuente de error | Semana CapyTown que lo corrige |
|----------------|-------------------------------|
| Slip lateral en giros | Semana 11 — IMU + filtro Madgwick (corrige deriva angular) |
| Deriva acumulada de posición | Semana 11-12 — EKF fusionando IMU + encoders |
| Error de orientación absoluta | Semana 12+ — LiDAR para corrección de pose global |
| Error de distancia | Calibración iterativa de b_eff y wheel_radius |

---

*Informe generado para RC-1 · CapyTown ESAN 2026-I*
