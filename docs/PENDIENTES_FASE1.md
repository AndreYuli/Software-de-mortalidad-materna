# Pendientes de la Fase 1 (corregir y simplificar el Análisis)

Fecha: 2026-09-20
Plan: `docs/superpowers/plans/2026-09-20-analisis-fase1-corregir-simplificar.md`
Spec: `docs/superpowers/specs/2026-09-20-analisis-fase1-corregir-simplificar-design.md`

## Estado

Hecho y commiteado: Tareas 2, 4, 5, 6, 7, 8 y 9, más el script de la Tarea 1 y el cargador de la Tarea 3.
Verificado: `tsc -b` sin errores, `vite build` correcto, 208 tests del frontend en verde, 8 tests del generador en verde.

## Cerrado el 2026-09-21

- Casos reiniciados (copia CSV en `data/local/backup_<fecha>/`, usuarios 6 -> 6) y datos realistas cargados: `caso_mortalidad` = 60, `caso_morbilidad` = 3000.
- Proporciones: `O14.1` primero en ambos eventos (mortalidad 25,0 %; morbilidad 27,1 %).
- Revisión visual a 1440 y 390 px: KPIs 60 / 3.000 / 50,0:1 / 2,0 %, vino y ámbar, mayor arriba, panel de IA plegado con aviso, filtros sin "Día" y sin sticky.
- Corregido en la revisión: el generador usaba textos de sitio de defunción que no están en el catálogo (la carga daba 500); las etiquetas `n (%)` no salían porque `/completo/` no devuelve `total_registros` (ahora el total sale de `estadisticas_basicas.total_casos`); en móvil el eje Y de las causas se recortaba u omitía etiquetas.
- Mortalidad usa reparto proporcional exacto de causas: con 60 casos, `random.choices` dejaba a `O14.1` fuera del primer lugar.

## Pendiente

- Capturas móviles: la cabecera móvil (hamburguesa) aparece a mitad de la página en capturas `fullPage`; parece un efecto de la captura (posición fija), no verificado con scroll real.
- Anotar qué sigue sobrando ("sopa"): decisión tuya tras ver la pantalla.

## Decisiones abiertas

- Nombre "Índice de mortalidad" (antes "Tasa de letalidad"): validar con quien conozca los lineamientos del INS, porque el informe oficial usa "índice de letalidad" en el contexto de la MME.
- Quitar "Día de Reporte" y el `sticky` de la barra de filtros son decisiones mías del spec (marcadas ⚠); se pueden revertir.

## Notas

- Se corrigió `_fecha_nacimiento_para_edad` en `backend/scripts/generar_excels_prueba.py` (fallaba con el 29 de febrero).
- ESLint marca 5 errores `no-explicit-any` en `useDashboardCharts.ts`; ya existían antes de esta fase.
- Los cambios del chatbot (`PLAN_CHATBOT.md`, `ia-service/*`, etc.) siguen sin commitear y no se tocaron.
