"""Constantes de mapeo y helpers de persistencia de archivos de análisis."""

from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from db.models_sqlalchemy import VMorbilidadCompleta, VMortalidadCompleta
from services._analisis_excel import preparar_dataframe_analisis

_MORBILIDAD_DB_MAPPING = {
    'nombres_apellidos': 'Nombres y apellidos',
    'tipo_id': 'Tipo de ID',
    'numero_id': 'N° identificación',
    'edad': 'Edad',
    'num_gestaciones': 'N° gestaciones',
    'partos_vaginales': 'Partos vaginales',
    'cesareas': 'Cesáreas',
    'abortos': 'Abortos',
    'num_controles_prenatales': 'N° controles prenatales',
    'semanas_inicio_cpn': 'Semanas inicio CPN',
    'edad_gestacional_sem': 'Edad gestacional ocurrencia (sem)',
    'terminacion_gestacion': 'Momento ocurrencia',
    'eclampsia': 'Eclampsia',
    'sepsis_sistemica_severa': 'Sepsis sistémica severa',
    'hemorragia_obstetrica': 'Hemorragia obstétrica severa',
    'preeclampsia': 'Preeclampsia',
    'ruptura_uterina': 'Ruptura uterina',
    'ingreso_uci': 'Ingreso UCI',
    'cirugia_adicional': 'Cirugía adicional',
    'transfusion': 'Transfusión',
    'total_criterios': 'Total criterios',
    'causa_principal_cie10': 'Causa principal CIE-10',
    'dias_estancia_hosp': 'Días estancia hospitalaria',
    'dias_estancia_uci': 'Días estancia UCI',
    'tiempo_remision_h': 'Tiempo remisión (h)',
    'institucion_ref_1': 'Institución referencia 1',
    'falla_hepatica': 'falla_hepatica',
    'falla_renal': 'falla_renal',
    'falla_coagulacion': 'falla_coagulacion',
    'zona_residencia': 'Zona de residencia',
    'poblacion_vulnerable': 'Población vulnerable',
    'etnia': 'Etnia',
    'tipo_afiliacion': 'Tipo de afiliación',
}

_MORTALIDAD_DB_MAPPING = {
    'nombres_apellidos': 'A. Nombres y Apellidos',
    'tipo_id': 'B. Tipo ID',
    'numero_id': 'C. Número ID',
    'sitio_defuncion': '5.1 Sitio de Defunción',
    'fecha_defuncion': '5.2 Fecha de defunción',
    'fecha_parto': '9.3 Fecha parto (dd/mm/aaaa)',
    'fecha_nacimiento': 'Fecha de Nacimiento',
    'edad': 'Edad',
    'convivencia': '6.1 Convivencia',
    'escolaridad': '6.3 Escolaridad',
    'regulacion_fecundidad': '6.4 Regulación Fecundidad',
    'gestaciones': '6.5 Gestaciones',
    'partos_vaginales': '6.6 Partos Vaginales',
    'cesareas': '6.7 Cesáreas',
    'nacidos_muertos': '6.8 Muertos',
    'hijos_vivos': '6.9 Vivos',
    'abortos': '6.10 Abortos',
    'num_cpn': '8.1 No. CPN',
    'semana_inicio_cpn': '8.2 Semana inicio CPN',
    'momento_muerte': '9.1 Momento de la muerte',
    'semana_gestacion_muerte': '9.2 Semana gestación',
    'tipo_parto': '9.4 Tipo de parto',
    'nivel_atencion_parto': '9.6 Nivel atención parto',
    'causa_basica_cie10': '10.1 Causa básica CIE-10',
    'demora_1': '10.3.1 Demora 1',
    'demora_2': '10.3.2 Demora 2',
    'demora_3': '10.3.3 Demora 3',
    'demora_4': '10.3.4 Demora 4',
    'zona_residencia': 'Zona de residencia',
    'poblacion_vulnerable': 'Población vulnerable',
    'etnia': 'Etnia',
    'tipo_afiliacion': 'Tipo de afiliación',
}


def _construir_df_desde_bd(db: Session, tipo: str) -> pd.DataFrame | None:
    """Reconstruye el DataFrame desde la vista de BD.

    Args:
        db: Sesión de base de datos.
        tipo: Tipo de análisis ('mortalidad' o 'morbilidad').

    Returns:
        DataFrame con todos los casos de la base de datos, o None si tipo es inválido.
    """
    dataframe_resultado: pd.DataFrame | None = None

    if tipo == 'mortalidad':
        registros = db.query(VMortalidadCompleta).order_by(VMortalidadCompleta.id_caso).all()
        mapping = _MORTALIDAD_DB_MAPPING
    elif tipo == 'morbilidad':
        registros = db.query(VMorbilidadCompleta).order_by(VMorbilidadCompleta.id_caso).all()
        mapping = _MORBILIDAD_DB_MAPPING
    else:
        return None

    if not registros:
        dataframe_resultado = pd.DataFrame(columns=mapping.values())
    else:
        records = []
        for r in registros:
            d = {}
            for key in mapping:
                val = getattr(r, key, None)
                d[key] = val.isoformat() if hasattr(val, 'isoformat') else val
            records.append(d)
        df_raw = pd.DataFrame.from_records(records)
        dataframe_resultado = df_raw.rename(columns=mapping)

    return dataframe_resultado


def _guardar_df_como_excel(
    df: pd.DataFrame,
    nombre_archivo: str,
) -> tuple[str, str, dict[str, int], int]:
    """Serializa un DataFrame a Excel, lo guarda en media/ y devuelve metadatos.

    Args:
        df: DataFrame a guardar.
        nombre_archivo: Nombre original del archivo subido.

    Returns:
        Tupla (ruta_relativa, archivo_hash, resumen, total_registros).
    """
    df_analisis, limpieza = preparar_dataframe_analisis(df)
    resumen = {
        'total_registros': len(df_analisis),
        'total_registros_original': limpieza['total_original'],
        'filas_vacias_omitidas': limpieza['filas_vacias_omitidas'],
        'filas_duplicadas_omitidas': limpieza['filas_duplicadas_omitidas'],
    }
    total_registros = resumen.pop('total_registros')

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_analisis.to_excel(writer, index=False)
    contenido = buffer.getvalue()

    now = datetime.now(timezone.utc)
    upload_dir = Path('media') / 'uploads' / str(now.year) / f'{now.month:02d}'
    upload_dir.mkdir(parents=True, exist_ok=True)

    safe_name = ''.join(c if c.isalnum() or c in ('.', '_', '-') else '_' for c in nombre_archivo)
    file_path = upload_dir / safe_name
    file_path.write_bytes(contenido)

    ruta = f'/media/uploads/{now.year}/{now.month:02d}/{safe_name}'
    archivo_hash = sha256(contenido).hexdigest()
    resultado_persistencia: tuple[str, str, dict[str, int], int] = (
        ruta,
        archivo_hash,
        resumen,
        total_registros,
    )
    return resultado_persistencia
