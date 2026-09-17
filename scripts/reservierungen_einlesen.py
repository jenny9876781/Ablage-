"""Trägt den Reservierungs-Export aus WordPress in die Datenbasis ein.

    python3 scripts/reservierungen_einlesen.py kikripp-reservierungen-20260916-1030.csv

Die Datei laden Sie in WordPress unter „Artikelkatalog → Reservierungen →
Alle Reservierungen als CSV exportieren“ herunter. Übernommen werden je Artikel
Status, verkaufte Menge, Verkaufspreis und Verkaufsdatum. Rechnungsnummer, Zahlung,
Zahlart und **Käufer** bleiben unberührt – die tragen Sie selbst ein, sobald die
Rechnung aus DATEV vorliegt. Der Webkatalog speichert keine Namen; die stehen
ausschließlich in den Benachrichtigungsmails an jennyp@kikripp.de.

Ohne --schreiben wird nur angezeigt, was sich ändern würde.
"""
import sys, os, csv, shutil, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import CSV_PFAD

# Positionsstatus aus WordPress -> Status in der Datenbasis
STATUS = {"bezahlt": "verkauft", "reserviert": "reserviert", "storniert": "verfügbar"}


def geld(v):
    """„1.234,50“ oder „1234.5“ -> 1234.50 als deutscher Text."""
    s = str(v or "").strip().replace("€", "").strip()
    if not s:
        return ""
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return f"{float(s):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except ValueError:
        return ""


def zahl(v):
    try:
        return float(str(v or "0").replace(".", "").replace(",", "."))
    except ValueError:
        return 0.0


def datum(v):
    """„2026-09-16 10:30:00“ -> „16.09.2026“."""
    s = str(v or "").strip()
    for form in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(s[:19 if " " in s else 10], form).strftime("%d.%m.%Y")
        except ValueError:
            continue
    return ""


def lese_export(pfad):
    """Fasst den Export je Artikelnummer zusammen."""
    with open(pfad, encoding="utf-8-sig") as f:
        zeilen = list(csv.DictReader(f, delimiter=";"))
    pflicht = {"ArtNr", "Menge", "Preis_netto", "Positionsstatus", "Name"}
    fehlt = pflicht - set(zeilen[0].keys() if zeilen else [])
    if fehlt:
        raise SystemExit("Die Datei sieht nicht nach dem Reservierungs-Export aus. "
                         "Es fehlen die Spalten: " + ", ".join(sorted(fehlt)))

    je_artikel = {}
    for z in zeilen:
        nr = (z.get("ArtNr") or "").strip()
        if not nr:
            continue
        pos = (z.get("Positionsstatus") or "").strip().lower()
        e = je_artikel.setdefault(nr, {"verkauft": 0.0, "reserviert": 0.0, "erloes": 0.0,
                                       "kaeufer": [], "reserviert_fuer": [], "datum": ""})
        menge = zahl(z.get("Menge"))
        preis = zahl(z.get("Preis_netto"))
        name = (z.get("Name") or "").strip()
        if pos == "bezahlt":
            e["verkauft"] += menge
            e["erloes"] += menge * preis
            if name and name not in e["kaeufer"]:
                e["kaeufer"].append(name)
            d = datum(z.get("Bezahlt_am")) or datum(z.get("Eingegangen"))
            if d and d > e["datum"]:          # das späteste Zahldatum gewinnt
                e["datum"] = d
        elif pos == "reserviert":
            e["reserviert"] += menge
            if name and name not in e["reserviert_fuer"]:
                e["reserviert_fuer"].append(name)
    return je_artikel


def eintragen(pfad, schreiben):
    je_artikel = lese_export(pfad)
    with open(CSV_PFAD, encoding="utf-8") as f:
        zeilen = list(csv.DictReader(f, delimiter=";"))
    felder = list(zeilen[0].keys())

    unbekannt = set(je_artikel) - {z["ArtNr"] for z in zeilen}
    aenderungen, ueberbucht = [], []

    for z in zeilen:
        e = je_artikel.get(z["ArtNr"])
        if not e:
            continue
        bestand = zahl(z["Menge"])
        if e["verkauft"] + e["reserviert"] > bestand:
            ueberbucht.append((z["ArtNr"], bestand, e["verkauft"], e["reserviert"]))

        neu = {}
        if e["verkauft"] > 0:
            neu["Status"] = "verkauft" if e["verkauft"] >= bestand else "teilverkauft"
            neu["Verkauft_Menge"] = (f'{e["verkauft"]:.0f}' if e["verkauft"] == int(e["verkauft"])
                                     else f'{e["verkauft"]}')
            # Der Artikelstamm rechnet Verkauft_Menge × Verkaufspreis_netto.
            # Hier gehört deshalb der Stückpreis hin, nicht der Gesamterlös.
            neu["Verkaufspreis_netto"] = geld(e["erloes"] / e["verkauft"])
            neu["Verkaufsdatum"] = e["datum"]
            # Der Webkatalog speichert keine Namen mehr (die stehen nur in den
            # Benachrichtigungsmails). Nur überschreiben, wenn wirklich etwas kam.
            if e["kaeufer"]:
                neu["Käufer"] = ", ".join(e["kaeufer"])
            neu["Kanal"] = "Webkatalog"
        elif e["reserviert"] > 0:
            neu["Status"] = "reserviert"
            if e["reserviert_fuer"]:
                neu["Reserviert_für"] = ", ".join(e["reserviert_fuer"])
            neu["Kanal"] = "Webkatalog"
        else:
            neu["Status"] = "verfügbar"
            neu["Reserviert_für"] = ""

        for sp, wert in neu.items():
            if sp in z and z[sp] != wert:
                aenderungen.append((z["ArtNr"], sp, z[sp], wert))
                if schreiben:
                    z[sp] = wert

    print(f"{len(je_artikel)} Artikel im Export · {len(aenderungen)} Feldänderungen")
    for nr, sp, a, b in aenderungen[:60]:
        print(f"   {nr:8} {sp:20} {a!r:>22}  ->  {b!r}")
    if len(aenderungen) > 60:
        print(f"   … und {len(aenderungen)-60} weitere")
    if unbekannt:
        print("\n  ACHTUNG: diese Artikelnummern stehen im Export, aber nicht in der Datenbasis:",
              ", ".join(sorted(unbekannt)))
        print("  Vermutlich wurde der Artikelstamm zwischenzeitlich geändert. Bitte prüfen.")
    if ueberbucht:
        print("\n  ACHTUNG: hier ist mehr vergeben als vorhanden:")
        for nr, b, v, r in ueberbucht:
            print(f"   {nr}: Bestand {b:.0f}, verkauft {v:.0f}, reserviert {r:.0f}")

    if not schreiben:
        print("\nProbelauf – es wurde nichts geändert. Zum Übernehmen noch einmal mit --schreiben aufrufen.")
        return

    stempel = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    shutil.copy2(CSV_PFAD, f"{CSV_PFAD}.{stempel}.bak")
    with open(CSV_PFAD, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=felder, delimiter=";")
        w.writeheader(); w.writerows(zeilen)
    print(f"\nGeschrieben. Sicherung: {CSV_PFAD}.{stempel}.bak")
    print("Jetzt neu erzeugen:  python3 scripts/build_artikelstamm_xlsx.py")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        raise SystemExit(__doc__)
    if not os.path.exists(args[0]):
        raise SystemExit(f"Datei nicht gefunden: {args[0]}")
    eintragen(args[0], "--schreiben" in sys.argv)
