# Generated manually to support courses shared by multiple options.

from django.db import migrations, models


def copier_option_principale(apps, schema_editor):
    Cours = apps.get_model("emploi_du_temps", "Cours")
    for cours in Cours.objects.exclude(option_id__isnull=True):
        cours.options.add(cours.option_id)


class Migration(migrations.Migration):

    dependencies = [
        ("emploi_du_temps", "0003_creneau_options"),
    ]

    operations = [
        migrations.AddField(
            model_name="cours",
            name="options",
            field=models.ManyToManyField(
                blank=True,
                related_name="cours_partages",
                to="emploi_du_temps.option",
                verbose_name="options concernées",
            ),
        ),
        migrations.RunPython(copier_option_principale, migrations.RunPython.noop),
    ]
