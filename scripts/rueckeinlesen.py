"""Liest einen überarbeiteten Artikelstamm zurück in die Datenbasis.

    python3 scripts/rueckeinlesen.py [pfad/zur/Artikelstamm.xlsx]

Übernommen werden die inhaltlichen Spalten aus dem Blatt „Artikelstamm“ und die
Werte aus dem Blatt „Design“. Formeln, Layout und Verkaufsdaten bleiben unberührt.
Gelöschte Zeilen werden nicht entfernt, sondern auf Aktiv = „entfällt“ gesetzt.
"""
import sys, os, csv, shutil, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import CSV_PFAD, AUSGABE, BASIS                       # noqa: F401
from openpyxl import load_workbook

DESIGN_PFAD = os.path.join(BASIS, "daten", "design.csv")
STANDARD = os.path.join(AUSGABE, "01_Artikelstamm_kikripp.xlsx")

# Spalten, die aus der Arbeitsmappe zurückwandern (Excel-Spalte -> CSV-Spalte)
UEBERNEHMEN = ["Bezeichnung", "Beschreibung", "Kategorie", "Marke", "Bündel", "Weitere_ArtNr",
               "Raum", "Menge", "Einheit",
               "Zustand", "Maße", "Wertklasse", "Aktiv", "Im_Katalog",
               "Anlagennr", "Anschaffungswert_netto",
               "Preis_netto", "Preisbasis", "Versand", "Foto", "Status", "Kanal",
               "Reserviert_für", "Verkauft_Menge", "Verkaufspreis_netto", "Verkaufsdatum",
               "Käufer", "Rechnungsnr", "Zahlung", "Zahlart", "Abholtermin",
               "Mengenhinweis", "Klinik_Markierung", "Bemerkung"]
GELDFELDER = {"Preis_netto", "Anschaffungswert_netto", "Verkaufspreis_netto"}


def zahl_aus(v):
    if v is None or v == "":
        return ""
    if isinstance(v, (int, float)):
        return f"{float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return str(v).strip()


def sichern(pfad):
    stempel = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    ziel = f"{pfad}.{stempel}.bak"
    shutil.copy2(pfad, ziel)
    return ziel


def einlesen(xlsx):
    wb = load_workbook(xlsx, data_only=True)
    if "Artikelstamm" not in wb.sheetnames:
        raise SystemExit(f"Blatt „Artikelstamm“ fehlt in {xlsx}")
    ws = wb["Artikelstamm"]
    kopf = {c.value: c.column for c in ws[2] if c.value}
    if "ArtNr" not in kopf:
        raise SystemExit("In Zeile 2 des Blattes „Artikelstamm“ steht keine Spalte „ArtNr“. "
                         "Wurde eine Zeile eingefügt oder gelöscht? Bitte die Kopfzeile wieder "
                         "auf Zeile 2 bringen.")
    fehlend = [s for s in UEBERNEHMEN if s not in kopf]
    if fehlend:
        print("  Hinweis: diese Spalten fehlen in der Mappe und bleiben unverändert:", ", ".join(fehlend))
    neu = {}
    for r in range(3, ws.max_row + 1):
        artnr = ws.cell(row=r, column=kopf["ArtNr"]).value
        if not artnr:
            continue
        satz = {}
        for sp in UEBERNEHMEN:
            if sp in kopf:
                v = ws.cell(row=r, column=kopf[sp]).value
                satz[sp] = zahl_aus(v) if sp in GELDFELDER else ("" if v is None else str(v).strip())
        nr = str(artnr).strip()
        if nr in neu:
            print(f"  ACHTUNG: Artikelnummer {nr} kommt mehrfach vor – es gilt die letzte Zeile.")
        neu[nr] = satz

    with open(CSV_PFAD, encoding="utf-8") as f:
        alt = list(csv.DictReader(f, delimiter=";"))
    felder = list(alt[0].keys())

    geaendert, entfallen, ergaenzt = [], [], []
    bekannt = set()
    for zeile in alt:
        nr = zeile["ArtNr"]
        bekannt.add(nr)
        if nr not in neu:
            if zeile.get("Aktiv", "ja") != "entfällt":
                zeile["Aktiv"] = "entfällt"
                entfallen.append(nr)
            continue
        for sp, wert in neu[nr].items():
            if sp in zeile and zeile[sp] != wert:
                geaendert.append((nr, sp, zeile[sp], wert))
                zeile[sp] = wert
    for nr, satz in neu.items():
        if nr not in bekannt:
            zeile = {f: "" for f in felder}
            zeile["ArtNr"] = nr
            zeile.update({k: v for k, v in satz.items() if k in felder})
            zeile.setdefault("Aktiv", "ja")
            alt.append(zeile)
            ergaenzt.append(nr)

    sicherung = sichern(CSV_PFAD)
    with open(CSV_PFAD, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=felder, delimiter=";")
        w.writeheader(); w.writerows(alt)

    print(f"\nArtikel: {len(geaendert)} Feldänderungen · {len(ergaenzt)} neu · {len(entfallen)} auf „entfällt“")
    for nr, sp, a, b in geaendert[:40]:
        print(f"   {nr:8} {sp:16} {a!r:>22}  ->  {b!r}")
    if len(geaendert) > 40:
        print(f"   … und {len(geaendert)-40} weitere")
    if ergaenzt:  print("   neu:", ", ".join(ergaenzt))
    if entfallen: print("   entfällt:", ", ".join(entfallen))

    # ---- Design ----
    if "Design" in wb.sheetnames:
        dg = wb["Design"]
        werte = {}
        for r in range(5, dg.max_row + 1):
            k = dg.cell(row=r, column=1).value
            if k:
                werte[str(k).strip()] = "" if dg.cell(row=r, column=2).value is None \
                    else str(dg.cell(row=r, column=2).value).strip()
        with open(DESIGN_PFAD, encoding="utf-8") as f:
            zeilen = list(csv.DictReader(f, delimiter=";"))
        d_geaendert = []
        for z in zeilen:
            k = z["Schluessel"]
            if k in werte and werte[k] != z["Wert"]:
                d_geaendert.append((k, z["Wert"], werte[k]))
                z["Wert"] = werte[k]
        sichern(DESIGN_PFAD)
        with open(DESIGN_PFAD, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["Schluessel", "Wert", "Hinweis"], delimiter=";")
            w.writeheader(); w.writerows(zeilen)
        print(f"\nDesign: {len(d_geaendert)} Änderungen")
        for k, a, b in d_geaendert:
            print(f"   {k:22} {a!r:>26}  ->  {b!r}")

    print(f"\nSicherung der alten Datenbasis: {sicherung}")
    print("Jetzt die Ausgabedateien neu erzeugen:")
    print("   python3 scripts/build_artikelstamm_xlsx.py")
    print("   python3 scripts/build_angebot_xlsx.py")
    print("   python3 scripts/build_katalog_import.py")
    print("   python3 scripts/build_fotopaket.py")
    print("   python3 scripts/build_webkatalog.py")
    print("   python3 scripts/pruefen.py")


if __name__ == "__main__":
    pfad = sys.argv[1] if len(sys.argv) > 1 else STANDARD
    if not os.path.exists(pfad):
        raise SystemExit(f"Datei nicht gefunden: {pfad}")
    print(f"Lese zurück aus: {pfad}")
    einlesen(pfad)
