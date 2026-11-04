"""Pruebas de la verificación automática de narrativas de IA (observación 9 de la asesora)."""

from services.narrativa_verificacion import cifras_del_texto, verificar_narrativa

INDICADORES = {
    'estadisticas_basicas': {'total_casos': 2000, 'edad_promedio': 30.6, 'cesareas_pct': 41.25},
    'causas_cie10': [{'codigo': 'O14.1', 'casos': 310, 'porcentaje': 15.5}],
}


def test_cifras_respaldadas_y_no_respaldadas():
    """Una cifra que no sale de los indicadores se marca; las que coinciden cuentan."""
    texto = (
        'Se registraron 2.000 casos con una edad promedio de 30,6 años. '
        'La causa O14.1 representó el 15,5% de los casos y las cesáreas el 99%.'
    )
    v = verificar_narrativa(texto, INDICADORES)
    assert v['cifras_total'] == 4
    assert v['cifras_respaldadas'] == 3
    assert v['cifras_sin_respaldo'] == ['99']


def test_codigos_cie10_y_demoras_no_cuentan_como_cifras():
    """Los códigos CIE-10, 'demora 1' y la numeración '(1)' no son datos."""
    texto = 'Demora 1 y CIE-10: O14.1 y O72.1. (1) Total 25 casos.'
    assert [c for c, *_ in cifras_del_texto(texto)] == ['25']


def test_lenguaje_prescriptivo_y_causal_genera_alerta():
    """Una narrativa descriptiva no debe recomendar tratamientos ni afirmar causalidad."""
    texto = (
        'Se recomienda iniciar tratamiento con sulfato de magnesio '
        'porque la edad causó la eclampsia en estas mujeres.'
    )
    alertas = verificar_narrativa(texto, INDICADORES)['alertas_coherencia']
    assert any('prescriptivo' in a for a in alertas)
    assert any('causal' in a for a in alertas)


def test_codigo_cie10_inventado_genera_alerta():
    """Un código CIE-10 que no está en los indicadores de origen no está sustentado."""
    texto = 'Predominó la causa O85 con 15,5% de los casos, seguida de O14.1 con 310 casos.'
    alertas = verificar_narrativa(texto, INDICADORES)['alertas_coherencia']
    assert any('O85' in a for a in alertas)
    assert not any('O14.1' in a for a in alertas)


def test_identificador_de_persona_genera_alerta():
    """Un número de documento (7 o más dígitos) no debe aparecer en una narrativa agregada."""
    texto = 'La paciente con documento 1234567890 falleció durante el periodo analizado.'
    alertas = verificar_narrativa(texto, INDICADORES)['alertas_coherencia']
    assert any('identificador' in a for a in alertas)


def test_texto_vacio_o_muy_corto_genera_alerta():
    """Un texto casi vacío no es una narrativa utilizable."""
    assert verificar_narrativa('Ok.', INDICADORES)['alertas_coherencia']


def test_narrativa_coherente_no_genera_alertas():
    """Una narrativa descriptiva con cifras de origen no produce alertas."""
    texto = (
        'En los 2.000 casos analizados, la causa O14.1 aparece en 310 casos, el 15,5% del total.'
    )
    v = verificar_narrativa(texto, INDICADORES)
    assert v['alertas_coherencia'] == []
    assert v['cifras_sin_respaldo'] == []
