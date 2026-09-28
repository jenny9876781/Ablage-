"""Erzeugt die begleitenden Unterlagen zum Webkatalog als Word-Dateien.

    python3 scripts/build_unterlagen_docx.py

  U2_Datenschutz_Absatz.docx         Textbaustein für die Datenschutzerklärung

Die Texte sind von mir formuliert und nicht anwaltlich geprüft.

Seit dem 28.09.2026 liegt der Katalog auf der eigenen Website der Gesellschaft
(www.kikripp.de). Die frueheren Unterlagen U1 (Aktennotiz zur Nutzung fremden
Speicherplatzes) und U3 (Knopf, der von kikripp.de auf die fremde Seite fuehrt)
sind damit gegenstandslos und werden nicht mehr erzeugt.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import AUSGABE, ASSETS, ROT, SCHWARZ, GRAU, FONT, FIRMA, STRASSE, PLZ_ORT, TELEFON, EMAIL

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.oxml.ns import qn


def dok_anlegen():
    d = Document()
    st = d.styles["Normal"]
    st.font.name = FONT
    st.font.size = Pt(10.5)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    for s in d.sections:
        s.top_margin, s.bottom_margin = Cm(2.2), Cm(2.0)
        s.left_margin, s.right_margin = Cm(2.4), Cm(2.4)
    return d


def p(d, text, groesse=10.5, fett=False, farbe=SCHWARZ, vor=0, nach=7, kursiv=False,
      schrift=None, ausrichtung=None):
    a = d.add_paragraph()
    a.paragraph_format.space_before = Pt(vor)
    a.paragraph_format.space_after = Pt(nach)
    if ausrichtung is not None:
        a.alignment = ausrichtung
    lauf = a.add_run(text)
    lauf.font.name = schrift or FONT
    lauf.font.size = Pt(groesse)
    lauf.bold = fett
    lauf.italic = kursiv
    lauf.font.color.rgb = RGBColor.from_string(farbe)
    return a


def kopf(d, titel, unter=""):
    p(d, "KIKRIPP", groesse=13, fett=True, farbe=ROT, nach=0)
    p(d, f"{FIRMA} · {STRASSE} · {PLZ_ORT}", groesse=8.5, farbe=GRAU, nach=16)
    p(d, titel, groesse=17, fett=True, nach=2)
    if unter:
        p(d, unter, groesse=11, farbe=GRAU, nach=16)


# --------------------------------------------------- U2 Datenschutz-Absatz

def datenschutz():
    d = dok_anlegen()
    kopf(d, "Textbaustein Datenschutzerklärung",
         "Zum Einfügen in die Datenschutzerklärung von www.kikripp.de")

    p(d, "Den folgenden Absatz in die bestehende Datenschutzerklärung aufnehmen, "
         "solange der Artikelkatalog dort erreichbar ist.", farbe=GRAU, nach=16)

    p(d, "Artikelkatalog der " + FIRMA, groesse=12, fett=True, vor=4, nach=6)
    for satz in [
        f"Im Zuge der Betriebsauflösung stellen wir auf dieser Website vorübergehend "
        f"einen passwortgeschützten Artikelkatalog bereit, über den vorhandenes Inventar "
        f"verkauft wird. Verantwortlich für das Angebot und für die Verarbeitung der "
        f"dabei anfallenden Daten ist die {FIRMA}, {STRASSE}, {PLZ_ORT} "
        f"(Telefon {TELEFON}, E-Mail {EMAIL}).",
        "Wenn Sie über den Katalog eine Reservierung abschicken, übermitteln Sie Ihren "
        "Namen bzw. Ihre Firma, Ihre E-Mail-Adresse, Ihre Telefonnummer und, sofern "
        "angegeben, eine Nachricht. Diese Angaben werden ausschließlich per E-Mail an "
        f"die für den Verkauf zuständige Stelle der {FIRMA} weitergeleitet und nicht "
        f"auf dieser Website gespeichert. Sie "
        "erhalten keine automatische Bestätigungsmail; die {0} nimmt persönlich "
        "Kontakt mit Ihnen auf.".format(FIRMA),
        "In der Datenbank dieser Website verbleiben ausschließlich Angaben ohne "
        "Personenbezug: Artikelnummer, Menge, Preis, Vorgangsnummer und die Frist, "
        "bis zu der ein Artikel vorgemerkt ist. Ihre IP-Adresse wird im Zusammenhang "
        "mit der Reservierung nicht gespeichert.",
        "Rechtsgrundlage der Verarbeitung ist Art. 6 Abs. 1 lit. b DSGVO "
        "(Durchführung vorvertraglicher Maßnahmen und Abwicklung des Kaufvertrags). "
        f"Ansprechpartnerin für Auskunft, Berichtigung und Löschung ist die {FIRMA} "
        f"unter {EMAIL}.",
    ]:
        p(d, satz)

    p(d, "Nicht anwaltlich geprüft. Wenn ohnehin jemand über die Verkaufsbedingungen "
         "schaut, diesen Absatz mitlaufen lassen.",
      groesse=8.5, farbe=GRAU, kursiv=True, vor=16)

    ziel = os.path.join(AUSGABE, "U2_Datenschutz_Absatz.docx")
    d.save(ziel)
    return ziel


if __name__ == "__main__":
    for fn in (datenschutz,):
        ziel = fn()
        print(f"geschrieben: {ziel}  ({os.path.getsize(ziel)//1024} KB)")
