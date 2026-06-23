"""
models.py
---------
Definición de todos los modelos del sistema. Mezcla de modelos
managed=False (tablas existentes en PostgreSQL) y managed=True
(tablas gestionadas por Django via migraciones).

Modelos managed=False (tablas creadas con creacion_tablas.sql):

Empresa
    Empresa cliente del sistema. Punto central del que dependen
    todos los demás modelos. __str__ incluye estado activo/inactivo.

Biblioteca
    Documentos PDF almacenados como BinaryField, vinculados a una
    empresa. Usados como contexto para los informes de Gemini.

Departamento, NivelJerarquico, Cargo
    Datos organizacionales de la empresa. Todos vinculados por FK
    a Empresa con DO_NOTHING.

Escala
    Valores de calificación (1-4) con título y descripción por
    empresa. PK es IntegerField (no AutoField).

Dimension, Competencia
    Estructura del cuestionario de evaluación. Competencia tiene
    FK a Dimension y Empresa.

TextosEvaluacion
    Indicadores del cuestionario identificados por codigo_excel.
    unique_together (codigo_excel, empresa). FK a Dimension,
    Competencia y NivelJerarquico.

CodigoEvaluacion
    Denormalización de TextosEvaluacion con FKs explícitas a
    Dimension, Competencia y NivelJerarquico.
    unique_together (empresa, textos_evaluacion_codigo_excel).

Trabajador
    Colaborador de la empresa. FK a Empresa, NivelJerarquico,
    Cargo, Departamento y User (OneToOne nullable).
    FK self-referencial id_jefe_directo con related_name='subordinados'.
    Propiedad es_jefe: True si tiene subordinados.
    Signal post_save: crea User de Django automáticamente con
    contraseña 'Mohala2026' al crear un Trabajador sin user.

Autoevaluacion
    Respuesta del trabajador a un indicador. FK compuesta
    (codigo_excel + empresa) a TextosEvaluacion. FK a Escala.

EvaluacionJefatura
    Respuesta del evaluador sobre un evaluado. Dos FK a Trabajador:
    evaluador (related_name='evaluaciones_como_jefe') y
    trabajador_evaluado (related_name='evaluaciones_recibidas').

ResultadoConsolidado
    Cruce de autoevaluación y evaluación de jefatura por código.
    unique_together (trabajador, codigo_excel, periodo).
    evaluacion_jefatura es nullable para trabajadores sin jefe.

Modelos managed=True (gestionados por Django):

ReporteGlobal
    PDF de reporte global por empresa y período. BinaryField.

PromptGemini
    Prompt e informe generado por Gemini AI. Ordering por
    timestamp descendente. FK a ReporteGlobal y Empresa.

RegistroVersiones
    Historial de versiones del RAT por empresa.

Instrumento
    Catálogo global de instrumentos RAT disponibles.
    nombre_instrumento único.

InstrumentoEmpresa
    Tabla pivote entre Instrumento y Empresa.
    unique_together (instrumento, empresa).
    habilitado controla si está activo para la empresa.

RATPreguntas
    Preguntas RAT vinculadas a InstrumentoEmpresa (no a Empresa
    directamente). choices para base_legitimidad:
    consentimiento, contrato, obligacion_legal, interes_legitimo.
    FK a Trabajador (responsable) y RegistroVersiones (version).

RATRespuestas
    Respuesta de un trabajador a una RATPreguntas.
    related_name='respuestas' en FK a RATPreguntas.
    Timestamps created_at y updated_at automáticos.

RATPlantillaPregunta
    Preguntas base globales de un Instrumento. Al habilitar el
    instrumento para una empresa se clonan a RATPreguntas via señal.
    choices de tipo: texto, sino, escala. Ordering por orden.
"""

from django.db import models
from django.contrib.auth.models import User
import re
from datetime import datetime


def generar_password_empresa(empresa, anio=None):
    """Genera la contraseña inicial/por defecto de un trabajador según
    su empresa, con el formato [PrimeraPalabraDelNombre][AñoDeCreación].
    Usa solo la primera palabra del nombre de la empresa (ignora
    sufijos como SpA, S.A., Ltda., etc.) para mantener la contraseña
    simple. Ej: empresa 'Mohala SpA' -> 'Mohala2026'.

    anio=None usa el año actual (datetime.now().year). Se usa al crear
    un Trabajador (señal automática, panel de gestión de usuarios,
    carga masiva por Excel) y al resetear una clave a su valor
    por defecto."""
    anio = anio or datetime.now().year
    primera_palabra = (empresa.nombre_empresa or '').strip().split(' ')[0]
    nombre_limpio = re.sub(r'[^A-Za-z0-9]', '', primera_palabra) or 'Empresa'
    return f"{nombre_limpio}{anio}"

# =========================
# Tabla Empresa
# =========================
class Empresa(models.Model):
    id_empresa = models.AutoField(primary_key=True)
    nombre_empresa = models.CharField(max_length=100)
    rut_empresa = models.CharField(max_length=20, unique=True)
    empresa_activa = models.BooleanField(default=False)
    registrada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'EMPRESA'

    def __str__(self):
        return f"{self.id_empresa} - {self.nombre_empresa} ({'Activa' if self.empresa_activa else 'Inactiva'})"


# ==========================================================
# Biblioteca
# ==========================================================
class Biblioteca(models.Model):
    id_biblioteca = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    archivo = models.BinaryField(editable=True)
    estado_carga = models.BooleanField(default=False)
    fecha_carga = models.DateTimeField(auto_now_add=True)
    empresa = models.ForeignKey(
        'Empresa',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='EMPRESA_ID_EMPRESA'
    )

    class Meta:
        managed = False
        db_table = 'BIBLIOTECA'

    def __str__(self):
        return self.nombre

# ==========================================================
# Reporte Global
# ==========================================================
class ReporteGlobal(models.Model):
    id_reporte_global = models.AutoField(primary_key=True)
    contenido_pdf = models.BinaryField()
    timestamp = models.DateTimeField(auto_now_add=True)
    total_trabajadores = models.IntegerField(default=0)
    periodo = models.IntegerField(default=2026)
    empresa = models.ForeignKey(
        'Empresa',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='EMPRESA_ID_EMPRESA'
    )

    class Meta:
        managed = False
        db_table = 'REPORTE_GLOBAL'

    def __str__(self):
        return f"Reporte Global {self.id_reporte_global} - Periodo {self.periodo}"

# ==========================================================
#  Prompt Gemini
# ==========================================================
class PromptGemini(models.Model):
    id_prompt = models.AutoField(primary_key=True)
    prompt_texto = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    respuesta_gemini = models.TextField(null=True, blank=True)
    pdf_generado = models.BooleanField(default=False)
    archivo_pdf = models.BinaryField(null=True, blank=True)

    empresa = models.ForeignKey(
        'Empresa',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='EMPRESA_ID_EMPRESA'
    )
    
    reporte_global = models.ForeignKey(
        ReporteGlobal,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='REPORTE_GLOBAL_ID'
    )

    class Meta:
        managed = False
        db_table = 'PROMPT_GEMINI'
        ordering = ['-timestamp']

    def __str__(self):
        return f"Prompt {self.id_prompt} - {self.timestamp.strftime('%d/%m/%Y')}"

# =========================
# Tabla Departamento
# =========================
class Departamento(models.Model):
    id_departamento = models.AutoField(primary_key=True)
    nombre_departamento = models.CharField(max_length=50)
    empresa = models.ForeignKey(
        'Empresa', 
        on_delete=models.DO_NOTHING, 
        db_column='empresa_id_empresa'
    )
    class Meta:
        managed = False
        db_table = 'DEPARTAMENTO'
    
    def __str__(self):
        return f"{self.nombre_departamento} | ID {self.empresa.id_empresa} - {self.empresa.nombre_empresa}"
    
# =========================
# Tabla Nivel Jerarquico
# =========================
class NivelJerarquico(models.Model):
    id_nivel_jerarquico = models.AutoField(primary_key=True)
    nombre_nivel_jerarquico = models.CharField(max_length=50)
    empresa = models.ForeignKey(
        'Empresa', 
        on_delete=models.DO_NOTHING, 
        db_column='empresa_id_empresa'
    )

    class Meta:
        managed = False
        db_table = 'NIVEL_JERARQUICO'

    def __str__(self):
        return f"{self.nombre_nivel_jerarquico} | ID {self.empresa.id_empresa} - {self.empresa.nombre_empresa}"
    
# =========================
# Tabla Escala
# =========================
class Escala(models.Model):
    id_escala = models.IntegerField(primary_key=True)
    valor = models.IntegerField()
    titulo = models.CharField(max_length=100)        
    descripcion = models.CharField(max_length=250)   
    empresa = models.ForeignKey(
        'Empresa', 
        on_delete=models.DO_NOTHING, 
        db_column='empresa_id_empresa'
    )

    class Meta:
        managed = False
        db_table = 'ESCALA'

    def __str__(self):
        return f"{self.valor} - {self.titulo} - {self.descripcion} | ID {self.empresa.id_empresa} - {self.empresa.nombre_empresa}"     

# =========================
# Tabla Dimension
# =========================
class Dimension(models.Model):
    id_dimension = models.AutoField(primary_key=True)
    nombre_dimension = models.CharField(max_length=50)
    empresa = models.ForeignKey(
        'Empresa', 
        on_delete=models.DO_NOTHING, 
        db_column='empresa_id_empresa'
    )

    class Meta:
        managed = False
        db_table = 'DIMENSION'
    
    def __str__(self):
        return f"{self.nombre_dimension} | ID {self.empresa.id_empresa} - {self.empresa.nombre_empresa}"

# =========================
# Tabla Competencia
# =========================
class Competencia(models.Model):
    id_competencia = models.AutoField(primary_key=True)
    nombre_competencia = models.CharField(max_length=50)
    dimension = models.ForeignKey(
        'Dimension', 
        on_delete=models.DO_NOTHING, 
        db_column='dimension_id_dimension'
    )
    empresa = models.ForeignKey(
        'Empresa', 
        on_delete=models.DO_NOTHING, 
        db_column='empresa_id_empresa'
    )

    class Meta:
        managed = False
        db_table = 'COMPETENCIA'
    
    def __str__(self):
        return f"{self.nombre_competencia} | ID {self.empresa.id_empresa} - {self.empresa.nombre_empresa}"

# =========================
# Tabla Cargo
# =========================
class Cargo(models.Model):
    id_cargo = models.AutoField(primary_key=True)
    nombre_cargo = models.CharField(max_length=50)
    empresa = models.ForeignKey(
        'Empresa', 
        on_delete=models.DO_NOTHING, 
        db_column='empresa_id_empresa'
    )
    nivel_jerarquico = models.ForeignKey(
        'NivelJerarquico', 
        on_delete=models.DO_NOTHING, 
        db_column='nivel_jerarquico_id_nivel_jerarquico'
    )

    class Meta:
        managed = False
        db_table = 'CARGO'
    
    def __str__(self):
        return f"{self.nombre_cargo} | ID {self.empresa.id_empresa} - {self.empresa.nombre_empresa}"

# =========================
# Tabla Textos Evaluación
# =========================
class TextosEvaluacion(models.Model):
    id_textos_evaluacion = models.AutoField(primary_key=True)
    codigo_excel = models.CharField(max_length=10)
    texto = models.TextField()
    empresa = models.ForeignKey(
        'Empresa',
        on_delete=models.DO_NOTHING,
        db_column='empresa_id_empresa'
    )
    dimension = models.ForeignKey(
        'Dimension',
        on_delete=models.DO_NOTHING,
        db_column='dimension_id_dimension'
    )
    competencia = models.ForeignKey(
        'Competencia',
        on_delete=models.DO_NOTHING,
        db_column='competencia_id_competencia'
    )
    nivel_jerarquico = models.ForeignKey(
        'NivelJerarquico',
        on_delete=models.DO_NOTHING,
        db_column='nivel_jerarquico_id_nivel_jerarquico'
    )

    class Meta:
        managed = False
        db_table = 'TEXTOS_EVALUACION'
        unique_together = (('codigo_excel', 'empresa'),)

# =========================
# Tabla Código Evaluación
# =========================
class CodigoEvaluacion(models.Model):
    id_codigo_evaluacion = models.AutoField(primary_key=True)
    empresa = models.ForeignKey(
        'Empresa',
        on_delete=models.DO_NOTHING,
        db_column='empresa_id_empresa'
    )
    dimension = models.ForeignKey(
        'Dimension',
        on_delete=models.DO_NOTHING,
        db_column='dimension_id_dimension'
    )
    competencia = models.ForeignKey(
        'Competencia',
        on_delete=models.DO_NOTHING,
        db_column='competencia_id_competencia'
    )
    nivel_jerarquico = models.ForeignKey(
        'NivelJerarquico',
        on_delete=models.DO_NOTHING,
        db_column='nivel_jerarquico_id_nivel_jerarquico'
    )
    textos_evaluacion_codigo_excel = models.CharField(max_length=10)
    textos_evaluacion_empresa = models.ForeignKey(
        'Empresa',
        on_delete=models.DO_NOTHING,
        db_column='textos_evaluacion_empresa_id_empresa',
        related_name='codigos_evaluacion_textos'
    )

    class Meta:
        managed = False
        db_table = 'CODIGO_EVALUACION'
        unique_together = (('empresa', 'textos_evaluacion_codigo_excel'),) 

# =========================
# Tabla Trabajador
# =========================
class Trabajador(models.Model):
    id_trabajador = models.AutoField(primary_key=True)
    rut = models.CharField(max_length=20, unique=True)
    id_jefe_directo = models.ForeignKey(
        'self', 
        on_delete=models.DO_NOTHING, 
        null=True, 
        blank=True, 
        related_name='subordinados',
        db_column='id_jefe_directo'
    )
    nombre = models.CharField(max_length=40)
    apellido_paterno = models.CharField(max_length=40)
    apellido_materno = models.CharField(max_length=40)
    email = models.CharField(max_length=80)
    genero = models.CharField(max_length=10)
    es_coordinador = models.BooleanField(default=False, db_column='es_coordinador')
    
    empresa = models.ForeignKey(
        'Empresa', 
        on_delete=models.DO_NOTHING, 
        db_column='empresa_id_empresa'
    )
    nivel_jerarquico = models.ForeignKey(
        'NivelJerarquico', 
        on_delete=models.DO_NOTHING, 
        db_column='nivel_jerarquico_id_nivel_jerarquico'
    )
    cargo = models.ForeignKey(
        'Cargo', 
        on_delete=models.DO_NOTHING, 
        db_column='cargo_id_cargo'
    )
    departamento = models.ForeignKey(
        'Departamento', 
        on_delete=models.DO_NOTHING, 
        db_column='departamento_id_departamento'
    )
    
    user = models.OneToOneField(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        db_column='user_id'
    )

    class Meta:
        managed = False
        db_table = 'TRABAJADOR'

    @property
    def es_jefe(self):
        return self.subordinados.exists()
    
    def __str__(self):
        return f"{self.nombre} {self.apellido_paterno} {self.apellido_materno}"

# =========================
# Tabla Autoevaluación
# =========================
class Autoevaluacion(models.Model):
    id_autoevaluacion = models.AutoField(primary_key=True)
    puntaje = models.IntegerField()
    fecha_evaluacion = models.DateField()
    momento_evaluacion = models.DateTimeField(auto_now_add=True)
    estado_finalizacion = models.BooleanField(default=False)
    comentario = models.TextField(null=True, blank=True)
    
    trabajador = models.ForeignKey(
        'Trabajador', 
        on_delete=models.DO_NOTHING, 
        db_column='trabajador_id_trabajador'
    )
    
    textos_evaluacion_codigo_excel = models.CharField(max_length=10)
    textos_evaluacion_empresa = models.ForeignKey(
        'Empresa',
        on_delete=models.DO_NOTHING,
        db_column='textos_evaluacion_empresa_id_empresa',
        related_name='autoevaluaciones_textos'
    )
    
    escala = models.ForeignKey(
        'Escala', 
        on_delete=models.DO_NOTHING, 
        db_column='escala_id_escala'
    )

    class Meta:
        managed = False
        db_table = 'AUTOEVALUACION'

    def __str__(self):
        return f"Autoevaluación {self.id_autoevaluacion}"


# =========================
# Tabla Evaluación Jefatura
# =========================
class EvaluacionJefatura(models.Model):
    id_evaluacion_jefatura = models.AutoField(primary_key=True)
    puntaje = models.IntegerField()
    
    evaluador = models.ForeignKey(
        'Trabajador', 
        on_delete=models.DO_NOTHING, 
        db_column='evaluador_id_trabajador', 
        related_name='evaluaciones_como_jefe'
    )
    
    fecha_evaluacion = models.DateField()
    momento_evaluacion = models.DateTimeField(auto_now_add=True)
    estado_finalizacion = models.BooleanField(default=False)
    comentario = models.TextField(null=True, blank=True)
    
    trabajador_evaluado = models.ForeignKey(
        'Trabajador', 
        on_delete=models.DO_NOTHING, 
        db_column='trabajador_id_trabajador', 
        related_name='evaluaciones_recibidas'
    )
    
    # FK compuesta a TEXTOS_EVALUACION
    textos_evaluacion_codigo_excel = models.CharField(max_length=10)
    textos_evaluacion_empresa = models.ForeignKey(
        'Empresa',
        on_delete=models.DO_NOTHING,
        db_column='textos_evaluacion_empresa_id_empresa',
        related_name='evaluaciones_jefatura_textos'
    )
    
    escala = models.ForeignKey(
        'Escala', 
        on_delete=models.DO_NOTHING, 
        db_column='escala_id_escala'
    )

    class Meta:
        managed = False
        db_table = 'EVALUACION_JEFATURA'

    def __str__(self):
        return f"Evaluación {self.id_evaluacion_jefatura}"


# =========================
# Tabla Resultado Consolidado
# =========================
class ResultadoConsolidado(models.Model):
    id_resultado_consolidado = models.AutoField(primary_key=True)
    puntaje_autoev = models.IntegerField()
    puntaje_jefe = models.IntegerField()
    diferencia = models.IntegerField()
    periodo = models.IntegerField()
    
    trabajador = models.ForeignKey(
        'Trabajador', 
        on_delete=models.DO_NOTHING, 
        db_column='trabajador_id_trabajador'
    )
    autoevaluacion = models.ForeignKey(
        'Autoevaluacion',
        on_delete=models.DO_NOTHING,
        db_column='autoevaluacion_id_autoevaluacion'
    )
    evaluacion_jefatura = models.ForeignKey(
        'EvaluacionJefatura',
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        db_column='evaluacion_jefatura_id_evaluacion_jefatura'
    )
    textos_evaluacion_codigo_excel = models.CharField(max_length=10)
    textos_evaluacion_empresa = models.ForeignKey(
        'Empresa',
        on_delete=models.DO_NOTHING,
        db_column='textos_evaluacion_empresa_id_empresa',
        related_name='resultados_consolidados_textos'
    )

    class Meta:
        managed = False
        db_table = 'RESULTADO_CONSOLIDADO'
        unique_together = (('trabajador', 'textos_evaluacion_codigo_excel', 'periodo'),)

    def __str__(self):
        return f"Resultado {self.id_resultado_consolidado}"

# =========================
# Tabla Registro Versiones
# =========================
class RegistroVersiones(models.Model):
    id_registro_version = models.AutoField(primary_key=True)
    version = models.CharField(max_length=20)
    fecha_modificacion = models.DateField(auto_now_add=True)
    motivo_modificacion = models.TextField()

    empresa = models.ForeignKey(
        'Empresa',
        on_delete=models.DO_NOTHING,
        db_column='empresa_id_empresa'
    )

    class Meta:
        managed = True
        db_table = 'REGISTRO_VERSIONES'

    def __str__(self):
        return f"v{self.version} - {self.fecha_modificacion}"

# =========================
# Tabla Instrumento (catálogo global)
# =========================
class Instrumento(models.Model):
    TIPO_CHOICES = [
        ('rat', 'Registro de Actividad de Tratamiento (RAT)'),
        ('evaluacion', 'Evaluación de Desempeño'),
    ]

    id_instrumento = models.AutoField(primary_key=True)
    nombre_instrumento = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='rat',
    )

    class Meta:
        managed = True
        db_table = 'INSTRUMENTO'

    def __str__(self):
        return self.nombre_instrumento


# =========================
# Tabla Instrumento_Empresa
# =========================
class InstrumentoEmpresa(models.Model):
    id_instrumento_empresa = models.AutoField(primary_key=True)
    instrumento = models.ForeignKey(
        'Instrumento',
        on_delete=models.DO_NOTHING,
        db_column='instrumento_id'
    )
    empresa = models.ForeignKey(
        'Empresa',
        on_delete=models.DO_NOTHING,
        db_column='empresa_id_empresa'
    )
    habilitado = models.BooleanField(default=True)
    fecha_habilitacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'INSTRUMENTO_EMPRESA'
        unique_together = (('instrumento', 'empresa'),)

    def __str__(self):
        return f"{self.instrumento} → {self.empresa}"
    
# =========================
# Tabla RAT Preguntas  ← FK cambia de Instrumento a InstrumentoEmpresa
# =========================
class RATPreguntas(models.Model):
    BASE_LEGITIMIDAD_CHOICES = [
        ('consentimiento', 'Consentimiento'),
        ('contrato', 'Contrato'),
        ('obligacion_legal', 'Obligación legal'),
        ('interes_legitimo', 'Interés legítimo'),
    ]
 
    id_rat_pregunta = models.AutoField(primary_key=True)
    orden = models.PositiveSmallIntegerField(default=0)
    actividad_tratamiento = models.CharField(max_length=255)
    CATEGORIAS_CHOICES = [
        ('contactabilidad', 'Datos de contactabilidad de personas'),
        ('bancarios', 'Datos bancarios o finanzas personales'),
        ('historia_clinica', 'Datos de historia clínica de personas'),
    ]
    categorias_datos = models.CharField(max_length=50, choices=CATEGORIAS_CHOICES)
    descripcion_titulares = models.TextField(blank=True, default='')
    finalidad_tratamiento = models.TextField(blank=True, default='')
    base_legitimidad = models.CharField(max_length=200, blank=True, default='')  # múltiple, separado por comas
    periodo_conservacion = models.PositiveIntegerField(default=0)
    UNIDAD_TIEMPO_CHOICES = [
        ('dias', 'Días'),
        ('meses', 'Meses'),
        ('anos', 'Años'),
    ]
    periodo_unidad = models.CharField(max_length=10, choices=UNIDAD_TIEMPO_CHOICES, default='meses')
    fuente_datos = models.CharField(max_length=255, blank=True, default='')
    destinatarios = models.ForeignKey(
        'Trabajador',
        on_delete=models.DO_NOTHING,
        db_column='trabajador_id_destinatario',
        related_name='preguntas_rat_destinatario',
        null=True,
        blank=True,
    )
    TIPO_PREGUNTA_CHOICES = [
        ('texto', 'Texto libre'),
        ('sino', 'Sí / No'),
        ('escala', 'Escala 1-5'),
        ('select_categorias', 'Selector de categorías'),
        ('periodo', 'Período (número + unidad)'),
        ('listado_usuarios', 'Listado de usuarios'),
        ('select_actividad', 'Selector de actividad de tratamiento'),
        ('select_formato', 'Selector de formato de archivo'),
        ('select_base_legitimidad', 'Selector de base de legitimidad (múltiple)'),
    ]
    tipo = models.CharField(
        max_length=30,
        choices=TIPO_PREGUNTA_CHOICES,
        default='texto',
    )
 
    # ← CAMBIO: antes Instrumento, ahora InstrumentoEmpresa
    instrumento_empresa = models.ForeignKey(
        'InstrumentoEmpresa',
        on_delete=models.CASCADE,
        db_column='instrumento_empresa_id',
        related_name='preguntas',
    )
    responsable = models.ForeignKey(
        'Trabajador',
        on_delete=models.DO_NOTHING,
        db_column='trabajador_id_responsable',
        related_name='preguntas_rat_responsable',
    )
    version = models.ForeignKey(
        'RegistroVersiones',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='registro_versiones_id',
    )
 
    class Meta:
        managed = True
        db_table = 'RAT_PREGUNTAS'
        ordering = ['orden', 'id_rat_pregunta']
 
    def __str__(self):
        return self.actividad_tratamiento
 
 
# =========================
# Tabla RAT Respuestas  (sin cambios estructurales)
# =========================
class RATRespuestas(models.Model):
    id_rat_respuesta = models.AutoField(primary_key=True)
    respuesta = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
 
    pregunta = models.ForeignKey(
        'RATPreguntas',
        on_delete=models.CASCADE,
        db_column='rat_preguntas_id_rat_pregunta',
        related_name='respuestas',
    )
    trabajador = models.ForeignKey(
        'Trabajador',
        on_delete=models.DO_NOTHING,
        db_column='trabajador_id_trabajador',
    )
 
    class Meta:
        managed = True
        db_table = 'RAT_RESPUESTAS'
 
    def __str__(self):
        return f"{self.trabajador} → {self.pregunta}"
 
 
# =========================
# Plantilla base de preguntas RAT (NUEVA)
# =========================
class RATPlantillaPregunta(models.Model):
    """Preguntas base globales de un instrumento RAT.
    Al habilitar el instrumento para una empresa se clonan a RATPreguntas."""
 
    TIPO_CHOICES = [
        ('texto', 'Texto libre'),
        ('sino', 'Sí / No'),
        ('escala', 'Escala 1-5'),
        ('select_categorias', 'Selector de categorías'),
        ('periodo', 'Período (número + unidad)'),
        ('listado_usuarios', 'Listado de usuarios'),
        ('select_actividad', 'Selector de actividad de tratamiento'),
        ('select_formato', 'Selector de formato de archivo'),
        ('select_base_legitimidad', 'Selector de base de legitimidad (múltiple)'),
    ]
 
    id_plantilla = models.AutoField(primary_key=True)
    instrumento = models.ForeignKey(
        'Instrumento',
        on_delete=models.CASCADE,
        db_column='instrumento_id',
        related_name='plantilla_preguntas',
    )
    orden = models.PositiveSmallIntegerField(default=0)
    enunciado = models.TextField()
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES, default='texto')
 
    class Meta:
        managed = True
        db_table = 'RAT_PLANTILLA_PREGUNTA'
        ordering = ['orden']
 
    def __str__(self):
        return f"[{self.instrumento}] {self.enunciado[:60]}"