"""
templatetags/dict_extras.py
---------------------------
Filtros de template personalizados para el sistema.

get_item(dictionary, key)
    Accede a un valor de un diccionario por clave variable en
    templates Django, donde la sintaxis dictionary[key] no está
    disponible directamente.
    Uso: {{ mi_dict|get_item:variable }}
    Retorna cadena vacía si la clave no existe.

formato_rut(rut)
    Formatea un RUT chileno al formato estándar XX.XXX.XXX-Y,
    eliminando puntos y guiones previos antes de reformatear.
    Uso: {{ trabajador.rut|formato_rut }}
    Retorna cadena vacía si el rut es None o vacío.
"""

from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, "")

@register.filter
def formato_rut(rut):
    if not rut:
        return ''
    rut = str(rut).replace('.', '').replace('-', '').strip()
    if len(rut) < 2:
        return rut
    cuerpo = rut[:-1]
    dv = rut[-1]
    cuerpo_fmt = ''
    for i, c in enumerate(reversed(cuerpo)):
        if i > 0 and i % 3 == 0:
            cuerpo_fmt = '.' + cuerpo_fmt
        cuerpo_fmt = c + cuerpo_fmt
    return f'{cuerpo_fmt}-{dv}'