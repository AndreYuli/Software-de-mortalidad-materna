# Diagrama entidad-relación COMPLETO de VidaMaterna (notación de pata de gallo), dibujado
# directamente desde la base PostgreSQL: tablas, columnas, tipos, llaves y cardinalidades salen
# del esquema real, no se escriben a mano. Genera un SVG (vectorial: se puede ampliar sin límite)
# y un PNG de alta resolución.
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
    if t not in TABLAS:
        continue
    corto = {
        'character varying': f'varchar({largo})',
        'integer': 'int',
        'smallint': 'smallint',
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
# índices únicos de una sola columna también cuentan como «uno a uno»
cur.execute("""SELECT i.indrelid::regclass::text, a.attname FROM pg_index i
               JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = i.indkey[0]
               WHERE i.indisunique AND i.indnatts = 1 AND NOT i.indisprimary""")
for t, col in cur.fetchall():
    UQ[t].add(col)

cur.execute("""SELECT c.conrelid::regclass::text, a.attname, c.confrelid::regclass::text
               FROM pg_constraint c JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = c.conkey[1]
               WHERE c.contype = 'f' AND c.connamespace = 'public'::regnamespace""")
FKS = [(t, col, ref) for t, col, ref in cur.fetchall()]
FKCOLS = defaultdict(set)
for t, col, _ in FKS:
    FKCOLS[t].add(col)

# ------------------------------------------------------------------ grupos y posiciones
GRUPOS = [
    (
        'Afiliación, eventos y sistema',
        '#E1D5E7',
        40,
        [
            'departamento',
            'secretaria',
            'cat_evento',
            'api_usuario',
            'api_analisis',
            'narrativa_ia',
            'api_sivigilaimportacion',
            'auditoria_cambio',
        ],
    ),
    (
        'Paciente y casos',
        '#FFF2CC',
        440,
        [
            'paciente',
            'caso_morbilidad',
            'caso_mortalidad',
            'antecedente_obstetrico',
            'datos_sociodemograficos',
        ],
    ),
    (
        'Morbilidad materna extrema (549)',
        '#DAE8FC',
        880,
        [
            'referencia',
            'referencia_institucion',
            'antecedentes_obstetricos',
            'criterios_enfermedad',
            'criterios_falla_organica',
            'criterios_manejo',
            'manejo_hospitalario',
            'cirugia_adicional_morbilidad',
            'causas_morbilidad',
            'causa_asociada_morbilidad',
        ],
    ),
    (
        'Mortalidad materna (550)',
        '#F8CECC',
        1320,
        [
            'antecedente_materno',
            'antecedente_riesgo',
            'complicacion_embarazo',
            'control_prenatal',
            'antecedente_parto_puerperio',
            'causa_muerte',
        ],
    ),
    (
        'Tablas maestras (catálogos)',
        '#D5E8D4',
        1760,
        [t for t in TABLAS if t.startswith('cat_') and t != 'cat_evento'] + ['cie10'],
    ),
]
asignadas = {t for _, _, _, ts in GRUPOS for t in ts}
faltan = [t for t in TABLAS if t not in asignadas]
sobran = [t for t in asignadas if t not in TABLAS]
assert not faltan and not sobran, f'tablas sin ubicar: {faltan}; que no existen: {sobran}'

RH, HH, CHAR = 17, 24, 6.0
CENTRAR = {}


def tam(t):
    filas = [f'{"PK/FK" if True else ""} {c} {tp} NN' for c, tp, _ in COLS[t]]
    ancho = max(len(t) * 7.4 + 20, max(len(f) for f in filas) * CHAR + 56)
    return max(ancho, 190), HH + RH * len(COLS[t])


POS = {}
GAP = 26
ALTO_MAX = 2900
for nombre, color, x0, tablas in GRUPOS:
    x, y, colmax, ancho_col = x0, 110, 0, 0
    for t in tablas:
        w, h = tam(t)
        if y + h > ALTO_MAX and y > 110:  # nueva sub-columna
            x += ancho_col + GAP
            y, ancho_col = 110, 0
        POS[t] = (x, y, w, h, color)
        y += h + GAP
        ancho_col = max(ancho_col, w)
        colmax = max(colmax, x + w)

ANCHO = max(p[0] + p[2] for p in POS.values()) + 60
ALTO = max(p[1] + p[3] for p in POS.values()) + 90
fig = plt.figure(figsize=(ANCHO / 100, ALTO / 100), dpi=100)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, ANCHO)
ax.set_ylim(ALTO, 0)
ax.axis('off')
ax.text(
    40,
    28,
    'VidaMaterna (MaternAnalytics) · modelo de datos de la base de datos',
    fontsize=17,
    fontweight='bold',
    va='center',
)
ax.text(
    40,
    50,
    f'{len(TABLAS)} tablas · {len(FKS)} llaves foráneas · notación de pata de gallo · '
    'PK = llave primaria · FK = llave foránea · UQ = único · NN = no admite nulo · '
    'trazo gris = relación con una tabla maestra',
    fontsize=9.5,
    va='center',
    color='#444',
)

# encabezados de grupo
for nombre, color, x0, tablas in GRUPOS:
    xs = [POS[t][0] for t in tablas]
    xe = [POS[t][0] + POS[t][2] for t in tablas]
    ax.add_patch(Rectangle((min(xs) - 8, 98), max(xe) - min(xs) + 16, 6, fc=color, ec='none'))
    ax.text(min(xs), 94, nombre, fontsize=11, fontweight='bold', va='bottom')

# ------------------------------------------------------------------ relaciones (debajo de las tablas)


def borde(t, hacia):
    """Punto del borde de la tabla `t` más cercano a (hx, hy), a la altura del centro del lado."""
    x, y, w, h, _ = POS[t]
    hx, hy = hacia
    cx, cy = x + w / 2, y + h / 2
    if hx >= cx:
        return (x + w, min(max(hy, y + HH), y + h - 4)), (1, 0)
    return (x, min(max(hy, y + HH), y + h - 4)), (-1, 0)


def pata(p, d, tipo, color, lw):
    """Marca en el extremo: 'muchos' (pata de gallo) o 'uno' (barra)."""
    x, y = p
    dx, dy = d
    if tipo == 'muchos':
        for s in (-6, 6):
            ax.plot([x, x + dx * 11], [y, y + s], color=color, lw=lw, solid_capstyle='butt')
        ax.plot([x + dx * 11, x + dx * 11], [y - 5, y + 5], color=color, lw=lw)
    else:
        ax.plot([x + dx * 9, x + dx * 9], [y - 5, y + 5], color=color, lw=lw)
        ax.plot([x + dx * 13, x + dx * 13], [y - 5, y + 5], color=color, lw=lw)


def fila_y(t, col):
    x, y, w, h, _ = POS[t]
    nombres = [c for c, _, _ in COLS[t]]
    return y + HH + RH * (nombres.index(col) + 0.5)


for t, col, ref in FKS:
    maestra = ref.startswith('cat_') or ref in ('cie10', 'departamento', 'secretaria')
    uno_a_uno = col in UQ[t] or col in PK[t]
    yc = fila_y(t, col)
    xh = POS[ref][0] + POS[ref][2] / 2
    yr = POS[ref][1] + HH + RH / 2
    p1, d1 = borde(t, (POS[ref][0] + POS[ref][2] / 2, yc))
    p1 = (p1[0], yc)
    # el lado del hijo se elige mirando al padre
    p2, d2 = borde(ref, (POS[t][0] + POS[t][2] / 2, yr))
    p2 = (p2[0], yr)
    if (POS[t][0] + POS[t][2] / 2) > xh:
        p1, d1 = (POS[t][0], yc), (-1, 0)
        p2, d2 = (POS[ref][0] + POS[ref][2], yr), (1, 0)
    else:
        p1, d1 = (POS[t][0] + POS[t][2], yc), (1, 0)
        p2, d2 = (POS[ref][0], yr), (-1, 0)
    color, lw = ('#9A9A9A', 0.7) if maestra else ('#222222', 1.1)
    ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=color, lw=lw, zorder=1)
    pata(p1, d1, 'uno' if uno_a_uno else 'muchos', color, lw)
    pata(p2, d2, 'uno', color, lw)

# ------------------------------------------------------------------ tablas
for t, (x, y, w, h, color) in POS.items():
    ax.add_patch(Rectangle((x, y), w, h, fc='white', ec='black', lw=1.0, zorder=3))
    ax.add_patch(Rectangle((x + 0.5, y + 0.5), w - 1, HH - 0.5, fc=color, ec='none', zorder=4))
    ax.text(
        x + w / 2,
        y + HH / 2,
        t,
        ha='center',
        va='center',
        fontsize=9.2,
        fontweight='bold',
        zorder=5,
    )
    ax.plot([x, x + w], [y + HH, y + HH], color='black', lw=1.0, zorder=5)
    for i, (c, tp, nn) in enumerate(COLS[t]):
        yy = y + HH + RH * (i + 0.5)
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
                x + 6,
                yy,
                marca,
                fontsize=7.6,
                fontweight='bold',
                va='center',
                zorder=5,
                color='#7A1F1F' if 'FK' in marca else 'black',
            )
        ax.text(x + 46, yy, c, fontsize=8, va='center', zorder=5)
        ax.text(
            x + w - 6,
            yy,
            tp + (' NN' if nn and c not in PK[t] else ''),
            fontsize=7.2,
            va='center',
            ha='right',
            color='#555',
            zorder=5,
        )

os.makedirs(SALIDA, exist_ok=True)
fig.savefig(os.path.join(SALIDA, 'bd_completa.svg'), format='svg')
fig.savefig(os.path.join(SALIDA, 'bd_completa.png'), dpi=170)
print(f'{len(TABLAS)} tablas, {len(FKS)} llaves foráneas -> {SALIDA}')
