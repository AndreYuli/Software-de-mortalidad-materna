# Actualizar el servidor con una versión nueva del código

Pasos para traer lo que hay en `main` al servidor y reiniciar lo necesario. Ejemplo real: 2026-11-05, cuando se
quitó el soporte de Ollama del `ia-service` (commit `bf7b69c6`); en ese pull también llegan cambios de otros
commits en el backend y el front-end. Los `.env` están en `.gitignore`, así que `git pull` no los toca.

Las referencias a secciones («sección 4.2», «sección 6») son de [DEPLOY.md](../DEPLOY.md), que describe la
instalación inicial.

> ⚠️ **Desde el PR #5 (2026-11-05) el paso 3 es obligatorio.** El backend nuevo exige la base de datos con la
> estructura nueva y **se niega a arrancar** sobre la anterior (`EstructuraAnteriorError`). No modifica la base: se
> probó contra una base con la estructura anterior y quedó con las mismas 36 tablas. Si se reinicia el servicio sin
> hacer el paso 3, `mortalidad-backend` no levanta.

**1. Revisar antes de actualizar** (no imprime ninguna clave):

```bash
cd ~/Software-de-mortalidad-materna
git rev-parse --short HEAD                  # anotar este commit: sirve para volver atrás
git status --short                          # debe salir vacío; si hay cambios locales, no forzar: avisar al equipo
grep -c '^LLM_BASE_URL=.' ia-service/.env   # debe imprimir 1
grep -c '^LLM_API_KEY=.' ia-service/.env    # debe imprimir 1
```

Desde el 2026-11-05 `LLM_BASE_URL` es **obligatoria**: sin ella `/chat` y `/generar-narrativa` responden 503.
En el servidor ya está definida (Groq), así que solo hay que comprobar que siga ahí.

**2. Traer el código:**

```bash
git fetch origin && git log --oneline HEAD..origin/main    # ver qué llega
git pull --ff-only origin main
```

**3. Base de datos: ¿la versión nueva cambia la estructura?** Se sabe si `git diff --stat <commit anotado> HEAD --
backend/db backend/sivigila_maternidad_postgres.sql` muestra cambios. Si no los hay, pasar al paso 4. Si los hay:

- **La base tiene datos que importan** → no seguir este paso: migrar a una base nueva con
  `backend/scripts/migrar_estructura_anterior.py` ([DEPLOY.md](../DEPLOY.md) sección 2.2 y
  [MIGRACION_BD.md](MIGRACION_BD.md)), con respaldo previo. **Nunca** `DROP DATABASE` sobre una base con datos.
- **La base no tiene datos reales** (como en la actualización del 2026-11-05) → recrearla con el script nuevo:

```bash
sudo systemctl stop mortalidad-backend.service            # nada debe estar conectado a la base
sudo -u postgres pg_dump -Fc sivigila_maternidad > ~/sivigila_maternidad-$(date +%F).dump   # respaldo, aunque no importe
sudo -u postgres psql -d postgres -c "DROP DATABASE IF EXISTS sivigila_maternidad;"
sudo -u postgres psql -d postgres -c "CREATE DATABASE sivigila_maternidad ENCODING 'UTF8';"
sudo -u postgres psql -d sivigila_maternidad -f ~/Software-de-mortalidad-materna/backend/sivigila_maternidad_postgres.sql
```

  Después hay que volver a dar permisos a `app_mortalidad` sobre las tablas nuevas: es el bloque `GRANT` final de
  [DEPLOY.md](../DEPLOY.md) sección 2.1 (el usuario ya existe; no hay que crearlo ni cambiar `db_password` en
  `backend/.env`). Sin ese bloque el backend falla con «permiso denegado a la tabla cat_tipo_id».

  Al arrancar, el backend sigue ejecutando ajustes sobre la base (triggers de auditoría, vistas, catálogos). En
  pruebas locales con un usuario que no es dueño de las tablas aparecieron avisos como «No se pudieron preparar las
  vistas… debe ser dueño de la vista» y un error al crear una función de los triggers; aun así el registro, el
  login y la carga de Excel funcionaron. Eso se vio en PostgreSQL 17 con un usuario limitado y **no está verificado
  en el servidor** (PostgreSQL 16, `app_mortalidad`). Si aparecen, comprobar en el paso 7 que la carga de un Excel y
  el dashboard funcionen.

**4. Dependencias** (es seguro repetirlo aunque no hayan cambiado):

```bash
cd ~/Software-de-mortalidad-materna/ia-service && source venv/bin/activate && pip install -r requirements.txt && deactivate
cd ~/Software-de-mortalidad-materna/backend && source venv/bin/activate && pip install -r requirements.txt && deactivate
```

**5. Reiniciar los servicios.** Si solo cambió el `ia-service`, basta reiniciar `mortalidad-ia` (el backend llama
por URL). Si también cambió el backend, reiniciar los dos:

```bash
sudo systemctl restart mortalidad-ia.service mortalidad-backend.service
systemctl is-active mortalidad-ia.service mortalidad-backend.service    # active / active
```

**6. Front-end, solo si cambió algo en `frontend/`** (`git diff --stat <commit anotado> HEAD -- frontend`).
Debe existir `frontend/maternanalytics/.env.production` ([DEPLOY.md](../DEPLOY.md) sección 4.2; no se versiona):

```bash
cd ~/Software-de-mortalidad-materna/frontend/maternanalytics
pnpm install
pnpm run build
rm -rf ~/public_html/maternalytics/*
cp -r dist/* ~/public_html/maternalytics/
```

El `.htaccess` de `~/public_html/maternalytics/` no se borra (el `*` no incluye archivos ocultos); si falta,
recrearlo como en [DEPLOY.md](../DEPLOY.md) sección 4.3.

**7. Verificar:**

```bash
curl -s http://127.0.0.1:8011/health                       # {"status":"ok"}
curl -sk -o /dev/null -w "%{http_code}
" https://ingenieria.unac.edu.co/~andrea.lopez/maternalytics/   # 200
journalctl -u mortalidad-ia -n 30 --no-pager               # sin errores al arrancar
journalctl -u mortalidad-backend -n 30 --no-pager          # sin EstructuraAnteriorError ni permisos denegados
```

Probar `POST :8011/chat` como en la verificación de [DEPLOY.md](../DEPLOY.md) sección 6 (debe responder 200 con
`"modelo":"openai/gpt-oss-20b"`) y, desde el navegador, que una narrativa y el chat respondan 200 y no 503. Si el
paso 3 recreó la base, subir un Excel de prueba y comprobar que carga y que el dashboard lo muestra.

**8. Si algo falla, volver al commit anotado** (no destruye nada; luego se reinician los servicios del paso 5):

```bash
git checkout <commit anotado en el paso 1>
# ...reiniciar servicios, y cuando se corrija el problema:
git switch main && git pull --ff-only origin main
```

Volver al commit anterior **no deshace el paso 3**: si la base ya se recreó con la estructura nueva, el código
anterior no funcionará sobre ella. Para volver atrás con la base, restaurar el respaldo del paso 3 con
`pg_restore`.

**Ollama en el servidor.** El `ia-service` ya no lo usa. Si quedó instalado por la prueba del 2026-11-04, se puede
detener: primero `systemctl is-active ollama` y, si responde `active`, `sudo systemctl disable --now ollama`.
