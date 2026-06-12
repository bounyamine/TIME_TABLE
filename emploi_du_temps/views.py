from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import ProtectedError, Q
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from emploi_du_temps.forms import (
    CreneauDirectForm,
    EmploiDuTempsForm,
    UtilisateurRoleCreationForm,
    UtilisateurRoleModificationForm,
)
from emploi_du_temps.grille import JOURS_EDT, PLAGES_HORAIRES, construire_grille_semaine, trouver_plage
from emploi_du_temps.pdf_export import generer_pdf_emplois_du_temps
from emploi_du_temps.permissions import cd_requis
from .models import Cours, Creneau, EmploiDuTemps, Option, Salle, UE, Utilisateur


class ConnexionView(LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True

    def get_success_url(self) -> str:
        return reverse_lazy("tableau_de_bord")


def accueil(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("tableau_de_bord")
    return render(request, "emploi_du_temps/accueil.html")


def inscription_etudiant(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("tableau_de_bord")

    if request.method == "POST":
        form = UtilisateurRoleCreationForm(request.POST, role=Utilisateur.Role.ETUDIANT)
        if form.is_valid():
            form.save()
            messages.success(request, "Votre compte étudiant a été créé. Vous pouvez maintenant vous connecter.")
            return redirect("login")
    else:
        form = UtilisateurRoleCreationForm(role=Utilisateur.Role.ETUDIANT)

    return render(request, "registration/inscription_etudiant.html", {"form": form})


@login_required
def tableau_de_bord(request: HttpRequest) -> HttpResponse:
    utilisateur = request.user
    context = {"utilisateur": utilisateur}

    if utilisateur.role == Utilisateur.Role.CD:
        template = "emploi_du_temps/tableaux_de_bord/cd.html"
        context.update({
            "nb_enseignants": Utilisateur.objects.filter(role=Utilisateur.Role.ENSEIGNANT).count(),
            "nb_etudiants": Utilisateur.objects.filter(role=Utilisateur.Role.ETUDIANT).count(),
            "nb_cours": Cours.objects.count(),
            "nb_ues": UE.objects.count(),
            "nb_salles": Salle.objects.count(),
            "nb_options": Option.objects.count(),
            "nb_emplois": EmploiDuTemps.objects.count(),
            "nb_brouillons": EmploiDuTemps.objects.filter(statut=EmploiDuTemps.Statut.BROUILLON).count(),
            "nb_publies": EmploiDuTemps.objects.filter(statut=EmploiDuTemps.Statut.PUBLIE).count(),
            "emplois_recents": EmploiDuTemps.objects.select_related("creePar")[:5],
        })
    elif utilisateur.role == Utilisateur.Role.ENSEIGNANT:
        template = "emploi_du_temps/tableaux_de_bord/enseignant.html"
        context["emplois_du_temps"] = EmploiDuTemps.objects.filter(
            statut=EmploiDuTemps.Statut.PUBLIE,
            creneaux__enseignant=utilisateur,
        ).distinct()
    elif utilisateur.role == Utilisateur.Role.ETUDIANT:
        template = "emploi_du_temps/tableaux_de_bord/etudiant.html"
        emplois_du_temps = EmploiDuTemps.objects.filter(statut=EmploiDuTemps.Statut.PUBLIE)
        if utilisateur.option_id:
            emplois_du_temps = emplois_du_temps.filter(
                Q(creneaux__option=utilisateur.option) | Q(creneaux__options=utilisateur.option)
            ).distinct()
        else:
            emplois_du_temps = emplois_du_temps.none()
        context["emplois_du_temps"] = emplois_du_temps
    else:
        return HttpResponseForbidden("Rôle utilisateur non autorisé.")

    return render(request, template, context)


@login_required
def deconnexion(request: HttpRequest) -> HttpResponse:
    logout(request)
    messages.success(request, "Vous êtes déconnecté.")
    return redirect("login")


# ─────────────────────────────────────────────
#  GRILLE EDT PAR SEMAINE (style PHP)
# ─────────────────────────────────────────────

def _get_lundi(semaine_str: str | None) -> date:
    """Retourne le lundi de la semaine donnée ou de la semaine courante."""
    if semaine_str:
        try:
            d = date.fromisoformat(semaine_str)
            return d - timedelta(days=d.weekday())
        except ValueError:
            pass
    today = date.today()
    return today - timedelta(days=today.weekday())


@login_required
def grille_edt(request: HttpRequest, semaine: str | None = None) -> HttpResponse:
    """Grille EDT par semaine — vue principale (équivalent PHP /edt)."""
    semaine_date = _get_lundi(semaine or request.GET.get("semaine"))
    salles = Salle.objects.all()
    salle_id_param = request.GET.get("salle_id", "")
    try:
        salle_id = int(salle_id_param) if salle_id_param else None
    except (TypeError, ValueError):
        salle_id = None
    if salle_id and not salles.filter(pk=salle_id).exists():
        salle_id = None
    if not salle_id:
        premiere_salle = salles.first()
        salle_id = premiere_salle.pk if premiere_salle else None
    
    est_cd = request.user.role == Utilisateur.Role.CD

    if request.GET.get("export") == "pdf":
        if not est_cd:
            return HttpResponseForbidden("Seul le chef de département peut exporter le planning global.")
        export = generer_pdf_emplois_du_temps(semaine_date)
        response = HttpResponse(export.contenu, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{export.nom_fichier}"'
        return response
    

    lignes = construire_grille_semaine(
        semaine_date,
        salle_id=salle_id,
        utilisateur=request.user,
    )

    # Semaines déjà planifiées
    semaines_dispo_qs = EmploiDuTemps.objects.all()
    if not est_cd:
        semaines_dispo_qs = semaines_dispo_qs.filter(statut=EmploiDuTemps.Statut.PUBLIE)
        if request.user.role == Utilisateur.Role.ENSEIGNANT:
            semaines_dispo_qs = semaines_dispo_qs.filter(creneaux__enseignant=request.user)
        elif request.user.role == Utilisateur.Role.ETUDIANT:
            if request.user.option_id:
                semaines_dispo_qs = semaines_dispo_qs.filter(
                    Q(creneaux__option=request.user.option) | Q(creneaux__options=request.user.option)
                )
            else:
                semaines_dispo_qs = semaines_dispo_qs.none()
    semaines_dispo = (
        semaines_dispo_qs.values_list("semaine", flat=True)
        .distinct()
        .order_by("semaine")
    )

    # Emplois de cette semaine (pour publication / export)
    emplois_semaine = EmploiDuTemps.objects.filter(semaine=semaine_date).prefetch_related("creneaux")
    if not est_cd:
        emplois_semaine = emplois_semaine.filter(statut=EmploiDuTemps.Statut.PUBLIE)
        if request.user.role == Utilisateur.Role.ENSEIGNANT:
            emplois_semaine = emplois_semaine.filter(creneaux__enseignant=request.user).distinct()
        elif request.user.role == Utilisateur.Role.ETUDIANT:
            if request.user.option_id:
                emplois_semaine = emplois_semaine.filter(
                    Q(creneaux__option=request.user.option) | Q(creneaux__options=request.user.option)
                ).distinct()
            else:
                emplois_semaine = emplois_semaine.none()

    return render(request, "emploi_du_temps/grille/index.html", {
        "semaine": semaine_date,
        "semaine_prev": semaine_date - timedelta(weeks=1),
        "semaine_next": semaine_date + timedelta(weeks=1),
        "jours": JOURS_EDT,
        "lignes": lignes,
        "plages": PLAGES_HORAIRES,
        "salles": salles,
        "salle_id_actif": salle_id,
        "semaines_dispo": semaines_dispo,
        "est_cd": est_cd,
        "emplois_semaine": emplois_semaine,
        "cours_modal": Cours.objects.select_related("ue", "option").filter(
            Q(status=True) | Q(creneaux__emploiDuTemps__semaine=semaine_date)
        ).prefetch_related("options").distinct(),
        "enseignants_modal": Utilisateur.objects.filter(
            Q(is_active=True) | Q(creneauxEnseignes__emploiDuTemps__semaine=semaine_date),
            role=Utilisateur.Role.ENSEIGNANT,
        ).distinct().order_by("nom", "prenom"),
        "plages_modal": [p for p in PLAGES_HORAIRES if not p.get("pause")],
    })


@cd_requis
def ajouter_creneau_grille(request: HttpRequest) -> HttpResponse:
    """Formulaire d'ajout d'un créneau depuis la grille"""
    semaine_str = request.GET.get("semaine") or request.POST.get("semaine") or str(date.today())
    semaine_date = _get_lundi(semaine_str)

    # Préremplissage si clic sur une cellule
    salle_initiale = request.GET.get("salle") or request.GET.get("salle_id") or ""
    if salle_initiale:
        try:
            salle_initiale = str(Salle.objects.get(pk=int(salle_initiale)).pk)
        except (Salle.DoesNotExist, TypeError, ValueError):
            salle_initiale = ""

    initial = {
        "semaine": semaine_date,
        "salle": salle_initiale,
        "jour": request.GET.get("jour", ""),
        "plage": request.GET.get("plage", ""),
    }

    if request.method == "POST":
        form = CreneauDirectForm(request.POST)
        if form.is_valid():
            # On récupère ou crée l'EmploiDuTemps brouillon global pour cette semaine.
            # Toujours utiliser LE LUNDI de la semaine comme clé
            semaine_lundi = _get_lundi(str(form.cleaned_data["semaine"]))
            emploi, _ = EmploiDuTemps.objects.get_or_create(
                semaine=semaine_lundi,
                defaults={"creePar": request.user, "statut": EmploiDuTemps.Statut.BROUILLON},
            )
            try:
                plage = trouver_plage(form.cleaned_data["plage"])
                creneau = Creneau(
                    emploiDuTemps=emploi,
                    option=form.cleaned_data["cours"].option,
                    jour=form.cleaned_data["jour"],
                    heureDebut=plage["debut"],
                    heureFin=plage["fin"],
                    cours=form.cleaned_data["cours"],
                    enseignant=form.cleaned_data["enseignant"],
                    salle=form.cleaned_data["salle"],
                )
                creneau.full_clean()
                creneau.save()
                creneau.options.set(creneau.cours.options_effectives)
                if request.headers.get("x-requested-with") == "XMLHttpRequest":
                    return JsonResponse({
                        "message": "Créneau ajouté.",
                        "redirect_url": _url_grille_emploi(emploi, creneau.salle_id),
                        "delete_url": f"/emplois-du-temps/grille/creneaux/{creneau.pk}/supprimer/",
                    })
                messages.success(request, "Créneau ajouté avec succès.")
            except ValidationError as e:
                if request.headers.get("x-requested-with") == "XMLHttpRequest":
                    return JsonResponse({"message": " ".join(e.messages)}, status=400)
                for msg in e.messages:
                    messages.error(request, msg)
                return render(request, "emploi_du_temps/grille/formulaire.html", {
                    "form": form,
                    "semaine": semaine_date,
                    "titre": "Ajouter un créneau",
                    "plages": PLAGES_HORAIRES,
                    "jours": JOURS_EDT,
                })
            return redirect(f"/emplois-du-temps/grille/{semaine_lundi.isoformat()}/?salle_id={form.cleaned_data['salle'].pk}")

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            errors = []
            for field_errors in form.errors.values():
                errors.extend(field_errors)
            return JsonResponse({
                "message": " ".join(errors) or "Formulaire invalide.",
                "errors": form.errors,
            }, status=400)

        return render(request, "emploi_du_temps/grille/formulaire.html", {
            "form": form,
            "semaine": semaine_date,
            "titre": "Ajouter un créneau",
            "plages": PLAGES_HORAIRES,
            "jours": JOURS_EDT,
        })

    form = CreneauDirectForm(initial=initial)
    return render(request, "emploi_du_temps/grille/formulaire.html", {
        "form": form,
        "semaine": semaine_date,
        "titre": "Ajouter un créneau",
        "plages": PLAGES_HORAIRES,
        "jours": JOURS_EDT,
    })


@cd_requis
def modifier_creneau_grille(request: HttpRequest, pk: int) -> HttpResponse:
    """Modifier un créneau depuis la grille."""
    creneau = get_object_or_404(
        Creneau.objects.select_related(
            "emploiDuTemps", "cours", "enseignant", "salle", "option"
        ).prefetch_related("options"),
        pk=pk,
    )
    semaine = creneau.emploiDuTemps.semaine

    if request.method == "POST":
        form = CreneauDirectForm(request.POST, instance=creneau)
        if form.is_valid():
            try:
                plage = trouver_plage(form.cleaned_data["plage"])
                creneau.jour = form.cleaned_data["jour"]
                creneau.heureDebut = plage["debut"]
                creneau.heureFin = plage["fin"]
                creneau.cours = form.cleaned_data["cours"]
                creneau.option = form.cleaned_data["cours"].option
                creneau.enseignant = form.cleaned_data["enseignant"]
                creneau.salle = form.cleaned_data["salle"]
                creneau.full_clean()
                creneau.save()
                creneau.options.set(creneau.cours.options_effectives)
                messages.success(request, "Créneau modifié avec succès.")
            except ValidationError as e:
                if request.headers.get("x-requested-with") == "XMLHttpRequest":
                    return JsonResponse({"message": " ".join(e.messages)}, status=400)
                for msg in e.messages:
                    messages.error(request, msg)
                return render(request, "emploi_du_temps/grille/formulaire.html", {
                    "form": form, "semaine": semaine, "titre": "Modifier un créneau",
                    "creneau": creneau, "plages": PLAGES_HORAIRES, "jours": JOURS_EDT,
                })
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({
                    "message": "Créneau modifié.",
                    "redirect_url": _url_grille_emploi(creneau.emploiDuTemps, creneau.salle_id),
                })
            return redirect(f"/emplois-du-temps/grille/{semaine.isoformat()}/?salle_id={creneau.salle_id}")
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            errors = []
            for field_errors in form.errors.values():
                errors.extend(field_errors)
            return JsonResponse({
                "message": " ".join(errors) or "Formulaire invalide.",
                "errors": form.errors,
            }, status=400)
    else:
        # Préremplir le formulaire avec les valeurs existantes
        # Trouver la plage correspondante
        plage_id = ""
        for p in PLAGES_HORAIRES:
            if p["debut"] == creneau.heureDebut and p["fin"] == creneau.heureFin:
                plage_id = p["id"]
                break
        form = CreneauDirectForm(initial={
            "semaine": semaine.isoformat(),
            "jour": creneau.jour,
            "plage": plage_id,
            "cours": creneau.cours,
            "enseignant": creneau.enseignant,
            "salle": creneau.salle,
        }, instance=creneau)

    return render(request, "emploi_du_temps/grille/formulaire.html", {
        "form": form, "semaine": semaine, "titre": "Modifier un créneau",
        "creneau": creneau, "plages": PLAGES_HORAIRES, "jours": JOURS_EDT,
    })


@cd_requis
def supprimer_creneau_grille(request: HttpRequest, pk: int) -> HttpResponse:
    """Supprimer un créneau depuis la grille."""
    creneau = get_object_or_404(Creneau.objects.select_related("emploiDuTemps", "salle"), pk=pk)
    semaine = creneau.emploiDuTemps.semaine
    emploi = creneau.emploiDuTemps
    salle_id = creneau.salle_id
    if request.method == "POST":
        creneau.delete()
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({
                "message": "Créneau supprimé.",
                "redirect_url": _url_grille_emploi(emploi, salle_id),
            })
        messages.success(request, "Créneau supprimé.")
        return redirect(f"/emplois-du-temps/grille/{semaine.isoformat()}/?salle_id={salle_id}")
    return render(request, "emploi_du_temps/grille/confirmer_suppression.html", {
        "creneau": creneau, "semaine": semaine,
    })


@cd_requis
def publier_semaine(request: HttpRequest) -> HttpResponse:
    """Publie tous les emplois du temps brouillons de la semaine donnée."""
    if request.method != "POST":
        return redirect("grille_edt")
    semaine_str = request.POST.get("semaine", "")
    semaine_lundi = _get_lundi(semaine_str)
    emplois = EmploiDuTemps.objects.filter(semaine=semaine_lundi, statut=EmploiDuTemps.Statut.BROUILLON)
    count = emplois.update(statut=EmploiDuTemps.Statut.PUBLIE, datePublication=timezone.now())
    if count:
        messages.success(request, f"{count} emploi(s) du temps publié(s) pour la semaine du {semaine_lundi.strftime('%d/%m/%Y')}.")
    else:
        messages.info(request, "Aucun brouillon à publier pour cette semaine.")
    return redirect(f"/emplois-du-temps/grille/{semaine_lundi.isoformat()}/")


@cd_requis
def depublier_semaine(request: HttpRequest) -> HttpResponse:
    """Repasse les emplois du temps de la semaine en brouillon."""
    if request.method != "POST":
        return redirect("grille_edt")
    semaine_str = request.POST.get("semaine", "")
    semaine_lundi = _get_lundi(semaine_str)
    count = EmploiDuTemps.objects.filter(semaine=semaine_lundi, statut=EmploiDuTemps.Statut.PUBLIE).update(statut=EmploiDuTemps.Statut.BROUILLON)
    messages.success(request, f"{count} emploi(s) repassé(s) en brouillon.")
    return redirect(f"/emplois-du-temps/grille/{semaine_lundi.isoformat()}/")


@cd_requis
def ajax_conflits(request: HttpRequest) -> JsonResponse:
    """Vérification AJAX des conflits (équivalent PHP /edt/check-conflicts)."""
    if request.method != "POST":
        return JsonResponse({"conflits": [], "count": 0})

    semaine_str = request.POST.get("semaine", "")
    cours_id = request.POST.get("cours_id")
    enseignant_id = request.POST.get("enseignant_id")
    salle_id = request.POST.get("salle_id")
    plage_id = request.POST.get("plage", "")
    jour = request.POST.get("jour", "")
    exclude_id = request.POST.get("exclude_id")

    plage = trouver_plage(plage_id)
    if not plage or not semaine_str or not jour:
        return JsonResponse({"conflits": [], "count": 0})

    try:
        semaine_date = _get_lundi(semaine_str)
    except Exception:
        return JsonResponse({"conflits": [], "count": 0})

    qs = Creneau.objects.filter(
        emploiDuTemps__semaine=semaine_date,
        jour=jour,
        heureDebut__lt=plage["fin"],
        heureFin__gt=plage["debut"],
    ).select_related("cours", "enseignant", "salle", "option").prefetch_related("options")

    if exclude_id:
        try:
            qs = qs.exclude(pk=int(exclude_id))
        except (TypeError, ValueError):
            pass

    conflits = []
    if salle_id:
        try:
            qs_salle = qs.filter(salle_id=int(salle_id))
        except (TypeError, ValueError):
            qs_salle = Creneau.objects.none()
        for c in qs_salle:
            conflits.append({
                "type": "salle",
                "message": f"Conflit de SALLE : « {c.salle.nom} » est déjà occupée le {c.get_jour_display()} de {c.heureDebut.strftime('%H:%M')} à {c.heureFin.strftime('%H:%M')} par le cours {c.cours.intitule} ({c.enseignant.nom} {c.enseignant.prenom}).",
            })
    if enseignant_id:
        try:
            qs_enseignant = qs.filter(enseignant_id=int(enseignant_id))
        except (TypeError, ValueError):
            qs_enseignant = Creneau.objects.none()
        for c in qs_enseignant:
            conflits.append({
                "type": "enseignant",
                "message": f"Conflit d'ENSEIGNANT : {c.enseignant.nom} {c.enseignant.prenom} est déjà programmé(e) le {c.get_jour_display()} de {c.heureDebut.strftime('%H:%M')} à {c.heureFin.strftime('%H:%M')} en salle {c.salle.nom} pour le cours {c.cours.intitule}.",
            })
    option_ids = []
    if cours_id:
        option_ids = list(Cours.objects.filter(pk=cours_id).values_list("options__id", flat=True))
        if not option_ids:
            option_principale = Cours.objects.filter(pk=cours_id).values_list("option_id", flat=True).first()
            option_ids = [option_principale] if option_principale else []
    if option_ids:
        for c in qs.filter(Q(option_id__in=option_ids) | Q(options__id__in=option_ids)).distinct():
            conflits.append({
                "type": "option",
                "message": f"Conflit OPTION : « {c.options_affichage} » a déjà un cours le {c.get_jour_display()} de {c.heureDebut.strftime('%H:%M')} à {c.heureFin.strftime('%H:%M')} ({c.cours.intitule} — salle {c.salle.nom}).",
            })

    # Dédupliquer
    seen = set()
    unique = []
    for conf in conflits:
        if conf["message"] not in seen:
            seen.add(conf["message"])
            unique.append(conf)

    return JsonResponse({"conflits": unique, "count": len(unique)})


@login_required
def ajax_cours_par_option(request: HttpRequest, option_id: int) -> JsonResponse:
    """Retourne les cours d'une option (équivalent PHP /edt/cours-par-filiere)."""
    cours = list(
        Cours.objects.filter(Q(option_id=option_id) | Q(options__id=option_id), status=True).distinct().values(
            "id",
            "codeCours",
            "intitule",
            "ue_id",
        )
    )
    return JsonResponse(cours, safe=False)


def _url_grille_emploi(emploi, salle_id=None):
    url = f"/emplois-du-temps/grille/{emploi.semaine.isoformat()}/"
    if salle_id:
        url += f"?salle_id={salle_id}"
    return url


def _reponse_edition_cellule(request, emploi, message, statut=200, salle_id=None, extra=None):
    redirect_url = _url_grille_emploi(emploi, salle_id)
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        payload = {"message": message, "redirect_url": redirect_url}
        if extra:
            payload.update(extra)
        return JsonResponse(payload, status=statut)
    if statut >= 400:
        messages.error(request, message)
    else:
        messages.success(request, message)
    return redirect(redirect_url)


def _salle_cible_depuis_post(request: HttpRequest, salle_actuelle: Salle) -> Salle | None:
    salle_id = request.POST.get("salle_id") or request.POST.get("salle")
    if not salle_id:
        return salle_actuelle
    try:
        return Salle.objects.get(pk=salle_id)
    except (Salle.DoesNotExist, TypeError, ValueError):
        return None


@cd_requis
def deplacer_creneau(request: HttpRequest, pk: int) -> HttpResponse:
    creneau = get_object_or_404(Creneau.objects.select_related("emploiDuTemps", "salle"), pk=pk)
    emploi = creneau.emploiDuTemps
    if request.method != "POST":
        return redirect(_url_grille_emploi(emploi, creneau.salle_id))
    plage = trouver_plage(request.POST.get("plage", ""))
    jour = request.POST.get("jour", "")
    if not plage or plage.get("pause") or jour not in dict(JOURS_EDT):
        return _reponse_edition_cellule(request, emploi, "Plage ou jour invalide.", 400, creneau.salle_id)
    salle = _salle_cible_depuis_post(request, creneau.salle)
    if salle is None:
        return _reponse_edition_cellule(request, emploi, "Salle invalide.", 400, creneau.salle_id)
    creneau.jour = jour
    creneau.heureDebut = plage["debut"]
    creneau.heureFin = plage["fin"]
    creneau.salle = salle
    try:
        creneau.full_clean()
    except ValidationError as e:
        return _reponse_edition_cellule(request, emploi, " ".join(e.messages), 400, salle.pk)
    creneau.save()
    return _reponse_edition_cellule(request, emploi, "Créneau déplacé.", salle_id=salle.pk)


@cd_requis
def copier_creneau(request: HttpRequest, pk: int) -> HttpResponse:
    source = get_object_or_404(
        Creneau.objects.select_related("emploiDuTemps", "salle").prefetch_related("options"),
        pk=pk,
    )
    emploi = source.emploiDuTemps
    if request.method != "POST":
        return redirect(_url_grille_emploi(emploi, source.salle_id))
    plage = trouver_plage(request.POST.get("plage", ""))
    jour = request.POST.get("jour", "")
    if not plage or plage.get("pause") or jour not in dict(JOURS_EDT):
        return _reponse_edition_cellule(request, emploi, "Plage ou jour invalide.", 400, source.salle_id)
    salle = _salle_cible_depuis_post(request, source.salle)
    if salle is None:
        return _reponse_edition_cellule(request, emploi, "Salle invalide.", 400, source.salle_id)
    copie = Creneau(
        emploiDuTemps=emploi, cours=source.cours,
        enseignant=source.enseignant, salle=salle, option=source.option,
        jour=jour, heureDebut=plage["debut"], heureFin=plage["fin"],
    )
    try:
        copie.full_clean()
    except ValidationError as e:
        return _reponse_edition_cellule(request, emploi, " ".join(e.messages), 400, salle.pk)
    copie.save()
    options_source = list(source.options.all()) or source.cours.options_effectives
    copie.options.set(options_source or [source.option])
    return _reponse_edition_cellule(
        request,
        emploi,
        "Créneau copié.",
        salle_id=salle.pk,
        extra={"delete_url": f"/emplois-du-temps/grille/creneaux/{copie.pk}/supprimer/"},
    )


@cd_requis
@require_POST
def restaurer_creneau(request: HttpRequest) -> HttpResponse:
    semaine_date = _get_lundi(request.POST.get("semaine"))
    plage = trouver_plage(request.POST.get("plage", ""))
    jour = request.POST.get("jour", "")
    if not plage or plage.get("pause") or jour not in dict(JOURS_EDT):
        return JsonResponse({"message": "Plage ou jour invalide."}, status=400)

    try:
        cours = Cours.objects.get(pk=request.POST.get("cours_id"))
        enseignant = Utilisateur.objects.get(pk=request.POST.get("enseignant_id"), role=Utilisateur.Role.ENSEIGNANT)
        salle = Salle.objects.get(pk=request.POST.get("salle_id"))
    except (Cours.DoesNotExist, Utilisateur.DoesNotExist, Salle.DoesNotExist, TypeError, ValueError):
        return JsonResponse({"message": "Données du créneau invalides."}, status=400)

    emploi, _ = EmploiDuTemps.objects.get_or_create(
        semaine=semaine_date,
        defaults={"creePar": request.user, "statut": EmploiDuTemps.Statut.BROUILLON},
    )
    creneau = Creneau(
        emploiDuTemps=emploi,
        jour=jour,
        heureDebut=plage["debut"],
        heureFin=plage["fin"],
        cours=cours,
        enseignant=enseignant,
        salle=salle,
        option=cours.option,
    )
    try:
        creneau.full_clean()
    except ValidationError as e:
        return JsonResponse({"message": " ".join(e.messages)}, status=400)
    creneau.save()
    options_ids = [
        int(option_id)
        for option_id in request.POST.get("options_ids", "").split(",")
        if option_id.strip().isdigit()
    ]
    options = list(Option.objects.filter(pk__in=options_ids)) if options_ids else []
    creneau.options.set(options or cours.options_effectives)
    return JsonResponse({
        "message": "Créneau restauré.",
        "redirect_url": _url_grille_emploi(emploi, salle.pk),
    })


# ─────────────────────────────────────────────
#  RESSOURCES
# ─────────────────────────────────────────────

RESSOURCES_PAR_PAGE = 7


def _paginer_ressources(request: HttpRequest, queryset, par_page: int = RESSOURCES_PAR_PAGE):
    paginator = Paginator(queryset, par_page)
    page_obj = paginator.get_page(request.GET.get("page"))
    query_params = request.GET.copy()
    query_params.pop("page", None)
    return page_obj, query_params.urlencode()


def _redirect_apres_action(request: HttpRequest, fallback: str):
    next_url = request.POST.get("next", "")
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(next_url)
    return redirect(fallback)


def _utilisateur_liste(request, role: str, template: str, context_name: str):
    utilisateurs = Utilisateur.objects.filter(role=role).select_related("option").order_by("nom", "prenom", "username")
    page_obj, pagination_query = _paginer_ressources(request, utilisateurs)
    context = {
        context_name: page_obj.object_list,
        "page_obj": page_obj,
        "pagination_query": pagination_query,
    }
    if role == Utilisateur.Role.ETUDIANT:
        context["options"] = Option.objects.all()
    return render(request, template, context)


def _utilisateur_creer(request, role: str, template: str, redirect_name: str, label: str):
    if request.method == "POST":
        form = UtilisateurRoleCreationForm(request.POST, role=role)
        if form.is_valid():
            utilisateur = form.save()
            messages.success(request, f"{label} {utilisateur.nom} {utilisateur.prenom} créé avec succès.")
            return redirect(redirect_name)
    else:
        form = UtilisateurRoleCreationForm(role=role)
    return render(request, template, {"action": "Créer", "form": form, "label": label})


def _utilisateur_modifier(request, pk: int, role: str, template: str, redirect_name: str, label: str):
    utilisateur = get_object_or_404(Utilisateur, pk=pk, role=role)
    if request.method == "POST":
        form = UtilisateurRoleModificationForm(request.POST, instance=utilisateur, role=role)
        if form.is_valid():
            form.save()
            messages.success(request, f"{label} modifié avec succès.")
            return redirect(redirect_name)
    else:
        form = UtilisateurRoleModificationForm(instance=utilisateur, role=role)
    return render(request, template, {"action": "Modifier", "form": form, "label": label, "utilisateur": utilisateur})


def _utilisateur_supprimer(request, pk: int, role: str, template: str, redirect_name: str, label: str, context_name: str):
    utilisateur = get_object_or_404(Utilisateur, pk=pk, role=role)
    if request.method == "POST":
        try:
            utilisateur.delete()
        except ProtectedError:
            messages.error(request, f"Impossible de supprimer ce {label.lower()} car il est lié à des créneaux.")
            return redirect(redirect_name)
        messages.success(request, f"{label} supprimé.")
        return redirect(redirect_name)
    return render(request, template, {context_name: utilisateur, "label": label})


@cd_requis
def enseignant_liste(request):
    return _utilisateur_liste(
        request,
        Utilisateur.Role.ENSEIGNANT,
        "emploi_du_temps/ressources/enseignants/liste.html",
        "enseignants",
    )


@cd_requis
def enseignant_creer(request):
    return _utilisateur_creer(
        request,
        Utilisateur.Role.ENSEIGNANT,
        "emploi_du_temps/ressources/enseignants/form.html",
        "enseignant_liste",
        "Enseignant",
    )


@cd_requis
def enseignant_modifier(request, pk):
    return _utilisateur_modifier(
        request,
        pk,
        Utilisateur.Role.ENSEIGNANT,
        "emploi_du_temps/ressources/enseignants/form.html",
        "enseignant_liste",
        "Enseignant",
    )


@cd_requis
@require_POST
def enseignant_basculer_statut(request, pk):
    enseignant = get_object_or_404(Utilisateur, pk=pk, role=Utilisateur.Role.ENSEIGNANT)
    enseignant.is_active = not enseignant.is_active
    enseignant.save(update_fields=["is_active"])

    statut = "activé" if enseignant.is_active else "désactivé"
    messages.success(request, f"Enseignant {enseignant.nom} {enseignant.prenom} {statut}.")
    return _redirect_apres_action(request, "enseignant_liste")


@cd_requis
def enseignant_supprimer(request, pk):
    return _utilisateur_supprimer(
        request,
        pk,
        Utilisateur.Role.ENSEIGNANT,
        "emploi_du_temps/ressources/enseignants/confirmer_suppression.html",
        "enseignant_liste",
        "Enseignant",
        "enseignant",
    )


@cd_requis
def etudiant_liste(request):
    return _utilisateur_liste(
        request,
        Utilisateur.Role.ETUDIANT,
        "emploi_du_temps/ressources/etudiants/liste.html",
        "etudiants",
    )


@cd_requis
def etudiant_creer(request):
    return _utilisateur_creer(
        request,
        Utilisateur.Role.ETUDIANT,
        "emploi_du_temps/ressources/etudiants/form.html",
        "etudiant_liste",
        "Étudiant",
    )


@cd_requis
def etudiant_modifier(request, pk):
    return _utilisateur_modifier(
        request,
        pk,
        Utilisateur.Role.ETUDIANT,
        "emploi_du_temps/ressources/etudiants/form.html",
        "etudiant_liste",
        "Étudiant",
    )


@cd_requis
@require_POST
def etudiant_basculer_statut(request, pk):
    etudiant = get_object_or_404(Utilisateur, pk=pk, role=Utilisateur.Role.ETUDIANT)
    etudiant.is_active = not etudiant.is_active
    etudiant.save(update_fields=["is_active"])

    statut = "activé" if etudiant.is_active else "désactivé"
    messages.success(request, f"Étudiant {etudiant.nom} {etudiant.prenom} {statut}.")
    return _redirect_apres_action(request, "etudiant_liste")


@cd_requis
def etudiant_supprimer(request, pk):
    return _utilisateur_supprimer(
        request,
        pk,
        Utilisateur.Role.ETUDIANT,
        "emploi_du_temps/ressources/etudiants/confirmer_suppression.html",
        "etudiant_liste",
        "Étudiant",
        "etudiant",
    )


@cd_requis
def ue_liste(request):
    ues = UE.objects.prefetch_related("cours").all()
    page_obj, pagination_query = _paginer_ressources(request, ues)
    return render(request, "emploi_du_temps/ressources/ues/liste.html", {
        "ues": page_obj.object_list,
        "page_obj": page_obj,
        "pagination_query": pagination_query,
    })


@cd_requis
def ue_creer(request):
    if request.method == "POST":
        code = request.POST.get("codeUE", "").strip().upper()
        intitule = request.POST.get("intituleUE", "").strip()
        if not all([code, intitule]):
            messages.error(request, "Tous les champs sont obligatoires.")
        elif UE.objects.filter(codeUE=code).exists():
            messages.error(request, "Ce code UE existe déjà.")
        else:
            UE.objects.create(codeUE=code, intituleUE=intitule)
            messages.success(request, f"UE {code} créée avec succès.")
            return redirect("ue_liste")
    return render(request, "emploi_du_temps/ressources/ues/form.html", {"action": "Créer", "ue": None})


@cd_requis
def ue_modifier(request, pk):
    ue = get_object_or_404(UE, codeUE=pk)
    if request.method == "POST":
        ue.intituleUE = request.POST.get("intituleUE", ue.intituleUE).strip()
        if not ue.intituleUE:
            messages.error(request, "L’intitulé UE est obligatoire.")
        else:
            ue.save()
            messages.success(request, "UE modifiée avec succès.")
            return redirect("ue_liste")
    return render(request, "emploi_du_temps/ressources/ues/form.html", {"action": "Modifier", "ue": ue})


@cd_requis
def ue_supprimer(request, pk):
    ue = get_object_or_404(UE, codeUE=pk)
    if request.method == "POST":
        try:
            ue.delete()
        except ProtectedError:
            messages.error(request, "Impossible de supprimer cette UE car elle est liée à des cours.")
            return redirect("ue_liste")
        messages.success(request, "UE supprimée.")
        return redirect("ue_liste")
    return render(request, "emploi_du_temps/ressources/ues/confirmer_suppression.html", {"ue": ue})


@cd_requis
def cours_liste(request):
    cours = Cours.objects.select_related("ue", "option").prefetch_related("options").all()
    page_obj, pagination_query = _paginer_ressources(request, cours)
    return render(request, "emploi_du_temps/ressources/cours/liste.html", {
        "cours": page_obj.object_list,
        "page_obj": page_obj,
        "pagination_query": pagination_query,
        "options": Option.objects.all(),
        "ues": UE.objects.prefetch_related("cours").all(),
    })

@cd_requis
def cours_creer(request):
    options = Option.objects.all()
    ues = UE.objects.all()
    if request.method == "POST":
        ue_id = request.POST.get("ue")
        intitule = request.POST.get("intitule", "").strip()
        volume = request.POST.get("volumeHoraire", "").strip()
        option_ids = request.POST.getlist("options") or request.POST.getlist("option")
        if not all([ue_id, intitule]) or not option_ids:
            messages.error(request, "Tous les champs marqués * sont obligatoires.")
        else:
            cours = Cours(ue_id=ue_id, intitule=intitule, volumeHoraire=volume, option_id=option_ids[0])
            try:
                cours.full_clean()
                cours.save()
                cours.options.set(options.filter(pk__in=option_ids))
            except ValidationError as e:
                for msg in e.messages:
                    messages.error(request, msg)
            else:
                messages.success(request, f"Cours {intitule} créé avec succès.")
                return redirect("cours_liste")
    return render(request, "emploi_du_temps/ressources/cours/form.html", {"action": "Créer", "cours": None, "options": options, "ues": ues})

@cd_requis
def cours_modifier(request, pk):
    cours = get_object_or_404(Cours.objects.select_related("ue", "option").prefetch_related("options"), pk=pk)
    options = Option.objects.all()
    ues = UE.objects.all()
    if request.method == "POST":
        option_ids = request.POST.getlist("options") or request.POST.getlist("option")
        cours.ue_id = request.POST.get("ue", cours.ue_id)
        cours.intitule = request.POST.get("intitule", cours.intitule).strip()
        cours.volumeHoraire = request.POST.get("volumeHoraire", cours.volumeHoraire).strip()
        if option_ids:
            cours.option_id = option_ids[0]
        try:
            cours.full_clean()
            cours.save()
            if option_ids:
                cours.options.set(options.filter(pk__in=option_ids))
                for creneau in Creneau.objects.filter(cours=cours):
                    creneau.option = cours.option
                    creneau.save(update_fields=["option"])
                    creneau.options.set(cours.options_effectives)
        except ValidationError as e:
            for msg in e.messages:
                messages.error(request, msg)
        else:
            messages.success(request, "Cours modifié avec succès.")
            return redirect("cours_liste")
    return render(request, "emploi_du_temps/ressources/cours/form.html", {"action": "Modifier", "cours": cours, "options": options, "ues": ues})


@cd_requis
@require_POST
def cours_basculer_statut(request, pk):
    cours = get_object_or_404(Cours, pk=pk)
    cours.status = not cours.status
    cours.save(update_fields=["status"])

    statut = "activé" if cours.status else "désactivé"
    messages.success(request, f"Cours {cours.intitule} {statut}.")
    return _redirect_apres_action(request, "cours_liste")


@cd_requis
def cours_supprimer(request, pk):
    cours = get_object_or_404(Cours, pk=pk)
    if request.method == "POST":
        try:
            cours.delete()
        except ProtectedError:
            messages.error(request, "Impossible de supprimer ce cours car il est utilisé dans des créneaux.")
            return redirect("cours_liste")
        messages.success(request, "Cours supprimé.")
        return redirect("cours_liste")
    return render(request, "emploi_du_temps/ressources/cours/confirmer_suppression.html", {"cours": cours})

@cd_requis
def salle_liste(request):
    salles = Salle.objects.all()
    page_obj, pagination_query = _paginer_ressources(request, salles)
    return render(request, "emploi_du_temps/ressources/salles/liste.html", {
        "salles": page_obj.object_list,
        "page_obj": page_obj,
        "pagination_query": pagination_query,
    })

@cd_requis
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
    return render(request, "emploi_du_temps/ressources/salles/form.html", {"action": "Créer", "salle": None})

@cd_requis
def salle_modifier(request, pk):
    salle = get_object_or_404(Salle, pk=pk)
    if request.method == "POST":
        salle.nom = request.POST.get("nom", salle.nom).strip()
        salle.capacite = int(request.POST.get("capacite", salle.capacite))
        salle.site = request.POST.get("site", salle.site).strip()
        salle.save()
        messages.success(request, "Salle modifiée avec succès.")
        return redirect("salle_liste")
    return render(request, "emploi_du_temps/ressources/salles/form.html", {"action": "Modifier", "salle": salle})

@cd_requis
def salle_supprimer(request, pk):
    salle = get_object_or_404(Salle, pk=pk)
    if request.method == "POST":
        try:
            salle.delete()
        except ProtectedError:
            messages.error(request, "Impossible de supprimer cette salle car elle est utilisée dans des créneaux.")
            return redirect("salle_liste")
        messages.success(request, "Salle supprimée.")
        return redirect("salle_liste")
    return render(request, "emploi_du_temps/ressources/salles/confirmer_suppression.html", {"salle": salle})

@cd_requis
def option_liste(request):
    options = Option.objects.all()
    page_obj, pagination_query = _paginer_ressources(request, options)
    return render(request, "emploi_du_temps/ressources/options/liste.html", {
        "options": page_obj.object_list,
        "page_obj": page_obj,
        "pagination_query": pagination_query,
    })

@cd_requis
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
    return render(request, "emploi_du_temps/ressources/options/form.html", {"action": "Créer", "option": None})

@cd_requis
def option_modifier(request, pk):
    option = get_object_or_404(Option, pk=pk)
    if request.method == "POST":
        option.nom = request.POST.get("nom", option.nom).strip()
        option.niveau = int(request.POST.get("niveau", option.niveau))
        option.save()
        messages.success(request, "Option modifiée avec succès.")
        return redirect("option_liste")
    return render(request, "emploi_du_temps/ressources/options/form.html", {"action": "Modifier", "option": option})

@cd_requis
def option_supprimer(request, pk):
    option = get_object_or_404(Option, pk=pk)
    if request.method == "POST":
        try:
            option.delete()
        except ProtectedError:
            messages.error(request, "Impossible de supprimer cette option car elle est liée à des cours, créneaux ou étudiants.")
            return redirect("option_liste")
        messages.success(request, "Option supprimée.")
        return redirect("option_liste")
    return render(request, "emploi_du_temps/ressources/options/confirmer_suppression.html", {"option": option})
