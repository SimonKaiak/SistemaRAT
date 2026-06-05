"""
urls.py
-------
Definición de todas las rutas URL de la aplicación cuestionario.

Autenticación:
    /login/   → login_view
    /logout/  → LogoutView (redirige a login)

Panel principal:
    /         → index

Seguimiento:
    /seguimiento/                              → panel_seguimiento
    /seguimiento/detalle/<id>/                 → detalle_seguimiento
    /seguimiento/detalle/<id>/pdf/             → generar_pdf_detalle
    /seguimiento/detalle/<id>/excel/           → generar_excel_detalle
    /seguimiento/reporte-global/               → generar_reporte_global_pdf
    /seguimiento/ver-reporte-global/<id>/      → ver_reporte_global_pdf

Biblioteca y Gemini:
    /biblioteca/ver-archivo/<id>/              → ver_archivo_biblioteca
    /gemini/                                   → panel_gemini
    /gemini/editar-prompt/                     → editar_prompt
    /gemini/eliminar-prompt/<id>/              → eliminar_prompt
    /gemini/generar/<id>/                      → generar_informe_gemini
    /gemini/listar-modelos/                    → listar_modelos
    /gemini/ver-informe/<id>/                  → ver_informe_gemini

Evaluaciones:
    /autoevaluacion/<tid>/                     → autoevaluacion_inicio
    /autoevaluacion/<tid>/<did>/               → autoevaluacion (con dimensión)
    /autoevaluacion/finalizar/<tid>/           → finalizar_autoevaluacion
    /evaluacion_jefe/<eid>/<evid>/             → evaluacion_jefe_inicio
    /evaluacion_jefe/<eid>/<evid>/<did>/       → evaluacion_jefe (con dimensión)
    /evaluacion_jefe/finalizar/<eid>/<evid>/   → finalizar_evaluacion_jefe
    /resultados/<tid>/<tipo>/                  → ver_resultados

Edición de cuestionario:
    /edicion/                                  → panel_edicion
    /edicion/dimension/editar/<id>/            → editar_dimension
    /edicion/competencia/editar/<id>/          → editar_competencia
    /edicion/nivel/editar/<id>/                → editar_nivel
    /edicion/texto/editar/<id>/                → editar_texto
    /edicion/escala/editar/<id>/               → editar_escala
    /edicion/niveles/                          → panel_edicion_niveles

Poblador (CRUD de datos maestros, todos POST JSON):
    /poblador/                                 → panel_poblador
    /poblador/empresa/                         → guardar_empresa
    /poblador/empresa/editar/<id>/             → editar_empresa
    /poblador/empresa/eliminar/<id>/           → eliminar_empresa
    /poblador/<entidad>/                       → guardar_<entidad>
    /poblador/<entidad>/editar/<pk>/           → editar_<entidad>_poblador
    /poblador/<entidad>/eliminar/<pk>/         → eliminar_<entidad>
    Entidades: departamento, nivel, escala, dimension,
               competencia, cargo, texto, trabajador.

Gestión de usuarios (POST JSON, solo superusuario):
    /gestion-usuarios/                         → panel_gestion_usuarios
    /gestion-usuarios/modificar/<id>/          → modificar_usuario
    /gestion-usuarios/resetear-clave/<id>/     → resetear_clave_usuario
    /gestion-usuarios/eliminar/<id>/           → eliminar_usuario_panel
    /gestion-usuarios/agregar-coordinador/<id>/ → agregar_coordinador
    /gestion-usuarios/quitar-coordinador/<id>/  → quitar_coordinador
    /gestion-usuarios/crear/                   → crear_usuario_panel
    /gestion-usuarios/cargar-excel/            → cargar_usuarios_excel

RAT:
    /rat/                                      → rat_panel_usuario
    /rat/responder/<id>/                       → rat_responder
    /rat/coordinador/                          → rat_panel_coordinador
    /rat/coordinador/nueva/                    → rat_nueva_pregunta
    /rat/coordinador/editar/<id>/              → rat_editar_pregunta
    /rat/coordinador/eliminar/<id>/            → rat_eliminar_pregunta
    /rat/versiones/                            → rat_versiones
    /rat/versiones/nueva/                      → rat_nueva_version
    /rat/version/<id>/editar/                  → rat_editar_version
    /rat/version/<id>/eliminar/                → rat_eliminar_version
    /instrumentos/                             → seleccion_instrumentos
    /rat/crear-instrumento/                    → rat_crear_instrumento
"""

from django.urls import path
from django.contrib.auth.views import LogoutView
from . import logica as views
from .logica import validador_login, seguimiento, detalle_seguimiento, reporte_pdf, reporte_excel, gemini_admin, reporte_global, manejo_archivos, edicion_cuestionario, poblador, gestion_usuarios, carga_excel, reporte_rat_pdf
from .logica.rat import rat_editar_version, rat_eliminar_version, seleccion_instrumentos, rat_crear_instrumento, rat_ver_trabajador

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
    path('edicion/niveles/', edicion_cuestionario.panel_edicion_niveles, name='panel_edicion_niveles'),

    # RUTAS POBLADOR
    path('poblador/', poblador.panel_poblador, name='panel_poblador'),
    path('poblador/empresa/editar/<int:empresa_id>/', poblador.editar_empresa, name='editar_empresa'),
    path('poblador/empresa/eliminar/<int:empresa_id>/', poblador.eliminar_empresa, name='eliminar_empresa'),
    path('poblador/empresa/', poblador.guardar_empresa, name='guardar_empresa'),
    path('poblador/departamento/editar/<int:pk>/', poblador.editar_departamento, name='editar_departamento'),
    path('poblador/departamento/eliminar/<int:pk>/', poblador.eliminar_departamento, name='eliminar_departamento'),
    path('poblador/departamento/', poblador.guardar_departamento, name='guardar_departamento'),
    path('poblador/nivel/editar/<int:pk>/', poblador.editar_nivel, name='editar_nivel_poblador'),
    path('poblador/nivel/eliminar/<int:pk>/', poblador.eliminar_nivel, name='eliminar_nivel'),
    path('poblador/nivel/', poblador.guardar_nivel, name='guardar_nivel'),
    path('poblador/escala/editar/<int:pk>/', poblador.editar_escala_poblador, name='editar_escala_poblador'),
    path('poblador/escala/', poblador.guardar_escala, name='guardar_escala'),
    path('poblador/dimension/editar/<int:pk>/', poblador.editar_dimension_poblador, name='editar_dimension_poblador'),
    path('poblador/dimension/eliminar/<int:pk>/', poblador.eliminar_dimension, name='eliminar_dimension'),
    path('poblador/dimension/', poblador.guardar_dimension, name='guardar_dimension'),
    path('poblador/competencia/editar/<int:pk>/', poblador.editar_competencia_poblador, name='editar_competencia_poblador'),
    path('poblador/competencia/eliminar/<int:pk>/', poblador.eliminar_competencia, name='eliminar_competencia'),
    path('poblador/competencia/', poblador.guardar_competencia, name='guardar_competencia'),
    path('poblador/cargo/editar/<int:pk>/', poblador.editar_cargo_poblador, name='editar_cargo_poblador'),
    path('poblador/cargo/eliminar/<int:pk>/', poblador.eliminar_cargo, name='eliminar_cargo'),
    path('poblador/cargo/', poblador.guardar_cargo, name='guardar_cargo'),
    path('poblador/texto/editar/<int:pk>/', poblador.editar_texto_poblador, name='editar_texto_poblador'),
    path('poblador/texto/eliminar/<int:pk>/', poblador.eliminar_texto, name='eliminar_texto'),
    path('poblador/texto/', poblador.guardar_texto, name='guardar_texto'),
    path('poblador/trabajador/editar/<int:pk>/', poblador.editar_trabajador_poblador, name='editar_trabajador_poblador'),
    path('poblador/trabajador/eliminar/<int:pk>/', poblador.eliminar_trabajador, name='eliminar_trabajador'),
    path('poblador/trabajador/', poblador.guardar_trabajador, name='guardar_trabajador'),

    # RUTAS GESTIÓN DE USUARIOS
    path('gestion-usuarios/', gestion_usuarios.panel_gestion_usuarios, name='gestion_usuarios'),
    path('gestion-usuarios/modificar/<int:trabajador_id>/', gestion_usuarios.modificar_usuario, name='modificar_usuario'),
    path('gestion-usuarios/resetear-clave/<int:trabajador_id>/', gestion_usuarios.resetear_clave, name='resetear_clave_usuario'),
    path('gestion-usuarios/eliminar/<int:trabajador_id>/', gestion_usuarios.eliminar_usuario_panel, name='eliminar_usuario_panel'),
    path('gestion-usuarios/agregar-coordinador/<int:trabajador_id>/', gestion_usuarios.agregar_coordinador, name='agregar_coordinador'),
    path('gestion-usuarios/quitar-coordinador/<int:trabajador_id>/', gestion_usuarios.quitar_coordinador, name='quitar_coordinador'),
    path('gestion-usuarios/crear/', gestion_usuarios.crear_usuario_panel, name='crear_usuario_panel'),
    path('gestion-usuarios/cargar-excel/', carga_excel.cargar_usuarios_excel, name='cargar_usuarios_excel'),

    # RUTAS RAT
    path('rat/', views.rat_panel_usuario, name='rat_panel_usuario'),
    path('rat/responder/<int:pregunta_id>/', views.rat_responder, name='rat_responder'),
    path('rat/coordinador/', views.rat_panel_coordinador, name='rat_panel_coordinador'),
    path('rat/coordinador/nueva/', views.rat_nueva_pregunta, name='rat_nueva_pregunta'),
    path('rat/coordinador/editar/<int:pregunta_id>/', views.rat_editar_pregunta, name='rat_editar_pregunta'),
    path('rat/coordinador/eliminar/<int:pregunta_id>/', views.rat_eliminar_pregunta, name='rat_eliminar_pregunta'),
    path('rat/versiones/', views.rat_versiones, name='rat_versiones'),
    path('rat/versiones/nueva/', views.rat_nueva_version, name='rat_nueva_version'),
    path('rat/version/<int:version_id>/editar/', rat_editar_version, name='rat_editar_version'),
    path('rat/version/<int:version_id>/eliminar/', rat_eliminar_version, name='rat_eliminar_version'),
    path('instrumentos/', seleccion_instrumentos, name='seleccion_instrumentos'),
    path('rat/crear-instrumento/', rat_crear_instrumento, name='rat_crear_instrumento'),
    path('rat/ver/<int:trabajador_id>/', rat_ver_trabajador, name='rat_ver_trabajador'),
    path('seguimiento/rat/', seguimiento.panel_seguimiento_rat, name='seguimiento_rat'),
    path('gestion-usuarios/resetear-clave-seguimiento/<int:trabajador_id>/', gestion_usuarios.resetear_clave_seguimiento, name='resetear_clave_seguimiento'),
    path('gestion-usuarios/enviar-recordatorio-rat/<int:trabajador_id>/', gestion_usuarios.enviar_recordatorio_rat, name='enviar_recordatorio_rat'),
    path('gestion-usuarios/resetear-respuestas-rat/<int:trabajador_id>/', gestion_usuarios.resetear_respuestas_rat, name='resetear_respuestas_rat'),
    path('seguimiento/rat/reporte-pdf/', reporte_rat_pdf.generar_reporte_rat_pdf, name='reporte_rat_pdf'),
]