from django.urls import path
from . import views

urlpatterns = [
    # ── Authentification ──────────────────────────
    path("", views.accueil, name="accueil"),
    path("connexion/", views.ConnexionView.as_view(), name="login"),
    path("deconnexion/", views.deconnexion, name="logout"),
    path("tableau-de-bord/", views.tableau_de_bord, name="tableau_de_bord"),

    # ── Enseignants ───────────────────────────────
    path("enseignants/", views.enseignant_liste, name="enseignant_liste"),
    path("enseignants/nouveau/", views.enseignant_creer, name="enseignant_creer"),
    path("enseignants/<int:pk>/modifier/", views.enseignant_modifier, name="enseignant_modifier"),
    path("enseignants/<int:pk>/supprimer/", views.enseignant_supprimer, name="enseignant_supprimer"),

    # ── Cours ─────────────────────────────────────
    path("cours/", views.cours_liste, name="cours_liste"),
    path("cours/nouveau/", views.cours_creer, name="cours_creer"),
    path("cours/<str:pk>/modifier/", views.cours_modifier, name="cours_modifier"),
    path("cours/<str:pk>/supprimer/", views.cours_supprimer, name="cours_supprimer"),

    # ── Salles ────────────────────────────────────
    path("salles/", views.salle_liste, name="salle_liste"),
    path("salles/nouvelle/", views.salle_creer, name="salle_creer"),
    path("salles/<int:pk>/modifier/", views.salle_modifier, name="salle_modifier"),
    path("salles/<int:pk>/supprimer/", views.salle_supprimer, name="salle_supprimer"),

    # ── Options (filières) ────────────────────────
    path("options/", views.option_liste, name="option_liste"),
    path("options/nouvelle/", views.option_creer, name="option_creer"),
    path("options/<int:pk>/modifier/", views.option_modifier, name="option_modifier"),
    path("options/<int:pk>/supprimer/", views.option_supprimer, name="option_supprimer"),
]