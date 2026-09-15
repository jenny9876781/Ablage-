"""Erzeugt 01_Artikelstamm_BEISPIEL.xlsx  (Artikelstamm + Verkaufsuebersicht + Legende)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import lade_artikel, BASIS, USt_SATZ

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import CellIsRule

FONT = "Arial"
DUNKEL = "1F3864"; MITTEL = "2E5A9C"; HELL = "D9E2F3"; GELB = "FFF2CC"; GRAU = "F2F2F2"
EUR = '#,##0.00 "€"'

# (Ueberschrift, Breite, Gruppe, Typ)
SPALTEN = [
    ("ArtNr",                  10, "Stammdaten",    "text"),
    ("Bezeichnung",            34, "Stammdaten",    "text"),
    ("Beschreibung",           52, "Stammdaten",    "text"),
    ("Kategorie",              18, "Stammdaten",    "text"),
    ("Raum",                   18, "Stammdaten",    "text"),
    ("Menge",                   8, "Stammdaten",    "int"),
    ("Verkauft_Menge",         12, "Stammdaten",    "int"),
    ("Restmenge",              11, "Stammdaten",    "formel"),
    ("Einheit",                10, "Stammdaten",    "text"),
    ("Zustand",                14, "Stammdaten",    "text"),
    ("Anschaffungsjahr",       11, "Buchhaltung",   "text"),
    ("Anlagennr",              12, "Buchhaltung",   "text"),
    ("Anschaffungswert_netto", 17, "Buchhaltung",   "eur"),
    ("Preis_netto",            14, "Preis",         "eur"),
    ("Preisbasis",             11, "Preis",         "text"),
    ("Versand",                16, "Vermarktung",   "text"),
    ("Foto",                   14, "Vermarktung",   "text"),
    ("Status",                 12, "Vermarktung",   "text"),
    ("Kanal",                  14, "Vermarktung",   "text"),
    ("Reserviert_für",         22, "Vermarktung",   "text"),
    ("Verkaufspreis_netto",    17, "Verkauf",       "eur"),
    ("Umsatz_netto",           14, "Verkauf",       "formel"),
    ("Verkaufsdatum",          14, "Verkauf",       "text"),
    ("Käufer",                 24, "Verkauf",       "text"),
    ("Rechnungsnr",            14, "Kaufmännisch",  "text"),
    ("Zahlung",                11, "Kaufmännisch",  "text"),
    ("Zahlart",                13, "Kaufmännisch",  "text"),
    ("Abholtermin",            13, "Kaufmännisch",  "text"),
    ("Bemerkung",              36, "Kaufmännisch",  "text"),
]
GRUPPENFARBE = {"Stammdaten": "1F3864", "Buchhaltung": "7F6000", "Preis": "833C00",
                "Vermarktung": "375623", "Verkauf": "633A82", "Kaufmännisch": "0E5A6B"}
IDX = {s[0]: i + 1 for i, s in enumerate(SPALTEN)}
def L(name): return get_column_letter(IDX[name])

AUSWAHL = {
    "Einheit":    '"Stück,Karton,Set,Palette,Konvolut,lfd. Meter"',
    "Zustand":    '"neuwertig,gut,gebraucht,stark gebraucht,defekt"',
    "Preisbasis": '"Fix,VHB"',
    "Versand":    '"nur Abholung,Versand möglich,Spedition"',
    "Status":     '"verfügbar,reserviert,verkauft,gespendet,entsorgt"',
    "Kanal":      '"Klinik,Kleinanzeigen,eBay,Direkt,Händler,intern"',
    "Zahlung":    '"offen,bezahlt,teilbezahlt"',
    "Zahlart":    '"Überweisung,bar,PayPal"',
}

daten = lade_artikel()
Z0 = 3                      # erste Datenzeile
Z1 = Z0 + len(daten) - 1    # letzte Datenzeile

wb = Workbook()
ws = wb.active
ws.title = "Artikelstamm"

# --- Zeile 1: Gruppenbaender -------------------------------------------------
start = 1
for i in range(len(SPALTEN) + 1):
    gruppe = SPALTEN[i][2] if i < len(SPALTEN) else None
    if i == len(SPALTEN) or (i > 0 and gruppe != SPALTEN[i - 1][2]):
        g = SPALTEN[i - 1][2]
        ws.merge_cells(start_row=1, start_column=start, end_row=1, end_column=i)
        c = ws.cell(row=1, column=start, value=g.upper())
        c.font = Font(name=FONT, size=9, bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor=GRUPPENFARBE[g])
        c.alignment = Alignment(horizontal="center", vertical="center")
        start = i + 1

# --- Zeile 2: Spaltenkoepfe --------------------------------------------------
duenn = Side(style="thin", color="BFBFBF")
for i, (name, breite, _g, _t) in enumerate(SPALTEN, start=1):
    c = ws.cell(row=2, column=i, value=name)
    c.font = Font(name=FONT, size=10, bold=True, color="FFFFFF")
    c.fill = PatternFill("solid", fgColor=MITTEL)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border = Border(left=duenn, right=duenn, top=duenn, bottom=duenn)
    ws.column_dimensions[get_column_letter(i)].width = breite
ws.row_dimensions[1].height = 16
ws.row_dimensions[2].height = 30

# --- Daten -------------------------------------------------------------------
for r, art in enumerate(daten, start=Z0):
    for name, _b, _g, typ in SPALTEN:
        col = IDX[name]
        if name == "Restmenge":
            wert = f'={L("Menge")}{r}-IF({L("Verkauft_Menge")}{r}="",0,{L("Verkauft_Menge")}{r})'
        elif name == "Umsatz_netto":
            wert = (f'=IF({L("Verkauft_Menge")}{r}="","",'
                    f'{L("Verkauft_Menge")}{r}*{L("Verkaufspreis_netto")}{r})')
        elif name == "Foto":
            wert = art.get("Foto") or ""
        else:
            wert = art.get(name)
            if wert == "":
                wert = None
        c = ws.cell(row=r, column=col, value=wert)
        c.font = Font(name=FONT, size=10)
        c.alignment = Alignment(vertical="top", wrap_text=(name in ("Beschreibung", "Bemerkung")))
        c.border = Border(left=duenn, right=duenn, top=duenn, bottom=duenn)
        if typ == "eur" or name == "Umsatz_netto":
            c.number_format = EUR
        if typ in ("int",) or name == "Restmenge":
            c.number_format = "0"
        if name in ("Preis_netto", "Verkaufspreis_netto", "Verkauft_Menge", "Status",
                    "Kanal", "Reserviert_für", "Rechnungsnr", "Zahlung", "Abholtermin"):
            c.fill = PatternFill("solid", fgColor=GELB)   # Pflegefelder
    ws.row_dimensions[r].height = 30

# --- Komfort -----------------------------------------------------------------
ws.freeze_panes = "C3"
ws.auto_filter.ref = f"A2:{get_column_letter(len(SPALTEN))}{Z1}"
for name, formel in AUSWAHL.items():
    dv = DataValidation(type="list", formula1=formel, allow_blank=True, showDropDown=False)
    ws.add_data_validation(dv)
    dv.add(f"{L(name)}{Z0}:{L(name)}{Z0+500}")

s = f"{L('Status')}{Z0}:{L('Status')}{Z1}"
ws.conditional_formatting.add(s, CellIsRule(operator="equal", formula=['"verfügbar"'],
    fill=PatternFill("solid", bgColor="E2EFDA")))
ws.conditional_formatting.add(s, CellIsRule(operator="equal", formula=['"reserviert"'],
    fill=PatternFill("solid", bgColor="FFF2CC")))
ws.conditional_formatting.add(s, CellIsRule(operator="equal", formula=['"verkauft"'],
    fill=PatternFill("solid", bgColor="D9D9D9")))

# =============================================================================
# Blatt 2: Verkaufsuebersicht
# =============================================================================
vu = wb.create_sheet("Verkaufsübersicht")
A = lambda n: f"Artikelstamm!${L(n)}${Z0}:${L(n)}${Z1}"

def titel(row, text, size=14):
    c = vu.cell(row=row, column=1, value=text)
    c.font = Font(name=FONT, size=size, bold=True, color=DUNKEL)

def kpi(row, label, formel, fmt=None, fett=False):
    a = vu.cell(row=row, column=1, value=label)
    a.font = Font(name=FONT, size=10, bold=fett)
    b = vu.cell(row=row, column=2, value=formel)
    b.font = Font(name=FONT, size=10, bold=fett)
    b.alignment = Alignment(horizontal="right")
    if fmt:
        b.number_format = fmt
    if fett:
        b.fill = PatternFill("solid", fgColor=HELL)
    return row + 1

vu.column_dimensions["A"].width = 42
vu.column_dimensions["B"].width = 18
for col in "CDE":
    vu.column_dimensions[col].width = 18

titel(1, "Verkaufsübersicht – alle Werte rechnen automatisch aus dem Artikelstamm", 13)
vu["A2"] = "Es muss nichts von Hand gepflegt werden. Wer im Artikelstamm einen Verkauf einträgt, sieht ihn sofort hier."
vu["A2"].font = Font(name=FONT, size=9, italic=True, color="808080")

titel(4, "Bestand", 11)
r = 5
r = kpi(r, "Artikelpositionen gesamt", f'=COUNTA({A("ArtNr")})', "0")
r = kpi(r, "davon verfügbar", f'=COUNTIF({A("Status")},"verfügbar")', "0")
r = kpi(r, "davon reserviert", f'=COUNTIF({A("Status")},"reserviert")', "0")
r = kpi(r, "davon verkauft", f'=COUNTIF({A("Status")},"verkauft")', "0")
r = kpi(r, "Einheiten noch im Bestand", f'=SUM({A("Restmenge")})', "0")
r = kpi(r, "Restbestand zu Wunschpreisen (netto)",
        f'=SUMPRODUCT({A("Restmenge")},{A("Preis_netto")})', EUR, fett=True)

titel(12, "Erlöse", 11)
r = 13
r = kpi(r, "Verkaufte Einheiten", f'=SUM({A("Verkauft_Menge")})', "0")
r = kpi(r, "Umsatz netto", f'=SUMPRODUCT({A("Verkauft_Menge")},{A("Verkaufspreis_netto")})', EUR)
r = kpi(r, f"zzgl. Umsatzsteuer {int(USt_SATZ*100)} %", f"=B14*{USt_SATZ}", EUR)
r = kpi(r, "Umsatz brutto", "=B14+B15", EUR, fett=True)
r = kpi(r, "davon bereits bezahlt (netto)",
        f'=SUMPRODUCT(({A("Zahlung")}="bezahlt")*{A("Verkauft_Menge")}*{A("Verkaufspreis_netto")})', EUR)
r = kpi(r, "noch offen (netto)", "=B14-B17", EUR)

titel(20, "To-do", 11)
r = 21
r = kpi(r, "Rechnungen noch zu schreiben",
        f'=COUNTIFS({A("Status")},"verkauft",{A("Rechnungsnr")},"")', "0", fett=True)
r = kpi(r, "Rechnungen offen (unbezahlt)",
        f'=COUNTIFS({A("Status")},"verkauft",{A("Zahlung")},"offen")', "0", fett=True)
r = kpi(r, "Reservierungen ohne Abholtermin",
        f'=COUNTIFS({A("Status")},"reserviert",{A("Abholtermin")},"")', "0")
r = kpi(r, "Artikel ohne Preis", f'=COUNTIFS({A("Preis_netto")},"")', "0")
r = kpi(r, "Artikel ohne Foto", f'=COUNTIFS({A("Foto")},"")', "0")

# Auswertung je Kategorie
kategorien = sorted({a["Kategorie"] for a in daten})
start_k = 28
titel(start_k - 1, "Nach Kategorie", 11)
for j, h in enumerate(["Kategorie", "Positionen", "Umsatz netto", "Restwert netto"]):
    c = vu.cell(row=start_k, column=1 + j, value=h)
    c.font = Font(name=FONT, size=10, bold=True, color="FFFFFF")
    c.fill = PatternFill("solid", fgColor=MITTEL)
for i, k in enumerate(kategorien):
    row = start_k + 1 + i
    vu.cell(row=row, column=1, value=k).font = Font(name=FONT, size=10)
    vu.cell(row=row, column=2, value=f'=COUNTIF({A("Kategorie")},$A{row})').number_format = "0"
    c = vu.cell(row=row, column=3, value=f'=SUMPRODUCT(({A("Kategorie")}=$A{row})*'
                                        f'{A("Verkauft_Menge")}*{A("Verkaufspreis_netto")})')
    c.number_format = EUR
    c = vu.cell(row=row, column=4, value=f'=SUMPRODUCT(({A("Kategorie")}=$A{row})*'
                                        f'{A("Restmenge")}*{A("Preis_netto")})')
    c.number_format = EUR
    for col in range(1, 5):
        vu.cell(row=row, column=col).font = Font(name=FONT, size=10)
sum_k = start_k + 1 + len(kategorien)
vu.cell(row=sum_k, column=1, value="Summe").font = Font(name=FONT, size=10, bold=True)
for col, letter in ((2, "B"), (3, "C"), (4, "D")):
    c = vu.cell(row=sum_k, column=col,
                value=f"=SUM({letter}{start_k+1}:{letter}{sum_k-1})")
    c.font = Font(name=FONT, size=10, bold=True)
    c.fill = PatternFill("solid", fgColor=HELL)
    c.number_format = "0" if col == 2 else EUR

# Auswertung je Kanal
kanaele = sorted({a["Kanal"] for a in daten if a["Kanal"]})
start_c = sum_k + 3
titel(start_c - 1, "Nach Verkaufskanal", 11)
for j, h in enumerate(["Kanal", "Positionen", "Umsatz netto"]):
    c = vu.cell(row=start_c, column=1 + j, value=h)
    c.font = Font(name=FONT, size=10, bold=True, color="FFFFFF")
    c.fill = PatternFill("solid", fgColor=MITTEL)
for i, k in enumerate(kanaele):
    row = start_c + 1 + i
    vu.cell(row=row, column=1, value=k).font = Font(name=FONT, size=10)
    vu.cell(row=row, column=2, value=f'=COUNTIF({A("Kanal")},$A{row})').number_format = "0"
    c = vu.cell(row=row, column=3, value=f'=SUMPRODUCT(({A("Kanal")}=$A{row})*'
                                        f'{A("Verkauft_Menge")}*{A("Verkaufspreis_netto")})')
    c.number_format = EUR
    for col in range(1, 4):
        vu.cell(row=row, column=col).font = Font(name=FONT, size=10)

# =============================================================================
# Blatt 3: Legende
# =============================================================================
lg = wb.create_sheet("Legende")
lg.column_dimensions["A"].width = 26
lg.column_dimensions["B"].width = 96
lg["A1"] = "Legende / Ausfüllhilfe"
lg["A1"].font = Font(name=FONT, size=14, bold=True, color=DUNKEL)
hinweise = [
    ("Gelbe Felder", "Das sind die Felder, die im Tagesgeschäft gepflegt werden. Alles andere bleibt meist unverändert."),
    ("ArtNr", "Eindeutige Nummer. Kommt auch als Etikett an den Artikel im Haus – so passen Liste und Realität zusammen."),
    ("Menge", "Ursprünglich vorhandene Stückzahl. Bleibt stehen, auch wenn verkauft wird."),
    ("Verkauft_Menge / Restmenge", "Restmenge rechnet sich selbst aus (Menge minus verkaufte Menge). Nicht überschreiben."),
    ("Einheit", "Stück, Karton, Set, Palette, Konvolut. Für 'ein Karton Acrylfarben' also Einheit = Karton."),
    ("Anlagennr", "Verweis auf Anlagenverzeichnis bzw. GWG-Liste – damit der Steuerberater den Abgang zuordnen kann."),
    ("Preis_netto", "Verkaufspreis OHNE Umsatzsteuer, pro Einheit. Gegenüber Firmen wird netto angeboten, gegenüber Privatleuten brutto ausgewiesen."),
    ("Preisbasis", "Fix = Festpreis, VHB = Verhandlungsbasis."),
    ("Status", "verfügbar / reserviert / verkauft / gespendet / entsorgt. Steuert, was im Online-Katalog angezeigt wird."),
    ("Kanal", "Wo der Artikel angeboten wird: Klinik, Kleinanzeigen, eBay, Direkt, Händler."),
    ("Umsatz_netto", "Rechnet sich selbst aus (verkaufte Menge × Verkaufspreis). Nicht überschreiben."),
    ("Zahlung", "offen / bezahlt / teilbezahlt. Bar bezahlte Beträge zusätzlich ins Kassenbuch eintragen (GoBD)."),
    ("Verkaufsübersicht", "Reines Auswertungsblatt. Rechnet automatisch, dort wird nichts eingetragen."),
    ("Wichtig", "Diese Datei ist die einzige Quelle der Wahrheit. Aus ihr entstehen Klinik-Angebot, Online-Katalog, "
                "eBay-/Kleinanzeigen-Inserate und die Zahlen für die Buchhaltung."),
]
for i, (a, b) in enumerate(hinweise, start=3):
    ca = lg.cell(row=i, column=1, value=a); ca.font = Font(name=FONT, size=10, bold=True)
    ca.alignment = Alignment(vertical="top")
    cb = lg.cell(row=i, column=2, value=b); cb.font = Font(name=FONT, size=10)
    cb.alignment = Alignment(vertical="top", wrap_text=True)
    lg.row_dimensions[i].height = 28

pfad = os.path.join(BASIS, "ausgabe", "01_Artikelstamm_BEISPIEL.xlsx")
wb.save(pfad)
print("geschrieben:", pfad)
