"""Erzeugt 02_Angebot_Klinik_BEISPIEL.xlsx - die Auswahlliste zum Zurueckschicken."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import lade_artikel, foto, BASIS, USt_SATZ

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.drawing.image import Image as XLImage
from openpyxl.utils import get_column_letter
from PIL import Image as PILImage

FONT = "Arial"; DUNKEL = "1F3864"; MITTEL = "2E5A9C"; GELB = "FFF2CC"; HELL = "D9E2F3"
EUR = '#,##0.00 "€"'
ANGEBOT_NR = "ANG-2026-0007"; DATUM = "15.09.2026"; GUELTIG = "30.09.2026"

SPALTEN = [("Pos", 5), ("ArtNr", 9), ("Foto", 20), ("Artikel", 46), ("Zustand", 13),
           ("Status", 12), ("Verfügbar", 10), ("Einheit", 9), ("Einzelpreis netto", 15),
           ("Preis", 8), ("Lieferung", 16), ("Ihre Wunschmenge", 13),
           ("Ihre Bemerkung / Frage", 30), ("Summe netto", 14)]
IDX = {s[0]: i + 1 for i, s in enumerate(SPALTEN)}
def L(n): return get_column_letter(IDX[n])

artikel = [a for a in lade_artikel() if a["Kanal"] == "Klinik" and a["Status"] != "verkauft"]

wb = Workbook(); ws = wb.active; ws.title = "Angebot"
for name, breite in SPALTEN:
    ws.column_dimensions[get_column_letter(IDX[name])].width = breite

# ---- Kopf -------------------------------------------------------------------
ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(SPALTEN))
c = ws.cell(row=1, column=1, value="Kinderkrippe Musterstadt GmbH – Angebot aus Betriebsauflösung")
c.font = Font(name=FONT, size=16, bold=True, color="FFFFFF")
c.fill = PatternFill("solid", fgColor=DUNKEL)
c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
ws.row_dimensions[1].height = 30

kopf = [("Angebot-Nr.", ANGEBOT_NR, "Datum", DATUM),
        ("Empfänger", "Klinikum Musterstadt, Frau Muster (Einkauf)", "Angebot gültig bis", GUELTIG),
        ("Ansprechpartnerin", "J. Preisigke · 0123 456789 · info@kikripp.de", "Alle Preise", "netto zzgl. 19 % USt")]
for i, (a, b, cc, d) in enumerate(kopf, start=2):
    ws.cell(row=i, column=1, value=a).font = Font(name=FONT, size=10, bold=True)
    ws.merge_cells(start_row=i, start_column=2, end_row=i, end_column=6)
    ws.cell(row=i, column=2, value=b).font = Font(name=FONT, size=10)
    ws.cell(row=i, column=8, value=cc).font = Font(name=FONT, size=10, bold=True)
    ws.merge_cells(start_row=i, start_column=9, end_row=i, end_column=len(SPALTEN))
    ws.cell(row=i, column=9, value=d).font = Font(name=FONT, size=10)

ws.merge_cells(start_row=5, start_column=1, end_row=5, end_column=len(SPALTEN))
c = ws.cell(row=5, column=1, value="So geht's: Bitte tragen Sie in den gelben Spalten ein, welche Artikel Sie in "
                                  "welcher Menge übernehmen möchten, und schicken die Datei zurück. "
                                  "Die Summe rechnet sich automatisch. Abholung nach Terminvereinbarung, "
                                  "Zahlung per Rechnung.")
c.font = Font(name=FONT, size=10, italic=True, color="7F6000")
c.fill = PatternFill("solid", fgColor=GELB)
c.alignment = Alignment(vertical="center", wrap_text=True, indent=1)
ws.row_dimensions[5].height = 30

# ---- Tabellenkopf -----------------------------------------------------------
KOPF = 7
duenn = Side(style="thin", color="BFBFBF")
for name, _b in SPALTEN:
    c = ws.cell(row=KOPF, column=IDX[name], value=name)
    c.font = Font(name=FONT, size=10, bold=True, color="FFFFFF")
    c.fill = PatternFill("solid", fgColor=GELB if name.startswith("Ihre") else MITTEL)
    if name.startswith("Ihre"):
        c.font = Font(name=FONT, size=10, bold=True, color="7F6000")
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border = Border(left=duenn, right=duenn, top=duenn, bottom=duenn)
ws.row_dimensions[KOPF].height = 32

# ---- Positionen -------------------------------------------------------------
Z0 = KOPF + 1
for i, a in enumerate(artikel):
    r = Z0 + i
    rest = (a["Menge"] or 0) - (a["Verkauft_Menge"] or 0)
    werte = {
        "Pos": i + 1, "ArtNr": a["ArtNr"], "Foto": None,
        "Artikel": f'{a["Bezeichnung"]}\n{a["Beschreibung"]}',
        "Zustand": a["Zustand"], "Status": a["Status"], "Verfügbar": rest,
        "Einheit": a["Einheit"], "Einzelpreis netto": a["Preis_netto"],
        "Preis": a["Preisbasis"], "Lieferung": a["Versand"],
        "Ihre Wunschmenge": None, "Ihre Bemerkung / Frage": None,
        "Summe netto": f'=IF({L("Ihre Wunschmenge")}{r}="","",'
                       f'{L("Ihre Wunschmenge")}{r}*{L("Einzelpreis netto")}{r})',
    }
    for name, _b in SPALTEN:
        c = ws.cell(row=r, column=IDX[name], value=werte[name])
        c.font = Font(name=FONT, size=10)
        c.border = Border(left=duenn, right=duenn, top=duenn, bottom=duenn)
        c.alignment = Alignment(vertical="center", wrap_text=name in ("Artikel", "Lieferung"),
                                horizontal="center" if name in ("Pos", "ArtNr", "Verfügbar",
                                "Einheit", "Preis", "Zustand", "Status", "Ihre Wunschmenge") else "left")
        if name in ("Einzelpreis netto", "Summe netto"):
            c.number_format = EUR
        if name.startswith("Ihre"):
            c.fill = PatternFill("solid", fgColor=GELB)
        if a["Status"] == "reserviert" and name == "Status":
            c.font = Font(name=FONT, size=10, bold=True, color="BF8F00")
    ws.row_dimensions[r].height = 78
    p = foto(a["ArtNr"])
    if p:
        with PILImage.open(p) as im:
            im.thumbnail((132, 99))
            tmp = f"/tmp/xl_{a['ArtNr']}.png"
            im.save(tmp)
        img = XLImage(tmp)
        ws.add_image(img, f'{L("Foto")}{r}')

# ---- Summen -----------------------------------------------------------------
Z1 = Z0 + len(artikel) - 1
sums = [("Zwischensumme netto", f'=SUM({L("Summe netto")}{Z0}:{L("Summe netto")}{Z1})', False),
        (f"zzgl. {int(USt_SATZ*100)} % Umsatzsteuer", f'={L("Summe netto")}{Z1+1}*{USt_SATZ}', False),
        ("Gesamtsumme brutto", f'={L("Summe netto")}{Z1+1}+{L("Summe netto")}{Z1+2}', True)]
for j, (label, formel, fett) in enumerate(sums):
    r = Z1 + 1 + j
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=IDX["Ihre Bemerkung / Frage"])
    c = ws.cell(row=r, column=1, value=label)
    c.font = Font(name=FONT, size=11, bold=True, color=DUNKEL)
    c.alignment = Alignment(horizontal="right", vertical="center")
    c = ws.cell(row=r, column=IDX["Summe netto"], value=formel)
    c.font = Font(name=FONT, size=11, bold=fett, color=DUNKEL)
    c.number_format = EUR
    c.fill = PatternFill("solid", fgColor=HELL if fett else "FFFFFF")
    c.border = Border(left=duenn, right=duenn, top=duenn, bottom=duenn)
    ws.row_dimensions[r].height = 20

fuss = Z1 + 5
ws.merge_cells(start_row=fuss, start_column=1, end_row=fuss + 2, end_column=len(SPALTEN))
c = ws.cell(row=fuss, column=1, value=
    "Hinweise: Verkauf erfolgt unter Ausschluss jeglicher Gewährleistung (Verkauf aus Betriebsauflösung, "
    "gebrauchte Gegenstände). Angebot freibleibend – Zwischenverkauf vorbehalten. Reservierung wird nach "
    "Rücksendung dieser Liste schriftlich bestätigt. Abholung nach Terminvereinbarung; Demontage und "
    "Transport durch den Käufer. Elektrogeräte werden ohne Prüfnachweis übergeben.")
c.font = Font(name=FONT, size=9, color="808080")
c.alignment = Alignment(vertical="top", wrap_text=True)

ws.freeze_panes = f"A{Z0}"
ws.page_setup.orientation = "landscape"
ws.page_setup.fitToWidth = 1
ws.sheet_properties.pageSetUpPr.fitToPage = True

pfad = os.path.join(BASIS, "ausgabe", "02_Angebot_Klinik_BEISPIEL.xlsx")
wb.save(pfad)
print("geschrieben:", pfad, "-", len(artikel), "Positionen")
