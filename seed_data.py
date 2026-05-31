"""
Script de seed — Ressources ENSPM pour les tests et démonstrations
Utilisation : python manage.py shell < seed_data.py
"""

import django
import os

# ─────────────────────────────────────────────
# 1. OPTIONS (filières / niveaux)
# ─────────────────────────────────────────────
from emploi_du_temps.models import Option, Cours, Salle, Utilisateur

options_data = [
    {"nom": "Sécurité Informatique",          "niveau": 4},  # SEC
    {"nom": "Réseaux et Télécommunications",  "niveau": 4},  # RTE
    {"nom": "Data Science",                   "niveau": 4},  # DSC
    {"nom": "Génie Logiciel",                 "niveau": 4},  # GLO
    {"nom": "Informatique et Télécommunications", "niveau": 3},  # ITE (3e année commune)
]

print("=== Création des Options ===")
options = {}
for o in options_data:
    obj, created = Option.objects.get_or_create(nom=o["nom"], defaults={"niveau": o["niveau"]})
    options[obj.nom] = obj
    print(f"  {'[CRÉÉ]' if created else '[EXISTE]'} {obj}")


# ─────────────────────────────────────────────
# 2. SALLES
# ─────────────────────────────────────────────
salles_data = [
    {"nom": "Labo INFOTEL",              "capacite": 40,  "site": "Campus de Sékandé"},
    {"nom": "INFOTEL & ENREN",           "capacite": 80,  "site": "Campus de Sékandé"},
    {"nom": "AMPHI 150",                 "capacite": 150, "site": "Campus de Sékandé"},
    {"nom": "IP1",                       "capacite": 60,  "site": "Campus de IRAD PITOARE"},
    {"nom": "IP2",                       "capacite": 60,  "site": "Campus de IRAD PITOARE"},
    {"nom": "NS7",                       "capacite": 50,  "site": "Campus de OURO-TCHEDE"},
    {"nom": "Orange Digital Club (ODC)", "capacite": 50,  "site": "Campus de KONGOLA-DJOULGOUF-KODEK"},
]

print("\n=== Création des Salles ===")
for s in salles_data:
    obj, created = Salle.objects.get_or_create(
        nom=s["nom"], site=s["site"],
        defaults={"capacite": s["capacite"]}
    )
    print(f"  {'[CRÉÉ]' if created else '[EXISTE]'} {obj}")


# ─────────────────────────────────────────────
# 3. COURS  (code, intitulé, volume, option)
# ─────────────────────────────────────────────
# Raccourcis vers les options
SEC = options["Sécurité Informatique"]
RTE = options["Réseaux et Télécommunications"]
DSC = options["Data Science"]
GLO = options["Génie Logiciel"]
ITE = options["Informatique et Télécommunications"]

VH_STD  = "CM:30h, TD:20h, TP:30h, TPE:10h"   # volume standard
VH_MATH = "CM:20h, TD:10h, TP:10h, TPE:5h"    # Maths ingénieur

cours_data = [
    # ── Cours ITE (niveau 3 commun) ──────────────────────────────────
    {"code": "ITE345",  "intitule": "Réseaux Locaux et Interconnexion",          "vh": VH_STD,  "option": ITE},
    {"code": "ITE345b", "intitule": "Logiques et Électronique Programmable",     "vh": VH_STD,  "option": ITE},
    {"code": "ITE345c", "intitule": "Architecture des Ordinateurs et SI",        "vh": VH_STD,  "option": ITE},
    {"code": "ITE355",  "intitule": "Logique Formelle",                          "vh": VH_STD,  "option": ITE},
    {"code": "ITE355b", "intitule": "Programmation Orientée Objet",              "vh": VH_STD,  "option": ITE},

    # ── Cours GLO (Génie Logiciel) ───────────────────────────────────
    {"code": "GLO346",  "intitule": "Modélisation Informatique",                 "vh": VH_STD,  "option": GLO},
    {"code": "GLO417",  "intitule": "IOT (Présentation des Projets)",            "vh": VH_STD,  "option": GLO},
    {"code": "GLO418",  "intitule": "Développement Web",                         "vh": VH_STD,  "option": GLO},
    {"code": "GLO418b", "intitule": "Développement d'Applications Mobiles",      "vh": VH_STD,  "option": GLO},
    {"code": "GLO428",  "intitule": "Administration Base de Données",            "vh": VH_STD,  "option": GLO},

    # ── Cours SEC (Sécurité) ─────────────────────────────────────────
    {"code": "SEC346",  "intitule": "Spécialisation en Cryptographie",           "vh": VH_STD,  "option": SEC},
    {"code": "SEC428",  "intitule": "Logique Théorie des Modèles",               "vh": VH_STD,  "option": SEC},
    {"code": "SEC438",  "intitule": "Spécialisation en Cryptographie et Codes Correcteurs 1", "vh": VH_STD, "option": SEC},

    # ── Cours DSC (Data Science) ─────────────────────────────────────
    {"code": "DSC356",  "intitule": "Ingénierie des Connaissances",              "vh": VH_STD,  "option": DSC},
    {"code": "DSC356b", "intitule": "Ingénierie des Données",                   "vh": VH_STD,  "option": DSC},
    {"code": "DSC418",  "intitule": "Technique de Veille",                       "vh": VH_STD,  "option": DSC},
    {"code": "DSC428",  "intitule": "Analyse Exploratoire des Données et Régression", "vh": VH_STD, "option": DSC},
    {"code": "DSC447",  "intitule": "IOT (Présentation des Projets) — DSC",     "vh": VH_STD,  "option": DSC},

    # ── Cours RTE (Réseaux/Télécoms) ─────────────────────────────────
    {"code": "RTE346",  "intitule": "Antenne, Propagation des Ondes et Hyperfréquence", "vh": VH_STD, "option": RTE},
    {"code": "RTE418",  "intitule": "Circuit Micro-Onde",                        "vh": VH_STD,  "option": RTE},
    {"code": "RTE437",  "intitule": "IOT (Présentation des Projets) — RTE",     "vh": VH_STD,  "option": RTE},

    # ── Cours transversaux (SEC/RTE/DSC/GLO) ────────────────────────
    {"code": "COM448",  "intitule": "Mathématiques pour Ingénieur",              "vh": VH_MATH, "option": SEC},
    {"code": "COM458",  "intitule": "Droits des TICs",                           "vh": VH_STD,  "option": SEC},
    {"code": "AHN4",    "intitule": "BDA",                                       "vh": VH_STD,  "option": DSC},
]

print("\n=== Création des Cours ===")
for c in cours_data:
    obj, created = Cours.objects.get_or_create(
        codeCours=c["code"],
        defaults={
            "intitule":      c["intitule"],
            "volumeHoraire": c["vh"],
            "option":        c["option"],
        }
    )
    print(f"  {'[CRÉÉ]' if created else '[EXISTE]'} {obj}")


# ─────────────────────────────────────────────
# 4. ENSEIGNANTS
# ─────────────────────────────────────────────
enseignants_data = [
    {"username": "awe.s",          "nom": "AWE",          "prenom": "S.",         "email": "awe.s@enspm.cm"},
    {"username": "awe.t",          "nom": "AWE",          "prenom": "T.",         "email": "awe.t@enspm.cm"},
    {"username": "boudjou",        "nom": "BOUDJOU",      "prenom": "",           "email": "boudjou@enspm.cm"},
    {"username": "nounamo",        "nom": "NOUNAMO",      "prenom": "",           "email": "nounamo@enspm.cm"},
    {"username": "warda",          "nom": "WARDA",        "prenom": "",           "email": "warda@enspm.cm"},
    {"username": "warda.lazare",   "nom": "WARDA",        "prenom": "LAZARE",     "email": "warda.lazare@enspm.cm"},
    {"username": "gazissou",       "nom": "GAZISSOU",     "prenom": "",           "email": "gazissou@enspm.cm"},
    {"username": "abdoulaziz",     "nom": "ABDOULAZIZ",   "prenom": "HAMAYADJI", "email": "abdoulaziz.hamayadji@enspm.cm"},
    {"username": "froumsia",       "nom": "FROUMSIA",     "prenom": "",           "email": "froumsia@enspm.cm"},
    {"username": "guiem",          "nom": "GUIEM",        "prenom": "",           "email": "guiem@enspm.cm"},
    {"username": "neneo",          "nom": "NENEO",        "prenom": "",           "email": "neneo@enspm.cm"},
    {"username": "temga",          "nom": "TEMGA",        "prenom": "",           "email": "temga@enspm.cm"},
    {"username": "mamai",          "nom": "MAMAI",        "prenom": "",           "email": "mamai@enspm.cm"},
    {"username": "touza",          "nom": "TOUZA",        "prenom": "",           "email": "touza@enspm.cm"},
    {"username": "anamak",         "nom": "ANAMAK",       "prenom": "",           "email": "anamak@enspm.cm"},
    {"username": "bayang",         "nom": "BAYANG",       "prenom": "",           "email": "bayang@enspm.cm"},
    {"username": "douwe",          "nom": "DOUWE",        "prenom": "",           "email": "douwe@enspm.cm"},
    {"username": "banang",         "nom": "BANANG",       "prenom": "",           "email": "banang@enspm.cm"},
    {"username": "ngazia",         "nom": "NGAZIA",       "prenom": "",           "email": "ngazia@enspm.cm"},
    {"username": "aboubakar",      "nom": "ABOUBAKAR",    "prenom": "",           "email": "aboubakar@enspm.cm"},
]

print("\n=== Création des Enseignants ===")
for e in enseignants_data:
    if Utilisateur.objects.filter(username=e["username"]).exists():
        print(f"  [EXISTE] {e['username']}")
        continue
    user = Utilisateur.objects.create_user(
        username=e["username"],
        email=e["email"],
        password="Enspm2026!",   # mot de passe temporaire uniforme
        nom=e["nom"],
        prenom=e["prenom"],
        role=Utilisateur.Role.ENSEIGNANT,
    )
    print(f"  [CRÉÉ]   {user.username} — {user.nom} {user.prenom}")


# ─────────────────────────────────────────────
# RÉSUMÉ
# ─────────────────────────────────────────────
print("\n" + "="*50)
print(f"  Options    : {Option.objects.count()}")
print(f"  Salles     : {Salle.objects.count()}")
print(f"  Cours      : {Cours.objects.count()}")
print(f"  Enseignants: {Utilisateur.objects.filter(role='ENSEIGNANT').count()}")
print("="*50)
print("Seed terminé avec succès !")
print("Mot de passe temporaire des enseignants : Enspm2026!")
print("Pensez à le changer depuis l'interface admin.")
