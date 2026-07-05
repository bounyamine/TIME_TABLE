# TIME_TABLE — Gestion Emploi du Temps

Application Django simple de gestion d'emploi du temps académique.

## Règles métier

- Le Chef de département gère les ressources, crée, modifie, supprime et publie les emplois du temps.
- La consultation des emplois du temps publiés est ouverte à tous, sans connexion.
- Seul le Chef de département se connecte à la plateforme.

## Structure simplifiée

- `config/settings.py` : configuration Django unique et simple avec SQLite.
- `emploi_du_temps/` : application métier avec les modèles en français : `Utilisateur`, `CD`, `Enseignant`, `Option`, `Cours`, `Salle`, `EmploiDuTemps`, `Creneau`, `Conflit`.
- `requirements.txt` : dépendance minimale du projet.

## Clonage du projet

```bash
git clone https://github.com/obouny/TIME_TABLE.git
cd TIME_TABLE
```

## Commandes à lancer

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py shell < seed_data.py
python manage.py runserver
```

## Commandes de vérification

```bash
python manage.py check
python -m compileall config emploi_du_temps
python manage.py test emploi_du_temps
```
