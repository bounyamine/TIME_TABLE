# Generated manually to support shared timetable slots across options.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("emploi_du_temps", "0002_cours_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="creneau",
            name="options",
            field=models.ManyToManyField(
                blank=True,
                related_name="creneaux_partages",
                to="emploi_du_temps.option",
                verbose_name="options concernées",
            ),
        ),
    ]
