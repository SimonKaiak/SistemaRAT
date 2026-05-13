from django.core.management.base import BaseCommand
from django.db import connection

# Las tablas se crean SIN la FK a auth_user en TRABAJADOR
# porque auth_user la crea el migrate que corre antes.
# Las migraciones de Django agregan esa FK posteriormente.

SQL = """
CREATE TABLE IF NOT EXISTS "EMPRESA" (
    id_empresa SERIAL PRIMARY KEY,
    nombre_empresa VARCHAR(100) NOT NULL,
    rut_empresa VARCHAR(20) NOT NULL UNIQUE,
    empresa_activa BOOLEAN NOT NULL DEFAULT FALSE,
    registrada_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS "BIBLIOTECA" (
    id_biblioteca SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    archivo BYTEA NOT NULL,
    estado_carga BOOLEAN NOT NULL DEFAULT FALSE,
    fecha_carga TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "EMPRESA_ID_EMPRESA" INT NULL REFERENCES "EMPRESA"(id_empresa)
);

CREATE TABLE IF NOT EXISTS "REPORTE_GLOBAL" (
    id_reporte_global SERIAL PRIMARY KEY,
    contenido_pdf BYTEA NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_trabajadores INT NOT NULL DEFAULT 0,
    periodo INT NOT NULL DEFAULT 2026,
    "EMPRESA_ID_EMPRESA" INT NULL REFERENCES "EMPRESA"(id_empresa)
);

CREATE TABLE IF NOT EXISTS "PROMPT_GEMINI" (
    id_prompt SERIAL PRIMARY KEY,
    prompt_texto TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    respuesta_gemini TEXT NULL,
    pdf_generado SMALLINT NOT NULL DEFAULT 0,
    archivo_pdf BYTEA NULL,
    reporte_global_id INT NULL REFERENCES "REPORTE_GLOBAL"(id_reporte_global) ON DELETE SET NULL,
    "EMPRESA_ID_EMPRESA" INT NULL REFERENCES "EMPRESA"(id_empresa)
);

CREATE TABLE IF NOT EXISTS "DEPARTAMENTO" (
    id_departamento SERIAL PRIMARY KEY,
    nombre_departamento VARCHAR(50) NOT NULL,
    "EMPRESA_ID_EMPRESA" INT NOT NULL REFERENCES "EMPRESA"(id_empresa)
);

CREATE TABLE IF NOT EXISTS "NIVEL_JERARQUICO" (
    id_nivel_jerarquico SERIAL PRIMARY KEY,
    nombre_nivel_jerarquico VARCHAR(50) NOT NULL,
    "EMPRESA_ID_EMPRESA" INT NOT NULL REFERENCES "EMPRESA"(id_empresa)
);

CREATE TABLE IF NOT EXISTS "ESCALA" (
    id_escala SERIAL PRIMARY KEY,
    valor INT NOT NULL,
    titulo VARCHAR(100) NOT NULL,
    descripcion VARCHAR(250) NOT NULL,
    "EMPRESA_ID_EMPRESA" INT NOT NULL REFERENCES "EMPRESA"(id_empresa)
);

CREATE TABLE IF NOT EXISTS "DIMENSION" (
    id_dimension SERIAL PRIMARY KEY,
    nombre_dimension VARCHAR(50) NOT NULL,
    "EMPRESA_ID_EMPRESA" INT NOT NULL REFERENCES "EMPRESA"(id_empresa)
);

CREATE TABLE IF NOT EXISTS "COMPETENCIA" (
    id_competencia SERIAL PRIMARY KEY,
    nombre_competencia VARCHAR(50) NOT NULL,
    dimension_id_dimension INT NOT NULL REFERENCES "DIMENSION"(id_dimension),
    "EMPRESA_ID_EMPRESA" INT NOT NULL REFERENCES "EMPRESA"(id_empresa)
);

CREATE TABLE IF NOT EXISTS "CARGO" (
    id_cargo SERIAL PRIMARY KEY,
    nombre_cargo VARCHAR(50) NOT NULL,
    "EMPRESA_ID_EMPRESA" INT NOT NULL REFERENCES "EMPRESA"(id_empresa),
    nivel_jerarquico_id_nivel_jerarquico INT NOT NULL REFERENCES "NIVEL_JERARQUICO"(id_nivel_jerarquico)
);

CREATE TABLE IF NOT EXISTS "TEXTOS_EVALUACION" (
    id_textos_evaluacion SERIAL PRIMARY KEY,
    codigo_excel VARCHAR(10) NOT NULL,
    texto TEXT NOT NULL,
    "EMPRESA_ID_EMPRESA" INT NOT NULL REFERENCES "EMPRESA"(id_empresa),
    dimension_id_dimension INT NOT NULL REFERENCES "DIMENSION"(id_dimension),
    competencia_id_competencia INT NOT NULL REFERENCES "COMPETENCIA"(id_competencia),
    nivel_jerarquico_id_nivel_jerarquico INT NOT NULL REFERENCES "NIVEL_JERARQUICO"(id_nivel_jerarquico),
    UNIQUE (codigo_excel, "EMPRESA_ID_EMPRESA")
);

CREATE TABLE IF NOT EXISTS "CODIGO_EVALUACION" (
    id_codigo_evaluacion SERIAL PRIMARY KEY,
    "EMPRESA_ID_EMPRESA" INT NOT NULL REFERENCES "EMPRESA"(id_empresa),
    dimension_id_dimension INT NOT NULL REFERENCES "DIMENSION"(id_dimension),
    competencia_id_competencia INT NOT NULL REFERENCES "COMPETENCIA"(id_competencia),
    nivel_jerarquico_id_nivel_jerarquico INT NOT NULL REFERENCES "NIVEL_JERARQUICO"(id_nivel_jerarquico),
    textos_evaluacion_codigo_excel VARCHAR(10) NOT NULL,
    textos_evaluacion_empresa_id_empresa INT NOT NULL,
    UNIQUE ("EMPRESA_ID_EMPRESA", textos_evaluacion_codigo_excel),
    FOREIGN KEY (textos_evaluacion_codigo_excel, textos_evaluacion_empresa_id_empresa)
        REFERENCES "TEXTOS_EVALUACION"(codigo_excel, "EMPRESA_ID_EMPRESA")
);

CREATE TABLE IF NOT EXISTS "TRABAJADOR" (
    id_trabajador SERIAL PRIMARY KEY,
    rut VARCHAR(20) NOT NULL UNIQUE,
    id_jefe_directo INT NULL REFERENCES "TRABAJADOR"(id_trabajador),
    nombre VARCHAR(40) NOT NULL,
    apellido_paterno VARCHAR(40) NOT NULL,
    apellido_materno VARCHAR(40) NOT NULL,
    email VARCHAR(80) NOT NULL,
    genero VARCHAR(10) NOT NULL,
    es_coordinador BOOLEAN NOT NULL,
    "EMPRESA_ID_EMPRESA" INT NOT NULL REFERENCES "EMPRESA"(id_empresa),
    nivel_jerarquico_id_nivel_jerarquico INT NOT NULL REFERENCES "NIVEL_JERARQUICO"(id_nivel_jerarquico),
    cargo_id_cargo INT NOT NULL REFERENCES "CARGO"(id_cargo),
    departamento_id_departamento INT NOT NULL REFERENCES "DEPARTAMENTO"(id_departamento),
    user_id INT UNIQUE NULL REFERENCES auth_user(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS "AUTOEVALUACION" (
    id_autoevaluacion SERIAL PRIMARY KEY,
    puntaje INT NOT NULL,
    fecha_evaluacion DATE NOT NULL,
    momento_evaluacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    estado_finalizacion BOOLEAN NOT NULL DEFAULT FALSE,
    comentario TEXT NULL,
    trabajador_id_trabajador INT NOT NULL REFERENCES "TRABAJADOR"(id_trabajador),
    textos_evaluacion_codigo_excel VARCHAR(10) NOT NULL,
    textos_evaluacion_empresa_id_empresa INT NOT NULL,
    escala_id_escala INT NOT NULL REFERENCES "ESCALA"(id_escala),
    FOREIGN KEY (textos_evaluacion_codigo_excel, textos_evaluacion_empresa_id_empresa)
        REFERENCES "TEXTOS_EVALUACION"(codigo_excel, "EMPRESA_ID_EMPRESA")
);

CREATE TABLE IF NOT EXISTS "EVALUACION_JEFATURA" (
    id_evaluacion_jefatura SERIAL PRIMARY KEY,
    puntaje INT NOT NULL,
    evaluador_id_trabajador INT NOT NULL REFERENCES "TRABAJADOR"(id_trabajador),
    fecha_evaluacion DATE NOT NULL,
    momento_evaluacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    estado_finalizacion BOOLEAN NOT NULL DEFAULT FALSE,
    comentario TEXT NULL,
    trabajador_id_trabajador INT NOT NULL REFERENCES "TRABAJADOR"(id_trabajador),
    textos_evaluacion_codigo_excel VARCHAR(10) NOT NULL,
    textos_evaluacion_empresa_id_empresa INT NOT NULL,
    escala_id_escala INT NOT NULL REFERENCES "ESCALA"(id_escala),
    FOREIGN KEY (textos_evaluacion_codigo_excel, textos_evaluacion_empresa_id_empresa)
        REFERENCES "TEXTOS_EVALUACION"(codigo_excel, "EMPRESA_ID_EMPRESA")
);

CREATE TABLE IF NOT EXISTS "RESULTADO_CONSOLIDADO" (
    id_resultado_consolidado SERIAL PRIMARY KEY,
    puntaje_autoev INT NOT NULL,
    puntaje_jefe INT NOT NULL,
    diferencia INT NOT NULL,
    periodo INT NOT NULL,
    trabajador_id_trabajador INT NOT NULL REFERENCES "TRABAJADOR"(id_trabajador),
    autoevaluacion_id_autoevaluacion INT NOT NULL REFERENCES "AUTOEVALUACION"(id_autoevaluacion),
    evaluacion_jefatura_id_evaluacion_jefatura INT NULL REFERENCES "EVALUACION_JEFATURA"(id_evaluacion_jefatura),
    textos_evaluacion_codigo_excel VARCHAR(10) NOT NULL,
    textos_evaluacion_empresa_id_empresa INT NOT NULL,
    UNIQUE (trabajador_id_trabajador, textos_evaluacion_codigo_excel, periodo),
    FOREIGN KEY (textos_evaluacion_codigo_excel, textos_evaluacion_empresa_id_empresa)
        REFERENCES "TEXTOS_EVALUACION"(codigo_excel, "EMPRESA_ID_EMPRESA")
);
"""


class Command(BaseCommand):
    help = 'Crea las tablas del sistema en PostgreSQL si no existen (seguro para re-deployar)'

    def handle(self, *args, **kwargs):
        self.stdout.write('🔧 Creando tablas del sistema...')
        try:
            with connection.cursor() as cursor:
                cursor.execute(SQL)
            self.stdout.write(self.style.SUCCESS('✅ Tablas creadas/verificadas correctamente.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error al crear tablas: {e}'))
            raise