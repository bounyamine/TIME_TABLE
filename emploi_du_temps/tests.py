from datetime import date, time

from django.test import TestCase
from django.urls import reverse

from .grille import construire_grilles_par_salle
from .models import Cours, Creneau, EmploiDuTemps, Option, Salle, UE, Utilisateur
from .pdf_export import generer_pdf_emplois_du_temps


PASSWORD = "temporary_password_for_tests_2026!"


class AuthEtExportTests(TestCase):
    def setUp(self):
        self.cd = Utilisateur.objects.create_user(
            username="chef",
            email="chef@example.com",
            password=PASSWORD,
            nom="Chef",
            prenom="Departement",
            role=Utilisateur.Role.CD,
        )
        self.enseignant = Utilisateur.objects.create_user(
            username="enseignant",
            email="enseignant@example.com",
            password=PASSWORD,
            nom="AWE",
            prenom="T.",
            role=Utilisateur.Role.ENSEIGNANT,
        )
        self.enseignant.set_unusable_password()
        self.enseignant.save()
        self.option, _ = Option.objects.update_or_create(
            sigle="GLO",
            defaults={"nom": "Génie Logiciel"},
        )
        self.ue = UE.objects.create(
            codeUE="GLO418",
            intituleUE="Développement d'applications mobiles",
        )
        self.cours = Cours.objects.create(
            ue=self.ue,
            intitule="Développement d'applications mobiles",
            volumeHoraire="CM:30h, TD:20h, TP:30h, TPE:10h",
            niveau=4,
            option=self.option,
        )
        self.cours.options.set([self.option])
        self.salle = Salle.objects.create(
            nom="Labo INFOTEL",
            capacite=40,
            site="Campus de Sékandé",
        )
        self.semaine = date(2026, 6, 1)
        self.emploi = EmploiDuTemps.objects.create(
            semaine=self.semaine,
            statut=EmploiDuTemps.Statut.PUBLIE,
            creePar=self.cd,
        )
        self.creneau = Creneau.objects.create(
            emploiDuTemps=self.emploi,
            jour=Creneau.Jour.MARDI,
            heureDebut=time(7, 30),
            heureFin=time(9, 30),
            cours=self.cours,
            enseignant=self.enseignant,
            option=self.option,
            niveau=4,
            salle=self.salle,
        )
        self.creneau.options.set([self.option])

    def test_login_cd_accepte_email(self):
        response = self.client.post(
            reverse("login"),
            {"username": self.cd.email, "password": PASSWORD},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("tableau_de_bord"))

    def test_login_enseignant_refuse(self):
        response = self.client.post(
            reverse("login"),
            {"username": self.enseignant.email, "password": PASSWORD},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("login"))
        self.assertFalse("_auth_user_id" in self.client.session)

    def test_grille_edt_accessible_sans_connexion(self):
        response = self.client.get(reverse("grille_edt_semaine", args=[self.semaine.isoformat()]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Emploi du Temps")

    def test_grille_edt_masque_brouillon_pour_visiteur_anonyme(self):
        EmploiDuTemps.objects.create(
            semaine=date(2026, 6, 8),
            statut=EmploiDuTemps.Statut.BROUILLON,
            creePar=self.cd,
        )

        response = self.client.get(reverse("grille_edt_semaine", args=["2026-06-08"]))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Brouillon")

    def test_cd_peut_creer_option_personnalisee(self):
        self.client.force_login(self.cd)

        response = self.client.post(
            reverse("option_creer"),
            {"sigle": "IA", "nom": "Intelligence Artificielle"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Option.objects.filter(sigle="IA", nom="Intelligence Artificielle").exists())

    def test_generateur_pdf_global_retourne_un_document_pdf(self):
        export = generer_pdf_emplois_du_temps(self.semaine)

        self.assertEqual(export.nom_fichier, "emplois-du-temps-2026-06-01.pdf")
        self.assertTrue(export.contenu.startswith(b"%PDF-"))
        self.assertTrue(export.contenu.rstrip().endswith(b"%%EOF"))

    def test_vue_export_pdf_cd_retourne_piece_jointe(self):
        self.client.force_login(self.cd)

        response = self.client.get(
            reverse("grille_edt_semaine", args=[self.semaine.isoformat()]),
            {"export": "pdf"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("attachment", response["Content-Disposition"])
        self.assertTrue(response.content.startswith(b"%PDF-"))

    def test_vue_export_pdf_anonyme_retourne_piece_jointe(self):
        response = self.client.get(
            reverse("grille_edt_semaine", args=[self.semaine.isoformat()]),
            {"export": "pdf"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF-"))

    def test_export_pdf_respecte_filtre_niveau(self):
        response = self.client.get(
            reverse("grille_edt_semaine", args=[self.semaine.isoformat()]),
            {"export": "pdf", "niveau": "3"},
        )

        self.assertEqual(response.status_code, 403)

    def test_grille_publique_sans_filtre_salle_affiche_plusieurs_sections(self):
        salle2 = Salle.objects.create(
            nom="AMPHI 150",
            capacite=150,
            site="Campus de Sékandé",
        )
        Creneau.objects.create(
            emploiDuTemps=self.emploi,
            jour=Creneau.Jour.MARDI,
            heureDebut=time(7, 30),
            heureFin=time(9, 30),
            cours=self.cours,
            enseignant=self.enseignant,
            option=self.option,
            niveau=4,
            salle=salle2,
        )

        response = self.client.get(reverse("grille_edt_semaine", args=[self.semaine.isoformat()]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Labo INFOTEL")
        self.assertContains(response, "AMPHI 150")
        self.assertEqual(response.content.count(b"edt-salle-section"), 2)

    def test_grille_publique_avec_filtre_salle_affiche_une_seule_grille(self):
        response = self.client.get(
            reverse("grille_edt_semaine", args=[self.semaine.isoformat()]),
            {"salle_id": self.salle.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Labo INFOTEL")
        self.assertEqual(response.content.count(b"edt-salle-section"), 0)
        self.assertEqual(response.content.count(b"edt-grid"), 1)

    def test_construire_grilles_par_salle_exclut_salles_vides(self):
        Salle.objects.create(
            nom="Salle vide",
            capacite=10,
            site="Campus test",
        )

        grilles = construire_grilles_par_salle(self.semaine)

        noms = [bloc["salle"].nom for bloc in grilles]
        self.assertIn("Labo INFOTEL", noms)
        self.assertNotIn("Salle vide", noms)
