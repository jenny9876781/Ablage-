"""Erzeugt ausgabe/katalog_import.json – die Datei für den Import ins WordPress-Plugin."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import lade_artikel, AUSGABE

def main():
    raeume, liste = [], []
    for i, a in enumerate(lade_artikel(nur_aktive=False)):
        if a["Raum"] not in raeume:
            raeume.append(a["Raum"])
        liste.append({
            "nr":         a["ArtNr"],
            "titel":      a["Bezeichnung"],
            "beschr":     a["Beschreibung"],
            "kat":        a["Kategorie"],
            "raum":       a["Raum"],
            "zustand":    a["Zustand"],
            "masse":      a.get("Maße", ""),
            "menge":      a["Menge"],
            "einheit":    a["Einheit"],
            "preis":      a["Preis_netto"] or 0,
            "basis":      a["Preisbasis"],
            "versand":    a["Versand"],
            "marke":      a.get("Marke", ""),
            "buendel":    a.get("Bündel", ""),
            "foto":       a["Foto"],
            "sortierung": i,
            "aktiv":      a.get("Aktiv", "ja").lower() != "entfällt",
            "im_katalog": a.get("Im_Katalog", "ja").lower() == "ja",
        })
    pfad = os.path.join(AUSGABE, "katalog_import.json")
    with open(pfad, "w", encoding="utf-8") as f:
        json.dump(liste, f, ensure_ascii=False, indent=1)
    imk = sum(1 for x in liste if x["im_katalog"] and x["aktiv"])
    print(f"geschrieben: {pfad}  {os.path.getsize(pfad)//1024} KB")
    print(f"{len(liste)} Artikel, davon {imk} im Katalog sichtbar, {len(raeume)} Räume")

if __name__ == "__main__":
    main()
