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
)