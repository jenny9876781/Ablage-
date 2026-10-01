"""Packt die Fotos, die der Webkatalog braucht, zu ausgabe/kikripp-fotos.zip.

Das Plugin findet ein Bild über den Dateinamen in der Mediathek (F-123.jpg) und zeigt
je Position genau ein Bild. In das Paket gehoeren deshalb genau die Fotos, auf die eine
im Katalog sichtbare Position zeigt. Alles andere wuerde die Mediathek unnoetig fuellen
und das Hochladen verlaengern - die weiteren Ansichten aus den Bemerkungen sind
Arbeitsmaterial und bleiben im Ordner fotos/.

    python3 scripts/build_fotopaket.py              # ein Paket
    python3 scripts/build_fotopaket.py --teile 25   # zusaetzlich Teilpakete zu je 25 MB
    python3 scripts/build_fotopaket.py --nachtrag alte_katalog_import.json
                                                    # zusaetzlich nur die Fotos, die seit
                                                    # dem letzten Import dazugekommen sind

Die Teilpakete sind fuer den Versand: viele Wege (Mail, Chat) nehmen keine 70 MB an.
Sie passen ausserdem zur Anleitung, die das Hochladen in Paketen empfiehlt. Die Fotos
sind ueber alle Teile hinweg dieselben - zusammen ergeben sie genau das Gesamtpaket.
"""
import os, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import lade_artikel, AUSGABE, FOTO_DIR

ZIEL = os.path.join(AUSGABE, "kikripp-fotos.zip")
def gebraucht():
    namen = set()
    for a in lade_artikel():
        if (a.get("Im_Katalog") or "ja").strip().lower() != "ja":
            continue
        if a["Foto"]:
            namen.add(a["Foto"].strip())
    return sorted(namen)


def teilpakete(namen, mb):
    """Verteilt die Fotos auf Pakete von hoechstens `mb` Megabyte, Reihenfolge bleibt."""
    grenze = mb * 1024 * 1024
    pakete, aktuell, groesse = [], [], 0
    for n in namen:
        g = os.path.getsize(os.path.join(FOTO_DIR, n + ".jpg"))
        if aktuell and groesse + g > grenze:
            pakete.append(aktuell); aktuell, groesse = [], 0
        aktuell.append(n); groesse += g
    if aktuell:
        pakete.append(aktuell)
    return pakete


def schreibe(ziel, namen):
    if os.path.exists(ziel):
        os.remove(ziel)
    with zipfile.ZipFile(ziel, "w", zipfile.ZIP_STORED) as z:   # JPEG ist schon komprimiert
        for n in namen:
            z.write(os.path.join(FOTO_DIR, n + ".jpg"), f"fotos/{n}.jpg")
    return os.path.getsize(ziel)


def nachtrag(namen, alte_importdatei):
    """Fotos, die die alte Importdatei noch nicht brauchte: genau das, was in der Mediathek
    fehlt, wenn das letzte Paket vollstaendig hochgeladen wurde. So muss beim Nachpflegen
    nicht alles erneut hoch - WordPress wuerde sonst jedes Bild doppelt anlegen (-1)."""
    import json
    with open(alte_importdatei, encoding="utf-8") as f:
        alt = json.load(f)
    schon_da = {a["foto"] for a in alt if a.get("foto") and a.get("aktiv") and a.get("im_katalog")}
    return [n for n in namen if n not in schon_da]


def main():
    namen = gebraucht()
    fehlt = [n for n in namen if not os.path.exists(os.path.join(FOTO_DIR, n + ".jpg"))]
    if fehlt:
        raise SystemExit("Fotodatei fehlt: " + ", ".join(fehlt))
    kb = schreibe(ZIEL, namen) // 1024
    print(f"geschrieben: {ZIEL}  ({len(namen)} Fotos, {kb//1024} MB)")
    print(f"             {namen[0]} bis {namen[-1]}")

    if "--nachtrag" in sys.argv:
        neu = nachtrag(namen, sys.argv[sys.argv.index("--nachtrag") + 1])
        ziel = os.path.join(AUSGABE, "kikripp-fotos-nachtrag.zip")
        if neu:
            b = schreibe(ziel, neu)
            print(f"geschrieben: {ziel}  ({len(neu)} Fotos, {b//1024//1024} MB, "
                  f"{neu[0]} bis {neu[-1]})")
        else:
            print("Nachtrag: keine neuen Fotos seit dem letzten Import")

    if "--teile" in sys.argv:
        mb = int(sys.argv[sys.argv.index("--teile") + 1])
        # Alte Teilpakete weg, sonst bleibt ein Rest liegen, wenn es weniger werden.
        for d in os.listdir(AUSGABE):
            if d.startswith("kikripp-fotos-") and d.endswith(".zip"):
                os.remove(os.path.join(AUSGABE, d))
        pakete = teilpakete(namen, mb)
        summe = 0
        for i, teil in enumerate(pakete, start=1):
            ziel = os.path.join(AUSGABE, f"kikripp-fotos-{i}von{len(pakete)}.zip")
            b = schreibe(ziel, teil)
            summe += len(teil)
            print(f"geschrieben: {ziel}  ({len(teil)} Fotos, {b//1024//1024} MB, "
                  f"{teil[0]} bis {teil[-1]})")
        if summe != len(namen):
            raise SystemExit(f"FEHLER: Teilpakete enthalten {summe} statt {len(namen)} Fotos")
        print(f"             alle {summe} Fotos sind in den Teilpaketen enthalten")


if __name__ == "__main__":
    main()
