from django.urls import path

from . import views

urlpatterns = [
    path("", views.accueil, name="accueil"),
    path("connexion/", views.ConnexionView.as_view(), name="login"),
    path("deconnexion/", views.deconnexion, name="logout"),
    path("tableau-de-bord/", views.tableau_de_bord, name="tableau_de_bord"),
]