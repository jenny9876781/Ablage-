"""Prüft Datenbasis und erzeugte Dateien. Vor jeder Übergabe laufen lassen.

    python3 scripts/pruefen.py

Gibt am Ende die Zahl der Beanstandungen aus und beendet sich mit Code 1, wenn es welche gibt.
"""
import sys, os, re, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import lade_artikel, foto, AUSGABE, BASIS, eur, USt_SATZ, PAKETRABATT
from openpyxl import load_workbook

fehler, warnung = [], []
def F(t): fehler.append(t);  print("  FEHLER  ", t)
def W(t): warnung.append(t); print("  Hinweis ", t)
def OK(t): print("  ok      ", t)

print("\n== 1. Datenbasis ==")
alle = lade_artikel(nur_aktive=False)
aktiv = lade_artikel()
nummern = [a["ArtNr"] for a in alle]
if len(nummern) != len(set(nummern)):
    doppelt = {n for n in nummern if nummern.count(n) > 1}
    F(f"doppelte Artikelnummern: {sorted(doppelt)}")
else:
    OK(f"{len(alle)} Positionen, davon {len(aktiv)} aktiv, keine doppelten Nummern")

ohne_foto = [a["ArtNr"] for a in aktiv if not a["Foto"]]
fehlt = [f'{a["ArtNr"]} ({a["Foto"]})' for a in aktiv if a["Foto"] and not foto(a["Foto"])]
if fehlt: F(f"Fotodatei fehlt: {fehlt}")
else:     OK("alle Fotoverweise zeigen auf vorhandene Dateien")
if ohne_foto: W(f"{len(ohne_foto)} Positionen ohne Foto: {ohne_foto[:8]}")

ohne_preis = [a["ArtNr"] for a in aktiv if not a["Preis_netto"]]
if ohne_preis: W(f"{len(ohne_preis)} Positionen ohne Preis: {ohne_preis[:8]}")
else:          OK("alle aktiven Positionen haben einen Preis")
ohne_mass = [a["ArtNr"] for a in aktiv if not a.get("Maße")]
if ohne_mass: W(f"{len(ohne_mass)} Positionen ohne Maßangabe")
nachzaehlen = [a["ArtNr"] for a in aktiv if "nachzählen" in (a.get("Mengenhinweis") or "")]
if nachzaehlen: W(f"{len(nachzaehlen)} Positionen mit offener Stückzahl")

print("\n== 2. Fotoindex ==")
idx = os.path.join(BASIS, "daten", "fotos_index.csv")
if not os.path.exists(idx):
    F("daten/fotos_index.csv fehlt – ohne Index werden Fotonummern neu vergeben")
else:
    rows = list(csv.DictReader(open(idx, encoding="utf-8"), delimiter=";"))
    nums = [r["Foto"] for r in rows]
    if len(nums) != len(set(nums)): F("doppelte Fotonummern im Index")
    else: OK(f"{len(rows)} Fotos im Index, Nummern eindeutig")
    dateien = {x[:-4] for x in os.listdir(os.path.join(BASIS, "fotos")) if x.endswith(".jpg")}
    verwaist = sorted(dateien - set(nums))
    if verwaist: W(f"Fotodateien ohne Indexeintrag: {verwaist[:8]}")

print("\n== 3. Arbeitsmappe ==")
p = os.path.join(AUSGABE, "01_Artikelstamm_kikripp.xlsx")
if not os.path.exists(p):
    F("01_Artikelstamm_kikripp.xlsx fehlt – erst erzeugen")
else:
    wb = load_workbook(p)
    erwartet = ["Anleitung", "Artikelstamm", "Verkaufsübersicht", "Rechnungen (DATEV)",
                "Kasse", "Design"]
    if wb.sheetnames != erwartet: F(f"Blätter weichen ab: {wb.sheetnames}")
    else: OK("alle sechs Blätter vorhanden")
    st, vu = wb["Artikelstamm"], wb["Verkaufsübersicht"]
    kopf = {c.column_letter: c.value for c in st[2] if c.value}
    # Zeile 8 „davon teilverkauft“ ist dazugekommen, alles darunter rückt eins nach unten.
    ERW = {5:["ArtNr"], 6:["Status"], 7:["Status"], 8:["Status"], 9:["Status"],
           10:["Restmenge"], 11:["Positionswert_netto"], 13:["Verkauft_Menge"],
           14:["Verkauft_Menge","Verkaufspreis_netto"],
           17:["Zahlung","Verkauft_Menge","Verkaufspreis_netto"],
           21:["Status","Rechnungsnr"], 22:["Status","Zahlung"],
           23:["Status","Abholtermin"], 24:["Preis_netto"], 25:["Maße"]}
    schief = []
    for z, erw in ERW.items():
        ist = list(dict.fromkeys(re.findall(r"Artikelstamm!\$([A-Z]{1,2})\$",
                                            vu.cell(row=z, column=2).value or "")))
        if [kopf.get(x) for x in ist] != erw:
            schief.append((z, vu.cell(row=z, column=1).value, [kopf.get(x) for x in ist], erw))
    if schief:
        for z, label, ist, erw in schief:
            F(f"Verkaufsübersicht Z{z} „{label}“ greift auf {ist} statt {erw}")
    else:
        OK(f"alle {len(ERW)} Kennzahlen greifen auf die richtigen Spalten")

    ZAHLEN = ["Preis_netto", "Anschaffungswert_netto", "Verkaufspreis_netto",
              "Menge", "Verkauft_Menge"]
    sp = {v: k for k, v in kopf.items()}
    text_in_zahl = []
    for name in ZAHLEN:
        if name not in sp: continue
        from openpyxl.utils import column_index_from_string
        c = column_index_from_string(sp[name])
        for r in range(3, st.max_row + 1):
            v = st.cell(row=r, column=c).value
            if isinstance(v, str) and v.strip():
                text_in_zahl.append(f"{name} Zeile {r}: {v!r}")
    if text_in_zahl: F(f"Text in Zahlenspalten (Formeln rechnen nicht): {text_in_zahl[:5]}")
    else: OK("alle Geld- und Mengenfelder sind Zahlen")

print("\n== 4. Ausgabedateien ==")
# Der PDF-Katalog ist entfallen; der Webkatalog auf kikripp.de hat ihn abgelöst.
for name, mindest in (("01_Artikelstamm_kikripp.xlsx", 20), ("02_Angebot_Klinik.xlsx", 500),
                      ("04_Webkatalog_MOCKUP.html", 500), ("06_Webkatalog_geschuetzt.html", 500),
                      ("katalog_import.json", 10)):
    pf = os.path.join(AUSGABE, name)
    if not os.path.exists(pf): F(f"{name} fehlt")
    elif os.path.getsize(pf) // 1024 < mindest: F(f"{name} ist auffällig klein")
    else: OK(f"{name} ({os.path.getsize(pf)//1024} KB)")

print("\n== 5. Summen ==")
gesamt = sum(a["Positionswert"] for a in aktiv)
print(f"  Gesamtwert netto  {eur(gesamt)}")
print(f"  zzgl. {int(USt_SATZ*100)} % USt    {eur(gesamt*USt_SATZ)}")
print(f"  brutto            {eur(gesamt*(1+USt_SATZ))}")
print(f"  Paketpreis netto  {eur(gesamt*(1-PAKETRABATT))}  (−{int(PAKETRABATT*100)} %)")
for k in ("A", "B", "C"):
    t = [a for a in aktiv if a["Wertklasse"] == k]
    print(f"  Wertklasse {k}      {len(t):>3} Positionen · {eur(sum(x['Positionswert'] for x in t))}")

print(f"\n== Ergebnis: {len(fehler)} Fehler, {len(warnung)} Hinweise ==")
sys.exit(1 if fehler else 0)
