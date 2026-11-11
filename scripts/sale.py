"""Sale-Preise nach einer Regel vorrechnen (1.15.1, 11.11.2026).

Beispiele:
  python3 scripts/sale.py --kategorie Spielzeug --kategorie Tonies --prozent 30            # Probelauf
  python3 scripts/sale.py --kategorie Spielzeug --prozent 30 --schreiben                   # übernehmen
  python3 scripts/sale.py --alle --prozent 20 --schreiben
  python3 scripts/sale.py --beenden --schreiben                                            # alle Sale-Preise leeren

Regeln:
  * Eingetragene Sale-Preise (Einzelvorgaben der Nutzerin) bleiben IMMER stehen – gerechnet wird nur,
    wo die Spalte Sale leer ist.
  * Nur aktive Artikel mit Preis; Geschenke (Preis 0) bleiben außen vor.
  * Gerundet wird nach unten: unter 10 € auf 50 Cent, sonst auf ganze Euro. Mindestens 0,50 €,
    und der Sale-Preis liegt immer unter dem normalen Preis.
  * Ohne --schreiben wird nichts verändert (Probelauf mit Liste).
"""
import sys, os, csv, math, argparse, shutil, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import CSV_PFAD, zahl


def geld(v):
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def runden(wert, preis):
    s = math.floor(wert * 2) / 2 if wert < 10 else math.floor(wert)
    s = max(0.5, s)
    if s >= preis:                       # Rundung darf den Rabatt nicht auffressen
        s = math.floor((preis - 0.01) * 2) / 2
    return s if s > 0 else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kategorie", action="append", default=[], help="Kategorie (mehrfach möglich)")
    ap.add_argument("--alle", action="store_true", help="alle Kategorien")
    ap.add_argument("--prozent", type=float, help="Rabatt in Prozent, z. B. 30")
    ap.add_argument("--beenden", action="store_true", help="alle Sale-Preise leeren")
    ap.add_argument("--schreiben", action="store_true")
    a = ap.parse_args()
    if not a.beenden and (a.prozent is None or not (0 < a.prozent < 100) or not (a.alle or a.kategorie)):
        ap.error("--prozent (1–99) und --kategorie oder --alle angeben, oder --beenden")

    with open(CSV_PFAD, encoding="utf-8") as f:
        zeilen = list(csv.DictReader(f, delimiter=";"))
    felder = list(zeilen[0].keys())
    if "Sale" not in felder:
        raise SystemExit("Spalte „Sale“ fehlt in der Datenbasis.")
    kats = {k.strip().lower() for k in a.kategorie}
    bekannt = {(z.get("Kategorie") or "").strip().lower() for z in zeilen}
    for k in kats - bekannt:
        raise SystemExit(f"Kategorie „{k}“ gibt es nicht. Vorhanden: {', '.join(sorted(bekannt))}")

    neu, behalten = [], []
    for z in zeilen:
        if a.beenden:
            if z["Sale"]:
                neu.append((z, z["Sale"], "")); z["Sale"] = ""
            continue
        if (z.get("Aktiv") or "ja").lower() != "ja" or (z.get("Status") or "") == "verkauft":
            continue
        if not (a.alle or (z.get("Kategorie") or "").strip().lower() in kats):
            continue
        preis = zahl(z["Preis_netto"]) or 0
        if preis <= 0:
            continue
        if z["Sale"]:
            behalten.append(z); continue
        s = runden(preis * (1 - a.prozent / 100), preis)
        if s:
            neu.append((z, "", geld(s))); z["Sale"] = geld(s)

    for z, alt, wert in neu[:400]:
        print(f"  {z['ArtNr']:10} {z['Bezeichnung'][:42]:42} {z['Preis_netto']:>9} €  ->  Sale {wert or '(leer)':>9}")
    print(f"\n{len(neu)} Sale-Preise {'geleert' if a.beenden else 'gerechnet'}"
          + (f", {len(behalten)} Einzelvorgaben unverändert gelassen" if behalten else ""))
    if not a.schreiben:
        print("Probelauf – nichts geändert. Zum Übernehmen mit --schreiben aufrufen.")
        return
    stempel = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    shutil.copy2(CSV_PFAD, f"{CSV_PFAD}.{stempel}.bak")
    with open(CSV_PFAD, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=felder, delimiter=";", lineterminator="\n")
        w.writeheader(); w.writerows(zeilen)
    print("Geschrieben. Danach Ablauf C (Excel, Importdatei, pruefen.py).")


if __name__ == "__main__":
    main()
