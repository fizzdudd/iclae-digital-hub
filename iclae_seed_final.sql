-- ============================================================
--  ICLAE DIGITAL HUB — GENERADOR DE DATOS DE PRUEBA BBDD
--  Motor: PostgreSQL 15+
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

SET session_replication_role = replica;

TRUNCATE TABLE
  recordatorio_masivo, notificacion, alumno_badge, badge,
  puntaje_competencia, evaluacion_hito, competencia_hito, hito_evaluacion,
  config_evaluacion_periodo, postulacion, bitacora_evidencia, bitacora,
  proyecto_periodo, proyecto, tutor_empresa, tutor_udd, alumno, usuario,
  empresa, carrera, sede, universidad, periodo_academico
CASCADE;

ALTER SEQUENCE empresa_id_seq RESTART WITH 1;
ALTER SEQUENCE carrera_id_seq RESTART WITH 1;
ALTER SEQUENCE sede_id_seq RESTART WITH 1;
ALTER SEQUENCE universidad_id_seq RESTART WITH 1;
ALTER SEQUENCE periodo_academico_id_seq RESTART WITH 1;
ALTER SEQUENCE proyecto_id_seq RESTART WITH 1;
ALTER SEQUENCE proyecto_periodo_id_seq RESTART WITH 1;
ALTER SEQUENCE bitacora_id_seq RESTART WITH 1;
ALTER SEQUENCE bitacora_evidencia_id_seq RESTART WITH 1;
ALTER SEQUENCE postulacion_id_seq RESTART WITH 1;
ALTER SEQUENCE hito_evaluacion_id_seq RESTART WITH 1;
ALTER SEQUENCE competencia_hito_id_seq RESTART WITH 1;
ALTER SEQUENCE evaluacion_hito_id_seq RESTART WITH 1;
ALTER SEQUENCE puntaje_competencia_id_seq RESTART WITH 1;
ALTER SEQUENCE badge_id_seq RESTART WITH 1;
ALTER SEQUENCE alumno_badge_id_seq RESTART WITH 1;
ALTER SEQUENCE notificacion_id_seq RESTART WITH 1;
ALTER SEQUENCE recordatorio_masivo_id_seq RESTART WITH 1;
ALTER SEQUENCE config_evaluacion_periodo_id_seq RESTART WITH 1;

SET session_replication_role = DEFAULT;

-- ============================================================
-- SECCIÓN 1: UNIVERSIDAD Y SEDES
-- ============================================================
INSERT INTO universidad (nombre, codigo) VALUES ('Universidad del Desarrollo', 'UDD');

INSERT INTO sede (universidad_id, nombre, ciudad, region) VALUES
  (1, 'Santiago',   'Santiago',    'Región Metropolitana'),
  (1, 'Concepción', 'Concepción',  'Región del Biobío');

-- ============================================================
-- SECCIÓN 2: CARRERAS — Facultad de Ingeniería UDD
-- ============================================================
INSERT INTO carrera (universidad_id, nombre, codigo, facultad) VALUES
  (1, 'Ingeniería Civil Informática',           'ICINF',  'Facultad de Ingeniería'),
  (1, 'Ingeniería Civil Industrial',            'ICIND',  'Facultad de Ingeniería'),
  (1, 'Ingeniería en Construcción',             'ICONS',  'Facultad de Ingeniería'),
  (1, 'Bioingeniería',                          'IBIO',   'Facultad de Ingeniería'),
  (1, 'Ingeniería Civil en Obras Civiles',      'ICOC',   'Facultad de Ingeniería'),
  (1, 'Ingeniería en Gestión Empresarial',      'IGE',    'Facultad de Ingeniería'),
  (1, 'Ingeniería Civil Mecánica',              'ICMEC',  'Facultad de Ingeniería'),
  (1, 'Ingeniería en Medio Ambiente',           'IMA',    'Facultad de Ingeniería');

-- ============================================================
-- SECCIÓN 3: PERÍODOS ACADÉMICOS (2021-1 al 2026-1)
-- ============================================================
INSERT INTO periodo_academico (nombre, fecha_inicio, fecha_fin, total_semanas, is_active) VALUES
  ('2021-1', '2021-03-01', '2021-07-16', 16, FALSE),
  ('2021-2', '2021-08-02', '2021-12-17', 16, FALSE),
  ('2022-1', '2022-03-07', '2022-07-22', 16, FALSE),
  ('2022-2', '2022-08-01', '2022-12-16', 16, FALSE),
  ('2023-1', '2023-03-06', '2023-07-21', 16, FALSE),
  ('2023-2', '2023-08-07', '2023-12-22', 16, FALSE),
  ('2024-1', '2024-03-04', '2024-07-19', 16, FALSE),
  ('2024-2', '2024-08-05', '2024-12-20', 16, FALSE),
  ('2025-1', '2025-03-03', '2025-07-18', 16, FALSE),
  ('2025-2', '2025-08-04', '2025-12-19', 16, FALSE),
  ('2026-1', '2026-03-02', '2026-07-17', 16, TRUE);

-- ============================================================
-- SECCIÓN 4: EMPRESAS REALES (42 empresas)
-- ============================================================
INSERT INTO empresa (nombre, rubro, tamano, presencia, empleados_aprox, ubicacion, campus_id, enps_score) VALUES
('Banco de Chile', 'Banca', 'grande', 'chile', '12.000+', 'Santiago Centro, Santiago', 1, 9.2),
('BCI', 'Banca', 'grande', 'chile', '8.500+', 'El Golf, Santiago', 1, 8.8),
('Santander Chile', 'Banca', 'grande', 'multinacional', '9.000+', 'Bandera, Santiago', 1, 8.5),
('Itaú Chile', 'Banca', 'grande', 'multinacional', '3.500+', 'Apoquindo, Santiago', 1, 8.3),
('Banco Estado', 'Banca', 'grande', 'chile', '15.000+', 'Monjitas, Santiago', 1, 7.9),
('BICE Vida', 'Banca', 'mediana', 'chile', '1.200+', 'Providencia, Santiago', 1, 8.0),
('Fintual', 'Fintech', 'pequeña', 'chile', '120+', 'Vitacura, Santiago', 1, 9.3),
('Global66', 'Fintech', 'mediana', 'multinacional', '400+', 'Providencia, Santiago', 1, 8.9),
('Khipu', 'Fintech', 'pequeña', 'chile', '80+', 'Ñuñoa, Santiago', 1, 8.7),
('Cumplo', 'Fintech', 'pequeña', 'chile', '150+', 'Las Condes, Santiago', 1, 8.4),
('MACH (BCI)', 'Fintech', 'mediana', 'chile', '300+', 'El Golf, Santiago', 1, 8.6),
('Google Chile', 'Tecnología', 'grande', 'multinacional', '200+', 'Las Condes, Santiago', 1, 9.8),
('Microsoft Chile', 'Tecnología', 'grande', 'multinacional', '500+', 'Vitacura, Santiago', 1, 9.5),
('IBM Chile', 'Tecnología', 'grande', 'multinacional', '600+', 'Providencia, Santiago', 1, 8.9),
('Accenture Chile', 'Tecnología', 'grande', 'multinacional', '1.500+', 'Las Condes, Santiago', 1, 8.7),
('Globant Chile', 'Tecnología', 'grande', 'multinacional', '700+', 'Providencia, Santiago', 1, 8.8),
('Mercado Libre Chile', 'E-commerce', 'grande', 'multinacional', '2.000+', 'Las Condes, Santiago', 1, 9.1),
('Buk', 'HR Tech', 'mediana', 'multinacional', '600+', 'Las Condes, Santiago', 1, 9.1),
('Rankmi', 'HR Tech', 'pequeña', 'chile', '130+', 'Providencia, Santiago', 1, 8.5),
('Talana', 'HR Tech', 'pequeña', 'chile', '70+', 'Ñuñoa, Santiago', 1, 8.2),
('Betterfly', 'InsurTech', 'mediana', 'multinacional', '800+', 'Providencia, Santiago', 1, 9.5),
('BNP Paribas Cardif', 'InsurTech', 'grande', 'multinacional', '1.100+', 'Las Condes, Santiago', 1, 8.3),
('Sura Chile', 'InsurTech', 'grande', 'multinacional', '2.500+', 'Las Condes, Santiago', 1, 8.1),
('Falabella', 'Retail', 'grande', 'multinacional', '95.000+', 'Las Condes, Santiago', 1, 8.6),
('Cencosud (Paris)', 'Retail', 'grande', 'chile', '100.000+', 'Las Condes, Santiago', 1, 7.8),
('Ripley Chile', 'Retail', 'grande', 'chile', '20.000+', 'Santiago Centro, Santiago', 1, 7.9),
('IKEA Chile', 'Retail', 'grande', 'multinacional', '500+', 'Pudahuel, Santiago', 1, 8.7),
('Enel Chile', 'Energía', 'grande', 'multinacional', '2.800+', 'Providencia, Santiago', 1, 8.4),
('Colbún', 'Energía', 'grande', 'chile', '1.500+', 'Las Condes, Santiago', 1, 8.0),
('AES Andes', 'Energía', 'grande', 'multinacional', '1.200+', 'Providencia, Santiago', 1, 7.9),
('Empresas Copec', 'Energía', 'grande', 'chile', '5.000+', 'Las Condes, Santiago', 1, 8.2),
('Codelco', 'Minería', 'grande', 'chile', '27.000+', 'Huérfanos, Santiago', 1, 7.8),
('Anglo American Chile', 'Minería', 'grande', 'multinacional', '6.000+', 'Las Condes, Santiago', 1, 7.9),
('Antofagasta Minerals', 'Minería', 'grande', 'chile', '8.000+', 'Apoquindo, Santiago', 1, 8.0),
('Entel', 'Telecomunicaciones', 'grande', 'chile', '6.000+', 'Ahumada, Santiago', 1, 8.1),
('Movistar Chile', 'Telecomunicaciones', 'grande', 'multinacional', '4.500+', 'Providencia, Santiago', 1, 7.8),
('Claro Chile', 'Telecomunicaciones', 'grande', 'multinacional', '3.000+', 'Apoquindo, Santiago', 1, 7.7),
('Clínica Las Condes', 'Salud', 'grande', 'chile', '5.000+', 'Lo Fontecilla, Santiago', 1, 8.5),
('Unilabs Chile', 'Salud', 'mediana', 'multinacional', '800+', 'Providencia, Santiago', 1, 8.0),
('LATAM Airlines', 'Transporte', 'grande', 'chile', '33.000+', 'Pudahuel, Santiago', 1, 8.0),
('Chilexpress', 'Logística', 'mediana', 'chile', '3.000+', 'Pudahuel, Santiago', 1, 7.8),
('Arauco (CMPC)', 'Manufactura', 'grande', 'chile', '12.000+', 'Coronel, Concepción', 2, 7.9),
('Aguas Araucanía', 'Servicios', 'mediana', 'chile', '600+', 'Concepción', 2, 7.8),
('Lipigas', 'Energía', 'mediana', 'chile', '2.000+', 'Concepción', 2, 7.7);

-- ============================================================
-- SECCIÓN 5: CONFIG EVALUACIÓN + HITOS POR PERÍODO
-- ============================================================
DO $$
DECLARE
  pid INT;
  h1  INT; h2 INT; h3 INT;
BEGIN
  FOR pid IN SELECT id FROM periodo_academico LOOP
    INSERT INTO config_evaluacion_periodo
      (periodo_id, peso_bitacoras_pct, metodo_calculo_bitacoras, umbral_bitacoras_pct)
    VALUES (pid, 10, 'aprobadas', 80);

    INSERT INTO hito_evaluacion (periodo_id, nombre, semana, peso_pct, evaluador, estado, orden)
    VALUES (pid, 'Diagnóstico inicial', 4, 20, 'udd', 'disponible', 1) RETURNING id INTO h1;
    INSERT INTO competencia_hito (hito_id, nombre, descripcion, peso_pct, orden) VALUES
      (h1, 'Adaptación al equipo', 'Integración con compañeros y cultura organizacional', 30, 1),
      (h1, 'Comprensión del proyecto', 'Entiende alcance, objetivos y tecnologías del proyecto', 40, 2),
      (h1, 'Comunicación inicial', 'Claridad en la comunicación con tutores y equipo', 30, 3);

    INSERT INTO hito_evaluacion (periodo_id, nombre, semana, peso_pct, evaluador, estado, orden)
    VALUES (pid, 'Evaluación intermedia', 8, 30, 'ambos', 'pendiente', 2) RETURNING id INTO h2;
    INSERT INTO competencia_hito (hito_id, nombre, descripcion, peso_pct, orden) VALUES
      (h2, 'Trabajo en equipo', 'Colaboración efectiva y aportes al equipo', 25, 1),
      (h2, 'Habilidades técnicas', 'Dominio de herramientas y tecnologías del proyecto', 35, 2),
      (h2, 'Resolución de problemas', 'Capacidad para identificar y superar obstáculos', 25, 3),
      (h2, 'Comunicación', 'Presentación de avances y resultados', 15, 4);

    INSERT INTO hito_evaluacion (periodo_id, nombre, semana, peso_pct, evaluador, estado, orden)
    VALUES (pid, 'Evaluación final', 16, 50, 'ambos', 'pendiente', 3) RETURNING id INTO h3;
    INSERT INTO competencia_hito (hito_id, nombre, descripcion, peso_pct, orden) VALUES
      (h3, 'Trabajo en equipo', 'Impacto sostenido durante toda la práctica', 20, 1),
      (h3, 'Habilidades técnicas', 'Nivel técnico alcanzado al finalizar', 30, 2),
      (h3, 'Liderazgo', 'Iniciativa y capacidad de liderazgo demostrada', 20, 3),
      (h3, 'Comunicación', 'Calidad de la presentación final del proyecto', 15, 4),
      (h3, 'Impacto en la empresa', 'Valor concreto generado para la organización', 15, 5);

    IF pid < (SELECT id FROM periodo_academico WHERE is_active LIMIT 1) THEN
      UPDATE hito_evaluacion SET estado = 'evaluado' WHERE periodo_id = pid;
    END IF;
  END LOOP;
END;
$$;

-- ============================================================
-- SECCIÓN 6: BADGES
-- ============================================================
INSERT INTO badge (nombre, descripcion, icono, criterio) VALUES
  ('Alumno Destacado', 'Rendimiento sobresaliente en el período', '🏆', 'Nota final >= 6.5'),
  ('Innovador', 'Propuso soluciones creativas al proyecto', '💡', 'Reconocimiento tutor empresa'),
  ('Colaborador', 'Excelente trabajo en equipo durante la práctica', '🤝', 'Comp. trabajo en equipo >= 6.5'),
  ('Puntualidad', 'Entregó todas las bitácoras sin atrasos', '⭐', '16/16 bitácoras en fecha'),
  ('Alto Desempeño', 'Nota final superior a 6.5', '🚀', 'Nota final calculada >= 6.5'),
  ('Liderazgo', 'Demostró iniciativa excepcional en el proyecto', '🎯', 'Comp. liderazgo >= 6.5'),
  ('Perfil Completo', 'Completó LinkedIn, CV y video de presentación', '✅', 'Los 3 links del perfil configurados'),
  ('Primera Práctica', 'Completó exitosamente su primera práctica ICLAE', '🎓', 'Primer proyecto_periodo cerrado'),
  ('Constancia', 'Aprobó 14 o más semanas de bitácoras', '🔥', 'Semanas aprobadas >= 14'),
  ('Referente Técnico', 'Nota en habilidades técnicas mayor a 6.8', '⚙️', 'Comp. habilidades técnicas >= 6.8'),
  ('Embajador ICLAE', 'Recomendado por la empresa para recontratación', '🌟', 'Flag contratado = true'),
  ('Impacto Real', 'El proyecto generó resultados medibles en la empresa', '📈', 'Comp. impacto en empresa >= 6.5');

-- ============================================================
-- SECCIÓN 7: TUTORES UDD (22 tutores - Correos @udd.cl)
-- ============================================================
DO $$
DECLARE
  uid UUID;
  tutores_udd TEXT[][] := ARRAY[
    ARRAY['Paulina','Gómez','Torres'], ARRAY['Roberto','Vera','Sánchez'],
    ARRAY['Carolina','Muñoz','Pérez'], ARRAY['Jorge','Soto','Rojas'],
    ARRAY['Luis','Araya','Fuentes'], ARRAY['Marcela','Castillo','Herrera'],
    ARRAY['Andrés','Morales','Díaz'], ARRAY['Verónica','Espinoza','Vega'],
    ARRAY['Rodrigo','Reyes','Contreras'], ARRAY['Patricia','Núñez','Ortiz'],
    ARRAY['Felipe','Vargas','Ramírez'], ARRAY['Claudia','Jiménez','Flores'],
    ARRAY['Sebastián','Medina','Gutiérrez'], ARRAY['Andrea','Riquelme','Pinto'],
    ARRAY['Cristián','Tapia','Cáceres'], ARRAY['Daniela','Salinas','Mendoza'],
    ARRAY['Eduardo','Mena','Sepúlveda'], ARRAY['Natalia','Bravo','Álvarez'],
    ARRAY['Ignacio','Cuadra','Miranda'], ARRAY['Francisca','Lobos','Cortés'],
    ARRAY['Tomás','Poblete','Ibáñez'], ARRAY['Valentina','Olivares','Molina']
  ];
  t TEXT[];
  idx INT := 1;
  sedes INT[] := ARRAY[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,2,2,2,2,2];
BEGIN
  -- Admin
  INSERT INTO usuario (id, email, password_hash, rol, nombre, apellido) VALUES (uuid_generate_v4(), 'admin.iclae@udd.cl', crypt('Admin123!', gen_salt('bf')), 'admin_iclae', 'Admin', 'ICLAE');

  FOREACH t SLICE 1 IN ARRAY tutores_udd LOOP
    uid := uuid_generate_v4();
    INSERT INTO usuario (id, email, password_hash, rol, nombre, apellido)
    VALUES (uid, lower(t[1]) || '.' || lower(t[2]) || '@udd.cl', crypt('Iclae2024!', gen_salt('bf')), 'tutor_udd', t[1], t[2] || ' ' || t[3]);
    INSERT INTO tutor_udd (id, sede_id, departamento, max_alumnos)
    VALUES (uid, sedes[idx], CASE WHEN idx % 4 = 0 THEN 'Ingeniería Civil Industrial' WHEN idx % 4 = 1 THEN 'Ingeniería Informática' WHEN idx % 4 = 2 THEN 'Ingeniería en Construcción' ELSE 'Bioingeniería y Ciencias' END, 18);
    idx := idx + 1;
  END LOOP;
END;
$$;

-- ============================================================
-- SECCIÓN 8: TUTORES EMPRESA (Correos corporativos realistas)
-- ============================================================
DO $$
DECLARE
  uid UUID;
  e_rec RECORD;
  nombres_h TEXT[] := ARRAY['Carlos','Diego','Matías','Alejandro','Felipe','Patricio','Rodrigo','Andrés','Pablo','Cristóbal','Nicolás','Sebastián','Francisco','Ignacio','Eduardo','Maximiliano','Tomás','Rafael','Gonzalo','Héctor','Ricardo','Gabriel','Hugo','Julio','César','Omar','Víctor','Alberto','Jorge','Ramón'];
  nombres_m TEXT[] := ARRAY['María','Ana','Claudia','Verónica','Lorena','Marcela','Daniela','Carolina','Pamela','Andrea','Javiera','Francisca','Valentina','Natalia','Constanza','Catalina','Pilar','Sofía','Isabel','Gabriela','Roxana','Carmen','Silvia','Susana','Ximena','Patricia','Beatriz','Gloria','Rosa','Elena'];
  apellidos TEXT[] := ARRAY['González','Rodríguez','Muñoz','Rojas','Díaz','Pérez','Soto','Contreras','Silva','Martínez','Sepúlveda','Morales','Torres','Flores','Rivera','Herrera','Medina','Aguilar','Vásquez','Castillo','Reyes','Fuentes','Núñez','Ramírez','Carrasco','Vargas','Ibáñez','Bravo','Espinoza','Cortés','Valenzuela','Pizarro','Ramos','Cáceres','Salinas','Castro','Navarrete','Figueroa','Araya','Lara'];
  cargos TEXT[] := ARRAY['Gerente de Proyectos','Jefe de Tecnología','Líder de Desarrollo','Coordinador de Innovación','Gerente de Personas','Head of Engineering','Tech Lead','Director de Operaciones','Subdirector de TI','Coordinador RRHH','Analista Senior','Product Manager','Jefe de Área Digital','CTO','Gerente de Área'];
  areas TEXT[] := ARRAY['Tecnología','Innovación','Recursos Humanos','Operaciones','Ingeniería','Digital','Proyectos','Desarrollo','Sistemas','Transformación Digital'];
  nom TEXT; ape1 TEXT; ape2 TEXT; cargo TEXT; area TEXT; cnt INT; domain TEXT;
BEGIN
  FOR e_rec IN SELECT id, nombre FROM empresa LOOP
    -- Generar dominio realista a partir del nombre de la empresa
    domain := regexp_replace(replace(lower(e_rec.nombre), ' chile', ''), '[^a-z0-9]', '', 'g');
    IF domain IN ('google', 'microsoft', 'ibm', 'accenture', 'globant', 'ikea', 'latamairlines', 'mercadolibre') THEN
      domain := domain || '.com';
    ELSE
      domain := domain || '.cl';
    END IF;

    FOR cnt IN 1..2 LOOP
      uid := uuid_generate_v4();
      IF cnt = 1 THEN nom := nombres_h[1 + ((e_rec.id * cnt + cnt) % array_length(nombres_h,1))]; ELSE nom := nombres_m[1 + ((e_rec.id * cnt + cnt + 5) % array_length(nombres_m,1))]; END IF;
      ape1 := apellidos[1 + ((e_rec.id + cnt * 3) % array_length(apellidos,1))];
      ape2 := apellidos[1 + ((e_rec.id + cnt * 7 + 13) % array_length(apellidos,1))];
      cargo := cargos[1 + ((e_rec.id + cnt) % array_length(cargos,1))];
      area  := areas[1 + ((e_rec.id + cnt * 2) % array_length(areas,1))];
      
      INSERT INTO usuario (id, email, password_hash, rol, nombre, apellido)
      VALUES (uid, lower(nom) || '.' || lower(ape1) || cnt::text || '@' || domain, crypt('Iclae2024!', gen_salt('bf')), 'tutor_empresa', nom, ape1 || ' ' || ape2);
      INSERT INTO tutor_empresa (id, empresa_id, cargo, area) VALUES (uid, e_rec.id, cargo, area);
    END LOOP;
  END LOOP;
END;
$$;

-- ============================================================
-- SECCIÓN 9: ALUMNOS (1200 en 11 períodos, correos @udd.cl)
-- ============================================================
DO $$
DECLARE
  uid UUID; pid INT; nombre TEXT; apellido1 TEXT; apellido2 TEXT;
  carrera_id INT; sede_id INT; gen INT; idx INT; total_alum INT;
  nombres_h TEXT[] := ARRAY['Matías','Diego','Sebastián','Felipe','Nicolás','Andrés','Ignacio','Pablo','Rodrigo','Alejandro','Cristóbal','Francisco','Tomás','Maximiliano','Eduardo','Gabriel','Gonzalo','Héctor','Julio','Rafael','Alberto','Víctor','Omar','César','Patricio','Cristián','Leonardo','Mauricio','Arturo','Iván','Ernesto','Jaime','Roberto','Manuel','Marcelo','Claudio','Javier','Sergio','Miguel','Daniel','Alonso','Camilo','Benjamín','Bastián','Emilio','Valentín','Lucas','Agustín','Martín','Álvaro','Hugo','Boris','Óscar','Enrique','Esteban','Darío','Raúl','Renato','Carlos','Pedro','Luis','José','Antonio','Ramón','Simón','Joaquín'];
  nombres_m TEXT[] := ARRAY['Sofía','Valentina','Javiera','Francisca','Daniela','Catalina','Carolina','Camila','Constanza','Natalia','Lorena','Andrea','Pamela','Claudia','Marcela','María','Ana','Isabel','Gabriela','Pilar','Verónica','Ximena','Patricia','Roxana','Beatriz','Gloria','Silvia','Susana','Carmen','Elena','Fernanda','Alejandra','Mónica','Cecilia','Margarita','Rebeca','Teresa','Laura','Sandra','Priscila','Valeria','Macarena','Stefanía','Tamara','Yasna','Karla','Nicole','Cindy','Paola','Denisse','Bárbara','Romina','Karina','Fabiola','Maite','Isidora','Emilia','Antonia','Luciana','Renata','Florencia','Agustina','Victoria'];
  apellidos TEXT[] := ARRAY['González','Rodríguez','Muñoz','Rojas','Díaz','Pérez','Soto','Contreras','Silva','Martínez','Sepúlveda','Morales','Torres','Flores','Rivera','Herrera','Medina','Aguilar','Vásquez','Castillo','Reyes','Fuentes','Núñez','Ramírez','Carrasco','Vargas','Ibáñez','Bravo','Espinoza','Cortés','Valenzuela','Pizarro','Ramos','Cáceres','Salinas','Castro','Navarrete','Figueroa','Araya','Lara','Vega','Guzmán','Tapia','Mena','Vera','Quezada','Palma','Ortega','Ojeda','Miranda','Lagos','Ríos','Jara','Molina','Henríquez','Opazo','Aravena','Meza','Acuña','Sanhueza','Bustos','Poblete','Urrutia','Saavedra','Leiva','Peña','Villalobos','Cornejo','Escobar','Becerra','Ruiz','López','Reinoso','Cid','Neira','Videla','Farías','Cabrera','Pacheco','Vilches','Troncoso','Garrido','Caro','Berríos','Méndez','Arias','Cuadra','Paredes','Baeza','Gallardo','Galindo','Navarro','Pinto','Alvarado','Barahona','Álvarez','Iturra'];
  -- Suma exacta de 1200 alumnos repartidos en 11 semestres
  alumnos_por_periodo INT[] := ARRAY[80, 90, 100, 100, 110, 110, 120, 120, 120, 120, 130]; 
  periodos_ids INT[]; carrera_ids INT[];
BEGIN
  SELECT ARRAY_AGG(id ORDER BY id) INTO periodos_ids FROM periodo_academico;
  SELECT ARRAY_AGG(id ORDER BY id) INTO carrera_ids FROM carrera;

  FOR pid IN 1..array_length(periodos_ids,1) LOOP
    total_alum := alumnos_por_periodo[pid];
    FOR idx IN 1..total_alum LOOP
      uid := uuid_generate_v4();
      IF (random() < 0.55) THEN nombre := nombres_h[1 + floor(random() * array_length(nombres_h,1))::int]; ELSE nombre := nombres_m[1 + floor(random() * array_length(nombres_m,1))::int]; END IF;
      apellido1 := apellidos[1 + floor(random() * array_length(apellidos,1))::int];
      apellido2 := apellidos[1 + floor(random() * array_length(apellidos,1))::int];
      sede_id := CASE WHEN random() < 0.70 THEN 1 ELSE 2 END;

      DECLARE r FLOAT := random(); BEGIN
        carrera_id := CASE WHEN r < 0.30 THEN carrera_ids[1] WHEN r < 0.52 THEN carrera_ids[2] WHEN r < 0.65 THEN carrera_ids[3] WHEN r < 0.74 THEN carrera_ids[6] WHEN r < 0.82 THEN carrera_ids[5] WHEN r < 0.89 THEN carrera_ids[4] WHEN r < 0.94 THEN carrera_ids[7] ELSE carrera_ids[8] END;
      END;
      gen := 2017 + floor(random() * 6)::int;

      INSERT INTO usuario (id, email, password_hash, rol, nombre, apellido, is_active)
      VALUES (uid, lower(nombre) || '.' || lower(apellido1) || floor(random()*900+100)::text || '@udd.cl', crypt('Alumno2026!', gen_salt('bf')), 'alumno', nombre, apellido1 || ' ' || apellido2, TRUE);

      INSERT INTO alumno (id, carrera_id, sede_id, generacion, url_linkedin, url_cv, url_youtube)
      VALUES (
        uid, carrera_id, sede_id, gen,
        CASE WHEN random() < 0.72 THEN 'linkedin.com/in/' || lower(nombre) || lower(apellido1) || floor(random()*999)::text ELSE NULL END,
        CASE WHEN random() < 0.65 THEN 'drive.google.com/file/d/cv_' || lower(apellido1) || floor(random()*9999)::text ELSE NULL END,
        CASE WHEN random() < 0.42 THEN 'youtube.com/watch?v=' || left(md5(uid::text), 11) ELSE NULL END
      );
    END LOOP;
  END LOOP;
END;
$$;

-- ============================================================
-- SECCIÓN 10: PROYECTOS
-- ============================================================
DO $$
DECLARE
  eid INT; e_rec RECORD; titles TEXT[]; t TEXT; n INT;
BEGIN
  FOR e_rec IN SELECT e.id, e.rubro FROM empresa e LOOP
    titles := CASE e_rec.rubro
      WHEN 'Banca' THEN ARRAY['Desarrollo de módulo de banca digital','Automatización de procesos de crédito','Plataforma de onboarding digital']
      WHEN 'Fintech' THEN ARRAY['Motor de inversión algorítmico','Transferencias internacionales','Scoring crediticio con ML']
      WHEN 'Tecnología' THEN ARRAY['Solución cloud-native','Pipeline de CI/CD','Sistema de monitoreo y observabilidad']
      WHEN 'Retail' THEN ARRAY['Optimización de cadena de suministro','Comportamiento del cliente','E-commerce omnicanal']
      ELSE ARRAY['Sistema de gestión interna','Automatización de reportería','Dashboard analítico']
    END;
    FOR n IN 1..LEAST(4, 1 + floor(random()*3)::int) LOOP
      t := titles[1 + ((n - 1) % array_length(titles, 1))];
      INSERT INTO proyecto (empresa_id, titulo, descripcion, carrera_id, modalidad, vacantes, is_active)
      VALUES (
        e_rec.id, t, 'Proyecto de práctica en ' || t, 1 + floor(random() * 8)::int,
        (ARRAY['presencial','hibrido','remoto'])[1 + floor(random()*3)::int]::modalidad_proyecto,
        1 + floor(random()*4)::int, TRUE
      );
    END LOOP;
  END LOOP;
END;
$$;

-- ============================================================
-- SECCIÓN 11: PROYECTO_PERIODO (Distribución en 11 semestres)
-- ============================================================
DO $$
DECLARE
  pp_id INT; a_id UUID; p_id INT; per_id INT; tudd_id UUID; temp_id UUID;
  sem_actual INT; tutores_udd UUID[]; tutores_emp UUID[]; alumno_rec RECORD;
  cnt INT; proyecto_ids INT[]; proyecto_id INT; per_rec RECORD;
  tudd_idx INT := 0; temd_idx INT := 0; pid_idx INT := 1;
  alumnos_por_periodo INT[] := ARRAY[80, 90, 100, 100, 110, 110, 120, 120, 120, 120, 130];
BEGIN
  SELECT ARRAY_AGG(id) INTO tutores_udd FROM tutor_udd;
  SELECT ARRAY_AGG(id) INTO tutores_emp FROM tutor_empresa;
  SELECT ARRAY_AGG(id) INTO proyecto_ids FROM proyecto;

  FOR per_rec IN SELECT pa.id, pa.is_active, pa.total_semanas, pa.fecha_inicio, pa.fecha_fin FROM periodo_academico pa ORDER BY pa.id LOOP
    IF per_rec.is_active THEN sem_actual := 8; ELSE sem_actual := per_rec.total_semanas; END IF;
    cnt := 0;
    
    FOR alumno_rec IN SELECT a.id FROM alumno a WHERE NOT EXISTS (SELECT 1 FROM proyecto_periodo pp WHERE pp.alumno_id = a.id) ORDER BY random() LIMIT alumnos_por_periodo[pid_idx] LOOP
      proyecto_id := proyecto_ids[1 + (cnt % array_length(proyecto_ids,1))];
      tudd_idx := (tudd_idx % array_length(tutores_udd,1)) + 1; tudd_id := tutores_udd[tudd_idx];
      temd_idx := (temd_idx % array_length(tutores_emp,1)) + 1; temp_id := tutores_emp[temd_idx];
      
      INSERT INTO proyecto_periodo (proyecto_id, periodo_id, alumno_id, tutor_udd_id, tutor_empresa_id, sede_id, estado, semana_actual, fecha_inicio, fecha_fin, nota_final)
      VALUES (
        proyecto_id, per_rec.id, alumno_rec.id, tudd_id, temp_id, (SELECT sede_id FROM alumno WHERE id = alumno_rec.id),
        CASE WHEN per_rec.is_active THEN 'en_curso'::estado_proyecto ELSE 'cerrado'::estado_proyecto END,
        sem_actual, per_rec.fecha_inicio, per_rec.fecha_fin, CASE WHEN NOT per_rec.is_active THEN ROUND((3.5 + random() * 3.4)::numeric, 1) ELSE NULL END
      );
      cnt := cnt + 1;
    END LOOP;
    pid_idx := pid_idx + 1;
  END LOOP;
END;
$$;

-- ============================================================
-- SECCIÓN 12: BITÁCORAS
-- ============================================================
DO $$
DECLARE
  pp_rec    RECORD;
  sem       INT;
  max_sem   INT;
  estado_e  estado_bitacora;
  estado_u  estado_bitacora;
  textos TEXT[] := ARRAY[
    'Inducción y configuración.', 'Reunión de kickoff.', 'Resolución de bugs.',
    'Desarrollo de specs.', 'Tests unitarios.', 'Retrospectiva.',
    'Integración API.', 'Optimización de queries.', 'Presentación de avance.',
    'Autenticación.', 'Reportería.', 'Migración de datos.', 'CI/CD.',
    'Cierre sprint.', 'Refactorización.', 'Entrega final.'
  ];
BEGIN
  FOR pp_rec IN
    SELECT pp.id, pp.periodo_id, pp.semana_actual, pa.is_active, pa.total_semanas
    FROM proyecto_periodo pp
    JOIN periodo_academico pa ON pa.id = pp.periodo_id
  LOOP
    max_sem := CASE WHEN pp_rec.is_active THEN 8 ELSE pp_rec.total_semanas END;

    FOR sem IN 1..max_sem LOOP
      IF NOT pp_rec.is_active THEN
        DECLARE r FLOAT := random(); BEGIN
          IF r < 0.85 THEN estado_e := 'aprobada'::estado_bitacora; estado_u := 'aprobada'::estado_bitacora;
          ELSIF r < 0.93 THEN estado_e := 'corregida'::estado_bitacora; estado_u := 'aprobada'::estado_bitacora;
          ELSIF r < 0.97 THEN estado_e := 'reprobada'::estado_bitacora; estado_u := 'aprobada'::estado_bitacora;
          ELSE estado_e := 'enviada'::estado_bitacora; estado_u := 'enviada'::estado_bitacora; END IF;
        END;
      ELSE
        IF sem < max_sem THEN
          estado_e := (CASE WHEN random() < 0.80 THEN 'aprobada' WHEN random() < 0.90 THEN 'corregida' ELSE 'enviada' END)::estado_bitacora;
          estado_u := (CASE WHEN estado_e = 'aprobada' AND random() < 0.85 THEN 'aprobada' ELSE 'enviada' END)::estado_bitacora;
        ELSE estado_e := 'enviada'::estado_bitacora; estado_u := 'enviada'::estado_bitacora; END IF;
      END IF;

      INSERT INTO bitacora (
        proyecto_periodo_id, semana, texto, fecha_envio, estado_emp, estado_udd,
        fecha_revision_emp, fecha_revision_udd, feedback_emp, feedback_udd
      )
      VALUES (
        pp_rec.id, sem, textos[sem], NOW() - ((max_sem - sem) * 7 || ' days')::interval,
        estado_e, estado_u,
        CASE WHEN estado_e IN ('aprobada','corregida','reprobada') THEN NOW() - ((max_sem - sem) * 7 - 2 || ' days')::interval ELSE NULL END,
        CASE WHEN estado_u IN ('aprobada','corregida') THEN NOW() - ((max_sem - sem) * 7 - 3 || ' days')::interval ELSE NULL END,
        CASE estado_e WHEN 'aprobada' THEN 'Buen trabajo' WHEN 'corregida' THEN 'Falta detalle' ELSE NULL END,
        CASE estado_u WHEN 'aprobada' THEN 'Aprobado' ELSE NULL END
      );
    END LOOP;
  END LOOP;
END;
$$;

-- ============================================================
-- SECCIÓN 13: EVALUACIONES
-- ============================================================
DO $$
DECLARE
  pp_rec RECORD; h_rec RECORD; eval_id INT; c_rec RECORD; nota DECIMAL(3,1); evaluador UUID; suma DECIMAL;
BEGIN
  FOR pp_rec IN
    SELECT pp.id, pp.periodo_id, pp.tutor_udd_id, pp.tutor_empresa_id, pa.is_active
    FROM proyecto_periodo pp JOIN periodo_academico pa ON pa.id = pp.periodo_id
  LOOP
    FOR h_rec IN
      SELECT he.id, he.semana, he.peso_pct, he.evaluador
      FROM hito_evaluacion he
      WHERE he.periodo_id = pp_rec.periodo_id AND (pp_rec.is_active = FALSE OR he.semana <= 4)
      ORDER BY he.orden
    LOOP
      evaluador := CASE h_rec.evaluador WHEN 'udd' THEN pp_rec.tutor_udd_id WHEN 'empresa' THEN pp_rec.tutor_empresa_id ELSE pp_rec.tutor_udd_id END;
      INSERT INTO evaluacion_hito (hito_id, proyecto_periodo_id, evaluado_por, feedback, fecha_evaluacion)
      VALUES (h_rec.id, pp_rec.id, evaluador, 'Buen desempeño general', NOW() - (floor(random()*30)::int || ' days')::interval) RETURNING id INTO eval_id;
      suma := 0;
      FOR c_rec IN SELECT id, peso_pct FROM competencia_hito WHERE hito_id = h_rec.id ORDER BY orden LOOP
        nota := LEAST(7.0, GREATEST(1.0, ROUND((4.5 + random() * 2.5)::numeric, 1)));
        INSERT INTO puntaje_competencia (evaluacion_id, competencia_id, nota) VALUES (eval_id, c_rec.id, nota);
        suma := suma + (nota * (c_rec.peso_pct::numeric / 100));
      END LOOP;
      UPDATE evaluacion_hito SET nota_calculada = ROUND(suma::numeric, 1) WHERE id = eval_id;
    END LOOP;
  END LOOP;
END;
$$;

-- ============================================================
-- SECCIÓN 14: POSTULACIONES
-- ============================================================
DO $$
DECLARE
  a_rec RECORD; p_rec RECORD; estados estado_postulacion[] := ARRAY['enviada','revision_udd','revision_empresa','entrevista','aceptada','rechazada'];
BEGIN
  FOR a_rec IN SELECT id FROM alumno ORDER BY random() LIMIT 800 LOOP
    FOR p_rec IN SELECT p.id, pp.periodo_id FROM proyecto p JOIN proyecto_periodo pp ON pp.proyecto_id = p.id WHERE pp.alumno_id != a_rec.id ORDER BY random() LIMIT 3 LOOP
      BEGIN
        INSERT INTO postulacion (proyecto_id, alumno_id, periodo_id, estado, carta_motivacion, fecha_postulacion)
        VALUES (p_rec.id, a_rec.id, p_rec.periodo_id, estados[1 + floor(random()*6)::int], 'Estoy muy motivado por este proyecto.', NOW() - (floor(random()*180)::int || ' days')::interval);
      EXCEPTION WHEN unique_violation THEN NULL; END;
    END LOOP;
  END LOOP;
END;
$$;

-- ============================================================
-- SECCIÓN 15: BADGES
-- ============================================================
DO $$
DECLARE
  pp_rec RECORD; nota DECIMAL; sem_aprov INT;
BEGIN
  FOR pp_rec IN
    SELECT pp.id AS pp_id, pp.alumno_id, pp.periodo_id, pp.nota_final
    FROM proyecto_periodo pp JOIN periodo_academico pa ON pa.id = pp.periodo_id WHERE pa.is_active = FALSE
  LOOP
    nota := COALESCE(pp_rec.nota_final, 0);
    SELECT COUNT(*) INTO sem_aprov FROM bitacora WHERE proyecto_periodo_id = pp_rec.pp_id AND estado_emp = 'aprobada' AND estado_udd = 'aprobada';

    IF nota >= 6.3 THEN
      BEGIN INSERT INTO alumno_badge (alumno_id, badge_id, periodo_id, motivo) SELECT pp_rec.alumno_id, b.id, pp_rec.periodo_id, 'Nota final ' || nota FROM badge b WHERE b.nombre = 'Alumno Destacado'; EXCEPTION WHEN unique_violation THEN NULL; END;
    END IF;
  END LOOP;
END;
$$;

-- ============================================================
-- SECCIÓN 16 Y 17: NOTIFICACIONES Y VERIFICACIÓN
-- ============================================================
INSERT INTO notificacion (destinatario_id, tipo, titulo, mensaje, enviada)
SELECT a.id, 'recordatorio_perfil', 'Completa tu perfil digital', 'Recuerda actualizar tu CV.', TRUE FROM alumno a WHERE a.url_linkedin IS NULL LIMIT 300;

DO $$
BEGIN
  RAISE NOTICE '============================================';
  RAISE NOTICE 'ICLAE SEED 2026 COMPLETADO A ESCALA REAL';
  RAISE NOTICE 'Alumnos:           %', (SELECT COUNT(*) FROM alumno);
  RAISE NOTICE 'Empresas:          %', (SELECT COUNT(*) FROM empresa);
  RAISE NOTICE 'Bitácoras:         %', (SELECT COUNT(*) FROM bitacora);
  RAISE NOTICE '============================================';
END;
$$;