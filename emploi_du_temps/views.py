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



from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy

from .models import Cours, Option, Salle, Utilisateur


class ConnexionView(LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy("tableau_de_bord")


def accueil(request):
    if request.user.is_authenticated:
        return redirect("tableau_de_bord")
    return render(request, "emploi_du_temps/accueil.html")


@login_required
def tableau_de_bord(request):
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


def deconnexion(request):
    logout(request)
    messages.success(request, "Vous êtes déconnecté.")
    return redirect("login")


# ─────────────────────────────────────────────
#  ENSEIGNANTS
# ─────────────────────────────────────────────

@login_required
def enseignant_liste(request):
    enseignants = Utilisateur.objects.filter(role=Utilisateur.Role.ENSEIGNANT)
    return render(request, "emploi_du_temps/ressources/enseignants/liste.html", {
        "enseignants": enseignants
    })


@login_required
def enseignant_creer(request):
    if request.method == "POST":
        nom = request.POST.get("nom", "").strip()
        prenom = request.POST.get("prenom", "").strip()
        email = request.POST.get("email", "").strip()
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        if not all([nom, prenom, email, username, password]):
            messages.error(request, "Tous les champs sont obligatoires.")
        elif Utilisateur.objects.filter(email=email).exists():
            messages.error(request, "Cet email est déjà utilisé.")
        elif Utilisateur.objects.filter(username=username).exists():
            messages.error(request, "Ce nom d'utilisateur est déjà pris.")
        else:
            Utilisateur.objects.create_user(
                username=username,
                email=email,
                password=password,
                nom=nom,
                prenom=prenom,
                role=Utilisateur.Role.ENSEIGNANT,
            )
            messages.success(request, f"Enseignant {prenom} {nom} créé avec succès.")
            return redirect("enseignant_liste")

    return render(request, "emploi_du_temps/ressources/enseignants/form.html", {
        "action": "Créer", "enseignant": None
    })


@login_required
def enseignant_modifier(request, pk):
    enseignant = get_object_or_404(Utilisateur, pk=pk, role=Utilisateur.Role.ENSEIGNANT)
    if request.method == "POST":
        enseignant.nom = request.POST.get("nom", enseignant.nom).strip()
        enseignant.prenom = request.POST.get("prenom", enseignant.prenom).strip()
        enseignant.email = request.POST.get("email", enseignant.email).strip()
        enseignant.save()
        messages.success(request, "Enseignant modifié avec succès.")
        return redirect("enseignant_liste")
    return render(request, "emploi_du_temps/ressources/enseignants/form.html", {
        "action": "Modifier", "enseignant": enseignant
    })


@login_required
def enseignant_supprimer(request, pk):
    enseignant = get_object_or_404(Utilisateur, pk=pk, role=Utilisateur.Role.ENSEIGNANT)
    if request.method == "POST":
        enseignant.delete()
        messages.success(request, "Enseignant supprimé.")
        return redirect("enseignant_liste")
    return render(request, "emploi_du_temps/ressources/enseignants/confirmer_suppression.html", {
        "enseignant": enseignant
    })


# ─────────────────────────────────────────────
#  COURS
# ─────────────────────────────────────────────

@login_required
def cours_liste(request):
    cours = Cours.objects.select_related("option").all()
    return render(request, "emploi_du_temps/ressources/cours/liste.html", {"cours": cours})


@login_required
def cours_creer(request):
    options = Option.objects.all()
    if request.method == "POST":
        code = request.POST.get("codeCours", "").strip()
        intitule = request.POST.get("intitule", "").strip()
        volume = request.POST.get("volumeHoraire", "").strip()
        option_id = request.POST.get("option")

        if not all([code, intitule, volume, option_id]):
            messages.error(request, "Tous les champs sont obligatoires.")
        elif Cours.objects.filter(codeCours=code).exists():
            messages.error(request, "Ce code cours existe déjà.")
        else:
            Cours.objects.create(
                codeCours=code,
                intitule=intitule,
                volumeHoraire=int(volume),
                option_id=option_id,
            )
            messages.success(request, f"Cours {intitule} créé avec succès.")
            return redirect("cours_liste")

    return render(request, "emploi_du_temps/ressources/cours/form.html", {
        "action": "Créer", "cours": None, "options": options
    })


@login_required
def cours_modifier(request, pk):
    cours = get_object_or_404(Cours, codeCours=pk)
    options = Option.objects.all()
    if request.method == "POST":
        cours.intitule = request.POST.get("intitule", cours.intitule).strip()
        cours.volumeHoraire = int(request.POST.get("volumeHoraire", cours.volumeHoraire))
        cours.option_id = request.POST.get("option", cours.option_id)
        cours.save()
        messages.success(request, "Cours modifié avec succès.")
        return redirect("cours_liste")
    return render(request, "emploi_du_temps/ressources/cours/form.html", {
        "action": "Modifier", "cours": cours, "options": options
    })


@login_required
def cours_supprimer(request, pk):
    cours = get_object_or_404(Cours, codeCours=pk)
    if request.method == "POST":
        cours.delete()
        messages.success(request, "Cours supprimé.")
        return redirect("cours_liste")
    return render(request, "emploi_du_temps/ressources/cours/confirmer_suppression.html", {
        "cours": cours
    })


# ─────────────────────────────────────────────
#  SALLES
# ─────────────────────────────────────────────

@login_required
def salle_liste(request):
    salles = Salle.objects.all()
    return render(request, "emploi_du_temps/ressources/salles/liste.html", {"salles": salles})


@login_required
def salle_creer(request):
    if request.method == "POST":
        nom = request.POST.get("nom", "").strip()
        capacite = request.POST.get("capacite", "").strip()
        site = request.POST.get("site", "").strip()

        if not all([nom, capacite, site]):
            messages.error(request, "Tous les champs sont obligatoires.")
        else:
            Salle.objects.create(nom=nom, capacite=int(capacite), site=site)
            messages.success(request, f"Salle {nom} créée avec succès.")
            return redirect("salle_liste")

    return render(request, "emploi_du_temps/ressources/salles/form.html", {
        "action": "Créer", "salle": None
    })


@login_required
def salle_modifier(request, pk):
    salle = get_object_or_404(Salle, pk=pk)
    if request.method == "POST":
        salle.nom = request.POST.get("nom", salle.nom).strip()
        salle.capacite = int(request.POST.get("capacite", salle.capacite))
        salle.site = request.POST.get("site", salle.site).strip()
        salle.save()
        messages.success(request, "Salle modifiée avec succès.")
        return redirect("salle_liste")
    return render(request, "emploi_du_temps/ressources/salles/form.html", {
        "action": "Modifier", "salle": salle
    })


@login_required
def salle_supprimer(request, pk):
    salle = get_object_or_404(Salle, pk=pk)
    if request.method == "POST":
        salle.delete()
        messages.success(request, "Salle supprimée.")
        return redirect("salle_liste")
    return render(request, "emploi_du_temps/ressources/salles/confirmer_suppression.html", {
        "salle": salle
    })


# ─────────────────────────────────────────────
#  OPTIONS (filières)
# ─────────────────────────────────────────────

@login_required
def option_liste(request):
    options = Option.objects.all()
    return render(request, "emploi_du_temps/ressources/options/liste.html", {"options": options})


@login_required
def option_creer(request):
    if request.method == "POST":
        nom = request.POST.get("nom", "").strip()
        niveau = request.POST.get("niveau", "").strip()

        if not all([nom, niveau]):
            messages.error(request, "Tous les champs sont obligatoires.")
        else:
            Option.objects.create(nom=nom, niveau=int(niveau))
            messages.success(request, f"Option {nom} créée avec succès.")
            return redirect("option_liste")

    return render(request, "emploi_du_temps/ressources/options/form.html", {
        "action": "Créer", "option": None
    })


@login_required
def option_modifier(request, pk):
    option = get_object_or_404(Option, pk=pk)
    if request.method == "POST":
        option.nom = request.POST.get("nom", option.nom).strip()
        option.niveau = int(request.POST.get("niveau", option.niveau))
        option.save()
        messages.success(request, "Option modifiée avec succès.")
        return redirect("option_liste")
    return render(request, "emploi_du_temps/ressources/options/form.html", {
        "action": "Modifier", "option": option
    })


@login_required
def option_supprimer(request, pk):
    option = get_object_or_404(Option, pk=pk)
    if request.method == "POST":
        option.delete()
        messages.success(request, "Option supprimée.")
        return redirect("option_liste")
    return render(request, "emploi_du_temps/ressources/options/confirmer_suppression.html", {
        "option": option
    })    