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