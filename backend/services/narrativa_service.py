"""Orquesta la generación y cache de narrativas de IA a partir de indicadores agregados."""

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from db.models_sqlalchemy import Analisis, NarrativaIA
from services import ia_client


def calcular_filtros_hash(filtros: dict[str, Any]) -> str:
    """Calcula un hash estable de los filtros activos para usar como clave de cache.

    Args:
        filtros: Diccionario de filtros (year, month, tipo_clustering, n_clusters, etc.).

    Returns:
        Hash SHA-256 hexadecimal de los filtros serializados de forma determinista.
    """
    filtros_serializados = json.dumps(filtros, sort_keys=True, default=str)
    return hashlib.sha256(filtros_serializados.encode('utf-8')).hexdigest()


def obtener_narrativa(
    db: Session,
    analisis: Analisis,
    tipo_narrativa: str,
    indicadores: dict[str, Any],
    filtros: dict[str, Any],
    regenerar: bool,
) -> dict[str, Any]:
    """Obtiene la narrativa desde cache, o la genera y la cachea si no existe.

    Args:
        db: Sesión de base de datos.
        analisis: Instancia del análisis al que pertenece la narrativa.
        tipo_narrativa: 'resumen_ejecutivo', 'demoras', 'clustering' o 'tendencias'.
        indicadores: Datos agregados relevantes ya calculados por el llamador.
        filtros: Filtros activos (year, month, tipo_clustering, n_clusters) usados para
            la clave de cache.
        regenerar: Si es True, ignora la cache y fuerza una nueva llamada a IA-SERVICE.

    Returns:
        Dict con `narrativa`, `modelo`, `generado_en` y `desde_cache`.

    Raises:
        services.ia_client.IAServiceUnavailableError: Si IA-SERVICE no está disponible.
    """
    filtros_hash = calcular_filtros_hash(filtros)

    if not regenerar:
        existente = (
            db.query(NarrativaIA)
            .filter_by(
                analisis_id=analisis.id,
                tipo_narrativa=tipo_narrativa,
                filtros_hash=filtros_hash,
            )
            .first()
        )
        if existente is not None:
            return {
                'narrativa': existente.contenido,
                'modelo': existente.modelo,
                'generado_en': existente.generado_en,
                'desde_cache': True,
            }

    resultado_ia = ia_client.generar_narrativa(tipo_narrativa, analisis.tipo, indicadores)
    texto = resultado_ia['narrativa']
    modelo = resultado_ia['modelo']
    ahora = datetime.now(timezone.utc)

    registro = (
        db.query(NarrativaIA)
        .filter_by(
            analisis_id=analisis.id,
            tipo_narrativa=tipo_narrativa,
            filtros_hash=filtros_hash,
        )
        .first()
    )
    if registro is not None:
        registro.contenido = texto
        registro.modelo = modelo
        registro.generado_en = ahora
    else:
        registro = NarrativaIA(
            analisis_id=analisis.id,
            tipo_narrativa=tipo_narrativa,
            filtros_hash=filtros_hash,
            contenido=texto,
            modelo=modelo,
            generado_en=ahora,
        )
        db.add(registro)
    db.commit()

    return {'narrativa': texto, 'modelo': modelo, 'generado_en': ahora, 'desde_cache': False}


def extraer_indicadores_para_narrativa(
    tipo_narrativa: str,
    analisis_completo: dict[str, Any] | None,
    clustering_resultado: dict[str, Any] | None,
) -> dict[str, Any]:
    """Filtra el dict completo de indicadores al subconjunto relevante para cada narrativa.

    Nunca reenvía columnas por-registro (p. ej. `pca_2d`, `pca_3d`, `clusters` de
    clustering) — solo agregados ya resumidos, para no sobrecargar el prompt ni
    exponer datos con granularidad de caso individual.

    Args:
        tipo_narrativa: 'resumen_ejecutivo', 'demoras', 'clustering' o 'tendencias'.
        analisis_completo: Resultado de `calcular_completo`, o None si no aplica.
        clustering_resultado: Resultado de `ejecutar_clustering`, o None si no aplica.

    Returns:
        Subconjunto de indicadores agregados relevante para la narrativa pedida.

    Raises:
        ValueError: Si `tipo_narrativa` es inválido, o si falta el resultado necesario.
    """
    if tipo_narrativa == 'resumen_ejecutivo':
        if analisis_completo is None:
            raise ValueError('Se requiere analisis_completo para resumen_ejecutivo')
        claves = ['estadisticas_basicas', 'causas_cie10', 'criterios_inclusion']
        return {k: analisis_completo[k] for k in claves if k in analisis_completo}

    if tipo_narrativa == 'demoras':
        if analisis_completo is None:
            raise ValueError('Se requiere analisis_completo para demoras')
        if 'demoras' in analisis_completo:
            return {'demoras': analisis_completo['demoras']}
        return {'tiempo_remision': analisis_completo.get('tiempo_remision', {})}

    if tipo_narrativa == 'tendencias':
        if analisis_completo is None:
            raise ValueError('Se requiere analisis_completo para tendencias')
        return {'distribucion_mensual': analisis_completo.get('distribucion_mensual', {})}

    if tipo_narrativa == 'clustering':
        if clustering_resultado is None:
            raise ValueError('Se requiere clustering_resultado para clustering')
        claves = ['n_clusters', 'n_samples', 'features_used', 'cluster_sizes', 'cluster_profiles']
        return {k: clustering_resultado[k] for k in claves if k in clustering_resultado}

    raise ValueError(f'tipo_narrativa inválido: {tipo_narrativa}')
