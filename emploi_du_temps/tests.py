from datetime import date, time

from django.test import TestCase
from django.urls import reverse

from .models import Cours, Creneau, EmploiDuTemps, Option, Salle, Utilisateur
from .pdf_export import generer_pdf_emplois_du_temps


class ExportPDFTests(TestCase):
     def setUp(self):
        self.cd = Utilisateur.objects.create_user(
            username="chef",
            email="chef@example.com",
            password="temporary_password_for_tests", # Modifiez cette chaîne
            nom="Chef",
            prenom="Departement",
            role=Utilisateur.Role.CD,
        )
        self.enseignant = Utilisateur.objects.create_user(
            username="enseignant",
            email="enseignant@example.com",
            password="temporary_password_for_tests", # Modifiez cette chaîne
            nom="AWE",
            prenom="T.",
            role=Utilisateur.Role.ENSEIGNANT,
        )
        # ... le reste de votre code reste inchangé
        self.option = Option.objects.create(nom="Génie Logiciel", niveau=4)
        self.cours = Cours.objects.create(
            codeCours="GLO418",
            intitule="Développement d'applications mobiles",
            volumeHoraire="CM:30h, TD:20h, TP:30h, TPE:10h",
            option=self.option,
        )
        self.salle = Salle.objects.create(
            nom="Labo INFOTEL",
            capacite=40,
            site="Campus de Sékandé",
        )
        self.semaine = date(2026, 6, 1)
        self.emploi = EmploiDuTemps.objects.create(
            semaine=self.semaine,
            statut=EmploiDuTemps.Statut.BROUILLON,
            creePar=self.cd,
        )
        Creneau.objects.create(
            emploiDuTemps=self.emploi,
            jour=Creneau.Jour.MARDI,
            heureDebut=time(7, 30),
            heureFin=time(9, 30),
            cours=self.cours,
            enseignant=self.enseignant,
            option=self.option,
            salle=self.salle,
        )

    def test_generateur_pdf_global_retourne_un_document_pdf(self):
        export = generer_pdf_emplois_du_temps(self.semaine)

        self.assertEqual(export.nom_fichier, "emplois-du-temps-2026-06-01.pdf")
        self.assertTrue(export.contenu.startswith(b"%PDF-"))
        self.assertIn(b"/Type /Page", export.contenu)

    def test_vue_export_pdf_retourne_piece_jointe(self):
        self.client.force_login(self.cd)

        response = self.client.get(
            reverse("grille_edt_semaine", args=[self.semaine.isoformat()]),
            {"export": "pdf"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("attachment", response["Content-Disposition"])
        self.assertTrue(response.content.startswith(b"%PDF-"))
