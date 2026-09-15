"""Test de regresión: cada subida debe dejar su propia fila en el historial.

Antes, `procesar_subida` actualizaba en el sitio la fila de `Analisis`
más reciente para ese `tipo` en vez de insertar una nueva, así que
`GET /api/analisis/historial/` nunca podía mostrar más de una entrada
por tipo (mortalidad/morbilidad), sin importar cuántas veces se subiera
un archivo.
"""

import io

import pandas as pd
import pytest
from fastapi import UploadFile

from db.models_sqlalchemy import Analisis
from services import analisis_service


def _archivo(nombre: str) -> UploadFile:
    return UploadFile(filename=nombre, file=io.BytesIO(b"contenido"))


@pytest.fixture
def _mocks_pipeline_excel(mocker):
    """Aísla `procesar_subida` de la lectura real de Excel y de SIVIGILA."""
    mocker.patch.object(analisis_service, "_leer_columnas_excel", return_value=["col"])
    mocker.patch.object(analisis_service, "_obtener_columnas_faltantes", return_value=[])
    mocker.patch.object(
        analisis_service, "_leer_dataframe_excel", return_value=pd.DataFrame({"col": [1]})
    )
    mocker.patch.object(
        analisis_service.sivigila_service,
        "persistir_dataframe",
        return_value={"registros_procesados": 1},
    )
    mocker.patch.object(analisis_service, "_construir_df_desde_bd", return_value=None)
    mocker.patch.object(
        analisis_service,
        "_guardar_df_como_excel",
        side_effect=[
            ("/media/a.xlsx", "hashA", {}, 10),
            ("/media/b.xlsx", "hashB", {}, 20),
        ],
    )


def test_segunda_subida_del_mismo_tipo_crea_fila_nueva_no_actualiza_la_existente(
    db_session, _mocks_pipeline_excel
):
    """Dos subidas de 'mortalidad' deben dejar 2 filas en Analisis, no 1."""
    analisis_service.procesar_subida(
        tipo="mortalidad", archivo=_archivo("semana1.xlsx"), db=db_session
    )
    analisis_service.procesar_subida(
        tipo="mortalidad", archivo=_archivo("semana2.xlsx"), db=db_session
    )

    filas = db_session.query(Analisis).filter(Analisis.tipo == "mortalidad").all()
    assert len(filas) == 2, "Cada subida debe insertar una fila nueva para conservar el historial"

    nombres = sorted(f.nombre_archivo for f in filas)
    assert nombres == ["semana1.xlsx", "semana2.xlsx"]


def test_historial_lista_ambas_subidas_ordenadas_por_fecha_desc(db_session, _mocks_pipeline_excel):
    """`listar_historial` debe devolver las 2 subidas, la más reciente primero."""
    analisis_service.procesar_subida(
        tipo="mortalidad", archivo=_archivo("semana1.xlsx"), db=db_session
    )
    analisis_service.procesar_subida(
        tipo="mortalidad", archivo=_archivo("semana2.xlsx"), db=db_session
    )

    items, total = analisis_service.listar_historial(db=db_session)
    assert total == 2
    assert [i.nombre_archivo for i in items] == ["semana2.xlsx", "semana1.xlsx"]
