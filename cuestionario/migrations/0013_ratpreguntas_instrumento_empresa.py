import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cuestionario', '0012_instrumento_remove_ratpreguntas_empresa_and_more'),
    ]

    operations = [
        # 1. Agregar la nueva FK a InstrumentoEmpresa (nullable para no romper filas existentes)
        migrations.AddField(
            model_name='ratpreguntas',
            name='instrumento_empresa',
            field=models.ForeignKey(
                to='cuestionario.instrumentoempresa',
                on_delete=django.db.models.deletion.CASCADE,
                db_column='instrumento_empresa_id',
                null=True,
                blank=True,
            ),
        ),
        # 2. Quitar la FK vieja a Instrumento
        migrations.RemoveField(
            model_name='ratpreguntas',
            name='instrumento',
        ),
        # 3. Hacer la nueva FK obligatoria
        migrations.AlterField(
            model_name='ratpreguntas',
            name='instrumento_empresa',
            field=models.ForeignKey(
                to='cuestionario.instrumentoempresa',
                on_delete=django.db.models.deletion.CASCADE,
                db_column='instrumento_empresa_id',
                related_name='preguntas',
            ),
        ),
    ]