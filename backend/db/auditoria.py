"""Tablas maestras, triggers de auditoría y controles que solo PostgreSQL ofrece.

Este módulo es la fuente única de lo que el esquema declarativo (`models_sqlalchemy`) no
puede expresar:

* **Tablas maestras** (`cat_evento`, `departamento`, `secretaria`, `cie10`): se siembran de
  forma idempotente al arrancar y se copian al script SQL de reconstrucción.
* **Triggers de tiempos**: `actualizado_en` lo escribe la base de datos, no la aplicación.
* **Bitácora de cambios** (`auditoria_cambio`): quién, cuándo, qué tabla, qué registro, de qué
  caso (también en las tablas hijas) y qué columnas cambiaron. No copia valores: los datos de
  pacientes no se duplican en la bitácora.
* **Trazabilidad de la carga**: una fila de `api_sivigilaimportacion` solo puede apuntar a un
  caso que exista en la tabla que corresponde a su `tipo`.

Todo es idempotente (`CREATE OR REPLACE`, `DROP TRIGGER IF EXISTS`, `ON CONFLICT`).
"""

import logging
from collections.abc import Iterator
from pathlib import Path

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

# Tablas que registran cambios en la bitácora y cómo se llega a su caso:
#   (tabla, llave primaria, evento, modo, argumentos)
#   - 'directo':    el caso es una columna de la fila (args: columna).
#   - 'exclusivo':  dos columnas excluyentes, una por evento (args: col_morbilidad, col_mortalidad).
#   - 'padre':      el caso está en la tabla padre (args: fk de la fila, tabla padre, pk del padre).
#   - 'ninguno':    la fila no pertenece a un caso (pacientes, usuarios, análisis).
TABLAS_AUDITADAS: tuple[tuple[str, str, str, str, tuple[str, ...]], ...] = (
    ('paciente', 'id_paciente', '', 'ninguno', ()),
    ('caso_morbilidad', 'id_caso', 'morbilidad', 'directo', ('id_caso',)),
    ('caso_mortalidad', 'id_caso', 'mortalidad', 'directo', ('id_caso',)),
    (
        'antecedente_obstetrico',
        'id',
        '',
        'exclusivo',
        ('caso_morbilidad_id', 'caso_mortalidad_id'),
    ),
    ('antecedente_obstetrico_morbilidad', 'id_antecedente', 'morbilidad', 'directo', ('id_caso',)),
    ('antecedente_materno_mortalidad', 'id_caso', 'mortalidad', 'directo', ('id_caso',)),
    ('control_prenatal', 'id_caso', 'mortalidad', 'directo', ('id_caso',)),
    ('causas_morbilidad', 'id_causa', 'morbilidad', 'directo', ('id_caso',)),
    ('causa_asociada_morbilidad', 'id', 'morbilidad', 'directo', ('id_caso',)),
    (
        'referencia_institucion',
        'id',
        'morbilidad',
        'padre',
        ('id_referencia', 'referencia', 'id_referencia'),
    ),
    (
        'cirugia_adicional_morbilidad',
        'id',
        'morbilidad',
        'padre',
        ('id_manejo', 'manejo_hospitalario', 'id_manejo'),
    ),
    ('causa_muerte', 'id_caso', 'mortalidad', 'directo', ('id_caso',)),
    ('api_analisis', 'id', '', 'ninguno', ()),
    ('api_usuario', 'id', '', 'ninguno', ()),
)

# Cirugías adicionales de la ficha 549 (variable 7.3): tabla maestra de la plataforma.
TIPOS_CIRUGIA: tuple[tuple[int, str], ...] = (
    (1, 'Histerectomía'),
    (2, 'Laparotomía'),
    (3, 'Legrado'),
    (4, 'Otra'),
)

SEMILLAS = Path(__file__).resolve().parent / 'semillas_catalogos.sql'

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
    # Bitácora: operación, registro, caso y NOMBRES de columnas modificadas (sin valores).
    # Argumentos: pk, evento, modo y los argumentos del modo (ver TABLAS_AUDITADAS).
    """
CREATE OR REPLACE FUNCTION fn_auditar() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    pk     text := TG_ARGV[0];
    evento text := NULLIF(TG_ARGV[1], '');
    modo   text := TG_ARGV[2];
    fila   jsonb;
    reg    text;
    caso   integer;
    cols   jsonb;
BEGIN
    IF TG_OP = 'DELETE' THEN
        fila := to_jsonb(OLD);
    ELSE
        fila := to_jsonb(NEW);
    END IF;
    reg := fila ->> pk;

    IF modo = 'directo' THEN
        caso := (fila ->> TG_ARGV[3])::integer;
    ELSIF modo = 'exclusivo' THEN
        IF fila ->> TG_ARGV[3] IS NOT NULL THEN
            evento := 'morbilidad';
            caso := (fila ->> TG_ARGV[3])::integer;
        ELSE
            evento := 'mortalidad';
            caso := (fila ->> TG_ARGV[4])::integer;
        END IF;
    ELSIF modo = 'padre' THEN
        -- Si el padre ya no existe (borrado en cascada), el caso queda NULL.
        EXECUTE format('SELECT id_caso FROM %I WHERE %I = $1', TG_ARGV[4], TG_ARGV[5])
            INTO caso USING (fila ->> TG_ARGV[3])::integer;
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

    INSERT INTO auditoria_cambio
        (tabla, registro_id, operacion, columnas_modificadas, usuario_bd, evento, id_caso)
    VALUES (TG_TABLE_NAME, reg, TG_OP, cols::json, current_user, evento, caso);
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
    for tabla, pk, evento, modo, args in TABLAS_AUDITADAS:
        argumentos = ', '.join(_comillas(a) for a in (pk, evento, modo, *args))
        sentencias.append(f'DROP TRIGGER IF EXISTS trg_auditoria ON {tabla}')
        sentencias.append(
            f'CREATE TRIGGER trg_auditoria AFTER INSERT OR UPDATE OR DELETE ON {tabla} '
            f'FOR EACH ROW EXECUTE FUNCTION fn_auditar({argumentos})'
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
    for id_tipo, descripcion in TIPOS_CIRUGIA:
        yield (
            f'INSERT INTO cat_tipo_cirugia (id, descripcion) VALUES ({id_tipo}, '
            f'{_comillas(descripcion)}) ON CONFLICT (id) DO UPDATE SET descripcion = '
            'EXCLUDED.descripcion'
        )
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


def sentencias_semillas() -> list[tuple[str, str]]:
    """(tabla, INSERT) de cada catálogo de `semillas_catalogos.sql`."""
    # Primero se quitan los comentarios (pueden llevar «;») y luego se separan las sentencias.
    lineas = SEMILLAS.read_text(encoding='utf-8').splitlines()
    sin_comentarios = '\n'.join(ln for ln in lineas if not ln.lstrip().startswith('--'))
    resultado: list[tuple[str, str]] = []
    for bloque in sin_comentarios.split(';'):
        sentencia = bloque.strip()
        if sentencia:
            resultado.append((sentencia.split()[2], sentencia))
    return resultado


def _sembrar_catalogos_vacios(conn) -> None:
    """Carga los catálogos que estén vacíos (una base creada solo por el arranque).

    No toca un catálogo que ya tenga filas: los valores de una base existente se respetan.
    """
    for tabla, sentencia in sentencias_semillas():
        if conn.execute(text(f'SELECT NOT EXISTS (SELECT 1 FROM {tabla})')).scalar():
            conn.execute(text(sentencia))


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
            _sembrar_catalogos_vacios(conn)
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
