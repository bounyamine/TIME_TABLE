from datetime import date, time

from django.db.models import Q

from .models import Creneau, EmploiDuTemps, Salle

JOURS_EDT = [
    ("LUNDI", "Lundi"),
    ("MARDI", "Mardi"),
    ("MERCREDI", "Mercredi"),
    ("JEUDI", "Jeudi"),
    ("VENDREDI", "Vendredi"),
    ("SAMEDI", "Samedi"),
]

PLAGES_HORAIRES = [
    {"id": "0730-0930", "debut": time(7, 30), "fin": time(9, 30),  "label": "7H30 - 9H30"},
    {"id": "0930-1130", "debut": time(9, 30), "fin": time(11, 30), "label": "9H30 - 11H30"},
    {"id": "1130-1330", "debut": time(11, 30),"fin": time(13, 30), "label": "11H30 - 13H30"},
    {"id": "1330-1400", "debut": time(13, 30),"fin": time(14, 0),  "label": "13H30 - 14H00", "pause": True},
    {"id": "1400-1600", "debut": time(14, 0), "fin": time(16, 0),  "label": "14H00 - 16H00"},
]


def trouver_plage(plage_id: str) -> dict | None:
    for plage in PLAGES_HORAIRES:
        if plage["id"] == plage_id:
            return plage
    return None


def construire_grille(emploi_du_temps: EmploiDuTemps) -> list[dict]:
    """Grille pour l'éditeur d'un EmploiDuTemps spécifique."""
    creneaux = Creneau.objects.filter(emploiDuTemps=emploi_du_temps).select_related(
        "cours__ue", "cours", "enseignant", "salle"
    ).prefetch_related("options", "cours__options")
    creneaux_par_cellule = {
        (c.jour, c.heureDebut, c.heureFin): c for c in creneaux
    }
    lignes = []
    for plage in PLAGES_HORAIRES:
        if plage.get("pause"):
            lignes.append({"plage": plage, "pause": True, "cellules": []})
            continue
        cellules = []
        for code_jour, libelle_jour in JOURS_EDT:
            creneau = creneaux_par_cellule.get((code_jour, plage["debut"], plage["fin"]))
            cellules.append({
                "jour": code_jour,
                "jour_label": libelle_jour,
                "plage": plage,
                "creneau": creneau,
            })
        lignes.append({"plage": plage, "pause": False, "cellules": cellules})
    return lignes


def construire_grille_semaine(
    semaine: date,
    salle_id: int | None = None,
    utilisateur=None,
    filtres: dict | None = None,
) -> list[dict]:
    """Grille hebdomadaire, limitée aux créneaux autorisés puis aux filtres choisis."""
    filtres = dict(filtres or {})
    if salle_id:
        filtres["salle_id"] = salle_id
    qs = creneaux_visibles_semaine(semaine, utilisateur, filtres=filtres)

    creneaux_par_cellule: dict[tuple, list] = {}
    for c in qs:
        key = (c.jour, c.heureDebut, c.heureFin)
        creneaux_par_cellule.setdefault(key, []).append(c)

    lignes = []
    for plage in PLAGES_HORAIRES:
        if plage.get("pause"):
            lignes.append({"plage": plage, "pause": True, "cellules": []})
            continue
        cellules = []
        for code_jour, libelle_jour in JOURS_EDT:
            key = (code_jour, plage["debut"], plage["fin"])
            cellules.append({
                "jour": code_jour,
                "jour_label": libelle_jour,
                "plage": plage,
                "creneaux": creneaux_par_cellule.get(key, []),
            })
        lignes.append({"plage": plage, "pause": False, "cellules": cellules})
    return lignes


def construire_grilles_par_salle(
    semaine: date,
    utilisateur=None,
    filtres: dict | None = None,
) -> list[dict]:
    """Une grille par salle ayant des créneaux visibles (ou la salle filtrée)."""
    filtres = dict(filtres or {})
    filtres_sans_salle = {key: value for key, value in filtres.items() if key != "salle_id"}
    creneaux = creneaux_visibles_semaine(semaine, utilisateur, filtres=filtres)
    est_cd = (
        utilisateur
        and utilisateur.is_authenticated
        and utilisateur.role == utilisateur.Role.CD
    )
    if filtres.get("salle_id"):
        salles = Salle.objects.filter(pk=filtres["salle_id"])
    elif est_cd:
        # Le CD doit pouvoir éditer/remplir même les salles encore vides cette semaine.
        salles = Salle.objects.all()
    else:
        salles = Salle.objects.filter(creneaux__in=creneaux).distinct()

    compte_par_salle: dict[int, int] = {}
    for c in creneaux:
        compte_par_salle[c.salle_id] = compte_par_salle.get(c.salle_id, 0) + 1

    return [
        {
            "salle": salle,
            "lignes": construire_grille_semaine(
                semaine,
                salle_id=salle.pk,
                utilisateur=utilisateur,
                filtres=filtres_sans_salle,
            ),
            "nb_creneaux": compte_par_salle.get(salle.pk, 0),
        }
        for salle in salles.order_by("site", "nom")
    ]


def appliquer_filtres_creneaux(qs, filtres: dict | None = None):
    filtres = filtres or {}
    if filtres.get("salle_id"):
        qs = qs.filter(salle_id=filtres["salle_id"])
    if filtres.get("enseignant_id"):
        qs = qs.filter(enseignant_id=filtres["enseignant_id"])
    if filtres.get("option_id"):
        qs = qs.filter(Q(option_id=filtres["option_id"]) | Q(options__id=filtres["option_id"]))
    if filtres.get("niveau"):
        qs = qs.filter(niveau=filtres["niveau"])
    return qs.distinct()


def creneaux_visibles_semaine(semaine: date, utilisateur=None, filtres: dict | None = None):
    qs = Creneau.objects.filter(
        emploiDuTemps__semaine=semaine,
    ).select_related(
        "cours__ue", "cours", "enseignant", "salle", "option", "emploiDuTemps"
    ).prefetch_related("options", "cours__options")

    est_cd = (
        utilisateur
        and utilisateur.is_authenticated
        and utilisateur.role == utilisateur.Role.CD
    )
    if not est_cd:
        qs = qs.filter(emploiDuTemps__statut=EmploiDuTemps.Statut.PUBLIE)

    return appliquer_filtres_creneaux(qs, filtres)
