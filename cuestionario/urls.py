from django.urls import path
from django.contrib.auth.views import LogoutView
from . import logica as views
from .logica import validador_login, seguimiento, detalle_seguimiento, reporte_pdf, reporte_excel, gemini_admin, reporte_global, manejo_archivos, edicion_cuestionario, poblador

urlpatterns = [
    path('login/', validador_login.login_view, name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('', views.index, name='index'),
    
    path('seguimiento/', seguimiento.panel_seguimiento, name='seguimiento_admin'),
    
    path('seguimiento/detalle/<int:trabajador_id>/', 
         detalle_seguimiento.detalle_seguimiento, 
         name='detalle_seguimiento'),
    
    path('seguimiento/detalle/<int:trabajador_id>/pdf/', 
         reporte_pdf.generar_pdf_detalle, 
         name='generar_pdf_detalle'),
    
    path('seguimiento/detalle/<int:trabajador_id>/excel/', 
         reporte_excel.generar_excel_detalle, 
         name='generar_excel_detalle'),
     
    path('seguimiento/reporte-global/', 
         reporte_global.generar_reporte_global_pdf, 
         name='generar_reporte_global_pdf'),
    
    path('seguimiento/ver-reporte-global/<int:reporte_id>/', 
         reporte_global.ver_reporte_global_pdf, 
         name='ver_reporte_global_pdf'),

    path('biblioteca/ver-archivo/<int:biblioteca_id>/', 
         manejo_archivos.ver_archivo_biblioteca, 
         name='ver_archivo_biblioteca'),
    
    # RUTAS GEMINI
    path('gemini/', gemini_admin.panel_gemini, name='panel_gemini'),
    path('gemini/editar-prompt/', gemini_admin.editar_prompt, name='editar_prompt'),
    path('gemini/eliminar-prompt/<int:prompt_id>/', gemini_admin.eliminar_prompt, name='eliminar_prompt'),
    path('gemini/generar/<int:prompt_id>/', gemini_admin.generar_informe_gemini, name='generar_informe_gemini'),
    path('gemini/listar-modelos/', gemini_admin.listar_modelos, name='listar_modelos'),
    path('gemini/ver-informe/<int:prompt_id>/', gemini_admin.ver_informe_gemini, name='ver_informe_gemini'),
    
    
    path('autoevaluacion/<int:trabajador_id>/', 
         views.cuestionario_autoevaluacion, 
         name='autoevaluacion_inicio'),
    
    path('autoevaluacion/<int:trabajador_id>/<int:dimension_id>/', 
         views.cuestionario_autoevaluacion, 
         name='autoevaluacion'),

    path('autoevaluacion/finalizar/<int:trabajador_id>/', 
         views.finalizar_autoevaluacion, 
         name='finalizar_autoevaluacion'),

    path('evaluacion_jefe/<int:evaluador_id>/<int:evaluado_id>/', 
         views.cuestionario_jefatura, 
         name='evaluacion_jefe_inicio'),
    
    path('evaluacion_jefe/<int:evaluador_id>/<int:evaluado_id>/<int:dimension_id>/', 
         views.cuestionario_jefatura, 
         name='evaluacion_jefe'),

    path('evaluacion_jefe/finalizar/<int:evaluador_id>/<int:evaluado_id>/', 
         views.finalizar_evaluacion_jefe, 
         name='finalizar_evaluacion_jefe'),

    path('resultados/<int:trabajador_id>/<str:tipo_evaluacion>/', 
         views.ver_resultados, 
         name='ver_resultados'),

    path('edicion/', edicion_cuestionario.panel_edicion, name='panel_edicion'),
    path('edicion/dimension/editar/<int:dimension_id>/', edicion_cuestionario.editar_dimension, name='editar_dimension'),
    path('edicion/competencia/editar/<int:competencia_id>/', edicion_cuestionario.editar_competencia, name='editar_competencia'),
    path('edicion/nivel/editar/<int:nivel_id>/', edicion_cuestionario.editar_nivel, name='editar_nivel'),
    path('edicion/texto/editar/<int:texto_id>/', edicion_cuestionario.editar_texto, name='editar_texto'),
    path('edicion/escala/editar/<int:escala_id>/', edicion_cuestionario.editar_escala, name='editar_escala'),

    # RUTAS POBLADOR
    path('poblador/', poblador.panel_poblador, name='panel_poblador'),
    path('poblador/empresa/', poblador.guardar_empresa, name='guardar_empresa'),
    path('poblador/departamento/', poblador.guardar_departamento, name='guardar_departamento'),
    path('poblador/nivel/', poblador.guardar_nivel, name='guardar_nivel'),
    path('poblador/escala/', poblador.guardar_escala, name='guardar_escala'),
    path('poblador/dimension/', poblador.guardar_dimension, name='guardar_dimension'),
    path('poblador/competencia/', poblador.guardar_competencia, name='guardar_competencia'),
    path('poblador/cargo/', poblador.guardar_cargo, name='guardar_cargo'),
    path('poblador/texto/', poblador.guardar_texto, name='guardar_texto'),
    path('poblador/trabajador/', poblador.guardar_trabajador, name='guardar_trabajador'),

    # RUTAS RAT
    path('rat/', views.rat_panel_usuario, name='rat_panel_usuario'),
    path('rat/responder/<int:pregunta_id>/', views.rat_responder, name='rat_responder'),
    path('rat/coordinador/', views.rat_panel_coordinador, name='rat_panel_coordinador'),
    path('rat/coordinador/nueva/', views.rat_nueva_pregunta, name='rat_nueva_pregunta'),
    path('rat/coordinador/editar/<int:pregunta_id>/', views.rat_editar_pregunta, name='rat_editar_pregunta'),
    path('rat/coordinador/eliminar/<int:pregunta_id>/', views.rat_eliminar_pregunta, name='rat_eliminar_pregunta'),
    path('rat/versiones/', views.rat_versiones, name='rat_versiones'),
    path('rat/versiones/nueva/', views.rat_nueva_version, name='rat_nueva_version'),
]