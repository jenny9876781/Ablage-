"""Erzeugt 02_Angebot_Klinik.xlsx – Auswahlliste mit Fotos, Einzelpositionen und Paketangebot."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import (lade_artikel, foto, AUSGABE, USt_SATZ, PAKETRABATT, FIRMA, STRASSE, ORT,
                 ANSPRECHPARTNER, TELEFON, EMAIL, EMPFAENGER, ANGEBOT_NR, DATUM, GUELTIG)

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.drawing.image import Image as XLImage
from openpyxl.utils import get_column_letter
from PIL import Image as PILImage

FONT = "Arial"
DUNKEL, MITTEL, HELL, GELB, ORANGE = "1F3864", "2E5A9C", "D9E2F3", "FFF2CC", "F8CBAD"
EUR = '#,##0.00 "€"'
duenn = Side(style="thin", color="BFBFBF")
RAHMEN = Border(left=duenn, right=duenn, top=duenn, bottom=duenn)
TMP = "/tmp/angebot_thumbs"
os.makedirs(TMP, exist_ok=True)

SPALTEN = [("Pos", 5), ("ArtNr", 9), ("Foto", 20), ("Artikel", 46), ("Maße", 18), ("Raum", 18),
           ("Zustand", 12), ("Verfügbar", 10), ("Einheit", 9), ("Einzelpreis netto", 15),
           ("Preis", 7), ("Lieferung", 15), ("Ihre Wunschmenge", 13),
           ("Ihre Bemerkung / Frage", 26), ("Summe netto", 14)]
IDX = {s[0]: i + 1 for i, s in enumerate(SPALTEN)}
def L(n): return get_column_letter(IDX[n])
PFLEGE_KLINIK = {"Ihre Wunschmenge", "Ihre Bemerkung / Frage"}
PFLEGE_INTERN = {"Maße"}

artikel = lade_artikel()
wb = Workbook(); ws = wb.active; ws.title = "Angebot"
for name, breite in SPALTEN:
    ws.column_dimensions[L(name)].width = breite

# ---- Kopf -------------------------------------------------------------------
ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(SPALTEN))
c = ws.cell(row=1, column=1, value=f"{FIRMA} – Angebot aus Betriebsauflösung")
c.font = Font(name=FONT, size=16, bold=True, color="FFFFFF")
c.fill = PatternFill("solid", fgColor=DUNKEL)
c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
ws.row_dimensions[1].height = 30

kopf = [("Angebot-Nr.", ANGEBOT_NR, "Datum", DATUM),
        ("Empfänger", EMPFAENGER, "Angebot gültig bis", GUELTIG),
        ("Ansprechpartnerin", f"{ANSPRECHPARTNER} · {TELEFON} · {EMAIL}", "Alle Preise",
         f"netto zzgl. {int(USt_SATZ*100)} % USt")]
for i, (a, b, cc, d) in enumerate(kopf, start=2):
    ws.cell(row=i, column=1, value=a).font = Font(name=FONT, size=10, bold=True)
    ws.merge_cells(start_row=i, start_column=2, end_row=i, end_column=7)
    ws.cell(row=i, column=2, value=b).font = Font(name=FONT, size=10)
    ws.cell(row=i, column=9, value=cc).font = Font(name=FONT, size=10, bold=True)
    ws.merge_cells(start_row=i, start_column=11, end_row=i, end_column=len(SPALTEN))
    ws.cell(row=i, column=11, value=d).font = Font(name=FONT, size=10)

ws.merge_cells(start_row=5, start_column=1, end_row=5, end_column=len(SPALTEN))
c = ws.cell(row=5, column=1, value=
    "So geht's: Bitte tragen Sie in den gelben Spalten ein, welche Artikel Sie in welcher Menge übernehmen "
    "möchten, und schicken die Datei zurück. Die Summen rechnen sich automatisch. Wenn Sie den gesamten "
    "Bestand übernehmen möchten, finden Sie am Ende der Liste ein Paketangebot. Abholung nach "
    "Terminvereinbarung, Zahlung per Rechnung.")
c.font = Font(name=FONT, size=10, italic=True, color="7F6000")
c.fill = PatternFill("solid", fgColor=GELB)
c.alignment = Alignment(vertical="center", wrap_text=True, indent=1)
ws.row_dimensions[5].height = 32

# ---- Tabellenkopf -----------------------------------------------------------
KOPF = 7
for name, _b in SPALTEN:
    c = ws.cell(row=KOPF, column=IDX[name], value=name)
    if name in PFLEGE_KLINIK:
        c.font = Font(name=FONT, size=10, bold=True, color="7F6000")
        c.fill = PatternFill("solid", fgColor=GELB)
    else:
        c.font = Font(name=FONT, size=10, bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor=MITTEL)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border = RAHMEN
ws.row_dimensions[KOPF].height = 32

# ---- Positionen -------------------------------------------------------------
Z0 = KOPF + 1
for i, a in enumerate(artikel):
    r = Z0 + i
    werte = {
        "Pos": i + 1, "ArtNr": a["ArtNr"], "Foto": None,
        "Artikel": f'{a["Bezeichnung"]}\n{a["Beschreibung"]}',
        "Maße": a.get("Maße") or None, "Raum": a["Raum"], "Zustand": a["Zustand"],
        "Verfügbar": a["Menge"], "Einheit": a["Einheit"], "Einzelpreis netto": a["Preis_netto"],
        "Preis": a["Preisbasis"], "Lieferung": a["Versand"],
        "Ihre Wunschmenge": None, "Ihre Bemerkung / Frage": None,
        "Summe netto": f'=IF({L("Ihre Wunschmenge")}{r}="","",'
                       f'{L("Ihre Wunschmenge")}{r}*{L("Einzelpreis netto")}{r})',
    }
    for name, _b in SPALTEN:
        c = ws.cell(row=r, column=IDX[name], value=werte[name])
        c.font = Font(name=FONT, size=10)
        c.border = RAHMEN
        c.alignment = Alignment(vertical="center",
                                wrap_text=name in ("Artikel", "Lieferung", "Raum", "Maße"),
                                horizontal="center" if name in ("Pos", "ArtNr", "Verfügbar", "Einheit",
                                "Preis", "Zustand", "Ihre Wunschmenge") else "left")
        if name in ("Einzelpreis netto", "Summe netto"):
            c.number_format = EUR
        if name in PFLEGE_KLINIK:
            c.fill = PatternFill("solid", fgColor=GELB)
        if name in PFLEGE_INTERN:
            c.fill = PatternFill("solid", fgColor=HELL)
        if a["Wertklasse"] == "A" and name == "ArtNr":
            c.fill = PatternFill("solid", fgColor=ORANGE)
    ws.row_dimensions[r].height = 78
    p = foto(a["Foto"])
    if p:
        thumb = os.path.join(TMP, f'{a["ArtNr"]}.png')
        with PILImage.open(p) as im:
            im.thumbnail((132, 99))
            im.save(thumb)
        ws.add_image(XLImage(thumb), f'{L("Foto")}{r}')

Z1 = Z0 + len(artikel) - 1
SN = L("Summe netto")
EP = L("Einzelpreis netto")
VF = L("Verfügbar")

def summenzeile(r, label, formel, fett=False, farbe=None, gross=False):
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=IDX["Ihre Bemerkung / Frage"])
    c = ws.cell(row=r, column=1, value=label)
    c.font = Font(name=FONT, size=12 if gross else 11, bold=True, color=DUNKEL)
    c.alignment = Alignment(horizontal="right", vertical="center")
    c2 = ws.cell(row=r, column=IDX["Summe netto"], value=formel)
    c2.font = Font(name=FONT, size=12 if gross else 11, bold=fett, color=DUNKEL)
    c2.number_format = EUR
    c2.border = RAHMEN
    if farbe:
        c.fill = PatternFill("solid", fgColor=farbe)
        c2.fill = PatternFill("solid", fgColor=farbe)
    ws.row_dimensions[r].height = 22 if not gross else 26

# ---- Block A: Ihre Auswahl --------------------------------------------------
rA = Z1 + 2
ws.merge_cells(start_row=rA, start_column=1, end_row=rA, end_column=len(SPALTEN))
c = ws.cell(row=rA, column=1, value="A · IHRE AUSWAHL (Einzelpositionen)")
c.font = Font(name=FONT, size=11, bold=True, color="FFFFFF")
c.fill = PatternFill("solid", fgColor=MITTEL)
c.alignment = Alignment(vertical="center", indent=1)
summenzeile(rA + 1, "Zwischensumme netto", f"=SUM({SN}{Z0}:{SN}{Z1})")
summenzeile(rA + 2, f"zzgl. {int(USt_SATZ*100)} % Umsatzsteuer", f"={SN}{rA+1}*{USt_SATZ}")
summenzeile(rA + 3, "Gesamtsumme brutto", f"={SN}{rA+1}+{SN}{rA+2}", fett=True, farbe=HELL, gross=True)

# ---- Block B: Paketangebot --------------------------------------------------
rB = rA + 5
ws.merge_cells(start_row=rB, start_column=1, end_row=rB, end_column=len(SPALTEN))
c = ws.cell(row=rB, column=1, value="B · PAKETANGEBOT (Übernahme des gesamten Bestands)")
c.font = Font(name=FONT, size=11, bold=True, color="FFFFFF")
c.fill = PatternFill("solid", fgColor="833C00")
c.alignment = Alignment(vertical="center", indent=1)
summenzeile(rB + 1, "Gesamtwert aller Positionen zu Einzelpreisen (netto)",
            f"=SUMPRODUCT({VF}{Z0}:{VF}{Z1},{EP}{Z0}:{EP}{Z1})")
summenzeile(rB + 2, f"abzüglich Paketnachlass {int(PAKETRABATT*100)} %",
            f"=-{SN}{rB+1}*{PAKETRABATT}")
summenzeile(rB + 3, "Paketpreis netto", f"={SN}{rB+1}+{SN}{rB+2}", fett=True, farbe=GELB)
summenzeile(rB + 4, f"zzgl. {int(USt_SATZ*100)} % Umsatzsteuer", f"={SN}{rB+3}*{USt_SATZ}")
summenzeile(rB + 5, "Paketpreis brutto", f"={SN}{rB+3}+{SN}{rB+4}", fett=True, farbe=HELL, gross=True)
ws.merge_cells(start_row=rB + 6, start_column=1, end_row=rB + 6, end_column=len(SPALTEN))
c = ws.cell(row=rB + 6, column=1, value=
    "Das Paketangebot gilt für die Übernahme sämtlicher oben gelisteter Positionen in einem Zug, "
    "inklusive Abholung innerhalb von zwei Wochen nach Zuschlag.")
c.font = Font(name=FONT, size=9, italic=True, color="808080")
c.alignment = Alignment(vertical="center", indent=1)

# ---- Fuß --------------------------------------------------------------------
rF = rB + 8
ws.merge_cells(start_row=rF, start_column=1, end_row=rF + 3, end_column=len(SPALTEN))
c = ws.cell(row=rF, column=1, value=
    "Verkaufsbedingungen: Der Verkauf erfolgt aus einer Betriebsauflösung unter Ausschluss jeglicher "
    "Gewährleistung; es handelt sich durchweg um gebrauchte Gegenstände, die in dem Zustand verkauft werden, "
    "in dem sie sich befinden. Angebot freibleibend, Zwischenverkauf vorbehalten. Eine Reservierung wird erst "
    "mit unserer schriftlichen Bestätigung verbindlich. Abholung nach Terminvereinbarung; Demontage, Verladung "
    "und Transport erfolgen durch den Käufer auf eigene Kosten und Gefahr. Elektrogeräte werden ohne "
    "Prüfnachweis nach DGUV V3 übergeben. Die Rechnung wird nach Abholung gestellt, zahlbar innerhalb von "
    "14 Tagen ohne Abzug. Das Eigentum geht erst mit vollständiger Bezahlung über.\n\n"
    f"{FIRMA} · {STRASSE} · {ORT} · {ANSPRECHPARTNER} · {TELEFON} · {EMAIL}")
c.font = Font(name=FONT, size=9, color="808080")
c.alignment = Alignment(vertical="top", wrap_text=True)

ws.freeze_panes = f"A{Z0}"
ws.auto_filter.ref = f"A{KOPF}:{get_column_letter(len(SPALTEN))}{Z1}"
ws.page_setup.orientation = "landscape"
ws.sheet_properties.pageSetUpPr.fitToPage = True
ws.page_setup.fitToWidth = 1

pfad = os.path.join(AUSGABE, "02_Angebot_Klinik.xlsx")
wb.save(pfad)
print("geschrieben:", pfad, "-", len(artikel), "Positionen,", os.path.getsize(pfad)//1024, "KB")
