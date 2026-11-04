"""Tablas maestras, triggers de auditoría y controles que solo PostgreSQL ofrece.

Este módulo es la fuente única de lo que el esquema declarativo (`models_sqlalchemy`) no
puede expresar:

* **Tablas maestras** (`cat_evento`, `departamento`, `secretaria`, `cie10`): se siembran de
  forma idempotente al arrancar y se copian al script SQL de reconstrucción.
* **Triggers de tiempos**: `actualizado_en` lo escribe la base de datos, no la aplicación.
* **Bitácora de cambios** (`auditoria_cambio`): quién, cuándo, qué tabla, qué registro y qué
  columnas cambiaron. No copia valores: los datos de pacientes no se duplican en la bitácora.
* **Trazabilidad de la carga**: una fila de `api_sivigilaimportacion` solo puede apuntar a un
  caso que exista en la tabla que corresponde a su `tipo`.

Todo es idempotente (`CREATE OR REPLACE`, `DROP TRIGGER IF EXISTS`, `ON CONFLICT`).
"""

import logging
from collections.abc import Iterator

from sqlalchemy import text
from sqlalchemy.engine import Engine

from core.tenant import DEPARTAMENTOS
from utils.cie10 import _cargar_cie10

logger = logging.getLogger(__name__)

EVENTOS: tuple[tuple[str, str], ...] = (
    ('mortalidad', 'Mortalidad materna (ficha 550)'),
    ('morbilidad', 'Morbilidad materna extrema (ficha 549)'),
)

# Tablas con `actualizado_en` mantenido por trigger.
TABLAS_CON_ACTUALIZADO_EN: tuple[str, ...] = (
    'paciente',
    'caso_morbilidad',
    'caso_mortalidad',
    'api_analisis',
    'api_usuario',
)

# Tablas que registran cambios en la bitácora: (tabla, columna de llave primaria).
TABLAS_AUDITADAS: tuple[tuple[str, str], ...] = (
    ('paciente', 'id_paciente'),
    ('caso_morbilidad', 'id_caso'),
    ('caso_mortalidad', 'id_caso'),
    ('antecedente_obstetrico', 'id'),
    ('causas_morbilidad', 'id_causa'),
    ('causa_muerte', 'id_caso'),
    ('api_analisis', 'id'),
    ('api_usuario', 'id'),
)

SQL_FUNCIONES: tuple[str, ...] = (
    # Marca de tiempo de la última modificación (la base de datos, no la aplicación).
    """
CREATE OR REPLACE FUNCTION fn_actualizado_en() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    NEW.actualizado_en := now();
    RETURN NEW;
END;
$$
""",
    # Bitácora: operación, registro y NOMBRES de columnas modificadas (sin valores).
    """
CREATE OR REPLACE FUNCTION fn_auditar() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    pk   text := TG_ARGV[0];
    reg  text;
    cols jsonb;
BEGIN
    IF TG_OP = 'DELETE' THEN
        reg := to_jsonb(OLD) ->> pk;
    ELSE
        reg := to_jsonb(NEW) ->> pk;
    END IF;

    IF TG_OP = 'UPDATE' THEN
        SELECT jsonb_agg(n.key ORDER BY n.key) INTO cols
        FROM jsonb_each(to_jsonb(NEW)) AS n(key, value)
        JOIN jsonb_each(to_jsonb(OLD)) AS o(key, value) ON o.key = n.key
        WHERE n.value IS DISTINCT FROM o.value AND n.key <> 'actualizado_en';
        IF cols IS NULL THEN
            RETURN NULL;  -- UPDATE sin cambios reales: no se registra
        END IF;
    END IF;

    INSERT INTO auditoria_cambio (tabla, registro_id, operacion, columnas_modificadas, usuario_bd)
    VALUES (TG_TABLE_NAME, reg, TG_OP, cols::json, current_user);
    RETURN NULL;
END;
$$
""",
    # La importación apunta a un caso de mortalidad o de morbilidad según su `tipo`.
    """
CREATE OR REPLACE FUNCTION fn_importacion_caso() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.tipo = 'mortalidad' THEN
        IF NOT EXISTS (SELECT 1 FROM caso_mortalidad WHERE id_caso = NEW.caso_id) THEN
            RAISE EXCEPTION 'importacion: caso % inexistente en caso_mortalidad', NEW.caso_id
                USING ERRCODE = 'foreign_key_violation';
        END IF;
    ELSIF NEW.tipo = 'morbilidad' THEN
        IF NOT EXISTS (SELECT 1 FROM caso_morbilidad WHERE id_caso = NEW.caso_id) THEN
            RAISE EXCEPTION 'importacion: caso % inexistente en caso_morbilidad', NEW.caso_id
                USING ERRCODE = 'foreign_key_violation';
        END IF;
    END IF;
    RETURN NEW;
END;
$$
""",
)


def sentencias_triggers() -> list[str]:
    """Sentencias que crean (o recrean) los triggers sobre las tablas del esquema."""
    sentencias: list[str] = []
    for tabla in TABLAS_CON_ACTUALIZADO_EN:
        sentencias.append(f'DROP TRIGGER IF EXISTS trg_actualizado_en ON {tabla}')
        sentencias.append(
            f'CREATE TRIGGER trg_actualizado_en BEFORE UPDATE ON {tabla} '
            'FOR EACH ROW EXECUTE FUNCTION fn_actualizado_en()'
        )
    for tabla, pk in TABLAS_AUDITADAS:
        sentencias.append(f'DROP TRIGGER IF EXISTS trg_auditoria ON {tabla}')
        sentencias.append(
            f'CREATE TRIGGER trg_auditoria AFTER INSERT OR UPDATE OR DELETE ON {tabla} '
            f"FOR EACH ROW EXECUTE FUNCTION fn_auditar('{pk}')"
        )
    sentencias.append('DROP TRIGGER IF EXISTS trg_importacion_caso ON api_sivigilaimportacion')
    sentencias.append(
        'CREATE TRIGGER trg_importacion_caso BEFORE INSERT OR UPDATE ON api_sivigilaimportacion '
        'FOR EACH ROW EXECUTE FUNCTION fn_importacion_caso()'
    )
    return sentencias


def codigos_cie10() -> list[tuple[str, str]]:
    """Códigos de la tabla de referencia CIE-10, ordenados.

    Además de los códigos de 4 caracteres (O141), incluye la categoría de 3 (O14) cuando la
    referencia solo trae su forma «O14X»: la carga acepta la categoría y la guarda tal cual.
    """
    ref = _cargar_cie10()
    filas = dict(ref)
    for codigo, nombre in ref.items():
        if len(codigo) == 4 and codigo.endswith('X'):
            filas.setdefault(codigo[:3], nombre)
    return sorted(filas.items())


def _comillas(valor: str) -> str:
    return "'" + valor.replace("'", "''") + "'"


def sentencias_maestras() -> Iterator[str]:
    """Genera los INSERT idempotentes de las tablas maestras."""
    for codigo, nombre in EVENTOS:
        yield (
            f'INSERT INTO cat_evento (codigo, nombre) VALUES ({_comillas(codigo)}, '
            f'{_comillas(nombre)}) ON CONFLICT (codigo) DO UPDATE SET nombre = EXCLUDED.nombre'
        )
    for dep in DEPARTAMENTOS:
        yield (
            f'INSERT INTO departamento (codigo, nombre) VALUES ({_comillas(dep.codigo)}, '
            f'{_comillas(dep.nombre)}) ON CONFLICT (codigo) DO UPDATE SET nombre = EXCLUDED.nombre'
        )
        for sec in dep.secretarias:
            yield (
                'INSERT INTO secretaria (codigo, nombre, departamento_codigo) VALUES '
                f'({_comillas(sec.codigo)}, {_comillas(sec.nombre)}, {_comillas(dep.codigo)}) '
                'ON CONFLICT (codigo) DO UPDATE SET nombre = EXCLUDED.nombre, '
                'departamento_codigo = EXCLUDED.departamento_codigo'
            )


def sentencia_cie10_por_lotes(tamano: int = 500) -> Iterator[str]:
    """Genera INSERT por lotes de la tabla `cie10` (idempotentes)."""
    filas = codigos_cie10()
    for i in range(0, len(filas), tamano):
        valores = ', '.join(f'({_comillas(c)}, {_comillas(n)})' for c, n in filas[i : i + tamano])
        yield (
            f'INSERT INTO cie10 (codigo, descripcion) VALUES {valores} '
            'ON CONFLICT (codigo) DO NOTHING'
        )


def aplicar_auditoria_y_maestras(engine: Engine) -> None:
    """Siembra las tablas maestras y crea funciones y triggers (solo PostgreSQL).

    En otros motores (las pruebas usan SQLite) no hace nada: los triggers usan PL/pgSQL.
    Nunca lanza: un fallo se registra para no impedir que la aplicación levante.
    """
    if engine.dialect.name != 'postgresql':
        return
    try:
        with engine.begin() as conn:
            # text() escapa el «%» (20 descripciones del CIE-10 lo llevan); ninguna lleva «:».
            for sentencia in sentencias_maestras():
                conn.execute(text(sentencia))
            total = conn.execute(text('SELECT count(*) FROM cie10')).scalar() or 0
            if total < len(codigos_cie10()):
                for sentencia in sentencia_cie10_por_lotes():
                    conn.execute(text(sentencia))
            for funcion in SQL_FUNCIONES:
                conn.execute(text(funcion))
            for sentencia in sentencias_triggers():
                conn.execute(text(sentencia))
    except Exception:
        logger.exception('No se pudieron aplicar las tablas maestras ni los triggers.')
