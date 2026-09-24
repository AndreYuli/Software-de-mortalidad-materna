# Mejora: Identificación Única de Pacientes (Evolución de Documento)

## Objetivo
Lograr que el sistema reconozca a una madre como la **misma paciente** basándose únicamente en su **número de identificación**. Si la madre fue registrada previamente con Tarjeta de Identidad (TI) y en un reporte futuro aparece con Cédula de Ciudadanía (CC) manteniendo el mismo número, el sistema no la duplicará, sino que actualizará su tipo de documento y mantendrá su historial unificado.

---

## 1. Modificación en la Base de Datos (PostgreSQL)

Actualmente, la tabla `paciente` exige que la combinación de `(id_tipo_id, numero_id)` sea única. Debemos cambiar esta regla para que **solo el `numero_id` sea único**.

**Archivo afectado:** `BACKEND/sivigila_maternidad_postgres.sql`

**Cambio:**
En la sección donde se crea la tabla `paciente` (aprox. línea 196), debes cambiar la restricción (`CONSTRAINT`) actual por una nueva que solo evalúe el número.

```sql
CREATE TABLE paciente (
    id_paciente        INT           GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombres_apellidos  VARCHAR(200)  NOT NULL,
    id_tipo_id         SMALLINT      NOT NULL,
    numero_id          VARCHAR(30)   NOT NULL,
    fecha_nacimiento   DATE          NULL,
    creado_en          TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    
    -- BORRAR ESTA LÍNEA:
    -- CONSTRAINT uq_paciente UNIQUE (id_tipo_id, numero_id),
    
    -- AGREGAR ESTA NUEVA LÍNEA:
    CONSTRAINT uq_paciente_numero_id UNIQUE (numero_id),
    
    CONSTRAINT fk_paciente_tipo_id
        FOREIGN KEY (id_tipo_id) REFERENCES cat_tipo_id(id)
);
```

> **Nota:** Si ya tienes la base de datos creada, puedes aplicar el cambio directamente en DBeaver ejecutando:
> ```sql
> ALTER TABLE paciente DROP CONSTRAINT uq_paciente;
> ALTER TABLE paciente ADD CONSTRAINT uq_paciente_numero_id UNIQUE (numero_id);
> ```

---

## 2. Modificación en la Carga del Caché (Python)

Debemos cambiar la forma en la que el backend precarga las pacientes en memoria. Ahora el diccionario (caché) usará solo el `numero_id` como llave, en lugar de la tupla `(tipo, numero)`.

**Archivo afectado:** `BACKEND/services/_sivigila_helpers.py`

**Cambio:**
Busca la función `_precargar_caches_sivigila` (aprox. línea 137). 

```python
    # ANTES:
    paciente_cache: dict[tuple[Any, str], Paciente] = {}
    if numeros_id:
        for i in range(0, len(numeros_id), _CHUNK_SIZE):
            chunk: list[str] = list(numeros_id)[i : i + _CHUNK_SIZE]
            for p in db.query(Paciente).filter(Paciente.numero_id.in_(chunk)).all():
                paciente_cache[(p.id_tipo_id, p.numero_id)] = p

    # DESPUÉS (El cambio):
    paciente_cache: dict[str, Paciente] = {}
    if numeros_id:
        for i in range(0, len(numeros_id), _CHUNK_SIZE):
            chunk: list[str] = list(numeros_id)[i : i + _CHUNK_SIZE]
            for p in db.query(Paciente).filter(Paciente.numero_id.in_(chunk)).all():
                # Ahora la llave es solo el número de ID
                paciente_cache[p.numero_id] = p
```

*(No olvides actualizar también la definición de `SivigilaCaches` al principio del archivo, cambiando `paciente_cache: dict[tuple[Any, str], Paciente]` a `paciente_cache: dict[str, Paciente]`)*.

---

## 3. Modificación en la Actualización de Pacientes (Python)

Finalmente, debemos indicarle al código que, si encuentra a la paciente pero nota que el tipo de documento cambió (ej. de 5 a 1), lo actualice en la base de datos.

**Archivo afectado:** `BACKEND/services/sivigila_service.py`

**Cambio:**
Busca la función `_fase2_upsert_pacientes` (aprox. línea 173).

```python
def _fase2_upsert_pacientes(
    non_dup_indices: list[int],
    pass1_data: dict[int, _DatosPasada1],
    caches: SivigilaCaches,
    db: Session,
    resumen: dict[str, Any],
) -> None:
    for index in non_dup_indices:
        ident = pass1_data[index].ident
        
        # ANTES: cache_key = (ident["tipo_obj"].id, ident["numero_id"])
        # AHORA:
        cache_key = ident["numero_id"]
        
        if cache_key not in caches.paciente_cache:
            p = Paciente(
                id_tipo_id=ident["tipo_obj"].id,
                numero_id=ident["numero_id"],
                nombres_apellidos=ident["nombres"],
                fecha_nacimiento=ident.get("fecha_nacimiento"),
                creado_en=datetime.now(timezone.utc),
            )
            db.add(p)
            caches.paciente_cache[cache_key] = p
            resumen["pacientes_nuevos"] += 1
        else:
            p = caches.paciente_cache[cache_key]
            
            # --- NUEVA LÓGICA DE ACTUALIZACIÓN ---
            
            # 1. Si el tipo de documento cambió (ej. TI a CC), se actualiza
            if p.id_tipo_id != ident["tipo_obj"].id:
                p.id_tipo_id = ident["tipo_obj"].id
                
            # 2. Si el nombre cambió, se actualiza
            if p.nombres_apellidos != ident["nombres"]:
                p.nombres_apellidos = ident["nombres"]
                
            # 3. Si mandaron fecha de nacimiento nueva, se actualiza
            if ident.get("fecha_nacimiento") and p.fecha_nacimiento != ident["fecha_nacimiento"]:
                p.fecha_nacimiento = ident["fecha_nacimiento"]
                
            resumen["pacientes_existentes"] += 1
```

## Resultado Esperado
Con estos tres cambios, cuando la Secretaría de Salud cargue un archivo con la cédula `102030` de "María López" pero bajo el tipo `CC` (y antes era `TI`), el sistema dirá: *"Encontré a María por su número. Noto que ahora es CC en lugar de TI. Actualizo su tipo de documento en la base de datos y le asocio este nuevo caso clínico"*.
