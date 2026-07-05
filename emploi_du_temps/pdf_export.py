from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date, timedelta

from django.conf import settings
from django.template.loader import render_to_string
from django.utils.text import slugify
from weasyprint import HTML

from .grille import JOURS_EDT, construire_grille_semaine, construire_grilles_par_salle
from .models import Salle


@dataclass(frozen=True)
class ExportPlanning:
    contenu: bytes
    nom_fichier: str


def generer_pdf_emplois_du_temps(semaine: date, utilisateur=None, filtres: dict | None = None) -> ExportPlanning:
    filtres = filtres or {}
    salles_lignes = construire_grilles_par_salle(semaine, utilisateur, filtres=filtres)
    if not salles_lignes and (
        not utilisateur
        or not utilisateur.is_authenticated
        or utilisateur.role == utilisateur.Role.CD
    ):
        filtres_sans_salle = {key: value for key, value in filtres.items() if key != "salle_id"}
        salles_lignes = [
            {
                "salle": salle,
                "lignes": construire_grille_semaine(
                    semaine,
                    salle_id=salle.pk,
                    utilisateur=utilisateur,
                    filtres=filtres_sans_salle,
                ),
            }
            for salle in Salle.objects.all().order_by("site", "nom")
        ]

    logo_path = os.path.join(
        settings.BASE_DIR,
        "emploi_du_temps", "static", "emploi_du_temps", "img", "logo_enspm.png"
    )
    if not os.path.isfile(logo_path):
        logo_path = None

    fin_semaine = semaine + timedelta(days=5)
    mois = [
        "",
        "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
        "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
    ]
    periode_label = (
        f"période du {semaine.day:02d} au {fin_semaine.day:02d} "
        f"{mois[fin_semaine.month]} {fin_semaine.year}"
    )

    html_str = render_to_string(
        "emploi_du_temps/grille/imprimer_global.html",
        {
            "semaine": semaine,
            "annee_debut": semaine.year - 1,
            "annee_fin": semaine.year,
            "periode_label": periode_label,
            "salles_lignes": salles_lignes,
            "jours": JOURS_EDT,
            "logo_path": logo_path,
        },
    )

    contenu = HTML(string=html_str).write_pdf()
    fin_semaine = semaine + timedelta(days=5)

    mois = [
        "",
        "JANVIER", "FÉVRIER", "MARS", "AVRIL", "MAI", "JUIN",
        "JUILLET", "AOÛT", "SEPTEMBRE", "OCTOBRE", "NOVEMBRE", "DÉCEMBRE",
    ]

    if semaine.month == fin_semaine.month:
        nom_fichier = (
            f"TIME_TABLE_ENSPM_INFOTEL_DU_"
            f"{semaine.day:02d}_AU_{fin_semaine.day:02d}_"
            f"{mois[semaine.month]}_{semaine.year}.pdf"
        )
    else:
        nom_fichier = (
            f"TIME_TABLE_ENSPM_INFOTEL_DU_"
            f"{semaine.day:02d}_{mois[semaine.month]}_"
            f"AU_{fin_semaine.day:02d}_{mois[fin_semaine.month]}_"
            f"{fin_semaine.year}.pdf"
        )

    return ExportPlanning(
        contenu=contenu,
        nom_fichier=nom_fichier,
    )