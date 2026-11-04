# Cambios de la corrección al aval condicionado (3-nov-2026)

Rama `correccion/aval-condicionado` (16 commits, último `a520cdbf`). Sin push ni despliegue.
Pruebas al cierre: back 228 (+2 omitidas), IA 24, front 247, e2e Playwright 23/23.
Fuente: `git log` de la rama. Los pendientes están en `PENDIENTES_CORRECCION_AVAL.md`.

## Base de datos y carga
| Commit | Cambio |
|---|---|
| `68473289` | Normalización a 1FN: tablas hijas `causa_asociada_morbilidad`, `referencia_institucion` y `cirugia_adicional_morbilidad` |
| `86e50448` | Errores de base de datos traducidos y reglas de valor validadas con número de fila |
| `148f7336` | Se valida formato y existencia de los códigos CIE-10 de morbilidad; «—» ya no se guarda como causa |

## Seguridad
| Commit | Cambio |
|---|---|
| `ae76d5d9` | Contraseñas más estrictas, nombre sin HTML, filtros de fecha validados (422, no 500) |
| `dd6e2feb` | Límite de 10 intentos / 15 min y tiempo de espera de la IA configurable. La contraseña mínima se subió a 15 (NIST SP 800-63B-4) y el 4-nov se volvió a **8** (ver «Cambios posteriores») |
| `8ab6a1a1` | La prueba e2e HU-01 usa una contraseña de 15+ caracteres (sigue siendo válida con mínimo 8) |

## IA y narrativas
| Commit | Cambio |
|---|---|
| `bed0c6c2` | Verificación automática de narrativas (cifras y coherencia) y aviso visible si la IA no responde |
| `3b10715d` | Diagnóstico del 404 del proveedor; el detalle del proveedor ya no llega al usuario |
| `f34827fa` | El verificador acepta cifras truncadas y los años/meses que son claves de los indicadores |
| `a520cdbf` | El verificador lee «6.065» también como decimal |
| `cbd0122a` | La narrativa de agrupamiento respondía 500 siempre (faltaba pasar la sesión de BD) |

## Análisis, dashboard y exportes
| Commit | Cambio |
|---|---|
| `ba49bad7` | Índice cuantitativo de relevancia bibliográfica de variables, con trazabilidad variable-artículo |
| `b420feb9` | Se versionan los CSV de relevancia que faltaban y se corrige «seis» por «cinco» |
| `c6baae6d` | Hoja y CSV de causas CIE-10 con código real, evento y porcentaje del dashboard |
| `1e8fe321` | «Última carga» pasa a «Última semana reportada» |
| `29e6ca08` | Autocompletado de credenciales y concordancia de número en el historial de cargas |

## Cambios posteriores (4-nov-2026, sin commit)
- Contraseña mínima de **8** caracteres (antes 15): `backend/schemas/user_schema.py`, `frontend/.../registerSchema.ts`, `Register.tsx`, `Register.test.tsx` y `backend/tests/test_revision_uso_api.py`. Back: 227 pruebas aprobadas (+2 omitidas); front, las 20 de `components/auth`.

## Fuera del repositorio (en `Proyecto de grado`)
- `CARACT_corregido (5).docx` (copia del (4); contraseña vuelve a 8) y (4) (copia del (3)), `Carta_de_Respuesta_corregida (3).docx`
- `respuesta_a_la_matriz_de_la_asesora_3-nov_v2.txt`
- Figura 4 v2: `Diagramas\figuras_nuevas\fig4_v2.py`
