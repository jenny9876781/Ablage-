"""Erzeugt die begleitenden Unterlagen zum Webkatalog als Word-Dateien.

    python3 scripts/build_unterlagen_docx.py

  U1_Aktennotiz_Speicherplatz.docx   Aktennotiz zur Nutzung fremden Speicherplatzes
  U2_Datenschutz_Absatz.docx         Textbaustein für die Datenschutzerklärung
  U3_Knopf_fuer_kikripp.docx         der HTML-Baustein für den Knopf auf kikripp.de

Die Texte sind von mir formuliert und nicht anwaltlich geprüft.
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


# ----------------------------------------------------------- U1 Aktennotiz

def aktennotiz():
    d = dok_anlegen()
    kopf(d, "Aktennotiz", "Nutzung fremden Speicherplatzes für den Artikelkatalog")

    p(d, "Sachverhalt", groesse=12, fett=True, vor=6, nach=4)
    p(d, f"Die {FIRMA} löst ihren Betrieb auf und verkauft das vorhandene Inventar. "
         "Dafür wird ein passwortgeschützter Artikelkatalog im Internet bereitgestellt. "
         "Der Katalog liegt technisch auf dem Webspace der Hundeschule Schlabberschnuten "
         "(www.schlabberschnuten.com), weil auf der eigenen Website der Gesellschaft die "
         "technischen Voraussetzungen derzeit nicht gegeben sind.")

    p(d, "Rollen", groesse=12, fett=True, vor=10, nach=4)
    p(d, f"Verantwortlich für den Verkauf, die Preise, den Inhalt des Katalogs und den "
         f"Umgang mit Interessentendaten ist ausschließlich die {FIRMA}. Die Hundeschule "
         "Schlabberschnuten stellt ausschließlich Speicherplatz zur Verfügung und tritt "
         "weder als Verkäuferin auf noch nimmt sie Bestellungen entgegen. Auf der "
         "Katalogseite ist die Gesellschaft als Anbieterin benannt und auf ihr Impressum "
         "verlinkt.")

    p(d, "Umgang mit personenbezogenen Daten", groesse=12, fett=True, vor=10, nach=4)
    p(d, "Der Katalog speichert auf dem genannten Webspace keine personenbezogenen Daten "
         "von Interessenten. Name, E-Mail-Adresse und Telefonnummer werden ausschließlich "
         f"per E-Mail an die {FIRMA} ({EMAIL}) übermittelt und unmittelbar nach dem "
         "Versand aus der Datenbank gelöscht. Gespeichert bleiben nur Artikelnummer, "
         "Menge, Preis und Vorgangsnummer ohne Personenbezug. Die IP-Adresse der "
         "Besucher wird nicht gespeichert.")
    p(d, "Scheitert der Versand einer Benachrichtigung, verbleiben die Kontaktdaten "
         "vorübergehend in der Datenbank, damit der Vorgang nicht verloren geht. Die "
         "Verwaltung weist darauf hin; die Daten werden anschließend manuell gelöscht.")

    p(d, "Dauer", groesse=12, fett=True, vor=10, nach=4)
    p(d, "Die Nutzung ist auf die Dauer der Betriebsauflösung befristet. Nach Abschluss "
         "werden Katalogseite, Plugin, Artikelbilder und alle Vorgangsdaten von dem "
         "Webspace entfernt. Die für Buchhaltung und Aufbewahrungsfristen erforderlichen "
         f"Unterlagen führt die {FIRMA} in ihren eigenen Systemen.")

    p(d, "Zeitraum der Nutzung: von ______________ bis ______________",
      vor=14, nach=26)

    p(d, "_______________________________          _______________________________",
      farbe=GRAU, nach=2)
    p(d, f"{FIRMA}                                        Hundeschule Schlabberschnuten",
      groesse=9, farbe=GRAU, nach=0)
    p(d, "Ort, Datum, Unterschrift                       Ort, Datum, Unterschrift",
      groesse=9, farbe=GRAU, nach=20)

    p(d, "Diese Notiz dient der internen Dokumentation. Sie wurde nicht anwaltlich geprüft.",
      groesse=8.5, farbe=GRAU, kursiv=True)

    ziel = os.path.join(AUSGABE, "U1_Aktennotiz_Speicherplatz.docx")
    d.save(ziel)
    return ziel


# --------------------------------------------------- U2 Datenschutz-Absatz

def datenschutz():
    d = dok_anlegen()
    kopf(d, "Textbaustein Datenschutzerklärung",
         "Zum Einfügen in die Datenschutzerklärung von www.schlabberschnuten.com")

    p(d, "Den folgenden Absatz in die bestehende Datenschutzerklärung aufnehmen, "
         "solange der Artikelkatalog dort erreichbar ist.", farbe=GRAU, nach=16)

    p(d, "Artikelkatalog der " + FIRMA, groesse=12, fett=True, vor=4, nach=6)
    for satz in [
        f"Auf dieser Website wird vorübergehend ein passwortgeschützter Artikelkatalog "
        f"der {FIRMA}, {STRASSE}, {PLZ_ORT} bereitgestellt. Anbieterin des dort "
        f"dargestellten Angebots und für die Verarbeitung der dabei anfallenden Daten "
        f"verantwortlich ist ausschließlich die {FIRMA} (Telefon {TELEFON}, "
        f"E-Mail {EMAIL}). Wir stellen für diesen Katalog lediglich Speicherplatz bereit.",
        "Wenn Sie über den Katalog eine Reservierung abschicken, übermitteln Sie Ihren "
        "Namen bzw. Ihre Firma, Ihre E-Mail-Adresse, Ihre Telefonnummer und, sofern "
        "angegeben, eine Nachricht. Diese Angaben werden ausschließlich per E-Mail an "
        f"die {FIRMA} weitergeleitet und nicht auf dieser Website gespeichert. Sie "
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


# ------------------------------------------------------------- U3 Knopf

KNOPF = """<div style="border:1px solid #DCDCDC;border-left:4px solid #C8102E;
            background:#F7F5F2;padding:22px 24px;max-width:620px;
            font-family:system-ui,Arial,sans-serif">
  <div style="font-size:19px;font-weight:700;color:#1A1A1A;margin-bottom:6px">
    Artikelkatalog aus der Betriebsauflösung
  </div>
  <p style="margin:0 0 16px;font-size:15px;line-height:1.6;color:#1A1A1A">
    Wir lösen unseren Kindergarten auf und geben die komplette Einrichtung ab &ndash;
    Möbel, Spielmaterial, Küche, Technik und Dekoration. Der Katalog zeigt Fotos,
    Preise und die tagesaktuelle Verfügbarkeit.
  </p>
  <a href="HIER_DIE_ADRESSE_MIT_PASSWORT_EINTRAGEN"
     style="display:inline-block;background:#C8102E;color:#fff;text-decoration:none;
            font-size:15px;font-weight:700;padding:13px 26px;border-radius:3px">
    Zum Artikelkatalog
  </a>
  <p style="margin:14px 0 0;font-size:12.5px;color:#6B7280">
    Der Katalog ist geschützt. Sie haben noch keinen Zugang?
    Schreiben Sie uns an jennyp@kikripp.de.
  </p>
</div>"""


def knopf():
    d = dok_anlegen()
    kopf(d, "Knopf für kikripp.de", "Zum Einfügen als Block „Custom HTML“")

    p(d, "So geht's", groesse=12, fett=True, vor=4, nach=6)
    for i, satz in enumerate([
        "In WordPress die Seite bearbeiten, auf der der Knopf stehen soll.",
        "Über das Plus einen Block einfügen und nach „Custom HTML“ suchen "
        "(auf Deutsch manchmal „Eigenes HTML“).",
        "Den gesamten Kasten unten hineinkopieren.",
        "In der Zeile, die mit <a href= beginnt, HIER_DIE_ADRESSE_MIT_PASSWORT_EINTRAGEN "
        "durch die Katalogadresse ersetzen – am besten gleich mit Passwort im Link, "
        "dann muss niemand etwas eintippen.",
        "Speichern und die Seite im privaten Browserfenster ansehen.",
    ], start=1):
        p(d, f"{i}.  {satz}", nach=5)

    p(d, "Die Adresse mit Passwort sieht so aus:", vor=10, nach=4)
    p(d, "https://www.schlabberschnuten.com/kikripp-artikelkatalog/?kik=PASSWORT",
      groesse=10, schrift="Consolas", farbe=ROT, nach=12)

    p(d, "Der Baustein", groesse=12, fett=True, vor=8, nach=6)
    for zeile in KNOPF.split("\n"):
        a = d.add_paragraph()
        a.paragraph_format.space_before = Pt(0)
        a.paragraph_format.space_after = Pt(0)
        lauf = a.add_run(zeile)
        lauf.font.name = "Consolas"
        lauf.font.size = Pt(8.5)
        lauf.font.color.rgb = RGBColor.from_string(SCHWARZ)

    p(d, "Falls das Kopieren aus Word Probleme macht: dieselbe Vorlage liegt zusätzlich "
         "als U3_Knopf_fuer_kikripp.txt daneben.",
      groesse=8.5, farbe=GRAU, kursiv=True, vor=14)

    ziel = os.path.join(AUSGABE, "U3_Knopf_fuer_kikripp.docx")
    d.save(ziel)
    with open(os.path.join(AUSGABE, "U3_Knopf_fuer_kikripp.txt"), "w", encoding="utf-8") as f:
        f.write(KNOPF + "\n")
    return ziel


if __name__ == "__main__":
    for fn in (aktennotiz, datenschutz, knopf):
        ziel = fn()
        print(f"geschrieben: {ziel}  ({os.path.getsize(ziel)//1024} KB)")
