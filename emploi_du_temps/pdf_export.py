"""Génération PDF officielle des emplois du temps par site et salle.

Le module n'utilise aucune dépendance externe : il écrit directement un PDF simple
avec les primitives texte/traits nécessaires pour obtenir un rendu imprimable en
paysage, proche des modèles fournis.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from io import BytesIO
from textwrap import wrap

from django.db.models import QuerySet
from django.utils.text import slugify

from .grille import JOURS_EDT, PLAGES_HORAIRES
from .models import Creneau, Salle

MM = 72 / 25.4
PAGE_WIDTH = 297 * MM
PAGE_HEIGHT = 210 * MM

VERT_ENSPM = (0.0, 0.651, 0.318)
VERT_CLAIR = (0.439, 0.788, 0.263)
VIOLET_ENSPM = (0.439, 0.188, 0.627)
BLEU_PAUSE = (0.741, 0.843, 0.933)
ROUGE = (1.0, 0.0, 0.0)
NOIR = (0.0, 0.0, 0.0)
BLANC = (1.0, 1.0, 1.0)
BLEU_LIEN = (0.0, 0.655, 1.0)
GRIS_CERCLE = (0.53, 0.53, 0.53)

MOIS_FR = [
    "Janvier",
    "Février",
    "Mars",
    "Avril",
    "Mai",
    "Juin",
    "Juillet",
    "Août",
    "Septembre",
    "Octobre",
    "Novembre",
    "Décembre",
]

SEMESTRES = {
    1: "Semestre II",
    2: "Semestre II",
    3: "Semestre II",
    4: "Semestre II",
    5: "Semestre II",
    6: "Semestre II",
    7: "Semestre II",
    8: "Semestre I",
    9: "Semestre I",
    10: "Semestre I",
    11: "Semestre I",
    12: "Semestre I",
}


@dataclass(frozen=True)
class PageSalle:
    """Données nécessaires pour dessiner une page de planning."""

    site: str
    salle: Salle
    lignes: list[dict]


@dataclass(frozen=True)
class ExportPlanning:
    """Résultat binaire et nom de fichier de l'export PDF."""

    contenu: bytes
    nom_fichier: str


class MiniPDF:
    """Petit générateur PDF vectoriel suffisant pour l'export des emplois du temps."""

    def __init__(self) -> None:
        self.pages: list[bytes] = []
        self.commands: list[bytes] = []

    def add_page(self) -> None:
        if self.commands:
            self.pages.append(b"\n".join(self.commands))
            self.commands = []

    def finish(self) -> bytes:
        if self.commands:
            self.pages.append(b"\n".join(self.commands))
            self.commands = []

        objects: list[bytes] = []
        catalog_id = 1
        pages_id = 2
        font_regular_id = 3
        font_bold_id = 4
        font_oblique_id = 5
        next_id = 6
        page_ids = []
        content_ids = []

        for content in self.pages:
            page_ids.append(next_id)
            content_ids.append(next_id + 1)
            next_id += 2

        objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
        kids = b" ".join(f"{page_id} 0 R".encode() for page_id in page_ids)
        objects.append(
            b"<< /Type /Pages /Kids [ " + kids + b" ] /Count " + str(len(page_ids)).encode() + b" >>"
        )
        objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
        objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")
        objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Oblique /Encoding /WinAnsiEncoding >>")

        for page_id, content_id, content in zip(page_ids, content_ids, self.pages):
            resources = (
                b"<< /Font << /F1 " + str(font_regular_id).encode() + b" 0 R "
                b"/F2 " + str(font_bold_id).encode() + b" 0 R "
                b"/F3 " + str(font_oblique_id).encode() + b" 0 R >> >>"
            )
            objects.append(
                b"<< /Type /Page /Parent " + str(pages_id).encode() + b" 0 R "
                b"/MediaBox [0 0 " + _num(PAGE_WIDTH) + b" " + _num(PAGE_HEIGHT) + b"] "
                b"/Resources " + resources + b" /Contents " + str(content_id).encode() + b" 0 R >>"
            )
            objects.append(
                b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream"
            )

        output = BytesIO()
        output.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = [0]
        for index, obj in enumerate(objects, start=1):
            offsets.append(output.tell())
            output.write(f"{index} 0 obj\n".encode())
            output.write(obj)
            output.write(b"\nendobj\n")
        xref = output.tell()
        output.write(f"xref\n0 {len(objects) + 1}\n".encode())
        output.write(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            output.write(f"{offset:010d} 00000 n \n".encode())
        output.write(
            b"trailer\n<< /Size " + str(len(objects) + 1).encode() + b" /Root "
            + str(catalog_id).encode() + b" 0 R >>\nstartxref\n" + str(xref).encode() + b"\n%%EOF\n"
        )
        return output.getvalue()

    def line(self, x1: float, y1: float, x2: float, y2: float, color=NOIR, width: float = 1.0) -> None:
        self.commands.append(_stroke(color) + b" " + _num(width) + b" w " + _num(x1) + b" " + _num(y1) + b" m " + _num(x2) + b" " + _num(y2) + b" l S")

    def rect(self, x: float, y: float, w: float, h: float, stroke=NOIR, fill=None, width: float = 1.0) -> None:
        prefix = _stroke(stroke) + b" " + _num(width) + b" w "
        if fill:
            prefix += _fill(fill) + b" "
        op = b"B" if fill else b"S"
        self.commands.append(prefix + _num(x) + b" " + _num(y) + b" " + _num(w) + b" " + _num(h) + b" re " + op)

    def round_rect(self, x: float, y: float, w: float, h: float, stroke=NOIR, width: float = 1.0) -> None:
        # Les coins arrondis sont approximés par un rectangle fin : rendu PDF stable sans courbes complexes.
        self.rect(x, y, w, h, stroke=stroke, width=width)

    def circle(self, x: float, y: float, radius: float, stroke=NOIR, width: float = 1.0) -> None:
        c = radius * 0.5522847498
        self.commands.append(
            _stroke(stroke) + b" " + _num(width) + b" w "
            + _num(x + radius) + b" " + _num(y) + b" m "
            + _num(x + radius) + b" " + _num(y + c) + b" " + _num(x + c) + b" " + _num(y + radius) + b" " + _num(x) + b" " + _num(y + radius) + b" c "
            + _num(x - c) + b" " + _num(y + radius) + b" " + _num(x - radius) + b" " + _num(y + c) + b" " + _num(x - radius) + b" " + _num(y) + b" c "
            + _num(x - radius) + b" " + _num(y - c) + b" " + _num(x - c) + b" " + _num(y - radius) + b" " + _num(x) + b" " + _num(y - radius) + b" c "
            + _num(x + c) + b" " + _num(y - radius) + b" " + _num(x + radius) + b" " + _num(y - c) + b" " + _num(x + radius) + b" " + _num(y) + b" c S"
        )

    def text(
        self,
        x: float,
        y: float,
        text: str,
        size: float = 8,
        font: str = "F1",
        color=NOIR,
        align: str = "left",
    ) -> None:
        rendered = _pdf_text(text)
        width = _text_width(text, size, font)
        if align == "center":
            x -= width / 2
        elif align == "right":
            x -= width
        self.commands.append(
            b"BT " + _fill(color) + b" /" + font.encode() + b" " + _num(size) + b" Tf "
            + _num(x) + b" " + _num(y) + b" Td " + rendered + b" Tj ET"
        )


def _num(value: float) -> bytes:
    return f"{value:.3f}".rstrip("0").rstrip(".").encode()


def _stroke(color: tuple[float, float, float]) -> bytes:
    return b" ".join(_num(c) for c in color) + b" RG"


def _fill(color: tuple[float, float, float]) -> bytes:
    return b" ".join(_num(c) for c in color) + b" rg"


def _pdf_text(text: str) -> bytes:
    encoded = text.encode("cp1252", errors="replace")
    out = bytearray(b"(")
    for byte in encoded:
        if byte in (40, 41, 92):
            out.extend(b"\\" + bytes([byte]))
        elif byte < 32 or byte > 126:
            out.extend(f"\\{byte:03o}".encode())
        else:
            out.append(byte)
    out.extend(b")")
    return bytes(out)


def _text_width(text: str, size: float, font: str) -> float:
    factor = 0.54 if font == "F1" else 0.58
    return len(text) * size * factor


def _wrap_text(text: str, max_chars: int) -> list[str]:
    if not text:
        return [""]
    return wrap(text, max_chars, break_long_words=False, replace_whitespace=False) or [text]


def _draw_multiline(
    pdf: MiniPDF,
    x: float,
    y: float,
    lines: list[str],
    size: float,
    leading: float,
    font: str = "F2",
    color=NOIR,
    align: str = "center",
) -> None:
    for index, line in enumerate(lines):
        pdf.text(x, y - index * leading, line, size=size, font=font, color=color, align=align)


def _annee_academique(semaine: date) -> str:
    debut = semaine.year if semaine.month >= 8 else semaine.year - 1
    return f"{debut} - {debut + 1}"


def _periode(semaine: date) -> str:
    samedi = semaine + timedelta(days=5)
    return f"{semaine.day:02d} au {samedi.day:02d} {MOIS_FR[samedi.month - 1]} {samedi.year}"


def _nom_enseignant(creneau: Creneau) -> str:
    nom = creneau.enseignant.nom.upper()
    prenom = creneau.enseignant.prenom.strip()
    return f"{nom} {prenom}".strip()


def _construire_lignes_salle(semaine: date, salle: Salle) -> list[dict]:
    qs = (
        Creneau.objects.filter(emploiDuTemps__semaine=semaine, salle=salle)
        .select_related("cours", "enseignant", "salle", "option", "emploiDuTemps")
        .order_by("jour", "heureDebut", "cours__codeCours")
    )
    creneaux_par_cellule: dict[tuple, list[Creneau]] = {}
    for creneau in qs:
        key = (creneau.jour, creneau.heureDebut, creneau.heureFin)
        creneaux_par_cellule.setdefault(key, []).append(creneau)

    lignes = []
    for plage in PLAGES_HORAIRES:
        if plage.get("pause"):
            lignes.append({"plage": plage, "pause": True, "cellules": []})
            continue
        cellules = []
        for code_jour, libelle_jour in JOURS_EDT:
            key = (code_jour, plage["debut"], plage["fin"])
            cellules.append({"jour": code_jour, "jour_label": libelle_jour, "creneaux": creneaux_par_cellule.get(key, [])})
        lignes.append({"plage": plage, "pause": False, "cellules": cellules})
    return lignes


def _pages_salles(semaine: date, salles: QuerySet[Salle]) -> list[PageSalle]:
    pages = []
    for salle in salles.order_by("site", "nom"):
        pages.append(PageSalle(site=salle.site, salle=salle, lignes=_construire_lignes_salle(semaine, salle)))
    return pages


def _draw_header(pdf: MiniPDF, semaine: date, page: PageSalle) -> None:
    left_lines = [
        "République du Cameroun",
        "Paix-Travail-Patrie",
        "-----------",
        "Ministère de l’Enseignement Supérieur",
        "-----------",
        "UNIVERSITÉ DE MAROUA",
        "-----------",
        "ECOLE NATIONALE SUPERIEURE POLYTECHNIQUE",
        "-----------",
        "Département d’Informatique et des Télécommunications",
    ]
    right_lines = [
        "Republic of Cameroon",
        "Peace-Work-Fatherland",
        "-----------",
        "Ministry of Higher Education",
        "-----------",
        "THE UNIVERSITY OF MAROUA",
        "-----------",
        "NATIONAL ADVANCED SCHOOL OF ENGINEERING",
        "-----------",
        "Department of Computer Science and Telecommunications",
    ]
    center_lines = [
        "B.P./P.O. Box : 46 Maroua",
        "Tel : (+237) 22 29 13 61 / (+237) 22 26 08 90",
        "Fax : (+237) 22 29 31 12 / (+237) 22 29 15 41",
        "Site web : http://www.enspm.univ-maroua.cm",
        "Email : polytech@univ-maroua.cm",
    ]

    _draw_multiline(pdf, 36 * MM, PAGE_HEIGHT - 13 * MM, left_lines, 5.6, 5.9, align="center")
    _draw_multiline(pdf, PAGE_WIDTH - 44 * MM, PAGE_HEIGHT - 13 * MM, right_lines, 5.6, 5.9, align="center")

    pdf.circle(PAGE_WIDTH / 2, PAGE_HEIGHT - 17 * MM, 9 * MM, stroke=GRIS_CERCLE, width=0.7)
    pdf.text(PAGE_WIDTH / 2, PAGE_HEIGHT - 16 * MM, "ENSPM", 7.2, "F2", VERT_ENSPM, "center")
    pdf.text(PAGE_WIDTH / 2, PAGE_HEIGHT - 20 * MM, "***", 8.5, "F2", VIOLET_ENSPM, "center")
    _draw_multiline(pdf, PAGE_WIDTH / 2, PAGE_HEIGHT - 30 * MM, center_lines, 4.4, 4.8, font="F1", align="center")

    pdf.line(7 * MM, PAGE_HEIGHT - 43 * MM, PAGE_WIDTH - 7 * MM, PAGE_HEIGHT - 43 * MM, VERT_CLAIR, 1.4)
    pdf.line(7 * MM, PAGE_HEIGHT - 44.2 * MM, PAGE_WIDTH - 7 * MM, PAGE_HEIGHT - 44.2 * MM, VERT_ENSPM, 0.8)

    box_x = 55 * MM
    box_y = PAGE_HEIGHT - 68 * MM
    box_w = PAGE_WIDTH - 110 * MM
    box_h = 20 * MM
    pdf.round_rect(box_x, box_y, box_w, box_h, stroke=VIOLET_ENSPM, width=1.8)
    pdf.text(PAGE_WIDTH / 2, box_y + 14.3 * MM, "EMPLOI DE TEMPS", 9.5, "F2", NOIR, "center")
    meta = f"Année académique {_annee_academique(semaine)} - {SEMESTRES[semaine.month]} - période du {_periode(semaine)}"
    pdf.text(PAGE_WIDTH / 2, box_y + 9 * MM, meta, 8, "F2", NOIR, "center")
    pdf.text(PAGE_WIDTH / 2 - 18 * MM, box_y + 4 * MM, f"Site : {page.site}", 8.8, "F2", NOIR, "right")
    pdf.text(PAGE_WIDTH / 2 + 19 * MM, box_y + 4 * MM, f"Salle : {page.salle.nom}", 8.8, "F2", ROUGE, "left")


def _draw_footer(pdf: MiniPDF) -> None:
    note_lines = [
        "NB : Ce calendrier est dynamique et susceptible d’être modifié, les étudiants sont invités à bien vouloir régulièrement consulter le babillard et le Site Web de l’ECOLE NATIONALE",
        "SUPERIEURE POLYTECHNIQUE pour s’enquérir des dernières modifications. http://enspm.univ-maroua.cm enspm@univ-maroua.cm",
    ]
    _draw_multiline(pdf, 8 * MM, 17 * MM, note_lines, 5.1, 5.5, font="F2", align="left")
    pdf.text(PAGE_WIDTH - 43 * MM, 20 * MM, "Le Directeur,", 7, "F2", NOIR, "center")


def _draw_table(pdf: MiniPDF, page: PageSalle) -> None:
    x0 = 7 * MM
    y_top = PAGE_HEIGHT - 76 * MM
    col_widths = [20 * MM] + [40 * MM] * 6
    header_h = 9 * MM
    row_h = 24 * MM
    pause_h = 12 * MM

    x = x0
    headers = ["HORAIRES"] + [label.upper() for _code, label in JOURS_EDT]
    for index, header in enumerate(headers):
        pdf.rect(x, y_top - header_h, col_widths[index], header_h, stroke=VERT_ENSPM, fill=BLANC, width=0.9)
        pdf.text(x + col_widths[index] / 2, y_top - 5.8 * MM, header, 6.7, "F2", NOIR, "center")
        x += col_widths[index]

    y = y_top - header_h
    for ligne in page.lignes:
        height = pause_h if ligne["pause"] else row_h
        y -= height
        pdf.rect(x0, y, col_widths[0], height, stroke=VERT_ENSPM, fill=BLANC, width=0.9)
        pdf.text(x0 + col_widths[0] / 2, y + height / 2 - 2, ligne["plage"]["label"], 6.2, "F2", NOIR, "center")

        if ligne["pause"]:
            x = x0 + col_widths[0]
            pdf.rect(x, y, sum(col_widths[1:]), height, stroke=VERT_ENSPM, fill=BLEU_PAUSE, width=0.9)
            pdf.text(x + sum(col_widths[1:]) / 2, y + height / 2 - 5, "PAUSE", 16, "F2", NOIR, "center")
            continue

        x = x0 + col_widths[0]
        for cellule in ligne["cellules"]:
            pdf.rect(x, y, 40 * MM, height, stroke=VERT_ENSPM, fill=BLANC, width=0.9)
            _draw_cell_content(pdf, x, y, 40 * MM, height, cellule["creneaux"])
            x += 40 * MM


def _draw_cell_content(pdf: MiniPDF, x: float, y: float, w: float, h: float, creneaux: list[Creneau]) -> None:
    if not creneaux:
        return
    block_top = y + h - 4 * MM
    cursor = block_top
    max_lines = 10 if len(creneaux) == 1 else 5
    for creneau_index, creneau in enumerate(creneaux):
        if creneau_index:
            cursor -= 2.5 * MM
        lines: list[tuple[str, tuple[float, float, float]]] = []
        for line in _wrap_text(creneau.cours.intitule, 28)[:3]:
            lines.append((line, NOIR))
        lines.append((creneau.cours.codeCours, NOIR))
        if creneau.cours.volumeHoraire:
            for line in _wrap_text(f"({creneau.cours.volumeHoraire})", 34)[:2]:
                lines.append((line, NOIR))
        lines.append((_nom_enseignant(creneau), ROUGE))
        for line, color in lines[:max_lines]:
            if cursor < y + 2 * MM:
                return
            pdf.text(x + w / 2, cursor, line, 5.2, "F2", color, "center")
            cursor -= 2.35 * MM


def _draw_page(pdf: MiniPDF, semaine: date, page: PageSalle) -> None:
    _draw_header(pdf, semaine, page)
    _draw_table(pdf, page)
    _draw_footer(pdf)


def generer_pdf_emplois_du_temps(semaine: date) -> ExportPlanning:
    """Génère un PDF fusionné contenant une page par salle, ordonnée par site puis salle."""
    salles = Salle.objects.filter(creneaux__emploiDuTemps__semaine=semaine).distinct()
    if not salles.exists():
        salles = Salle.objects.all()
    pages = _pages_salles(semaine, salles)

    pdf = MiniPDF()
    if pages:
        for index, page in enumerate(pages):
            if index:
                pdf.add_page()
            _draw_page(pdf, semaine, page)
    else:
        pdf.text(PAGE_WIDTH / 2, PAGE_HEIGHT / 2, "Aucune salle à exporter", 14, "F2", NOIR, "center")

    slug = slugify(f"emplois-du-temps-{semaine.isoformat()}")
    return ExportPlanning(contenu=pdf.finish(), nom_fichier=f"{slug}.pdf")
