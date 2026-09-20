"""Script de depuración: imprime columnas y datos de ejemplo de los Excel de plantilla."""

import pandas as pd


def analyze_excel(path: str) -> None:
    """Imprime las columnas y las primeras filas de un archivo Excel.

    Args:
        path: Ruta del archivo Excel a inspeccionar.
    """
    try:
        print(f"\n--- Analyzing: {path} ---")
        df = pd.read_excel(path, nrows=5)
        print("Columns:")
        for col in df.columns:
            print(f"  - {col}")
        print("\nSample Data (First 2 rows):")
        print(df.head(2).to_dict("records"))
    except Exception as e:
        print(f"Error reading {path}: {e}")


def main() -> None:
    """Punto de entrada principal."""
    analyze_excel(r"C:\Users\lopez\Documents\UNIVERSIDAD\PLANTILLA DATOS MORBILIDAD.xlsx")
    analyze_excel(r"C:\Users\lopez\Documents\UNIVERSIDAD\PLANTILLA Mortalidad materna.xlsx")


if __name__ == "__main__":
    main()
