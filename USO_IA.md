# Declaración de uso de inteligencia artificial

**Herramienta:** Claude (Anthropic), modelo Claude Opus 5.5, usado como asistente agéntico en claude.ai.

## Partes del proyecto en las que se usó IA

| Actividad | Uso de IA | Revisión humana |
|---|---|---|
| Ideación | Generación y comparación de alternativas de proyecto según disponibilidad de datos y perfil del equipo | Selección final del problema por el equipo |
| Búsqueda de contexto | Búsqueda web de cifras de inasistencia en Colombia y literatura (Dantas et al., 2018; Salazar et al., 2022) | Verificación de fuentes citadas |
| Implementación | Redacción del código del EDA (`notebooks/01_eda_calidad.py`, `src/utils.py`), del mockup y del generador del reporte | Revisión del código y de los resultados |
| Control de calidad | Detección y corrección de una fuga temporal en las variables de historial del paciente | Validación metodológica |
| Interpretación | Borrador de la interpretación estadística (paradoja de Simpson en SMS, tamaños de efecto) | Validación con el criterio del equipo |
| Documentación | Borrador del reporte ejecutivo, diccionario de datos y README | Edición y aprobación final |

## Prompts más relevantes

1. "Qué ideas potenciales a convertir en un negocio puedes ayudarme a crear [...] enfocándome en mi área de neurociencia, relacionado con análisis de datos."
2. "Desarrollemos la idea 2: Predicción de inasistencia a citas en consulta de neurología o salud mental" (desarrollo de la Entrega 1 completa siguiendo el enunciado del curso).

## Flujo de trabajo

El asistente descargó el conjunto de datos, ejecutó el EDA de forma iterativa (ejecución → revisión de resultados → corrección), generó figuras y tablas, y construyó el reporte leyendo los resultados del notebook para evitar errores de transcripción. Todas las cifras del reporte son reproducibles ejecutando el notebook.
