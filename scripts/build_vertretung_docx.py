"""Anleitung für die Urlaubsvertretung (26.–30.10.2026) -> ausgabe/V1_Anleitung_Vertretung.docx

Für eine Kollegin, die wenig mit dem Computer arbeitet: nur zwei Situationen (geplante Abholung,
spontaner Kunde), große Schrift, ein Bild je Schritt. Seite 3 ist die Kassenliste zum Ausdrucken –
vor Ort gibt es keinen Drucker, die Nutzerin druckt alles vorher aus.

Die Bilder in assets/vertretung/ stammen vom Testserver mit dem echten Plugin (angemeldet als
Verwaltung), nicht aus dem echten WordPress – deshalb ohne Kundendaten.
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from lib import AUSGABE, ROT, SCHWARZ, GRAU
from build_unterlagen_docx import dok_anlegen, p
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_BREAK
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

BASIS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BILDER = os.path.join(BASIS, "assets", "vertretung")
ZIEL = os.path.join(AUSGABE, "V1_Anleitung_Vertretung.docx")
GROSS = 14


def text(d, t, fett=False, farbe=SCHWARZ, nach=6, groesse=GROSS):
    return p(d, t, groesse=groesse, fett=fett, farbe=farbe, nach=nach)


def schritt(d, nr, t, bild=None, breite=12):
    a = d.add_paragraph()
    a.paragraph_format.space_before = Pt(8)
    a.paragraph_format.space_after = Pt(4)
    a.paragraph_format.keep_with_next = True
    z = a.add_run(f"{nr}  ")
    z.font.size = Pt(GROSS + 4); z.bold = True; z.font.color.rgb = RGBColor.from_string(ROT)
    for i, teil in enumerate(t.split("**")):
        r = a.add_run(teil)
        r.font.size = Pt(GROSS); r.bold = i % 2 == 1
    if bild:
        d.add_picture(os.path.join(BILDER, bild), width=Cm(breite))
        d.paragraphs[-1].paragraph_format.space_after = Pt(4)


def kasten(d, zeilen, farbe="FBE9EC"):
    t = d.add_table(rows=1, cols=1)
    z = t.cell(0, 0)
    sh = OxmlElement("w:shd"); sh.set(qn("w:val"), "clear"); sh.set(qn("w:fill"), farbe)
    z._tc.get_or_add_tcPr().append(sh)
    z.paragraphs[0].text = ""
    for i, (t_, fett) in enumerate(zeilen):
        a = z.paragraphs[0] if i == 0 else z.add_paragraph()
        a.paragraph_format.space_after = Pt(3)
        r = a.add_run(t_); r.font.size = Pt(GROSS); r.bold = fett
    d.add_paragraph().paragraph_format.space_after = Pt(2)


def seitenumbruch(d):
    d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def bauen():
    d = dok_anlegen()
    for s in d.sections:
        s.top_margin, s.bottom_margin = Cm(1.6), Cm(1.5)
        s.left_margin, s.right_margin = Cm(2.0), Cm(2.0)

    p(d, "Artikelverkauf – Vertretung 26. bis 30.10.2026", groesse=20, fett=True, nach=4)
    text(d, "Jenny ist ab Montag, 02.11. wieder da. Bis dahin gibt es für dich nur zwei Fälle.",
         farbe=GRAU, nach=10)

    kasten(d, [("Das musst du NICHT tun:", True),
               ("Reservierungs-Mails beantworten, Rechnungen schreiben, "
                "unter „Reservierungen“ etwas anklicken. Das macht Jenny danach.", False)],
               farbe="F2F2F2")

    p(d, "1. Geplante Abholung", groesse=17, fett=True, farbe=ROT, vor=6, nach=4)
    text(d, "Wie immer: Name auf der Abholliste suchen, Ware vom Abholplatz geben, abhaken.")
    text(d, "Ist noch nicht bezahlt: **bar kassieren** und in die **Kassenliste** eintragen (letzte Seite). "
            "Das Geld kommt in die Kasse. Die Rechnung schreibt Jenny danach.".replace("**", ""))

    p(d, "2. Kunde kommt ohne Reservierung", groesse=17, fett=True, farbe=ROT, vor=10, nach=2)
    text(d, "Erst prüfen, ob der Artikel noch frei ist – sonst verkaufen wir ihn vielleicht zweimal.",
         farbe=GRAU, nach=4)
    schritt(d, "①", "Am PC mit Jennys Zugang anmelden und **www.kikripp.de/artikelkatalog** öffnen.")
    schritt(d, "②", "Die **Artikelnummer** vom Etikett am Artikel oben ins Suchfeld tippen.", "1_suche.png", 11)

    seitenumbruch(d)
    schritt(d, "③", "Oben rechts am Foto steht **VERFÜGBAR**? Dann weiter mit ④.")
    tab = d.add_table(rows=2, cols=2)
    for i, (bild, unter) in enumerate([("2_verfuegbar.png", "VERFÜGBAR → verkaufen"),
                                        ("2b_reserviert.png", "RESERVIERT → nicht verkaufen")]):
        z = tab.cell(0, i); z.paragraphs[0].add_run().add_picture(os.path.join(BILDER, bild), width=Cm(3.6))
        r = tab.cell(1, i).paragraphs[0].add_run(unter); r.bold = True; r.font.size = Pt(GROSS - 1)
    text(d, "Steht dort RESERVIERT, steht beim Preis „VHB“ oder findest du den Artikel nicht: "
            "nicht verkaufen. Name und Telefon des Kunden auf die Kassenliste schreiben – Jenny meldet sich.",
         nach=4, groesse=GROSS - 1)
    schritt(d, "④", "Auf **reservieren** klicken. Oben erscheint ein schwarzer Balken – "
                    "dort auf **Reservierung abschicken** klicken.", "3_leiste.png", 16)
    schritt(d, "⑤", "Nur **Name** und **Telefon** des Kunden eintragen. Alles andere leer lassen.", "4_name.png", 7.5)

    seitenumbruch(d)
    schritt(d, "⑥", "Bei **Nachricht** schreiben: „Barverkauf vor Ort, … € bar“. "
                    "Dann auf **Reservierung verbindlich abschicken**.", "5_abschicken.png", 11)
    schritt(d, "⑦", "Es erscheint ein **grüner Kasten**. Auf **Schließen** klicken – fertig.",
            "6_bestaetigung.png", 11)
    schritt(d, "⑧", "Den **Preis aus dem Katalog** bar kassieren, in die **Kassenliste** eintragen, "
                    "Ware mitgeben.")
    kasten(d, [("Wenn etwas nicht klappt:", True),
               ("Nichts verkaufen. Name, Telefon und Artikelnummer auf die Kassenliste schreiben. "
                "Jenny ruft den Kunden ab 02.11. an.", False)])

    # ----- Kassenliste
    seitenumbruch(d)
    p(d, "Kassenliste 26. bis 30.10.2026", groesse=18, fett=True, nach=2)
    text(d, "Jede Barzahlung und jeden Kunden, der wiederkommen soll, hier eintragen.", farbe=GRAU, nach=8,
         groesse=GROSS - 2)
    spalten = [("Datum", 2.0), ("Name Kunde", 4.0), ("Telefon", 3.4), ("Artikelnr.", 2.6),
               ("bar €", 1.8), ("Notiz", 3.2)]
    t = d.add_table(rows=17, cols=len(spalten))
    t.style = "Table Grid"
    for i, (k, b) in enumerate(spalten):
        for zeile in t.rows:
            zeile.cells[i].width = Cm(b)
        r = t.cell(0, i).paragraphs[0].add_run(k); r.bold = True; r.font.size = Pt(12)
    for zeile in t.rows[1:]:
        zeile.height = Cm(1.15)
    d.save(ZIEL)
    print("geschrieben:", ZIEL)


if __name__ == "__main__":
    bauen()
