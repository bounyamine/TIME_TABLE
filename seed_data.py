"""
Seed propre des ressources ENSPM.

Utilisation :
    python manage.py shell < seed_data.py

Pour repartir totalement propre en développement :
    python manage.py flush
    python manage.py migrate
    python manage.py shell < seed_data.py
"""

from datetime import date, time

from emploi_du_temps.models import (
    Creneau,
    Cours,
    EmploiDuTemps,
    Option,
    Salle,
    UE,
    Utilisateur,
)


PASSWORD = "Enspm2026!"
VH_STD = "CM:30h, TD:20h, TP:30h, TPE:10h"
SEMAINE_EDT = date(2026, 6, 8)


OPTIONS = {
    "SEC": {"nom": "Sécurité et Cryptographie", "niveau": 4},
    "RTE": {"nom": "Réseaux et Télécommunications", "niveau": 4},
    "DSC": {"nom": "Data Science", "niveau": 4},
    "GLO": {"nom": "Génie Logiciel", "niveau": 4},
    "ITE": {"nom": "Informatique et Télécommunications", "niveau": 3},
}


SALLES = [
    {"nom": "Labo INFOTEL", "capacite": 40, "site": "Campus de Sékandé"},
    {"nom": "INFOTEL & ENREN", "capacite": 80, "site": "Campus de Sékandé"},
    {"nom": "AMPHI 150", "capacite": 150, "site": "Campus de Sékandé"},
    {"nom": "Incubateur des entreprises ENSPM", "capacite": 40, "site": "Domayo"},
    {"nom": "IP1", "capacite": 60, "site": "Campus de IRAD PITOARE"},
    {"nom": "IP2", "capacite": 60, "site": "Campus de IRAD PITOARE"},
    {"nom": "NS7", "capacite": 50, "site": "Campus de OURO-TCHEDE"},
    {"nom": "Orange Digital Club (ODC)", "capacite": 50, "site": "Campus de KONGOLA-DJOULGOUF-KODEK"},
]


# Un cours peut appartenir à une ou plusieurs options.
# "option_principale" = première option de la liste, gardée pour compatibilité avec l'ancien modèle.
COURS = [
    # ITE niveau 3
    {"code": "ITE345", "ue": "Réseaux Locaux et Interconnexion", "cours": "Réseaux Locaux et Interconnexion", "options": ["ITE"]},
    {"code": "ITE345", "ue": "Logiques et Électronique Programmable", "cours": "Logiques et Électronique Programmable", "options": ["ITE"]},
    {"code": "ITE325", "ue": "Architecture des Ordinateurs et SI", "cours": "Architecture des Ordinateurs et SI", "options": ["ITE"]},
    {"code": "ITE355", "ue": "Logique Formelle", "cours": "Logique Formelle", "options": ["ITE"]},
    {"code": "ITE315", "ue": "Programmation Orientée Objet", "cours": "Programmation Orientée Objet", "options": ["ITE"]},

    # GLO
    {"code": "GLO346", "ue": "Modélisation Informatique", "cours": "Modélisation Informatique", "options": ["GLO"]},
    {"code": "GLO417", "ue": "IOT - Présentation des Projets", "cours": "IOT (Présentation des Projets)", "options": ["GLO"]},
    {"code": "GLO418", "ue": "Développement Web", "cours": "Développement Web", "options": ["GLO"]},
    {"code": "GLO418", "ue": "Développement d'Applications Mobiles", "cours": "Développement d'Applications Mobiles", "options": ["GLO"]},
    {"code": "GLO428", "ue": "Administration Base de Données", "cours": "Administration Base de Données", "options": ["GLO"]},
    {"code": "GLO438", "ue": "Atelier de Programmation", "cours": "Atelier de Programmation", "options": ["GLO"]},

    # SEC
    {"code": "SEC346", "ue": "Spécialisation en Cryptographie", "cours": "Spécialisation en Cryptographie", "options": ["SEC"]},
    {"code": "SEC428", "ue": "Logique Théorie des Modèles", "cours": "Logique Théorie des Modèles", "options": ["SEC"]},
    {"code": "SEC438", "ue": "Cryptographie et Codes Correcteurs 1", "cours": "Spécialisation en Cryptographie et Codes Correcteurs 1", "options": ["SEC"]},

    # DSC
    {"code": "DSC356", "ue": "Ingénierie des Connaissances", "cours": "Ingénierie des Connaissances", "options": ["DSC"]},
    {"code": "DSC356", "ue": "Ingénierie des Données", "cours": "Ingénierie des Données", "options": ["DSC"]},
    {"code": "DSC418", "ue": "Technique de Veille", "cours": "Technique de Veille", "options": ["DSC"]},
    {"code": "DSC418", "ue": "Intelligence Économique", "cours": "Intelligence Économique", "options": ["DSC"]},
    {"code": "DSC428", "ue": "Analyse Exploratoire des Données et Régression", "cours": "Analyse Exploratoire des Données et Régression", "options": ["DSC"]},
    {"code": "DSC438", "ue": "Data Mining", "cours": "Data mining (online)", "options": ["DSC"]},
    {"code": "DSC447", "ue": "IOT - Présentation des Projets DSC", "cours": "IOT (Présentation des Projets) - DSC", "options": ["DSC"]},

    # RTE
    {"code": "RTE346", "ue": "Antenne, Propagation des Ondes et Hyperfréquence", "cours": "Antenne, Propagation des Ondes et Hyperfréquence", "options": ["RTE"]},
    {"code": "RTE418", "ue": "Circuit Micro-Onde", "cours": "Circuit Micro-Onde", "options": ["RTE"]},
    {"code": "RTE418", "ue": "Optique guidée", "cours": "Optique guidée", "options": ["RTE"], "vh": "CM:20h, TD:10h, TP:10h, TPE:5h"},
    {"code": "RTE437", "ue": "IOT - Présentation des Projets RTE", "cours": "IOT (Présentation des Projets) - RTE", "options": ["RTE"]},

    # Cours communs
    {"code": "COM356", "ue": "Sécurité des Systèmes d'Informations", "cours": "Sécurité des Systèmes d'Informations", "options": ["GLO", "RTE", "SEC", "DSC"]},
    {"code": "COM448", "ue": "Mathématiques pour Ingénieur", "cours": "Mathématiques pour Ingénieur", "options": ["SEC"]},
    {"code": "COM458", "ue": "Droits des TICs", "cours": "Droits des TICs", "options": ["SEC"]},
]


ENSEIGNANTS = [
    {"username": "awe.s", "nom": "Dr AWE", "prenom": "S.", "email": "awe.s@enspm.cm"},
    {"username": "awe.t", "nom": "Dr AWE", "prenom": "T.", "email": "awe.t@enspm.cm"},
    {"username": "boudjou", "nom": "Dr Boudjou", "prenom": "", "email": "boudjou@enspm.cm"},
    {"username": "nounamo", "nom": "Dr Nounamo", "prenom": "", "email": "nounamo@enspm.cm"},
    {"username": "warda", "nom": "Dr Warda", "prenom": "", "email": "warda@enspm.cm"},
    {"username": "warda.lazare", "nom": "Dr Warda", "prenom": "Lazare", "email": "warda.lazare@enspm.cm"},
    {"username": "gazissou", "nom": "Dr Gazissou", "prenom": "", "email": "gazissou@enspm.cm"},
    {"username": "abdoulaziz", "nom": "Dr Abdoulaziz", "prenom": "Hamayadji", "email": "abdoulaziz.hamayadji@enspm.cm"},
    {"username": "froumsia", "nom": "Dr Froumsia", "prenom": "", "email": "froumsia@enspm.cm"},
    {"username": "guiem", "nom": "Dr Guiem", "prenom": "", "email": "guiem@enspm.cm"},
    {"username": "neneo", "nom": "Dr Neneo", "prenom": "", "email": "neneo@enspm.cm"},
    {"username": "temga", "nom": "M. Temga", "prenom": "", "email": "temga@enspm.cm"},
    {"username": "mamai", "nom": "M. Mamai", "prenom": "", "email": "mamai@enspm.cm"},
    {"username": "touza", "nom": "M. Touza", "prenom": "", "email": "touza@enspm.cm"},
    {"username": "anamak", "nom": "M. Anamak", "prenom": "", "email": "anamak@enspm.cm"},
    {"username": "bayang", "nom": "M. Bayang", "prenom": "", "email": "bayang@enspm.cm"},
    {"username": "douwe", "nom": "M. Douwe", "prenom": "", "email": "douwe@enspm.cm"},
    {"username": "banang", "nom": "Dr Banang", "prenom": "", "email": "banang@enspm.cm"},
    {"username": "ngazia", "nom": "M. Ngazia", "prenom": "", "email": "ngazia@enspm.cm"},
    {"username": "aboubakar", "nom": "M. Aboubakar", "prenom": "", "email": "aboubakar@enspm.cm"},
    {"username": "ombiono", "nom": "Pr Ombiono", "prenom": "", "email": "ombiono@enspm.cm"},
    {"username": "wandji", "nom": "Dr Wandji", "prenom": "", "email": "wandji@enspm.cm"},
    {"username": "gawarai", "nom": "Dr Gawarai", "prenom": "", "email": "gawarai@enspm.cm"},
]


CRENEAUX = [
    # Labo INFOTEL
    {"salle": ("Campus de Sékandé", "Labo INFOTEL"), "jour": Creneau.Jour.MARDI, "debut": "07:30", "fin": "09:30", "cours": ("GLO418", "Développement d'Applications Mobiles"), "enseignant": "touza"},
    {"salle": ("Campus de Sékandé", "Labo INFOTEL"), "jour": Creneau.Jour.MARDI, "debut": "09:30", "fin": "11:30", "cours": ("GLO418", "Développement d'Applications Mobiles"), "enseignant": "touza"},
    {"salle": ("Campus de Sékandé", "Labo INFOTEL"), "jour": Creneau.Jour.JEUDI, "debut": "07:30", "fin": "09:30", "cours": ("RTE418", "Circuit Micro-Onde"), "enseignant": "awe.t"},
    {"salle": ("Campus de Sékandé", "Labo INFOTEL"), "jour": Creneau.Jour.JEUDI, "debut": "09:30", "fin": "11:30", "cours": ("RTE418", "Circuit Micro-Onde"), "enseignant": "awe.t"},
    {"salle": ("Campus de Sékandé", "Labo INFOTEL"), "jour": Creneau.Jour.JEUDI, "debut": "11:30", "fin": "13:30", "cours": ("RTE346", "Antenne, Propagation des Ondes et Hyperfréquence"), "enseignant": "awe.t"},
    {"salle": ("Campus de Sékandé", "Labo INFOTEL"), "jour": Creneau.Jour.JEUDI, "debut": "14:00", "fin": "16:00", "cours": ("RTE346", "Antenne, Propagation des Ondes et Hyperfréquence"), "enseignant": "awe.t"},

    # INFOTEL & ENREN
    {"salle": ("Campus de Sékandé", "INFOTEL & ENREN"), "jour": Creneau.Jour.LUNDI, "debut": "07:30", "fin": "09:30", "cours": ("COM356", "Sécurité des Systèmes d'Informations"), "enseignant": "boudjou"},
    {"salle": ("Campus de Sékandé", "INFOTEL & ENREN"), "jour": Creneau.Jour.LUNDI, "debut": "09:30", "fin": "11:30", "cours": ("COM356", "Sécurité des Systèmes d'Informations"), "enseignant": "boudjou"},
    {"salle": ("Campus de Sékandé", "INFOTEL & ENREN"), "jour": Creneau.Jour.MARDI, "debut": "07:30", "fin": "09:30", "cours": ("ITE355", "Logique Formelle"), "enseignant": "awe.s"},
    {"salle": ("Campus de Sékandé", "INFOTEL & ENREN"), "jour": Creneau.Jour.MARDI, "debut": "09:30", "fin": "11:30", "cours": ("ITE355", "Logique Formelle"), "enseignant": "awe.s"},
    {"salle": ("Campus de Sékandé", "INFOTEL & ENREN"), "jour": Creneau.Jour.VENDREDI, "debut": "07:30", "fin": "09:30", "cours": ("COM356", "Sécurité des Systèmes d'Informations"), "enseignant": "boudjou"},
    {"salle": ("Campus de Sékandé", "INFOTEL & ENREN"), "jour": Creneau.Jour.VENDREDI, "debut": "09:30", "fin": "11:30", "cours": ("COM356", "Sécurité des Systèmes d'Informations"), "enseignant": "boudjou"},
    {"salle": ("Campus de Sékandé", "INFOTEL & ENREN"), "jour": Creneau.Jour.LUNDI, "debut": "11:30", "fin": "13:30", "cours": ("ITE345", "Logiques et Électronique Programmable"), "enseignant": "awe.t"},
    {"salle": ("Campus de Sékandé", "INFOTEL & ENREN"), "jour": Creneau.Jour.LUNDI, "debut": "14:00", "fin": "16:00", "cours": ("ITE345", "Logiques et Électronique Programmable"), "enseignant": "awe.t"},
    {"salle": ("Campus de Sékandé", "INFOTEL & ENREN"), "jour": Creneau.Jour.MARDI, "debut": "11:30", "fin": "13:30", "cours": ("GLO428", "Administration Base de Données"), "enseignant": "mamai"},
    {"salle": ("Campus de Sékandé", "INFOTEL & ENREN"), "jour": Creneau.Jour.JEUDI, "debut": "11:30", "fin": "13:30", "cours": ("SEC346", "Spécialisation en Cryptographie"), "enseignant": "boudjou"},
    {"salle": ("Campus de Sékandé", "INFOTEL & ENREN"), "jour": Creneau.Jour.JEUDI, "debut": "14:00", "fin": "16:00", "cours": ("SEC346", "Spécialisation en Cryptographie"), "enseignant": "boudjou"},
    {"salle": ("Campus de Sékandé", "INFOTEL & ENREN"), "jour": Creneau.Jour.VENDREDI, "debut": "11:30", "fin": "13:30", "cours": ("DSC356", "Ingénierie des Connaissances"), "enseignant": "warda"},
    {"salle": ("Campus de Sékandé", "INFOTEL & ENREN"), "jour": Creneau.Jour.VENDREDI, "debut": "14:00", "fin": "16:00", "cours": ("DSC356", "Ingénierie des Connaissances"), "enseignant": "warda"},

    # IP1
    {"salle": ("Campus de IRAD PITOARE", "IP1"), "jour": Creneau.Jour.LUNDI, "debut": "07:30", "fin": "09:30", "cours": ("DSC418", "Intelligence Économique"), "enseignant": "ombiono"},
    {"salle": ("Campus de IRAD PITOARE", "IP1"), "jour": Creneau.Jour.LUNDI, "debut": "09:30", "fin": "11:30", "cours": ("DSC418", "Intelligence Économique"), "enseignant": "ombiono"},
    {"salle": ("Campus de IRAD PITOARE", "IP1"), "jour": Creneau.Jour.MARDI, "debut": "07:30", "fin": "09:30", "cours": ("DSC418", "Intelligence Économique"), "enseignant": "ombiono"},
    {"salle": ("Campus de IRAD PITOARE", "IP1"), "jour": Creneau.Jour.MARDI, "debut": "09:30", "fin": "11:30", "cours": ("DSC418", "Intelligence Économique"), "enseignant": "ombiono"},
    {"salle": ("Campus de IRAD PITOARE", "IP1"), "jour": Creneau.Jour.JEUDI, "debut": "07:30", "fin": "09:30", "cours": ("DSC418", "Intelligence Économique"), "enseignant": "ombiono"},
    {"salle": ("Campus de IRAD PITOARE", "IP1"), "jour": Creneau.Jour.JEUDI, "debut": "09:30", "fin": "11:30", "cours": ("DSC418", "Intelligence Économique"), "enseignant": "ombiono"},
    {"salle": ("Campus de IRAD PITOARE", "IP1"), "jour": Creneau.Jour.VENDREDI, "debut": "07:30", "fin": "09:30", "cours": ("DSC418", "Intelligence Économique"), "enseignant": "ombiono"},
    {"salle": ("Campus de IRAD PITOARE", "IP1"), "jour": Creneau.Jour.VENDREDI, "debut": "09:30", "fin": "11:30", "cours": ("DSC418", "Intelligence Économique"), "enseignant": "ombiono"},
    {"salle": ("Campus de IRAD PITOARE", "IP1"), "jour": Creneau.Jour.LUNDI, "debut": "11:30", "fin": "13:30", "cours": ("DSC438", "Data mining (online)"), "enseignant": "wandji"},
    {"salle": ("Campus de IRAD PITOARE", "IP1"), "jour": Creneau.Jour.LUNDI, "debut": "14:00", "fin": "16:00", "cours": ("DSC438", "Data mining (online)"), "enseignant": "wandji"},
    {"salle": ("Campus de IRAD PITOARE", "IP1"), "jour": Creneau.Jour.MARDI, "debut": "11:30", "fin": "13:30", "cours": ("DSC428", "Analyse Exploratoire des Données et Régression"), "enseignant": "temga"},
    {"salle": ("Campus de IRAD PITOARE", "IP1"), "jour": Creneau.Jour.MARDI, "debut": "14:00", "fin": "16:00", "cours": ("DSC428", "Analyse Exploratoire des Données et Régression"), "enseignant": "temga"},
    {"salle": ("Campus de IRAD PITOARE", "IP1"), "jour": Creneau.Jour.VENDREDI, "debut": "11:30", "fin": "13:30", "cours": ("GLO346", "Modélisation Informatique"), "enseignant": "bayang"},
    {"salle": ("Campus de IRAD PITOARE", "IP1"), "jour": Creneau.Jour.VENDREDI, "debut": "14:00", "fin": "16:00", "cours": ("GLO346", "Modélisation Informatique"), "enseignant": "bayang"},

    # IP2
    {"salle": ("Campus de IRAD PITOARE", "IP2"), "jour": Creneau.Jour.LUNDI, "debut": "07:30", "fin": "09:30", "cours": ("SEC428", "Logique Théorie des Modèles"), "enseignant": "awe.s"},
    {"salle": ("Campus de IRAD PITOARE", "IP2"), "jour": Creneau.Jour.LUNDI, "debut": "09:30", "fin": "11:30", "cours": ("SEC428", "Logique Théorie des Modèles"), "enseignant": "awe.s"},
    {"salle": ("Campus de IRAD PITOARE", "IP2"), "jour": Creneau.Jour.JEUDI, "debut": "07:30", "fin": "09:30", "cours": ("SEC346", "Spécialisation en Cryptographie"), "enseignant": "anamak"},
    {"salle": ("Campus de IRAD PITOARE", "IP2"), "jour": Creneau.Jour.JEUDI, "debut": "09:30", "fin": "11:30", "cours": ("SEC346", "Spécialisation en Cryptographie"), "enseignant": "anamak"},
    {"salle": ("Campus de IRAD PITOARE", "IP2"), "jour": Creneau.Jour.VENDREDI, "debut": "07:30", "fin": "09:30", "cours": ("RTE418", "Optique guidée"), "enseignant": "gawarai"},
    {"salle": ("Campus de IRAD PITOARE", "IP2"), "jour": Creneau.Jour.VENDREDI, "debut": "09:30", "fin": "11:30", "cours": ("RTE418", "Optique guidée"), "enseignant": "gawarai"},
    {"salle": ("Campus de IRAD PITOARE", "IP2"), "jour": Creneau.Jour.VENDREDI, "debut": "11:30", "fin": "13:30", "cours": ("GLO428", "Administration Base de Données"), "enseignant": "mamai"},
    {"salle": ("Campus de IRAD PITOARE", "IP2"), "jour": Creneau.Jour.VENDREDI, "debut": "14:00", "fin": "16:00", "cours": ("GLO428", "Administration Base de Données"), "enseignant": "mamai"},

    # Incubateur ENSPM
    {"salle": ("Domayo", "Incubateur des entreprises ENSPM"), "jour": Creneau.Jour.LUNDI, "debut": "07:30", "fin": "09:30", "cours": ("GLO438", "Atelier de Programmation"), "enseignant": "abdoulaziz"},
    {"salle": ("Domayo", "Incubateur des entreprises ENSPM"), "jour": Creneau.Jour.LUNDI, "debut": "09:30", "fin": "11:30", "cours": ("GLO438", "Atelier de Programmation"), "enseignant": "abdoulaziz"},
    {"salle": ("Domayo", "Incubateur des entreprises ENSPM"), "jour": Creneau.Jour.LUNDI, "debut": "11:30", "fin": "13:30", "cours": ("GLO438", "Atelier de Programmation"), "enseignant": "abdoulaziz"},
    {"salle": ("Domayo", "Incubateur des entreprises ENSPM"), "jour": Creneau.Jour.LUNDI, "debut": "14:00", "fin": "16:00", "cours": ("GLO438", "Atelier de Programmation"), "enseignant": "abdoulaziz"},
]


def parse_time(value):
    hour, minute = value.split(":")
    return time(int(hour), int(minute))


def sync_options(cours, option_objects):
    cours.options.set(option_objects)


def seed_options():
    print("=== Options ===")
    created_options = {}
    for sigle, data in OPTIONS.items():
        option, created = Option.objects.update_or_create(
            nom=data["nom"],
            defaults={"niveau": data["niveau"]},
        )
        created_options[sigle] = option
        print(f"  {'[CRÉÉ]  ' if created else '[OK]    '} {sigle} - {option.nom}")
    return created_options


def seed_salles():
    print("\n=== Salles ===")
    created_salles = {}
    for data in SALLES:
        salle, created = Salle.objects.update_or_create(
            nom=data["nom"],
            site=data["site"],
            defaults={"capacite": data["capacite"]},
        )
        created_salles[(salle.site, salle.nom)] = salle
        print(f"  {'[CRÉÉ]  ' if created else '[OK]    '} {salle.nom} - {salle.site}")
    return created_salles


def seed_cours(options):
    print("\n=== UE et cours ===")
    created_courses = {}
    for data in COURS:
        ue, _ = UE.objects.update_or_create(
            codeUE=data["code"],
            defaults={"intituleUE": data["ue"]},
        )
        course_options = [options[sigle] for sigle in data["options"]]
        cours, created = Cours.objects.update_or_create(
            ue=ue,
            intitule=data["cours"],
            defaults={
                "volumeHoraire": data.get("vh", VH_STD),
                "option": course_options[0],
                "status": data.get("status", True),
            },
        )
        sync_options(cours, course_options)
        created_courses[(cours.codeCours, cours.intitule)] = cours
        labels = ", ".join(data["options"])
        print(f"  {'[CRÉÉ]  ' if created else '[OK]    '} {cours.codeCours} - {cours.intitule} ({labels})")
    return created_courses


def seed_enseignants():
    print("\n=== Enseignants ===")
    created_teachers = {}
    for data in ENSEIGNANTS:
        user, created = Utilisateur.objects.get_or_create(
            username=data["username"],
            defaults={
                "email": data["email"],
                "nom": data["nom"],
                "prenom": data["prenom"],
                "role": Utilisateur.Role.ENSEIGNANT,
            },
        )
        changed = False
        for field in ("email", "nom", "prenom"):
            if getattr(user, field) != data[field]:
                setattr(user, field, data[field])
                changed = True
        if user.role != Utilisateur.Role.ENSEIGNANT:
            user.role = Utilisateur.Role.ENSEIGNANT
            changed = True
        if created:
            user.set_password(PASSWORD)
            changed = True
        if changed:
            user.save()
        created_teachers[user.username] = user
        print(f"  {'[CRÉÉ]  ' if created else '[OK]    '} {user.username}")
    return created_teachers


def seed_cd():
    print("\n=== Chef de département de démonstration ===")
    cd_user, created = Utilisateur.objects.get_or_create(
        username="cd.demo",
        defaults={
            "email": "cd.demo@enspm.cm",
            "nom": "CD",
            "prenom": "Démo",
            "role": Utilisateur.Role.CD,
            "is_staff": True,
        },
    )
    if created:
        cd_user.set_password(PASSWORD)
        cd_user.save()
    print(f"  {'[CRÉÉ]  ' if created else '[OK]    '} {cd_user.username}")
    return cd_user


def seed_emploi_du_temps(courses, salles, teachers, cd_user):
    print("\n=== Emploi du temps - semaine du 08/06/2026 ===")
    emploi, created = EmploiDuTemps.objects.update_or_create(
        semaine=SEMAINE_EDT,
        defaults={
            "statut": EmploiDuTemps.Statut.BROUILLON,
            "creePar": cd_user,
        },
    )

    deleted_count, _ = emploi.creneaux.all().delete()
    print(f"  {'[CRÉÉ]  ' if created else '[OK]    '} {emploi}")
    print(f"  Anciens créneaux supprimés : {deleted_count}")

    for data in CRENEAUX:
        cours = courses[data["cours"]]
        creneau = Creneau.objects.create(
            emploiDuTemps=emploi,
            jour=data["jour"],
            heureDebut=parse_time(data["debut"]),
            heureFin=parse_time(data["fin"]),
            cours=cours,
            enseignant=teachers[data["enseignant"]],
            salle=salles[data["salle"]],
            option=cours.option,
        )
        creneau.options.set(cours.options_effectives)

    print(f"  Créneaux créés : {len(CRENEAUX)}")
    return emploi


def print_resume():
    print("\n" + "=" * 50)
    print(f"  Options     : {Option.objects.count()}")
    print(f"  Salles      : {Salle.objects.count()}")
    print(f"  UE          : {UE.objects.count()}")
    print(f"  Cours       : {Cours.objects.count()} ({Cours.objects.filter(status=True).count()} actifs)")
    print(f"  Enseignants : {Utilisateur.objects.filter(role=Utilisateur.Role.ENSEIGNANT).count()}")
    print(f"  Créneaux    : {Creneau.objects.count()}")
    print("=" * 50)
    print("Seed terminé avec succès.")
    print(f"Mot de passe temporaire : {PASSWORD}")


options = seed_options()
salles = seed_salles()
courses = seed_cours(options)
teachers = seed_enseignants()
cd = seed_cd()
seed_emploi_du_temps(courses, salles, teachers, cd)
print_resume()
