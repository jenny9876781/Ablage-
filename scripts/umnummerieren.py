"""Stellt die Datenbasis einmalig auf das Raumschema aus den Bauplänen um.

    python3 scripts/umnummerieren.py            # Probelauf
    python3 scripts/umnummerieren.py --schreiben

Aus `K-031` wird `NU01-02`: Gebäude, Ebene, Raum, laufende Nummer. Die alte
Nummer bleibt in der neuen Spalte `Alt_ArtNr` erhalten — falls im Haus noch ein
alter Zettel klebt, ist die Zuordnung darüber auffindbar.

Das Skript läuft nur einmal. Ist `Alt_ArtNr` schon gefüllt, bricht es ab.
"""
import sys, os, csv, shutil, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import CSV_PFAD, BASIS

RAEUME_PFAD = os.path.join(BASIS, "daten", "raeume.csv")

# Alter Raumname -> neuer Raumcode. Vom Nutzer am 17.09.2026 bestätigt.
# Wo mehrere Blöcke eines Sammelnamens auf verschiedene Räume gehen, steht die
# Fotonummer als zweites Kriterium (die Fotos sind in Aufnahmereihenfolge).
ZUORDNUNG = {
    "Neubau Flur":          "NE01",
    "Neubau Raum 1":        "NU02",   # Gruppenraum 5
    "Neubau Raum 2":        "NU03",   # Schlafraum 4
    "Neubau Raum 3":        "NU04",   # Schlafraum 5
    "Neubau Küche":         "NE05",   # Speisesaal
    "Neubau Elternlounge":  "NU01",
    "Neubau Eingang":       "NU01",
    "Besprechung":          "BE10",
    "Büro":                 "BE11",
    "WC":                   "BA12",   # WC Personal in der Attika
    "Atelier":              "BA08",
    "Werkstatt":            "BU09",   # Werkraum
    "Mitarbeiter-Ruheraum": "BA10",
    "Mitarbeiterraum":      "BA09",   # Personal
    "Raum 2":               "BE06",   # Gruppenraum 2
    "Eingang":              "BE01",   # Flur 1
    "Dachgeschoss":         "BA04",   # Gruppenraum 4
    "UG":                   "BU04",   # Annahme: Gruppenraum im Bestand-UG
    "Flur UG":              "NU01",
    "Terrasse":             "TE01",
    "Terrasse hinten":      "TE01",
    "Dachterrasse":         "TE02",
    "Außen":                "GA01",
}

# Der Sammeltopf „Flur“ zerfällt nach Aufnahmeblöcken auf mehrere Räume.
def flur_code(fotonr):
    if fotonr <= 41:  return "NE01"   # Bollenhut-Galerie, Neubau EG
    if fotonr == 54:  return "BE01"   # zwischen Eingang und WC im Bestand
    if fotonr <= 50:  return "NU01"   # die beiden Nachzügler F-049/050
    if fotonr <= 73:  return "NE01"   # Flur B
    return "NU01"                     # Flur C


def lade_raeume():
    with open(RAEUME_PFAD, encoding="utf-8") as f:
        return {r["Raumcode"]: r for r in csv.DictReader(f, delimiter=";")}


def fotonr(wert):
    try:
        return int(str(wert).split("-")[1])
    except (IndexError, ValueError):
        return 0


def umstellen(schreiben):
    raeume = lade_raeume()
    with open(CSV_PFAD, encoding="utf-8") as f:
        zeilen = list(csv.DictReader(f, delimiter=";"))
    felder = list(zeilen[0].keys())

    if "Alt_ArtNr" in felder and any(z.get("Alt_ArtNr") for z in zeilen):
        raise SystemExit("Die Datenbasis ist bereits umgestellt – „Alt_ArtNr“ ist gefüllt. "
                         "Das Skript läuft nur einmal.")

    # ---- Raumcode je Zeile bestimmen ------------------------------------
    ohne = {}
    for z in zeilen:
        alt = z["Raum"].strip()
        code = flur_code(fotonr(z["Foto"])) if alt == "Flur" else ZUORDNUNG.get(alt)
        if not code:
            ohne[alt] = ohne.get(alt, 0) + 1
            code = ""
        z["_code"] = code

    if ohne:
        print("  ACHTUNG: für diese alten Raumnamen fehlt eine Zuordnung:")
        for k, v in sorted(ohne.items()):
            print(f"    {k!r}  ({v} Positionen)")
        raise SystemExit("Abbruch – erst die Zuordnung ergänzen.")

    # ---- Neue Nummern vergeben, Reihenfolge = alte Nummer ---------------
    # Nur aktive Positionen bekommen eine neue Nummer. Entfallene behalten ihre
    # K-Nummer: sie stehen in keiner Ausgabedatei und sollen im Raum keine
    # Nummer verbrauchen, sonst fängt das Erfassungsblatt bei einer Lücke an.
    zaehler = {}
    for z in sorted(zeilen, key=lambda x: x["ArtNr"]):
        if (z.get("Aktiv") or "ja").lower() == "entfällt":
            z["_neu"] = z["ArtNr"]
            continue
        code = z["_code"]
        zaehler[code] = zaehler.get(code, 0) + 1
        z["_neu"] = f"{code}-{zaehler[code]:02d}"

    # ---- Felder umbauen -------------------------------------------------
    neue_felder = ["ArtNr", "Alt_ArtNr", "Raumcode"] + [f for f in felder
                   if f not in ("ArtNr", "Alt_ArtNr", "Raumcode")]
    ergebnis = []
    for z in sorted(zeilen, key=lambda x: x["_neu"]):
        neu = {f: z.get(f, "") for f in neue_felder}
        neu["Alt_ArtNr"] = "" if z["_neu"] == z["ArtNr"] else z["ArtNr"]
        neu["ArtNr"] = z["_neu"]
        neu["Raumcode"] = z["_code"]
        neu["Raum"] = raeume[z["_code"]]["Raumname"]
        ergebnis.append(neu)

    # ---- Bericht --------------------------------------------------------
    je_raum = {}
    for z in ergebnis:
        je_raum.setdefault(z["Raumcode"], {"gesamt": 0, "aktiv": 0})
        je_raum[z["Raumcode"]]["gesamt"] += 1
        if (z.get("Aktiv") or "ja").lower() != "entfällt":
            je_raum[z["Raumcode"]]["aktiv"] += 1

    print(f"{len(ergebnis)} Positionen auf {len(je_raum)} Räume verteilt\n")
    for code in sorted(je_raum):
        r = raeume[code]
        z = je_raum[code]
        print(f"  {code}  {r['Gebaeude'][:6]:<6} {r['Ebene']:<9} {r['Raumname']:<22} "
              f"{z['aktiv']:>3} aktiv von {z['gesamt']:>3}")

    print("\n  Beispiele:")
    for z in ergebnis[:6] + ergebnis[-4:]:
        print(f"    {z['Alt_ArtNr']:>6}  ->  {z['ArtNr']:<9} {z['Raum']:<22} {z['Bezeichnung'][:36]}")

    if not schreiben:
        print("\nProbelauf – nichts geschrieben. Mit --schreiben übernehmen.")
        return

    stempel = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    shutil.copy2(CSV_PFAD, f"{CSV_PFAD}.{stempel}.bak")
    with open(CSV_PFAD, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=neue_felder, delimiter=";")
        w.writeheader(); w.writerows(ergebnis)
    print(f"\nGeschrieben. Sicherung: {CSV_PFAD}.{stempel}.bak")


if __name__ == "__main__":
    umstellen("--schreiben" in sys.argv)
