# Diagramas entidad-relación de VidaMaterna (notación de pata de gallo), dibujados DIRECTAMENTE
# desde la base PostgreSQL: tablas, columnas, tipos, llaves y cardinalidades salen del esquema real.
# Genera, en SVG (vectorial, se puede ampliar sin límite) y PNG:
#   bd_00_completa      todas las tablas
#   bd_01_nucleo        paciente, casos y datos comunes
#   bd_02_sistema       afiliación, usuarios, cargas, análisis y bitácora
#   bd_03_morbilidad    ficha 549
#   bd_04_mortalidad    ficha 550
#   bd_05_catalogos     tablas maestras (catálogos)
# En los diagramas por dominio, las llaves hacia un catálogo no se dibujan como línea: la columna
# lleva la anotación «→ cat_xxx» (así no se cruzan líneas). En el completo sí se dibujan (en gris).
#
# Uso:
#   set DB_HOST=localhost DB_PORT=5432 DB_USER=postgres DB_PASSWORD=...
#   python bd_completa.py NOMBRE_DE_LA_BASE [carpeta_de_salida]
import os
import sys
from collections import defaultdict

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import psycopg2
from matplotlib.patches import Rectangle

BD = sys.argv[1]
SALIDA = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(os.path.abspath(__file__))
con = psycopg2.connect(
    dbname=BD,
    host=os.environ.get('DB_HOST', 'localhost'),
    port=os.environ.get('DB_PORT', '5432'),
    user=os.environ['DB_USER'],
    password=os.environ['DB_PASSWORD'],
)
cur = con.cursor()

# ------------------------------------------------------------------ lectura del esquema
cur.execute("""SELECT table_name FROM information_schema.tables
               WHERE table_schema='public' AND table_type='BASE TABLE' ORDER BY 1""")
TABLAS = [r[0] for r in cur.fetchall()]
cur.execute("""SELECT table_name, column_name, data_type, character_maximum_length, numeric_precision,
                      numeric_scale, is_nullable
               FROM information_schema.columns WHERE table_schema='public'
               ORDER BY table_name, ordinal_position""")
COLS = defaultdict(list)
for t, c, tipo, largo, prec, esc, nulo in cur.fetchall():
    if t in TABLAS:
        corto = {
            'character varying': f'varchar({largo})',
            'integer': 'int',
            'boolean': 'bool',
            'timestamp without time zone': 'timestamp',
            'time without time zone': 'time',
            'numeric': f'numeric({prec},{esc})',
        }.get(tipo, tipo)
        COLS[t].append([c, corto, nulo == 'NO'])
cur.execute("""SELECT c.conrelid::regclass::text, a.attname, c.contype
               FROM pg_constraint c JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY(c.conkey)
               WHERE c.contype IN ('p','u') AND c.connamespace = 'public'::regnamespace
                 AND (c.contype = 'p' OR array_length(c.conkey, 1) = 1)""")
PK, UQ = defaultdict(set), defaultdict(set)
for t, col, tipo in cur.fetchall():
    (PK if tipo == 'p' else UQ)[t].add(col)
cur.execute("""SELECT i.indrelid::regclass::text, a.attname FROM pg_index i
               JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = i.indkey[0]
               WHERE i.indisunique AND i.indnatts = 1 AND NOT i.indisprimary""")
for t, col in cur.fetchall():
    UQ[t].add(col)
cur.execute("""SELECT c.conrelid::regclass::text, a.attname, c.confrelid::regclass::text
               FROM pg_constraint c JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = c.conkey[1]
               WHERE c.contype = 'f' AND c.connamespace = 'public'::regnamespace""")
FKS = list(cur.fetchall())
FKCOLS = defaultdict(set)
DESTINO_FK = {}
for t, col, ref in FKS:
    FKCOLS[t].add(col)
    DESTINO_FK[(t, col)] = ref

CATALOGOS = [t for t in TABLAS if t.startswith('cat_') and t != 'cat_evento'] + ['cie10']


def es_catalogo(t):
    return t in CATALOGOS


# ------------------------------------------------------------------ definición de los diagramas
C_SIS, C_NUC, C_MORB, C_MORT, C_CAT = '#E1D5E7', '#FFF2CC', '#DAE8FC', '#F8CECC', '#D5E8D4'
SISTEMA = [
    ['departamento', 'secretaria', 'cat_evento'],
    ['api_usuario', 'api_analisis'],
    ['narrativa_ia', 'api_sivigilaimportacion', 'auditoria_cambio'],
]
NUCLEO = [
    ['paciente', 'caso_morbilidad', 'caso_mortalidad'],
    ['antecedente_obstetrico', 'datos_sociodemograficos'],
]
MORB = [
    [
        'referencia',
        'referencia_institucion',
        'criterios_manejo',
        'manejo_hospitalario',
        'cirugia_adicional_morbilidad',
    ],
    ['antecedente_obstetrico_morbilidad', 'criterios_enfermedad', 'criterios_falla_organica'],
    ['causas_morbilidad', 'causa_asociada_morbilidad'],
]
MORT = [
    [
        'antecedente_materno_mortalidad',
        'control_prenatal',
        'antecedente_parto_puerperio',
        'causa_muerte',
    ],
    ['antecedente_riesgo'],
    ['complicacion_embarazo'],
]
CATS = [CATALOGOS[i : i + 6] for i in range(0, len(CATALOGOS), 6)]

DIAGRAMAS = [
    (
        'bd_00_completa',
        'Modelo de datos completo',
        True,
        [
            ('Afiliación, eventos y sistema', C_SIS, SISTEMA),
            ('Paciente y casos', C_NUC, NUCLEO),
            ('Morbilidad materna extrema (549)', C_MORB, MORB),
            ('Mortalidad materna (550)', C_MORT, MORT),
            ('Tablas maestras (catálogos)', C_CAT, CATS),
        ],
    ),
    ('bd_01_nucleo', 'Núcleo: paciente y casos', False, [('Paciente y casos', C_NUC, NUCLEO)]),
    (
        'bd_02_sistema',
        'Afiliación, usuarios, cargas y bitácora',
        False,
        [('Sistema', C_SIS, SISTEMA)],
    ),
    (
        'bd_03_morbilidad',
        'Morbilidad materna extrema (ficha 549)',
        False,
        [('Morbilidad', C_MORB, MORB)],
    ),
    ('bd_04_mortalidad', 'Mortalidad materna (ficha 550)', False, [('Mortalidad', C_MORT, MORT)]),
    ('bd_05_catalogos', 'Tablas maestras (catálogos)', False, [('Catálogos', C_CAT, CATS)]),
]
dibujadas = {t for _, _, cols in DIAGRAMAS[0][3] for col in cols for t in col}
assert dibujadas == set(
    TABLAS
), f'sin ubicar: {set(TABLAS) - dibujadas}; sobran: {dibujadas - set(TABLAS)}'

RH, HH, CHAR = 17, 24, 6.0


VISIBLES = set()  # tablas dibujadas en el diagrama actual


def anotacion(t, c):
    """Texto «→ tabla» de una columna con llave hacia un catálogo o una tabla de otro diagrama."""
    ref = DESTINO_FK.get((t, c))
    return f' → {ref}' if ref and (es_catalogo(ref) or ref not in VISIBLES) else ''


def filas(t, stub):
    if stub:
        return [x for x in COLS[t] if x[0] in PK[t]]
    return COLS[t]


def tam(t, dominio, stub):
    fs = filas(t, stub)
    texto = [f'PK/FK {c}{anotacion(t, c) if dominio else ""} {tp} NN' for c, tp, _ in fs]
    ancho = max(len(t) * 7.6 + 24, max(len(x) for x in texto) * CHAR + 56)
    return max(ancho, 200), HH + RH * len(fs)


def dibujar(archivo, titulo, completo, grupos):
    dominio = not completo
    global VISIBLES
    VISIBLES = {t for _, _, cols in grupos for col in cols for t in col}
    stubs = []
    POS = {}
    x = 40
    GAP, GAPX, GAPG = 28, 70, 90
    cabeceras = []
    for nombre, color, columnas in grupos:
        x_ini = x
        for col in columnas:
            y, ancho_col = 130, 0
            for t in col:
                w, h = tam(t, dominio, t in stubs)
                POS[t] = (x, y, w, h, color, t in stubs)
                y += h + GAP
                ancho_col = max(ancho_col, w)
            x += ancho_col + GAPX
        cabeceras.append((nombre, color, x_ini, x - GAPX))
        x += GAPG - GAPX
    ANCHO = x + 20
    ALTO = max(p[1] + p[3] for p in POS.values()) + 60
    fig = plt.figure(figsize=(ANCHO / 100, ALTO / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, ANCHO)
    ax.set_ylim(ALTO, 0)
    ax.axis('off')
    n_t = len([t for t in POS if t not in stubs])
    ax.text(
        40,
        30,
        f'VidaMaterna (MaternAnalytics) · {titulo}',
        fontsize=17,
        fontweight='bold',
        va='center',
    )
    ax.text(
        40,
        52,
        'Notación de pata de gallo · PK = llave primaria · FK = llave foránea · UQ = único · '
        'NN = no admite nulo',
        fontsize=9.5,
        va='center',
        color='#444',
    )
    ax.text(
        40,
        70,
        (
            '«→ tabla» = llave hacia una tabla maestra o de otro diagrama'
            if dominio
            else 'línea gris = llave hacia una tabla maestra'
        ),
        fontsize=9.5,
        va='center',
        color='#2E7D32',
    )
    for nombre, color, xa, xb in cabeceras:
        ax.add_patch(Rectangle((xa - 6, 112), xb - xa + 12, 6, fc=color, ec='none'))
        ax.text(xa, 108, nombre, fontsize=11.5, fontweight='bold', va='bottom')

    def fila_y(t, col):
        nombres = [c for c, _, _ in filas(t, t in stubs)]
        return POS[t][1] + HH + RH * (nombres.index(col) + 0.5)

    def pata(p, d, tipo, color, lw):
        px, py = p
        if tipo == 'muchos':
            for s in (-6, 6):
                ax.plot([px, px + d * 11], [py, py + s], color=color, lw=lw, solid_capstyle='butt')
            ax.plot([px + d * 11] * 2, [py - 5, py + 5], color=color, lw=lw)
        else:
            for k in (9, 13):
                ax.plot([px + d * k] * 2, [py - 5, py + 5], color=color, lw=lw)

    n = 0
    for t, col, ref in FKS:
        if t not in POS or ref not in POS:
            continue
        maestra = es_catalogo(ref)
        if dominio and maestra:
            continue
        n += 1
        uno = col in UQ[t] or col in PK[t]
        yc = fila_y(t, col)
        yr = fila_y(ref, sorted(PK[ref])[0])
        xt, wt, xr, wr = POS[t][0], POS[t][2], POS[ref][0], POS[ref][2]
        color, lw = ('#9A9A9A', 0.7) if maestra else ('#222222', 1.1)
        if abs(xt - xr) < 5:  # misma columna: codo por el costado izquierdo
            off = 10 + 5 * (n % 5)
            ax.plot([xt, xt - off, xt - off, xt], [yc, yc, yr, yr], color=color, lw=lw, zorder=1)
            pata((xt, yc), -1, 'uno' if uno else 'muchos', color, lw)
            pata((xt, yr), -1, 'uno', color, lw)
        else:
            if xt > xr:
                p1, d1, p2, d2 = xt, -1, xr + wr, 1
            else:
                p1, d1, p2, d2 = xt + wt, 1, xr, -1
            xm = (p1 + p2) / 2 + (n % 7 - 3) * 4
            ax.plot([p1, xm, xm, p2], [yc, yc, yr, yr], color=color, lw=lw, zorder=1)
            pata((p1, yc), d1, 'uno' if uno else 'muchos', color, lw)
            pata((p2, yr), d2, 'uno', color, lw)

    for t, (x0, y0, w, h, color, stub) in POS.items():
        ax.add_patch(
            Rectangle(
                (x0, y0), w, h, fc='white', ec='black', lw=1.0, ls='--' if stub else '-', zorder=3
            )
        )
        ax.add_patch(
            Rectangle((x0 + 0.5, y0 + 0.5), w - 1, HH - 0.5, fc=color, ec='none', zorder=4)
        )
        ax.text(
            x0 + w / 2,
            y0 + HH / 2,
            t,
            ha='center',
            va='center',
            fontsize=9.2,
            fontweight='bold',
            zorder=5,
        )
        ax.plot([x0, x0 + w], [y0 + HH, y0 + HH], color='black', lw=1.0, zorder=5)
        for i, (c, tp, nn) in enumerate(filas(t, stub)):
            yy = y0 + HH + RH * (i + 0.5)
            marca = (
                'PK/FK'
                if c in PK[t] and c in FKCOLS[t]
                else 'PK'
                if c in PK[t]
                else 'FK'
                if c in FKCOLS[t]
                else 'UQ'
                if c in UQ[t]
                else ''
            )
            if marca:
                ax.text(
                    x0 + 6,
                    yy,
                    marca,
                    fontsize=7.6,
                    fontweight='bold',
                    va='center',
                    zorder=5,
                    color='#7A1F1F' if 'FK' in marca else 'black',
                )
            ax.text(x0 + 46, yy, c, fontsize=8, va='center', zorder=5)
            if dominio and anotacion(t, c):
                ax.text(
                    x0 + 46 + len(c) * 5.9 + 6,
                    yy,
                    anotacion(t, c),
                    fontsize=7.4,
                    va='center',
                    color='#2E7D32',
                    zorder=5,
                )
            ax.text(
                x0 + w - 6,
                yy,
                tp + (' NN' if nn and c not in PK[t] else ''),
                fontsize=7.2,
                va='center',
                ha='right',
                color='#555',
                zorder=5,
            )
    os.makedirs(SALIDA, exist_ok=True)
    fig.savefig(os.path.join(SALIDA, archivo + '.svg'), format='svg')
    fig.savefig(os.path.join(SALIDA, archivo + '.png'), dpi=170)
    plt.close(fig)
    print(f'{archivo}: {n_t} tablas, {n} relaciones dibujadas')


for archivo, titulo, completo, grupos in DIAGRAMAS:
    dibujar(archivo, titulo, completo, grupos)
