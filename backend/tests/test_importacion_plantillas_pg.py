"""Importación de las plantillas OFICIALES 549 y 550 sobre PostgreSQL (base desechable).

Usa el mismo flujo del endpoint de carga (lectura del Excel, preparación y
`persistir_dataframe`) y comprueba que las causas asociadas, las instituciones y las cirugías
quedan en sus tablas hijas y se recuperan en la vista, en el DataFrame de análisis y en el API.

Requiere `VM_PG_PRUEBAS` y las plantillas: las de `frontend/maternanalytics/public/plantillas`
(llegan con la rama main) o la carpeta indicada en `VM_PLANTILLAS_DIR`.
"""

import io
import os
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from api.routers import sivigila as router_sivigila
from services import sivigila_service
from services._analisis_excel import (
    _leer_columnas_excel,
    _leer_dataframe_excel,
    _obtener_columnas_faltantes,
    preparar_dataframe_analisis,
)
from services._analisis_persistencia import _construir_df_desde_bd
from services._morbilidad_processor import MorbilidadProcessor
from tests.pg_desechable import bases_desechables, conectar, parametros

_RAIZ = Path(__file__).resolve().parent.parent
_SCRIPT_SQL = _RAIZ / 'sivigila_maternidad_postgres.sql'
_NOMBRES = {
    'morbilidad': 'PLANTILLA DATOS MORBILIDAD.xlsx',
    'mortalidad': 'PLANTILLA Mortalidad materna.xlsx',
}


def _plantilla(tipo: str) -> Path:
    carpeta = Path(
        os.environ.get('VM_PLANTILLAS_DIR')
        or _RAIZ.parent / 'frontend' / 'maternanalytics' / 'public' / 'plantillas'
    )
    ruta = carpeta / _NOMBRES[tipo]
    if not ruta.is_file():
        pytest.skip(f'no está la plantilla oficial {ruta}')
    return ruta


def _leer(tipo: str) -> pd.DataFrame:
    buffer = io.BytesIO(_plantilla(tipo).read_bytes())
    assert _obtener_columnas_faltantes(tipo, _leer_columnas_excel(buffer, tipo)) == []
    df, _ = preparar_dataframe_analisis(_leer_dataframe_excel(buffer, tipo))
    return df


@pytest.fixture
def db():
    """Sesión sobre una base desechable con el script completo."""
    params = parametros()
    with bases_desechables('carga') as nombres:
        con = conectar(nombres['carga'])
        con.cursor().execute(_SCRIPT_SQL.read_text(encoding='utf-8'))
        con.close()
        motor = create_engine(
            f'postgresql+psycopg2://{params.get("user")}:{params.get("password", "")}@'
            f'{params.get("host")}:{params.get("port")}/{nombres["carga"]}'
        )
        sesion = Session(bind=motor)
        try:
            yield sesion
        finally:
            sesion.close()
            motor.dispose()


def _quitar_asociadas_repetidas(df: pd.DataFrame) -> pd.DataFrame:
    """Deja vacía una causa asociada que repite otra de la misma fila (error de los ejemplos)."""
    columnas = ['Causa asociada CIE-10', 'Causa asociada CIE-10.1', 'Causa asociada CIE-10.2']
    df = df.copy()
    for i in df.index:
        vistos = set()
        for c in columnas:
            v = df.at[i, c]
            clave = str(v).replace('.', '').strip().upper() if pd.notna(v) else None
            if clave and clave in vistos:
                df.at[i, c] = None
            elif clave:
                vistos.add(clave)
    return df


def test_plantilla_549_con_causa_asociada_repetida_se_rechaza_con_fila(db):
    """La regla UNIQUE(id_caso, cie10) se avisa con fila y columna, sin error de base."""
    df = _leer('morbilidad')
    repetidas = _quitar_asociadas_repetidas(df).compare(df)
    if repetidas.empty:
        pytest.skip('la plantilla ya no trae causas asociadas repetidas')
    with pytest.raises(
        ValueError, match=r"Fila \d+: la columna 'Causa asociada CIE-10\.\d' repite"
    ):
        sivigila_service.persistir_dataframe(db, df, 'morbilidad', 'bello')
    db.rollback()
    assert db.execute(text('SELECT count(*) FROM caso_morbilidad')).scalar() == 0


def test_plantilla_549_carga_y_recupera_causas_asociadas_en_todas_las_capas(db):
    """Plantilla 549 carga y recupera causas asociadas en todas las capas."""
    df = _quitar_asociadas_repetidas(_leer('morbilidad'))
    resumen = sivigila_service.persistir_dataframe(db, df, 'morbilidad', 'bello')
    db.commit()
    assert resumen['casos_creados'] == len(df)

    columnas = ['Causa asociada CIE-10', 'Causa asociada CIE-10.1', 'Causa asociada CIE-10.2']
    esperadas = sorted(
        str(v).replace('.', '').strip().upper()
        for c in columnas
        for v in df[c]
        if pd.notna(v) and str(v).strip() not in ('', '—', '-')
    )
    # 1) Tabla hija y vista: una fila por causa, con su descripción del catálogo.
    filas = db.execute(
        text('SELECT cie10, descripcion FROM v_causa_asociada_morbilidad ORDER BY cie10')
    ).all()
    assert sorted(f[0] for f in filas) == esperadas
    assert all(f[1] for f in filas)
    # 2) DataFrame de análisis: las filas hijas vuelven a las columnas de la plantilla.
    df_bd = _construir_df_desde_bd(db, 'morbilidad', 'bello')
    en_df = sorted(str(v) for c in columnas for v in df_bd[c] if pd.notna(v) and v is not None)
    assert en_df == esperadas
    # 3) Análisis del dashboard.
    analisis = MorbilidadProcessor(df_bd).analizar_causas_asociadas(top_n=20)
    assert sum(c['casos'] for c in analisis['top_causas']) == len(esperadas)
    # 4) API.
    respuesta = router_sivigila.listar_morbilidad(
        skip=0, limit=None, db=db, usuario=SimpleNamespace(secretaria_codigo='bello')
    )
    assert sorted(c.cie10 for r in respuesta for c in r.causas_asociadas) == esperadas
    assert all(
        [c.orden for c in r.causas_asociadas] == sorted(c.orden for c in r.causas_asociadas)
        for r in respuesta
    )
    # 5) Instituciones y cirugías como filas hijas.
    instituciones = sum(
        df[c].notna().sum() for c in ('Institución referencia 1', 'Institución referencia 2')
    )
    assert db.execute(text('SELECT count(*) FROM referencia_institucion')).scalar() == instituciones
    cirugias = sum(df[c].notna().sum() for c in ('Cirugía adicional 1', 'Cirugía adicional 2'))
    assert (
        db.execute(text('SELECT count(*) FROM cirugia_adicional_morbilidad')).scalar() == cirugias
    )
    # 6) Volver a cargar el mismo archivo no duplica nada.
    otra = sivigila_service.persistir_dataframe(db, df, 'morbilidad', 'bello')
    db.commit()
    assert otra['filas_omitidas_duplicadas'] == len(df)
    assert db.execute(text('SELECT count(*) FROM causa_asociada_morbilidad')).scalar() == len(
        esperadas
    )


def test_plantilla_550_carga_con_antecedentes_y_cie10_normalizados(db):
    """Plantilla 550 carga con antecedentes y cie10 normalizados."""
    df = _leer('mortalidad')
    resumen = sivigila_service.persistir_dataframe(db, df, 'mortalidad', 'bello')
    db.commit()
    assert resumen['casos_creados'] == len(df)
    assert db.execute(
        text('SELECT count(*) FROM antecedente_obstetrico WHERE caso_mortalidad_id IS NOT NULL')
    ).scalar() == len(df)
    # Todos los CIE-10 guardados existen en el catálogo y están normalizados (sin punto).
    assert (
        db.execute(
            text("SELECT count(*) FROM causa_muerte WHERE causa_basica_cie10 LIKE '%.%'")
        ).scalar()
        == 0
    )
    assert (
        db.execute(
            text("SELECT count(*) FROM control_prenatal WHERE compl_feto_rn_cie10 LIKE '%.%'")
        ).scalar()
        == 0
    )
    filas = db.execute(
        text('SELECT gestaciones, num_cpn FROM v_mortalidad_completa ORDER BY id_caso')
    ).all()
    assert [f[0] for f in filas] == [int(v) for v in df['6.5 Gestaciones']]
