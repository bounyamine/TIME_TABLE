"""
Script de seed — Ressources ENSPM pour les tests et démonstrations
Utilisation : python manage.py shell < seed_data.py
"""

from emploi_du_temps.models import Option, UE, Cours, Salle, Utilisateur


# ─────────────────────────────────────────────
# 1. OPTIONS (filières / niveaux)
# ─────────────────────────────────────────────

options_data = [
    {"nom": "Sécurité Informatique",             "niveau": 4},  # SEC
    {"nom": "Réseaux et Télécommunications",      "niveau": 4},  # RTE
    {"nom": "Data Science",                       "niveau": 4},  # DSC
    {"nom": "Génie Logiciel",                     "niveau": 4},  # GLO
    {"nom": "Informatique et Télécommunications", "niveau": 3},  # ITE
]

print("=== Création des Options ===")
options = {}
for o in options_data:
    obj, created = Option.objects.get_or_create(
        nom=o["nom"], defaults={"niveau": o["niveau"]}
    )
    options[obj.nom] = obj
    print(f"  {'[CRÉÉ]  ' if created else '[EXISTE]'} {obj}")

SEC = options["Sécurité et Cryptographie"]
RTE = options["Réseaux et Télécommunications"]
DSC = options["Data Science"]
GLO = options["Génie Logiciel"]
ITE = options["Informatique et Télécommunications"]


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
    print(f"  {'[CRÉÉ]  ' if created else '[EXISTE]'} {obj}")


# ─────────────────────────────────────────────
# 3. UE (Unités d'Enseignement)
# ─────────────────────────────────────────────

VH_STD  = "CM:30h, TD:20h, TP:30h, TPE:10h"

# Format : (codeUE, intituleUE, option, volumeHoraire, intitule_cours)
# Chaque UE peut avoir 1 ou 2 cours maximum
ue_cours_data = [

    # ── ITE niveau 3 commun ───────────────────────────────────────────
    ("ITE345", "Réseaux Locaux et Interconnexion",       ITE, VH_STD,  "Réseaux Locaux et Interconnexion"),
    ("ITE345", "Logiques et Électronique Programmable",  ITE, VH_STD,  "Logiques et Électronique Programmable"),
    ("ITE325", "Architecture des Ordinateurs et SI",     ITE, VH_STD,  "Architecture des Ordinateurs et SI"),
    ("ITE355", "Logique Formelle",                       ITE, VH_STD,  "Logique Formelle"),
    ("ITE315", "Programmation Orientée Objet",           ITE, VH_STD,  "Programmation Orientée Objet"),

    # ── GLO Génie Logiciel ────────────────────────────────────────────
    ("GLO346", "Modélisation Informatique",              GLO, VH_STD,  "Modélisation Informatique"),
    ("GLO417", "IOT — Présentation des Projets",         GLO, VH_STD,  "IOT (Présentation des Projets)"),
    ("GLO418", "Développement Web",                      GLO, VH_STD,  "Développement Web"),
    ("GLO418", "Développement d'Applications Mobiles",   GLO, VH_STD,  "Développement d'Applications Mobiles"),
    ("GLO428", "Administration Base de Données",         GLO, VH_STD,  "Administration Base de Données"),

    # ── SEC Sécurité Informatique ─────────────────────────────────────
    ("SEC346",  "Spécialisation en Cryptographie",                         SEC, VH_STD,  "Spécialisation en Cryptographie"),
    ("SEC428",  "Logique Théorie des Modèles",                             SEC, VH_STD,  "Logique Théorie des Modèles"),
    ("SEC438",  "Cryptographie et Codes Correcteurs 1",                    SEC, VH_STD,  "Spécialisation en Cryptographie et Codes Correcteurs 1"),

    # ── DSC Data Science ──────────────────────────────────────────────
    ("DSC356",  "Ingénierie des Connaissances",                            DSC, VH_STD,  "Ingénierie des Connaissances"),
    ("DSC356", "Ingénierie des Données",                                   DSC, VH_STD,  "Ingénierie des Données"),
    ("DSC418",  "Technique de Veille",                                     DSC, VH_STD,  "Technique de Veille"),
    ("DSC428",  "Analyse Exploratoire des Données et Régression",          DSC, VH_STD,  "Analyse Exploratoire des Données et Régression"),
    ("DSC447",  "IOT — Présentation des Projets DSC",                      DSC, VH_STD,  "IOT (Présentation des Projets) — DSC"),

    # ── RTE Réseaux et Télécommunications ─────────────────────────────
    ("RTE346",  "Antenne, Propagation des Ondes et Hyperfréquence",        RTE, VH_STD,  "Antenne, Propagation des Ondes et Hyperfréquence"),
    ("RTE418",  "Circuit Micro-Onde",                                      RTE, VH_STD,  "Circuit Micro-Onde"),
    ("RTE437",  "IOT — Présentation des Projets RTE",                      RTE, VH_STD,  "IOT (Présentation des Projets) — RTE"),

    # ── Cours niveau 4 commun ────────────────────────────────────────────
    ("COM448",  "Mathématiques pour Ingénieur",                            SEC, VH_STD, "Mathématiques pour Ingénieur"),
    ("COM458",  "Droits des TICs",                                         SEC, VH_STD,  "Droits des TICs"),
]

print("\n=== Création des UE et Cours ===")
for code_ue, intitule_ue, option, vh, intitule_cours in ue_cours_data:
    # Créer l'UE
    ue, ue_created = UE.objects.get_or_create(
        codeUE=code_ue,
        defaults={"intituleUE": intitule_ue}
    )

    # Créer le cours lié à cette UE
    cours_qs = Cours.objects.filter(ue=ue, option=option)
    if cours_qs.exists():
        print(f"  [EXISTE] UE {code_ue} → cours déjà présent")
    else:
        cours = Cours(
            ue=ue,
            intitule=intitule_cours,
            volumeHoraire=vh,
            option=option,
        )
        cours.save()
        print(f"  {'[UE CRÉÉE]' if ue_created else '[UE EXISTE]'} {code_ue} → cours '{intitule_cours}' créé")


# ─────────────────────────────────────────────
# 4. ENSEIGNANTS
# ─────────────────────────────────────────────

enseignants_data = [
    {"username": "awe.s",        "nom": "Dr AWE",         "prenom": "S.",         "email": "awe.s@enspm.cm"},
    {"username": "awe.t",        "nom": "Dr AWE",         "prenom": "T.",         "email": "awe.t@enspm.cm"},
    {"username": "boudjou",      "nom": "Dr Boudjou",     "prenom": "",           "email": "boudjou@enspm.cm"},
    {"username": "nounamo",      "nom": "Dr Nounamo",     "prenom": "",           "email": "nounamo@enspm.cm"},
    {"username": "warda",        "nom": "Dr Warda",       "prenom": "",           "email": "warda@enspm.cm"},
    {"username": "warda.lazare", "nom": "Dr Warda",       "prenom": "Lazare",     "email": "warda.lazare@enspm.cm"},
    {"username": "gazissou",     "nom": "Dr Gazissou",    "prenom": "",           "email": "gazissou@enspm.cm"},
    {"username": "abdoulaziz",   "nom": "Dr Abdoulaziz",  "prenom": "Hamayadji",  "email": "abdoulaziz.hamayadji@enspm.cm"},
    {"username": "froumsia",     "nom": "Dr Froumsia",    "prenom": "",           "email": "froumsia@enspm.cm"},
    {"username": "guiem",        "nom": "Dr Guiem",       "prenom": "",           "email": "guiem@enspm.cm"},
    {"username": "neneo",        "nom": "Dr Neneo",       "prenom": "",           "email": "neneo@enspm.cm"},
    {"username": "temga",        "nom": "M. Temga",       "prenom": "",           "email": "temga@enspm.cm"},
    {"username": "mamai",        "nom": "M. Mamai",       "prenom": "",           "email": "mamai@enspm.cm"},
    {"username": "touza",        "nom": "M. Touza",       "prenom": "",           "email": "touza@enspm.cm"},
    {"username": "anamak",       "nom": "M. Anamak",      "prenom": "",           "email": "anamak@enspm.cm"},
    {"username": "bayang",       "nom": "M. Bayang",      "prenom": "",           "email": "bayang@enspm.cm"},
    {"username": "douwe",        "nom": "M. Douwe",       "prenom": "",           "email": "douwe@enspm.cm"},
    {"username": "banang",       "nom": "Dr Banang",      "prenom": "",           "email": "banang@enspm.cm"},
    {"username": "ngazia",       "nom": "M. Ngazia",      "prenom": "",           "email": "ngazia@enspm.cm"},
    {"username": "aboubakar",    "nom": "M. Aboubakar",   "prenom": "",           "email": "aboubakar@enspm.cm"},
]

print("\n=== Création des Enseignants ===")
for e in enseignants_data:
    if Utilisateur.objects.filter(username=e["username"]).exists():
        print(f"  [EXISTE] {e['username']}")
        continue
    user = Utilisateur.objects.create_user(
        username=e["username"],
        email=e["email"],
        password="Enspm2026!",
        nom=e["nom"],
        prenom=e["prenom"],
        role=Utilisateur.Role.ENSEIGNANT,
    )
    print(f"  [CRÉÉ]   {user.username} — {user.nom} {user.prenom}")


# ─────────────────────────────────────────────
# RÉSUMÉ
# ─────────────────────────────────────────────
print("\n" + "=" * 50)
print(f"  Options     : {Option.objects.count()}")
print(f"  Salles      : {Salle.objects.count()}")
print(f"  UE          : {UE.objects.count()}")
print(f"  Cours       : {Cours.objects.count()}")
print(f"  Enseignants : {Utilisateur.objects.filter(role='ENSEIGNANT').count()}")
print("=" * 50)
print("Seed terminé avec succès !")
print("Mot de passe temporaire des enseignants : Enspm2026!")
print("Pensez à le changer depuis l'interface admin.")
