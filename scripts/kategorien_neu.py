"""Neue Kategorien (05.11.2026, mit der Nutzerin abgestimmt) – einmalig auf daten/artikel_kikripp.csv anwenden.

„Kita-Ausstattung“ (151 sichtbar) und „Spielzeug“ (129) waren zu groß und gemischt; Technik/Küchentechnik/
Sonstiges/Uhren zu klein. Neu:
  Kindermöbel · Kinderfahrzeuge (worauf ein Kind fährt) · Turnen & Bewegung (drinnen) ·
  Spielplatz & Außenspiel · Baby & Unterwegs · Spielzeug (inkl. Spielküchen, Kaufläden, Werkbänke) ·
  Bücher, Spiele & Puzzles · Tonies · Bastel- & Malmaterial (war Verbrauchsmaterial) ·
  Haushalt & Geräte (Technik + Küchentechnik + Sonstiges + Becher/Teller) · Garten nur noch für Erwachsene.
  Uhren → Deko. „zu verschenken“ bleibt unverändert.
Gemischte Pakete nach Hauptinhalt. Das Skript ist idempotent (zweiter Lauf ändert nichts).
"""
import csv, os, sys, collections

BASIS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(BASIS, "daten", "artikel_kikripp.csv")

def liste(s):
    return s.split()

FEST = {}
def setze(kat, nrn):
    for n in liste(nrn):
        assert n not in FEST, n
        FEST[n] = kat

setze("Kinderfahrzeuge", """BA02-02 BA06-02 BA06-03 BA06-04 BA06-06 BA06-09 GA01-11 GA01-12 K-039
    BU12-01 BU12-02 BU12-04 BU12-05 BU12-06 BU12-07 BU12-08 BU12-09 BU12-11 BU12-17 BU12-12 BU12-13
    BU12-14 BU12-15 BU12-16 BU13-05 BU13-06 BU13-07 BU13-08 NU06-12""")
setze("Turnen & Bewegung", """NU04-16 BA05-02 BA05-03 BA05-04 BA05-05 BA05-06 BA05-07 BA05-08 BA05-09
    BA05-10 BA06-05 BA06-07 BA06-08 BA06-11 BA06-12""")
setze("Spielplatz & Außenspiel", """GA01-03 GA01-04 GA01-14 GA01-02 GA01-05 GA01-06 GA01-07 GA01-08 GA01-09
    GA01-10 GA01-13 GA01-15 GA01-16 GA01-17 GA01-18 GA01-19 GA01-20 GA01-21 TE02-07 TE02-09 TE02-10 TE02-11
    TE02-12 TE02-13 TE02-14 TE02-15 TE02-17 BU12-03 BU12-10 K-136""")
setze("Baby & Unterwegs", """NE03-05 NE04-11 GA01-22 NU06-08 NU06-09 NU06-11 BU01-32 BU01-34 NU05-01
    NE05-06 NE05-07 NE05-08 NE05-09 BU14-01 NE05-19 NE05-20 NE04-07 NE04-20 NE04-08 NE04-09 NE04-10 NE04-13
    NE03-03 NE03-04 K-027 NU03-10 BU05-10""")
setze("Spielzeug", """NU03-03 NU03-04 NU07-02 NU07-03 BA03-02 BA03-06 BU01-02 BU02-05 BU05-02 BU02-06
    BU01-37 BU01-42 BU01-43 BU01-39 BU01-38 NU04-18 K-017 BU09-04 BU09-05 K-111 BA05-01""")
setze("Bücher, Spiele & Puzzles", """BU01-14 BU01-15 BU01-16 BU01-17 BU01-18 BU01-19 BU01-20 BU01-21 BU04-16
    BA04-23 BA04-25 BA04-26 BA04-27 BA04-28 BA04-29 BA04-30 BA04-31 BA04-32 BA04-34 BA04-35 BA04-37 BA04-38
    BA04-39 NU05-39 NU05-40 NU05-42 NU05-43 NU05-46 NU05-46A NU05-47 NU05-48 NU05-49 NU05-50 NU05-51 NU05-52
    NU07-14 NU07-15 NU07-16 NU07-17 NU07-18 NU04-25 NU04-27 NU04-28 NU04-29 NU04-30 NU04-31 NU04-32 NU04-33
    NU04-34 NU04-36 NU04-37 NU04-38 NU04-39 NU04-40 NU04-43 NU04-44 NU04-45 NU04-47 NU04-48 NU04-49 NU04-52
    NU04-53 NU04-54 NU04-55 NU04-61 NU04-62 NU05-18""")
setze("Tonies", "NE01-27 NE01-28 NE01-29 NE01-30 NE01-31 NE01-32 NE01-33 NE01-34 NE01-35 NE01-36 NE01-37 NE01-38 NE01-39")
setze("Bastel- & Malmaterial", "BA08-09 NU05-45")
setze("Haushalt & Geräte", "NE02-05 NE02-06 NE02-07 BU06-03 BU01-10 BU14-02 BU14-07 BU01-40")
setze("Deko", "BA09-03 BE06-01")
# Kindermöbel, die bisher unter „Möbel“ standen
setze("Kindermöbel", """NU02-23 NU04-10 NU04-20 NE01-20 BA02-04 BA02-08 BU02-03 BU04-06 BU04-10 BU05-05""")

# Alles Übrige einer alten Kategorie
REST = {
    "Kita-Ausstattung": "Kindermöbel",
    "Verbrauchsmaterial": "Bastel- & Malmaterial",
    "Technik": "Haushalt & Geräte",
    "Küchentechnik": "Haushalt & Geräte",
    "Sonstiges": "Haushalt & Geräte",
    "Uhren": "Deko",
}

def main():
    with open(CSV, encoding="utf-8", newline="") as f:
        r = csv.DictReader(f, delimiter=";")
        felder, zeilen = r.fieldnames, list(r)
    bekannt = {z["ArtNr"] for z in zeilen}
    fehlt = [n for n in FEST if n not in bekannt]
    if fehlt:
        sys.exit("unbekannte ArtNr: " + ", ".join(fehlt))
    geaendert = collections.Counter()
    for z in zeilen:
        alt = z["Kategorie"]
        if alt == "zu verschenken":
            continue
        neu = FEST.get(z["ArtNr"], REST.get(alt, alt))
        if neu != alt:
            geaendert[(alt, neu)] += 1
            z["Kategorie"] = neu
    with open(CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=felder, delimiter=";", lineterminator="\n")
        w.writeheader(); w.writerows(zeilen)
    for (a, n), c in sorted(geaendert.items()):
        print(f"{c:4} {a} → {n}")
    print("geändert:", sum(geaendert.values()))

if __name__ == "__main__":
    main()
