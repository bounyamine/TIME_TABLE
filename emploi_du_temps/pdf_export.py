from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date

from django.conf import settings
from django.template.loader import render_to_string
from django.utils.text import slugify
from weasyprint import HTML

from .grille import JOURS_EDT, construire_grille_semaine
from .models import Salle


@dataclass(frozen=True)
class ExportPlanning:
    contenu: bytes
    nom_fichier: str


def generer_pdf_emplois_du_temps(semaine: date) -> ExportPlanning:
    salles = Salle.objects.filter(
        creneaux__emploiDuTemps__semaine=semaine
    ).distinct()
    if not salles.exists():
        salles = Salle.objects.all()

    salles_lignes = [
        {
            "salle": salle,
            "lignes": construire_grille_semaine(semaine, salle_id=salle.pk),
        }
        for salle in salles.order_by("site", "nom")
    ]

    logo_path = os.path.join(
        settings.BASE_DIR,
        "emploi_du_temps", "static", "emploi_du_temps", "img", "logo_enspm.png"
    )
    # Si le fichier n'existe pas, on passe None → le template affiche "ENSPM" en texte
    if not os.path.isfile(logo_path):
        logo_path = None

    html_str = render_to_string(
        "emploi_du_temps/grille/imprimer_global.html",
        {
            "semaine": semaine,
            "salles_lignes": salles_lignes,
            "jours": JOURS_EDT,
            "logo_path": logo_path,
        },
    )

    contenu = HTML(string=html_str).write_pdf()
    slug = slugify(f"emplois-du-temps-{semaine.isoformat()}")
    return ExportPlanning(contenu=contenu, nom_fichier=f"{slug}.pdf")