from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from .models import Utilisateur


class ConnexionView(LoginView):
    """Page de connexion en français avec redirection par rôle."""

    template_name = "registration/login.html"
    redirect_authenticated_user = True

    def get_success_url(self) -> str:
        """Rediriger tous les utilisateurs connectés vers leur tableau de bord."""
        return reverse_lazy("tableau_de_bord")


def accueil(request: HttpRequest) -> HttpResponse:
    """Page d'accueil publique de l'application."""
    if request.user.is_authenticated:
        return redirect("tableau_de_bord")
    return render(request, "emploi_du_temps/accueil.html")


@login_required
def tableau_de_bord(request: HttpRequest) -> HttpResponse:
    """Afficher le tableau de bord correspondant au rôle de l'utilisateur."""
    utilisateur = request.user

    if utilisateur.role == Utilisateur.Role.CD:
        template = "emploi_du_temps/tableaux_de_bord/cd.html"
    elif utilisateur.role == Utilisateur.Role.ENSEIGNANT:
        template = "emploi_du_temps/tableaux_de_bord/enseignant.html"
    elif utilisateur.role == Utilisateur.Role.ETUDIANT:
        template = "emploi_du_temps/tableaux_de_bord/etudiant.html"
    else:
        return HttpResponseForbidden("Rôle utilisateur non autorisé.")

    return render(request, template, {"utilisateur": utilisateur})


def deconnexion(request: HttpRequest) -> HttpResponse:
    """Déconnecter l'utilisateur puis revenir à la page de connexion."""
    logout(request)
    messages.success(request, "Vous êtes déconnecté.")
    return redirect("login")