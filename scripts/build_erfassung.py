"""Erzeugt die Unterlagen für den Rundgang durchs Haus.

    python3 scripts/build_erfassung.py

Drei Dateien in `ausgabe/`:

  T1_Tuerschilder.docx    fünf Räume je A4-Blatt, zum Ausschneiden und Ankleben
  T2_Erfassungsblaetter.docx  ein Blatt je Raum, vorgedruckte Artikelnummern
  T3_Erfassungsliste.xlsx     dieselben Nummern zum Abtippen der Stückzahlen

Auf den Erfassungsblättern stehen die bereits erfassten Artikel oben mit Nummer
und Kurzbezeichnung — dann muss beim Rundgang niemand nachschlagen, welche
Nummer auf welchen Gegenstand gehört.
"""
import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import AUSGABE, BASIS, CSV_PFAD, ROT, SCHWARZ, GRAU, FONT, FIRMA

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.table import WD_ROW_HEIGHT_RULE
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

from openpyxl import Workbook
from openpyxl.styles import Font as XFont, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation

RAEUME_PFAD = os.path.join(BASIS, "daten", "raeume.csv")
RESERVE = 10          # freie Zeilen über den schon erfassten Artikeln hinaus


def zeilenzahl(raum, bereits):
    """Zeilen je Raum: nach Fläche, mindestens die schon erfassten plus Reserve."""
    vorgabe = (raum.get("Zeilen") or "").strip()
    if vorgabe.isdigit():
        nach_flaeche = int(vorgabe)
    else:
        f = (raum.get("Flaeche_m2") or "").replace(".", "").replace(",", ".")
        try:
            qm = float(f)
        except ValueError:
            qm = 20.0
        nach_flaeche = 5 if qm < 5 else 15 if qm < 20 else 25 if qm <= 40 else 40
    return max(nach_flaeche, bereits + RESERVE)


def lade():
    with open(RAEUME_PFAD, encoding="utf-8") as f:
        raeume = list(csv.DictReader(f, delimiter=";"))
    with open(CSV_PFAD, encoding="utf-8") as f:
        artikel = [a for a in csv.DictReader(f, delimiter=";")
                   if (a.get("Aktiv") or "ja").lower() != "entfällt"]
    je_raum = {}
    for a in artikel:
        je_raum.setdefault(a["Raumcode"], []).append(a)
    for v in je_raum.values():
        v.sort(key=lambda a: a["ArtNr"])
    return raeume, je_raum


# ------------------------------------------------------------------ Werkzeug

def grundschrift(dok):
    st = dok.styles["Normal"]
    st.font.name = FONT
    st.font.size = Pt(10)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    for p in st.element.findall(qn("w:pPr")):
        p.clear()


def rand(dok, oben=1.4, unten=1.2, links=1.6, rechts=1.6):
    for s in dok.sections:
        s.top_margin, s.bottom_margin = Cm(oben), Cm(unten)
        s.left_margin, s.right_margin = Cm(links), Cm(rechts)


def zeile(absatz, text, groesse=10, fett=False, farbe=SCHWARZ, abstand_vor=0, abstand_nach=0):
    absatz.paragraph_format.space_before = Pt(abstand_vor)
    absatz.paragraph_format.space_after = Pt(abstand_nach)
    lauf = absatz.add_run(text)
    lauf.font.name = FONT
    lauf.font.size = Pt(groesse)
    lauf.bold = fett
    lauf.font.color.rgb = RGBColor.from_string(farbe)
    return lauf


def linie_unten(zellen, farbe="BFBFBF", staerke="6"):
    for z in zellen:
        tcPr = z._tc.get_or_add_tcPr()
        borders = OxmlElement("w:tcBorders")
        b = OxmlElement("w:bottom")
        b.set(qn("w:val"), "single"); b.set(qn("w:sz"), staerke)
        b.set(qn("w:color"), farbe)
        borders.append(b); tcPr.append(borders)


# ------------------------------------------------------- 1. Türschilder

def tuerschilder(raeume):
    dok = Document(); grundschrift(dok); rand(dok, 1.0, 1.0, 1.4, 1.4)

    for i, r in enumerate(raeume):
        if i and i % 5 == 0:
            dok.add_page_break()

        t = dok.add_table(rows=1, cols=1)
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.columns[0].width = Cm(17.5)
        zelle = t.cell(0, 0)
        zelle.width = Cm(17.5)

        p = zelle.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        zeile(p, r["Raumcode"], groesse=48, fett=True, farbe=ROT, abstand_vor=6, abstand_nach=2)

        p = zelle.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        zeile(p, r["Raumname"], groesse=20, fett=True, abstand_nach=1)

        p = zelle.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        ebene = r["Ebene"] if r["Ebene"] != "-" else ""
        zeile(p, " · ".join(x for x in (r["Gebaeude"], ebene) if x),
              groesse=11, farbe=GRAU, abstand_nach=6)

        p = zelle.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        zeile(p, "Inventarerfassung – bitte nicht entfernen", groesse=8, farbe=GRAU, abstand_nach=6)

        linie_unten([zelle], farbe="808080", staerke="8")

        p = dok.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        zeile(p, "✂ " + "– " * 28, groesse=7, farbe="BFBFBF", abstand_vor=2, abstand_nach=2)

    ziel = os.path.join(AUSGABE, "T1_Tuerschilder.docx")
    dok.save(ziel)
    return ziel, len(raeume)


# ------------------------------------------------- 2. Erfassungsblätter

def erfassungsblaetter(raeume, je_raum):
    dok = Document(); grundschrift(dok); rand(dok)
    gesamt_zeilen = 0

    for i, r in enumerate(raeume):
        if i:
            dok.add_page_break()
        code = r["Raumcode"]
        bereits = je_raum.get(code, [])
        anzahl = zeilenzahl(r, len(bereits))
        gesamt_zeilen += anzahl

        # Kopf
        p = dok.add_paragraph()
        zeile(p, code, groesse=28, fett=True, farbe=ROT, abstand_nach=0)
        p = dok.add_paragraph()
        zeile(p, r["Raumname"], groesse=15, fett=True, abstand_nach=0)
        p = dok.add_paragraph()
        ebene = r["Ebene"] if r["Ebene"] != "-" else ""
        kopf = " · ".join(x for x in (r["Gebaeude"], ebene) if x)
        if r.get("Flaeche_m2"):
            kopf += f" · {r['Flaeche_m2']} m²"
        if r.get("Bemerkung"):
            kopf += f" · {r['Bemerkung']}"
        zeile(p, kopf, groesse=9, farbe=GRAU, abstand_nach=10)

        # Tabelle
        t = dok.add_table(rows=1, cols=4)
        t.style = "Table Grid"
        breiten = (Cm(2.6), Cm(8.4), Cm(2.2), Cm(4.6))
        kopfzeile = ("Nummer", "Artikel", "Stück", "Bemerkung")
        for sp, (txt, br) in enumerate(zip(kopfzeile, breiten)):
            z = t.cell(0, sp); z.width = br
            z._tc.get_or_add_tcPr().append(
                _schattierung(SCHWARZ))
            zeile(z.paragraphs[0], txt, groesse=9, fett=True, farbe="FFFFFF")
        _kopf_wiederholen(t.rows[0])

        for n in range(1, anzahl + 1):
            nummer = f"{code}-{n:02d}"
            art = bereits[n - 1] if n <= len(bereits) else None
            rz = t.add_row()
            for sp, br in enumerate(breiten):
                rz.cells[sp].width = br
            rz.height = Cm(0.85)
            rz.height_rule = WD_ROW_HEIGHT_RULE.AT_LEAST

            zeile(rz.cells[0].paragraphs[0], nummer, groesse=10,
                  fett=art is not None, farbe=SCHWARZ if art else GRAU)
            if art:
                zeile(rz.cells[1].paragraphs[0], art["Bezeichnung"][:60], groesse=9)
                menge = f"{art['Menge']} {art['Einheit']}"
                zeile(rz.cells[2].paragraphs[0], menge, groesse=8, farbe=GRAU)
                for z in rz.cells:
                    z._tc.get_or_add_tcPr().append(_schattierung("F2F2F2"))

        p = dok.add_paragraph()
        zeile(p, f"bereits erfasst: {len(bereits)}   ·   freie Nummern: {anzahl - len(bereits)}"
                 f"   ·   nächste freie Nummer: {code}-{len(bereits)+1:02d}",
              groesse=8, farbe=GRAU, abstand_vor=8)
        p = dok.add_paragraph()
        zeile(p, "Grau hinterlegte Zeilen sind schon erfasst — dort nur die Stückzahl prüfen. "
                 "Für jeden weiteren Gegenstand die nächste freie Nummer auf einen Post-it "
                 "schreiben, ankleben und fotografieren.",
              groesse=8, farbe=GRAU)
        p = dok.add_paragraph()
        zeile(p, f"{FIRMA} · Betriebsauflösung · Blatt {i+1} von {len(raeume)}",
              groesse=7, farbe=GRAU, abstand_vor=6)

    ziel = os.path.join(AUSGABE, "T2_Erfassungsblaetter.docx")
    dok.save(ziel)
    return ziel, gesamt_zeilen


def _kopf_wiederholen(zeile_obj):
    trPr = zeile_obj._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader")
    el.set(qn("w:val"), "true")
    trPr.append(el)


def _schattierung(hexfarbe):
    el = OxmlElement("w:shd")
    el.set(qn("w:val"), "clear"); el.set(qn("w:color"), "auto")
    el.set(qn("w:fill"), hexfarbe)
    return el


# --------------------------------------------------- 3. Erfassungsliste

def erfassungsliste(raeume, je_raum):
    EUR = '#,##0.00 "€"'
    d = Side(style="thin", color="DCDCDC")
    rahmen = Border(left=d, right=d, top=d, bottom=d)

    wb = Workbook(); ws = wb.active; ws.title = "Erfassung"
    spalten = [("Nummer", 12), ("Gebäude", 17), ("Ebene", 10), ("Raum", 24),
               ("Artikel", 42), ("Stückzahl", 11), ("Einheit", 10), ("Bemerkung", 34)]
    for i, (name, br) in enumerate(spalten, start=1):
        ws.cell(row=1, column=i, value=name)
        ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = br
    for c in ws[1]:
        c.fill = PatternFill("solid", fgColor=SCHWARZ)
        c.font = XFont(name=FONT, size=10, bold=True, color="FFFFFF")
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = rahmen
    ws.row_dimensions[1].height = 24

    r = 2
    for raum in raeume:
        code = raum["Raumcode"]
        bereits = je_raum.get(code, [])
        anzahl = zeilenzahl(raum, len(bereits))
        for n in range(1, anzahl + 1):
            art = bereits[n - 1] if n <= len(bereits) else None
            werte = [f"{code}-{n:02d}", raum["Gebaeude"],
                     raum["Ebene"] if raum["Ebene"] != "-" else "",
                     raum["Raumname"],
                     art["Bezeichnung"] if art else None,
                     int(art["Menge"]) if art and str(art["Menge"]).isdigit() else None,
                     art["Einheit"] if art else None, None]
            for i, w in enumerate(werte, start=1):
                c = ws.cell(row=r, column=i, value=w)
                c.font = XFont(name=FONT, size=10, color=SCHWARZ)
                c.border = rahmen
                if art:
                    c.fill = PatternFill("solid", fgColor="F2F2F2")
                if i == 6:
                    c.fill = PatternFill("solid", fgColor="E4E4E4")
                    c.alignment = Alignment(horizontal="center")
            r += 1

    letzte = r - 1
    dv = DataValidation(type="whole", operator="greaterThan", formula1="0",
                        allow_blank=True, showErrorMessage=True,
                        errorTitle="Stückzahl", error="Bitte eine ganze Zahl größer 0 eintragen.")
    ws.add_data_validation(dv)
    dv.add(f"F2:F{letzte}")

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:H{letzte}"
    ws.sheet_view.showGridLines = False

    # Kurze Anleitung als zweites Blatt
    an = wb.create_sheet("Anleitung")
    an.column_dimensions["A"].width = 112
    texte = [
        ("So wird die Liste benutzt", True, 14),
        ("", False, 10),
        ("Grau hinterlegte Zeilen sind bereits erfasst. Dort bitte nur prüfen, ob die "
         "Stückzahl noch stimmt, und sie gegebenenfalls überschreiben.", False, 10),
        ("Alle übrigen Zeilen sind freie Nummern. Für jeden Gegenstand, den ihr aufnimmt, "
         "die nächste freie Nummer auf einen Post-it schreiben, ankleben, fotografieren "
         "und hier die Stückzahl eintragen.", False, 10),
        ("Die Spalte „Artikel“ muss nicht ausgefüllt werden — Bezeichnung und Beschreibung "
         "entstehen aus dem Foto. Wer mag, kann ein Schlagwort hineinschreiben.", False, 10),
        ("In „Bemerkung“ gehört alles, was auf dem Foto nicht zu sehen ist: Defekte, "
         "Maße, Typenschild-Angaben, „gehört nicht dazu“.", False, 10),
        ("", False, 10),
        ("Nicht ändern: die Spalte „Nummer“ und die Raumangaben. Daran wird die Liste "
         "wieder eingelesen.", True, 10),
        ("Zeilen, die leer bleiben, werden ignoriert. Es ist also kein Problem, wenn in "
         "einem Raum weniger Gegenstände stehen als Nummern vorgedruckt sind.", False, 10),
    ]
    for i, (txt, fett, gr) in enumerate(texte, start=1):
        c = an.cell(row=i, column=1, value=txt)
        c.font = XFont(name=FONT, size=gr, bold=fett, color=SCHWARZ)
        c.alignment = Alignment(wrap_text=True, vertical="top")
        an.row_dimensions[i].height = 30 if len(txt) > 90 else 16
    an.sheet_view.showGridLines = False

    ziel = os.path.join(AUSGABE, "T3_Erfassungsliste.xlsx")
    wb.save(ziel)
    return ziel, letzte - 1


if __name__ == "__main__":
    raeume, je_raum = lade()
    p1, n1 = tuerschilder(raeume)
    p2, n2 = erfassungsblaetter(raeume, je_raum)
    p3, n3 = erfassungsliste(raeume, je_raum)
    for p, n, was in ((p1, n1, "Türschilder"), (p2, n2, "Zeilen"), (p3, n3, "Zeilen")):
        print(f"geschrieben: {p}  ({n} {was}, {os.path.getsize(p)//1024} KB)")
    print(f"\n{len(raeume)} Räume · {sum(len(v) for v in je_raum.values())} bereits erfasste Artikel")
