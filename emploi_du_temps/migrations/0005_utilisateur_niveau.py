# Generated manually to store the student's level on the user account.

from django.db import migrations, models


def remplir_niveau_etudiants(apps, schema_editor):
    Utilisateur = apps.get_model("emploi_du_temps", "Utilisateur")
    for utilisateur in Utilisateur.objects.filter(role="ETUDIANT", option__isnull=False).select_related("option"):
        utilisateur.niveau = utilisateur.option.niveau
        utilisateur.save(update_fields=["niveau"])


class Migration(migrations.Migration):

    dependencies = [
        ("emploi_du_temps", "0004_cours_options"),
    ]

    operations = [
        migrations.AddField(
            model_name="utilisateur",
            name="niveau",
            field=models.PositiveSmallIntegerField(
                blank=True,
                choices=[(3, "Niveau 3"), (4, "Niveau 4"), (5, "Niveau 5")],
                null=True,
                verbose_name="niveau de l’étudiant",
            ),
        ),
        migrations.RunPython(remplir_niveau_etudiants, migrations.RunPython.noop),
    ]
