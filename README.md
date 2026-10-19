# NeuroAgenda — Predicción del riesgo de inasistencia a citas

Proyecto final de **MINE-4101 Ciencia de Datos Aplicada** (Universidad de los Andes, 2026-20), metodología ASUM-DM.

**Repositorio:** https://github.com/Juliethr3/neuroagenda-minhalma

**Integrantes:** Julieth Dayanna Rodriguez Animero
**Organización aliada:** MinHalma (centro ambulatorio de psicología, nutrición y fisioterapia) · **Stakeholder:** _[nombre y cargo]_

## Alcance

Producto de datos que estima, al agendar y 72 h antes de la cita, la probabilidad de que un paciente no asista a consulta ambulatoria de psicología, nutrición o fisioterapia, para focalizar confirmaciones y reasignar cupos. Componentes: (1) modelo de ML calibrado y explicable, (2) API REST, (3) dashboard operativo, (4) integración opcional con mensajería.

La **Entrega 1** cubre entendimiento del negocio, ideación, ética, enfoque analítico, recolección y entendimiento de los datos, usando un conjunto público como proxy mientras se formaliza el acceso a datos de MinHalma.

## Principales hallazgos (Entrega 1)

- Tasa de inasistencia del conjunto proxy: **20,2 %** (110.521 citas válidas, 62.299 pacientes).
- **La antelación es el predictor más fuerte**: 4,6 % de inasistencia en citas del mismo día frente a 30–34 % con 8 a 60 días.
- **Paradoja de Simpson en el SMS**: el OR crudo es 1,90, pero al estratificar por antelación es **0,77 [0,74–0,80]**, es decir, el recordatorio protege.
- El historial de inasistencias del paciente (calculado sin fuga temporal) es un predictor independiente (OR ≈ 1,44).
- Una línea base sin optimizar alcanza **ROC-AUC 0,733** con validación cruzada agrupada por paciente; contactar el 30 % de mayor riesgo capturaría ≈ 53 % de los no-show.

## Organización del repositorio

```
├── data/raw/KaggleV2-May-2016.csv      # Datos crudos (no se modifican)
├── docs/diccionario_datos.md            # Diccionario de datos de las 3 fuentes
├── notebooks/
│   ├── 01_eda_calidad.ipynb             # EDA y calidad de datos (ejecutado, con salidas)
│   └── 01_eda_calidad.py                # Misma lógica en formato script (percent / jupytext)
├── src/
│   ├── utils.py                         # Funciones estadísticas (Wilson, Cramér, Mantel-Haenszel, OR logísticos)
│   ├── mockup.py                        # Genera el mockup del dashboard
│   └── build_report.py                  # Genera el reporte a partir de los resultados del EDA
├── mockup/mockup_dashboard.png
├── reports/
│   ├── Entrega1_Reporte.pdf / .docx     # Reporte ejecutivo (≤ 6 páginas, Arial 12)
│   ├── figures/                         # Figuras del EDA
│   └── tables/                          # Tablas de calidad, pruebas, OR, línea base y resultados_eda.json
├── USO_IA.md                            # Declaración de uso de IA
└── requirements.txt
```

## Instrucciones de ejecución

Requiere Python ≥ 3.10.

```bash
pip install -r requirements.txt
cd notebooks && jupyter nbconvert --to notebook --execute --inplace 01_eda_calidad.ipynb   # 1. EDA (≈ 30 s)
cd .. && python src/mockup.py                                                              # 2. Mockup
python src/build_report.py                                                                 # 3. Reporte (.docx)
```

El orden importa: `build_report.py` lee `reports/tables/resultados_eda.json`, que genera el notebook. Semilla fija `42`.

## Fuente de datos

Hoppen, J. (2016). *Medical Appointment No Shows* [Conjunto de datos]. Kaggle. https://www.kaggle.com/datasets/joniarroba/noshowappointments. Datos públicos y anonimizados, usados con fines académicos.
