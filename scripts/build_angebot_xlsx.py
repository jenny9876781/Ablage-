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

# Die Klinik trägt ihr Interesse in den grau hinterlegten Spalten rechts ein.
# Das ist eine Interessenbekundung, keine Reservierung — verbindlich vorgemerkt
# wird ausschließlich im Webkatalog, sonst ist dasselbe Stück zweimal vergeben.
SPALTEN = [("Pos", 5), ("ArtNr", 10), ("Foto", 20), ("Artikel", 42), ("Maße", 14), ("Raum", 16),
           ("Zustand", 12), ("Verfügbar", 10), ("Einheit", 9),
           ("Einzelpreis netto", 15), ("Einzelpreis brutto", 16),
           ("Preis", 7), ("Lieferung", 15),
           ("Interesse", 11), ("Stückzahl", 11), ("Ihre Bemerkung", 24), ("Wert netto", 14)]
IDX = {s[0]: i + 1 for i, s in enumerate(SPALTEN)}
def L(n): return get_column_letter(IDX[n])
KLINIK_FELD = {"Interesse", "Stückzahl", "Ihre Bemerkung"}
INTERN_FELD = {"Maße"}
# Markierung aus der Datenbasis (Spalte Klinik_Markierung)
MARKE_FARBE = "D6E3F0"   # heller Blauton, wie von der Nutzerin gesetzt
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
        ("Alle Preise", f"netto und brutto (inkl. {int(USt_SATZ*100)} % USt)", "Gültig bis", GUELTIG)]
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
    "So geht's:  Tragen Sie in den drei grau hinterlegten Spalten rechts ein, woran Sie Interesse "
    "haben. „Interesse = ja\" genügt; lassen Sie die Stückzahl leer, zählt die volle verfügbare "
    "Menge. Der Wert Ihrer Auswahl rechnet sich unten automatisch. Rot markierte Artikelnummern "
    "sind Markenware oder Designstücke. "
    "Ihre Eintragungen sind eine Interessenbekundung und keine Reservierung — wir stimmen die "
    "Mengen anschließend gemeinsam ab. Abholung nach Terminvereinbarung, Zahlung per Rechnung. "
    f"Möchten Sie den gesamten Bestand übernehmen, finden Sie am Ende ein Paketangebot mit "
    f"{int(PAKETRABATT*100)} % Nachlass.")
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
        "Einzelpreis brutto": f'={L("Einzelpreis netto")}{r}*{1 + USt_SATZ}',
        "Preis": a["Preisbasis"], "Lieferung": a["Versand"],
        "Interesse": None, "Stückzahl": None, "Ihre Bemerkung": None,
        # Leer, solange kein Interesse steht. „ja" ohne Stückzahl = volle Menge.
        "Wert netto": f'=IF({L("Interesse")}{r}<>"ja","",'
                      f'IF({L("Stückzahl")}{r}="",{L("Verfügbar")}{r},{L("Stückzahl")}{r})'
                      f'*{L("Einzelpreis netto")}{r})',
    }
    for name, _b in SPALTEN:
        c = ws.cell(row=r, column=IDX[name], value=werte[name])
        c.font = Font(name=FONT, size=10, color=SCHWARZ)
        c.border = RAHMEN
        c.fill = PatternFill("solid", fgColor=wechsel)
        c.alignment = Alignment(vertical="center",
                                wrap_text=name in ("Artikel", "Lieferung", "Raum", "Maße"),
                                horizontal="center" if name in ("Pos", "ArtNr", "Verfügbar", "Einheit",
                                "Preis", "Zustand", "Interesse", "Stückzahl") else "left")
        if name in ("Einzelpreis netto", "Einzelpreis brutto", "Wert netto"):
            c.number_format = EUR
        if name == "Einzelpreis netto":
            c.font = Font(name=FONT, size=10, bold=True, color=SCHWARZ)
        if name == "Einzelpreis brutto":
            c.font = Font(name=FONT, size=10, color=GRAU)
        if name in KLINIK_FELD:
            c.fill = PatternFill("solid", fgColor=FELD_KLINIK)
        if name in INTERN_FELD:
            c.fill = PatternFill("solid", fgColor=FELD_INTERN)
        if name == "Pos":
            c.font = Font(name=FONT, size=9, color=GRAU)
        if name == "ArtNr" and ist_a:
            c.fill = PatternFill("solid", fgColor=ROT)
            c.font = Font(name=FONT, size=10, bold=True, color="FFFFFF")
        if name == "Interesse":
            c.border = ROT_KANTE
        # Deine Markierung aus der Spalte Klinik_Markierung
        if a.get("Klinik_Markierung", "").strip().lower() == "ja" and name not in KLINIK_FELD:
            c.fill = PatternFill("solid", fgColor=MARKE_FARBE)
    ws.row_dimensions[r].height = 78
    p = foto(a["Foto"])
    if p:
        thumb = os.path.join(TMP, f'{a["ArtNr"]}.png')
        with PILImage.open(p) as im:
            im.thumbnail((132, 99)); im.save(thumb)
        ws.add_image(XLImage(thumb), f'{L("Foto")}{r}')

Z1 = Z0 + len(artikel) - 1
SN, EP, VF = L("Wert netto"), L("Einzelpreis netto"), L("Verfügbar")
IN = L("Interesse")

def bandzeile(r, text, farbe):
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=N)
    for col in range(1, N + 1):
        ws.cell(row=r, column=col).fill = PatternFill("solid", fgColor=farbe)
    c = ws.cell(row=r, column=1, value=text)
    c.font = Font(name=FONT, size=11, bold=True, color="FFFFFF")
    c.alignment = Alignment(vertical="center", indent=1)
    ws.row_dimensions[r].height = 24

def summenzeile(r, label, formel, fett=False, farbe=None, gross=False):
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=IDX["Ihre Bemerkung"])
    c = ws.cell(row=r, column=1, value=label)
    c.font = Font(name=FONT, size=12 if gross else 11, bold=True, color=SCHWARZ)
    c.alignment = Alignment(horizontal="right", vertical="center")
    c2 = ws.cell(row=r, column=IDX["Wert netto"], value=formel)
    c2.font = Font(name=FONT, size=12 if gross else 11, bold=fett,
                   color=("FFFFFF" if farbe == ROT else SCHWARZ))
    c2.number_format = EUR
    c2.border = RAHMEN
    if farbe:
        c.fill = PatternFill("solid", fgColor=PAPIER)
        c2.fill = PatternFill("solid", fgColor=farbe)
    ws.row_dimensions[r].height = 26 if gross else 22

rA = Z1 + 2
bandzeile(rA, "A · IHRE AUSWAHL", SCHWARZ)
summenzeile(rA + 1, "Wert Ihrer Auswahl netto", f"=SUM({SN}{Z0}:{SN}{Z1})")
summenzeile(rA + 2, f"zzgl. {int(USt_SATZ*100)} % Umsatzsteuer", f"={SN}{rA+1}*{USt_SATZ}")
summenzeile(rA + 3, "Wert Ihrer Auswahl brutto", f"={SN}{rA+1}+{SN}{rA+2}",
            fett=True, farbe=ROT, gross=True)
summenzeile(rA + 4, "gewählte Positionen", f'=COUNTIF({IN}{Z0}:{IN}{Z1},"ja")')
ws.cell(row=rA + 4, column=IDX["Wert netto"]).number_format = "0"
ws.merge_cells(start_row=rA + 5, start_column=1, end_row=rA + 5, end_column=N)
c = ws.cell(row=rA + 5, column=1, value="Solange Sie nichts eintragen, bleiben diese Summen leer. "
            "Ihre Eintragungen sind eine Interessenbekundung und keine Reservierung.")
c.font = Font(name=FONT, size=9, italic=True, color=GRAU)
c.alignment = Alignment(vertical="center", indent=1)

# Gesamtwert des Bestands – als Bezugsgröße für das Paketangebot
rG = rA + 7
bandzeile(rG, "B · GESAMTBESTAND", "595959")
summenzeile(rG + 1, "Gesamtwert aller gelisteten Positionen netto",
            f"=SUMPRODUCT({VF}{Z0}:{VF}{Z1},{EP}{Z0}:{EP}{Z1})")
summenzeile(rG + 2, f"zzgl. {int(USt_SATZ*100)} % Umsatzsteuer", f"={SN}{rG+1}*{USt_SATZ}")
summenzeile(rG + 3, "Gesamtwert brutto", f"={SN}{rG+1}+{SN}{rG+2}", fett=True, farbe=PAPIER)

# Abschnitt C baut auf dem Gesamtbestand aus B auf – die Zahl steht nur einmal in der Datei.
rB = rG + 5
bandzeile(rB, "C · PAKETANGEBOT  (Übernahme des gesamten Bestands)", ROT)
summenzeile(rB + 1, f"Gesamtwert netto abzüglich Paketnachlass {int(PAKETRABATT*100)} %",
            f"=-{SN}{rG+1}*{PAKETRABATT}")
summenzeile(rB + 2, "Paketpreis netto", f"={SN}{rG+1}+{SN}{rB+1}", fett=True, farbe=PAPIER)
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
    "in dem sie sich befinden. Angebot freibleibend, Zwischenverkauf vorbehalten. Ihre Eintragungen in "
    "dieser Liste sind eine Interessenbekundung; verbindlich wird die Zuteilung erst mit unserer "
    "schriftlichen Bestätigung. Abholung nach Terminvereinbarung; Demontage, Verladung "
    "und Transport erfolgen durch den Käufer auf eigene Kosten und Gefahr. Elektrogeräte werden ohne "
    "Prüfnachweis nach DGUV V3 übergeben. Die Rechnung wird nach Abholung gestellt, zahlbar innerhalb von "
    "14 Tagen ohne Abzug. Das Eigentum geht erst mit vollständiger Bezahlung über.\n\n" + ABSENDER)
c.font = Font(name=FONT, size=9, color=GRAU)
c.alignment = Alignment(vertical="top", wrap_text=True)

# ---- Eingabehilfen für die Klinik -------------------------------------------
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import FormulaRule

dv_ja = DataValidation(type="list", formula1='"ja,nein"', allow_blank=True, showDropDown=False,
                       errorTitle="Interesse", error='Bitte „ja" oder „nein" wählen.',
                       showErrorMessage=True)
ws.add_data_validation(dv_ja)
dv_ja.add(f'{IN}{Z0}:{IN}{Z1}')

dv_menge = DataValidation(type="whole", operator="greaterThan", formula1="0", allow_blank=True,
                          errorTitle="Stückzahl",
                          error="Bitte eine ganze Zahl größer 0 eintragen oder das Feld leer "
                                "lassen – dann gilt die volle verfügbare Menge.",
                          showErrorMessage=True)
ws.add_data_validation(dv_menge)
dv_menge.add(f'{L("Stückzahl")}{Z0}:{L("Stückzahl")}{Z1}')

# Zeilen mit „ja" heben sich ab, damit die Auswahl auf einen Blick sichtbar ist.
bereich = f"A{Z0}:{get_column_letter(N)}{Z1}"
ws.conditional_formatting.add(bereich, FormulaRule(
    formula=[f'${IN}{Z0}="ja"'],
    fill=PatternFill("solid", bgColor="E8F0E4"), stopIfTrue=False))

ws.freeze_panes = f"A{Z0}"
ws.auto_filter.ref = f"A{KOPF}:{get_column_letter(N)}{Z1}"
ws.page_setup.orientation = "landscape"
ws.sheet_properties.pageSetUpPr.fitToPage = True
ws.page_setup.fitToWidth = 1
ws.sheet_view.showGridLines = False

pfad = os.path.join(AUSGABE, "02_Angebot_Klinik.xlsx")
wb.save(pfad)
print("geschrieben:", pfad, "-", len(artikel), "Positionen,", os.path.getsize(pfad)//1024, "KB")
