-- Datos de los catálogos (tablas maestras). Fuente única; el generador del esquema los copia al script.

INSERT INTO cat_tipo_id VALUES
    (1,'CC' ,'Cédula de Ciudadanía'),
    (2,'CE' ,'Cédula de Extranjería'),
    (3,'PA' ,'Pasaporte'),
    (4,'PPT','Permiso por Protección Temporal'),
    (5,'TI' ,'Tarjeta de Identidad'),
    (6,'RC' ,'Registro Civil'),
    (7,'MS' ,'Menor sin ID'),
    (8,'AS' ,'Adulto sin ID');

INSERT INTO cat_sitio_defuncion VALUES
    (1,'IPS (hospital/clínica)'),
    (2,'IPS (centro/puesto de salud)'),
    (3,'Lugar de trabajo'),
    (4,'Vía pública'),
    (5,'Durante el traslado'),
    (6,'Domicilio'),
    (7,'Otro');

INSERT INTO cat_convivencia VALUES
    (1,'Cónyuge'),(2,'Familia'),(3,'Sola'),(4,'Otro');

INSERT INTO cat_escolaridad VALUES
    (1,'Ninguna'),(2,'Primaria'),(3,'Secundaria'),
    (4,'Superior'),(5,'Sin información');

INSERT INTO cat_regulacion_fecundidad VALUES
    (1,'No usó métodos por desconocimiento'),
    (2,'No usó métodos por acceso'),
    (3,'No usó métodos porque no deseaba'),
    (4,'Natural'),(5,'Dispositivo intrauterino'),(6,'Hormonal'),
    (7,'Barrera'),(8,'Quirúrgico'),(9,'Otro');

INSERT INTO cat_nivel_atencion VALUES (1,'I'),(2,'II'),(3,'III'),(4,'IV');

INSERT INTO cat_personal_salud VALUES
    (1,'Médico general'),(2,'Médico obstetra'),
    (3,'Enfermera'),(4,'Aux. enfermería'),(5,'Promotor'),
    (6,'Partera'),(7,'Otro');

INSERT INTO cat_momento_muerte VALUES
    (1,'Gestación'),
    (2,'Parto'),
    (3,'Puerperio < 24 horas'),
    (4,'Puerperio > 24 horas');

INSERT INTO cat_tipo_parto VALUES
    (1,'Vaginal'),(2,'Cesárea'),(3,'Instrumentado'),(4,'Ignorado');

INSERT INTO cat_fuente_causa_muerte VALUES
    (1,'Historia clínica'),(2,'Autopsia verbal'),(3,'Necropsia');

INSERT INTO cat_remisiones VALUES (1,'Sí'),(2,'No'),(3,'No aplica');

INSERT INTO cat_terminacion_gestacion VALUES
    (1,'Aborto'),(2,'Parto'),(3,'Parto instrumentado'),
    (4,'Cesárea'),(5,'Continúa embarazada');

INSERT INTO cat_grupo_causa VALUES
    (1,'Trastornos hipertensivos'),
    (2,'Hemorragia obstétrica'),
    (3,'Sepsis de origen obstétrico'),
    (4,'Aborto'),
    (5,'Complicaciones del parto y puerperio'),
    (6,'Enfermedades concurrentes'),
    (7,'Causas no obstétricas'),
    (8,'Otras');

INSERT INTO cat_zona_residencia VALUES
    (1,'Urbana'),(2,'Rural');

INSERT INTO cat_poblacion_vulnerable VALUES
    (1,'Ninguna'),(2,'Migrante'),(3,'Indígena'),(4,'Afro'),
    (5,'Discapacidad'),(6,'Víctima de conflicto'),(7,'Desplazada');

INSERT INTO cat_etnia VALUES
    (1,'Ninguna'),(2,'Indígena'),(3,'Afrocolombiana'),
    (4,'Rrom'),(5,'Raizal'),(6,'Otra');

INSERT INTO cat_tipo_afiliacion VALUES
    (1,'Contributivo'),(2,'Subsidiado'),(3,'No afiliada');
