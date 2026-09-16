"""Erzeugt 02_Angebot_Klinik.xlsx – Auswahlliste im kikripp-Design."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import (lade_artikel, foto, AUSGABE, ASSETS, USt_SATZ, PAKETRABATT, FIRMA, STRASSE,
                 PLZ_ORT, ANSPRECH, TELEFON, EMAIL, EMPF_FIRMA, EMPF_PERSON, ANGEBOT_NR,
                 DATUM, GUELTIG, ROT, SCHWARZ, PAPIER, GRAU, LINIE, FELD_KLINIK, FELD_INTERN,
                 ZEILE, FONT, ABSENDER, KATALOG_URL, KATALOG_PW)

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.drawing.image import Image as XLImage
from openpyxl.utils import get_column_letter
from PIL import Image as PILImage

EUR = '#,##0.00 "€"'
d_linie = Side(style="thin", color=LINIE)
RAHMEN = Border(left=d_linie, right=d_linie, top=d_linie, bottom=d_linie)
ROT_KANTE = Border(left=Side(style="thick", color=ROT), right=d_linie, top=d_linie, bottom=d_linie)
TMP = "/tmp/angebot_thumbs"
os.makedirs(TMP, exist_ok=True)

# Reine Übersichtsliste: reserviert wird ausschließlich über den Webkatalog,
# damit derselbe Artikel nicht zweimal vergeben werden kann.
SPALTEN = [("Pos", 5), ("ArtNr", 9), ("Foto", 20), ("Artikel", 46), ("Maße", 18), ("Raum", 18),
           ("Zustand", 12), ("Verfügbar", 10), ("Einheit", 9), ("Einzelpreis netto", 15),
           ("Preis", 7), ("Lieferung", 15), ("Positionswert netto", 16)]
IDX = {s[0]: i + 1 for i, s in enumerate(SPALTEN)}
def L(n): return get_column_letter(IDX[n])
KLINIK_FELD = set()
INTERN_FELD = {"Maße"}
N = len(SPALTEN)

artikel = lade_artikel()
wb = Workbook(); ws = wb.active; ws.title = "Angebot"
for name, breite in SPALTEN:
    ws.column_dimensions[L(name)].width = breite

# ---- Kopfbalken schwarz mit Logo --------------------------------------------
ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=2)
ws.merge_cells(start_row=1, start_column=3, end_row=1, end_column=N)
for col in range(1, N + 1):
    ws.cell(row=1, column=col).fill = PatternFill("solid", fgColor=SCHWARZ)
c = ws.cell(row=1, column=3, value="Angebot aus der Betriebsauflösung")
c.font = Font(name=FONT, size=16, bold=True, color="FFFFFF")
c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
ws.row_dimensions[1].height = 42
logo = os.path.join(ASSETS, "kopflogo.png")
if os.path.exists(logo):
    with PILImage.open(logo) as im:
        h = 48; im = im.resize((int(im.width * h / im.height), h))
        im.save("/tmp/_kopflogo_xl.png")
    ws.add_image(XLImage("/tmp/_kopflogo_xl.png"), "A1")

# ---- Kopfdaten --------------------------------------------------------------
kopf = [("Empfänger", f"{EMPF_FIRMA} · {EMPF_PERSON}", "Angebot-Nr.", ANGEBOT_NR),
        ("Ansprechpartnerin", f"{ANSPRECH} · {TELEFON} · {EMAIL}", "Datum", DATUM),
        ("Alle Preise", f"netto zzgl. {int(USt_SATZ*100)} % USt", "Gültig bis", GUELTIG)]
for i, (a, b, cc, dd) in enumerate(kopf, start=2):
    ca = ws.cell(row=i, column=1, value=a)
    ca.font = Font(name=FONT, size=10, bold=True, color=GRAU)
    ws.merge_cells(start_row=i, start_column=3, end_row=i, end_column=9)
    ws.cell(row=i, column=3, value=b).font = Font(name=FONT, size=10, color=SCHWARZ)
    ws.cell(row=i, column=10, value=cc).font = Font(name=FONT, size=10, bold=True, color=GRAU)
    ws.merge_cells(start_row=i, start_column=12, end_row=i, end_column=N)
    ws.cell(row=i, column=12, value=dd).font = Font(name=FONT, size=10, bold=True, color=SCHWARZ)
    ws.row_dimensions[i].height = 17

# ---- Hinweisbox -------------------------------------------------------------
ws.merge_cells(start_row=5, start_column=1, end_row=5, end_column=N)
c = ws.cell(row=5, column=1, value=
    "So geht's:  Diese Liste ist Ihre Übersicht zum Blättern und Weitergeben. Reserviert wird über unseren "
    f"Onlinekatalog unter {KATALOG_URL}"
    + (f" (Passwort: {KATALOG_PW})" if KATALOG_PW else " (Passwort haben Sie von uns per E-Mail erhalten)")
    + ". Dort sehen Sie die tagesaktuelle Verfügbarkeit und merken Artikel mit einem Klick für sich vor – "
    "so ist ausgeschlossen, dass ein Stück doppelt vergeben wird. Möchten Sie den gesamten Bestand übernehmen, "
    "finden Sie am Ende der Liste ein Paketangebot; melden Sie sich dafür bitte direkt bei uns. "
    "Rot markierte Artikelnummern sind Marken- und Designstücke. Abholung nach Terminvereinbarung, "
    "Zahlung per Rechnung.")
c.font = Font(name=FONT, size=10, color=SCHWARZ)
c.fill = PatternFill("solid", fgColor=PAPIER)
c.alignment = Alignment(vertical="center", wrap_text=True, indent=1)
c.border = Border(left=Side(style="thick", color=ROT))
ws.row_dimensions[5].height = 34

# ---- Tabellenkopf -----------------------------------------------------------
KOPF = 7
for name, _b in SPALTEN:
    c = ws.cell(row=KOPF, column=IDX[name], value=name)
    c.fill = PatternFill("solid", fgColor=(ROT if name in KLINIK_FELD else SCHWARZ))
    c.font = Font(name=FONT, size=10, bold=True, color="FFFFFF")
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border = RAHMEN
ws.row_dimensions[KOPF].height = 32

# ---- Positionen -------------------------------------------------------------
Z0 = KOPF + 1
for i, a in enumerate(artikel):
    r = Z0 + i
    ist_a = a["Wertklasse"] == "A"
    wechsel = ZEILE if i % 2 else "FFFFFF"
    werte = {
        "Pos": i + 1, "ArtNr": a["ArtNr"], "Foto": None,
        "Artikel": f'{a["Bezeichnung"]}\n{a["Beschreibung"]}',
        "Maße": a.get("Maße") or None, "Raum": a["Raum"], "Zustand": a["Zustand"],
        "Verfügbar": a["Menge"], "Einheit": a["Einheit"], "Einzelpreis netto": a["Preis_netto"],
        "Preis": a["Preisbasis"], "Lieferung": a["Versand"],
        "Positionswert netto": f'={L("Verfügbar")}{r}*{L("Einzelpreis netto")}{r}',
    }
    for name, _b in SPALTEN:
        c = ws.cell(row=r, column=IDX[name], value=werte[name])
        c.font = Font(name=FONT, size=10, color=SCHWARZ)
        c.border = RAHMEN
        c.fill = PatternFill("solid", fgColor=wechsel)
        c.alignment = Alignment(vertical="center",
                                wrap_text=name in ("Artikel", "Lieferung", "Raum", "Maße"),
                                horizontal="center" if name in ("Pos", "ArtNr", "Verfügbar", "Einheit",
                                "Preis", "Zustand") else "left")
        if name in ("Einzelpreis netto", "Positionswert netto"):
            c.number_format = EUR
        if name == "Einzelpreis netto":
            c.font = Font(name=FONT, size=10, bold=True, color=SCHWARZ)
        if name in KLINIK_FELD:
            c.fill = PatternFill("solid", fgColor=FELD_KLINIK)
        if name in INTERN_FELD:
            c.fill = PatternFill("solid", fgColor=FELD_INTERN)
        if name == "Pos":
            c.font = Font(name=FONT, size=9, color=GRAU)
        if name == "ArtNr" and ist_a:
            c.fill = PatternFill("solid", fgColor=ROT)
            c.font = Font(name=FONT, size=10, bold=True, color="FFFFFF")
        if name == "Positionswert netto":
            c.border = ROT_KANTE
    ws.row_dimensions[r].height = 78
    p = foto(a["Foto"])
    if p:
        thumb = os.path.join(TMP, f'{a["ArtNr"]}.png')
        with PILImage.open(p) as im:
            im.thumbnail((132, 99)); im.save(thumb)
        ws.add_image(XLImage(thumb), f'{L("Foto")}{r}')

Z1 = Z0 + len(artikel) - 1
SN, EP, VF = L("Positionswert netto"), L("Einzelpreis netto"), L("Verfügbar")

def bandzeile(r, text, farbe):
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=N)
    for col in range(1, N + 1):
        ws.cell(row=r, column=col).fill = PatternFill("solid", fgColor=farbe)
    c = ws.cell(row=r, column=1, value=text)
    c.font = Font(name=FONT, size=11, bold=True, color="FFFFFF")
    c.alignment = Alignment(vertical="center", indent=1)
    ws.row_dimensions[r].height = 24

def summenzeile(r, label, formel, fett=False, farbe=None, gross=False):
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=IDX["Lieferung"])
    c = ws.cell(row=r, column=1, value=label)
    c.font = Font(name=FONT, size=12 if gross else 11, bold=True, color=SCHWARZ)
    c.alignment = Alignment(horizontal="right", vertical="center")
    c2 = ws.cell(row=r, column=IDX["Positionswert netto"], value=formel)
    c2.font = Font(name=FONT, size=12 if gross else 11, bold=fett,
                   color=("FFFFFF" if farbe == ROT else SCHWARZ))
    c2.number_format = EUR
    c2.border = RAHMEN
    if farbe:
        c.fill = PatternFill("solid", fgColor=PAPIER)
        c2.fill = PatternFill("solid", fgColor=farbe)
    ws.row_dimensions[r].height = 26 if gross else 22

rA = Z1 + 2
bandzeile(rA, "A · EINZELVERKAUF  (Reservierung über den Onlinekatalog)", SCHWARZ)
summenzeile(rA + 1, "Gesamtwert aller Positionen netto", f"=SUM({SN}{Z0}:{SN}{Z1})")
summenzeile(rA + 2, f"zzgl. {int(USt_SATZ*100)} % Umsatzsteuer", f"={SN}{rA+1}*{USt_SATZ}")
summenzeile(rA + 3, "Gesamtwert brutto", f"={SN}{rA+1}+{SN}{rA+2}", fett=True, farbe=ROT, gross=True)
ws.merge_cells(start_row=rA + 4, start_column=1, end_row=rA + 4, end_column=N)
c = ws.cell(row=rA + 4, column=1, value="Einzelne Artikel reservieren Sie bitte im Onlinekatalog; "
            "der Wert oben ist die Summe aller hier gelisteten Positionen.")
c.font = Font(name=FONT, size=9, italic=True, color=GRAU)
c.alignment = Alignment(vertical="center", indent=1)

# Abschnitt B baut auf dem Gesamtwert aus A auf – die Zahl steht nur einmal in der Datei.
rB = rA + 6
bandzeile(rB, "B · PAKETANGEBOT  (Übernahme des gesamten Bestands)", ROT)
summenzeile(rB + 1, f"Gesamtwert netto abzüglich Paketnachlass {int(PAKETRABATT*100)} %",
            f"=-{SN}{rA+1}*{PAKETRABATT}")
summenzeile(rB + 2, "Paketpreis netto", f"={SN}{rA+1}+{SN}{rB+1}", fett=True, farbe=PAPIER)
summenzeile(rB + 3, f"zzgl. {int(USt_SATZ*100)} % Umsatzsteuer", f"={SN}{rB+2}*{USt_SATZ}")
summenzeile(rB + 4, "Paketpreis brutto", f"={SN}{rB+2}+{SN}{rB+3}", fett=True, farbe=ROT, gross=True)
ws.merge_cells(start_row=rB + 5, start_column=1, end_row=rB + 5, end_column=N)
c = ws.cell(row=rB + 5, column=1, value="Das Paketangebot gilt für die Übernahme sämtlicher oben "
            "gelisteter Positionen in einem Zug, inklusive Abholung innerhalb von zwei Wochen nach Zuschlag. "
            "Sprechen Sie uns dafür bitte direkt an – eine Reservierung im Onlinekatalog ist dann nicht nötig.")
c.font = Font(name=FONT, size=9, italic=True, color=GRAU)
c.alignment = Alignment(vertical="center", indent=1)

rF = rB + 7
ws.merge_cells(start_row=rF, start_column=1, end_row=rF + 3, end_column=N)
c = ws.cell(row=rF, column=1, value=
    "Verkaufsbedingungen: Der Verkauf erfolgt aus einer Betriebsauflösung unter Ausschluss jeglicher "
    "Gewährleistung; es handelt sich durchweg um gebrauchte Gegenstände, die in dem Zustand verkauft werden, "
    "in dem sie sich befinden. Angebot freibleibend, Zwischenverkauf vorbehalten. Eine Reservierung wird erst "
    "mit unserer Bestätigung verbindlich; Reservierungen nehmen wir ausschließlich über den Onlinekatalog "
    "entgegen. Abholung nach Terminvereinbarung; Demontage, Verladung "
    "und Transport erfolgen durch den Käufer auf eigene Kosten und Gefahr. Elektrogeräte werden ohne "
    "Prüfnachweis nach DGUV V3 übergeben. Die Rechnung wird nach Abholung gestellt, zahlbar innerhalb von "
    "14 Tagen ohne Abzug. Das Eigentum geht erst mit vollständiger Bezahlung über.\n\n" + ABSENDER)
c.font = Font(name=FONT, size=9, color=GRAU)
c.alignment = Alignment(vertical="top", wrap_text=True)

ws.freeze_panes = f"A{Z0}"
ws.auto_filter.ref = f"A{KOPF}:{get_column_letter(N)}{Z1}"
ws.page_setup.orientation = "landscape"
ws.sheet_properties.pageSetUpPr.fitToPage = True
ws.page_setup.fitToWidth = 1
ws.sheet_view.showGridLines = False

pfad = os.path.join(AUSGABE, "02_Angebot_Klinik.xlsx")
wb.save(pfad)
print("geschrieben:", pfad, "-", len(artikel), "Positionen,", os.path.getsize(pfad)//1024, "KB")
