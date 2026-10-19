# %% [markdown]
# # 01 · Entendimiento y calidad de los datos — Inasistencia a citas (no-show)
# **MINE-4101 Ciencia de Datos Aplicada · Proyecto final · Entrega 1**
#
# Objetivo: describir la estructura, calidad y suficiencia del conjunto *Medical Appointment No Shows*
# (citas ambulatorias del sistema público de Vitória, ES, Brasil; abril–junio 2016) como **conjunto proxy**
# para validar el enfoque analítico antes de recibir datos de MinHalma (organización aliada).
#
# Orden de ejecución: este notebook es autocontenido; ejecutar de arriba a abajo. Semilla fija = 42.

# %%
import json
import sys
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

warnings.filterwarnings("ignore", category=FutureWarning)
ROOT = Path.cwd().resolve().parent if Path.cwd().name == "notebooks" else Path.cwd().resolve()
sys.path.insert(0, str(ROOT / "src"))
from utils import (cramers_v, logit_or_table, mann_whitney_rb, mantel_haenszel_or,
                   rate_table, wilson_ci)

SEED = 42
RAW = ROOT / "data" / "raw" / "KaggleV2-May-2016.csv"
FIG = ROOT / "reports" / "figures"; FIG.mkdir(parents=True, exist_ok=True)
TAB = ROOT / "reports" / "tables"; TAB.mkdir(parents=True, exist_ok=True)
sns.set_theme(style="whitegrid", context="notebook", font="DejaVu Sans")
plt.rcParams.update({"figure.dpi": 110, "savefig.dpi": 200, "savefig.bbox": "tight"})
pd.set_option("display.width", 140, "display.max_columns", 30)
RESULTS = {}  # métricas clave que alimentan el reporte ejecutivo

# %% [markdown]
# ## 1. Carga y estructura

# %%
raw = pd.read_csv(RAW)
print("Dimensiones:", raw.shape)
print(raw.dtypes.to_string())
RENAME = {
    "PatientId": "paciente_id", "AppointmentID": "cita_id", "Gender": "sexo",
    "ScheduledDay": "fecha_agendamiento", "AppointmentDay": "fecha_cita", "Age": "edad",
    "Neighbourhood": "barrio", "Scholarship": "subsidio_bolsa_familia", "Hipertension": "hipertension",
    "Diabetes": "diabetes", "Alcoholism": "alcoholismo", "Handcap": "discapacidad",
    "SMS_received": "sms_recibido", "No-show": "no_show_txt",
}
df = raw.rename(columns=RENAME).copy()
df["fecha_agendamiento"] = pd.to_datetime(df["fecha_agendamiento"], utc=True)
df["fecha_cita"] = pd.to_datetime(df["fecha_cita"], utc=True)
df["no_show"] = (df["no_show_txt"] == "Yes").astype(int)
RESULTS["n_citas"] = int(len(df))
RESULTS["n_pacientes"] = int(df["paciente_id"].nunique())
RESULTS["periodo_citas"] = [str(df["fecha_cita"].min().date()), str(df["fecha_cita"].max().date())]
RESULTS["periodo_agendamiento"] = [str(df["fecha_agendamiento"].min().date()), str(df["fecha_agendamiento"].max().date())]
print(json.dumps({k: RESULTS[k] for k in RESULTS}, indent=1))

# %% [markdown]
# ## 2. Calidad de datos
# Dimensiones evaluadas: completitud, unicidad, validez (rangos y dominios), consistencia temporal y precisión.

# %%
q = []
q.append(("Completitud", "Valores nulos (todas las columnas)", int(df.isna().sum().sum())))
q.append(("Unicidad", "cita_id duplicado", int(df["cita_id"].duplicated().sum())))
q.append(("Unicidad", "Filas duplicadas sin cita_id",
          int(df.drop(columns="cita_id").duplicated().sum())))
q.append(("Validez", "edad < 0", int((df["edad"] < 0).sum())))
q.append(("Validez", "edad > 100", int((df["edad"] > 100).sum())))
q.append(("Validez", "discapacidad fuera de {0,1} (codificada 0–4)", int((df["discapacidad"] > 1).sum())))
lead = (df["fecha_cita"].dt.normalize() - df["fecha_agendamiento"].dt.normalize()).dt.days
q.append(("Consistencia temporal", "fecha_cita anterior a fecha_agendamiento", int((lead < 0).sum())))
q.append(("Precisión", "fecha_cita sin hora (todas 00:00)",
          int((df["fecha_cita"].dt.hour == 0).sum())))
q.append(("Validez", "paciente_id no entero (float corrupto)",
          int((df["paciente_id"] % 1 != 0).sum())))
q.append(("Dominio", "sexo: categorías", ", ".join(sorted(df["sexo"].unique()))))
q.append(("Dominio", "barrio: cardinalidad", int(df["barrio"].nunique())))
q.append(("Dominio", "días de la semana con citas", int(df["fecha_cita"].dt.dayofweek.nunique())))
calidad = pd.DataFrame(q, columns=["dimension", "regla", "resultado"])
calidad.to_csv(TAB / "calidad_datos.csv", index=False)
print(calidad.to_string(index=False))
RESULTS["calidad"] = {r: v for _, r, v in q}

# %% [markdown]
# **Decisiones de limpieza (exploratorias, se formalizan en la Entrega 2):** se excluyen registros con
# `edad < 0` y con antelación negativa (errores de captura, < 0,01 %); `discapacidad` se recodifica a
# binaria y se conserva el conteo original; las edades > 100 se mantienen y se marcan (plausibles en población real,
# pero se revisarán con el stakeholder). La fecha de la cita carece de hora, lo que impide modelar la franja horaria.

# %%
df["antelacion_dias"] = lead
mask_valid = (df["edad"] >= 0) & (df["antelacion_dias"] >= 0)
RESULTS["registros_excluidos"] = int((~mask_valid).sum())
d = df.loc[mask_valid].copy()
d["discapacidad_bin"] = (d["discapacidad"] > 0).astype(int)
d["mismo_dia"] = (d["antelacion_dias"] == 0).astype(int)
d["dia_semana"] = pd.Categorical(d["fecha_cita"].dt.day_name(),
    categories=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], ordered=True)
d["grupo_edad"] = pd.cut(d["edad"], [-1, 11, 17, 29, 44, 59, 74, 120],
    labels=["0–11", "12–17", "18–29", "30–44", "45–59", "60–74", "75+"])
d["antelacion_cat"] = pd.cut(d["antelacion_dias"], [-1, 0, 2, 7, 14, 30, 60, 200],
    labels=["0", "1–2", "3–7", "8–14", "15–30", "31–60", "61+"])
# Historial del paciente SIN fuga temporal: solo cuentan citas cuya fecha (y por tanto su desenlace)
# es estrictamente anterior al día en que se agenda la cita actual, que es el momento de la predicción.
h = d[["paciente_id", "fecha_cita", "no_show"]].sort_values(["fecha_cita", "paciente_id"]).copy()
gh = h.groupby("paciente_id")
h["citas_previas"] = gh.cumcount() + 1
h["inasist_previas"] = gh["no_show"].cumsum()
left = d[["paciente_id"]].assign(t=d["fecha_agendamiento"].dt.normalize(), _idx=d.index).sort_values("t")
hist_join = pd.merge_asof(left, h.rename(columns={"fecha_cita": "t"})[["paciente_id", "t", "citas_previas", "inasist_previas"]],
                          on="t", by="paciente_id", allow_exact_matches=False, direction="backward")
hist_join = hist_join.set_index("_idx").reindex(d.index)
d["citas_previas"] = hist_join["citas_previas"].fillna(0).astype(int)
d["inasist_previas"] = hist_join["inasist_previas"].fillna(0).astype(int)
RESULTS["pct_con_historial"] = round(float((d["citas_previas"] > 0).mean()), 3)
print("Citas con ≥1 cita previa observada:", RESULTS["pct_con_historial"])
print("Registros analizados:", len(d), "| excluidos:", RESULTS["registros_excluidos"])

# %% [markdown]
# ## 3. Análisis univariado

# %%
y_rate = d["no_show"].mean()
RESULTS["tasa_no_show"] = round(float(y_rate), 4)
num = d[["edad", "antelacion_dias"]].describe(percentiles=[.25, .5, .75, .9]).T
num["asimetria"] = d[["edad", "antelacion_dias"]].skew()
num["curtosis"] = d[["edad", "antelacion_dias"]].kurt()
print(num.round(2).to_string())
bins = ["sexo", "subsidio_bolsa_familia", "hipertension", "diabetes", "alcoholismo",
        "discapacidad_bin", "sms_recibido", "mismo_dia"]
prev = pd.DataFrame({c: [(d[c] == (1 if c != "sexo" else "F")).mean()] for c in bins}, index=["prevalencia"]).T
prev.index = [i if i != "sexo" else "sexo = F" for i in prev.index]
print(prev.round(3).to_string())
cpp = d.groupby("paciente_id").size()
RESULTS["citas_por_paciente"] = {"media": round(float(cpp.mean()), 2), "p50": int(cpp.median()),
                                 "p99": int(cpp.quantile(.99)), "max": int(cpp.max()),
                                 "pct_pacientes_1_cita": round(float((cpp == 1).mean()), 3)}
RESULTS["antelacion"] = {"mediana": float(d["antelacion_dias"].median()),
                         "pct_mismo_dia": round(float(d["mismo_dia"].mean()), 3),
                         "asimetria": round(float(d["antelacion_dias"].skew()), 2)}
RESULTS["pct_sms"] = round(float(d["sms_recibido"].mean()), 3)
print(RESULTS["citas_por_paciente"], RESULTS["antelacion"])

# %%
fig, ax = plt.subplots(1, 4, figsize=(16, 3.4))
d["no_show"].map({0: "Asistió", 1: "No asistió"}).value_counts().plot.bar(ax=ax[0], color=["#4C72B0", "#C44E52"])
ax[0].set_title(f"Variable objetivo (no-show = {y_rate:.1%})"); ax[0].tick_params(axis="x", rotation=0)
sns.histplot(d["edad"], bins=40, ax=ax[1], color="#4C72B0"); ax[1].set_title("Edad (años)")
sns.histplot(d["antelacion_dias"], bins=60, ax=ax[2], color="#4C72B0"); ax[2].set_title("Antelación (días)")
ax[2].set_yscale("log")
sns.histplot(cpp.clip(upper=15), discrete=True, ax=ax[3], color="#4C72B0")
ax[3].set_title("Citas por paciente (recortado en 15)"); ax[3].set_yscale("log")
fig.suptitle("Fig. 1. Distribuciones univariadas", x=0.01, ha="left", fontweight="bold")
fig.tight_layout(); fig.savefig(FIG / "fig1_univariado.png"); plt.show()

# %% [markdown]
# ## 4. Análisis bivariado (variable vs. no-show)
# Categóricas: χ² de independencia y V de Cramér corregida. Continuas: U de Mann-Whitney y r rank-biserial
# (distribuciones asimétricas, se descarta t de Student). IC de Wilson al 95 % para las tasas.

# %%
rows = []
for c in bins + ["dia_semana", "grupo_edad", "antelacion_cat", "barrio"]:
    chi2, p, v = cramers_v(d[c], d["no_show"])
    rows.append((c, "χ²", chi2, p, "V de Cramér", v))
for c in ["edad", "antelacion_dias"]:
    u, p, r = mann_whitney_rb(d.loc[d.no_show == 1, c].values, d.loc[d.no_show == 0, c].values)
    rows.append((c, "U Mann-Whitney", u, p, "r rank-biserial", r))
biv = pd.DataFrame(rows, columns=["variable", "prueba", "estadistico", "p_valor", "efecto", "tamano_efecto"])
biv = biv.sort_values("tamano_efecto", key=np.abs, ascending=False)
biv.to_csv(TAB / "bivariado_pruebas.csv", index=False)
print(biv.round(4).to_string(index=False))
RESULTS["bivariado"] = biv.set_index("variable")["tamano_efecto"].round(3).to_dict()

# %%
fig, ax = plt.subplots(1, 4, figsize=(16, 3.6), sharey=True)
for a, c, lab in zip(ax, ["antelacion_cat", "grupo_edad", "dia_semana", "sms_recibido"],
                     ["Antelación (días)", "Grupo de edad", "Día de la cita", "SMS recibido"]):
    t = rate_table(d, c)
    x = np.arange(len(t))
    a.bar(x, t["tasa"], color="#C44E52", alpha=.85)
    a.errorbar(x, t["tasa"], yerr=[t["tasa"] - t["ic95_inf"], t["ic95_sup"] - t["tasa"]], fmt="none", c="k", lw=1)
    a.set_xticks(x); a.set_xticklabels([str(i)[:3] if c == "dia_semana" else str(i) for i in t.index],
                                      rotation=40 if c in ("antelacion_cat", "grupo_edad") else 0, fontsize=9)
    a.axhline(y_rate, ls="--", c="grey", lw=1); a.set_title(lab); a.set_xlabel("")
ax[0].set_ylabel("Tasa de no-show (IC 95 %)"); ax[0].yaxis.set_major_formatter(plt.matplotlib.ticker.PercentFormatter(1))
fig.suptitle("Fig. 2. Tasa de inasistencia por variable (línea = tasa global)", x=0.01, ha="left", fontweight="bold")
fig.tight_layout(); fig.savefig(FIG / "fig2_bivariado.png"); plt.show()
RESULTS["tasa_por_antelacion"] = rate_table(d, "antelacion_cat")["tasa"].round(3).to_dict()
RESULTS["tasa_por_edad"] = rate_table(d, "grupo_edad")["tasa"].round(3).to_dict()
RESULTS["tasa_por_sms"] = rate_table(d, "sms_recibido")["tasa"].round(3).to_dict()

# %% [markdown]
# ## 5. Análisis multivariado
# ### 5.1 Confusión: ¿el SMS "aumenta" la inasistencia? (paradoja de Simpson)
# El SMS solo se envía a citas con cierta antelación, que a su vez es el principal predictor del no-show.
# Se estratifica por antelación y se estima el OR ajustado de Mantel-Haenszel.

# %%
sms_by_lead = d.groupby("antelacion_cat", observed=True)["sms_recibido"].mean()
print("Proporción con SMS por antelación:\n", sms_by_lead.round(3).to_string())
ct = pd.crosstab(d["sms_recibido"], d["no_show"])
or_crudo = (ct.loc[1, 1] * ct.loc[0, 0]) / (ct.loc[1, 0] * ct.loc[0, 1])
d_sms = d[d["antelacion_dias"] >= 3]  # dominio donde el SMS es posible
or_mh, lo, hi = mantel_haenszel_or(d_sms, "sms_recibido", "no_show", "antelacion_dias")
print(f"OR crudo SMS = {or_crudo:.2f} | OR Mantel-Haenszel (estratos = días de antelación, ≥3 d) = {or_mh:.2f} [{lo:.2f}; {hi:.2f}]")
RESULTS["sms_or_crudo"] = round(float(or_crudo), 2)
RESULTS["sms_or_mh"] = [round(float(x), 2) for x in (or_mh, lo, hi)]
RESULTS["sms_min_antelacion"] = int(d.loc[d.sms_recibido == 1, "antelacion_dias"].min())

# %% [markdown]
# ### 5.2 Modelo logístico exploratorio (efectos ajustados)
# No es el modelo final: sirve para cuantificar asociaciones ajustadas mutuamente (OR con IC 95 %).

# %%
X = pd.DataFrame({
    "antelacion_10d": d["antelacion_dias"] / 10,
    "mismo_dia": d["mismo_dia"],
    "edad_10a": d["edad"] / 10,
    "sexo_F": (d["sexo"] == "F").astype(int),
    "subsidio": d["subsidio_bolsa_familia"],
    "hipertension": d["hipertension"], "diabetes": d["diabetes"],
    "alcoholismo": d["alcoholismo"], "discapacidad": d["discapacidad_bin"],
    "sms_recibido": d["sms_recibido"],
    "inasist_previas_ge1": (d["inasist_previas"] >= 1).astype(int),
    "sabado": (d["dia_semana"] == "Saturday").astype(int),
})
ors = logit_or_table(X, d["no_show"])
ors.to_csv(TAB / "logit_or_exploratorio.csv")
print(ors.round(3).to_string())
RESULTS["or_ajustados"] = ors[["OR", "ic95_inf", "ic95_sup", "p_valor"]].round(3).to_dict(orient="index")

# %%
fig, ax = plt.subplots(1, 3, figsize=(16, 4.2), gridspec_kw={"width_ratios": [1.1, 1, 1]})
corr = X.assign(no_show=d["no_show"]).corr(method="spearman")
sns.heatmap(corr, ax=ax[0], cmap="RdBu_r", center=0, vmin=-.6, vmax=.6, cbar_kws={"shrink": .7},
            xticklabels=True, yticklabels=True)
ax[0].set_title("Correlación de Spearman"); ax[0].tick_params(labelsize=7)
o = ors.sort_values("OR")
ax[1].errorbar(o["OR"], np.arange(len(o)), xerr=[o["OR"] - o["ic95_inf"], o["ic95_sup"] - o["OR"]],
               fmt="o", c="#C44E52", capsize=2)
ax[1].axvline(1, c="grey", ls="--"); ax[1].set_yticks(np.arange(len(o))); ax[1].set_yticklabels(o.index, fontsize=8)
ax[1].set_xscale("log"); ax[1].set_title("OR ajustados (IC 95 %, escala log)")
hist = d[d["citas_previas"] >= 1].copy()
hist["inasist_prev_cat"] = pd.cut(hist["inasist_previas"], [-1, 0, 1, 2, 100], labels=["0", "1", "2", "3+"])
t = rate_table(hist, "inasist_prev_cat")
ax[2].bar(t.index.astype(str), t["tasa"], color="#C44E52", alpha=.85)
ax[2].errorbar(np.arange(len(t)), t["tasa"], yerr=[t["tasa"] - t["ic95_inf"], t["ic95_sup"] - t["tasa"]], fmt="none", c="k")
ax[2].yaxis.set_major_formatter(plt.matplotlib.ticker.PercentFormatter(1))
ax[2].set_title("No-show según inasistencias previas\n(pacientes con ≥1 cita previa)"); ax[2].set_xlabel("Inasistencias previas")
fig.suptitle("Fig. 3. Análisis multivariado", x=0.01, ha="left", fontweight="bold")
fig.tight_layout(); fig.savefig(FIG / "fig3_multivariado.png"); plt.show()
RESULTS["tasa_por_inasist_previas"] = t["tasa"].round(3).to_dict()
RESULTS["n_con_historial"] = int(len(hist))

# %% [markdown]
# ### 5.3 Heterogeneidad territorial (funnel plot por barrio)
# Se contrasta la tasa por barrio contra los límites binomiales del 95 % y 99,8 % alrededor de la tasa global,
# para distinguir variación real de ruido por tamaño de muestra.

# %%
nb = rate_table(d, "barrio")
n_grid = np.linspace(max(5, nb["n"].min()), nb["n"].max(), 300)
fig, ax = plt.subplots(figsize=(7, 3.8))
for z, ls in [(1.96, "--"), (3.09, ":")]:
    se = np.sqrt(y_rate * (1 - y_rate) / n_grid)
    ax.plot(n_grid, y_rate + z * se, c="grey", ls=ls); ax.plot(n_grid, y_rate - z * se, c="grey", ls=ls)
out3 = (np.abs(nb["tasa"] - y_rate) > 3.09 * np.sqrt(y_rate * (1 - y_rate) / nb["n"]))
ax.scatter(nb["n"], nb["tasa"], s=14, c=np.where(out3, "#C44E52", "#4C72B0"))
ax.set_xscale("log"); ax.axhline(y_rate, c="k", lw=.8)
ax.yaxis.set_major_formatter(plt.matplotlib.ticker.PercentFormatter(1))
ax.set_xlabel("Citas por barrio (log)"); ax.set_ylabel("Tasa de no-show")
ax.set_title("Fig. 4. Funnel plot por barrio (rojo: fuera del límite 99,8 %)", loc="left", fontweight="bold")
fig.tight_layout(); fig.savefig(FIG / "fig4_funnel_barrio.png"); plt.show()
RESULTS["barrios_fuera_998"] = int(out3.sum()); RESULTS["n_barrios"] = int(len(nb))
print(nb[out3].sort_values("tasa").round(3).to_string())

# %% [markdown]
# ## 6. Suficiencia de los datos: línea base predictiva
# Validación cruzada agrupada por paciente (GroupKFold, k = 5) para evitar que citas de un mismo paciente queden
# en entrenamiento y prueba. Métricas: ROC-AUC, PR-AUC (referencia = prevalencia) y Brier.

# %%
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

feat_base = X.drop(columns=["inasist_previas_ge1"]).columns.tolist()
Xh = X.assign(citas_previas=d["citas_previas"], inasist_previas=d["inasist_previas"])
feat_hist = feat_base + ["citas_previas", "inasist_previas"]
y = d["no_show"].values; groups = d["paciente_id"].values
models = {
    "Regresión logística": lambda: make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000)),
    "Gradient boosting (HGB)": lambda: HistGradientBoostingClassifier(random_state=SEED, max_iter=300, learning_rate=.08),
}
res = []
for fs_name, cols in [("Sin historial", feat_base), ("Con historial del paciente", feat_hist)]:
    for m_name, mk in models.items():
        sc = {"roc": [], "pr": [], "brier": [], "recall_top30": []}
        for tr, te in GroupKFold(n_splits=5).split(Xh, y, groups):
            m = mk().fit(Xh.iloc[tr][cols], y[tr]); p = m.predict_proba(Xh.iloc[te][cols])[:, 1]
            sc["roc"].append(roc_auc_score(y[te], p)); sc["pr"].append(average_precision_score(y[te], p))
            sc["brier"].append(brier_score_loss(y[te], p))
            top = p >= np.quantile(p, 0.70)  # contactar el 30 % de citas con mayor riesgo
            sc["recall_top30"].append(y[te][top].sum() / y[te].sum())
        res.append({"variables": fs_name, "modelo": m_name,
                    **{f"{k}_media": np.mean(v) for k, v in sc.items()}, **{f"{k}_de": np.std(v) for k, v in sc.items()}})
base = pd.DataFrame(res); base.to_csv(TAB / "linea_base_cv.csv", index=False)
print(base.round(4).to_string(index=False))
print(f"Referencia PR-AUC (clasificador aleatorio) = prevalencia = {y.mean():.3f}; Brier de predecir la prevalencia = {y.mean()*(1-y.mean()):.3f}")
RESULTS["linea_base"] = base.round(4).to_dict(orient="records")

# %% [markdown]
# ## 7. Hallazgos y guardado de resultados
# Ver interpretación en el reporte ejecutivo (`reports/Entrega1_Reporte.pdf`).

# %%
with open(TAB / "resultados_eda.json", "w", encoding="utf-8") as f:
    json.dump(RESULTS, f, ensure_ascii=False, indent=1, default=str)
print(json.dumps(RESULTS, ensure_ascii=False, indent=1, default=str)[:3000])
