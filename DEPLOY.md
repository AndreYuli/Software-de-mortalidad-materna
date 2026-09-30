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

```bash
# Crear la base (DROP/CREATE no puede ir junto con otras sentencias en -c)
sudo -u postgres psql -d postgres -c "DROP DATABASE IF EXISTS sivigila_maternidad;"
sudo -u postgres psql -d postgres -c "CREATE DATABASE sivigila_maternidad ENCODING 'UTF8';"

# Cargar el esquema completo
sudo -u postgres psql -d sivigila_maternidad -f Software-de-mortalidad-materna/backend/sivigila_maternidad_postgres.sql

# Verificar
sudo -u postgres psql -d sivigila_maternidad -c "\dt"

# Usuario de aplicación (no usar el superusuario postgres desde el backend)
sudo -u postgres psql -c "CREATE USER app_mortalidad WITH PASSWORD 'mortalidad123';"
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

```bash
cd ~/Software-de-mortalidad-materna/backend
cat > .env << 'EOF'
db_engine=postgresql
db_user=app_mortalidad
db_password=mortalidad123
db_name=sivigila_maternidad
db_host=localhost
db_port=5432
jwt_secret=cambia-esto-por-un-valor-seguro
EOF
```

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
curl -sk https://ingenieria.unac.edu.co/~andrea.lopez/maternalytics/api/health
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

**Ollama no se pudo usar en este servidor**: la CPU no tiene `avx`
(`grep -c avx /proc/cpuinfo` → 0), tiene 4 núcleos y ~6 GB de RAM libres en
un servidor compartido, y Ollama no está instalado. En su lugar `ia-service`
llama a la API gratuita de NVIDIA (compatible con OpenAI,
`https://integrate.api.nvidia.com/v1`). Se activa solo si `LLM_BASE_URL`
está definido; sin esa variable sigue usando Ollama (desarrollo local).

- Límites del plan gratuito: ~40 peticiones/min y créditos limitados; pensado
  para prototipos, no producción. Los indicadores agregados salen a un tercero.
- Modelo: `meta/llama-3.2-11b-vision-instruct` (responde 200 y en español).
  Los catálogos cambian: `meta/llama-3.3-70b-instruct` y
  `meta/llama-3.1-8b-instruct` ya devolvían `410` (retirados) al desplegar.
  Si el chat empieza a dar 503, probar la clave/modelo con:
  `curl -s https://integrate.api.nvidia.com/v1/chat/completions -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" -d '{"model":"<id>","messages":[{"role":"user","content":"OK"}],"max_tokens":8}'`
  y listar ids vivos con `GET https://integrate.api.nvidia.com/v1/models`.

```bash
cd ~/Software-de-mortalidad-materna/ia-service
python3.11 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# La clave se pide sin eco y no queda en el historial ni en el repo
read -rsp "NVIDIA API key: " K; echo
umask 177
cat > .env << EOF
LLM_API_KEY=$K
LLM_BASE_URL=https://integrate.api.nvidia.com/v1
OLLAMA_MODEL=meta/llama-3.2-11b-vision-instruct
EOF
unset K; umask 022
```

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

# Conectar el backend y reiniciarlo
echo "ia_service_url=http://localhost:8011" >> ~/Software-de-mortalidad-materna/backend/.env
sudo systemctl restart mortalidad-backend
```

Verificación: `POST http://localhost:8011/chat` con
`{"pregunta":"hola","historial":[],"tipo_analisis":"mortalidad","contexto":{}}`
responde texto y `"modelo":"meta/llama-3.2-11b-vision-instruct"`.
Logs: `journalctl -u mortalidad-ia -f`.

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
- [ ] Rotar la API key de NVIDIA: se pegó en un chat durante el despliegue.
- [ ] Hacer `git pull` + reinicio del backend en el servidor (sección 7) y subir
      `sivigila_mortalidad_10_casos.xlsx` desde el navegador; confirmar que carga
      con PostgreSQL y que el dashboard muestra los 10 casos.
- [ ] Antes de versionar este archivo: cambiar `mortalidad123` y `jwt_secret` por
      placeholders (el repo es público).
