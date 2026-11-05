# Despliegue en el servidor (ingenieria.unac.edu.co)

Servidor compartido de la universidad (`ubuntusrv`, usuario `andrea.lopez`, con
sudo). Apache sirve varios proyectos de distintos estudiantes bajo el mismo
dominio, cada uno en su propia subruta `/~usuario/proyecto`.

- **URL pública del frontend**: `https://ingenieria.unac.edu.co/~andrea.lopez/maternalytics/`
- **API**: mismo path + `/api` → `https://ingenieria.unac.edu.co/~andrea.lopez/maternalytics/api/...`
- **Backend interno**: `127.0.0.1:8010` (FastAPI/uvicorn, vía systemd)
- **BD**: PostgreSQL local, base `sivigila_maternidad`

## 1. Clonar el repo

```bash
git clone https://github.com/AndreYuli/Software-de-mortalidad-materna.git
```

Si el clone falla con `fatal: could not open '.../tmp_pack_...' for reading` o
`invalid index-pack output`, normalmente es una conexión lenta/inestable
(no falta de disco, ya se verificó con `df -h ~`). Reintentar, si sigue
fallando usar `git clone --depth 1 <url>`.

## 2. Base de datos (PostgreSQL)

PostgreSQL ya estaba instalado y corriendo en el servidor
(`sudo systemctl status postgresql`).

> ⚠️ **Solo para la instalación inicial.** `DROP DATABASE` borra la base y
> **todos sus datos**. No ejecutarlo en un servidor que ya tiene datos cargados;
> para eso, hacer antes una copia con
> `sudo -u postgres pg_dump -Fc sivigila_maternidad > ~/sivigila_maternidad-$(date +%F).dump`.

```bash
# Crear la base (DROP/CREATE no puede ir junto con otras sentencias en -c)
sudo -u postgres psql -d postgres -c "DROP DATABASE IF EXISTS sivigila_maternidad;"
sudo -u postgres psql -d postgres -c "CREATE DATABASE sivigila_maternidad ENCODING 'UTF8';"

# Cargar el esquema completo
sudo -u postgres psql -d sivigila_maternidad -f Software-de-mortalidad-materna/backend/sivigila_maternidad_postgres.sql

# Verificar
sudo -u postgres psql -d sivigila_maternidad -c "\dt"

# Usuario de aplicación (no usar el superusuario postgres desde el backend).
# Generar la contraseña con: openssl rand -hex 24
# Usar solo caracteres hexadecimales: backend/core/config.py la inserta sin
# escapar en la URL de conexión, y caracteres como @ : / % # rompen el arranque.
# La misma contraseña va en backend/.env (db_password), ver "Credenciales del despliegue".
sudo -u postgres psql -c "CREATE USER app_mortalidad WITH PASSWORD 'REEMPLAZAR_CON_LA_CONTRASEÑA_DE_LA_BD';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE sivigila_maternidad TO app_mortalidad;"

# Las tablas las creó postgres, así que también hay que dar permiso sobre ellas.
# Sin esto el backend falla con "InsufficientPrivilege: permiso denegado a la tabla cat_tipo_id".
sudo -u postgres psql -d sivigila_maternidad << 'EOF'
GRANT USAGE ON SCHEMA public TO app_mortalidad;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO app_mortalidad;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO app_mortalidad;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO app_mortalidad;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO app_mortalidad;
EOF
```

El script `backend/sivigila_maternidad_postgres.sql` trae en su cabecera las
instrucciones equivalentes para ejecutarlo desde DBeaver.

## 3. Backend (FastAPI)

### 3.1 Variables de entorno

`backend/core/config.py` lee `backend/.env` (no se versiona, `.env.*` está en
`.gitignore`):

Reemplazar los dos valores `REEMPLAZAR_...` antes de arrancar el servicio
(qué es cada uno y de dónde sale: sección "Credenciales del despliegue"):

```bash
cd ~/Software-de-mortalidad-materna/backend
umask 177   # el .env queda con permisos 600 (solo la dueña puede leerlo)
cat > .env << 'EOF'
db_engine=postgresql
db_user=app_mortalidad
db_password=REEMPLAZAR_CON_LA_CONTRASEÑA_DE_LA_BD
db_name=sivigila_maternidad
db_host=localhost
db_port=5432
jwt_secret=REEMPLAZAR_CON_SECRETO_JWT_ALEATORIO
ia_service_url=http://localhost:8011
EOF
umask 022
ls -l .env   # debe ser -rw------- (600)
```

- `jwt_secret`: generarlo con `openssl rand -hex 32`. Si se cambia, todas las
  sesiones abiertas dejan de ser válidas y los usuarios deben volver a iniciar
  sesión.
- `ia_service_url`: URL del ia-service en este servidor (puerto 8011, ver
  sección 6). Sin esta línea el backend usa `http://localhost:8001`, que aquí
  es otro proceso.
- Si el `.env` ya existía, hacer antes una copia:
  `cp -pn .env .env.bak-$(date +%Y%m%d)`.

### 3.2 Entorno virtual e instalación

```bash
sudo apt install python3-venv python3-pip -y
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

**Problema encontrado y resuelto**: la CPU de este servidor (una VM) no
soporta instrucciones x86-64-v2 (falta `sse4_2`, `popcnt`, `ssse3`, etc. —
confirmado con `lscpu | grep -i flags`). Los wheels precompilados de
`numpy==2.4.4` / `pandas==3.0.2` / `scipy==1.15.1` exigen ese nivel y fallan
en tiempo de arranque con:

```
RuntimeError: NumPy was built with baseline optimizations: (X86_V2) but your
machine doesn't support: (X86_V2).
```

Solución: bajar esas 4 librerías a versiones compiladas con baseline SSE2.
Esto ya quedó fijado en `backend/requirements.txt` (commit `71d24d3`,
etiquetado con `# ponytail:` explicando el porqué):

```
numpy==1.26.4
pandas==2.2.3
scipy==1.13.1
scikit-learn==1.5.2
```

También se necesitó Python **3.11+** (numpy 2.x lo exigía; el venv se
recreó con `python3.11 -m venv venv` tras instalar `python3.11-venv` vía
`deadsnakes` PPA).

### 3.3 Servicio systemd

Puerto elegido: **8010** (no 8000 — ese puerto ya está reservado en el vhost
de Apache para el proxy `/blogs` de otro proyecto; usarlo habría causado un
choque de puertos en este servidor compartido). Antes de fijar un puerto
nuevo, revisar qué está en uso: `sudo ss -tlnp` y buscar en
`/etc/apache2/sites-enabled/000-default.conf`.

```bash
sudo tee /etc/systemd/system/mortalidad-backend.service > /dev/null << 'EOF'
[Unit]
Description=Mortalidad Materna Backend (FastAPI)
After=network.target postgresql.service

[Service]
User=andrea.lopez
WorkingDirectory=/home/andrea.lopez/Software-de-mortalidad-materna/backend
ExecStart=/home/andrea.lopez/Software-de-mortalidad-materna/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8010
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now mortalidad-backend
sudo systemctl status mortalidad-backend
curl http://localhost:8010/health   # {"status":"ok"}
```

Nota: con `--host 0.0.0.0` el backend también acepta conexiones directas por
la red, sin pasar por Apache. Apache llega por `127.0.0.1:8010` (sección 5),
así que se puede usar `--host 127.0.0.1` para limitarlo al propio servidor.
Pendiente de decidir; si se cambia: `sudo systemctl daemon-reload` y
`sudo systemctl restart mortalidad-backend`.

Logs: `journalctl -u mortalidad-backend -f`.

## 4. Frontend (React + Vite, servido por Apache vía mod_userdir)

`ingenieria.unac.edu.co` tiene `mod_userdir` activo
(`UserDir public_html`, `AllowOverride FileInfo AuthConfig Limit Indexes` en
`/etc/apache2/mods-enabled/userdir.conf`), así que todo lo que se copie a
`~/public_html/maternalytics/` queda accesible en
`https://ingenieria.unac.edu.co/~andrea.lopez/maternalytics/` sin tocar la
config de Apache para la parte estática.

El repo usa **pnpm** (hay `pnpm-lock.yaml`), no npm.

### 4.1 Cambios en el código para servir bajo una subruta

Como la app no vive en la raíz del dominio sino en
`/~andrea.lopez/maternalytics/`, hicieron falta 2 ajustes (commit `71d24d3`):

- `frontend/maternanalytics/vite.config.ts`: `base` condicional —
  `/~andrea.lopez/maternalytics/` solo en build de producción (`vite dev`
  sigue sirviendo en `/`).
- `frontend/maternanalytics/src/App.tsx`: `<BrowserRouter
  basename={import.meta.env.BASE_URL}>` — Vite inyecta `BASE_URL`
  automáticamente a partir del `base` de arriba, así que el router queda
  sincronizado sin duplicar la ruta a mano.

### 4.2 Instalar pnpm y compilar

```bash
sudo npm install -g pnpm   # corepack estaba con la caché rota, se instaló así
pnpm -v

cd ~/Software-de-mortalidad-materna/frontend/maternanalytics
cat > .env.production << 'EOF'
VITE_API_URL=/~andrea.lopez/maternalytics/api
EOF
# .env.production NO se versiona (.gitignore: .env.*) — crear siempre en el servidor
pnpm install
pnpm run build
```

### 4.3 Desplegar a public_html

```bash
rm -rf ~/public_html/maternalytics/*
cp -r dist/* ~/public_html/maternalytics/

# Fallback de rutas para el SPA (React Router) al recargar /dashboard, /historial, etc.
cat > ~/public_html/maternalytics/.htaccess << 'EOF'
RewriteEngine On
RewriteBase /~andrea.lopez/maternalytics/
RewriteRule ^index\.html$ - [L]
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule . index.html [L]
EOF

curl -sk -o /dev/null -w "%{http_code}\n" https://ingenieria.unac.edu.co/~andrea.lopez/maternalytics/   # 200
```

## 5. Proxy de la API en Apache

El vhost real y activo es `/etc/apache2/sites-enabled/000-default.conf`
(bloque `<VirtualHost *:443>` — es el "default server"; existe también
`smartpath-ssl.conf` con el mismo `ServerName` pero Apache nunca lo toma
porque el primero gana). Ahí están todos los `ProxyPass` de los demás
proyectos del servidor.

`ProxyPass` **no se puede definir en `.htaccess`**, solo en el vhost
principal — a diferencia de las reglas de rewrite del paso 4.3, que sí
corren en `.htaccess` gracias al `AllowOverride` de `mod_userdir`.

Se agregó, siguiendo el mismo patrón que usan otros proyectos
(`/~ana.garces/univita/api`, etc.), justo después del bloque de `/blogs`:

```apache
ProxyPass /~andrea.lopez/maternalytics/api http://127.0.0.1:8010/api
ProxyPassReverse /~andrea.lopez/maternalytics/api http://127.0.0.1:8010/api
```

Comando usado para insertarlo:

```bash
sudo sed -i '/ProxyPassReverse \/blogs http:\/\/localhost:8000\/blogs/a\
        ProxyPass /~andrea.lopez/maternalytics/api http://127.0.0.1:8010/api\
        ProxyPassReverse /~andrea.lopez/maternalytics/api http://127.0.0.1:8010/api' /etc/apache2/sites-enabled/000-default.conf

sudo apache2ctl configtest      # debe decir "Syntax OK"
sudo systemctl reload apache2

# /health no está bajo /api, así que .../api/health da 404 aunque el proxy
# funcione. Comprobar el proxy con una ruta real de la API:
curl -sk -o /dev/null -w "%{http_code}\n" -X POST https://ingenieria.unac.edu.co/~andrea.lopez/maternalytics/api/auth/login/   # 422 (falta el cuerpo) = proxy OK
curl -sk -o /dev/null -w "%{http_code}\n" https://ingenieria.unac.edu.co/~andrea.lopez/maternalytics/api/analisis/            # 401 (sin token) = proxy OK
```

Nota: el backend ya trae `/api` como prefijo fijo en sus routers
(`backend/api/routers/auth.py`, `analisis.py`, `sivigila.py` →
`/api/auth`, `/api`, `/api/sivigila`), por eso el `ProxyPass` mapea
`.../maternalytics/api` → `127.0.0.1:8010/api` (mismo sufijo a ambos lados).

## 6. ia-service (narrativas y chat)

Microservicio FastAPI (`ia-service/`) que el backend llama vía
`ia_service_url` (`/generar-narrativa` y `/chat`). Si no está disponible, el
resto de la app funciona y las narrativas/chat se ocultan (el backend
responde 503).

### Proveedor LLM actual: Groq (desde 2026-11-04)

`ia-service` tiene dos modos (`ia-service/core/config.py`,
`ia-service/ollama_client.py`):

- **`LLM_BASE_URL` definido** → llama a `{LLM_BASE_URL}/chat/completions`
  (API compatible con OpenAI) con `Authorization: Bearer {LLM_API_KEY}` y
  `model={OLLAMA_MODEL}`. Lo usan tanto `/chat` como `/generar-narrativa`.
- **`LLM_BASE_URL` vacío** → Ollama local (`OLLAMA_HOST`), pensado para
  desarrollo.

En producción se usa **Groq** (plan gratuito) con el modelo
**`openai/gpt-oss-20b`** (DEC-005). La variable del modelo se llama
`OLLAMA_MODEL` por razones históricas, pero también es el id del modelo para
el proveedor externo.

**Por qué no Ollama local en este servidor** (medido el 2026-11-04): la VM
expone una CPU genérica (`Common KVM processor`) **sin** `sse4_2`, `avx`,
`avx2` ni `fma`, así que llama.cpp usa su ruta sin vectorizar. Con Ollama
instalado, `qwen2.5:1.5b` generó a **0,6 tokens/s** (126 s para 50 tokens),
por encima del timeout de 120 s del chat; `minicpm-v` (8B) no terminó en
300 s. Volver a evaluarlo solo si el hipervisor expone AVX2 (tipo de CPU
`host`).

**Por qué no NVIDIA** (proveedor anterior): desde el 2026-11-04 la clave
devuelve `404 "Function ... not found for account"` en todos los modelos
probados, y varios (`meta/llama-3.1-8b-instruct`, `meta/llama-3.3-70b-instruct`)
devuelven `410` por fin de vida.

Límites de Groq **observados el 2026-11-04** en las cabeceras
`x-ratelimit-*` (no son garantías; Groq puede cambiarlos y los vigentes están
en <https://console.groq.com/settings/limits>):

| Límite | Valor observado |
|---|---|
| Peticiones por día (`x-ratelimit-limit-requests`) | 1.000 |
| Tokens por minuto (`x-ratelimit-limit-tokens`) | 8.000 |

Si se superan, Groq responde `429` y el chat muestra error (el backend devuelve
503). Cada pregunta envía el contexto de indicadores agregados, así que en
análisis grandes el límite de tokens por minuto es el que se alcanza primero.
Ese mismo día, `llama-3.3-70b-versatile` y `llama-3.1-8b-instant` no estaban
disponibles para la cuenta (`model_not_found`); los modelos accesibles se
listan con `GET https://api.groq.com/openai/v1/models`.

Datos enviados: solo los indicadores agregados que arma el backend
(`backend/api/routers/analisis.py`, claves de `claves_contexto`) y las
preguntas del usuario; nunca filas de pacientes. Según la política de Groq
(<https://console.groq.com/docs/your-data>), por defecto no retiene los datos
de inferencia, salvo registros temporales (hasta 30 días) para fiabilidad o
abuso, que se desactivan con *Zero Data Retention* en *Settings → Data
Controls*. Comprobar en la consola si ZDR está activo; este documento no lo
asume.

Configuración (la clave se escribe solo en el servidor, sin eco, y nunca se
versiona; `ia-service/.env` está en `.gitignore`, plantilla en
`ia-service/.env.example`):

```bash
cd ~/Software-de-mortalidad-materna/ia-service
python3.11 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Copia de seguridad del .env anterior (no sobrescribir una existente)
[ -f .env ] && cp -pn .env .env.bak-$(date +%Y%m%d)

# La clave se pide sin eco y no queda en el historial ni en el repo
read -rsp "Groq API key: " K; echo
umask 177
cat > .env << EOF
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_API_KEY=$K
OLLAMA_MODEL=openai/gpt-oss-20b
EOF
unset K; umask 022
ls -l .env   # debe ser -rw------- (600)
```

Al cambiar el `.env` basta con reiniciar **solo** el ia-service; el backend no
necesita reinicio porque llama por URL:

```bash
sudo systemctl restart mortalidad-ia.service
systemctl is-active mortalidad-ia.service
```

Probar la clave y el modelo directamente (sin pasar por el servicio):

```bash
read -rsp "Groq API key: " K; echo
curl -s https://api.groq.com/openai/v1/chat/completions \
  -H @<(printf 'Authorization: Bearer %s\n' "$K") -H "Content-Type: application/json" \
  -d '{"model":"openai/gpt-oss-20b","max_tokens":50,"messages":[{"role":"user","content":"OK"}]}'
unset K
```

Volver a la configuración anterior: restaurar la copia
(`cp -p .env.bak-<fecha> .env`) y reiniciar `mortalidad-ia.service`. En el
cambio a Groq del 2026-11-04 la copia del `.env` de NVIDIA quedó como
`ia-service/.env.bak-nvidia-20261104` (NVIDIA ya no responde, así que solo
sirve como referencia).

Servicio systemd, puerto **8011** (solo `127.0.0.1`; el 8001 por defecto está
ocupado por otro proceso):

```bash
sudo tee /etc/systemd/system/mortalidad-ia.service > /dev/null << 'EOF'
[Unit]
Description=Mortalidad Materna IA Service (FastAPI)
After=network.target

[Service]
User=andrea.lopez
WorkingDirectory=/home/andrea.lopez/Software-de-mortalidad-materna/ia-service
ExecStart=/home/andrea.lopez/Software-de-mortalidad-materna/ia-service/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8011
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now mortalidad-ia

# Conectar el backend y reiniciarlo (si ia_service_url ya está en backend/.env
# desde la sección 3.1, no repetir el echo)
grep -q '^ia_service_url=' ~/Software-de-mortalidad-materna/backend/.env || \
  echo "ia_service_url=http://localhost:8011" >> ~/Software-de-mortalidad-materna/backend/.env
sudo systemctl restart mortalidad-backend
```

Verificación (con datos ficticios):

```bash
curl -s http://127.0.0.1:8011/health          # {"status":"ok"}
curl -s http://127.0.0.1:8011/chat -H 'Content-Type: application/json' \
  -d '{"pregunta":"Cual es la principal causa?","historial":[],"tipo_analisis":"mortalidad","contexto":{"causas_cie10":[{"codigo":"O72.1","nombre":"Hemorragia postparto","casos":12}]}}'
```

Debe responder 200 con texto y `"modelo":"openai/gpt-oss-20b"`. El 2026-11-04
respondió en 0,86 s. Logs: `journalctl -u mortalidad-ia -f` (un `503` en
`POST /chat` indica que falló el proveedor; el `detail` de la respuesta trae el
error de Groq). Timeouts: `/chat` tiene 120 s fijos en el código;
`/generar-narrativa` usa `OLLAMA_TIMEOUT_S` (por defecto 120 s).

## 7. Carga de Excel: errores encontrados al desplegar y cómo se resolvieron

Al subir el primer archivo de mortalidad en el servidor aparecieron, en cadena,
estos errores. Van en el orden en que salieron; los 3 últimos son del mismo tipo
(un valor del Excel no coincide con el catálogo de la BD).

| Error (mensaje en pantalla) | Causa | Solución |
|---|---|---|
| `InsufficientPrivilege: permiso denegado a la tabla cat_tipo_id` | Las tablas las creó `postgres`; a `app_mortalidad` solo se le dio permiso sobre la base, no sobre las tablas | `GRANT ... ON ALL TABLES/SEQUENCES` (ver paso 2) |
| `Fila N: el campo 10.1 Causa básica CIE-10 es obligatorio` | El Excel trae la causa vacía en alguna fila; un solo vacío aborta toda la carga | Corregir el Excel. Ahora el error lista **todas** las filas vacías de una vez |
| `NotNullViolation: id_regulacion_fec` (`antecedente_materno`) | El Excel escribe `No usó por acceso` y `DIU`; el catálogo dice `No usó métodos por acceso` y `Dispositivo intrauterino`. No coincidían, quedaba `null` y la columna es `NOT NULL` | `_sivigila_catalog.py`: la comparación ignora "métodos" y expande la sigla `DIU` |
| (mismo tipo) `id_momento_muerte` | El Excel escribe `Puerperio > 24h`; el catálogo `Puerperio > 24 horas` | Alias `24h` → `24 horas` en `_sivigila_catalog.py` |

Cambios de código asociados (commits `63bafd45` y `eb3a8676`, más los del punto
siguiente):

- Un error de datos del Excel ya no sale como "Error al persistir en base de datos"
  (500): se devuelve como **422** con el mensaje tal cual.
- `sivigila_service._CATALOGOS_OBLIGATORIOS_MORTALIDAD` valida en la pasada 1, con
  número de fila, las columnas que son `NOT NULL` en la BD: `6.1 Convivencia`,
  `6.3 Escolaridad`, `6.4 Regulación Fecundidad` y `9.1 Momento de la muerte`.
  Si se agrega otra columna `NOT NULL` con catálogo, va en esa lista.
- `analisis_service._mensaje_error_bd` traduce el error de permisos (`42501`) y el de
  dato obligatorio (`23502`, con tabla y columna), y recorta los errores de BD
  largos a 400 caracteres.
- Tests en `backend/tests/test_mensajes_error_carga.py`.

Los valores categóricos del Excel deben ser los del catálogo de la BD
(`backend/sivigila_maternidad_postgres.sql`, tablas `cat_*`); la comparación ignora
mayúsculas, tildes, artículos ("de", "la"…) y "métodos", pero no sinónimos. Por
ejemplo `Ninguno`, `Preservativo` o `Inyectable` (los usa
`scripts/generar_excels_prueba.py`) **no** existen en `cat_regulacion_fecundidad`.

**Después de cada cambio de código en el backend**, en el servidor:

```bash
cd ~/Software-de-mortalidad-materna && git pull
sudo systemctl restart mortalidad-backend
journalctl -u mortalidad-backend -n 50 --no-pager   # si algo falla
```

### 7.1 Excel de prueba con 10 casos (mortalidad, ficha 550)

`backend/media/uploads/2026/08/sivigila_mortalidad_10_casos.xlsx` (83 columnas,
10 filas). `backend/media/` está en `.gitignore`: **el archivo no viaja con
`git pull`**; para probar en el servidor se sube desde el navegador con el archivo
de tu PC.

- Personas y documentos ficticios. Cada caso es clínicamente coherente:
  `gestaciones = partos vaginales + cesáreas + abortos + 1` y
  `vivos + muertos = partos vaginales + cesáreas`; la edad se calcula a la fecha de
  defunción; las fechas y la hora del parto son consistentes con el momento de la
  muerte (los casos en "Gestación" no llevan datos de parto).
- Cubre los 4 momentos de la muerte, 4 de los 7 sitios de defunción (hospital,
  puesto de salud, domicilio y durante el traslado), zona urbana y rural, población
  migrante, indígena y afro, una adolescente (TI, 17 años) y una migrante con PPT.
- El script que lo generó no está en el repo (era temporal); si hace falta
  regenerarlo o ampliarlo, pedirlo y se agrega a `backend/scripts/`.
- Causas CIE-10: `O14.2` (HELLP), `O72.1` (hemorragia posparto), `O85` (sepsis
  puerperal), `O00.1` (embarazo tubárico), `O88.1` (embolia de líquido amniótico),
  `O88.2` (embolia por coágulo), `O99.4` (cardiopatía), `O45.9` (desprendimiento de
  placenta), `O99.5` (enfermedad respiratoria) y `O15.1` (eclampsia en trabajo de
  parto). Ninguna empieza por `P` (la BD lo rechaza).
- Además de las 24 columnas requeridas trae las opcionales que la carga sí lee:
  fechas de defunción y parto, hora del parto, zona, etnia, población vulnerable,
  afiliación, los 24 antecedentes `7.1.x`, las 18 complicaciones `7.2.x`,
  personal y nivel de atención del CPN y del parto, remisiones y fuente de la causa.
- Verificado con una carga completa (POST `/api/analisis/`) contra los catálogos
  reales del script SQL, sobre SQLite: 10 filas → 10 casos creados. El mismo test
  con `base_datos_sivigila_mortalidad.xlsx` (50 filas, el que falló) → 50 casos.
  Falta confirmarlo contra PostgreSQL en el servidor.

## Credenciales del despliegue

Ningún valor real de estas credenciales se escribe en el repositorio, en chats
ni en issues. Se comparten por un gestor de contraseñas o un canal privado, y en
el servidor viven solo en los `.env` (permisos 600, fuera de git). En este
documento aparecen como `REEMPLAZAR_...`.

| Credencial | Qué es | Dónde se obtiene | Quién la proporciona | Dónde se configura |
|---|---|---|---|---|
| `REEMPLAZAR_CON_LA_CONTRASEÑA_DE_LA_BD` | Contraseña del rol `app_mortalidad` de PostgreSQL, con el que se conecta el backend | Se genera: `openssl rand -hex 24` (solo hexadecimal) | Quien administra el despliegue de Maternalytics | En PostgreSQL (`CREATE USER` / `ALTER ROLE`, sección 2) **y** en `backend/.env` (`db_password`); deben coincidir |
| `REEMPLAZAR_CON_SECRETO_JWT_ALEATORIO` | Clave con la que el backend firma y verifica los tokens de sesión | Se genera: `openssl rand -hex 32` | Se genera en el servidor; nadie más necesita conocerla | `backend/.env` (`jwt_secret`) |
| API key de Groq (`LLM_API_KEY`) | Acceso del ia-service a Groq | <https://console.groq.com> → API Keys | Quien tiene la cuenta de Groq del equipo | `ia-service/.env` (sección 6) |
| Cuenta SSH/sudo del servidor | Acceso a `ubuntusrv` para desplegar | La asigna la UNAC | El administrador del servidor | Personal; no se configura en el proyecto |
| Superusuario `postgres` | Administración de PostgreSQL (compartido con otros proyectos) | Servidor | El administrador del servidor | Se usa con `sudo -u postgres`; no va en ningún `.env` |

**Rotar la contraseña de `app_mortalidad` y el `jwt_secret`** (un solo reinicio
del backend, unos segundos sin servicio; todas las sesiones se cierran y los
usuarios deben volver a iniciar sesión):

```bash
cd ~/Software-de-mortalidad-materna/backend
cp -pn .env .env.bak-$(date +%Y%m%d) && chmod 600 .env.bak-*   # copia para volver atrás

# 1. Editar .env con los valores nuevos (db_password y jwt_secret), p. ej. con nano.
#    El backend sigue funcionando con los anteriores hasta que se reinicie.
#    Generarlos con: openssl rand -hex 24  /  openssl rand -hex 32

# 2. Cambiar la contraseña en PostgreSQL enviando solo su hash md5
#    (el texto en claro no queda en logs ni en el historial):
read -rsp "Nueva contraseña de app_mortalidad (la misma del .env): " P; echo
H="md5$(printf '%s' "${P}app_mortalidad" | md5sum | cut -c1-32)"
printf "ALTER ROLE app_mortalidad PASSWORD '%s';\n" "$H" | sudo -u postgres psql -X -q
unset P H

# 3. Reiniciar el backend enseguida (las conexiones nuevas fallan hasta reiniciar)
sudo systemctl restart mortalidad-backend
systemctl is-active mortalidad-backend
```

Verificación: `curl http://localhost:8010/health` → 200; login desde el
navegador → 200; un token anterior debe dar 401. Logs:
`journalctl -u mortalidad-backend -f`.

Volver atrás: `cp -p .env.bak-<fecha> .env`, restaurar la contraseña anterior
con `ALTER ROLE` y reiniciar `mortalidad-backend`.

## Puertos en uso en el servidor (referencia, `sudo ss -tlnp`)

Antes de asignar un puerto nuevo a cualquier servicio en este servidor
compartido, revisar que no choque con: 3000, 3001, 3005, 3010, 3020, 3030,
3031, 4000, 5000, 5432-5434, 8000 (`/blogs`), 8001, 8081, 8088, 8090, 8501,
8502, 9002, 10000, 18080, 27027, 28028 (los dos últimos vistos en el vhost,
no en `ss` al momento de revisar). Nuestros: 8010 (backend), 8011 (ia-service).

## Pendiente / próximos pasos

- [x] Confirmar el proxy de Apache tras el reload. Nota: `/health` está fuera
      del prefijo `/api`, así que `.../maternalytics/api/health` da 404 aunque
      el proxy funcione; se verificó con `.../api/auth/login/` (422) y
      `.../api/analisis/` (401).
- [x] Probar registro y login end-to-end desde el navegador
      (`POST .../api/auth/register/` → 201, `POST .../api/auth/login/` → 200,
      navegación a `/historial` con token).
- [ ] Revisar `cors_origins` en `backend/core/config.py` si en algún momento
      el frontend deja de llamar por la misma ruta relativa `/api` (con el
      `ProxyPass` actual la llamada es same-origin, así que CORS no debería
      hacer falta).
- [x] Desplegar `ia-service` como servicio systemd en el puerto 8011 (ver
      sección 6). `POST :8011/chat` responde.
- [ ] Probar narrativa y chat desde el navegador (que `.../api/analisis/{id}/narrativa/...`
      y `.../chat/` respondan 200 y no 503).
- [x] Cambiar el proveedor LLM de NVIDIA a Groq (`openai/gpt-oss-20b`) y
      verificar `POST :8011/chat` → 200 (2026-11-04, sección 6).
- [ ] Revocar en la consola de NVIDIA la API key anterior (se pegó en un chat
      durante el despliegue y ya no se usa).
- [ ] Revocar la primera API key de Groq que se pegó en un chat el 2026-11-04
      (producción usa otra clave nueva).
- [ ] Comprobar en <https://console.groq.com/settings/data-controls> si Zero
      Data Retention está activo y activarlo si el equipo lo aprueba.
- [ ] Hacer `git pull` + reinicio del backend en el servidor (sección 7) y subir
      `sivigila_mortalidad_10_casos.xlsx` desde el navegador; confirmar que carga
      con PostgreSQL y que el dashboard muestra los 10 casos.
- [x] Sustituir en este archivo las credenciales reales por placeholders
      `REEMPLAZAR_...` (el repo es público).
- [ ] Rotar la contraseña de `app_mortalidad` y el `jwt_secret` de producción:
      los valores anteriores estuvieron publicados en el historial de este
      archivo y deben darse por comprometidos. Procedimiento en
      "Credenciales del despliegue".
