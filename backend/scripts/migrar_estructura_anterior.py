r"""Migra los datos de una base con la estructura anterior (rama `main`) a una base NUEVA.

La base de ORIGEN no se modifica: se abre en modo de solo lectura y queda como respaldo y
referencia. Los datos se copian a una base de DESTINO creada con el script actual
(`sivigila_maternidad_postgres.sql`), conservando los identificadores (casos, pacientes,
análisis, importaciones), de modo que todas las relaciones se mantienen.

Uso (desde `backend/`), ver docs/MIGRACION_BD.md:

    python scripts/migrar_estructura_anterior.py --origen sivigila_maternidad \\
        --destino sivigila_maternidad_v2 --simular
    python scripts/migrar_estructura_anterior.py --origen sivigila_maternidad \\
        --destino sivigila_maternidad_v2 --confirmar [--correcciones correcciones_cie10.csv]

Conexión: --host/--port/--usuario (por defecto DB_HOST/DB_PORT/DB_USER) y la contraseña en
PGPASSWORD o DB_PASSWORD. Nada se borra en ninguna de las dos bases.

* `--simular`: hace toda la copia y las validaciones dentro de una transacción y al final la
  DESHACE. Solo quedan los informes.
* `--confirmar`: exige un respaldo previo con `pg_dump` (se crea y se verifica con
  `pg_restore --list`) y confirma la transacción solo si todas las validaciones pasan.

Reglas de datos:
* Los CIE-10 se normalizan (mayúsculas, sin punto ni espacios) antes de relacionarlos con el
  catálogo `cie10`. Vacíos y guiones («—») se tratan como «sin dato».
* Un CIE-10 OBLIGATORIO (causa principal de morbilidad, causa básica de mortalidad) que no
  exista en el catálogo DETIENE la migración. Se corrige en el origen o con un archivo de
  correcciones (`tabla,columna,id_caso,valor_original,codigo_corregido`; `id_caso` vacío aplica
  a todos los casos). No se inventan equivalencias.
* Un valor OPCIONAL que no puede guardarse (CIE-10 inexistente, causa asociada que repite la
  principal o que se repite en el caso, institución de referencia 2 igual a la 1) no se
  descarta: queda en la tabla `migracion_registro_pendiente` del destino y en el informe.
* Duplicados que la estructura nueva no admite (dos antecedentes para un caso, dos casos con la
  misma secretaría, paciente y fecha, etc.) DETIENEN la migración y se listan en el informe.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import psycopg2
import psycopg2.extras

RAIZ = Path(__file__).resolve().parent.parent

# Tablas que se copian con sus columnas comunes (en orden de llaves foráneas).
TABLAS_COMUNES: tuple[str, ...] = (
    'paciente',
    'api_usuario',
    'api_analisis',
    'narrativa_ia',
    'caso_morbilidad',
    'caso_mortalidad',
    'api_sivigilaimportacion',
    'referencia',
    'criterios_enfermedad',
    'criterios_falla_organica',
    'criterios_manejo',
    'manejo_hospitalario',
    'causas_morbilidad',
    'datos_sociodemograficos',
    'antecedente_riesgo',
    'complicacion_embarazo',
    'control_prenatal',
    'antecedente_parto_puerperio',
    'causa_muerte',
)

# Tablas de detalle que en la estructura nueva admiten una sola fila por caso.
UNO_POR_CASO: tuple[tuple[str, str], ...] = (
    ('antecedentes_obstetricos', 'id_caso'),
    ('referencia', 'id_caso'),
    ('criterios_enfermedad', 'id_caso'),
    ('criterios_falla_organica', 'id_caso'),
    ('criterios_manejo', 'id_caso'),
    ('manejo_hospitalario', 'id_caso'),
    ('causas_morbilidad', 'id_caso'),
    ('datos_sociodemograficos', 'caso_morbilidad_id'),
    ('datos_sociodemograficos', 'caso_mortalidad_id'),
)

# Columnas de la estructura anterior que deben existir en el origen.
SENALES_ORIGEN: tuple[str, ...] = ('antecedentes_obstetricos', 'antecedente_materno')

# Tablas con datos que deben estar VACÍAS en el destino antes de migrar.
TABLAS_DESTINO_VACIAS: tuple[str, ...] = (
    'paciente',
    'api_usuario',
    'api_analisis',
    'caso_morbilidad',
    'caso_mortalidad',
    'api_sivigilaimportacion',
)

COLUMNAS_ASOCIADAS: tuple[str, ...] = ('causa_asociada_2', 'causa_asociada_3', 'causa_asociada_4')

# Columnas con fecha de creación obligatoria en el destino.
CREADO_EN_OBLIGATORIO: tuple[str, ...] = ('paciente', 'caso_morbilidad', 'caso_mortalidad')

SQL_PENDIENTES = """
CREATE TABLE IF NOT EXISTS migracion_registro_pendiente (
    id SERIAL PRIMARY KEY,
    tabla_origen VARCHAR(60) NOT NULL,
    columna_origen VARCHAR(60) NOT NULL,
    evento VARCHAR(20),
    id_caso INTEGER,
    orden SMALLINT,
    valor_original TEXT,
    valor_normalizado TEXT,
    motivo VARCHAR(60) NOT NULL,
    detalle TEXT,
    migrado_en TIMESTAMP NOT NULL DEFAULT now()
)
"""


class MigracionError(RuntimeError):
    """La migración no puede continuar; el detalle está en el informe."""


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------


def normalizar_cie10(valor: Any) -> str | None:
    """'o72.1 ' -> 'O721'; vacío o solo guiones -> None."""
    if valor is None:
        return None
    texto = str(valor).strip()
    if not texto or re.fullmatch(r'[-–—\s]+', texto):
        return None
    return texto.replace('.', '').replace(' ', '').upper()


def normalizar_institucion(valor: Any) -> str | None:
    """Nombre de institución sin espacios de los extremos, o None si está vacío."""
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto or None


@dataclass
class Informe:
    """Todo lo que ocurre en la migración: se guarda en JSON y en Markdown."""

    entorno: dict[str, Any]
    bloqueantes: list[dict[str, Any]] = field(default_factory=list)
    observaciones: list[dict[str, Any]] = field(default_factory=list)
    pendientes: list[dict[str, Any]] = field(default_factory=list)
    correcciones_aplicadas: list[dict[str, Any]] = field(default_factory=list)
    conteos: list[dict[str, Any]] = field(default_factory=list)
    validaciones: list[dict[str, Any]] = field(default_factory=list)
    respaldo: dict[str, Any] = field(default_factory=dict)
    resultado: str = 'sin ejecutar'

    def bloquear(self, motivo: str, **detalle: Any) -> None:
        """Registra un problema que impide completar la migración."""
        self.bloqueantes.append({'motivo': motivo, **detalle})

    def observar(self, motivo: str, **detalle: Any) -> None:
        """Registra una observación que no impide migrar (queda en el informe)."""
        self.observaciones.append({'motivo': motivo, **detalle})

    def validar(self, nombre: str, esperado: Any, obtenido: Any) -> bool:
        """Registra una validación (esperado contra obtenido) y devuelve si coincide."""
        ok = esperado == obtenido
        self.validaciones.append(
            {'validacion': nombre, 'esperado': esperado, 'obtenido': obtenido, 'ok': ok}
        )
        return ok

    def guardar(self, carpeta: Path, sello: str) -> tuple[Path, Path]:
        """Escribe el informe en JSON y en Markdown y devuelve las dos rutas."""
        carpeta.mkdir(parents=True, exist_ok=True)
        base = carpeta / f'migracion_{sello}'
        datos = {k: v for k, v in self.__dict__.items()}
        ruta_json = base.with_suffix('.json')
        ruta_json.write_text(
            json.dumps(datos, ensure_ascii=False, indent=2, default=str), encoding='utf-8'
        )
        ruta_md = base.with_suffix('.md')
        ruta_md.write_text(self._markdown(), encoding='utf-8')
        return ruta_json, ruta_md

    def _markdown(self) -> str:
        e = self.entorno
        lineas = [
            f'# Informe de migración ({e["modo"]})',
            '',
            f'- Resultado: **{self.resultado}**',
            f'- Servidor: `{e["host"]}:{e["port"]}` · usuario `{e["usuario"]}`',
            f'- Origen (solo lectura): `{e["origen"]}` · Destino: `{e["destino"]}`',
            f'- Inicio: {e["inicio"]}',
        ]
        if self.respaldo:
            lineas.append(
                f'- Respaldo: `{self.respaldo.get("archivo")}` '
                f'({self.respaldo.get("bytes")} bytes, verificado: '
                f'{self.respaldo.get("verificado")})'
            )
        secciones = (
            ('Bloqueantes (detienen la migración)', self.bloqueantes),
            ('Registros pendientes (en migracion_registro_pendiente)', self.pendientes),
            ('Correcciones CIE-10 aplicadas', self.correcciones_aplicadas),
            ('Observaciones', self.observaciones),
        )
        for titulo, filas in secciones:
            lineas += ['', f'## {titulo} ({len(filas)})', '']
            for f in filas[:500]:
                lineas.append('- ' + ', '.join(f'{k}: {v}' for k, v in f.items()))
            if len(filas) > 500:
                lineas.append(f'- … y {len(filas) - 500} más (ver el JSON).')
        lineas += [
            '',
            '## Conteos',
            '',
            '| Tabla destino | Origen | Destino | Nota |',
            '|---|---|---|---|',
        ]
        for c in self.conteos:
            lineas.append(
                f'| {c["tabla"]} | {c["origen"]} | {c["destino"]} | {c.get("nota", "")} |'
            )
        lineas += [
            '',
            '## Validaciones',
            '',
            '| Validación | Esperado | Obtenido | OK |',
            '|---|---|---|---|',
        ]
        for v in self.validaciones:
            lineas.append(
                f'| {v["validacion"]} | {v["esperado"]} | {v["obtenido"]} | '
                f'{"sí" if v["ok"] else "**NO**"} |'
            )
        return '\n'.join(lineas) + '\n'


# ---------------------------------------------------------------------------
# Lectura del origen
# ---------------------------------------------------------------------------


def _filas(cur, sql: str, params: Any = None) -> list[dict[str, Any]]:
    cur.execute(sql, params)
    return [dict(r) for r in cur.fetchall()]


def _tablas(cur) -> set[str]:
    cur.execute(
        'SELECT table_name FROM information_schema.tables '
        "WHERE table_schema = current_schema() AND table_type = 'BASE TABLE'"
    )
    return {r['table_name'] for r in cur.fetchall()}


def _columnas(cur, tabla: str) -> list[str]:
    cur.execute(
        'SELECT column_name FROM information_schema.columns '
        'WHERE table_schema = current_schema() AND table_name = %s ORDER BY ordinal_position',
        (tabla,),
    )
    return [r['column_name'] for r in cur.fetchall()]


def _contar(cur, tabla: str, where: str = '') -> int:
    cur.execute(f'SELECT count(*) AS n FROM {tabla} {where}')
    return int(cur.fetchone()['n'])


# ---------------------------------------------------------------------------
# Correcciones CIE-10
# ---------------------------------------------------------------------------


@dataclass
class Correcciones:
    """Correcciones de códigos CIE-10 leídas de un archivo CSV."""

    reglas: dict[tuple[str, str, str, str], str] = field(default_factory=dict)
    registradas: set[tuple[Any, ...]] = field(default_factory=set)

    @classmethod
    def leer(cls, ruta: Path | None, informe: Informe) -> Correcciones:
        """Lee el archivo de correcciones; sin archivo devuelve un conjunto vacío."""
        corr = cls()
        if ruta is None:
            return corr
        if not ruta.is_file():
            raise MigracionError(f'No existe el archivo de correcciones {ruta}')
        with ruta.open(encoding='utf-8-sig', newline='') as f:
            lector = csv.DictReader(f)
            requeridas = {'tabla', 'columna', 'id_caso', 'valor_original', 'codigo_corregido'}
            if not lector.fieldnames or not requeridas <= set(lector.fieldnames):
                raise MigracionError(
                    f'{ruta}: el encabezado debe ser {",".join(sorted(requeridas))}'
                )
            for n, fila in enumerate(lector, start=2):
                original = normalizar_cie10(fila['valor_original'])
                corregido = normalizar_cie10(fila['codigo_corregido'])
                if not original or not corregido:
                    informe.bloquear('correccion_incompleta', archivo=str(ruta), linea=n)
                    continue
                clave = (
                    fila['tabla'].strip(),
                    fila['columna'].strip(),
                    (fila['id_caso'] or '').strip() or '*',
                    original,
                )
                corr.reglas[clave] = corregido
        return corr

    def aplicar(
        self, tabla: str, columna: str, id_caso: int | None, codigo: str | None, informe: Informe
    ) -> str | None:
        """Devuelve el código corregido si hay una regla para él, o el mismo código."""
        if codigo is None:
            return None
        for alcance in (str(id_caso), '*'):
            nuevo = self.reglas.get((tabla, columna, alcance, codigo))
            if nuevo:
                clave = (tabla, columna, id_caso, codigo)
                if clave in self.registradas:
                    return nuevo
                self.registradas.add(clave)
                informe.correcciones_aplicadas.append(
                    {
                        'tabla': tabla,
                        'columna': columna,
                        'id_caso': id_caso,
                        'valor_original': codigo,
                        'codigo_corregido': nuevo,
                    }
                )
                return nuevo
        return codigo


# ---------------------------------------------------------------------------
# Migración
# ---------------------------------------------------------------------------


class Migracion:
    """Copia de los datos del origen (estructura anterior) al destino (estructura nueva)."""

    def __init__(self, origen, destino, informe: Informe, correcciones: Correcciones):
        """Prepara los cursores de origen y destino."""
        self.o = origen.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        self.d = destino.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        self.informe = informe
        self.corr = correcciones
        self.cie10: set[str] = set()

    # -- comprobaciones previas ------------------------------------------------

    def verificar_bases(self) -> None:
        """Comprueba que el origen tenga la estructura anterior y el destino la nueva, vacía."""
        tablas_o = _tablas(self.o)
        faltan = [t for t in SENALES_ORIGEN if t not in tablas_o]
        if faltan:
            raise MigracionError(
                f'El origen no tiene la estructura anterior (faltan {", ".join(faltan)}).'
            )
        tablas_d = _tablas(self.d)
        if 'antecedente_obstetrico' not in tablas_d or 'antecedentes_obstetricos' in tablas_d:
            raise MigracionError(
                'El destino no tiene la estructura nueva: créelo vacío y ejecute '
                'sivigila_maternidad_postgres.sql antes de migrar.'
            )
        con_datos = [t for t in TABLAS_DESTINO_VACIAS if _contar(self.d, t) > 0]
        if con_datos:
            raise MigracionError(
                'El destino ya tiene datos en ' + ', '.join(con_datos) + '; use una base nueva.'
            )
        self.cie10 = {r['codigo'] for r in _filas(self.d, 'SELECT codigo FROM cie10')}
        if not self.cie10:
            raise MigracionError('El catálogo cie10 del destino está vacío.')

    def verificar_catalogos(self) -> None:
        """Los catálogos del origen deben coincidir con los del destino (mismos id y textos)."""
        tablas_o = _tablas(self.o)
        for tabla in sorted(t for t in tablas_o if t.startswith('cat_')):
            cols = [c for c in _columnas(self.o, tabla) if c in _columnas(self.d, tabla)]
            if not cols:
                self.informe.bloquear('catalogo_inexistente_en_destino', tabla=tabla)
                continue
            lista = ', '.join(cols)
            orig = {
                tuple(str(v).strip() for v in r.values())
                for r in _filas(self.o, f'SELECT {lista} FROM {tabla}')
            }
            dest = {
                tuple(str(v).strip() for v in r.values())
                for r in _filas(self.d, f'SELECT {lista} FROM {tabla}')
            }
            for fila in sorted(orig - dest):
                self.informe.bloquear(
                    'catalogo_distinto', tabla=tabla, fila_origen=dict(zip(cols, fila, strict=True))
                )

    def verificar_referencias(self) -> None:
        """Secretarías, eventos y correos que el destino exige deben existir."""
        secretarias = {r['codigo'] for r in _filas(self.d, 'SELECT codigo FROM secretaria')}
        eventos = {r['codigo'] for r in _filas(self.d, 'SELECT codigo FROM cat_evento')}
        for tabla in (
            'api_usuario',
            'api_analisis',
            'api_sivigilaimportacion',
            'caso_morbilidad',
            'caso_mortalidad',
        ):
            if 'secretaria_codigo' not in _columnas(self.o, tabla):
                continue
            for r in _filas(
                self.o,
                f'SELECT DISTINCT secretaria_codigo AS s FROM {tabla} '
                'WHERE secretaria_codigo IS NOT NULL',
            ):
                if r['s'] not in secretarias:
                    self.informe.bloquear('secretaria_inexistente', tabla=tabla, valor=r['s'])
        for tabla in ('api_analisis', 'api_sivigilaimportacion'):
            for r in _filas(self.o, f'SELECT DISTINCT tipo FROM {tabla}'):
                if r['tipo'] not in eventos:
                    self.informe.bloquear('evento_inexistente', tabla=tabla, valor=r['tipo'])
        for r in _filas(self.o, 'SELECT id FROM api_usuario WHERE email IS NULL'):
            self.informe.bloquear('usuario_sin_correo', tabla='api_usuario', id=r['id'])

    def verificar_duplicados(self) -> None:
        """Detecta filas que la estructura nueva no admite (una por caso, caso único)."""
        for tabla, col in UNO_POR_CASO:
            for r in _filas(
                self.o,
                f'SELECT {col} AS caso, count(*) AS n FROM {tabla} '
                f'WHERE {col} IS NOT NULL GROUP BY {col} HAVING count(*) > 1',
            ):
                self.informe.bloquear(
                    'mas_de_una_fila_por_caso', tabla=tabla, id_caso=r['caso'], filas=r['n']
                )
        for tabla, fecha in (
            ('caso_morbilidad', 'fecha_egreso'),
            ('caso_mortalidad', 'fecha_defuncion'),
        ):
            for r in _filas(
                self.o,
                f'SELECT secretaria_codigo, id_paciente, {fecha} AS fecha, '
                f'array_agg(id_caso ORDER BY id_caso) AS casos FROM {tabla} '
                f'GROUP BY 1, 2, 3 HAVING count(*) > 1',
            ):
                self.informe.bloquear('caso_repetido', tabla=tabla, **r)

    def verificar_cie10_obligatorios(self) -> None:
        """Las causas obligatorias deben existir en el catálogo cie10 del destino."""
        for tabla, col in (
            ('causas_morbilidad', 'causa_principal_cie10'),
            ('causa_muerte', 'causa_basica_cie10'),
        ):
            for r in _filas(self.o, f'SELECT id_caso, {col} AS v FROM {tabla} ORDER BY id_caso'):
                codigo = self.corr.aplicar(
                    tabla, col, r['id_caso'], normalizar_cie10(r['v']), self.informe
                )
                if codigo is None or codigo not in self.cie10:
                    self.informe.bloquear(
                        'cie10_obligatorio_inexistente',
                        tabla=tabla,
                        columna=col,
                        id_caso=r['id_caso'],
                        valor_original=r['v'],
                        valor_normalizado=codigo,
                    )

    # -- copia ------------------------------------------------------------------

    def _insertar(self, tabla: str, filas: list[dict[str, Any]]) -> int:
        """Inserta `filas`; si una falla, la identifica y la registra como bloqueante."""
        if not filas:
            return 0
        # Las columnas JSON (api_analisis.resumen, ...) llegan como dict/list.
        filas = [
            {k: psycopg2.extras.Json(v) if isinstance(v, (dict, list)) else v for k, v in f.items()}
            for f in filas
        ]
        cols = list(filas[0])
        sql = f'INSERT INTO {tabla} ({", ".join(cols)}) VALUES %s'
        self.d.execute('SAVEPOINT lote')
        try:
            psycopg2.extras.execute_values(
                self.d, sql, [tuple(f[c] for c in cols) for f in filas], page_size=500
            )
            self.d.execute('RELEASE SAVEPOINT lote')
            return len(filas)
        except psycopg2.Error:
            self.d.execute('ROLLBACK TO SAVEPOINT lote')
        # Fila por fila para identificar las que no entran.
        insertadas = 0
        for f in filas:
            self.d.execute('SAVEPOINT fila')
            try:
                self.d.execute(
                    f'INSERT INTO {tabla} ({", ".join(cols)}) '
                    f'VALUES ({", ".join(["%s"] * len(cols))})',
                    tuple(f[c] for c in cols),
                )
                self.d.execute('RELEASE SAVEPOINT fila')
                insertadas += 1
            except psycopg2.Error as exc:
                self.d.execute('ROLLBACK TO SAVEPOINT fila')
                self.informe.bloquear(
                    'fila_rechazada_por_la_base',
                    tabla=tabla,
                    fila={k: f[k] for k in cols if k.startswith('id') or k.endswith('_id')},
                    error=(exc.pgerror or str(exc)).strip().splitlines()[0],
                )
        return insertadas

    def _pendiente(self, **datos: Any) -> None:
        self.informe.pendientes.append(datos)

    def copiar_comunes(self) -> None:
        """Copia las tablas que conservan su forma, con las columnas comunes."""
        ahora = datetime.now()
        for tabla in TABLAS_COMUNES:
            cols_d = _columnas(self.d, tabla)
            cols = [c for c in _columnas(self.o, tabla) if c in cols_d]
            filas = _filas(self.o, f'SELECT {", ".join(cols)} FROM {tabla} ORDER BY 1')
            if tabla in CREADO_EN_OBLIGATORIO:
                pk = cols[0]
                for f in filas:
                    if f.get('creado_en') is None:
                        f['creado_en'] = ahora
                        self.informe.observar(
                            'creado_en_desconocido_se_usa_fecha_migracion', tabla=tabla, id=f[pk]
                        )
            if tabla == 'causas_morbilidad':
                for f in filas:
                    f['causa_principal_cie10'] = self.corr.aplicar(
                        tabla,
                        'causa_principal_cie10',
                        f['id_caso'],
                        normalizar_cie10(f['causa_principal_cie10']),
                        self.informe,
                    )
            if tabla == 'causa_muerte':
                for f in filas:
                    f['causa_basica_cie10'] = self.corr.aplicar(
                        tabla,
                        'causa_basica_cie10',
                        f['id_caso'],
                        normalizar_cie10(f['causa_basica_cie10']),
                        self.informe,
                    )
            if tabla == 'control_prenatal':
                self._preparar_complicacion_feto(filas)
            if tabla == 'api_usuario':
                self._observar_afiliacion_textual()
            n = self._insertar(tabla, filas)
            self.informe.conteos.append({'tabla': tabla, 'origen': len(filas), 'destino': n})

    def _preparar_complicacion_feto(self, filas: list[dict[str, Any]]) -> None:
        for f in filas:
            original = f.get('compl_feto_rn_cie10')
            codigo = self.corr.aplicar(
                'control_prenatal',
                'compl_feto_rn_cie10',
                f['id_caso'],
                normalizar_cie10(original),
                self.informe,
            )
            if codigo is not None and codigo not in self.cie10:
                self._pendiente(
                    tabla_origen='control_prenatal',
                    columna_origen='compl_feto_rn_cie10',
                    evento='mortalidad',
                    id_caso=f['id_caso'],
                    orden=None,
                    valor_original=original,
                    valor_normalizado=codigo,
                    motivo='cie10_inexistente',
                    detalle='se guarda NULL en el destino',
                )
                codigo = None
            f['compl_feto_rn_cie10'] = codigo

    def _observar_afiliacion_textual(self) -> None:
        """Los nombres de departamento/secretaría como texto ya no se guardan (salen del código)."""
        if 'secretaria' not in _columnas(self.o, 'api_usuario'):
            return
        nombres = {
            r['codigo']: r['nombre']
            for r in _filas(self.d, 'SELECT codigo, nombre FROM secretaria')
        }
        for r in _filas(self.o, 'SELECT id, secretaria, secretaria_codigo FROM api_usuario'):
            texto = (r['secretaria'] or '').strip()
            maestro = nombres.get(r['secretaria_codigo'] or '', '')
            if texto and texto.lower() != maestro.strip().lower():
                self.informe.observar(
                    'nombre_secretaria_distinto_al_maestro',
                    tabla='api_usuario',
                    id=r['id'],
                    texto_origen=texto,
                    codigo=r['secretaria_codigo'],
                    nombre_maestro=maestro or None,
                )

    def copiar_antecedentes(self) -> None:
        # Morbilidad: los campos comunes van a antecedente_obstetrico y los propios a
        # antecedente_obstetrico_morbilidad.
        """Reparte los antecedentes de morbilidad y mortalidad en las tablas nuevas."""
        ao = _filas(self.o, 'SELECT * FROM antecedentes_obstetricos ORDER BY id_antecedente')
        comunes = [
            {
                'caso_morbilidad_id': r['id_caso'],
                'caso_mortalidad_id': None,
                'gestaciones': r['num_gestaciones'],
                'partos_vaginales': r['partos_vaginales'],
                'cesareas': r['cesareas'],
                'abortos': r['abortos'],
                'nacidos_muertos': r['muertos'],
                'hijos_vivos': r['vivos'],
                'id_regulacion_fecundidad': r['id_regulacion_fecundidad'],
                'num_controles_prenatales': r['num_controles_prenatales'],
                'semana_inicio_cpn': r['semanas_inicio_cpn'],
            }
            for r in ao
        ]
        propios = [
            {
                'id_antecedente': r['id_antecedente'],
                'id_caso': r['id_caso'],
                'molas': r['molas'],
                'ectopicos': r['ectopicos'],
                'fecha_ultima_gestacion': r['fecha_ultima_gestacion'],
                'id_terminacion_gestacion': r['id_terminacion_gestacion'],
                'edad_gestacional_sem': r['edad_gestacional_sem'],
                'momento_ocurrencia': r['momento_ocurrencia'],
                'estado_recien_nacido': r['estado_recien_nacido'],
                'multiplicidad': r['multiplicidad'],
                'peso_rn_gramos': r['peso_rn_gramos'],
            }
            for r in ao
        ]
        n1 = self._insertar('antecedente_obstetrico', comunes)
        n2 = self._insertar('antecedente_obstetrico_morbilidad', propios)
        self.informe.conteos.append(
            {
                'tabla': 'antecedente_obstetrico (morbilidad)',
                'origen': len(ao),
                'destino': n1,
                'nota': 'desde antecedentes_obstetricos',
            }
        )
        self.informe.conteos.append(
            {
                'tabla': 'antecedente_obstetrico_morbilidad',
                'origen': len(ao),
                'destino': n2,
                'nota': 'desde antecedentes_obstetricos',
            }
        )

        # Mortalidad: antecedente_materno + control_prenatal.num_cpn/semana_inicio_cpn.
        am = {r['id_caso']: r for r in _filas(self.o, 'SELECT * FROM antecedente_materno')}
        cp = {
            r['id_caso']: r
            for r in _filas(
                self.o, 'SELECT id_caso, num_cpn, semana_inicio_cpn FROM control_prenatal'
            )
        }
        propios_m = [
            {
                'id_caso': r['id_caso'],
                'id_convivencia': r['id_convivencia'],
                'otro_convivencia': r['otro_convivencia'],
                'id_escolaridad': r['id_escolaridad'],
            }
            for r in sorted(am.values(), key=lambda x: x['id_caso'])
        ]
        comunes_m = []
        for caso in sorted(set(am) | set(cp)):
            a, c = am.get(caso, {}), cp.get(caso, {})
            comunes_m.append(
                {
                    'caso_morbilidad_id': None,
                    'caso_mortalidad_id': caso,
                    'gestaciones': a.get('gestaciones'),
                    'partos_vaginales': a.get('partos_vaginales'),
                    'cesareas': a.get('cesareas'),
                    'abortos': a.get('abortos'),
                    'nacidos_muertos': a.get('nacidos_muertos'),
                    'hijos_vivos': a.get('hijos_vivos'),
                    'id_regulacion_fecundidad': a.get('id_regulacion_fec'),
                    'num_controles_prenatales': c.get('num_cpn'),
                    'semana_inicio_cpn': c.get('semana_inicio_cpn'),
                }
            )
        n3 = self._insertar('antecedente_materno_mortalidad', propios_m)
        n4 = self._insertar('antecedente_obstetrico', comunes_m)
        self.informe.conteos.append(
            {
                'tabla': 'antecedente_materno_mortalidad',
                'origen': len(am),
                'destino': n3,
                'nota': 'desde antecedente_materno',
            }
        )
        self.informe.conteos.append(
            {
                'tabla': 'antecedente_obstetrico (mortalidad)',
                'origen': len(comunes_m),
                'destino': n4,
                'nota': 'casos con antecedente_materno o control_prenatal',
            }
        )

    def copiar_hijas(self) -> None:
        # Causas asociadas (orden 1..3 = antiguas columnas 2..4).
        """Pasa los grupos de columnas repetidas a sus tablas hijas (1FN)."""
        principal = {
            r['id_caso']: r['causa_principal_cie10']
            for r in _filas(self.d, 'SELECT id_caso, causa_principal_cie10 FROM causas_morbilidad')
        }
        filas, valores_origen = [], 0
        for r in _filas(
            self.o,
            'SELECT id_caso, '
            + ', '.join(COLUMNAS_ASOCIADAS)
            + ' FROM causas_morbilidad ORDER BY id_caso',
        ):
            vistos: set[str] = set()
            for orden, col in enumerate(COLUMNAS_ASOCIADAS, start=1):
                original = r[col]
                codigo = self.corr.aplicar(
                    'causas_morbilidad', col, r['id_caso'], normalizar_cie10(original), self.informe
                )
                if codigo is None:
                    continue
                valores_origen += 1
                motivo = None
                if codigo not in self.cie10:
                    motivo = 'cie10_inexistente'
                elif codigo == principal.get(r['id_caso']):
                    motivo = 'repite_causa_principal'
                elif codigo in vistos:
                    motivo = 'causa_asociada_repetida_en_el_caso'
                if motivo:
                    self._pendiente(
                        tabla_origen='causas_morbilidad',
                        columna_origen=col,
                        evento='morbilidad',
                        id_caso=r['id_caso'],
                        orden=orden,
                        valor_original=original,
                        valor_normalizado=codigo,
                        motivo=motivo,
                        detalle=None,
                    )
                    continue
                vistos.add(codigo)
                filas.append({'id_caso': r['id_caso'], 'orden': orden, 'cie10': codigo})
        n = self._insertar('causa_asociada_morbilidad', filas)
        pendientes = valores_origen - len(filas)
        self.informe.conteos.append(
            {
                'tabla': 'causa_asociada_morbilidad',
                'origen': len(filas),
                'destino': n,
                'nota': f'{valores_origen} valores no vacíos de '
                f'causa_asociada_2/3/4; {pendientes} pendientes',
            }
        )
        self.esperado_asociadas = valores_origen

        # Instituciones de referencia (orden 1 y 2).
        filas, valores_origen = [], 0
        for r in _filas(
            self.o,
            'SELECT id_referencia, id_caso, institucion_ref_1, '
            'institucion_ref_2 FROM referencia ORDER BY id_referencia',
        ):
            n1 = normalizar_institucion(r['institucion_ref_1'])
            n2 = normalizar_institucion(r['institucion_ref_2'])
            for orden, nombre in ((1, n1), (2, n2)):
                if nombre is None:
                    continue
                valores_origen += 1
                if orden == 2 and n1 and nombre.lower() == n1.lower():
                    self._pendiente(
                        tabla_origen='referencia',
                        columna_origen='institucion_ref_2',
                        evento='morbilidad',
                        id_caso=r['id_caso'],
                        orden=2,
                        valor_original=r['institucion_ref_2'],
                        valor_normalizado=nombre,
                        motivo='repite_institucion_1',
                        detalle=None,
                    )
                    continue
                filas.append(
                    {'id_referencia': r['id_referencia'], 'orden': orden, 'institucion': nombre}
                )
        n = self._insertar('referencia_institucion', filas)
        self.informe.conteos.append(
            {
                'tabla': 'referencia_institucion',
                'origen': len(filas),
                'destino': n,
                'nota': f'{valores_origen} valores de institucion_ref_1/2; '
                f'{valores_origen - len(filas)} pendientes',
            }
        )
        self.esperado_instituciones = valores_origen

        # Cirugías adicionales (orden 1 y 2).
        filas = []
        for r in _filas(
            self.o,
            'SELECT id_manejo, cirugia_1, cirugia_1_cual, cirugia_2, '
            'cirugia_2_cual FROM manejo_hospitalario ORDER BY id_manejo',
        ):
            for orden in (1, 2):
                tipo = r[f'cirugia_{orden}']
                if tipo is not None:
                    filas.append(
                        {
                            'id_manejo': r['id_manejo'],
                            'orden': orden,
                            'id_tipo_cirugia': tipo,
                            'cual': r[f'cirugia_{orden}_cual'],
                        }
                    )
        n = self._insertar('cirugia_adicional_morbilidad', filas)
        self.informe.conteos.append(
            {
                'tabla': 'cirugia_adicional_morbilidad',
                'origen': len(filas),
                'destino': n,
                'nota': 'valores de cirugia_1/2',
            }
        )
        self.esperado_cirugias = len(filas)

    def guardar_pendientes(self) -> None:
        """Guarda en el destino los valores que no pudieron migrarse."""
        self.d.execute(SQL_PENDIENTES)
        if self.informe.pendientes:
            filas = [
                {
                    k: p[k]
                    for k in (
                        'tabla_origen',
                        'columna_origen',
                        'evento',
                        'id_caso',
                        'orden',
                        'valor_original',
                        'valor_normalizado',
                        'motivo',
                        'detalle',
                    )
                }
                for p in self.informe.pendientes
            ]
            self._insertar('migracion_registro_pendiente', filas)

    def ajustar_secuencias(self) -> None:
        """Lleva cada secuencia al máximo id copiado para que no choque con datos nuevos."""
        for r in _filas(
            self.d,
            """
            SELECT c.table_name, c.column_name,
                   pg_get_serial_sequence(c.table_name, c.column_name) AS seq
            FROM information_schema.columns c
            WHERE c.table_schema = current_schema() AND c.column_default LIKE 'nextval%%'""",
        ):
            if r['seq']:
                self.d.execute(
                    f'SELECT setval(%s, COALESCE((SELECT max({r["column_name"]}) '
                    f'FROM {r["table_name"]}), 0) + 1, false)',
                    (r['seq'],),
                )

    # -- validaciones -------------------------------------------------------------

    def validar(self) -> bool:
        """Registra una validación (esperado contra obtenido) y devuelve si coincide."""
        inf = self.informe
        ok = True
        for c in inf.conteos:
            ok &= inf.validar(f'conteo {c["tabla"]}', c['origen'], c['destino'])
        n_pend = lambda tabla: sum(1 for p in inf.pendientes if p['tabla_origen'] == tabla)  # noqa: E731
        ok &= inf.validar(
            'causas asociadas: origen = migradas + pendientes',
            self.esperado_asociadas,
            _contar(self.d, 'causa_asociada_morbilidad') + n_pend('causas_morbilidad'),
        )
        ok &= inf.validar(
            'instituciones: origen = migradas + pendientes',
            self.esperado_instituciones,
            _contar(self.d, 'referencia_institucion') + n_pend('referencia'),
        )
        # Casos por secretaría.
        for tabla in ('caso_morbilidad', 'caso_mortalidad'):
            sql = (
                f"SELECT coalesce(secretaria_codigo, '(sin)') AS s, count(*) AS n FROM {tabla} "
                'GROUP BY 1'
            )
            o = {r['s']: r['n'] for r in _filas(self.o, sql)}
            d = {r['s']: r['n'] for r in _filas(self.d, sql)}
            ok &= inf.validar(f'{tabla} por secretaría', o, d)
        # Cada importación apunta a un caso existente de su evento.
        huerfanas = _contar(
            self.d,
            'api_sivigilaimportacion i',
            """
            WHERE (i.tipo = 'morbilidad' AND NOT EXISTS
                     (SELECT 1 FROM caso_morbilidad c WHERE c.id_caso = i.caso_id))
               OR (i.tipo = 'mortalidad' AND NOT EXISTS
                     (SELECT 1 FROM caso_mortalidad c WHERE c.id_caso = i.caso_id))""",
        )
        ok &= inf.validar('importaciones sin caso', 0, huerfanas)
        ok &= self._validar_antecedentes()
        ok &= self._validar_causas_principales()
        return bool(ok)

    def _validar_antecedentes(self) -> bool:
        """Compara campo por campo los antecedentes de cada caso entre origen y destino."""
        o = {
            ('morbilidad', r['id_caso']): r
            for r in _filas(
                self.o,
                """
            SELECT id_caso, num_gestaciones AS gestaciones, partos_vaginales, cesareas, abortos,
                   muertos AS nacidos_muertos, vivos AS hijos_vivos, id_regulacion_fecundidad,
                   num_controles_prenatales, semanas_inicio_cpn AS semana_inicio_cpn, molas,
                   ectopicos, fecha_ultima_gestacion, id_terminacion_gestacion,
                   edad_gestacional_sem, momento_ocurrencia, estado_recien_nacido, multiplicidad,
                   peso_rn_gramos
            FROM antecedentes_obstetricos""",
            )
        }
        o.update(
            {
                ('mortalidad', r['id_caso']): r
                for r in _filas(
                    self.o,
                    """
            SELECT coalesce(a.id_caso, c.id_caso) AS id_caso, a.gestaciones, a.partos_vaginales,
                   a.cesareas, a.abortos, a.nacidos_muertos, a.hijos_vivos,
                   a.id_regulacion_fec AS id_regulacion_fecundidad,
                   c.num_cpn AS num_controles_prenatales, c.semana_inicio_cpn,
                   a.id_convivencia, a.otro_convivencia, a.id_escolaridad
            FROM antecedente_materno a FULL JOIN control_prenatal c ON c.id_caso = a.id_caso""",
                )
            }
        )
        d = {
            ('morbilidad', r['id_caso']): r
            for r in _filas(
                self.d,
                """
            SELECT ao.caso_morbilidad_id AS id_caso, ao.gestaciones, ao.partos_vaginales,
                   ao.cesareas, ao.abortos, ao.nacidos_muertos, ao.hijos_vivos,
                   ao.id_regulacion_fecundidad, ao.num_controles_prenatales, ao.semana_inicio_cpn,
                   m.molas, m.ectopicos, m.fecha_ultima_gestacion, m.id_terminacion_gestacion,
                   m.edad_gestacional_sem, m.momento_ocurrencia, m.estado_recien_nacido,
                   m.multiplicidad, m.peso_rn_gramos
            FROM antecedente_obstetrico ao
                 JOIN antecedente_obstetrico_morbilidad m ON m.id_caso = ao.caso_morbilidad_id""",
            )
        }
        d.update(
            {
                ('mortalidad', r['id_caso']): r
                for r in _filas(
                    self.d,
                    """
            SELECT ao.caso_mortalidad_id AS id_caso, ao.gestaciones, ao.partos_vaginales,
                   ao.cesareas, ao.abortos, ao.nacidos_muertos, ao.hijos_vivos,
                   ao.id_regulacion_fecundidad, ao.num_controles_prenatales, ao.semana_inicio_cpn,
                   m.id_convivencia, m.otro_convivencia, m.id_escolaridad
            FROM antecedente_obstetrico ao
                 LEFT JOIN antecedente_materno_mortalidad m ON m.id_caso = ao.caso_mortalidad_id
            WHERE ao.caso_mortalidad_id IS NOT NULL""",
                )
            }
        )
        distintos = [
            {'caso': k, 'campo': campo, 'origen': o[k][campo], 'destino': d.get(k, {}).get(campo)}
            for k in o
            for campo in o[k]
            if k not in d or o[k][campo] != d[k].get(campo)
        ]
        for x in distintos[:50]:
            self.informe.bloquear('antecedente_distinto_tras_migrar', **x)
        return self.informe.validar(
            'antecedentes: campos distintos entre origen y destino', 0, len(distintos)
        )

    def _validar_causas_principales(self) -> bool:
        """Cada causa obligatoria quedó igual a su valor normalizado (o a su corrección)."""
        ok = True
        for tabla, col in (
            ('causas_morbilidad', 'causa_principal_cie10'),
            ('causa_muerte', 'causa_basica_cie10'),
        ):
            sql = f'SELECT id_caso, {col} AS v FROM {tabla}'
            esperado = {
                r['id_caso']: self.corr.aplicar(
                    tabla, col, r['id_caso'], normalizar_cie10(r['v']), self.informe
                )
                for r in _filas(self.o, sql)
            }
            obtenido = {r['id_caso']: r['v'] for r in _filas(self.d, sql)}
            distintos = sum(1 for k, v in esperado.items() if obtenido.get(k) != v)
            ok &= self.informe.validar(f'{tabla}.{col} igual a origen normalizado', 0, distintos)
        return bool(ok)


# ---------------------------------------------------------------------------
# Respaldo
# ---------------------------------------------------------------------------


def _binario(nombre: str, pg_bin: str | None) -> str:
    if pg_bin:
        ruta = Path(pg_bin) / (nombre + ('.exe' if os.name == 'nt' else ''))
        if ruta.is_file():
            return str(ruta)
    encontrado = shutil.which(nombre)
    if not encontrado:
        raise MigracionError(f'No se encontró {nombre}; indique --pg-bin.')
    return encontrado


def respaldar(args, informe: Informe, sello: str) -> None:
    """Crea el respaldo del origen con pg_dump y lo verifica con pg_restore --list."""
    carpeta = Path(args.respaldo_dir)
    carpeta.mkdir(parents=True, exist_ok=True)
    archivo = carpeta / f'{args.origen}_{sello}.dump'
    entorno = {**os.environ, 'PGPASSWORD': args.password or ''}
    subprocess.run(
        [
            _binario('pg_dump', args.pg_bin),
            '-h',
            args.host,
            '-p',
            str(args.port),
            '-U',
            args.usuario,
            '-Fc',
            '-f',
            str(archivo),
            args.origen,
        ],
        check=True,
        env=entorno,
    )
    lista = subprocess.run(
        [_binario('pg_restore', args.pg_bin), '--list', str(archivo)],
        check=True,
        capture_output=True,
        text=True,
    )
    entradas = sum(1 for ln in lista.stdout.splitlines() if ln and not ln.startswith(';'))
    tamano = archivo.stat().st_size if archivo.exists() else 0
    informe.respaldo = {
        'archivo': str(archivo),
        'bytes': tamano,
        'entradas': entradas,
        'verificado': tamano > 0 and entradas > 0,
    }
    if not informe.respaldo['verificado']:
        raise MigracionError(f'El respaldo {archivo} no se pudo verificar.')


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------


def _argumentos(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    p.add_argument('--origen', required=True, help='Base con la estructura anterior (solo lectura)')
    p.add_argument('--destino', required=True, help='Base NUEVA creada con el script actual')
    modo = p.add_mutually_exclusive_group(required=True)
    modo.add_argument('--simular', action='store_true', help='Copia, valida y deshace todo')
    modo.add_argument('--confirmar', action='store_true', help='Respaldo + copia definitiva')
    p.add_argument('--host', default=os.environ.get('DB_HOST', 'localhost'))
    p.add_argument('--port', type=int, default=int(os.environ.get('DB_PORT', '5432')))
    p.add_argument('--usuario', default=os.environ.get('DB_USER', 'postgres'))
    p.add_argument('--correcciones', type=Path, default=None)
    p.add_argument('--reporte-dir', default=str(RAIZ / 'migracion_reportes'))
    p.add_argument('--respaldo-dir', default=str(RAIZ / 'backups'))
    p.add_argument('--pg-bin', default=None, help='Carpeta de pg_dump/pg_restore')
    args = p.parse_args(argv)
    args.password = os.environ.get('PGPASSWORD') or os.environ.get('DB_PASSWORD')
    return args


def ejecutar(argv: list[str] | None = None) -> int:
    """Ejecuta la migración y devuelve el código de salida.

    0 si terminó bien, 2 si hay bloqueantes, 3 si falla una validación y 1 ante un error de uso
    o de conexión.
    """
    args = _argumentos(argv)
    sello = datetime.now().strftime('%Y%m%d_%H%M%S')
    informe = Informe(
        entorno={
            'modo': 'simulación' if args.simular else 'confirmada',
            'host': args.host,
            'port': args.port,
            'usuario': args.usuario,
            'origen': args.origen,
            'destino': args.destino,
            'inicio': datetime.now().isoformat(),
        }
    )
    print(
        f'Servidor {args.host}:{args.port} · origen {args.origen} (solo lectura) · '
        f'destino {args.destino} · modo {informe.entorno["modo"]}'
    )
    if args.origen == args.destino:
        print('El origen y el destino deben ser bases distintas.')
        return 1

    def conectar(nombre: str):
        return psycopg2.connect(
            host=args.host, port=args.port, user=args.usuario, password=args.password, dbname=nombre
        )

    codigo = 1
    origen = destino = None
    try:
        origen = conectar(args.origen)
        origen.set_session(readonly=True, isolation_level='REPEATABLE READ')
        destino = conectar(args.destino)
        destino.autocommit = False
        correcciones = Correcciones.leer(args.correcciones, informe)
        m = Migracion(origen, destino, informe, correcciones)

        m.verificar_bases()
        m.verificar_catalogos()
        m.verificar_referencias()
        m.verificar_duplicados()
        m.verificar_cie10_obligatorios()
        if informe.bloqueantes:
            informe.resultado = 'detenida antes de copiar: hay bloqueantes'
            codigo = 2
            return codigo

        if args.confirmar:
            respaldar(args, informe, sello)

        m.copiar_comunes()
        m.copiar_antecedentes()
        m.copiar_hijas()
        m.guardar_pendientes()
        m.ajustar_secuencias()
        valido = m.validar()
        if informe.bloqueantes or not valido:
            destino.rollback()
            informe.resultado = 'deshecha: fallaron validaciones o filas (ver bloqueantes)'
            codigo = 3 if not informe.bloqueantes else 2
        elif args.simular:
            destino.rollback()
            informe.resultado = 'simulación correcta: todo se deshizo, el destino no cambió'
            codigo = 0
        else:
            destino.commit()
            informe.resultado = 'migración confirmada'
            codigo = 0
        return codigo
    except MigracionError as exc:
        informe.resultado = f'detenida: {exc}'
        if destino is not None:
            destino.rollback()
        return 1
    finally:
        if origen is not None:
            origen.rollback()
            origen.close()
        if destino is not None:
            if not destino.closed and destino.status != psycopg2.extensions.STATUS_READY:
                destino.rollback()
            destino.close()
        ruta_json, ruta_md = informe.guardar(Path(args.reporte_dir), sello)
        print(
            f'{informe.resultado}. Bloqueantes: {len(informe.bloqueantes)}, pendientes: '
            f'{len(informe.pendientes)}. Informe: {ruta_md}'
        )


if __name__ == '__main__':
    sys.exit(ejecutar())
