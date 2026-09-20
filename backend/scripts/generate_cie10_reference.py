"""Genera el catálogo JSON de descripciones CIE-10 para el frontend.

Lee la tabla de referencia oficial (Excel, provista por el cliente) y
produce un archivo JSON código -> nombre que el frontend usa para
etiquetar las causas de morbilidad y mortalidad en las gráficas. Se
ejecuta manualmente cuando la tabla de referencia se actualiza; el JSON
generado se versiona como código fuente del frontend.

Uso:
    backend/venv/Scripts/python.exe scripts/generate_cie10_reference.py
"""

import json
from pathlib import Path

import pandas as pd

_EXCEL_PATH = (
    Path(__file__).resolve().parent.parent.parent / "ayudas" / "TablaReferencia_CIE10__1.xlsx"
)
_OUTPUT_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "frontend"
    / "maternanalytics"
    / "src"
    / "constants"
    / "cie10Nombres.json"
)


def main() -> None:
    """Lee el Excel de referencia y escribe el JSON código -> nombre."""
    df = pd.read_excel(_EXCEL_PATH, usecols=["Codigo", "Nombre"])
    df = df.dropna(subset=["Codigo", "Nombre"])
    mapping = {
        str(codigo).strip().upper(): str(nombre).strip().title()
        for codigo, nombre in zip(df["Codigo"], df["Nombre"])
    }
    _OUTPUT_PATH.write_text(
        json.dumps(mapping, ensure_ascii=False, sort_keys=True), encoding="utf-8"
    )
    print(f"Escritas {len(mapping)} descripciones CIE-10 en {_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
