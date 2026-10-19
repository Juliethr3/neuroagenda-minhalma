# Diccionario de datos

## Fuente 1 — *Medical Appointment No Shows* (conjunto proxy)

- **Origen:** Hoppen, J. (2016). Kaggle. <https://www.kaggle.com/datasets/joniarroba/noshowappointments>
- **Contexto:** citas ambulatorias del sistema público de salud de Vitória (Espírito Santo, Brasil).
- **Archivo:** `data/raw/KaggleV2-May-2016.csv` (CSV, separador coma, UTF-8, 10,7 MB, MD5 `cc55525de6e2b615aeba50095e8aaa95`).
- **Volumen:** 110.527 citas × 14 atributos, 62.299 pacientes. Citas del 2016-04-29 al 2016-06-08; agendamientos desde 2015-11-10.
- **Granularidad:** una fila = una cita.

| # | Atributo original | Nombre en el proyecto | Tipo | Dominio / formato | Descripción | Calidad observada |
|---|---|---|---|---|---|---|
| 1 | PatientId | paciente_id | ID (float) | ~10¹⁴ | Identificador seudonimizado del paciente | 5 valores no enteros (corrupción de precisión al exportar como float) |
| 2 | AppointmentID | cita_id | ID (int) | único | Identificador de la cita | Sin duplicados |
| 3 | Gender | sexo | Categórica | F, M | Sexo registrado | Completo |
| 4 | ScheduledDay | fecha_agendamiento | Fecha-hora UTC | ISO 8601 | Momento en que se agendó la cita | Completo |
| 5 | AppointmentDay | fecha_cita | Fecha | ISO 8601, hora siempre 00:00 | Día de la cita | **Sin hora**: no permite modelar franja horaria |
| 6 | Age | edad | Entera | −1 a 115 | Edad en años | 1 valor negativo (excluido); 7 > 100 (marcados) |
| 7 | Neighbourhood | barrio | Categórica | 81 niveles | Barrio de la unidad de atención | Alta cardinalidad: requiere codificación por objetivo o agrupación |
| 8 | Scholarship | subsidio_bolsa_familia | Binaria | 0/1 | Beneficiario del programa Bolsa Família (proxy socioeconómico) | Completo; variable sensible para equidad |
| 9 | Hipertension | hipertension | Binaria | 0/1 | Hipertensión registrada | Dato de salud (sensible) |
| 10 | Diabetes | diabetes | Binaria | 0/1 | Diabetes registrada | Dato de salud (sensible) |
| 11 | Alcoholism | alcoholismo | Binaria | 0/1 | Alcoholismo registrado | Dato de salud mental (sensible) |
| 12 | Handcap | discapacidad | Entera | 0–4 | Número de discapacidades (no binaria) | 199 casos > 1 |
| 13 | SMS_received | sms_recibido | Binaria | 0/1 | Se envió ≥ 1 SMS de recordatorio | Solo se envía con antelación ≥ 3 días |
| 14 | No-show | no_show | Binaria (objetivo) | Yes/No → 1/0 | 1 = el paciente **no** asistió | Prevalencia 20,2 % |

### Variables derivadas para el EDA

| Variable | Definición | Nota metodológica |
|---|---|---|
| antelacion_dias | `fecha_cita − fecha_agendamiento` (en días calendario) | 5 valores negativos excluidos |
| mismo_dia | `antelacion_dias == 0` | 34,9 % de las citas |
| antelacion_cat | Cortes 0, 1–2, 3–7, 8–14, 15–30, 31–60, 61+ | Para tasas e IC |
| grupo_edad | 0–11, 12–17, 18–29, 30–44, 45–59, 60–74, 75+ | Etapas del ciclo vital |
| dia_semana | Día de la semana de la cita | Sábado: n muy bajo |
| discapacidad_bin | `discapacidad > 0` | Se conserva también el conteo |
| citas_previas, inasist_previas | Citas del paciente cuya **fecha** es anterior al día del agendamiento actual, y cuántas fueron no-show | Sin fuga temporal: solo usa desenlaces ya conocidos al momento de predecir |

## Fuente 2 — Sistema de agendamiento de MinHalma (Entrega 2, por solicitar)

| Atributo | Tipo | Justificación |
|---|---|---|
| id_cita, id_paciente (seudónimo) | ID | Agrupación, historial |
| fecha_hora_agendamiento, fecha_hora_cita | Fecha-hora | Antelación y franja horaria |
| servicio (psicología, nutrición, fisioterapia), tipo (primera vez / control / n.º de sesión del plan) | Categórica | Riesgo diferencial por servicio |
| profesional (seudónimo), sede, modalidad (presencial / teleconsulta) | Categórica | Efectos de proveedor y canal |
| canal de agendamiento (teléfono, web, presencial) | Categórica | Compromiso del paciente |
| estado final (asistió / canceló con aviso / no asistió) | Categórica | Variable objetivo y cancelaciones |
| edad, sexo, régimen (contributivo/subsidiado), municipio | Mixta | Riesgo y auditoría de equidad |
| recordatorios enviados (canal, fecha) | Evento | Evaluar intervención |

Se excluyen explícitamente diagnósticos, notas clínicas y cualquier dato de la historia clínica (minimización, Ley 1581 de 2012).

## Fuente 3 — Calendario de festivos de Colombia

Fecha y tipo de festivo; permite crear variables de puente festivo y cercanía a festivos.
