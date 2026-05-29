from django.db import migrations


def renombrar_kickoff_a_rat1(apps, schema_editor):
    # Ya está hecho manualmente en producción, no hacer nada
    pass


def revertir_rat1_a_kickoff(apps, schema_editor):
    pass


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