from datetime import date, time

from django.test import TestCase
from django.urls import reverse

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
        self.option, _ = Option.objects.update_or_create(
            sigle="GLO",
            defaults={"nom": "Génie Logiciel"},
        )
        self.etudiant = Utilisateur.objects.create_user(
            username="etudiant",
            email="etudiant@example.com",
            password=PASSWORD,
            nom="Etudiant",
            prenom="GLO",
            role=Utilisateur.Role.ETUDIANT,
            option=self.option,
            niveau=4,
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

    def test_login_accepte_email(self):
        response = self.client.post(
            reverse("login"),
            {"username": self.enseignant.email, "password": PASSWORD},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("tableau_de_bord"))

    def test_inscription_etudiant_enregistre_option_et_niveau(self):
        response = self.client.post(
            reverse("inscription_etudiant"),
            {
                "nom": "Nouveau",
                "prenom": "Compte",
                "email": "nouveau@example.com",
                "username": "nouveau",
                "option_sigle": "GLO",
                "niveau": "4",
                "password": PASSWORD,
            },
        )

        self.assertEqual(response.status_code, 302)
        utilisateur = Utilisateur.objects.get(username="nouveau")
        self.assertEqual(utilisateur.option, self.option)
        self.assertEqual(utilisateur.niveau, 4)

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

    def test_vue_export_pdf_enseignant_retourne_piece_jointe(self):
        self.client.force_login(self.enseignant)

        response = self.client.get(
            reverse("grille_edt_semaine", args=[self.semaine.isoformat()]),
            {"export": "pdf"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF-"))

    def test_vue_export_pdf_etudiant_retourne_piece_jointe(self):
        self.client.force_login(self.etudiant)

        response = self.client.get(
            reverse("grille_edt_semaine", args=[self.semaine.isoformat()]),
            {"export": "pdf"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF-"))

    def test_export_etudiant_autre_niveau_accede_au_pdf_global(self):
        autre_etudiant = Utilisateur.objects.create_user(
            username="autre",
            email="autre@example.com",
            password=PASSWORD,
            nom="Autre",
            prenom="Niveau",
            role=Utilisateur.Role.ETUDIANT,
            option=self.option,
            niveau=3,
        )
        self.client.force_login(autre_etudiant)

        response = self.client.get(
            reverse("grille_edt_semaine", args=[self.semaine.isoformat()]),
            {"export": "pdf"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_export_pdf_respecte_filtre_niveau(self):
        self.client.force_login(self.etudiant)

        response = self.client.get(
            reverse("grille_edt_semaine", args=[self.semaine.isoformat()]),
            {"export": "pdf", "niveau": "3"},
        )

        self.assertEqual(response.status_code, 403)
