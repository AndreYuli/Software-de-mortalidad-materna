"""Lote 3 de la validación de narrativas: Groq / openai/gpt-oss-20b (mismo procedimiento del LOTE 2 del manuscrito,
el del 3-nov-2026 con gemma-4-31b-it: lote_narrativas_3-nov.json; val2 fue el lote 1).

Reutiliza: el verificador de la plataforma tal como estaba al generar el lote 2 (narrativa_verificacion_a520cdbf.py,
copia de `git show a520cdbf:backend/services/narrativa_verificacion.py`), los prompts de producción de ia-service y
los procesadores de indicadores del backend. Criterio: ver criterio.md.

Uso (PowerShell):
    $env:LLM_API_KEY = Read-Host "Clave Groq"            # la clave solo vive en esta sesión
    python validacion3_gpt-oss.py                        # todo: indicadores -> 18 solicitudes -> análisis
    python validacion3_gpt-oss.py --simulado             # sin red: respuestas falsas, salida en simulado/
    python validacion3_gpt-oss.py narrativas|analisis    # pasos sueltos (indicadores usa el venv del backend)

Si se corta (429 diario, red), se vuelve a ejecutar y retoma las solicitudes ya guardadas.
Solo se envían indicadores agregados de datos sintéticos. La clave se lee SOLO de LLM_API_KEY.
"""

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

SIMULADO = '--simulado' in sys.argv
ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]

REPO = (
    Path(__file__).resolve().parents[2]
)  # raíz del repo (scripts/validacion_narrativas/)
BACKEND, IA = REPO / 'backend', REPO / 'ia-service'
FIXTURES = REPO / 'frontend' / 'maternanalytics' / 'e2e' / 'fixtures'
AQUI = Path(__file__).resolve().parent
SALIDA = AQUI / 'simulado' if SIMULADO else AQUI
SALIDA.mkdir(exist_ok=True)
F_IND, F_NAR = SALIDA / 'val3_indicadores.json', SALIDA / 'val3_narrativas.json'
sys.path.insert(0, str(AQUI))
F_JSON, F_TXT = (
    SALIDA / 'resultado_validacion3.json',
    SALIDA / 'resultado_validacion3.txt',
)

BASE_URL = (
    'https://api.groq.com/openai/v1'  # LLM_BASE_URL del servidor (DEPLOY.md sección 6)
)
MODELO = 'openai/gpt-oss-20b'
N_REPETICIONES = 3
# Mortalidad: el lote 2 tenía 400 casos = mortalidad-realista-200 + mortalidad-valida-pequena (inferido, ver criterio.md)
ARCHIVOS = {
    'mortalidad': ['mortalidad-realista-200.xlsx', 'mortalidad-valida-pequena.xlsx'],
    'morbilidad': ['morbilidad-realista-200.xlsx'],
}
EVENTOS = ['mortalidad', 'morbilidad']
TIPOS = ['resumen_ejecutivo', 'demoras', 'tendencias']
TIMEOUT_S = 120.0  # igual que OLLAMA_TIMEOUT_S por defecto en ia-service
REINTENTOS_429, ESPERA_429_S, PAUSA_ENTRE_S = (
    6,
    30.0,
    8.0,
)  # TPM observado: 8.000 (DEPLOY.md)


# ---------- Paso 1 (venv del backend): indicadores ----------
def paso_indicadores():
    import pandas as pd

    sys.path.insert(0, str(BACKEND))
    from services._analisis_excel import (
        _canonizar_columnas_dataframe,
        preparar_dataframe_analisis,
    )
    from services._analisis_filtros import _calcular_distribucion_mensual
    from services._morbilidad_processor import MorbilidadProcessor
    from services._mortalidad_processor import MortalidadProcessor
    from utils.json_utils import _sanitize_json

    todo = {}
    for ev, Proc in [
        ('mortalidad', MortalidadProcessor),
        ('morbilidad', MorbilidadProcessor),
    ]:
        partes = []
        for f in ARCHIVOS[ev]:
            d = _canonizar_columnas_dataframe(pd.read_excel(FIXTURES / f), ev)
            partes.append(preparar_dataframe_analisis(d)[0])
        df = pd.concat(partes, ignore_index=True)
        # El Excel dice «(horas)»; en producción la BD lo entrega como «Tiempo remisión (h)» (_analisis_persistencia.py)
        df = df.rename(columns={'Tiempo remisión (horas)': 'Tiempo remisión (h)'})
        p = Proc(df)
        r = {
            'estadisticas_basicas': p.calcular_estadisticas_basicas(),
            'causas_cie10': p.analizar_causas_cie10(top_n=10),
            'distribucion_mensual': _calcular_distribucion_mensual(df, ev),
        }
        if ev == 'mortalidad':
            r['demoras'] = p.analizar_demoras()
        else:
            r.update(
                criterios_inclusion=p.analizar_criterios_inclusion(),
                severidad_fallas=p.analizar_severidad_fallas(),
                tiempo_remision=p.analizar_tiempo_remision(),
            )
        todo[ev] = {'n_filas': len(df), **_sanitize_json(r)}
    F_IND.write_text(
        json.dumps(todo, ensure_ascii=False, default=float), encoding='utf-8'
    )
    print('indicadores:', {e: todo[e]['n_filas'] for e in todo}, '->', F_IND.name)


def indicadores_de(todo, evento, tipo):
    """Subconjunto por tipo: copia de narrativa_service.extraer_indicadores_para_narrativa (backend)."""
    d = todo[evento]
    if tipo == 'resumen_ejecutivo':
        return {
            k: d[k]
            for k in [
                'estadisticas_basicas',
                'causas_cie10',
                'criterios_inclusion',
                'severidad_fallas',
            ]
            if k in d
        }
    if tipo == 'demoras':
        return (
            {'demoras': d['demoras']}
            if 'demoras' in d
            else {'tiempo_remision': d.get('tiempo_remision', {})}
        )
    return {'distribucion_mensual': d.get('distribucion_mensual', {})}


# ---------- Paso 2: 18 solicitudes ----------
def llamar_groq(prompt):
    """Igual que ia-service/ollama_client._chat_openai, más reintentos ante 429. Devuelve (JSON, latencia_s, intentos)."""
    clave = os.environ.get('LLM_API_KEY')
    if not clave:
        sys.exit('Falta la variable de entorno LLM_API_KEY (o usa --simulado).')
    cuerpo = json.dumps(
        {'model': MODELO, 'messages': [{'role': 'user', 'content': prompt}]}
    ).encode()
    for intento in range(1, REINTENTOS_429 + 2):
        req = urllib.request.Request(
            f'{BASE_URL}/chat/completions',
            cuerpo,
            method='POST',
            headers={
                'Authorization': f'Bearer {clave}',
                'Content-Type': 'application/json',
                'User-Agent': 'validacion3/1.0',
            },
        )
        t0 = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
                return json.loads(r.read()), time.perf_counter() - t0, intento
        except urllib.error.HTTPError as e:
            if e.code == 429 and intento <= REINTENTOS_429:
                espera = float(e.headers.get('retry-after') or ESPERA_429_S) + 1
                print(f'    429 (intento {intento}): espero {espera:.0f} s', flush=True)
                time.sleep(espera)
                continue
            sys.exit(
                f'Groq devolvió {e.code}: {e.read().decode(errors="replace")[:500]}'
            )
        except (urllib.error.URLError, TimeoutError) as e:
            sys.exit(f'No se pudo contactar a Groq: {e}')


def respuesta_falsa(indicadores):
    """Texto de prueba (--simulado): usa cifras reales de los indicadores y una inventada (99.9%)."""
    from narrativa_verificacion_a520cdbf import numeros_de

    nums = [n for n in numeros_de(indicadores) if n == int(n) or 0 < n < 100][:4]
    return (
        'Texto SIMULADO. Cifras de origen: '
        + ', '.join(str(round(n, 2)) for n in nums)
        + '. Cifra inventada: 99.9% (demora 2, O75.1).'
    )


def paso_narrativas():
    sys.path.insert(0, str(IA))
    from prompts import (
        construir_prompt,
    )  # solo stdlib; NO se importa core.config (leería ia-service/.env)

    todo = json.loads(F_IND.read_text(encoding='utf-8'))
    salida = (
        json.loads(F_NAR.read_text(encoding='utf-8'))
        if F_NAR.exists()
        else {'modelo': MODELO, 'simulado': SIMULADO, 'narrativas': []}
    )
    hechas = {(n['evento'], n['tipo'], n['rep']) for n in salida['narrativas']}
    for evento in EVENTOS:
        for tipo in TIPOS:
            ind = indicadores_de(todo, evento, tipo)
            for rep in range(1, N_REPETICIONES + 1):
                if (evento, tipo, rep) in hechas:
                    continue
                prompt = construir_prompt(tipo, ind, evento)
                fecha = datetime.now().astimezone().isoformat(timespec='seconds')
                if SIMULADO:
                    texto, crudo, lat, intentos, modelo_id = (
                        respuesta_falsa(ind),
                        {'simulado': True},
                        0.0,
                        1,
                        MODELO + ' (simulado)',
                    )
                else:
                    crudo, lat, intentos = llamar_groq(prompt)
                    texto, modelo_id = (
                        crudo['choices'][0]['message']['content'] or '',
                        crudo.get('model', ''),
                    )
                    time.sleep(PAUSA_ENTRE_S)
                salida['narrativas'].append(
                    {
                        'evento': evento,
                        'tipo': tipo,
                        'rep': rep,
                        'fecha': fecha,
                        'modelo_id': modelo_id,
                        'latencia_s': round(lat, 2),
                        'intentos': intentos,
                        'prompt_chars': len(prompt),
                        'texto': texto,
                        'indicadores': ind,
                        'respuesta_cruda': crudo,
                    }
                )
                F_NAR.write_text(
                    json.dumps(salida, ensure_ascii=False, indent=1), encoding='utf-8'
                )  # guarda tras cada una
                print(
                    f'  generada: {evento}/{tipo} #{rep}  ({lat:.1f} s, {len(texto)} car.)',
                    flush=True,
                )


# ---------- Paso 3: verificador del lote 2 ----------
def paso_analisis():
    from narrativa_verificacion_a520cdbf import verificar_narrativa

    d = json.loads(F_NAR.read_text(encoding='utf-8'))
    filas, malas_todas, alertas = [], [], []
    for n in d['narrativas']:
        v = verificar_narrativa(n['texto'], n['indicadores'])
        filas.append(
            (
                n['evento'],
                n['tipo'],
                n['rep'],
                v['cifras_total'],
                v['cifras_respaldadas'],
            )
        )
        malas_todas += [
            (n['evento'], n['tipo'], n['rep'], c, '') for c in v['cifras_sin_respaldo']
        ]
        alertas += [
            (n['evento'], n['tipo'], n['rep'], a) for a in v['alertas_coherencia']
        ]
    N = {
        e: json.loads(F_IND.read_text(encoding='utf-8'))[e]['n_filas'] for e in EVENTOS
    }
    L, ancho = [], 80
    ids = sorted({n['modelo_id'] for n in d['narrativas']})
    L += [
        '=' * ancho,
        'VALIDACIÓN 3 - CIFRAS DE LAS NARRATIVAS DE IA'
        + ('  [SIMULADO: NO ES RESULTADO REAL]' if SIMULADO else ''),
        f'Modelo: {d["modelo"]} (devuelto por la API: {", ".join(ids)}) | {N_REPETICIONES} repeticiones por tipo | datos E2E (mortalidad {N['mortalidad']}, morbilidad {N['morbilidad']} casos)',
        'Coincide = la cifra del texto es igual a un indicador de origen (redondeada como aparece)',
        '=' * ancho,
        f'{"Evento":<11}{"Narrativa":<19}{"Rep.":>5}{"Cifras":>8}{"Coinciden":>11}{"%":>8}',
        '-' * ancho,
    ]
    L += [
        f'{ev:<11}{t:<19}{rep:>5}{c:>8}{ok:>11}{(ok / c * 100 if c else 100):>7.0f}%'
        for ev, t, rep, c, ok in filas
    ]
    L.append('-' * ancho)
    for ev in EVENTOS:
        for t in TIPOS:
            sel = [f for f in filas if f[0] == ev and f[1] == t]
            c, ok = sum(f[3] for f in sel), sum(f[4] for f in sel)
            L.append(
                f'{ev:<11}{t:<19}{"total":>5}{c:>8}{ok:>11}{(ok / c * 100 if c else 100):>7.1f}%'
            )
    C, OK = sum(f[3] for f in filas), sum(f[4] for f in filas)
    sin_error = sum(1 for f in filas if f[3] == f[4])
    L += [
        '=' * ancho,
        f'TOTAL: {OK}/{C} cifras coinciden ({OK / C * 100 if C else 100:.1f}%) | narrativas sin ninguna cifra fuera de los datos: {sin_error}/{len(filas)}',
        '=' * ancho,
    ]
    if malas_todas:
        L.append('\nCIFRAS QUE NO COINCIDEN DIRECTAMENTE (revisar una a una):')
        L += [f'  {ev}/{t} #{rep}: «{c}»' for ev, t, rep, c, ctx in malas_todas]
    if alertas:
        L.append('\nALERTAS DE COHERENCIA DEL VERIFICADOR (tal como en el lote 2):')
        L += [f'  {ev}/{t} #{rep}: {a}' for ev, t, rep, a in alertas]
    F_TXT.write_text('\n'.join(L) + '\n', encoding='utf-8')
    F_JSON.write_text(
        json.dumps(
            {
                'simulado': SIMULADO,
                'modelo': d['modelo'],
                'modelo_ids': ids,
                'total_cifras': C,
                'coinciden': OK,
                'filas': [
                    dict(zip(['evento', 'tipo', 'rep', 'cifras', 'coinciden'], f))
                    for f in filas
                ],
                'no_coinciden': [
                    dict(zip(['evento', 'tipo', 'rep', 'cifra', 'contexto'], m))
                    for m in malas_todas
                ],
                'alertas': [
                    dict(zip(['evento', 'tipo', 'rep', 'alerta'], a)) for a in alertas
                ],
            },
            ensure_ascii=False,
            indent=1,
        ),
        encoding='utf-8',
    )
    print('\n'.join(L))


if __name__ == '__main__':
    paso = ARGS[0] if ARGS else 'todo'
    if paso == 'indicadores':
        paso_indicadores()
    elif paso == 'narrativas':
        paso_narrativas()
    elif paso == 'analisis':
        paso_analisis()
    else:
        env = {**os.environ, 'PYTHONIOENCODING': 'utf-8'}
        subprocess.run(
            [
                str(BACKEND / 'venv' / 'Scripts' / 'python.exe'),
                str(Path(__file__).resolve()),
                'indicadores',
                *(['--simulado'] if SIMULADO else []),
            ],
            cwd=BACKEND,
            check=True,
            env=env,
        )
        paso_narrativas()
        paso_analisis()
