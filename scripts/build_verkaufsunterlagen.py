"""Unterlagen für die Abwicklung der Verkäufe aus dem Webkatalog.

    python3 scripts/build_verkaufsunterlagen.py

  S2_Verkauf_Ablauf_und_Texte.docx   Checkliste je Vorgang, DATEV-Textbausteine, Mail-Vorlagen
  05_Abholuebersicht.xlsx            Kommissionier- und Abholliste (wer holt wann was, wo steht es)

Die Abholübersicht ist eine Arbeitsdatei der Nutzerin. Sie wird nur einmal erzeugt und
danach von Hand gepflegt – nicht überschreiben, wenn sie schon Einträge hat (--neu erzwingt es).
Das Blatt „Artikel“ darin ist nur das Nachschlageverzeichnis für Bezeichnung und Raum.
"""
import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import AUSGABE, ROT, SCHWARZ, GRAU, FONT, FIRMA, STRASSE, PLZ_ORT, TELEFON, EMAIL
from build_unterlagen_docx import dok_anlegen, p, kopf

from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_BREAK
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import FormulaRule

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATEN = os.path.join(WURZEL, "daten", "artikel_kikripp.csv")
ADRESSE = f"{STRASSE}, {PLZ_ORT}"


# ------------------------------------------------------------------ Word
def schattieren(zelle, farbe):
    tcPr = zelle._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), farbe)
    tcPr.append(shd)


def zellentext(zelle, text, fett=False, groesse=9.5, farbe=SCHWARZ):
    zelle.text = ""
    a = zelle.paragraphs[0]
    a.paragraph_format.space_after = Pt(1)
    lauf = a.add_run(text); lauf.bold = fett; lauf.font.size = Pt(groesse)
    lauf.font.name = FONT; lauf.font.color.rgb = RGBColor.from_string(farbe)


def kasten(d, titel, text):
    """Ein grau hinterlegter Kasten mit Text zum Herauskopieren."""
    p(d, titel, groesse=10, fett=True, vor=6, nach=2)
    t = d.add_table(rows=1, cols=1)
    t.style = "Table Grid"
    z = t.rows[0].cells[0]
    schattieren(z, "F2F2F2")
    z.text = ""
    for i, absatz in enumerate(text.split("\n")):
        a = z.paragraphs[0] if i == 0 else z.add_paragraph()
        a.paragraph_format.space_after = Pt(3)
        lauf = a.add_run(absatz); lauf.font.size = Pt(9.5); lauf.font.name = FONT


def seitenumbruch(d):
    d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


CHECKLISTE = [
    ("Reservierung kommt", "Mail kommt an, Vorgang steht unter Artikelkatalog → Reservierungen. "
     "Innerhalb von 3 Werktagen beim Interessenten melden."),
    ("Käufer sagt zu", "WordPress: „bestellt“ klicken und Abholtermin eintragen. Sonst läuft die "
     "Reservierung nach 3 Werktagen ab und die Ware steht wieder im Katalog."),
    ("Bestellung", "„Bestellung erstellen: Unternehmen“ oder „Privatperson“ → als PDF speichern. "
     "Nicht drucken – sie geht per Mail mit."),
    ("Rechnung", "In DATEV Auftragswesen mit dem Artikel „Verkauf Webkatalog“ und den Textbausteinen "
     "auf Seite 2. Leistungsdatum = Abholtag."),
    ("Mail an den Käufer", "Rechnung und Bestellung als PDF anhängen, Vorlage auf Seite 3."),
    ("Listen", "Excel „Rechnungen (DATEV)“: Zeile mit Rechnungsnr. und „geschrieben am“. "
     "Abholübersicht: je Artikel eine Zeile mit Abholtag und Uhrzeit."),
    ("Geld ist da", "WordPress: „bezahlt“. Excel: „bezahlt am“. Abholübersicht: bezahlt = ja."),
    ("Tag vor der Abholung", "Abholübersicht nach Abholtag filtern, drucken, Ware bereitstellen und "
     "mit Zettel „Name + Vorgangsnummer“ markieren. Bestellung 2× drucken."),
    ("Abholung", "Nur gegen bezahlte Rechnung herausgeben. Beide Exemplare unterschreiben lassen, "
     "eins geht mit. Abholübersicht: abgeholt = ja."),
    ("Abschluss", "Mappe je Vorgang: Bestellung, Rechnung, Zahlungseingang. Kontaktdaten in WordPress "
     "löschen – bei Privatpersonen erst 14 Tage nach der Abholung (Widerrufsfrist)."),
    ("Einmal pro Woche", "Unter Artikelkatalog → Reservierungen die CSV herunterladen und an Claude "
     "schicken, zusammen mit der Excel-Artikelstammliste."),
]

SONDERFAELLE = [
    "Nimmt der Käufer nur einen Teil: Rest in WordPress einzeln stornieren, Rechnung korrigieren.",
    "Keine Zahlung bis zum Termin: einmal erinnern, danach in WordPress „stornieren“.",
    "Privatperson widerruft (14 Tage ab Abholung): Ware zurücknehmen, Geld innerhalb von 14 Tagen "
    "zurücküberweisen, Gutschrift in DATEV.",
]

EINLEITUNG = ("Sehr geehrte Damen und Herren,\n"
              "vielen Dank für Ihre Bestellung aus unserem Artikelkatalog (Vorgang Nr. ___). "
              "Wir berechnen Ihnen die folgenden gebrauchten Artikel aus unserer Betriebsauflösung:")

POSITION = "BE10-12 IKEA Galant Aktenschrank weiß (gebraucht)"

PFLICHT = ("Steuerfreie Lieferung gemäß § 4 Nr. 28 UStG. Die Gegenstände wurden ausschließlich für "
           "Umsätze verwendet, die nach § 4 Nr. 23 UStG steuerfrei waren; ein Vorsteuerabzug war "
           "ausgeschlossen. Umsatzsteuer wird daher nicht berechnet und nicht ausgewiesen.\n"
           "Es handelt sich um gebrauchte Gegenstände, verkauft im vorhandenen Zustand.")
# Das Leistungsdatum steht als „Lieferdatum“ (= Abholtag) im Rechnungskopf von DATEV.

ABSCHLUSS = ("Bitte überweisen Sie den Rechnungsbetrag bis spätestens __.__.2026 unter Angabe der "
             "Rechnungsnummer. Die Ware wird nach Zahlungseingang zum vereinbarten Termin herausgegeben.\n"
             f"Abholung: ________, __.__.2026, __:__ Uhr, {ADRESSE}. Bitte bringen Sie Helfer, Werkzeug "
             "und ein passendes Fahrzeug mit. Nicht bis zum 10.12.2026 abgeholte Ware geht ohne "
             "Erstattung in unser Eigentum zurück.\n"
             "Vielen Dank für Ihren Einkauf.\n"
             f"Mit freundlichen Grüßen\n{FIRMA}")

GEWAEHR_FIRMA = "Die Gewährleistung für Sach- und Rechtsmängel ist ausgeschlossen."
GEWAEHR_PRIVAT = ("Für Verbraucher gelten die gesetzlichen Bestimmungen; die Verjährungsfrist für "
                  "Mängelansprüche beträgt gemäß der gesonderten Vereinbarung in Ihrer Bestellung ein Jahr "
                  "ab Übergabe. Über Ihr gesetzliches Widerrufsrecht informiert Sie die Widerrufsbelehrung "
                  "in Ihrer Bestellung.")


ZUFAHRT = ("Die Zufahrt ist nur über die Peterzeller Straße 8 möglich: am Firmengelände vorbei bis ans "
           "Ende durchfahren, das Gebäude liegt auf der rechten Seite.")


def mail(privat, du=False):
    """Mail an den Käufer – Wortlaut der Nutzerin vom 08.10.2026, in Sie- und Du-Form."""
    if du:
        zeilen = [
            "Betreff: Deine Bestellung Nr. [Vorgang] – Rechnung und Abholtermin", "",
            "Hallo [Vorname],", "",
            "vielen Dank für deine Reservierung! Anbei findest du die Rechnung Nr. [Rechnungsnr.] und deine Bestellung.", "",
            "Bitte überweise den Rechnungsbetrag zeitnah unter Angabe der Rechnungsnummer auf das angegebene Konto. "
            "Die Bestellung kannst du uns unterschrieben per Scan zurückschicken oder bei der Abholung unterschreiben.", "",
            "Dein Abholtermin am [Wochentag], [Datum] um [Uhrzeit] Uhr ist mit dem Zahlungseingang bestätigt – "
            "die Ware geben wir erst nach Zahlungseingang heraus.", "",
            f"Abholadresse: {ADRESSE}",
            ZUFAHRT,
            "Bitte bring ausreichend Helfer, Werkzeug und ein passendes Fahrzeug mit.",
        ]
        if privat:
            zeilen += ["", "Die Widerrufsbelehrung und das Widerrufsformular findest du in der beigefügten Bestellung."]
        zeilen += ["", f"Bei Fragen erreichst du uns unter {TELEFON} oder {EMAIL}.", "",
                   "Viele Grüße", "[Name]", FIRMA]
        return "\n".join(zeilen)
    zeilen = [
        "Betreff: Ihre Bestellung Nr. [Vorgang] – Rechnung und Abholtermin", "",
        ("Guten Tag [Frau/Herr Name]," if privat else "Sehr geehrte Damen und Herren, / Guten Tag [Frau/Herr Name],"), "",
        ("vielen Dank für Ihre Reservierung. Anbei erhalten Sie die Rechnung Nr. [Rechnungsnr.] und Ihre Bestellung."
         if privat else
         "vielen Dank für Ihre Reservierung aus unserem Artikelkatalog. Anbei erhalten Sie die Rechnung "
         "Nr. [Rechnungsnr.] und die Bestellung für [Firma]."), "",
        "Bitte überweisen Sie den Rechnungsbetrag zeitnah unter Angabe der Rechnungsnummer auf das angegebene Konto. "
        "Die Bestellung senden Sie uns bitte unterschrieben per Scan zurück oder unterschreiben sie bei der Abholung.", "",
        "Ihr Abholtermin am [Wochentag], [Datum] um [Uhrzeit] Uhr ist mit dem Zahlungseingang bestätigt – "
        "die Ware geben wir erst nach Zahlungseingang heraus.", "",
        f"Abholadresse: {ADRESSE}",
        ZUFAHRT,
        "Bitte bringen Sie ausreichend Helfer, Werkzeug und ein passendes Fahrzeug mit.",
    ]
    if privat:
        zeilen += ["", "Die Widerrufsbelehrung und das Widerrufsformular finden Sie in der beigefügten Bestellung."]
    zeilen += ["", f"Bei Fragen erreichen Sie uns unter {TELEFON} oder {EMAIL}.", "",
               "Mit freundlichen Grüßen", "[Name]", FIRMA]
    return "\n".join(zeilen)


def word():
    d = dok_anlegen()
    kopf(d, "Verkauf aus dem Webkatalog", "Ablauf je Vorgang – zum Abhaken")
    t = d.add_table(rows=1, cols=3)
    t.style = "Table Grid"
    for z, (txt, b) in zip(t.rows[0].cells, (("☐", 0.8), ("Schritt", 3.6), ("Was zu tun ist", 11.4))):
        zellentext(z, txt, fett=True, farbe="FFFFFF"); schattieren(z, "C8102E"); z.width = Cm(b)
    for i, (schritt, was) in enumerate(CHECKLISTE, 1):
        r = t.add_row().cells
        zellentext(r[0], "☐", groesse=12); zellentext(r[1], f"{i}. {schritt}", fett=True); zellentext(r[2], was)
        for z, b in zip(r, (0.8, 3.6, 11.4)): z.width = Cm(b)
    p(d, "Sonderfälle", groesse=11, fett=True, vor=10, nach=3)
    for s in SONDERFAELLE:
        d.add_paragraph(s, style="List Bullet").paragraph_format.space_after = Pt(2)

    seitenumbruch(d)
    kopf(d, "Rechnung in DATEV Auftragswesen", "Artikel anlegen und Textbausteine zum Kopieren")
    p(d, "Artikel anlegen (einmalig)", groesse=11, fett=True, nach=3)
    for s in ["Bezeichnung: Verkauf Webkatalog",
              "Steuer: steuerfrei / 0 % – keine Umsatzsteuer",
              "Erlöskonto (SKR 04): Vorschlag 4849 „Erlöse aus Verkäufen Sachanlagevermögen (bei Buchgewinn)“ "
              "– bitte vor der ersten Rechnung mit dem Steuerberater abstimmen (siehe unten)",
              "Preis: leer lassen, je Rechnung von Hand",
              "In jeder Position den Text ändern: Artikelnummer und Bezeichnung aus unserer Liste, z. B.:"]:
        d.add_paragraph(s, style="List Bullet").paragraph_format.space_after = Pt(2)
    p(d, POSITION, groesse=9.5, kursiv=True, vor=2, nach=6)
    kasten(d, "Einleitungstext", EINLEITUNG)
    kasten(d, "Pflichtangaben (auf jede Rechnung)", PFLICHT)
    kasten(d, "Gewährleistung (beide Sätze stehen auf jeder Rechnung)", GEWAEHR_PRIVAT + "\nBei Unternehmen: " + GEWAEHR_FIRMA)
    kasten(d, "Schlusstext", ABSCHLUSS)
    kasten(d, "Fußzeile (Pflicht für die GmbH, § 35a GmbHG)",
           "Sitz: Villingen-Schwenningen · Amtsgericht Freiburg i. Br. HRB 707915 · Geschäftsführung: Marisa Faißt-Neininger\n"
           "Steuernummer und/oder USt-IdNr. (mindestens eine davon ist Pflicht)")
    p(d, "Lieferdatum im Rechnungskopf = Abholtag. Eine Zeile je Artikelnummer, Stückzahl in die Spalte Menge.",
      groesse=9.5, kursiv=True, vor=4)
    p(d, "Zum Erlöskonto", groesse=10, fett=True, vor=10, nach=2)
    p(d, "Ein eigenes Konto ist richtig: Verkauft werden Gegenstände der Einrichtung, keine laufenden "
         "Leistungen. Die meisten Möbel und Geräte sind Anlagevermögen und abgeschrieben oder geringwertig "
         "(Restbuchwert 0) – dann entsteht ein Buchgewinn, dafür ist 4849 gedacht. Der Steuerberater muss "
         "den Anlagenabgang buchen und die steuerfreien Umsätze in der Umsatzsteuer-Voranmeldung melden "
         "(Kennzahl 48, steuerfrei ohne Vorsteuerabzug). Ob er dafür 4849 oder ein anderes Konto möchte – "
         "etwa für Verbrauchsmaterial –, entscheidet er. Das ist ein Vorschlag, keine Steuerberatung.",
      groesse=9.5, nach=4)

    seitenumbruch(d)
    kopf(d, "Mail an den Käufer", "Vorlage – Rechnung und Bestellung als PDF anhängen")
    kasten(d, "Sie – Privatperson", mail(True))
    kasten(d, "Du – Privatperson", mail(True, du=True))
    kasten(d, "Unternehmen (ohne Widerrufsbelehrung – Firmen haben kein Widerrufsrecht)", mail(False))
    ziel = os.path.join(AUSGABE, "S2_Verkauf_Ablauf_und_Texte.docx")
    d.save(ziel)
    print("geschrieben:", ziel)


# ------------------------------------------------------------------ Excel
SPALTEN = [  # (Überschrift, Breite, ausfüllen?)
    ("Abholtag", 11, True), ("Uhrzeit", 8, True), ("Vorgang", 8, True), ("Käufer", 22, True),
    ("Telefon", 15, True), ("Rechnungsnr.", 12, True), ("bezahlt", 8, True), ("ArtNr", 10, True),
    ("Bezeichnung", 34, False), ("Raum (Post-it)", 22, False), ("Menge", 7, True), ("Einheit", 9, False),
    ("Demontage", 10, True), ("bereit-gestellt", 9, True), ("abgeholt", 9, True), ("Bemerkung", 26, True),
]
ZEILEN = 400


def excel(neu):
    ziel = os.path.join(AUSGABE, "05_Abholuebersicht.xlsx")
    if os.path.exists(ziel) and not neu:
        ws = load_workbook(ziel)["Abholungen"]
        if any(ws.cell(r, 1).value or ws.cell(r, 8).value for r in range(5, 5 + ZEILEN)):
            print("übersprungen:", ziel, "enthält schon Einträge (--neu überschreibt)")
            return

    with open(DATEN, encoding="utf-8") as f:
        artikel = [r for r in csv.DictReader(f, delimiter=";") if r["Aktiv"] == "ja"]

    wb = Workbook()
    ws = wb.active
    ws.title = "Abholungen"
    rot = PatternFill("solid", fgColor="C8102E")
    grau = PatternFill("solid", fgColor="F2F2F2")
    duenn = Side(style="thin", color="BFBFBF")
    rahmen = Border(left=duenn, right=duenn, top=duenn, bottom=duenn)

    ws["A1"] = "Abholübersicht – wer holt wann was ab"
    ws["A1"].font = Font(name=FONT, size=14, bold=True, color="C8102E")
    ws["A2"] = ("Je Artikel eine Zeile. Grau = ausfüllen, Bezeichnung, Raum und Einheit ergänzen sich aus der "
                "Artikelnummer. Vor dem Abholtag: Filter in Zeile 4 auf den Tag setzen und drucken (Querformat).")
    ws["A2"].font = Font(name=FONT, size=9, italic=True, color="595959")
    for i, (titel, breite, _) in enumerate(SPALTEN, 1):
        z = ws.cell(4, i, titel)
        z.font = Font(name=FONT, bold=True, color="FFFFFF", size=10)
        z.fill = rot
        z.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
        z.border = rahmen
        ws.column_dimensions[z.column_letter].width = breite
    ws.row_dimensions[4].height = 30

    for r in range(5, 5 + ZEILEN):
        for i, (_, _, aus) in enumerate(SPALTEN, 1):
            z = ws.cell(r, i)
            z.border = rahmen
            z.font = Font(name=FONT, size=10)
            z.alignment = Alignment(vertical="center", wrap_text=i in (9, 10, 16))
            if aus:
                z.fill = grau
        ws.cell(r, 1).number_format = "ddd dd.mm.yy"
        ws.cell(r, 9, f'=IF(H{r}="","",IFERROR(VLOOKUP(H{r},Artikel!$A:$E,2,FALSE),"? Nummer prüfen"))')
        ws.cell(r, 10, f'=IF(H{r}="","",IFERROR(VLOOKUP(H{r},Artikel!$A:$E,3,FALSE)&" ("&VLOOKUP(H{r},Artikel!$A:$E,4,FALSE)&")",""))')
        ws.cell(r, 12, f'=IF(H{r}="","",IFERROR(VLOOKUP(H{r},Artikel!$A:$E,5,FALSE),""))')

    bereich = f"5:{4 + ZEILEN}"
    jn = DataValidation(type="list", formula1='"ja,nein"', allow_blank=True)
    zeit = DataValidation(type="list", formula1='"08:00,08:30,09:00,09:30,10:00,10:30,Fr nachm.,Sa vorm."', allow_blank=True)
    datum = DataValidation(type="date", operator="between", formula1="DATE(2026,10,1)", formula2="DATE(2026,12,31)",
                           allow_blank=True, error="Bitte ein Datum zwischen Oktober und Dezember 2026 eingeben.")
    for dv in (jn, zeit, datum): ws.add_data_validation(dv)
    datum.add(f"A5:A{4 + ZEILEN}"); zeit.add(f"B5:B{4 + ZEILEN}")
    for sp in "GMNO": jn.add(f"{sp}5:{sp}{4 + ZEILEN}")

    ende = 4 + ZEILEN
    # abgeholt: ganze Zeile grau und durchgestrichen · bereitgestellt aber nicht bezahlt: orange
    ws.conditional_formatting.add(f"A5:P{ende}", FormulaRule(formula=['$O5="ja"'],
        font=Font(color="808080", strike=True), fill=PatternFill("solid", fgColor="E7E6E6")))
    ws.conditional_formatting.add(f"A5:P{ende}", FormulaRule(formula=['AND($A5<>"",$G5<>"ja",$A5-TODAY()<=1)'],
        fill=PatternFill("solid", fgColor="FCE4D6")))
    ws.conditional_formatting.add(f"I5:I{ende}", FormulaRule(formula=['LEFT($I5,1)="?"'], font=Font(color="C8102E", bold=True)))

    ws.freeze_panes = "A5"
    ws.auto_filter.ref = f"A4:P{ende}"
    ws.print_title_rows = "4:4"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1; ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.oddFooter.center.text = "Seite &P von &N"
    ws.oddHeader.left.text = "Abholübersicht Kikripp GmbH"
    ws.oddHeader.right.text = "Stand &D"

    erkl = wb.create_sheet("So geht's")
    for i, (a, b) in enumerate([
        ("Abholübersicht", "Damit am Abholtag alles bereitsteht und nichts doppelt verkauft wird."),
        ("Eintragen", "Sobald ein Abholtermin feststeht: je Artikel eine Zeile. Abholtag, Uhrzeit, Vorgang, Käufer, "
                      "Telefon, ArtNr und Menge. Bezeichnung und Raum erscheinen von selbst."),
        ("Raum (Post-it)", "Der Raum aus dem Katalog, in Klammern der Code auf dem Post-it am Möbel (z. B. BE10)."),
        ("bezahlt", "Erst „ja“, wenn das Geld auf dem Konto ist. Orange Zeile = Abholung morgen oder heute, aber "
                    "noch nicht bezahlt."),
        ("Vor dem Abholtag", "Filter in Zeile 4 beim Abholtag auf den Tag setzen → drucken. Ware bereitstellen, "
                             "mit Name + Vorgangsnummer markieren, dann „bereitgestellt“ = ja."),
        ("Bei der Abholung", "Ausdruck abhaken, danach „abgeholt“ = ja – die Zeile wird grau durchgestrichen."),
        ("Teilabholung", "Was nicht mitgeht: in der Bemerkung vermerken, in WordPress die Position stornieren."),
        ("Neue Artikel", "Kommt eine neue Artikelnummer dazu, die hier „? Nummer prüfen“ zeigt: von Claude eine "
                         "neue Abholübersicht holen oder die Bezeichnung von Hand in die Bemerkung schreiben."),
    ], 1):
        erkl.cell(i, 1, a).font = Font(name=FONT, bold=True, size=10)
        z = erkl.cell(i, 2, b); z.font = Font(name=FONT, size=10); z.alignment = Alignment(wrap_text=True, vertical="top")
        erkl.cell(i, 1).alignment = Alignment(vertical="top")
    erkl.column_dimensions["A"].width = 18; erkl.column_dimensions["B"].width = 95

    nach = wb.create_sheet("Artikel")
    for i, t in enumerate(("ArtNr", "Bezeichnung", "Raum", "Raumcode", "Einheit"), 1):
        nach.cell(1, i, t).font = Font(name=FONT, bold=True)
    for r, a in enumerate(artikel, 2):
        for i, k in enumerate(("ArtNr", "Bezeichnung", "Raum", "Raumcode", "Einheit"), 1):
            nach.cell(r, i, a[k])
    for sp, b in zip("ABCDE", (11, 45, 24, 10, 10)): nach.column_dimensions[sp].width = b
    nach.protection.sheet = True
    nach.sheet_state = "visible"

    wb.save(ziel)
    print("geschrieben:", ziel, f"({len(artikel)} Artikel im Verzeichnis, {ZEILEN} Zeilen)")


if __name__ == "__main__":
    word()
    excel("--neu" in sys.argv)
