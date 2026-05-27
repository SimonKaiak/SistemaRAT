"""
__init__.py
-----------------
Punto de entrada del módulo de vistas del proyecto.
Centraliza las importaciones de todas las vistas para que puedan
ser referenciadas directamente desde `cuestionario.views` sin
necesidad de conocer en qué submódulo están definidas.

Módulos que agrupa:
- vistas_generales: índice principal y visualización de resultados.
- vistas_evaluaciones: flujo completo de autoevaluación y evaluación de jefatura.
- rat: panel RAT del usuario, respuesta de preguntas, gestión de preguntas
  (crear, editar, eliminar), versiones y selección de instrumentos.
"""
from .vistas_generales import index, ver_resultados
from .vistas_evaluaciones import (
    cuestionario_autoevaluacion, 
    finalizar_autoevaluacion, 
    cuestionario_jefatura, 
    finalizar_evaluacion_jefe
)
from .rat import (
    rat_panel_usuario,
    rat_responder,
    rat_panel_coordinador,
    rat_nueva_pregunta,
    rat_editar_pregunta,
    rat_eliminar_pregunta,
    rat_versiones,
    rat_nueva_version,
    seleccion_instrumentos,
)