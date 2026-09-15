"""HEIC-Uploads -> fotos/F-xxx.jpg  (gedreht, verkleinert, ohne EXIF/GPS, Personen beschnitten).

Die Fotonummern sind dauerhaft: daten/fotos_index.csv merkt sich über eine Prüfsumme des
Bildinhalts, welche Quelldatei welche F-Nummer bekommen hat. Die Prüfsumme statt des Namens,
weil mehrere Uploads denselben Dateinamen tragen können und ein erneuter Upload ein anderes
Präfix bekommt. Neue Fotos werden hinten angehängt, bestehende Nummern ändern sich nie.
Ohne diesen Index würden neue Fotos die Nummerierung verschieben und alle Artikel im
Artikelstamm zeigten auf das falsche Bild.
"""
import os, glob, csv, sys, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageOps
import pillow_heif
pillow_heif.register_heif_opener()

BASIS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZIEL = os.path.join(BASIS, "fotos")
INDEX = os.path.join(BASIS, "daten", "fotos_index.csv")
QUELLEN = [os.path.expanduser("~/.claude/uploads"), "/root/.claude/uploads"]

# Datenschutz: Beschnitt oben, adressiert über die feste Fotonummer.
# Gepflegt in daten/fotos_beschnitt.csv  (Spalten: Foto;Anteil_oben;Grund)
BESCHNITT_PFAD = os.path.join(BASIS, "daten", "fotos_beschnitt.csv")


def lade_beschnitt():
    if not os.path.exists(BESCHNITT_PFAD):
        return {}
    with open(BESCHNITT_PFAD, encoding="utf-8") as f:
        return {r["Foto"]: float(r["Anteil_oben"].replace(",", "."))
                for r in csv.DictReader(f, delimiter=";") if r.get("Foto")}

def pruefsumme(pfad):
    h = hashlib.md5()
    with open(pfad, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def klarname(pfad):
    """Upload-Dateinamen haben ein Präfix: '38ae3d27-Neubau_Raum_1.HEIC' -> 'Neubau_Raum_1.HEIC'"""
    b = os.path.basename(pfad)
    return b.split("-", 1)[1] if "-" in b.split(".")[0] else b

def aufnahmezeit(im):
    return str(im.getexif().get(306) or im.getexif().get(36867) or "")

def lade_index():
    if not os.path.exists(INDEX):
        return {}, 0
    with open(INDEX, encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter=";"))
    return ({r["Pruefsumme"]: r for r in rows},
            max((int(r["Foto"].split("-")[1]) for r in rows), default=0))

def main():
    os.makedirs(ZIEL, exist_ok=True)
    os.makedirs(os.path.dirname(INDEX), exist_ok=True)
    dateien = []
    for q in QUELLEN:
        for muster in ("*.HEIC", "*.heic", "*.jpg", "*.JPG", "*.jpeg", "*.png", "*.PNG"):
            dateien += glob.glob(os.path.join(q, "**", muster), recursive=True)
    dateien = sorted(set(dateien))
    if not dateien:
        print("Keine Quelldateien gefunden in:", ", ".join(QUELLEN)); return

    index, hoechste = lade_index()
    beschnitt = lade_beschnitt()
    neu, uebersprungen, doppelt = [], 0, []
    kandidaten, gesehen = [], set()
    for f in dateien:
        summe = pruefsumme(f)
        if summe in index:
            uebersprungen += 1
            continue
        if summe in gesehen:                    # zwei Uploads mit identischem Bildinhalt
            doppelt.append(os.path.basename(f))
            continue
        gesehen.add(summe)
        try:
            with Image.open(f) as im:
                kandidaten.append((aufnahmezeit(im), os.path.basename(f), klarname(f), summe, f))
        except Exception as e:
            print(f"  übersprungen (nicht lesbar): {os.path.basename(f)} – {e}")
    kandidaten.sort(key=lambda x: (x[0], x[1]))     # neue Fotos nach Aufnahmezeit, dann Dateiname

    for zeit, _basis, name, summe, f in kandidaten:
        hoechste += 1
        nummer = f"F-{hoechste:03d}"
        im = ImageOps.exif_transpose(Image.open(f)).convert("RGB")
        anteil = beschnitt.get(nummer)
        if anteil:
            w, h = im.size
            im = im.crop((0, int(h * anteil), w, h))
        im.thumbnail((1400, 1400))
        im.save(os.path.join(ZIEL, nummer + ".jpg"), quality=82, optimize=True)   # ohne EXIF
        index[summe] = {"Foto": nummer, "Quelldatei": name, "Aufnahmezeit": zeit,
                        "Beschnitten": "ja" if anteil else "", "Pruefsumme": summe}
        neu.append((nummer, name, zeit))

    with open(INDEX, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["Foto", "Quelldatei", "Aufnahmezeit", "Beschnitten",
                                          "Pruefsumme"], delimiter=";")
        w.writeheader()
        w.writerows(sorted(index.values(), key=lambda r: int(r["Foto"].split("-")[1])))

    print(f"{len(neu)} neue Fotos, {uebersprungen} bereits vorhanden, "
          f"{len(doppelt)} inhaltsgleiche Doppel übersprungen, {len(index)} insgesamt")
    for d in doppelt:
        print(f"   Doppel übersprungen: {d}")
    for nummer, name, zeit in neu:
        print(f"   {nummer}  {zeit[:19] or '(ohne Zeitstempel)':<19}  {name}")
    if neu:
        print("\nDiese Fotonummern sind jetzt zu vergeben. Bestehende Nummern haben sich nicht geändert.")

if __name__ == "__main__":
    main()
