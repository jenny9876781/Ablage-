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
from PIL import Image, ImageOps, ImageFilter
import pillow_heif
pillow_heif.register_heif_opener()

BASIS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZIEL = os.path.join(BASIS, "fotos")
INDEX = os.path.join(BASIS, "daten", "fotos_index.csv")
QUELLEN = [os.path.expanduser("~/.claude/uploads"), "/root/.claude/uploads"]

# Datenschutz: Beschnitt oben und/oder Masken, adressiert über die feste Fotonummer.
# Gepflegt in daten/fotos_beschnitt.csv  (Spalten: Foto;Anteil_oben;Maske;Grund)
#
# Anteil_oben schneidet einen Streifen am oberen Rand ab. Das genügt nicht, wenn eine Person
# mitten im Bild steht — etwa ein gerahmtes Foto in einer Vitrine oder eine Spiegelung in einer
# Gerätescheibe. Dafür gibt es Masken: Rechtecke in der Form x1/y1/x2/y2, Werte 0..1 bezogen auf
# das FERTIGE Bild (nach Beschnitt und Verkleinerung), mehrere durch Leerzeichen getrennt. Die
# Fläche wird zuerst zu einem Mosaik gerechnet und dann weichgezeichnet — das ist nicht
# umkehrbar, anders als eine reine Weichzeichnung.
#
# Ändert sich der Eintrag eines Fotos, wird es aus der Quelldatei neu erzeugt; die Fotonummer
# bleibt dieselbe. Die Signatur in der Spalte "Beschnitten" des Index merkt sich, mit welcher
# Vorgabe das Bild auf der Platte entstanden ist.
BESCHNITT_PFAD = os.path.join(BASIS, "daten", "fotos_beschnitt.csv")


def zahl(text):
    text = (text or "").strip().replace(",", ".")
    return float(text) if text else 0.0


def lade_masken(text):
    """'0.33/0.09/0.42/0.32 0.47/0.13/0.60/0.28' -> [(x1,y1,x2,y2), ...]"""
    felder = []
    for stueck in (text or "").split():
        teile = stueck.split("/")
        if len(teile) != 4:
            raise SystemExit(f"Maske nicht lesbar: {stueck!r} – erwartet x1/y1/x2/y2")
        x1, y1, x2, y2 = (float(t.replace(",", ".")) for t in teile)
        felder.append((min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)))
    return felder


def lade_beschnitt():
    if not os.path.exists(BESCHNITT_PFAD):
        return {}
    vorgaben = {}
    with open(BESCHNITT_PFAD, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter=";"):
            if not r.get("Foto"):
                continue
            vorgaben[r["Foto"]] = {"anteil": zahl(r.get("Anteil_oben")),
                                   "masken": lade_masken(r.get("Maske"))}
    return vorgaben


def signatur(vorgabe):
    """Kurzform der Vorgabe, damit eine Änderung das Foto neu erzeugt."""
    if not vorgabe:
        return ""
    teile = []
    if vorgabe["anteil"]:
        teile.append(f"oben{vorgabe['anteil']:.3f}")
    for x1, y1, x2, y2 in vorgabe["masken"]:
        teile.append(f"maske{x1:.3f}/{y1:.3f}/{x2:.3f}/{y2:.3f}")
    return "+".join(teile)


def aufbereiten(quelle, vorgabe):
    """Quelldatei -> fertiges Bild: drehen, oben beschneiden, verkleinern, Masken setzen."""
    im = ImageOps.exif_transpose(Image.open(quelle)).convert("RGB")
    anteil = vorgabe["anteil"] if vorgabe else 0.0
    if anteil:
        w, h = im.size
        im = im.crop((0, int(h * anteil), w, h))
    im.thumbnail((1400, 1400))
    for x1, y1, x2, y2 in (vorgabe["masken"] if vorgabe else []):
        w, h = im.size
        kasten = (max(0, int(x1 * w)), max(0, int(y1 * h)),
                  min(w, int(x2 * w)), min(h, int(y2 * h)))
        bx, by = kasten[2] - kasten[0], kasten[3] - kasten[1]
        if bx < 2 or by < 2:
            continue
        teil = im.crop(kasten)
        # Mosaik zuerst: das verwirft die Bildinformation und lässt sich nicht zurückrechnen.
        teil = teil.resize((max(1, bx // 24), max(1, by // 24)), Image.BOX).resize((bx, by), Image.NEAREST)
        im.paste(teil.filter(ImageFilter.GaussianBlur(max(3, bx // 12))), kasten)
    return im

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
    quellen = {}                                # Prüfsumme -> Quelldatei, auch für alte Fotos
    for f in dateien:
        summe = pruefsumme(f)
        quellen.setdefault(summe, f)
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
        vorgabe = beschnitt.get(nummer)
        bild = aufbereiten(f, vorgabe)
        bild.save(os.path.join(ZIEL, nummer + ".jpg"), quality=82, optimize=True)   # ohne EXIF
        index[summe] = {"Foto": nummer, "Quelldatei": name, "Aufnahmezeit": zeit,
                        "Beschnitten": signatur(vorgabe), "Pruefsumme": summe}
        neu.append((nummer, name, zeit))

    # Fotos, deren Datenschutz-Vorgabe sich geändert hat, aus der Quelle neu erzeugen.
    # Die Fotonummer bleibt dieselbe — sie hängt an der Prüfsumme, nicht an der Reihenfolge.
    erneuert, ohne_quelle = [], []
    for summe, zeile in index.items():
        nummer = zeile["Foto"]
        soll = signatur(beschnitt.get(nummer))
        if (zeile.get("Beschnitten") or "") == soll:
            continue
        quelle = quellen.get(summe)
        if not quelle:
            ohne_quelle.append(nummer)
            continue
        bild = aufbereiten(quelle, beschnitt.get(nummer))
        bild.save(os.path.join(ZIEL, nummer + ".jpg"), quality=82, optimize=True)
        zeile["Beschnitten"] = soll
        erneuert.append((nummer, soll or "ohne Vorgabe"))

    with open(INDEX, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["Foto", "Quelldatei", "Aufnahmezeit", "Beschnitten",
                                          "Pruefsumme"], delimiter=";", lineterminator="\n")
        w.writeheader()
        w.writerows(sorted(index.values(), key=lambda r: int(r["Foto"].split("-")[1])))

    print(f"{len(neu)} neue Fotos, {uebersprungen} bereits vorhanden, "
          f"{len(doppelt)} inhaltsgleiche Doppel übersprungen, {len(index)} insgesamt")
    for d in doppelt:
        print(f"   Doppel übersprungen: {d}")
    for nummer, name, zeit in neu:
        print(f"   {nummer}  {zeit[:19] or '(ohne Zeitstempel)':<19}  {name}")
    for nummer, soll in erneuert:
        print(f"   neu erzeugt nach geänderter Vorgabe: {nummer}  ({soll})")
    for nummer in ohne_quelle:
        print(f"   ACHTUNG {nummer}: Vorgabe geändert, aber die Quelldatei fehlt – "
              f"das Bild auf der Platte ist unverändert.")
    if neu:
        print("\nDiese Fotonummern sind jetzt zu vergeben. Bestehende Nummern haben sich nicht geändert.")

if __name__ == "__main__":
    main()
