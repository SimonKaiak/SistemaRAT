-- =============================================================
-- Poblamiento Empresa 1: Mohala SpA
-- PostgreSQL — SistemaRAT
-- Ejecutar DESPUÉS de: creacion_tablas_postgresql.sql
-- y DESPUÉS de: python manage.py migrate
-- =============================================================

SET session_replication_role = 'replica';

-- =========================
-- Empresa
-- =========================
INSERT INTO "EMPRESA" ("ID_EMPRESA", "NOMBRE_EMPRESA", "RUT_EMPRESA", "EMPRESA_ACTIVA", "REGISTRADA_EN")
VALUES (1, 'Mohala SpA', '76.123.456-7', TRUE, CURRENT_TIMESTAMP);

-- =========================
-- Departamento
-- =========================
INSERT INTO "DEPARTAMENTO" ("ID_DEPARTAMENTO", "NOMBRE_DEPARTAMENTO", "EMPRESA_ID_EMPRESA")
VALUES
    (1, 'Gerencia General',               1),
    (2, 'Recursos Humanos',               1),
    (3, 'Tecnología de la Información',   1);

-- =========================
-- Nivel Jerárquico
-- =========================
INSERT INTO "NIVEL_JERARQUICO" ("ID_NIVEL_JERARQUICO", "NOMBRE_NIVEL_JERARQUICO", "EMPRESA_ID_EMPRESA")
VALUES
    (1, 'Operativo',   1),
    (2, 'Táctico',     1),
    (3, 'Estratégico', 1);

-- =========================
-- Escala
-- =========================
INSERT INTO "ESCALA" ("ID_ESCALA", "VALOR", "TITULO", "DESCRIPCION", "EMPRESA_ID_EMPRESA")
VALUES
    (1, 1, 'No Logra lo Esperado',          'No cumple con los comportamientos y resultados mínimos definidos para la competencia.', 1),
    (2, 2, 'Logra Parcialmente lo Esperado','Cumple solo en forma incompleta o inconsistente con los comportamientos y resultados definidos para la competencia.', 1),
    (3, 3, 'Logra lo Esperado',             'Cumple de manera consistente con los comportamientos y resultados definidos para la competencia.', 1),
    (4, 4, 'Supera lo Esperado',            'Supera de forma sostenida los comportamientos y resultados definidos para la competencia, agregando valor más allá de lo requerido.', 1);

-- =========================
-- Dimensión
-- =========================
INSERT INTO "DIMENSION" ("ID_DIMENSION", "NOMBRE_DIMENSION", "EMPRESA_ID_EMPRESA")
VALUES
    (1, 'Organizacionales', 1),
    (2, 'Funcionales',      1);

-- =========================
-- Competencia
-- =========================
-- Organizacionales (Dimensión 1)
INSERT INTO "COMPETENCIA" ("ID_COMPETENCIA", "NOMBRE_COMPETENCIA", "DIMENSION_ID_DIMENSION", "EMPRESA_ID_EMPRESA")
VALUES
    (1,  'Creatividad e Innovación',    1, 1),
    (2,  'Enfoque de Negocio',          1, 1),
    (3,  'Identificación Cultural',     1, 1),
    (4,  'Trabajo en Equipo',           1, 1),
    (5,  'Visión Global y Sistemática', 1, 1);

-- Funcionales (Dimensión 2)
INSERT INTO "COMPETENCIA" ("ID_COMPETENCIA", "NOMBRE_COMPETENCIA", "DIMENSION_ID_DIMENSION", "EMPRESA_ID_EMPRESA")
VALUES
    (6,  'Análisis y Solución de Problemas',  2, 1),
    (7,  'Aprendizaje e Innovación',           2, 1),
    (8,  'Comunicación',                       2, 1),
    (9,  'Innovación',                         2, 1),
    (10, 'Liderazgo',                          2, 1),
    (11, 'Liderazgo y Desarrollo de Equipos',  2, 1),
    (12, 'Orientación a la Rentabilidad',      2, 1),
    (13, 'Orientación al Logro',               2, 1),
    (14, 'Planificación Estratégica',          2, 1),
    (15, 'Proactividad',                       2, 1);

-- =========================
-- Cargo
-- =========================
-- Operativos (Nivel 1)
INSERT INTO "CARGO" ("ID_CARGO", "NOMBRE_CARGO", "EMPRESA_ID_EMPRESA", "NIVEL_JERARQUICO_ID_NIVEL_JERARQUICO")
VALUES
    (1, 'Analista',                  1, 1),
    (2, 'Asistente Administrativo',  1, 1);

-- Tácticos (Nivel 2)
INSERT INTO "CARGO" ("ID_CARGO", "NOMBRE_CARGO", "EMPRESA_ID_EMPRESA", "NIVEL_JERARQUICO_ID_NIVEL_JERARQUICO")
VALUES
    (3, 'Jefe de Recursos Humanos',  1, 2),
    (4, 'Coordinador de Proyectos',  1, 2);

-- Estratégicos (Nivel 3)
INSERT INTO "CARGO" ("ID_CARGO", "NOMBRE_CARGO", "EMPRESA_ID_EMPRESA", "NIVEL_JERARQUICO_ID_NIVEL_JERARQUICO")
VALUES
    (5, 'Gerente General',      1, 3),
    (6, 'Gerente de Innovación',1, 3);

-- =========================
-- Textos Evaluación
-- =========================

-- 1. CREATIVIDAD E INNOVACIÓN (Competencia 1)
INSERT INTO "TEXTOS_EVALUACION" ("ID_TEXTOS_EVALUACION", "CODIGO_EXCEL", "TEXTO", "EMPRESA_ID_EMPRESA", "DIMENSION_ID_DIMENSION", "COMPETENCIA_ID_COMPETENCIA", "NIVEL_JERARQUICO_ID_NIVEL_JERARQUICO")
VALUES
    (1, 'CIO1.1', 'Trabaja con mecanismos conocidos y rutinarios.', 1, 1, 1, 1),
    (2, 'CIO1.2', 'Se mueve con facilidad en situaciones conocidas con pautas de acción prefijadas.', 1, 1, 1, 1),
    (3, 'CIO1.3', 'Implementa ideas y soluciones que le permiten resolver situaciones rutinarias y complejas.', 1, 1, 1, 1),
    (4, 'CIT1.1', 'Promueve un estilo de gestión innovador y de vinculación con su entorno, brindando a su equipo herramientas para que trabajen con el mismo enfoque.', 1, 1, 1, 2),
    (5, 'CIT1.2', 'Estructura equipos de alto rendimiento, que suelen tener formatos atípicos utilizando las formas más adecuadas para la consecución de sus objetivos.', 1, 1, 1, 2),
    (6, 'CIT1.3', 'Lidera la implementación de nuevas ideas y soluciones dentro del negocio, es requerido por su aporte de creatividad y visión innovadora, que le permiten resolver situaciones complejas que otros no han podido solucionar.', 1, 1, 1, 2),
    (7, 'CIE1.1', 'Es consultado por pares y subordinados porque se le reconoce por su habilidad de abordar desde nuevos enfoques los problemas y dificultades, pudiendo plantear alternativas impensadas.', 1, 1, 1, 3),
    (8, 'CIE1.2', 'Es intelectualmente curioso, le gusta estar informado y mantenerse en constante aprendizaje para aplicar los conocimientos a la organización.', 1, 1, 1, 3),
    (9, 'CIE1.3', 'Plantea mejoras o soluciones nuevas a problemas sencillos y complejos, garantizando su efectividad y calidad.', 1, 1, 1, 3);

-- 2. ENFOQUE DE NEGOCIO (Competencia 2)
INSERT INTO "TEXTOS_EVALUACION" ("ID_TEXTOS_EVALUACION", "CODIGO_EXCEL", "TEXTO", "EMPRESA_ID_EMPRESA", "DIMENSION_ID_DIMENSION", "COMPETENCIA_ID_COMPETENCIA", "NIVEL_JERARQUICO_ID_NIVEL_JERARQUICO")
VALUES
    (10, 'ENO2.1', 'Comprende las peculiaridades de los servicios.', 1, 1, 2, 1),
    (11, 'ENO2.2', 'Conoce las estrategias, principios y valores corporativos.', 1, 1, 2, 1),
    (12, 'ENO2.3', 'Invierte tiempo adicional para identificar y capturar oportunidades de crecimiento y desarrollo de la empresa.', 1, 1, 2, 1),
    (13, 'ENT2.1', 'Es capaz de establecer relaciones interpersonales en cualquier contexto, promoviendo los servicios a través del networking.', 1, 1, 2, 2),
    (14, 'ENT2.2', 'Es hábil para adaptarse rápidamente y funcionar con eficacia en nuevos contextos laborales.', 1, 1, 2, 2),
    (15, 'ENT2.3', 'Promueve en todas las áreas de trabajo, la capacidad para comprender las peculiaridades de los servicios.', 1, 1, 2, 2),
    (16, 'ENE2.1', 'Desarrolla dentro y fuera de la organización la capacidad de adecuar productos, servicios y procedimientos organizacionales, a fin de amoldarse a nuevos contextos de acuerdo con la estrategia del negocio.', 1, 1, 2, 3),
    (17, 'ENE2.2', 'Es un referente dentro y fuera de la organización por su capacidad de identificar y desarrollar oportunidades de negocio.', 1, 1, 2, 3),
    (18, 'ENE2.3', 'Es reconocido por su expertise, su alto conocimiento cultural y estrategias de relacionamiento.', 1, 1, 2, 3);

-- 6. ANÁLISIS Y SOLUCIÓN DE PROBLEMAS (Competencia 6)
INSERT INTO "TEXTOS_EVALUACION" ("ID_TEXTOS_EVALUACION", "CODIGO_EXCEL", "TEXTO", "EMPRESA_ID_EMPRESA", "DIMENSION_ID_DIMENSION", "COMPETENCIA_ID_COMPETENCIA", "NIVEL_JERARQUICO_ID_NIVEL_JERARQUICO")
VALUES
    (19, 'ASO1.1', 'Resuelve problemas rutinarios de forma efectiva.', 1, 2, 6, 1),
    (20, 'ASO1.2', 'Acude a sus superiores o pares para crear alternativas que le permitan resolver los problemas con mayor grado de dificultad.', 1, 2, 6, 1),
    (21, 'ASO1.3', 'Logra detectar las variables que influyen en el problema de forma oportuna.', 1, 2, 6, 1),
    (22, 'AST1.1', 'Utiliza eficazmente datos históricos y actuales como ayuda para prever tendencias futuras, siendo efectivo en crear contingencias para que no afecten los resultados.', 1, 2, 6, 2),
    (23, 'AST1.2', 'Analiza las relaciones entre las distintas partes y causales de un problema, anticipándose a los obstáculos y creando alternativas.', 1, 2, 6, 2),
    (24, 'AST1.3', 'Aporta soluciones válidas para la situación en tiempo y forma, responsabilizándose de ellas.', 1, 2, 6, 2),
    (25, 'ASE1.1', 'Realiza análisis complejos utilizando hipótesis y diferentes escenarios, logrando rescatar los aspectos más significativos.', 1, 2, 6, 3),
    (26, 'ASE1.2', 'Comprende problemas complejos y los define en torno a principios y estrategias organizacionales.', 1, 2, 6, 3),
    (27, 'ASE1.3', 'Se anticipa a las situaciones, previendo y planteando respuestas adecuadas y rentables antes que se presente la situación.', 1, 2, 6, 3);

-- =========================
-- Código Evaluación
-- =========================
INSERT INTO "CODIGO_EVALUACION" ("ID_CODIGO_EVALUACION", "EMPRESA_ID_EMPRESA", "DIMENSION_ID_DIMENSION", "COMPETENCIA_ID_COMPETENCIA", "NIVEL_JERARQUICO_ID_NIVEL_JERARQUICO", "TEXTOS_EVALUACION_CODIGO_EXCEL", "TEXTOS_EVALUACION_EMPRESA_ID_EMPRESA")
VALUES
    -- Creatividad e Innovación: Operativo
    (1,  1, 1, 1, 1, 'CIO1.1', 1),
    (2,  1, 1, 1, 1, 'CIO1.2', 1),
    (3,  1, 1, 1, 1, 'CIO1.3', 1),
    -- Creatividad e Innovación: Táctico
    (4,  1, 1, 1, 2, 'CIT1.1', 1),
    (5,  1, 1, 1, 2, 'CIT1.2', 1),
    (6,  1, 1, 1, 2, 'CIT1.3', 1),
    -- Creatividad e Innovación: Estratégico
    (7,  1, 1, 1, 3, 'CIE1.1', 1),
    (8,  1, 1, 1, 3, 'CIE1.2', 1),
    (9,  1, 1, 1, 3, 'CIE1.3', 1),
    -- Enfoque de Negocio: Operativo
    (10, 1, 1, 2, 1, 'ENO2.1', 1),
    (11, 1, 1, 2, 1, 'ENO2.2', 1),
    (12, 1, 1, 2, 1, 'ENO2.3', 1),
    -- Enfoque de Negocio: Táctico
    (13, 1, 1, 2, 2, 'ENT2.1', 1),
    (14, 1, 1, 2, 2, 'ENT2.2', 1),
    (15, 1, 1, 2, 2, 'ENT2.3', 1),
    -- Enfoque de Negocio: Estratégico
    (16, 1, 1, 2, 3, 'ENE2.1', 1),
    (17, 1, 1, 2, 3, 'ENE2.2', 1),
    (18, 1, 1, 2, 3, 'ENE2.3', 1),
    -- Análisis y Solución de Problemas: Operativo
    (19, 1, 2, 6, 1, 'ASO1.1', 1),
    (20, 1, 2, 6, 1, 'ASO1.2', 1),
    (21, 1, 2, 6, 1, 'ASO1.3', 1),
    -- Análisis y Solución de Problemas: Táctico
    (22, 1, 2, 6, 2, 'AST1.1', 1),
    (23, 1, 2, 6, 2, 'AST1.2', 1),
    (24, 1, 2, 6, 2, 'AST1.3', 1),
    -- Análisis y Solución de Problemas: Estratégico
    (25, 1, 2, 6, 3, 'ASE1.1', 1),
    (26, 1, 2, 6, 3, 'ASE1.2', 1),
    (27, 1, 2, 6, 3, 'ASE1.3', 1);

-- =========================
-- Trabajador
-- =========================
-- Estratégico (sin jefe)
INSERT INTO "TRABAJADOR" ("ID_TRABAJADOR", "RUT", "ID_JEFE_DIRECTO", "NOMBRE", "APELLIDO_PATERNO", "APELLIDO_MATERNO", "EMAIL", "GENERO", "ES_COORDINADOR", "EMPRESA_ID_EMPRESA", "NIVEL_JERARQUICO_ID_NIVEL_JERARQUICO", "CARGO_ID_CARGO", "DEPARTAMENTO_ID_DEPARTAMENTO")
VALUES
    (1, '10.234.567-1', NULL, 'Roberto',  'Méndez', 'Castro', 'r.mendez@mohala.cl', 'Masculino', FALSE, 1, 3, 5, 1),
    (2, '12.456.789-2', NULL, 'Patricia', 'Lorca',  'Vial',   'p.lorca@mohala.cl',  'Femenino',  TRUE,  1, 3, 6, 1);

-- Táctico (reportan a ID 1 y 2)
INSERT INTO "TRABAJADOR" ("ID_TRABAJADOR", "RUT", "ID_JEFE_DIRECTO", "NOMBRE", "APELLIDO_PATERNO", "APELLIDO_MATERNO", "EMAIL", "GENERO", "ES_COORDINADOR", "EMPRESA_ID_EMPRESA", "NIVEL_JERARQUICO_ID_NIVEL_JERARQUICO", "CARGO_ID_CARGO", "DEPARTAMENTO_ID_DEPARTAMENTO")
VALUES
    (3, '13.567.890-4', 1, 'Mónica', 'Sánchez', 'Paz', 'm.sanchez@mohala.cl', 'Femenino',  FALSE, 1, 2, 4, 3),
    (4, '11.345.678-3', 2, 'Andrés', 'Tapia',   'Ruiz','a.tapia@mohala.cl',   'Masculino', FALSE, 1, 2, 3, 2);

-- Operativo (reportan a ID 3 y 4)
INSERT INTO "TRABAJADOR" ("ID_TRABAJADOR", "RUT", "ID_JEFE_DIRECTO", "NOMBRE", "APELLIDO_PATERNO", "APELLIDO_MATERNO", "EMAIL", "GENERO", "ES_COORDINADOR", "EMPRESA_ID_EMPRESA", "NIVEL_JERARQUICO_ID_NIVEL_JERARQUICO", "CARGO_ID_CARGO", "DEPARTAMENTO_ID_DEPARTAMENTO")
VALUES
    (5, '18.456.789-9', 3, 'Valeria',  'Cáceres','Pinto','v.caceres@mohala.cl','Femenino',  FALSE, 1, 1, 1, 3),
    (6, '19.567.890-0', 4, 'Sebastián','Marín',  'Rojas','s.marin@mohala.cl',  'Masculino', FALSE, 1, 1, 2, 2);

-- =========================
-- Sincronizar secuencias SERIAL
-- =========================
SELECT setval(pg_get_serial_sequence('"EMPRESA"',             'ID_EMPRESA'),             MAX("ID_EMPRESA"))             FROM "EMPRESA";
SELECT setval(pg_get_serial_sequence('"DEPARTAMENTO"',        'ID_DEPARTAMENTO'),        MAX("ID_DEPARTAMENTO"))        FROM "DEPARTAMENTO";
SELECT setval(pg_get_serial_sequence('"NIVEL_JERARQUICO"',    'ID_NIVEL_JERARQUICO'),    MAX("ID_NIVEL_JERARQUICO"))    FROM "NIVEL_JERARQUICO";
SELECT setval(pg_get_serial_sequence('"ESCALA"',              'ID_ESCALA'),              MAX("ID_ESCALA"))              FROM "ESCALA";
SELECT setval(pg_get_serial_sequence('"DIMENSION"',           'ID_DIMENSION'),           MAX("ID_DIMENSION"))           FROM "DIMENSION";
SELECT setval(pg_get_serial_sequence('"COMPETENCIA"',         'ID_COMPETENCIA'),         MAX("ID_COMPETENCIA"))         FROM "COMPETENCIA";
SELECT setval(pg_get_serial_sequence('"CARGO"',               'ID_CARGO'),               MAX("ID_CARGO"))               FROM "CARGO";
SELECT setval(pg_get_serial_sequence('"TEXTOS_EVALUACION"',   'ID_TEXTOS_EVALUACION'),   MAX("ID_TEXTOS_EVALUACION"))   FROM "TEXTOS_EVALUACION";
SELECT setval(pg_get_serial_sequence('"CODIGO_EVALUACION"',   'ID_CODIGO_EVALUACION'),   MAX("ID_CODIGO_EVALUACION"))   FROM "CODIGO_EVALUACION";
SELECT setval(pg_get_serial_sequence('"TRABAJADOR"',          'ID_TRABAJADOR'),          MAX("ID_TRABAJADOR"))          FROM "TRABAJADOR";

SET session_replication_role = 'origin';