"""
migrations/0013_ratpreguntas_instrumento_empresa.py
----------------------------------------------------
Migración generada manualmente. Reemplaza la FK de RATPreguntas
desde Instrumento hacia InstrumentoEmpresa, completando el diseño
multi-empresa del módulo RAT.

Cambios aplicados en 3 pasos para evitar romper filas existentes:

1. Agrega instrumento_empresa (FK a InstrumentoEmpresa) como campo
   nullable/blank, permitiendo que las filas existentes queden
   temporalmente sin valor.

2. Elimina el campo instrumento (FK a Instrumento) que fue
   introducido en la migración 0012.

3. Hace instrumento_empresa obligatorio (not null) con
   related_name='preguntas', quedando como la única FK de
   RATPreguntas hacia la configuración de empresa.

Resultado final:
    RATPreguntas apunta a InstrumentoEmpresa en lugar de a
    Instrumento directamente, lo que permite que cada empresa
    tenga su propio conjunto de preguntas RAT independiente
    por instrumento asignado.
"""
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