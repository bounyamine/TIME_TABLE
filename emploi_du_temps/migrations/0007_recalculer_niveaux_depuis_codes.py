# Generated manually to infer course levels after option normalization.

from django.db import migrations


def niveau_depuis_code(code):
    chiffres = "".join(char for char in (code or "") if char.isdigit())
    if chiffres and int(chiffres[0]) in (3, 4, 5):
        return int(chiffres[0])
    return 4


def recalculer_niveaux(apps, schema_editor):
    Cours = apps.get_model("emploi_du_temps", "Cours")
    Creneau = apps.get_model("emploi_du_temps", "Creneau")

    for cours in Cours.objects.all():
        niveau = niveau_depuis_code(cours.codeCours or cours.ue_id)
        if cours.niveau != niveau:
            cours.niveau = niveau
            cours.save(update_fields=["niveau"])

    for creneau in Creneau.objects.select_related("cours"):
        niveau = niveau_depuis_code(creneau.cours.codeCours or creneau.cours.ue_id)
        if creneau.niveau != niveau:
            creneau.niveau = niveau
            creneau.save(update_fields=["niveau"])


class Migration(migrations.Migration):

    dependencies = [
        ("emploi_du_temps", "0006_normaliser_options_et_niveaux"),
    ]

    operations = [
        migrations.RunPython(recalculer_niveaux, migrations.RunPython.noop),
    ]
