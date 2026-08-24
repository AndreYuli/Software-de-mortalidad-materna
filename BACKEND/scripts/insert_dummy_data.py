"""Script para generar datos de prueba y subirlos al servidor."""

import datetime
import io
import random

import pandas as pd
import requests


def generate_random_dates(num_rows, start_year, end_year):
    dates = []
    for _ in range(num_rows):
        year = random.randint(start_year, end_year)
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        dates.append(datetime.date(year, month, day))
    return dates


def process_and_upload(template_path: str, tipo: str, date_cols: list[str], url: str):
    print(f"Generando datos para {tipo}...")
    try:
        df = pd.read_excel(template_path)
        # Duplicate rows to have enough data (e.g., 50 rows)
        if len(df) < 50:
            df = pd.concat([df] * (50 // len(df) + 1), ignore_index=True).head(50)

        # Randomize dates
        random_dates = generate_random_dates(len(df), 2022, 2024)
        for col in date_cols:
            if col in df.columns:
                df[col] = random_dates

        # Save to bytes buffer
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False)
        buffer.seek(0)

        # Upload
        print(f"Subiendo {tipo} a {url}...")
        files = {
            "archivo": (
                f"dummy_{tipo}.xlsx",
                buffer,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        }
        data = {"tipo": tipo}
        response = requests.post(url, data=data, files=files)

        if response.status_code == 201:
            print(f"¡Éxito! {tipo} insertado. ID: {response.json().get('id')}")
        else:
            print(f"Error al subir {tipo}: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"Excepción procesando {tipo}: {e}")


def main():
    base_url = "http://localhost:8000/api/analisis/"

    # Morbilidad
    process_and_upload(
        r"C:\Users\lopez\Documents\UNIVERSIDAD\PLANTILLA DATOS MORBILIDAD.xlsx",
        "morbilidad",
        ["Fecha de egreso", "Fecha egreso"],
        base_url,
    )

    # Mortalidad
    process_and_upload(
        r"C:\Users\lopez\Documents\UNIVERSIDAD\PLANTILLA Mortalidad materna.xlsx",
        "mortalidad",
        ["5.2 Fecha de defunción", "5.2 Fecha de defuncion", "Fecha de defunción"],
        base_url,
    )


if __name__ == "__main__":
    main()
