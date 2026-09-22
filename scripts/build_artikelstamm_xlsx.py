"""Erzeugt 01_Artikelstamm_kikripp.xlsx – die Arbeitsdatei für OneDrive."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import (lade_artikel, AUSGABE, ASSETS, USt_SATZ, ROT, SCHWARZ, PAPIER, GRAU, LINIE,
                 FELD_KLINIK, FELD_INTERN, ZEILE, FONT, FIRMA, ABSENDER)
from openpyxl.drawing.image import Image as XLImage
from PIL import Image as PILImage

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import CellIsRule

DUNKEL, MITTEL, HELL, GELB = SCHWARZ, "404040", PAPIER, FELD_INTERN
EUR = '#,##0.00 "€"'
duenn = Side(style="thin", color=LINIE)
RAHMEN = Border(left=duenn, right=duenn, top=duenn, bottom=duenn)

# (Überschrift, Breite, Gruppe, Typ)  Typ: text|int|eur|formel
SPALTEN = [
    ("ArtNr",                  10, "Stammdaten",   "text"),
    ("Alt_ArtNr",              10, "Stammdaten",   "text"),
    ("Raumcode",               10, "Stammdaten",   "text"),
    ("Bezeichnung",            34, "Stammdaten",   "text"),
    ("Beschreibung",           54, "Stammdaten",   "text"),
    ("Kategorie",              18, "Stammdaten",   "text"),
    ("Raum",                   20, "Stammdaten",   "text"),
    ("Wertklasse",             10, "Stammdaten",   "text"),
    ("Menge",                   8, "Stammdaten",   "int"),
    ("Verkauft_Menge",         13, "Stammdaten",   "int"),
    ("Restmenge",              10, "Stammdaten",   "formel"),
    ("Einheit",                10, "Stammdaten",   "text"),
    ("Zustand",                14, "Stammdaten",   "text"),
    ("Maße",                   22, "Stammdaten",   "text"),
    ("Aktiv",                  9,  "Stammdaten",   "text"),
    ("Anlagennr",              12, "Buchhaltung",  "text"),
    ("Anschaffungswert_netto", 17, "Buchhaltung",  "eur"),
    ("Preis_netto",            13, "Preis",        "eur"),
    ("Preisbasis",             11, "Preis",        "text"),
    ("Positionswert_netto",    17, "Preis",        "formel"),
    ("Versand",                16, "Vermarktung",  "text"),
    ("Foto",                   9,  "Vermarktung",  "text"),
    ("Im_Katalog",             12, "Vermarktung",  "text"),
    ("Klinik_Markierung",      18, "Vermarktung",  "text"),
    ("Status",                 12, "Vermarktung",  "text"),
    ("Marke",                  14, "Vermarktung",  "text"),
    ("Kanal",                  14, "Vermarktung",  "text"),
    ("Reserviert_für",         22, "Vermarktung",  "text"),
    ("Verkaufspreis_netto",    17, "Verkauf",      "eur"),
    ("Umsatz_netto",           14, "Verkauf",      "formel"),
    ("Verkaufsdatum",          14, "Verkauf",      "text"),
    ("Käufer",                 24, "Verkauf",      "text"),
    ("Rechnungsnr",            14, "Kaufmännisch", "text"),
    ("Zahlung",                11, "Kaufmännisch", "text"),
    ("Zahlart",                13, "Kaufmännisch", "text"),
    ("Abholtermin",            13, "Kaufmännisch", "text"),
    ("Mengenhinweis",          40, "Notizen",      "text"),
    ("Bemerkung",              32, "Notizen",      "text"),
]
GRUPPENFARBE = {"Stammdaten": SCHWARZ, "Buchhaltung": "595959", "Preis": ROT,
                "Vermarktung": "404040", "Verkauf": ROT, "Kaufmännisch": "595959",
                "Notizen": "8C8C8C"}
IDX = {s[0]: i + 1 for i, s in enumerate(SPALTEN)}
def L(n): return get_column_letter(IDX[n])

PFLEGE = {"Menge", "Verkauft_Menge", "Maße", "Aktiv", "Im_Katalog", "Klinik_Markierung",
          "Anlagennr", "Anschaffungswert_netto", "Preis_netto",
          "Preisbasis", "Marke", "Status", "Kanal", "Reserviert_für", "Verkaufspreis_netto",
          "Verkaufsdatum", "Käufer", "Rechnungsnr", "Zahlung", "Zahlart", "Abholtermin", "Bemerkung"}

AUSWAHL = {
    "Wertklasse": '"A,B,C"',
    "Aktiv":      '"ja,entfällt"',
    "Im_Katalog": '"ja,nein"',
    "Klinik_Markierung": '"ja,nein"',
    "Einheit":    '"Stück,Karton,Set,Palette,Konvolut"',
    "Zustand":    '"neuwertig,gut,gebraucht,stark gebraucht,defekt"',
    "Preisbasis": '"Fix,VHB"',
    "Versand":    '"nur Abholung,Versand möglich,Spedition"',
    "Status":     '"verfügbar,reserviert,teilverkauft,verkauft,gespendet,entsorgt"',
    "Kanal":      '"Webkatalog,Kleinanzeigen,eBay,Direkt,Händler,Verkaufstag"',
    "Zahlung":    '"offen,bezahlt,teilbezahlt"',
    "Zahlart":    '"Überweisung,bar,PayPal"',
}

daten = lade_artikel(nur_aktive=False)   # entfallene Zeilen bleiben sichtbar
Z0, Z1 = 3, 2 + len(daten)

wb = Workbook()

# =============================================================================
# Blatt 1: Anleitung
# =============================================================================
an = wb.active
an.title = "Anleitung"
an.column_dimensions["A"].width = 30
an.column_dimensions["B"].width = 104
an.merge_cells("A1:B1")
for col in (1, 2):
    an.cell(row=1, column=col).fill = PatternFill("solid", fgColor=SCHWARZ)
an["A1"] = "        Artikelverwaltung Betriebsauflösung – Kurzanleitung"
an["A1"].font = Font(name=FONT, size=15, bold=True, color="FFFFFF")
an["A1"].alignment = Alignment(vertical="center")
an.row_dimensions[1].height = 42
_logo = os.path.join(ASSETS, "kopflogo.png")
if os.path.exists(_logo):
    with PILImage.open(_logo) as _im:
        _h = 46; _im = _im.resize((int(_im.width * _h / _im.height), _h))
        _im.save("/tmp/_kopflogo_stamm.png")
    an.add_image(XLImage("/tmp/_kopflogo_stamm.png"), "A1")
an["A2"] = "Diese Datei liegt in OneDrive und ist die einzige Quelle der Wahrheit. Bitte immer direkt hier arbeiten – nicht herunterladen, bearbeiten und wieder hochladen."
an["A2"].font = Font(name=FONT, size=10, italic=True, color=SCHWARZ)
an["A2"].fill = PatternFill("solid", fgColor=PAPIER)
an.merge_cells("A2:B2")
an.row_dimensions[2].height = 28
an["A2"].alignment = Alignment(wrap_text=True, vertical="center")

TEXTE = [
    ("Die vier Blätter", ""),
    ("  Artikelstamm", "Alle Artikel. Hier wird gepflegt. Grau hinterlegte Spalten sind die Felder zum Ausfüllen, alles andere rechnet sich selbst oder bleibt stehen."),
    ("  Verkaufsübersicht", "Reines Auswertungsblatt. Umsatz, offene Rechnungen, Restbestand – rechnet automatisch. Hier nichts eintragen."),
    ("  Rechnungen (DATEV)", "Abtippliste: je Zeile eine Rechnung, in der Reihenfolge der DATEV-Erfassungsmaske. Ausdrucken und abarbeiten."),
    ("  Kasse", "Barverkäufe je Tag für das Kassenbuch. Pflicht bei einer GmbH (GoBD)."),
    ("", ""),
    ("Die wichtigsten Regeln", ""),
    ("  Ein Artikel verkauft", "Status auf „verkauft“, Verkaufspreis, Verkaufte Menge, Käufer und Datum eintragen. Der Rest rechnet sich."),
    ("  Reservierung", "Status auf „reserviert“, Name und Abholtermin eintragen. Ohne Abholtermin keine Reservierung – sonst blockiert die Ware."),
    ("  Restmenge", "Rechnet sich aus Menge minus verkaufter Menge. Nicht überschreiben."),
    ("  Preise", "Immer netto pro Einheit. Firmen bekommen Nettopreise, Privatpersonen müssen den Bruttopreis sehen (Preisangabenverordnung)."),
    ("  Wertklasse", "A = Wertträger, einzeln vermarkten · B = Einzelposition im Katalog · C = Kleinteil, geht in den Verkaufstag."),
    ("  Barzahlung", "Immer zusätzlich im Blatt „Kasse“ erfassen. Die Rechnung mit dem Vermerk „bar erhalten“ allein genügt bei einer GmbH nicht."),
    ("  Anlagennummer", "Wenn bekannt eintragen – der Steuerberater braucht sie für den Anlagenabgang."),
    ("", ""),
    ("Hinweise zu den Preisen", "Alle Preise in dieser Datei sind Schätzwerte auf Basis der Fotos. Maße, Marken und Stückzahlen fehlen teilweise – die gelb markierten Spalten „Maße“ und „Preis_netto“ sind zur Überarbeitung gedacht."),
    ("Designmöbel", "Vitra Alcove und USM Haller sind als solche vermerkt. Für beide gibt es einen eigenen Gebrauchtmarkt mit Fachhändlern – dort sind höhere Preise erzielbar als im Sammelangebot."),
    ("Kunst", "Die Acrylbilder sind Eigenarbeiten einer Privatperson, die Schwarzwald-Trachtenmotive sind Kaufware. Beides ist in der Beschreibung vermerkt."),
]
r = 4
for a, b in TEXTE:
    ca = an.cell(row=r, column=1, value=a)
    ca.font = Font(name=FONT, size=10, bold=not a.startswith("  ") and bool(a), color=DUNKEL if not a.startswith("  ") else "000000")
    ca.alignment = Alignment(vertical="top")
    cb = an.cell(row=r, column=2, value=b)
    cb.font = Font(name=FONT, size=10)
    cb.alignment = Alignment(vertical="top", wrap_text=True)
    an.row_dimensions[r].height = 30 if b else 12
    r += 1

# =============================================================================
# Blatt 2: Artikelstamm
# =============================================================================
ws = wb.create_sheet("Artikelstamm")
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
for i, (name, breite, _g, _t) in enumerate(SPALTEN, start=1):
    c = ws.cell(row=2, column=i, value=name)
    c.font = Font(name=FONT, size=10, bold=True, color="FFFFFF")
    c.fill = PatternFill("solid", fgColor=("7A7A7A" if name in PFLEGE else SCHWARZ))
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border = RAHMEN
    ws.column_dimensions[get_column_letter(i)].width = breite
ws.row_dimensions[1].height = 16
ws.row_dimensions[2].height = 32

for j, art in enumerate(daten):
    r = Z0 + j
    for name, _b, _g, typ in SPALTEN:
        if name == "Restmenge":
            wert = f'={L("Menge")}{r}-IF({L("Verkauft_Menge")}{r}="",0,{L("Verkauft_Menge")}{r})'
        elif name == "Positionswert_netto":
            wert = f'={L("Restmenge")}{r}*{L("Preis_netto")}{r}'
        elif name == "Umsatz_netto":
            wert = (f'=IF({L("Verkauft_Menge")}{r}="","",'
                    f'{L("Verkauft_Menge")}{r}*{L("Verkaufspreis_netto")}{r})')
        else:
            wert = art.get(name) or None
        c = ws.cell(row=r, column=IDX[name], value=wert)
        c.font = Font(name=FONT, size=10)
        c.border = RAHMEN
        c.alignment = Alignment(vertical="top",
                                wrap_text=name in ("Beschreibung", "Bemerkung", "Mengenhinweis"))
        if typ == "eur" or name in ("Positionswert_netto", "Umsatz_netto"):
            c.number_format = EUR
        if typ == "int" or name == "Restmenge":
            c.number_format = "0"
        if name in PFLEGE:
            c.fill = PatternFill("solid", fgColor=FELD_INTERN)
    ws.row_dimensions[r].height = 30

ws.freeze_panes = "C3"
ws.auto_filter.ref = f"A2:{get_column_letter(len(SPALTEN))}{Z1}"
for name, formel in AUSWAHL.items():
    dv = DataValidation(type="list", formula1=formel, allow_blank=True, showDropDown=False)
    ws.add_data_validation(dv)
    dv.add(f"{L(name)}{Z0}:{L(name)}{Z0+800}")
s = f"{L('Status')}{Z0}:{L('Status')}{Z1}"
for wert, farbe in (("reserviert", "E4E4E4"), ("teilverkauft", "DCDCDC"), ("verkauft", "C9C9C9")):
    ws.conditional_formatting.add(s, CellIsRule(operator="equal", formula=[f'"{wert}"'],
                                                fill=PatternFill("solid", bgColor=farbe)))
wk = f"{L('Wertklasse')}{Z0}:{L('Wertklasse')}{Z1}"
ws.conditional_formatting.add(wk, CellIsRule(operator="equal", formula=['"A"'],
    font=Font(name=FONT, size=10, bold=True, color=ROT)))
ak = f"{L('Aktiv')}{Z0}:{L('Aktiv')}{Z1}"
ws.conditional_formatting.add(ak, CellIsRule(operator="equal", formula=['"entfällt"'],
    fill=PatternFill("solid", bgColor="C9C9C9"),
    font=Font(name=FONT, size=10, italic=True, color="7A7A7A")))

# =============================================================================
# Blatt 3: Verkaufsübersicht
# =============================================================================
vu = wb.create_sheet("Verkaufsübersicht")
A = lambda n: f"Artikelstamm!${L(n)}${Z0}:${L(n)}${Z1}"
vu.column_dimensions["A"].width = 44
for col in "BCDE":
    vu.column_dimensions[col].width = 18

def titel(row, text, size=12):
    c = vu.cell(row=row, column=1, value=text)
    c.font = Font(name=FONT, size=size, bold=True, color=DUNKEL)

def kpi(row, label, formel, fmt=None, fett=False):
    a = vu.cell(row=row, column=1, value=label); a.font = Font(name=FONT, size=10, bold=fett)
    b = vu.cell(row=row, column=2, value=formel); b.font = Font(name=FONT, size=10, bold=fett)
    b.alignment = Alignment(horizontal="right")
    if fmt: b.number_format = fmt
    if fett: b.fill = PatternFill("solid", fgColor=HELL)
    return row + 1

titel(1, "Verkaufsübersicht – rechnet automatisch aus dem Artikelstamm", 13)
vu["A2"] = "Hier wird nichts eingetragen. Wer im Artikelstamm einen Verkauf erfasst, sieht ihn sofort hier."
vu["A2"].font = Font(name=FONT, size=9, italic=True, color="808080")

titel(4, "Bestand")
r = 5
r = kpi(r, "Artikelpositionen gesamt", f'=COUNTA({A("ArtNr")})', "0")
r = kpi(r, "davon verfügbar", f'=COUNTIF({A("Status")},"verfügbar")', "0")
r = kpi(r, "davon reserviert", f'=COUNTIF({A("Status")},"reserviert")', "0")
r = kpi(r, "davon teilverkauft", f'=COUNTIF({A("Status")},"teilverkauft")', "0")
r = kpi(r, "davon verkauft", f'=COUNTIF({A("Status")},"verkauft")', "0")
r = kpi(r, "Einheiten noch im Bestand", f'=SUM({A("Restmenge")})', "0")
r = kpi(r, "Restbestand zu Wunschpreisen (netto)", f'=SUM({A("Positionswert_netto")})', EUR, fett=True)

titel(12, "Erlöse")
r = 13
r = kpi(r, "Verkaufte Einheiten", f'=SUM({A("Verkauft_Menge")})', "0")
r = kpi(r, "Umsatz netto", f'=SUMPRODUCT({A("Verkauft_Menge")},{A("Verkaufspreis_netto")})', EUR)
r = kpi(r, f"zzgl. Umsatzsteuer {int(USt_SATZ*100)} %", f"=B14*{USt_SATZ}", EUR)
r = kpi(r, "Umsatz brutto", "=B14+B15", EUR, fett=True)
r = kpi(r, "davon bereits bezahlt (netto)",
        f'=SUMPRODUCT(({A("Zahlung")}="bezahlt")*{A("Verkauft_Menge")}*{A("Verkaufspreis_netto")})', EUR)
r = kpi(r, "noch offen (netto)", "=B14-B17", EUR)

titel(20, "To-do")
r = 21
r = kpi(r, "Rechnungen noch zu schreiben",
        f'=COUNTIFS({A("Status")},"*verkauft",{A("Rechnungsnr")},"")', "0", fett=True)
r = kpi(r, "Rechnungen offen (unbezahlt)",
        f'=COUNTIFS({A("Status")},"*verkauft",{A("Zahlung")},"offen")', "0", fett=True)
r = kpi(r, "Reservierungen ohne Abholtermin",
        f'=COUNTIFS({A("Status")},"reserviert",{A("Abholtermin")},"")', "0")
r = kpi(r, "Artikel ohne Preis", f'=COUNTIFS({A("Preis_netto")},"")', "0")
r = kpi(r, "Artikel ohne Maßangabe", f'=COUNTIFS({A("Maße")},"")', "0")

def block(startzeile, ueberschrift, spalte, werte, mit_rest=True):
    titel(startzeile - 1, ueberschrift)
    kopf = [ueberschrift.replace("Nach ", ""), "Positionen", "Umsatz netto"] + (["Restwert netto"] if mit_rest else [])
    for j, h in enumerate(kopf):
        c = vu.cell(row=startzeile, column=1 + j, value=h)
        c.font = Font(name=FONT, size=10, bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor=MITTEL)
    for i, k in enumerate(werte):
        row = startzeile + 1 + i
        vu.cell(row=row, column=1, value=k).font = Font(name=FONT, size=10)
        c = vu.cell(row=row, column=2, value=f'=COUNTIF({A(spalte)},$A{row})'); c.number_format = "0"
        c.font = Font(name=FONT, size=10)
        c = vu.cell(row=row, column=3, value=f'=SUMPRODUCT(({A(spalte)}=$A{row})*'
                                            f'{A("Verkauft_Menge")}*{A("Verkaufspreis_netto")})')
        c.number_format = EUR; c.font = Font(name=FONT, size=10)
        if mit_rest:
            c = vu.cell(row=row, column=4, value=f'=SUMIF({A(spalte)},$A{row},{A("Positionswert_netto")})')
            c.number_format = EUR; c.font = Font(name=FONT, size=10)
    ende = startzeile + 1 + len(werte)
    vu.cell(row=ende, column=1, value="Summe").font = Font(name=FONT, size=10, bold=True)
    for col in range(2, 5 if mit_rest else 4):
        letter = get_column_letter(col)
        c = vu.cell(row=ende, column=col, value=f"=SUM({letter}{startzeile+1}:{letter}{ende-1})")
        c.font = Font(name=FONT, size=10, bold=True)
        c.fill = PatternFill("solid", fgColor=HELL)
        c.number_format = "0" if col == 2 else EUR
    return ende + 3

nz = block(29, "Nach Wertklasse", "Wertklasse", ["A", "B", "C"])
nz = block(nz, "Nach Kategorie", "Kategorie", sorted({a["Kategorie"] for a in daten}))
nz = block(nz, "Nach Raum", "Raum", sorted({a["Raum"] for a in daten}))
block(nz, "Nach Verkaufskanal", "Kanal",
      ["Klinik", "Kleinanzeigen", "eBay", "Direkt", "Händler", "Verkaufstag"], mit_rest=False)

# =============================================================================
# Blatt 4: Rechnungen (DATEV)
# =============================================================================
re_ = wb.create_sheet("Rechnungen (DATEV)")
RE_SP = [("lfd.", 6), ("Käufer / Firma", 30), ("Anschrift", 38), ("Artikel (ArtNr)", 26),
         ("Leistungsdatum", 14), ("Netto", 13), ("USt 19 %", 13), ("Brutto", 13),
         ("Zahlart", 13), ("DATEV-Rechnungsnr", 18), ("geschrieben am", 14), ("bezahlt am", 13)]
re_["A1"] = "Rechnungen – Abtippliste für DATEV Auftragswesen"
re_["A1"].font = Font(name=FONT, size=14, bold=True, color=DUNKEL)
re_.merge_cells("A2:L2")
re_["A2"] = ("Die Spalten stehen in der Reihenfolge der DATEV-Erfassungsmaske. Ausdrucken, abarbeiten, "
             "die DATEV-Rechnungsnummer hier und im Artikelstamm eintragen. USt und Brutto rechnen sich selbst. "
             "Die Rechnung selbst wird ausschließlich in DATEV erstellt – es gibt bewusst kein zweites Rechnungsdokument.")
re_["A2"].font = Font(name=FONT, size=9, italic=True, color=SCHWARZ)
re_["A2"].fill = PatternFill("solid", fgColor=PAPIER)
re_["A2"].border = Border(left=Side(style="thick", color=ROT))
re_["A2"].alignment = Alignment(wrap_text=True, vertical="center")
re_.row_dimensions[2].height = 34
for i, (h, w) in enumerate(RE_SP, start=1):
    c = re_.cell(row=4, column=i, value=h)
    c.font = Font(name=FONT, size=10, bold=True, color="FFFFFF")
    c.fill = PatternFill("solid", fgColor=MITTEL)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border = RAHMEN
    re_.column_dimensions[get_column_letter(i)].width = w
re_.row_dimensions[4].height = 30
for r in range(5, 45):
    re_.cell(row=r, column=1, value=r - 4).font = Font(name=FONT, size=10)
    re_.cell(row=r, column=7, value=f"=IF(F{r}=\"\",\"\",F{r}*{USt_SATZ})").number_format = EUR
    re_.cell(row=r, column=8, value=f"=IF(F{r}=\"\",\"\",F{r}+G{r})").number_format = EUR
    re_.cell(row=r, column=6).number_format = EUR
    for col in range(1, len(RE_SP) + 1):
        cc = re_.cell(row=r, column=col)
        cc.border = RAHMEN
        cc.font = Font(name=FONT, size=10)
        if col in (2, 3, 4, 5, 6, 9, 10, 11, 12):
            cc.fill = PatternFill("solid", fgColor=FELD_INTERN)
re_.cell(row=45, column=5, value="Summe").font = Font(name=FONT, size=11, bold=True)
for col in (6, 7, 8):
    letter = get_column_letter(col)
    c = re_.cell(row=45, column=col, value=f"=SUM({letter}5:{letter}44)")
    c.font = Font(name=FONT, size=11, bold=True); c.number_format = EUR
    c.fill = PatternFill("solid", fgColor=HELL); c.border = RAHMEN
re_.freeze_panes = "A5"
re_.page_setup.orientation = "landscape"
re_.sheet_properties.pageSetUpPr.fitToPage = True
re_.page_setup.fitToWidth = 1

# =============================================================================
# Blatt 5: Kasse
# =============================================================================
ka = wb.create_sheet("Kasse")
KA_SP = [("Datum", 13), ("Beleg-Nr", 12), ("Vorgang / Käufer", 42), ("Einnahme brutto", 16),
         ("davon USt 19 %", 16), ("netto", 14), ("Ausgabe brutto", 15), ("Kassenbestand", 16)]
ka["A1"] = "Kassenbuch Barverkäufe"
ka["A1"].font = Font(name=FONT, size=14, bold=True, color=DUNKEL)
ka.merge_cells("A2:H2")
ka["A2"] = ("Pflicht bei einer GmbH (GoBD): jede Bareinnahme am selben Tag erfassen. Am Verkaufstag reicht eine "
            "Sammelzeile mit der Tageseinnahme, dazu ein Zählprotokoll aufbewahren. Bitte einmal mit dem "
            "Steuerberater abstimmen, in welcher Form er die Daten haben will.")
ka["A2"].font = Font(name=FONT, size=9, italic=True, color=SCHWARZ)
ka["A2"].fill = PatternFill("solid", fgColor=PAPIER)
ka["A2"].border = Border(left=Side(style="thick", color=ROT))
ka["A2"].alignment = Alignment(wrap_text=True, vertical="center")
ka.row_dimensions[2].height = 32
for i, (h, w) in enumerate(KA_SP, start=1):
    c = ka.cell(row=4, column=i, value=h)
    c.font = Font(name=FONT, size=10, bold=True, color="FFFFFF")
    c.fill = PatternFill("solid", fgColor=MITTEL)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border = RAHMEN
    ka.column_dimensions[get_column_letter(i)].width = w
ka.cell(row=5, column=3, value="Anfangsbestand Kasse")
ka.cell(row=5, column=8, value=0).number_format = EUR
for r in range(6, 56):
    ka.cell(row=r, column=5, value=f'=IF(D{r}="","",D{r}-D{r}/{1+USt_SATZ})').number_format = EUR
    ka.cell(row=r, column=6, value=f'=IF(D{r}="","",D{r}/{1+USt_SATZ})').number_format = EUR
    ka.cell(row=r, column=8, value=f'=H{r-1}+IF(D{r}="",0,D{r})-IF(G{r}="",0,G{r})').number_format = EUR
    ka.cell(row=r, column=4).number_format = EUR
    ka.cell(row=r, column=7).number_format = EUR
    for col in range(1, 9):
        cc = ka.cell(row=r, column=col); cc.border = RAHMEN; cc.font = Font(name=FONT, size=10)
        if col in (1, 2, 3, 4, 7):
            cc.fill = PatternFill("solid", fgColor=FELD_INTERN)
ka.freeze_panes = "A5"

# =============================================================================
# Blatt 6: Design – hier werden Farben, Firmendaten und Konditionen gepflegt
# =============================================================================
import csv as _csv
dg = wb.create_sheet("Design")
dg.column_dimensions["A"].width = 26
dg.column_dimensions["B"].width = 34
dg.column_dimensions["C"].width = 62
dg.merge_cells("A1:C1")
for col in (1, 2, 3):
    dg.cell(row=1, column=col).fill = PatternFill("solid", fgColor=SCHWARZ)
dg["A1"] = "Design und Stammdaten"
dg["A1"].font = Font(name=FONT, size=14, bold=True, color="FFFFFF")
dg["A1"].alignment = Alignment(vertical="center", indent=1)
dg.row_dimensions[1].height = 30
dg.merge_cells("A2:C2")
dg["A2"] = ("Hier ändern – nicht in den anderen Blättern. Farben als HEX ohne Raute (z. B. C8102E). "
            "Die Werte werden beim Rückeinlesen übernommen und gelten dann für Angebot, Katalog und Webkatalog.")
dg["A2"].font = Font(name=FONT, size=9, italic=True, color=SCHWARZ)
dg["A2"].fill = PatternFill("solid", fgColor=PAPIER)
dg["A2"].border = Border(left=Side(style="thick", color=ROT))
dg["A2"].alignment = Alignment(wrap_text=True, vertical="center")
dg.row_dimensions[2].height = 30
for j, h in enumerate(["Schlüssel", "Wert", "Hinweis"]):
    c = dg.cell(row=4, column=1 + j, value=h)
    c.font = Font(name=FONT, size=10, bold=True, color="FFFFFF")
    c.fill = PatternFill("solid", fgColor=("595959" if j == 1 else MITTEL))
    c.border = RAHMEN
    c.alignment = Alignment(horizontal="center", vertical="center")
with open(os.path.join(os.path.dirname(AUSGABE), "daten", "design.csv"), encoding="utf-8") as _f:
    for i, row in enumerate(_csv.DictReader(_f, delimiter=";"), start=5):
        dg.cell(row=i, column=1, value=row["Schluessel"]).font = Font(name=FONT, size=10, bold=True)
        cw = dg.cell(row=i, column=2, value=row["Wert"])
        cw.font = Font(name=FONT, size=10)
        cw.fill = PatternFill("solid", fgColor=FELD_INTERN)
        ch = dg.cell(row=i, column=3, value=row.get("Hinweis") or "")
        ch.font = Font(name=FONT, size=9, color=GRAU)
        for col in (1, 2, 3):
            dg.cell(row=i, column=col).border = RAHMEN
        if row["Schluessel"].startswith("Farbe_") or row["Schluessel"].startswith("Feld_") \
           or row["Schluessel"] == "Zeile_Wechsel":
            try:
                dg.cell(row=i, column=3).fill = PatternFill("solid", fgColor=row["Wert"])
            except Exception:
                pass
dg.freeze_panes = "A5"

pfad = os.path.join(AUSGABE, "01_Artikelstamm_kikripp.xlsx")
os.makedirs(AUSGABE, exist_ok=True)
wb.save(pfad)
print("geschrieben:", pfad, "-", len(daten), "Positionen,", len(wb.sheetnames), "Blätter")
