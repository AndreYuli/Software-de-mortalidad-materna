"""Genera el ranking de relevancia bibliográfica de las variables (Tabla 1 del artículo).

Uso (desde backend/):  python scripts/relevancia_variables.py
Lee    docs/relevancia_variables/variables_literatura.csv
Escribe docs/relevancia_variables/relevancia_variables.csv y .txt
"""

import csv
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / 'backend'))

from services.relevancia_variables import calcular_relevancia, leer_variables  # noqa: E402

TOTAL_ARTICULOS = 30
CARPETA = RAIZ / 'docs' / 'relevancia_variables'


def main() -> None:
    """Calcula el ranking y lo guarda en CSV y en texto legible."""
    filas = calcular_relevancia(
        leer_variables(CARPETA / 'variables_literatura.csv'), TOTAL_ARTICULOS
    )
    columnas = [
        'posicion',
        'variable',
        'factor',
        'n_articulos',
        'frecuencia',
        'ic_bajo',
        'ic_alto',
        'disponible_en',
        'campo_ficha',
    ]
    with (CARPETA / 'relevancia_variables.csv').open('w', encoding='utf-8-sig', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=columnas, extrasaction='ignore')
        w.writeheader()
        w.writerows(filas)
    lineas = [
        f'Relevancia bibliográfica de las variables (N = {TOTAL_ARTICULOS} artículos)',
        'Puntaje = límite inferior del IC 95 % de Wilson de la frecuencia. No mide asociación '
        'estadística.',
        '',
        f'{"#":>2}  {"Variable":<52}{"k/N":>6}{"f":>8}{"IC 95 %":>16}  Fichas',
    ]
    for r in filas:
        ic = f'[{r["ic_bajo"] * 100:.1f}; {r["ic_alto"] * 100:.1f}]'
        lineas.append(
            f'{r["posicion"]:>2}  {r["variable"]:<52}{r["n_articulos"]:>3}/{TOTAL_ARTICULOS}'
            f'{r["frecuencia"] * 100:>7.1f}%{ic:>16}  {r["disponible_en"]}'
        )
    texto = '\n'.join(lineas) + '\n'
    (CARPETA / 'relevancia_variables.txt').write_text(texto, encoding='utf-8')
    print(texto)


if __name__ == '__main__':
    main()
