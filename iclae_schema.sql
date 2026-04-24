-- ============================================================
--  ICLAE DIGITAL HUB — Schema SQL completO
--  Motor: PostgreSQL 15+
-- ============================================================

-- ============================================================
-- 1. EXTENSIONES
-- ============================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- 2. ENUMERACIONES
-- ============================================================

CREATE TYPE rol_usuario AS ENUM (
  'alumno',
  'tutor_udd',
  'tutor_empresa',
  'admin_iclae'
);

CREATE TYPE estado_proyecto AS ENUM (
  'abierto',
  'en_curso',
  'cerrado'
);

CREATE TYPE modalidad_proyecto AS ENUM (
  'presencial',
  'hibrido',
  'remoto'
);

CREATE TYPE estado_bitacora AS ENUM (
  'pendiente',
  'borrador',
  'enviada',
  'aprobada',
  'corregida',
  'reprobada'
);

CREATE TYPE estado_postulacion AS ENUM (
  'enviada',
  'revision_udd',
  'revision_empresa',
  'entrevista',
  'aceptada',
  'rechazada'
);

CREATE TYPE estado_hito AS ENUM (
  'pendiente',
  'disponible',
  'evaluado'
);

CREATE TYPE metodo_calculo_bitacora AS ENUM (
  'aprobadas',
  'promedio',
  'completitud'
);

CREATE TYPE evaluador_hito AS ENUM (
  'ambos',
  'udd',
  'empresa'
);

CREATE TYPE tamano_empresa AS ENUM (
  'pequeña',
  'mediana',
  'grande'
);

CREATE TYPE presencia_empresa AS ENUM (
  'chile',
  'multinacional'
);

-- ============================================================
-- 3. TABLAS BASE (sin dependencias)
-- ============================================================

-- 3.1 Universidad / institución
CREATE TABLE universidad (
  id          SERIAL PRIMARY KEY,
  nombre      VARCHAR(255) NOT NULL,
  codigo      VARCHAR(20) UNIQUE NOT NULL
);

-- 3.2 Sedes / campus
CREATE TABLE sede (
  id              SERIAL PRIMARY KEY,
  universidad_id  INT NOT NULL REFERENCES universidad(id) ON DELETE CASCADE,
  nombre          VARCHAR(150) NOT NULL,      -- 'Santiago', 'Concepción'
  ciudad          VARCHAR(100),
  region          VARCHAR(100)
);

-- 3.3 Carreras
CREATE TABLE carrera (
  id              SERIAL PRIMARY KEY,
  universidad_id  INT NOT NULL REFERENCES universidad(id) ON DELETE CASCADE,
  nombre          VARCHAR(255) NOT NULL,      -- 'Ingeniería Informática'
  codigo          VARCHAR(30) UNIQUE,
  facultad        VARCHAR(150)
);

-- 3.4 Empresas
CREATE TABLE empresa (
  id                SERIAL PRIMARY KEY,
  nombre            VARCHAR(255) NOT NULL,
  rubro             VARCHAR(150),             -- 'Fintech', 'Banca', 'Retail'...
  tamano            tamano_empresa,
  presencia         presencia_empresa DEFAULT 'chile',
  empleados_aprox   VARCHAR(50),              -- '500+', '10.000+'
  ubicacion         VARCHAR(255),
  campus_id         INT REFERENCES sede(id),  -- campus UDD al que está vinculada
  is_active         BOOLEAN DEFAULT TRUE,
  enps_score        DECIMAL(3,1),             -- 0.0 – 10.0
  created_at        TIMESTAMPTZ DEFAULT NOW(),
  updated_at        TIMESTAMPTZ DEFAULT NOW()
);

-- 3.5 Período académico
CREATE TABLE periodo_academico (
  id              SERIAL PRIMARY KEY,
  nombre          VARCHAR(20) NOT NULL UNIQUE, -- '2024-1'
  fecha_inicio    DATE NOT NULL,
  fecha_fin       DATE NOT NULL,
  total_semanas   INT NOT NULL DEFAULT 13,
  is_active       BOOLEAN DEFAULT FALSE,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 4. USUARIOS
-- ============================================================

CREATE TABLE usuario (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email           VARCHAR(254) UNIQUE NOT NULL,
  password_hash   TEXT NOT NULL,
  rol             rol_usuario NOT NULL,
  nombre          VARCHAR(150) NOT NULL,
  apellido        VARCHAR(150) NOT NULL,
  avatar_url      TEXT,
  is_active       BOOLEAN DEFAULT TRUE,
  last_login      TIMESTAMPTZ,
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 4.1 Perfil extendido alumno
CREATE TABLE alumno (
  id              UUID PRIMARY KEY REFERENCES usuario(id) ON DELETE CASCADE,
  carrera_id      INT NOT NULL REFERENCES carrera(id),
  sede_id         INT NOT NULL REFERENCES sede(id),
  generacion      INT,                        -- año de ingreso
  numero_alumno   VARCHAR(30) UNIQUE,
  url_linkedin    TEXT,
  url_cv          TEXT,
  url_youtube     TEXT,
  preferences     JSONB DEFAULT '{}',         -- preferencias personalizadas
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 4.2 Perfil extendido tutor UDD
CREATE TABLE tutor_udd (
  id              UUID PRIMARY KEY REFERENCES usuario(id) ON DELETE CASCADE,
  sede_id         INT REFERENCES sede(id),
  departamento    VARCHAR(150),
  max_alumnos     INT DEFAULT 15,             -- carga máxima
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 4.3 Perfil extendido tutor empresa
CREATE TABLE tutor_empresa (
  id              UUID PRIMARY KEY REFERENCES usuario(id) ON DELETE CASCADE,
  empresa_id      INT NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
  cargo           VARCHAR(150),
  area            VARCHAR(150),
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 5. PROYECTOS Y ASIGNACIONES
-- ============================================================

-- 5.1 Proyecto (plantilla, independiente del período)
CREATE TABLE proyecto (
  id              SERIAL PRIMARY KEY,
  empresa_id      INT NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
  titulo          VARCHAR(255) NOT NULL,
  descripcion     TEXT,
  carrera_id      INT REFERENCES carrera(id),
  modalidad       modalidad_proyecto DEFAULT 'hibrido',
  vacantes        INT DEFAULT 1,
  is_active       BOOLEAN DEFAULT TRUE,
  created_by      UUID REFERENCES usuario(id),
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 5.2 Proyecto en período (instancia activa de un proyecto)
CREATE TABLE proyecto_periodo (
  id              SERIAL PRIMARY KEY,
  proyecto_id     INT NOT NULL REFERENCES proyecto(id) ON DELETE CASCADE,
  periodo_id      INT NOT NULL REFERENCES periodo_academico(id),
  alumno_id       UUID REFERENCES alumno(id),
  tutor_udd_id    UUID REFERENCES tutor_udd(id),
  tutor_empresa_id UUID REFERENCES tutor_empresa(id),
  sede_id         INT REFERENCES sede(id),
  estado          estado_proyecto DEFAULT 'abierto',
  semana_actual   INT DEFAULT 1,
  nota_final      DECIMAL(3,1),
  fecha_inicio    DATE,
  fecha_fin       DATE,
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (proyecto_id, periodo_id, alumno_id)
);

-- ============================================================
-- 6. BITÁCORAS
-- ============================================================

CREATE TABLE bitacora (
  id                  SERIAL PRIMARY KEY,
  proyecto_periodo_id INT NOT NULL REFERENCES proyecto_periodo(id) ON DELETE CASCADE,
  semana              INT NOT NULL,           -- 1 a 13
  texto               TEXT,
  fecha_envio         TIMESTAMPTZ,
  estado_emp          estado_bitacora DEFAULT 'pendiente',
  estado_udd          estado_bitacora DEFAULT 'pendiente',
  fecha_revision_emp  TIMESTAMPTZ,
  fecha_revision_udd  TIMESTAMPTZ,
  feedback_emp        TEXT,
  feedback_udd        TEXT,
  created_at          TIMESTAMPTZ DEFAULT NOW(),
  updated_at          TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (proyecto_periodo_id, semana)
);

-- 6.1 Evidencias adjuntas a bitácoras
CREATE TABLE bitacora_evidencia (
  id              SERIAL PRIMARY KEY,
  bitacora_id     INT NOT NULL REFERENCES bitacora(id) ON DELETE CASCADE,
  nombre_archivo  VARCHAR(255) NOT NULL,
  url             TEXT NOT NULL,
  tipo_archivo    VARCHAR(50),                -- 'pdf', 'imagen', 'video'
  tamaño_bytes    BIGINT,
  uploaded_by     UUID REFERENCES usuario(id),
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 7. POSTULACIONES
-- ============================================================

CREATE TABLE postulacion (
  id                  SERIAL PRIMARY KEY,
  proyecto_id         INT NOT NULL REFERENCES proyecto(id) ON DELETE CASCADE,
  alumno_id           UUID NOT NULL REFERENCES alumno(id) ON DELETE CASCADE,
  periodo_id          INT NOT NULL REFERENCES periodo_academico(id),
  estado              estado_postulacion DEFAULT 'enviada',
  carta_motivacion    TEXT,
  linkedin_snapshot   TEXT,                  -- copia del URL al momento de postular
  cv_snapshot         TEXT,
  youtube_snapshot    TEXT,
  feedback_rechazo    TEXT,
  fecha_postulacion   TIMESTAMPTZ DEFAULT NOW(),
  fecha_actualizacion TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (proyecto_id, alumno_id, periodo_id)
);

-- ============================================================
-- 8. SISTEMA DE EVALUACIONES
-- ============================================================

-- 8.1 Configuración global por período
CREATE TABLE config_evaluacion_periodo (
  id                          SERIAL PRIMARY KEY,
  periodo_id                  INT NOT NULL UNIQUE REFERENCES periodo_academico(id),
  peso_bitacoras_pct          INT NOT NULL DEFAULT 10  CHECK (peso_bitacoras_pct BETWEEN 0 AND 50),
  metodo_calculo_bitacoras    metodo_calculo_bitacora DEFAULT 'aprobadas',
  umbral_bitacoras_pct        INT DEFAULT 80,
  created_at                  TIMESTAMPTZ DEFAULT NOW(),
  updated_at                  TIMESTAMPTZ DEFAULT NOW()
);

-- 8.2 Hitos de evaluación (por período)
CREATE TABLE hito_evaluacion (
  id              SERIAL PRIMARY KEY,
  periodo_id      INT NOT NULL REFERENCES periodo_academico(id) ON DELETE CASCADE,
  nombre          VARCHAR(150) NOT NULL,      -- 'Evaluación intermedia'
  semana          INT NOT NULL,               -- semana en que se aplica
  peso_pct        INT NOT NULL CHECK (peso_pct BETWEEN 1 AND 100),
  evaluador       evaluador_hito DEFAULT 'ambos',
  estado          estado_hito DEFAULT 'pendiente',
  doc_rubrica_url TEXT,                       -- URL al documento de rúbrica
  orden           INT DEFAULT 1,
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 8.3 Competencias por hito
CREATE TABLE competencia_hito (
  id              SERIAL PRIMARY KEY,
  hito_id         INT NOT NULL REFERENCES hito_evaluacion(id) ON DELETE CASCADE,
  nombre          VARCHAR(150) NOT NULL,
  descripcion     TEXT,
  peso_pct        INT NOT NULL CHECK (peso_pct BETWEEN 1 AND 100),
  orden           INT DEFAULT 1,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 8.4 Evaluación de un alumno en un hito
CREATE TABLE evaluacion_hito (
  id                  SERIAL PRIMARY KEY,
  hito_id             INT NOT NULL REFERENCES hito_evaluacion(id) ON DELETE CASCADE,
  proyecto_periodo_id INT NOT NULL REFERENCES proyecto_periodo(id) ON DELETE CASCADE,
  evaluado_por        UUID NOT NULL REFERENCES usuario(id),
  feedback            TEXT,
  nota_calculada      DECIMAL(3,1),           -- calculada automáticamente
  fecha_evaluacion    TIMESTAMPTZ DEFAULT NOW(),
  updated_at          TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (hito_id, proyecto_periodo_id)
);

-- 8.5 Puntaje por competencia dentro de una evaluación
CREATE TABLE puntaje_competencia (
  id                  SERIAL PRIMARY KEY,
  evaluacion_id       INT NOT NULL REFERENCES evaluacion_hito(id) ON DELETE CASCADE,
  competencia_id      INT NOT NULL REFERENCES competencia_hito(id) ON DELETE CASCADE,
  nota                DECIMAL(3,1) NOT NULL CHECK (nota BETWEEN 1.0 AND 7.0),
  UNIQUE (evaluacion_id, competencia_id)
);

-- ============================================================
-- 9. BADGES / INSIGNIAS
-- ============================================================

CREATE TABLE badge (
  id          SERIAL PRIMARY KEY,
  nombre      VARCHAR(100) NOT NULL,
  descripcion TEXT,
  icono       VARCHAR(10),                    -- emoji o código de ícono
  criterio    TEXT,                           -- descripción del criterio de otorgamiento
  is_active   BOOLEAN DEFAULT TRUE,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE alumno_badge (
  id          SERIAL PRIMARY KEY,
  alumno_id   UUID NOT NULL REFERENCES alumno(id) ON DELETE CASCADE,
  badge_id    INT NOT NULL REFERENCES badge(id) ON DELETE CASCADE,
  periodo_id  INT REFERENCES periodo_academico(id),
  motivo      TEXT,
  otorgado_por UUID REFERENCES usuario(id),
  fecha_logro TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (alumno_id, badge_id, periodo_id)
);

-- ============================================================
-- 10. NOTIFICACIONES Y RECORDATORIOS
-- ============================================================

CREATE TABLE notificacion (
  id              SERIAL PRIMARY KEY,
  destinatario_id UUID NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
  tipo            VARCHAR(50) NOT NULL,       -- 'recordatorio_perfil', 'bitacora_pendiente', etc.
  titulo          VARCHAR(255) NOT NULL,
  mensaje         TEXT,
  leida           BOOLEAN DEFAULT FALSE,
  enviada         BOOLEAN DEFAULT FALSE,
  fecha_envio     TIMESTAMPTZ,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Envío masivo de recordatorios (admin)
CREATE TABLE recordatorio_masivo (
  id              SERIAL PRIMARY KEY,
  enviado_por     UUID NOT NULL REFERENCES usuario(id),
  segmento        VARCHAR(50),                -- 'sin_linkedin', 'sin_cv', 'sin_youtube', 'todos'
  mensaje         TEXT NOT NULL,
  cantidad_envios INT,
  fecha_envio     TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 11. ANALÍTICO — VISTAS MATERIALIZADAS
-- ============================================================

-- 11.1 Vista: resumen por período
CREATE OR REPLACE VIEW v_resumen_periodo AS
SELECT
  pa.id               AS periodo_id,
  pa.nombre           AS periodo,
  COUNT(DISTINCT pp.alumno_id)        AS total_alumnos,
  COUNT(DISTINCT pp.proyecto_id)      AS total_proyectos,
  COUNT(DISTINCT p.empresa_id)        AS total_empresas,
  AVG(pp.nota_final)                  AS nota_promedio,
  COUNT(DISTINCT po.alumno_id)
    FILTER (WHERE po.estado = 'aceptada') AS contratados
FROM periodo_academico pa
LEFT JOIN proyecto_periodo pp ON pp.periodo_id = pa.id
LEFT JOIN proyecto p ON p.id = pp.proyecto_id
LEFT JOIN postulacion po ON po.periodo_id = pa.id
GROUP BY pa.id, pa.nombre;

-- 11.2 Vista: progreso de bitácoras por alumno
CREATE OR REPLACE VIEW v_progreso_bitacoras AS
SELECT
  pp.id                               AS proyecto_periodo_id,
  pp.alumno_id,
  pp.periodo_id,
  pa.total_semanas,
  COUNT(b.id)                         AS semanas_registradas,
  COUNT(b.id) FILTER (WHERE b.estado_emp = 'aprobada' AND b.estado_udd = 'aprobada')
                                      AS semanas_aprobadas,
  COUNT(b.id) FILTER (WHERE b.estado_emp = 'corregida' OR b.estado_emp = 'reprobada')
                                      AS semanas_con_observaciones,
  ROUND(
    COUNT(b.id) FILTER (WHERE b.estado_emp='aprobada' AND b.estado_udd='aprobada')::NUMERIC
    / pa.total_semanas * 7.0, 1
  )                                   AS nota_bitacoras
FROM proyecto_periodo pp
JOIN periodo_academico pa ON pa.id = pp.periodo_id
LEFT JOIN bitacora b ON b.proyecto_periodo_id = pp.id
GROUP BY pp.id, pp.alumno_id, pp.periodo_id, pa.total_semanas;

-- 11.3 Vista: nota final consolidada
CREATE OR REPLACE VIEW v_nota_final AS
SELECT
  pp.id                               AS proyecto_periodo_id,
  pp.alumno_id,
  pp.periodo_id,
  vb.nota_bitacoras,
  cep.peso_bitacoras_pct,
  COALESCE(
    SUM(eh.nota_calculada * (hi.peso_pct::NUMERIC / 100)),
    0
  )                                   AS nota_hitos_ponderada,
  ROUND(
    vb.nota_bitacoras * (cep.peso_bitacoras_pct::NUMERIC / 100)
    + COALESCE(SUM(eh.nota_calculada * (hi.peso_pct::NUMERIC / 100)), 0)
    / (1 - cep.peso_bitacoras_pct::NUMERIC / 100 + 1e-9), 1
  )                                   AS nota_final_estimada
FROM proyecto_periodo pp
JOIN periodo_academico pa ON pa.id = pp.periodo_id
JOIN config_evaluacion_periodo cep ON cep.periodo_id = pa.id
JOIN v_progreso_bitacoras vb ON vb.proyecto_periodo_id = pp.id
LEFT JOIN evaluacion_hito eh ON eh.proyecto_periodo_id = pp.id
LEFT JOIN hito_evaluacion hi ON hi.id = eh.hito_id
GROUP BY pp.id, pp.alumno_id, pp.periodo_id, vb.nota_bitacoras, cep.peso_bitacoras_pct;

-- 11.4 Vista: distribución por rubro
CREATE OR REPLACE VIEW v_distribucion_rubro AS
SELECT
  e.rubro,
  pp.periodo_id,
  COUNT(DISTINCT pp.alumno_id) AS alumnos,
  COUNT(DISTINCT pp.proyecto_id) AS proyectos
FROM proyecto_periodo pp
JOIN proyecto p ON p.id = pp.proyecto_id
JOIN empresa e ON e.id = p.empresa_id
GROUP BY e.rubro, pp.periodo_id;

-- ============================================================
-- 12. ÍNDICES
-- ============================================================

CREATE INDEX idx_alumno_carrera       ON alumno(carrera_id);
CREATE INDEX idx_alumno_sede          ON alumno(sede_id);
CREATE INDEX idx_proyecto_empresa     ON proyecto(empresa_id);
CREATE INDEX idx_pp_alumno            ON proyecto_periodo(alumno_id);
CREATE INDEX idx_pp_periodo           ON proyecto_periodo(periodo_id);
CREATE INDEX idx_pp_tutor_udd         ON proyecto_periodo(tutor_udd_id);
CREATE INDEX idx_pp_tutor_emp         ON proyecto_periodo(tutor_empresa_id);
CREATE INDEX idx_bitacora_pp          ON bitacora(proyecto_periodo_id);
CREATE INDEX idx_bitacora_semana      ON bitacora(proyecto_periodo_id, semana);
CREATE INDEX idx_postulacion_alumno   ON postulacion(alumno_id);
CREATE INDEX idx_postulacion_proyecto ON postulacion(proyecto_id);
CREATE INDEX idx_ev_hito_pp           ON evaluacion_hito(proyecto_periodo_id);
CREATE INDEX idx_puntaje_eval         ON puntaje_competencia(evaluacion_id);
CREATE INDEX idx_notif_dest           ON notificacion(destinatario_id, leida);
CREATE INDEX idx_alumno_badge         ON alumno_badge(alumno_id);
CREATE INDEX idx_hito_periodo         ON hito_evaluacion(periodo_id);

-- ============================================================
-- 13. TRIGGERS — updated_at automático
-- ============================================================

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Aplicar a todas las tablas con updated_at
DO $$
DECLARE
  t TEXT;
BEGIN
  FOREACH t IN ARRAY ARRAY[
    'usuario','alumno','empresa','proyecto','proyecto_periodo',
    'bitacora','postulacion','config_evaluacion_periodo',
    'hito_evaluacion','evaluacion_hito'
  ] LOOP
    EXECUTE format('
      CREATE TRIGGER trg_%I_updated_at
      BEFORE UPDATE ON %I
      FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    ', t, t);
  END LOOP;
END;
$$;

-- ============================================================
-- 14. TRIGGER — calcular nota_calculada automáticamente
-- ============================================================

CREATE OR REPLACE FUNCTION calcular_nota_hito()
RETURNS TRIGGER AS $$
DECLARE
  v_nota DECIMAL(3,1);
BEGIN
  SELECT ROUND(SUM(pc.nota * (ch.peso_pct::NUMERIC / 100)), 1)
  INTO v_nota
  FROM puntaje_competencia pc
  JOIN competencia_hito ch ON ch.id = pc.competencia_id
  WHERE pc.evaluacion_id = NEW.evaluacion_id;

  UPDATE evaluacion_hito
  SET nota_calculada = v_nota
  WHERE id = NEW.evaluacion_id;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_calcular_nota
AFTER INSERT OR UPDATE ON puntaje_competencia
FOR EACH ROW EXECUTE FUNCTION calcular_nota_hito();

-- ============================================================
-- 15. DATOS INICIALES (seed)
-- ============================================================

-- Universidad
INSERT INTO universidad (nombre, codigo) VALUES ('Universidad del Desarrollo', 'UDD');

-- Sedes
INSERT INTO sede (universidad_id, nombre, ciudad, region)
VALUES
  (1, 'Santiago',    'Santiago',    'Región Metropolitana'),
  (1, 'Concepción',  'Concepción',  'Región del Biobío');

-- Carreras
INSERT INTO carrera (universidad_id, nombre, codigo, facultad)
VALUES
  (1, 'Ingeniería Informática',    'INFO', 'Ingeniería'),
  (1, 'Ingeniería Civil Industrial','ICI',  'Ingeniería'),
  (1, 'Ingeniería Comercial',      'ICOM', 'Economía y Negocios'),
  (1, 'Diseño',                    'DIS',  'Arquitectura y Diseño'),
  (1, 'Psicología',                'PSI',  'Ciencias Sociales'),
  (1, 'Administración de Empresas','ADM',  'Economía y Negocios');

-- Período activo
INSERT INTO periodo_academico (nombre, fecha_inicio, fecha_fin, total_semanas, is_active)
VALUES ('2024-1', '2024-03-01', '2024-06-30', 13, TRUE);

-- Configuración evaluación del período
INSERT INTO config_evaluacion_periodo (periodo_id, peso_bitacoras_pct, metodo_calculo_bitacoras, umbral_bitacoras_pct)
VALUES (1, 10, 'aprobadas', 80);

-- Hitos del período 2024-1 (pesos: 10% bitácoras + 20 + 30 + 50 = 100%)
INSERT INTO hito_evaluacion (periodo_id, nombre, semana, peso_pct, evaluador, estado, orden)
VALUES
  (1, 'Diagnóstico inicial',    3,  20, 'udd',    'disponible', 1),
  (1, 'Evaluación intermedia',  7,  30, 'ambos',  'pendiente',  2),
  (1, 'Evaluación final',       13, 50, 'ambos',  'pendiente',  3);

-- Competencias Hito 1
INSERT INTO competencia_hito (hito_id, nombre, descripcion, peso_pct, orden)
VALUES
  (1, 'Adaptación al equipo',     'Integración con compañeros y cultura organizacional', 30, 1),
  (1, 'Comprensión del proyecto', 'Entiende alcance, objetivos y tecnologías',           40, 2),
  (1, 'Comunicación inicial',     'Claridad en comunicación con tutores y equipo',       30, 3);

-- Competencias Hito 2
INSERT INTO competencia_hito (hito_id, nombre, descripcion, peso_pct, orden)
VALUES
  (2, 'Trabajo en equipo',        'Colaboración efectiva con el equipo',          25, 1),
  (2, 'Habilidades técnicas',     'Dominio de tecnologías del proyecto',           35, 2),
  (2, 'Resolución de problemas',  'Capacidad para superar obstáculos técnicos',    25, 3),
  (2, 'Comunicación',             'Presentación de avances y resultados',          15, 4);

-- Competencias Hito 3
INSERT INTO competencia_hito (hito_id, nombre, descripcion, peso_pct, orden)
VALUES
  (3, 'Trabajo en equipo',       'Impacto sostenido durante la práctica',        20, 1),
  (3, 'Habilidades técnicas',    'Nivel técnico alcanzado al finalizar',          30, 2),
  (3, 'Liderazgo',               'Iniciativa y capacidad de liderazgo',           20, 3),
  (3, 'Comunicación',            'Presentación final del proyecto',               15, 4),
  (3, 'Impacto en la empresa',   'Valor generado para la organización',           15, 5);

-- Badges disponibles
INSERT INTO badge (nombre, descripcion, icono, criterio)
VALUES
  ('Alumno Destacado',  'Rendimiento sobresaliente en el período',          '🏆', 'Nota final >= 6.5'),
  ('Innovador',         'Propuso soluciones creativas al proyecto',         '💡', 'Reconocimiento del tutor empresa'),
  ('Colaborador',       'Demostró excelente trabajo en equipo',             '🤝', 'Puntaje competencia trabajo en equipo >= 6.5'),
  ('Puntualidad',       'Entregó todas las bitácoras sin atrasos',          '⭐', '13/13 bitácoras enviadas en fecha'),
  ('Alto Desempeño',    'Nota final >= 6.5',                                '🚀', 'Nota final calculada >= 6.5'),
  ('Liderazgo',         'Demostró iniciativa excepcional en el proyecto',   '🎯', 'Puntaje liderazgo >= 6.5'),
  ('Perfil Completo',   'Completó LinkedIn, CV y video de presentación',    '✅', 'Los 3 links del perfil configurados'),
  ('Primera Práctica',  'Completó su primera práctica ICLAE',               '🎓', 'primer proyecto_periodo cerrado');

-- ============================================================
-- FIN DEL SCHEMA
-- ============================================================
/*
  RESUMEN DE ENTIDADES:
  ┌─────────────────────────────────────────────────────────┐
  │  CORE           │ usuario, alumno, tutor_udd,           │
  │                 │ tutor_empresa                          │
  │  ACADÉMICO      │ universidad, sede, carrera,            │
  │                 │ periodo_academico                      │
  │  EMPRESAS       │ empresa                               │
  │  PROYECTOS      │ proyecto, proyecto_periodo             │
  │  BITÁCORAS      │ bitacora, bitacora_evidencia           │
  │  POSTULACIONES  │ postulacion                           │
  │  EVALUACIONES   │ config_evaluacion_periodo,             │
  │                 │ hito_evaluacion, competencia_hito,     │
  │                 │ evaluacion_hito, puntaje_competencia   │
  │  GAMIFICACIÓN   │ badge, alumno_badge                   │
  │  COMUNICACIÓN   │ notificacion, recordatorio_masivo      │
  │  ANALÍTICO      │ v_resumen_periodo, v_progreso_bitacoras│
  │                 │ v_nota_final, v_distribucion_rubro     │
  └─────────────────────────────────────────────────────────┘
*/
