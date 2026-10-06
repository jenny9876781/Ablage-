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

def katalog_saetze():
    """Der Absatz zum Artikelkatalog - in U2 einzeln, in U4 Teil der ganzen Erklärung."""
    return [
        f"Im Zuge der Betriebsauflösung stellen wir auf dieser Website vorübergehend "
        f"einen Artikelkatalog bereit, über den vorhandenes Inventar verkauft wird. "
        f"Verantwortlich für das Angebot und für die Verarbeitung der dabei anfallenden "
        f"Daten ist die {FIRMA}, {STRASSE}, {PLZ_ORT} (Telefon {TELEFON}, E-Mail {EMAIL}).",
        "Wenn Sie über den Katalog eine Reservierung abschicken, übermitteln Sie Ihren "
        "Namen, gegebenenfalls Ihre Firma, Ihre Rechnungsanschrift (Straße, Postleitzahl, "
        "Ort), Ihre E-Mail-Adresse, Ihre Telefonnummer, Ihren Wunschtermin für Abholung "
        "und gegebenenfalls Besichtigung sowie, sofern angegeben, eine Nachricht. Diese "
        "Angaben werden zusammen mit den von Ihnen vorgemerkten Artikeln in der Datenbank "
        "dieser Website gespeichert, damit wir Ihre Reservierung bearbeiten, Sie anrufen "
        "und Bestellung und Rechnung erstellen können. Sie erhalten keine automatische "
        "Bestätigungsmail; die {0} nimmt persönlich Kontakt mit Ihnen auf.".format(FIRMA),
        "Ihre Kontaktdaten werden in der Datenbank gelöscht, sobald der Vorgang abgewickelt "
        "ist – spätestens, wenn der Artikelkatalog nach Abschluss der Betriebsauflösung "
        "abgeschaltet wird. Danach verbleiben dort nur noch Angaben ohne Personenbezug: "
        "Artikelnummer, Menge, Preis und Vorgangsnummer. Kommt ein Kauf zustande, "
        "bewahren wir Bestellung und Rechnung im Rahmen der gesetzlichen "
        "Aufbewahrungsfristen auf.",
        "Zum Schutz vor automatisierten Einträgen wird eine Prüfsumme Ihrer IP-Adresse "
        "für höchstens eine Stunde vorübergehend gespeichert, um die Zahl der "
        "Reservierungen je Anschluss zu begrenzen. Am Vorgang selbst wird Ihre "
        "IP-Adresse nicht gespeichert.",
        "Eine Weitergabe an Dritte findet nicht statt. Der Katalog liegt auf der "
        f"Website der {FIRMA}; es werden keine Daten an fremde Dienste übermittelt.",
        "Rechtsgrundlage der Verarbeitung ist Art. 6 Abs. 1 lit. b DSGVO "
        "(Durchführung vorvertraglicher Maßnahmen und Abwicklung des Kaufvertrags), "
        "für die Aufbewahrung von Rechnungen Art. 6 Abs. 1 lit. c DSGVO und für den "
        "Schutz vor automatisierten Einträgen Art. 6 Abs. 1 lit. f DSGVO. "
        f"Ansprechpartnerin für Auskunft, Berichtigung und Löschung ist die {FIRMA} "
        f"unter {EMAIL}.",
    ]


def datenschutz():
    d = dok_anlegen()
    kopf(d, "Textbaustein Datenschutzerklärung",
         "Zum Einfügen in die Datenschutzerklärung von www.kikripp.de")

    p(d, "Den folgenden Absatz in die bestehende Datenschutzerklärung aufnehmen, "
         "solange der Artikelkatalog dort erreichbar ist.", farbe=GRAU, nach=16)

    p(d, "Artikelkatalog der " + FIRMA, groesse=12, fett=True, vor=4, nach=6)
    for satz in katalog_saetze():
        p(d, satz)

    p(d, "Nicht anwaltlich geprüft. Wenn ohnehin jemand über die Verkaufsbedingungen "
         "schaut, diesen Absatz mitlaufen lassen.",
      groesse=8.5, farbe=GRAU, kursiv=True, vor=16)

    ziel = os.path.join(AUSGABE, "U2_Datenschutz_Absatz.docx")
    d.save(ziel)
    return ziel


# --------------------------------------------------- U4 Impressum und Datenschutz

def impressum_datenschutz():
    """Beide Seiten fertig zum Einfügen - für die Umstellung von kikripp.de auf die GmbH
    (06.10.2026). Nur Geschäftsführung und Handelsregister sind auszufüllen."""
    d = dok_anlegen()
    kopf(d, "Impressum und Datenschutz für kikripp.de",
         "Fertige Texte für die beiden Seiten – nur die gelb markierten Stellen ausfüllen")
    p(d, "So geht es: Seite in WordPress öffnen, zweimal Strg + A und Entf (alles weg), den "
         "Text unten von der Überschrift bis zum Strich kopieren und einfügen, Aktualisieren.",
      farbe=GRAU, nach=14)

    def gelb(text):
        a = p(d, text)
        a.runs[0].font.highlight_color = 7      # gelb
        return a

    p(d, "SEITE 1: IMPRESSUM", groesse=9, fett=True, farbe=ROT, vor=6, nach=6)
    p(d, "Impressum", groesse=14, fett=True, nach=4)
    p(d, "Angaben gemäß § 5 DDG")
    p(d, f"{FIRMA}\n{STRASSE}\n{PLZ_ORT}")
    gelb("Vertreten durch die Geschäftsführung: [Name eintragen]")
    p(d, f"Telefon: {TELEFON}\nE-Mail: {EMAIL}")
    gelb("Registergericht: Amtsgericht [Freiburg im Breisgau – bitte prüfen]\nRegisternummer: HRB [Nummer eintragen]")
    p(d, "Wir sind nicht bereit und nicht verpflichtet, an Streitbeilegungsverfahren vor einer "
         "Verbraucherschlichtungsstelle teilzunehmen.")
    p(d, "―" * 30, farbe=GRAU, vor=6, nach=18)

    p(d, "SEITE 2: DATENSCHUTZ", groesse=9, fett=True, farbe=ROT, vor=6, nach=6)
    p(d, "Datenschutzerklärung", groesse=14, fett=True, nach=4)
    abschnitte = [
        ("1. Verantwortlicher",
         [f"Verantwortlich für die Datenverarbeitung auf dieser Website ist die {FIRMA}, "
          f"{STRASSE}, {PLZ_ORT}, Telefon {TELEFON}, E-Mail {EMAIL}."]),
        ("2. Aufruf der Website und Server-Logdateien",
         ["Bei jedem Aufruf dieser Website speichert der Server, auf dem sie betrieben wird, "
          "automatisch Angaben, die Ihr Browser übermittelt: IP-Adresse, Datum und Uhrzeit, "
          "aufgerufene Seite, Browser und Betriebssystem sowie die zuvor besuchte Seite. Diese "
          "Daten sind nötig, um die Website auszuliefern und ihre Sicherheit zu gewährleisten "
          "(Art. 6 Abs. 1 lit. f DSGVO). Sie werden nicht mit anderen Daten zusammengeführt und "
          "nach kurzer Zeit automatisch gelöscht. Die Website liegt bei einem Hosting-Dienstleister, "
          "der die Daten in unserem Auftrag verarbeitet."]),
        ("3. Cookies und Besucherstatistik",
         ["Diese Website setzt für Besucher keine Cookies zu Werbe- oder Analysezwecken. "
          "Technisch notwendige Cookies werden nur für angemeldete Redakteure verwendet. "
          "Für eine einfache Besucherstatistik zählen wir Seitenaufrufe ohne Cookies und ohne "
          "Speicherung von IP-Adressen; ein Rückschluss auf einzelne Besucher ist nicht möglich."]),
        ("4. Kontakt per E-Mail oder Telefon",
         ["Wenn Sie uns per E-Mail oder Telefon kontaktieren, verarbeiten wir Ihre Angaben, um "
          "Ihre Anfrage zu beantworten (Art. 6 Abs. 1 lit. b bzw. f DSGVO). Die Daten werden "
          "gelöscht, sobald sie dafür nicht mehr benötigt werden und keine gesetzlichen "
          "Aufbewahrungspflichten bestehen."]),
        ("5. Artikelkatalog", katalog_saetze()),
        ("6. Ihre Rechte",
         ["Sie haben das Recht auf Auskunft über Ihre bei uns gespeicherten Daten, auf "
          "Berichtigung, Löschung und Einschränkung der Verarbeitung, auf Datenübertragbarkeit "
          "sowie das Recht, einer Verarbeitung auf Grundlage von Art. 6 Abs. 1 lit. f DSGVO zu "
          f"widersprechen. Wenden Sie sich dazu an {EMAIL}.",
          "Sie können sich außerdem bei einer Datenschutz-Aufsichtsbehörde beschweren, zum "
          "Beispiel beim Landesbeauftragten für den Datenschutz und die Informationsfreiheit "
          "Baden-Württemberg."]),
        ("7. Verschlüsselung",
         ["Diese Website nutzt aus Sicherheitsgründen eine SSL- bzw. TLS-Verschlüsselung. "
          "Eine verschlüsselte Verbindung erkennen Sie am Schloss-Symbol in der Adresszeile."]),
    ]
    for titel, saetze in abschnitte:
        p(d, titel, groesse=11.5, fett=True, vor=8, nach=4)
        for satz in saetze:
            p(d, satz)
    p(d, "―" * 30, farbe=GRAU, vor=6, nach=12)
    p(d, "Nicht anwaltlich geprüft. Abschnitt 3 setzt voraus, dass auf kikripp.de keine weiteren "
         "Dienste wie Google Analytics, Google Maps, YouTube-Videos oder Schriften von Google "
         "eingebunden sind. Falls doch, bitte Bescheid geben – dann ergänze ich den Abschnitt.",
      groesse=8.5, farbe=GRAU, kursiv=True)
    ziel = os.path.join(AUSGABE, "U4_Impressum_Datenschutz_GmbH.docx")
    d.save(ziel)
    return ziel


if __name__ == "__main__":
    for fn in (datenschutz, impressum_datenschutz):
        ziel = fn()
        print(f"geschrieben: {ziel}  ({os.path.getsize(ziel)//1024} KB)")
