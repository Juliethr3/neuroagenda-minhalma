"""Genera el mockup (wireframe) del dashboard NeuroAgenda. Datos ficticios, solo ilustrativos."""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

OUT = Path(__file__).resolve().parents[1] / "mockup" / "mockup_dashboard.png"
OUT.parent.mkdir(exist_ok=True)
C = {"bg": "#F5F6F8", "card": "white", "ink": "#1F2A37", "mut": "#6B7280", "hi": "#C44E52", "mid": "#E3A13B", "lo": "#3C8D5A", "pri": "#2F5D8A"}

fig = plt.figure(figsize=(12, 6.6), facecolor=C["bg"])
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 120); ax.set_ylim(0, 66); ax.axis("off")

def card(x, y, w, h, fc=C["card"]):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=1.2", fc=fc, ec="#D9DDE3", lw=1))

# Barra superior
ax.add_patch(plt.Rectangle((0, 60), 120, 6, fc=C["pri"]))
ax.text(2, 63, "NeuroAgenda", color="white", fontsize=15, fontweight="bold", va="center")
ax.text(25, 63, "Riesgo de inasistencia · MinHalma · Psicología, Nutrición y Fisioterapia", color="white", fontsize=10, va="center")
ax.text(118, 63, "Coordinadora de agenda  ▾", color="white", fontsize=9, va="center", ha="right")
# Filtros
for i, f in enumerate(["Fecha: mar 20 oct", "Sede: Principal", "Servicio: Todos", "Profesional: Todos"]):
    card(2 + i * 22, 54, 20, 3.6); ax.text(3 + i * 22, 55.8, f + "  ▾", fontsize=8.5, color=C["ink"], va="center")
# KPIs
kpis = [("Citas del día", "148", C["ink"]), ("No-show esperado", "29 (19,6 %)", C["hi"]),
        ("Riesgo alto (≥ 40 %)", "22 citas", C["hi"]), ("Cupos recuperados (sem.)", "+31", C["lo"])]
for i, (k, v, col) in enumerate(kpis):
    card(2 + i * 29, 43, 27, 8.5)
    ax.text(3.5 + i * 29, 49.3, k, fontsize=9, color=C["mut"]); ax.text(3.5 + i * 29, 45.3, v, fontsize=17, fontweight="bold", color=col)
# Tabla de priorización
card(2, 2, 72, 38)
ax.text(4, 37.3, "Lista priorizada de contacto (top riesgo)", fontsize=11, fontweight="bold", color=C["ink"])
hdr = ["Hora", "Paciente*", "Servicio", "Antelación", "Riesgo", "Factores principales", "Acción sugerida"]
xs = [4, 9.5, 17.5, 28, 35, 45, 61.8]
for x, h in zip(xs, hdr):
    ax.text(x, 34, h, fontsize=8, color=C["mut"], fontweight="bold")
rows = [("07:30", "P-0192", "Fisioterapia", "34 d", .71, "2 inasist. previas; antelación", "Llamar hoy"),
        ("08:00", "P-0457", "Psicología", "21 d", .58, "Antelación; edad 19", "Llamar + WhatsApp"),
        ("09:20", "P-0033", "Nutrición", "45 d", .52, "Antelación; sin SMS", "Enviar recordatorio"),
        ("10:40", "P-0811", "Psicología", "15 d", .44, "1 inasist. previa", "Confirmar 24 h antes"),
        ("11:00", "P-0290", "Fisioterapia", "9 d", .37, "Antelación", "Recordatorio estándar"),
        ("14:00", "P-0616", "Psicología", "0 d", .06, "Agendada el mismo día", "Sin acción")]
for j, r in enumerate(rows):
    yy = 30.5 - j * 4.4
    if j % 2 == 0:
        ax.add_patch(plt.Rectangle((3, yy - 1.6), 70, 3.8, fc="#F3F5F8", ec="none"))
    col = C["hi"] if r[4] >= .5 else (C["mid"] if r[4] >= .3 else C["lo"])
    for x, val in zip(xs, [r[0], r[1], r[2], r[3], None, r[5], r[6]]):  # noqa
        if val is not None:
            ax.text(x, yy, val, fontsize=7.6 if x > 60 else 8, color=C["ink"], va="center")
    ax.add_patch(plt.Rectangle((35, yy - 0.8), 5 * r[4] / .75, 1.6, fc=col))
    ax.text(35 + 5 * r[4] / .75 + 0.5, yy, f"{r[4]:.0%}", fontsize=7.5, va="center", color=col)
    ax.add_patch(FancyBboxPatch((61.3, yy - 1.1), 12, 2.2, boxstyle="round,pad=0.1,rounding_size=0.6", fc="none", ec=col, lw=.8))
ax.text(4, 3.3, "* Seudónimo: el tablero nunca muestra nombre ni diagnóstico. Explicación por SHAP; decisión final humana.", fontsize=7.5, color=C["mut"])
# Panel derecho: tendencia y desempeño
card(77, 22, 41, 18)
ax.text(79, 37.3, "Tasa de no-show semanal (real vs. meta)", fontsize=10, fontweight="bold", color=C["ink"])
wk = list(range(8)); real = [22, 21, 23, 20, 19, 18, 17.5, 16.8]
ax.plot([80 + w * 4.8 for w in wk], [24 + (v - 14) * 1.2 for v in real], c=C["hi"], lw=2, marker="o", ms=3)
ax.plot([80, 113.6], [24 + (15 - 14) * 1.2] * 2, c=C["lo"], ls="--", lw=1); ax.text(114, 25.2, "meta 15 %", fontsize=7, color=C["lo"])
card(77, 2, 41, 18)
ax.text(79, 17.3, "Modelo en producción", fontsize=10, fontweight="bold", color=C["ink"])
for k, (lab, val) in enumerate([("ROC-AUC (validación)", "0,73"), ("Captura de no-show contactando top 30 %", "53 %"),
                                ("Calibración (Brier)", "0,144"), ("Brecha de recall por subgrupo", "≤ 5 p.p."),
                                ("Última actualización", "lun 19 oct 06:00")]):
    ax.text(79, 14 - k * 2.6, lab, fontsize=8, color=C["mut"]); ax.text(116, 14 - k * 2.6, val, fontsize=8.5, ha="right", color=C["ink"], fontweight="bold")
ax.text(119, 0.6, "Mockup de baja fidelidad · datos ficticios", fontsize=7, color=C["mut"], ha="right")
fig.savefig(OUT, dpi=200, facecolor=C["bg"])
print("Mockup:", OUT)
