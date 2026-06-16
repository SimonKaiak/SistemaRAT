-- =============================================================
-- Poblamiento Empresa 2: Permify SpA
-- PostgreSQL — SistemaRAT
-- Ejecutar DESPUÉS de: poblacion_empresa1_postgresql.sql
-- =============================================================

-- =========================
-- poblacion_empresa_permify.sql
-- =========================
-- Script de poblamiento inicial para Permify SpA (EMPRESA ID=2).
-- Debe ejecutarse DESPUÉS de poblacion_empresa_mohala.sql.
--
-- Datos que inserta:
--   Empresa   → Permify SpA (RUT 74.123.456-7, activa).
--
--   Departamentos (3, IDs 4-6):
--     Gerencia General, Recursos Humanos, TI.
--
--   Niveles Jerárquicos (3, IDs 4-6):
--     Colaborador (4), Supervisor (5), Directivo (6).
--
--   Escala (4 valores, IDs 5-8):
--     1=Desempeño Insuficiente, 2=En Desarrollo,
--     3=Satisfactorio, 4=Sobresaliente.
--
--   Dimensiones (2, IDs 3-4):
--     Corporativas (3), Técnicas (4).
--
--   Competencias (15, IDs 16-30):
--     Corporativas: Innovación y Creatividad, Orientación al
--     Cliente, Cultura Organizacional, Colaboración,
--     Pensamiento Estratégico.
--     Técnicas: Resolución de Problemas, Aprendizaje Continuo,
--     Comunicación Efectiva, Gestión de la Innovación,
--     Liderazgo de Equipos, Desarrollo de Personas, Gestión
--     de Resultados, Logro de Objetivos, Planificación y
--     Control, Iniciativa.
--
--   Cargos (6, IDs 7-12):
--     Colaborador: Analista, Asistente Administrativo.
--     Supervisor: Jefe de RRHH, Coordinador de Proyectos.
--     Directivo: Gerente General, Gerente de Innovación.
--
--   TextosEvaluacion (27, IDs 28-54):
--     Solo para competencias 16, 17 y 21 con textos de prueba.
--     3 indicadores por nivel jerárquico (Colaborador/Supervisor/
--     Directivo). Pendiente reemplazar por textos reales.
--
--   CodigoEvaluacion (27, IDs 28-54):
--     Una fila por TextosEvaluacion.
--
--   Trabajadores (6, IDs 7-12, sin usuario Django):
--     Directivos (sin jefe): Carlos Fuentes, Daniela Vega (coord).
--     Supervisores: Felipe Rojas (jefe=7), Camila Núñez (jefe=8).
--     Colaboradores: Ignacio Pérez (jefe=9), Javiera Muñoz (jefe=10).
--
-- Al final sincroniza las secuencias SERIAL de todas las tablas.
-- =========================

-- =========================
-- Empresa
-- =========================
INSERT INTO "EMPRESA" ("id_empresa", "nombre_empresa", "rut_empresa", "empresa_activa", "registrada_en")
VALUES (2, 'Permify SpA', '74.123.456-7', TRUE, CURRENT_TIMESTAMP);

-- =========================
-- Departamento
-- =========================
INSERT INTO "DEPARTAMENTO" ("id_departamento", "nombre_departamento", "empresa_id_empresa")
VALUES
    (4, 'Gerencia General',             2),
    (5, 'Recursos Humanos',             2),
    (6, 'Tecnología de la Información', 2);

-- =========================
-- Nivel Jerárquico
-- =========================
INSERT INTO "NIVEL_JERARQUICO" ("id_nivel_jerarquico", "nombre_nivel_jerarquico", "empresa_id_empresa")
VALUES
    (4, 'Colaborador', 2),
    (5, 'Supervisor',  2),
    (6, 'Directivo',   2);

-- =========================
-- Escala
-- =========================
INSERT INTO "ESCALA" ("id_escala", "valor", "titulo", "descripcion", "empresa_id_empresa")
VALUES
    (5, 1, 'Desempeño Insuficiente',   'No cumple estándares empresa 2.', 2),
    (6, 2, 'Desempeño en Desarrollo',  'Cumple estándares de manera incompleta en empresa 2.', 2),
    (7, 3, 'Desempeño Satisfactorio',  'Cumple de manera consistente en empresa 2.', 2),
    (8, 4, 'Desempeño Sobresaliente',  'Supera de forma sostenida lo esperado en empresa 2.', 2);

-- =========================
-- Dimensión
-- =========================
INSERT INTO "DIMENSION" ("id_dimension", "nombre_dimension", "empresa_id_empresa")
VALUES
    (3, 'Corporativas', 2),
    (4, 'Técnicas',     2);

-- =========================
-- Competencia
-- =========================
-- Corporativas (Dimensión 3)
INSERT INTO "COMPETENCIA" ("id_competencia", "nombre_competencia", "dimension_id_dimension", "empresa_id_empresa")
VALUES
    (16, 'Innovación y Creatividad',  3, 2),
    (17, 'Orientación al Cliente',    3, 2),
    (18, 'Cultura Organizacional',    3, 2),
    (19, 'Colaboración',              3, 2),
    (20, 'Pensamiento Estratégico',   3, 2);

-- Técnicas (Dimensión 4)
INSERT INTO "COMPETENCIA" ("id_competencia", "nombre_competencia", "dimension_id_dimension", "empresa_id_empresa")
VALUES
    (21, 'Resolución de Problemas',   4, 2),
    (22, 'Aprendizaje Continuo',      4, 2),
    (23, 'Comunicación Efectiva',     4, 2),
    (24, 'Gestión de la Innovación',  4, 2),
    (25, 'Liderazgo de Equipos',      4, 2),
    (26, 'Desarrollo de Personas',    4, 2),
    (27, 'Gestión de Resultados',     4, 2),
    (28, 'Logro de Objetivos',        4, 2),
    (29, 'Planificación y Control',   4, 2),
    (30, 'Iniciativa',                4, 2);

-- =========================
-- Cargo
-- =========================
-- Colaborador (Nivel 4)
INSERT INTO "CARGO" ("id_cargo", "nombre_cargo", "empresa_id_empresa", "nivel_jerarquico_id_nivel_jerarquico")
VALUES
    (7,  'Analista',                 2, 4),
    (8,  'Asistente Administrativo', 2, 4);

-- Supervisor (Nivel 5)
INSERT INTO "CARGO" ("id_cargo", "nombre_cargo", "empresa_id_empresa", "nivel_jerarquico_id_nivel_jerarquico")
VALUES
    (9,  'Jefe de Recursos Humanos', 2, 5),
    (10, 'Coordinador de Proyectos', 2, 5);

-- Directivo (Nivel 6)
INSERT INTO "CARGO" ("id_cargo", "nombre_cargo", "empresa_id_empresa", "nivel_jerarquico_id_nivel_jerarquico")
VALUES
    (11, 'Gerente General',      2, 6),
    (12, 'Gerente de Innovación',2, 6);

-- =========================
-- Textos Evaluación
-- =========================

-- 16. INNOVACIÓN Y CREATIVIDAD (Competencia 16)
INSERT INTO "TEXTOS_EVALUACION" ("id_textos_evaluacion", "codigo_excel", "texto", "empresa_id_empresa", "dimension_id_dimension", "competencia_id_competencia", "nivel_jerarquico_id_nivel_jerarquico")
VALUES
    (28, 'ICC1.1', 'Texto de prueba empresa 2.', 2, 3, 16, 4),
    (29, 'ICC1.2', 'Texto de prueba empresa 2.', 2, 3, 16, 4),
    (30, 'ICC1.3', 'Texto de prueba empresa 2.', 2, 3, 16, 4),
    (31, 'ICS1.1', 'Texto de prueba empresa 2.', 2, 3, 16, 5),
    (32, 'ICS1.2', 'Texto de prueba empresa 2.', 2, 3, 16, 5),
    (33, 'ICS1.3', 'Texto de prueba empresa 2.', 2, 3, 16, 5),
    (34, 'ICD1.1', 'Texto de prueba empresa 2.', 2, 3, 16, 6),
    (35, 'ICD1.2', 'Texto de prueba empresa 2.', 2, 3, 16, 6),
    (36, 'ICD1.3', 'Texto de prueba empresa 2.', 2, 3, 16, 6);

-- 17. ORIENTACIÓN AL CLIENTE (Competencia 17)
INSERT INTO "TEXTOS_EVALUACION" ("id_textos_evaluacion", "codigo_excel", "texto", "empresa_id_empresa", "dimension_id_dimension", "competencia_id_competencia", "nivel_jerarquico_id_nivel_jerarquico")
VALUES
    (37, 'OCC1.1', 'Texto de prueba empresa 2.', 2, 3, 17, 4),
    (38, 'OCC1.2', 'Texto de prueba empresa 2.', 2, 3, 17, 4),
    (39, 'OCC1.3', 'Texto de prueba empresa 2.', 2, 3, 17, 4),
    (40, 'OCS1.1', 'Texto de prueba empresa 2.', 2, 3, 17, 5),
    (41, 'OCS1.2', 'Texto de prueba empresa 2.', 2, 3, 17, 5),
    (42, 'OCS1.3', 'Texto de prueba empresa 2.', 2, 3, 17, 5),
    (43, 'OCD1.1', 'Texto de prueba empresa 2.', 2, 3, 17, 6),
    (44, 'OCD1.2', 'Texto de prueba empresa 2.', 2, 3, 17, 6),
    (45, 'OCD1.3', 'Texto de prueba empresa 2.', 2, 3, 17, 6);

-- 21. RESOLUCIÓN DE PROBLEMAS (Competencia 21)
INSERT INTO "TEXTOS_EVALUACION" ("id_textos_evaluacion", "codigo_excel", "texto", "empresa_id_empresa", "dimension_id_dimension", "competencia_id_competencia", "nivel_jerarquico_id_nivel_jerarquico")
VALUES
    (46, 'RPC1.1', 'Texto de prueba empresa 2.', 2, 4, 21, 4),
    (47, 'RPC1.2', 'Texto de prueba empresa 2.', 2, 4, 21, 4),
    (48, 'RPC1.3', 'Texto de prueba empresa 2.', 2, 4, 21, 4),
    (49, 'RPS1.1', 'Texto de prueba empresa 2.', 2, 4, 21, 5),
    (50, 'RPS1.2', 'Texto de prueba empresa 2.', 2, 4, 21, 5),
    (51, 'RPS1.3', 'Texto de prueba empresa 2.', 2, 4, 21, 5),
    (52, 'RPD1.1', 'Texto de prueba empresa 2.', 2, 4, 21, 6),
    (53, 'RPD1.2', 'Texto de prueba empresa 2.', 2, 4, 21, 6),
    (54, 'RPD1.3', 'Texto de prueba empresa 2.', 2, 4, 21, 6);

-- =========================
-- Código Evaluación
-- =========================
INSERT INTO "CODIGO_EVALUACION" ("id_codigo_evaluacion", "empresa_id_empresa", "dimension_id_dimension", "competencia_id_competencia", "nivel_jerarquico_id_nivel_jerarquico", "textos_evaluacion_codigo_excel", "textos_evaluacion_empresa_id_empresa")
VALUES
    -- Innovación y Creatividad: Colaborador
    (28, 2, 3, 16, 4, 'ICC1.1', 2),
    (29, 2, 3, 16, 4, 'ICC1.2', 2),
    (30, 2, 3, 16, 4, 'ICC1.3', 2),
    -- Innovación y Creatividad: Supervisor
    (31, 2, 3, 16, 5, 'ICS1.1', 2),
    (32, 2, 3, 16, 5, 'ICS1.2', 2),
    (33, 2, 3, 16, 5, 'ICS1.3', 2),
    -- Innovación y Creatividad: Directivo
    (34, 2, 3, 16, 6, 'ICD1.1', 2),
    (35, 2, 3, 16, 6, 'ICD1.2', 2),
    (36, 2, 3, 16, 6, 'ICD1.3', 2),
    -- Orientación al Cliente: Colaborador
    (37, 2, 3, 17, 4, 'OCC1.1', 2),
    (38, 2, 3, 17, 4, 'OCC1.2', 2),
    (39, 2, 3, 17, 4, 'OCC1.3', 2),
    -- Orientación al Cliente: Supervisor
    (40, 2, 3, 17, 5, 'OCS1.1', 2),
    (41, 2, 3, 17, 5, 'OCS1.2', 2),
    (42, 2, 3, 17, 5, 'OCS1.3', 2),
    -- Orientación al Cliente: Directivo
    (43, 2, 3, 17, 6, 'OCD1.1', 2),
    (44, 2, 3, 17, 6, 'OCD1.2', 2),
    (45, 2, 3, 17, 6, 'OCD1.3', 2),
    -- Resolución de Problemas: Colaborador
    (46, 2, 4, 21, 4, 'RPC1.1', 2),
    (47, 2, 4, 21, 4, 'RPC1.2', 2),
    (48, 2, 4, 21, 4, 'RPC1.3', 2),
    -- Resolución de Problemas: Supervisor
    (49, 2, 4, 21, 5, 'RPS1.1', 2),
    (50, 2, 4, 21, 5, 'RPS1.2', 2),
    (51, 2, 4, 21, 5, 'RPS1.3', 2),
    -- Resolución de Problemas: Directivo
    (52, 2, 4, 21, 6, 'RPD1.1', 2),
    (53, 2, 4, 21, 6, 'RPD1.2', 2),
    (54, 2, 4, 21, 6, 'RPD1.3', 2);

-- =========================
-- Trabajador
-- =========================
-- Directivo (sin jefe)
INSERT INTO "TRABAJADOR" ("id_trabajador", "rut", "id_jefe_directo", "nombre", "apellido_paterno", "apellido_materno", "email", "genero", "es_coordinador", "empresa_id_empresa", "nivel_jerarquico_id_nivel_jerarquico", "cargo_id_cargo", "departamento_id_departamento")
VALUES
    (7,  '14.123.456-1', NULL, 'Carlos',  'Fuentes','Mora', 'c.fuentes@permify.cl','Masculino', FALSE, 2, 6, 11, 4),
    (8,  '15.234.567-2', NULL, 'Daniela', 'Vega',   'Soto', 'd.vega@permify.cl',   'Femenino',  TRUE,  2, 6, 12, 4);

-- Supervisor (reportan a ID 7 y 8)
INSERT INTO "TRABAJADOR" ("id_trabajador", "rut", "id_jefe_directo", "nombre", "apellido_paterno", "apellido_materno", "email", "genero", "es_coordinador", "empresa_id_empresa", "nivel_jerarquico_id_nivel_jerarquico", "cargo_id_cargo", "departamento_id_departamento")
VALUES
    (9,  '16.345.678-3', 7, 'Felipe', 'Rojas', 'Lima', 'f.rojas@permify.cl',  'Masculino', FALSE, 2, 5, 9,  5),
    (10, '17.456.789-4', 8, 'Camila', 'Núñez', 'Ríos', 'c.nunez@permify.cl',  'Femenino',  FALSE, 2, 5, 10, 6);

-- Colaborador (reportan a ID 9 y 10)
INSERT INTO "TRABAJADOR" ("id_trabajador", "rut", "id_jefe_directo", "nombre", "apellido_paterno", "apellido_materno", "email", "genero", "es_coordinador", "empresa_id_empresa", "nivel_jerarquico_id_nivel_jerarquico", "cargo_id_cargo", "departamento_id_departamento")
VALUES
    (11, '18.567.890-5', 9,  'Ignacio', 'Pérez', 'Blanc', 'i.perez@permify.cl', 'Masculino', FALSE, 2, 4, 7, 6),
    (12, '19.678.901-6', 10, 'Javiera', 'Muñoz', 'Cerda', 'j.munoz@permify.cl', 'Femenino',  FALSE, 2, 4, 8, 5);

-- =========================
-- =========================