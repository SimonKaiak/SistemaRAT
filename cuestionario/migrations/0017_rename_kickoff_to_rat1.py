from django.db import migrations


def renombrar_kickoff_a_rat1(apps, schema_editor):
    Instrumento = apps.get_model('cuestionario', 'Instrumento')
    # Si ya existe RAT 1 y también existe Kick Off, eliminar el RAT 1 duplicado
    rat1_duplicado = Instrumento.objects.filter(nombre_instrumento='RAT 1').first()
    kickoff = Instrumento.objects.filter(nombre_instrumento='Kick Off').first()
    if rat1_duplicado and kickoff:
        rat1_duplicado.delete()
    if kickoff:
        kickoff.nombre_instrumento = 'RAT 1'
        kickoff.save()


def revertir_rat1_a_kickoff(apps, schema_editor):
    Instrumento = apps.get_model('cuestionario', 'Instrumento')
    Instrumento.objects.filter(nombre_instrumento='RAT 1').update(
        nombre_instrumento='Kick Off'
    )


class Migration(migrations.Migration):

    dependencies = [
        ('cuestionario', '0016_ratpreguntas_tipo'),
    ]

    operations = [
        migrations.RunPython(
            renombrar_kickoff_a_rat1,
            reverse_code=revertir_rat1_a_kickoff,
        ),
    ]