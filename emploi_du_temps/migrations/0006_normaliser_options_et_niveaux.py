# Generated manually to separate programme options from academic levels.

import django.db.models.deletion
from django.db import migrations, models


OPTIONS_SEED = {
    "GLO": "Génie Logiciel",
    "DSC": "Data Science",
    "SEC": "Sécurité et Cryptographie",
    "RTE": "Réseaux et Télécommunications",
}

SIGLES_LEGACY = {
    "Génie Logiciel": "GLO",
    "Data Science": "DSC",
    "Sécurité et Cryptographie": "SEC",
    "Réseaux et Télécommunications": "RTE",
    "Informatique et Télécommunications": "ITE",
}


def sigle_option(option):
    if not option:
        return None
    sigle = (getattr(option, "sigle", "") or "").upper()
    return sigle or SIGLES_LEGACY.get(option.nom)


def niveau_valide(niveau, fallback=4):
    try:
        niveau = int(niveau)
    except (TypeError, ValueError):
        return fallback
    return niveau if niveau in (3, 4, 5) else fallback


def sigle_depuis_nom(nom):
    sigle = SIGLES_LEGACY.get(nom)
    if sigle:
        return sigle
    morceaux = [
        "".join(char for char in mot if char.isalnum())
        for mot in (nom or "").replace("-", " ").split()
    ]
    sigle = "".join(mot[0] for mot in morceaux if mot).upper()
    return (sigle or "OPT")[:10]


def normaliser_options_et_niveaux(apps, schema_editor):
    Option = apps.get_model("emploi_du_temps", "Option")
    Cours = apps.get_model("emploi_du_temps", "Cours")
    Creneau = apps.get_model("emploi_du_temps", "Creneau")
    Utilisateur = apps.get_model("emploi_du_temps", "Utilisateur")

    options_par_sigle = {}
    for option in Option.objects.all():
        sigle_base = sigle_option(option) or sigle_depuis_nom(option.nom)
        sigle = sigle_base
        compteur = 2
        while Option.objects.exclude(pk=option.pk).filter(sigle=sigle).exists():
            suffixe = str(compteur)
            sigle = f"{sigle_base[:10 - len(suffixe)]}{suffixe}"
            compteur += 1
        option.sigle = sigle
        option.save(update_fields=["sigle"])
        options_par_sigle[sigle] = option

    for sigle, nom in OPTIONS_SEED.items():
        option = Option.objects.filter(nom=nom).first() or Option.objects.filter(sigle=sigle).first()
        if option is None:
            continue
        else:
            option.sigle = sigle
            option.nom = nom
            option.save(update_fields=["sigle", "nom"])
        options_par_sigle[sigle] = option

    def options_valides(options):
        ids = []
        for option in options:
            sigle = sigle_option(option)
            if sigle in options_par_sigle:
                option_id = options_par_sigle[sigle].pk
                if option_id not in ids:
                    ids.append(option_id)
        return ids

    for cours in Cours.objects.select_related("option").prefetch_related("options"):
        niveau_source = getattr(cours.option, "niveau", None) if cours.option_id else None
        niveau = niveau_valide(niveau_source, niveau_valide(getattr(cours, "niveau", 4)))
        option_ids = options_valides(list(cours.options.all()))
        if not option_ids and cours.option_id:
            option_ids = options_valides([cours.option])
        if not option_ids:
            Creneau.objects.filter(cours_id=cours.pk).delete()
            cours.delete()
            continue
        cours.option_id = option_ids[0]
        cours.niveau = niveau
        cours.save(update_fields=["option", "niveau"])
        cours.options.set(option_ids)

    for utilisateur in Utilisateur.objects.select_related("option").filter(role="ETUDIANT"):
        if not utilisateur.option_id:
            continue
        sigle = sigle_option(utilisateur.option)
        if sigle not in options_par_sigle:
            continue
        utilisateur.option_id = options_par_sigle[sigle].pk
        utilisateur.niveau = niveau_valide(
            getattr(utilisateur, "niveau", None),
            niveau_valide(getattr(utilisateur.option, "niveau", None)),
        )
        utilisateur.save(update_fields=["option", "niveau"])

    for creneau in Creneau.objects.select_related("option", "cours").prefetch_related("options"):
        option_ids = options_valides(list(creneau.options.all()))
        if not option_ids and creneau.option_id:
            option_ids = options_valides([creneau.option])
        if not option_ids and creneau.cours_id:
            option_ids = list(creneau.cours.options.values_list("pk", flat=True))
        if not option_ids:
            creneau.delete()
            continue
        creneau.option_id = option_ids[0]
        creneau.niveau = niveau_valide(getattr(creneau.cours, "niveau", None))
        creneau.save(update_fields=["option", "niveau"])
        creneau.options.set(option_ids)


class Migration(migrations.Migration):

    dependencies = [
        ("emploi_du_temps", "0005_utilisateur_niveau"),
    ]

    operations = [
        migrations.AddField(
            model_name="option",
            name="sigle",
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name="cours",
            name="niveau",
            field=models.PositiveSmallIntegerField(
                choices=[(3, "Niveau 3"), (4, "Niveau 4"), (5, "Niveau 5")],
                default=4,
                verbose_name="niveau",
            ),
        ),
        migrations.AddField(
            model_name="creneau",
            name="niveau",
            field=models.PositiveSmallIntegerField(
                choices=[(3, "Niveau 3"), (4, "Niveau 4"), (5, "Niveau 5")],
                default=4,
                verbose_name="niveau",
            ),
        ),
        migrations.AlterField(
            model_name="cours",
            name="option",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="cours",
                to="emploi_du_temps.option",
                verbose_name="option principale",
            ),
        ),
        migrations.RunPython(normaliser_options_et_niveaux, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="option",
            name="sigle",
            field=models.CharField(max_length=10, unique=True),
        ),
        migrations.RemoveField(
            model_name="option",
            name="niveau",
        ),
        migrations.AlterModelOptions(
            name="option",
            options={"ordering": ["sigle"], "verbose_name": "option", "verbose_name_plural": "options"},
        ),
        migrations.AlterModelOptions(
            name="cours",
            options={"ordering": ["niveau", "codeCours", "intitule"], "verbose_name": "cours", "verbose_name_plural": "cours"},
        ),
    ]
