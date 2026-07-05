from django.db import migrations, models


def supprimer_etudiants(apps, schema_editor):
    Utilisateur = apps.get_model("emploi_du_temps", "Utilisateur")
    Utilisateur.objects.filter(role="ETUDIANT").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("emploi_du_temps", "0007_recalculer_niveaux_depuis_codes"),
    ]

    operations = [
        migrations.RunPython(supprimer_etudiants, migrations.RunPython.noop),
        migrations.DeleteModel(
            name="Etudiant",
        ),
        migrations.RemoveField(
            model_name="utilisateur",
            name="niveau",
        ),
        migrations.RemoveField(
            model_name="utilisateur",
            name="option",
        ),
        migrations.AlterField(
            model_name="utilisateur",
            name="role",
            field=models.CharField(
                choices=[("CD", "Chef de département"), ("ENSEIGNANT", "Enseignant")],
                max_length=20,
            ),
        ),
    ]
