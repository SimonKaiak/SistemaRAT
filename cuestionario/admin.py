from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    Dimension, Departamento, NivelJerarquico, Cargo, Trabajador, 
    Competencia, TextosEvaluacion, Autoevaluacion, 
    EvaluacionJefatura, ResultadoConsolidado, Escala,
    PromptGemini, ReporteGlobal,
    Biblioteca, Empresa, CodigoEvaluacion,
    RATPreguntas, RATRespuestas, RegistroVersiones
)
from django.utils.html import format_html
from django import forms

# --- Configuración Estética ---
admin.site.site_header = "Administración Sistema Mohala"
admin.site.index_title = "Panel de Control Evaluación 2026"

admin.site.unregister(User)

@admin.register(User)
class MyUserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'get_rut', 'first_name', 'get_paterno', 'get_materno', 'is_staff')
    
    @admin.display(description='RUT')
    def get_rut(self, obj):
        return obj.trabajador.rut if hasattr(obj, 'trabajador') else "---"

    @admin.display(description='A. Paterno')
    def get_paterno(self, obj):
        return obj.trabajador.apellido_paterno if hasattr(obj, 'trabajador') else "---"

    @admin.display(description='A. Materno')
    def get_materno(self, obj):
        return obj.trabajador.apellido_materno if hasattr(obj, 'trabajador') else "---"

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('id_empresa', 'nombre_empresa', 'rut_empresa', 'empresa_activa', 'registrada_en')
    list_filter = ('empresa_activa',)
    search_fields = ('nombre_empresa', 'rut_empresa')

@admin.register(Escala)
class EscalaAdmin(admin.ModelAdmin):
    list_display = ('id_escala', 'descripcion', 'empresa')
    ordering = ('id_escala',)

@admin.register(Trabajador)
class TrabajadorAdmin(admin.ModelAdmin):
    list_display = ('id_trabajador', 'nombre', 'apellido_paterno', 'apellido_materno', 'rut', 'email', 'nivel_jerarquico', 'cargo', 'departamento', 'id_jefe_directo')
    list_filter = ('nivel_jerarquico', 'departamento', 'cargo')
    search_fields = ('nombre', 'apellido_paterno', 'rut', 'email')
    ordering = ('apellido_paterno', 'nombre')

@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    list_display = ('nombre_cargo', 'nivel_jerarquico', 'empresa')
    list_filter = ('nivel_jerarquico', 'empresa')

@admin.register(Competencia)
class CompetenciaAdmin(admin.ModelAdmin):
    list_display = ('nombre_competencia', 'dimension', 'empresa')
    list_filter = ('dimension', 'empresa')

@admin.register(CodigoEvaluacion)
class CodigoEvaluacionAdmin(admin.ModelAdmin):
    list_display = ('id_codigo_evaluacion', 'textos_evaluacion_codigo_excel', 'competencia', 'dimension', 'nivel_jerarquico', 'empresa')
    list_filter = ('dimension', 'competencia', 'nivel_jerarquico', 'empresa')
    search_fields = ('textos_evaluacion_codigo_excel',)

@admin.register(TextosEvaluacion)
class TextosEvaluacionAdmin(admin.ModelAdmin):
    list_display = ('codigo_excel', 'empresa', 'get_texto_corto')
    list_filter = ('empresa',)
    search_fields = ('codigo_excel', 'texto')
    ordering = ('id_textos_evaluacion',)

    @admin.display(description='Pregunta')
    def get_texto_corto(self, obj):
        return obj.texto

@admin.register(Autoevaluacion)
class AutoevaluacionAdmin(admin.ModelAdmin):
    list_display = ('trabajador', 'textos_evaluacion_codigo_excel', 'escala', 'estado_finalizacion', 'fecha_evaluacion')
    list_filter = ('estado_finalizacion', 'fecha_evaluacion', 'escala')
    search_fields = ('trabajador__nombre', 'trabajador__apellido_paterno', 'textos_evaluacion_codigo_excel')
    ordering = ('id_autoevaluacion',)

@admin.register(EvaluacionJefatura)
class EvaluacionJefaturaAdmin(admin.ModelAdmin):
    list_display = ('evaluador', 'trabajador_evaluado', 'textos_evaluacion_codigo_excel', 'escala', 'estado_finalizacion')
    list_filter = ('estado_finalizacion', 'evaluador', 'trabajador_evaluado', 'escala')
    search_fields = ('trabajador_evaluado__nombre', 'trabajador_evaluado__apellido_paterno', 'textos_evaluacion_codigo_excel')
    ordering = ('id_evaluacion_jefatura',)

@admin.register(ResultadoConsolidado)
class ResultadoConsolidadoAdmin(admin.ModelAdmin):
    list_display = ('trabajador', 'textos_evaluacion_codigo_excel', 'puntaje_jefe', 'puntaje_autoev', 'diferencia', 'periodo')
    list_filter = ('periodo', 'trabajador')
    readonly_fields = ('diferencia',)
    ordering = ('id_resultado_consolidado',)

@admin.register(PromptGemini)
class PromptGeminiAdmin(admin.ModelAdmin):
    list_display = ['id_prompt', 'prompt_texto', 'timestamp', 'pdf_generado', 'ver_pdf_link']
    list_filter = ['pdf_generado', 'timestamp']
    search_fields = ['prompt_texto', 'respuesta_gemini']
    readonly_fields = ['timestamp', 'ver_pdf_link']
    exclude = ['archivo_pdf']
    
    def ver_pdf_link(self, obj):
        if obj.archivo_pdf:
            return format_html('<a href="/gemini/ver-informe/{}/" target="_blank">📄 Ver PDF</a>', obj.id_prompt)
        return "Sin PDF"
    ver_pdf_link.short_description = 'PDF'
    
@admin.register(ReporteGlobal)
class ReporteGlobalAdmin(admin.ModelAdmin):
    list_display = ('id_reporte_global', 'periodo', 'total_trabajadores', 'timestamp', 'get_prompt_corto', 'ver_pdf_link')
    list_filter = ('periodo', 'timestamp')
    search_fields = ('id_reporte_global', 'periodo')
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp', 'ver_pdf_link')
    exclude = ['contenido_pdf']

    @admin.display(description='Reporte')
    def get_prompt_corto(self, obj):
        return f"ID: {obj.id_reporte_global} | Período: {obj.periodo}"
    
    def ver_pdf_link(self, obj):
        if obj.contenido_pdf:
            return format_html('<a href="/seguimiento/ver-reporte-global/{}/" target="_blank">📄 Ver PDF Global</a>', obj.id_reporte_global)
        return "Sin PDF"
    ver_pdf_link.short_description = 'PDF Global'


class BibliotecaForm(forms.ModelForm):
    archivo = forms.FileField(label='Archivo PDF')

    class Meta:
        model = Biblioteca
        fields = ['nombre', 'archivo']

    def save(self, commit=True):
        instance = super().save(commit=False)
        try:
            instance.archivo = self.cleaned_data['archivo'].read()
            instance.estado_carga = True
        except Exception:
            instance.estado_carga = False
        if commit:
            instance.save()
        return instance

@admin.register(Biblioteca)
class BibliotecaAdmin(admin.ModelAdmin):
    form = BibliotecaForm
    list_display = ['id_biblioteca', 'nombre', 'estado_carga', 'fecha_carga', 'ver_pdf_link']
    readonly_fields = ['estado_carga', 'fecha_carga', 'ver_pdf_link']

    def ver_pdf_link(self, obj):
        if obj.archivo:
            return format_html('<a href="/biblioteca/ver-archivo/{}/" target="_blank">📄 Ver PDF</a>', obj.id_biblioteca)
        return "Sin archivo"
    ver_pdf_link.short_description = 'Archivo'

# Registros simples
admin.site.register(Dimension)
admin.site.register(Departamento)
admin.site.register(NivelJerarquico)
# --- RAT ---
admin.site.register(RATPreguntas)
admin.site.register(RATRespuestas)
admin.site.register(RegistroVersiones)